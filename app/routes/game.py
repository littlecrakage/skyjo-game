from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session
import uuid

from app import db, socketio
from app.models import Game, Player

game_bp = Blueprint('game', __name__, url_prefix='/game')


def get_or_create_session_id():
    """Get or create a unique session ID for the guest user."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']


@game_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create a new game room."""
    if request.method == 'POST':
        # Get form data
        player_name = request.form.get('player_name', 'Player').strip()
        max_players = int(request.form.get('max_players', 4))
        is_public = request.form.get('is_public') == 'on'
        turn_timer = int(request.form.get('turn_timer', 60))
        finish_round = request.form.get('finish_round') == 'on'
        
        # Validate
        if not player_name:
            player_name = 'Player'
        max_players = max(2, min(8, max_players))  # Clamp 2-8
        turn_timer = max(0, min(300, turn_timer))  # Clamp 0-300
        
        # Create game
        game = Game(
            code=Game.generate_code(),
            max_players=max_players,
            is_public=is_public,
            turn_timer=turn_timer,
            finish_round=finish_round
        )
        db.session.add(game)
        db.session.flush()  # Get game.id
        
        # Create host player
        session_id = get_or_create_session_id()
        
        # Mark player as disconnected from any previous games
        old_players = Player.query.filter_by(session_id=session_id).all()
        for old_player in old_players:
            old_player.is_connected = False
        
        host = Player(
            game_id=game.id,
            name=player_name,
            session_id=session_id,
            is_host=True,
            turn_order=0
        )
        db.session.add(host)
        db.session.commit()
        
        # Redirect to game room
        return redirect(url_for('game.room', code=game.code))
    
    # GET - show create form
    return render_template('game/create.html')


@game_bp.route('/join', methods=['GET', 'POST'])
def join():
    """Join a game by code."""
    error = None
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        player_name = request.form.get('player_name', 'Player').strip()
        
        if not player_name:
            player_name = 'Player'
        
        # Find the game
        game = Game.query.filter_by(code=code).first()
        
        if not game:
            error = 'Game not found. Check the code and try again.'
        elif game.status != 'waiting':
            error = 'This game has already started.'
        elif game.is_full():
            error = 'This game is full.'
        else:
            # Check if player is already in the game (reconnecting)
            session_id = get_or_create_session_id()
            existing_player = game.players.filter_by(session_id=session_id).first()
            
            if existing_player:
                # Reconnecting - just redirect
                return redirect(url_for('game.room', code=game.code))
            
            # Mark player as disconnected from any previous games
            old_players = Player.query.filter_by(session_id=session_id).all()
            for old_player in old_players:
                old_player.is_connected = False
            
            # Create new player
            turn_order = game.player_count()
            player = Player(
                game_id=game.id,
                name=player_name,
                session_id=session_id,
                turn_order=turn_order
            )
            db.session.add(player)
            db.session.commit()
            
            # Notify other players via WebSocket
            socketio.emit('player_joined', {
                'player': player.to_dict()
            }, room=game.code)
            socketio.emit('game_state', game.to_dict(include_players=True), room=game.code)
            
            return redirect(url_for('game.room', code=game.code))
    
    # GET or error - show join form
    code = request.args.get('code', '')
    return render_template('game/join.html', error=error, code=code)


@game_bp.route('/room/<code>')
def room(code):
    """Game room page."""
    game = Game.query.filter_by(code=code.upper()).first()
    
    if not game:
        return redirect(url_for('game.join'))
    
    # Get current player
    session_id = get_or_create_session_id()
    player = game.players.filter_by(session_id=session_id).first()
    
    # If not a player, they're a spectator
    is_spectator = player is None
    
    # Use different template based on game status
    if game.status == 'playing':
        return render_template('game/playing.html', 
                             game=game,
                             player=player, 
                             is_spectator=is_spectator)
    
    return render_template('game/room.html', 
                         game=game, 
                         player=player, 
                         is_spectator=is_spectator)


@game_bp.route('/lobbies')
def lobbies():
    """List public game lobbies."""
    return render_template('game/lobbies.html')


# ============ API Endpoints ============

@game_bp.route('/api/lobbies')
def api_lobbies():
    """Get list of public waiting games."""
    games = Game.query.filter_by(
        is_public=True,
        status='waiting'
    ).order_by(Game.created_at.desc()).limit(20).all()
    
    return jsonify({
        'games': [g.to_dict(include_players=True) for g in games]
    })


@game_bp.route('/api/room/<code>')
def api_room(code):
    """Get game room data."""
    game = Game.query.filter_by(code=code.upper()).first()
    
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    return jsonify(game.to_dict(include_players=True))
