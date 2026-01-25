"""
WebSocket event handlers for real-time game updates.
"""
from flask import session
from flask_socketio import emit, join_room, leave_room

from app import socketio, db
from app.models import Game, Player


def get_session_id():
    """Get current session ID."""
    return session.get('session_id')


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {get_session_id()}")


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    session_id = get_session_id()
    print(f"Client disconnected: {session_id}")
    
    # Find player by session_id and mark as disconnected
    player = Player.query.filter_by(session_id=session_id).first()
    if player:
        player.is_connected = False
        db.session.commit()
        
        # Notify others in the room
        emit('player_disconnected', {
            'player_id': player.id,
            'player_name': player.name
        }, room=player.game.code)


@socketio.on('join_room')
def handle_join_room(data):
    """Player joins a game room for real-time updates."""
    code = data.get('code', '').upper()
    session_id = get_session_id()
    
    game = Game.query.filter_by(code=code).first()
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    # Join the SocketIO room
    join_room(code)
    
    # Find the player and mark as connected
    player = game.players.filter_by(session_id=session_id).first()
    if player:
        player.is_connected = True
        db.session.commit()
        
        # Notify others that player connected
        emit('player_connected', {
            'player_id': player.id,
            'player_name': player.name
        }, room=code, include_self=False)
    
    # Send current game state to the joining client
    emit('game_state', game.to_dict(include_players=True))


@socketio.on('leave_room')
def handle_leave_room(data):
    """Player leaves a game room."""
    code = data.get('code', '').upper()
    leave_room(code)


@socketio.on('add_bot')
def handle_add_bot(data):
    """Host adds a bot to the game."""
    code = data.get('code', '').upper()
    difficulty = data.get('difficulty', 'medium')
    session_id = get_session_id()
    
    game = Game.query.filter_by(code=code).first()
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    # Verify requester is the host
    player = game.players.filter_by(session_id=session_id).first()
    if not player or not player.is_host:
        emit('error', {'message': 'Only the host can add bots'})
        return
    
    # Check if game is full
    if game.is_full():
        emit('error', {'message': 'Game is full'})
        return
    
    # Check if game is in waiting state
    if game.status != 'waiting':
        emit('error', {'message': 'Cannot add bots after game has started'})
        return
    
    # Create bot
    bot_count = game.players.filter_by(is_bot=True).count()
    bot = Player(
        game_id=game.id,
        name=f"Bot {bot_count + 1}",
        is_bot=True,
        bot_difficulty=difficulty,
        turn_order=game.player_count(),
        is_connected=True
    )
    db.session.add(bot)
    db.session.commit()
    
    # Notify all players in the room
    emit('player_joined', {
        'player': bot.to_dict()
    }, room=code)
    
    # Send updated game state
    emit('game_state', game.to_dict(include_players=True), room=code)


@socketio.on('remove_player')
def handle_remove_player(data):
    """Host removes a player (bot or disconnected player) from the game."""
    code = data.get('code', '').upper()
    player_id = data.get('player_id')
    session_id = get_session_id()
    
    game = Game.query.filter_by(code=code).first()
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    # Verify requester is the host
    host = game.players.filter_by(session_id=session_id).first()
    if not host or not host.is_host:
        emit('error', {'message': 'Only the host can remove players'})
        return
    
    # Find player to remove
    player_to_remove = Player.query.get(player_id)
    if not player_to_remove or player_to_remove.game_id != game.id:
        emit('error', {'message': 'Player not found'})
        return
    
    # Can't remove yourself
    if player_to_remove.id == host.id:
        emit('error', {'message': 'Cannot remove yourself'})
        return
    
    player_name = player_to_remove.name
    db.session.delete(player_to_remove)
    
    # Reorder remaining players
    for i, p in enumerate(game.players.order_by(Player.turn_order).all()):
        p.turn_order = i
    
    db.session.commit()
    
    # Notify all players
    emit('player_left', {
        'player_id': player_id,
        'player_name': player_name
    }, room=code)
    
    emit('game_state', game.to_dict(include_players=True), room=code)


@socketio.on('start_game')
def handle_start_game(data):
    """Host starts the game."""
    code = data.get('code', '').upper()
    session_id = get_session_id()
    
    game = Game.query.filter_by(code=code).first()
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    # Verify requester is the host
    player = game.players.filter_by(session_id=session_id).first()
    if not player or not player.is_host:
        emit('error', {'message': 'Only the host can start the game'})
        return
    
    # Check minimum players
    if game.player_count() < 2:
        emit('error', {'message': 'Need at least 2 players'})
        return
    
    # Check game status
    if game.status != 'waiting':
        emit('error', {'message': 'Game already started'})
        return
    
    # Initialize the game (will be implemented in game logic)
    from app.game.logic import initialize_game
    initialize_game(game)
    
    # Notify all players
    emit('game_started', {
        'game': game.to_dict(include_players=True)
    }, room=code)


def broadcast_game_update(game):
    """Broadcast game state to all players in a room."""
    emit('game_state', game.to_dict(include_players=True), 
         room=game.code, namespace='/')
