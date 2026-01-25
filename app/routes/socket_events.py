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


# ============ Gameplay Events ============

@socketio.on('reveal_initial')
def handle_reveal_initial(data):
    """Player reveals a card during initial phase."""
    code = data.get('code', '').upper()
    card_index = data.get('card_index')
    session_id = get_session_id()
    
    game = Game.query.filter_by(code=code).first()
    if not game or game.status != 'playing':
        emit('error', {'message': 'Game not found or not playing'})
        return
    
    player = game.players.filter_by(session_id=session_id).first()
    if not player:
        emit('error', {'message': 'Player not found'})
        return
    
    # Check if player still needs to reveal
    if player.revealed_count() >= 2:
        emit('error', {'message': 'Already revealed 2 cards'})
        return
    
    cards = player.get_cards()
    if card_index < 0 or card_index >= len(cards):
        emit('error', {'message': 'Invalid card index'})
        return
    
    if cards[card_index]['revealed']:
        emit('error', {'message': 'Card already revealed'})
        return
    
    # Reveal the card
    cards[card_index]['revealed'] = True
    player.set_cards(cards)
    db.session.commit()
    
    # Broadcast update
    emit('game_state', game.to_dict(include_players=True), room=code)
    
    # Check if all players have revealed 2 cards
    all_ready = all(p.revealed_count() >= 2 for p in game.players)
    if all_ready:
        # Determine starting player based on highest revealed total
        from app.game.logic import determine_starting_player
        game.current_player_index = determine_starting_player(game)
        db.session.commit()
        
        emit('initial_reveal_complete', {'all_ready': True}, room=code)
        
        # Notify who starts
        current = game.get_current_player()
        emit('turn_changed', {
            'current_player_id': current.id,
            'current_player_name': current.name
        }, room=code)
        
        # If starting player is a bot, process their turn
        if current.is_bot:
            process_bot_turn(game, current)
    
    # Broadcast updated state
    emit('game_state', game.to_dict(include_players=True), room=code)


@socketio.on('draw_card')
def handle_draw_card(data):
    """Player draws a card from draw or discard pile."""
    code = data.get('code', '').upper()
    from_discard = data.get('from_discard', False)
    session_id = get_session_id()
    
    game = Game.query.filter_by(code=code).first()
    if not game or game.status != 'playing':
        emit('error', {'message': 'Game not found or not playing'})
        return
    
    player = game.players.filter_by(session_id=session_id).first()
    if not player:
        emit('error', {'message': 'Player not found'})
        return
    
    # Check if it's player's turn
    current = game.get_current_player()
    if not current or current.id != player.id:
        emit('error', {'message': "Not your turn"})
        return
    
    # Check if player already has a held card
    if player.held_card is not None:
        emit('error', {'message': 'Already holding a card'})
        return
    
    # Draw the card
    from app.game.logic import draw_card
    try:
        card_value = draw_card(game, player, from_discard)
    except ValueError as e:
        emit('error', {'message': str(e)})
        return
    
    # Notify the player who drew
    emit('card_drawn', {
        'player_id': player.id,
        'player_name': player.name,
        'card_value': card_value,
        'from_discard': from_discard
    }, room=code)
    
    # Broadcast game state
    emit('game_state', game.to_dict(include_players=True), room=code)


@socketio.on('place_card')
def handle_place_card(data):
    """Player places held card on their grid."""
    code = data.get('code', '').upper()
    card_index = data.get('card_index')
    session_id = get_session_id()
    
    game = Game.query.filter_by(code=code).first()
    if not game or game.status != 'playing':
        emit('error', {'message': 'Game not found or not playing'})
        return
    
    player = game.players.filter_by(session_id=session_id).first()
    if not player:
        emit('error', {'message': 'Player not found'})
        return
    
    # Check if it's player's turn
    current = game.get_current_player()
    if not current or current.id != player.id:
        emit('error', {'message': "Not your turn"})
        return
    
    # Place the card
    from app.game.logic import place_card, check_round_end, next_turn
    try:
        place_card(game, player, card_index)
    except ValueError as e:
        emit('error', {'message': str(e)})
        return
    
    emit('card_placed', {
        'player_id': player.id,
        'player_name': player.name
    }, room=code)
    
    # Check if round should end
    if check_round_end(game, player):
        handle_round_end(game, code)
    else:
        # Move to next turn
        next_player = next_turn(game)
        emit('turn_changed', {
            'current_player_id': next_player.id,
            'current_player_name': next_player.name
        }, room=code)
        
        # If next player is a bot, process their turn
        if next_player.is_bot:
            process_bot_turn(game, next_player)
    
    emit('game_state', game.to_dict(include_players=True), room=code)


@socketio.on('discard_held')
def handle_discard_held(data):
    """Player discards the held card (must reveal a card after)."""
    code = data.get('code', '').upper()
    session_id = get_session_id()
    
    game = Game.query.filter_by(code=code).first()
    if not game or game.status != 'playing':
        emit('error', {'message': 'Game not found or not playing'})
        return
    
    player = game.players.filter_by(session_id=session_id).first()
    if not player:
        emit('error', {'message': 'Player not found'})
        return
    
    # Check if it's player's turn
    current = game.get_current_player()
    if not current or current.id != player.id:
        emit('error', {'message': "Not your turn"})
        return
    
    from app.game.logic import discard_held_card
    try:
        discard_held_card(game, player)
    except ValueError as e:
        emit('error', {'message': str(e)})
        return
    
    # Player now needs to reveal a card - don't end turn yet
    emit('game_state', game.to_dict(include_players=True), room=code)


@socketio.on('reveal_card')
def handle_reveal_card(data):
    """Player reveals a face-down card (after discarding held card)."""
    code = data.get('code', '').upper()
    card_index = data.get('card_index')
    session_id = get_session_id()
    
    game = Game.query.filter_by(code=code).first()
    if not game or game.status != 'playing':
        emit('error', {'message': 'Game not found or not playing'})
        return
    
    player = game.players.filter_by(session_id=session_id).first()
    if not player:
        emit('error', {'message': 'Player not found'})
        return
    
    # Check if it's player's turn
    current = game.get_current_player()
    if not current or current.id != player.id:
        emit('error', {'message': "Not your turn"})
        return
    
    from app.game.logic import reveal_card, check_round_end, next_turn
    try:
        reveal_card(game, player, card_index)
    except ValueError as e:
        emit('error', {'message': str(e)})
        return
    
    emit('card_revealed', {
        'player_id': player.id,
        'player_name': player.name
    }, room=code)
    
    # Check if round should end
    if check_round_end(game, player):
        handle_round_end(game, code)
    else:
        # Move to next turn
        next_player = next_turn(game)
        emit('turn_changed', {
            'current_player_id': next_player.id,
            'current_player_name': next_player.name
        }, room=code)
        
        # If next player is a bot, process their turn
        if next_player.is_bot:
            process_bot_turn(game, next_player)
    
    emit('game_state', game.to_dict(include_players=True), room=code)


def handle_round_end(game, code):
    """Handle end of round."""
    from app.game.logic import end_round, check_game_end
    
    end_round(game)
    
    # Build scores data
    scores = []
    for p in game.players.order_by(Player.turn_order).all():
        scores.append({
            'name': p.name,
            'round_score': p.round_score,
            'total_score': p.score,
            'triggered': p.triggered_end
        })
    
    emit('round_ended', {
        'scores': scores
    }, room=code)
    
    if check_game_end(game):
        # Find winner (lowest score)
        players = list(game.players.all())
        winner = min(players, key=lambda p: p.score)
        game.status = 'finished'
        db.session.commit()
        
        emit('game_ended', {
            'winner': winner.name,
            'final_scores': scores
        }, room=code)


@socketio.on('next_round')
def handle_next_round(data):
    """Host starts the next round."""
    code = data.get('code', '').upper()
    session_id = get_session_id()
    
    game = Game.query.filter_by(code=code).first()
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    player = game.players.filter_by(session_id=session_id).first()
    if not player or not player.is_host:
        emit('error', {'message': 'Only the host can start next round'})
        return
    
    # Initialize new round
    from app.game.logic import initialize_game
    game.round_number += 1
    initialize_game(game)
    
    emit('game_state', game.to_dict(include_players=True), room=code)


def process_bot_turn(game, bot):
    """Process a bot's turn with difficulty-based AI."""
    import time
    from app.game.logic import draw_card, place_card, discard_held_card, reveal_card, check_round_end, next_turn
    import random
    
    # Small delay to simulate thinking
    time.sleep(1)
    
    code = game.code
    difficulty = bot.bot_difficulty or 'medium'
    
    cards = bot.get_cards()
    discard_pile = game.get_discard_pile()
    discard_top = discard_pile[-1] if discard_pile else None
    
    # Analyze current hand
    revealed_cards = [(i, c) for i, c in enumerate(cards) if c.get('revealed') and not c.get('eliminated')]
    unrevealed_indices = [i for i, c in enumerate(cards) if not c.get('revealed') and not c.get('eliminated')]
    
    # Calculate average revealed value
    if revealed_cards:
        avg_revealed = sum(c['value'] for i, c in revealed_cards) / len(revealed_cards)
        max_revealed_idx = max(revealed_cards, key=lambda x: x[1]['value'])[0]
        max_revealed_val = cards[max_revealed_idx]['value']
    else:
        avg_revealed = 6  # Assume average
        max_revealed_idx = None
        max_revealed_val = 0
    
    # HARD MODE: Card counting and statistics
    cards_seen = []  # All cards we know about
    if difficulty == 'hard':
        # Count all visible cards (discard pile + all revealed cards)
        cards_seen = list(discard_pile)  # All discarded cards
        
        # Add all revealed cards from all players
        for player in game.players.all():
            player_cards = player.get_cards()
            for c in player_cards:
                if c.get('revealed') and not c.get('eliminated'):
                    cards_seen.append(c['value'])
        
        # Calculate probability distribution of remaining cards
        # Skyjo deck: -2(5), -1(10), 0(15), 1-12(10 each)
        deck_composition = {-2: 5, -1: 10, 0: 15}
        for v in range(1, 13):
            deck_composition[v] = 10
        
        remaining_cards = {}
        for value, count in deck_composition.items():
            seen_count = cards_seen.count(value)
            remaining_cards[value] = max(0, count - seen_count)
        
        total_remaining = sum(remaining_cards.values())
        
        # Calculate expected value of drawing from deck
        if total_remaining > 0:
            expected_draw_value = sum(v * c for v, c in remaining_cards.items()) / total_remaining
        else:
            expected_draw_value = 5
    
    # Decide whether to take from discard or draw pile
    take_from_discard = False
    
    if discard_top is not None:
        if difficulty == 'easy':
            # Easy (old medium): take low cards from discard
            take_from_discard = discard_top <= 2 or (discard_top < max_revealed_val - 2)
            
        elif difficulty == 'medium':
            # Medium (old hard): strategic - take if it improves position
            take_from_discard = (discard_top <= 1) or (discard_top < max_revealed_val - 1) or (discard_top < avg_revealed - 2)
            
            # Check for column elimination opportunity
            for col in range(4):
                col_indices = [col, col + 4, col + 8]
                col_cards = [cards[i] for i in col_indices if i < len(cards)]
                revealed_in_col = [c for c in col_cards if c.get('revealed') and not c.get('eliminated')]
                
                if len(revealed_in_col) == 2 and revealed_in_col[0]['value'] == revealed_in_col[1]['value']:
                    if discard_top == revealed_in_col[0]['value']:
                        take_from_discard = True
                        break
                        
        else:  # hard
            # Hard: Use card counting + analyze opponent hands
            
            # Check column elimination first (highest priority)
            for col in range(4):
                col_indices = [col, col + 4, col + 8]
                col_cards = [cards[i] for i in col_indices if i < len(cards)]
                revealed_in_col = [c for c in col_cards if c.get('revealed') and not c.get('eliminated')]
                
                if len(revealed_in_col) == 2 and revealed_in_col[0]['value'] == revealed_in_col[1]['value']:
                    if discard_top == revealed_in_col[0]['value']:
                        take_from_discard = True
                        break
            
            if not take_from_discard:
                # Compare discard vs expected draw value
                if discard_top <= expected_draw_value - 2:
                    take_from_discard = True
                elif discard_top <= 0:
                    take_from_discard = True
                elif discard_top < max_revealed_val - 1:
                    take_from_discard = True
                    
                # Consider if taking prevents opponent from getting a good card
                # Look at the next player's revealed cards
                players = list(game.players.order_by(Player.turn_order).all())
                bot_idx = next(i for i, p in enumerate(players) if p.id == bot.id)
                prev_player = players[(bot_idx - 1) % len(players)]
                
                if not prev_player.is_bot:
                    prev_cards = prev_player.get_cards()
                    prev_revealed = [(i, c) for i, c in enumerate(prev_cards) if c.get('revealed') and not c.get('eliminated')]
                    
                    # Check if opponent could use this card for column elimination
                    for col in range(4):
                        col_indices = [col, col + 4, col + 8]
                        if all(i < len(prev_cards) for i in col_indices):
                            prev_col_revealed = [prev_cards[i] for i in col_indices if prev_cards[i].get('revealed') and not prev_cards[i].get('eliminated')]
                            if len(prev_col_revealed) == 2:
                                if prev_col_revealed[0]['value'] == prev_col_revealed[1]['value'] == discard_top:
                                    # Opponent could complete a column! Take it to block
                                    take_from_discard = True
                                    break
    
    # Draw card
    try:
        card_value = draw_card(game, bot, from_discard=take_from_discard)
    except Exception as e:
        print(f"Bot draw error: {e}")
        return
    
    emit('card_drawn', {
        'player_id': bot.id,
        'player_name': bot.name,
        'card_value': None,  # Don't show bot's card
        'from_discard': take_from_discard
    }, room=code, namespace='/')
    
    time.sleep(0.5)
    
    # Refresh cards after draw
    cards = bot.get_cards()
    revealed_cards = [(i, c) for i, c in enumerate(cards) if c.get('revealed') and not c.get('eliminated')]
    unrevealed_indices = [i for i, c in enumerate(cards) if not c.get('revealed') and not c.get('eliminated')]
    
    # Decide what to do with the drawn card
    should_place = False
    place_index = None
    
    if difficulty == 'easy':
        # Easy: smarter placement (old medium)
        if card_value <= 2:
            # Very low card - place it for sure
            should_place = True
            if revealed_cards:
                # Replace highest revealed card if it's higher
                high_idx = max(revealed_cards, key=lambda x: x[1]['value'])[0]
                if cards[high_idx]['value'] > card_value:
                    place_index = high_idx
                elif unrevealed_indices:
                    place_index = random.choice(unrevealed_indices)
            elif unrevealed_indices:
                place_index = random.choice(unrevealed_indices)
                
        elif card_value <= 6:
            # Medium card - replace if we have higher
            if revealed_cards:
                high_idx = max(revealed_cards, key=lambda x: x[1]['value'])[0]
                if cards[high_idx]['value'] > card_value + 2:
                    should_place = True
                    place_index = high_idx
            if not should_place and unrevealed_indices and random.random() < 0.4:
                should_place = True
                place_index = random.choice(unrevealed_indices)
                
        else:
            # High card - only replace if we have even higher
            if revealed_cards:
                high_idx = max(revealed_cards, key=lambda x: x[1]['value'])[0]
                if cards[high_idx]['value'] > card_value:
                    should_place = True
                    place_index = high_idx
                    
    elif difficulty == 'medium':
        # Medium: strategic placement (old hard)
        # First check for column elimination
        best_col_match = None
        for col in range(4):
            col_indices = [col, col + 4, col + 8]
            if all(i < len(cards) for i in col_indices):
                col_cards_data = [(i, cards[i]) for i in col_indices]
                revealed_in_col = [(i, c) for i, c in col_cards_data if c.get('revealed') and not c.get('eliminated')]
                unrevealed_in_col = [(i, c) for i, c in col_cards_data if not c.get('revealed') and not c.get('eliminated')]
                
                if len(revealed_in_col) == 2 and len(unrevealed_in_col) == 1:
                    if revealed_in_col[0][1]['value'] == revealed_in_col[1][1]['value'] == card_value:
                        best_col_match = unrevealed_in_col[0][0]
                        break
        
        if best_col_match is not None:
            should_place = True
            place_index = best_col_match
        elif card_value <= 0:
            should_place = True
            if revealed_cards:
                high_idx = max(revealed_cards, key=lambda x: x[1]['value'])[0]
                place_index = high_idx
            elif unrevealed_indices:
                place_index = random.choice(unrevealed_indices)
        elif card_value <= 4:
            should_place = True
            if revealed_cards:
                candidates = [(i, c) for i, c in revealed_cards if c['value'] > card_value]
                if candidates:
                    place_index = max(candidates, key=lambda x: x[1]['value'])[0]
                elif unrevealed_indices:
                    place_index = random.choice(unrevealed_indices)
            elif unrevealed_indices:
                place_index = random.choice(unrevealed_indices)
        else:
            if revealed_cards:
                high_idx = max(revealed_cards, key=lambda x: x[1]['value'])[0]
                if cards[high_idx]['value'] > card_value:
                    should_place = True
                    place_index = high_idx
                    
    else:  # hard
        # Hard: Optimal play with card counting
        
        # Priority 1: Complete column elimination
        best_col_match = None
        for col in range(4):
            col_indices = [col, col + 4, col + 8]
            if all(i < len(cards) for i in col_indices):
                col_cards_data = [(i, cards[i]) for i in col_indices]
                revealed_in_col = [(i, c) for i, c in col_cards_data if c.get('revealed') and not c.get('eliminated')]
                unrevealed_in_col = [(i, c) for i, c in col_cards_data if not c.get('revealed') and not c.get('eliminated')]
                
                if len(revealed_in_col) == 2 and len(unrevealed_in_col) == 1:
                    if revealed_in_col[0][1]['value'] == revealed_in_col[1][1]['value'] == card_value:
                        best_col_match = unrevealed_in_col[0][0]
                        break
        
        if best_col_match is not None:
            should_place = True
            place_index = best_col_match
        else:
            # Priority 2: Use expected value calculations
            # Place if card is better than expected unrevealed value
            # Expected unrevealed value based on remaining deck
            
            if card_value <= 0:
                # Negative/zero always good
                should_place = True
                if revealed_cards:
                    high_idx = max(revealed_cards, key=lambda x: x[1]['value'])[0]
                    place_index = high_idx
                elif unrevealed_indices:
                    # Place on unrevealed that's NOT part of a potential column match
                    place_index = unrevealed_indices[0]
                    
            elif card_value <= expected_draw_value:
                # Card is better than average remaining
                should_place = True
                if revealed_cards:
                    # Replace highest card that's worse than drawn
                    candidates = [(i, c) for i, c in revealed_cards if c['value'] > card_value]
                    if candidates:
                        place_index = max(candidates, key=lambda x: x[1]['value'])[0]
                    elif unrevealed_indices:
                        place_index = random.choice(unrevealed_indices)
                elif unrevealed_indices:
                    place_index = random.choice(unrevealed_indices)
                    
            else:
                # Card is worse than average - only place if we have something worse
                if revealed_cards:
                    high_idx = max(revealed_cards, key=lambda x: x[1]['value'])[0]
                    if cards[high_idx]['value'] > card_value:
                        should_place = True
                        place_index = high_idx
            
            # Priority 3: Consider building towards column elimination
            if not should_place and unrevealed_indices:
                for col in range(4):
                    col_indices = [col, col + 4, col + 8]
                    if all(i < len(cards) for i in col_indices):
                        col_cards_data = [(i, cards[i]) for i in col_indices]
                        revealed_in_col = [(i, c) for i, c in col_cards_data if c.get('revealed') and not c.get('eliminated')]
                        unrevealed_in_col = [i for i, c in col_cards_data if not c.get('revealed') and not c.get('eliminated')]
                        
                        # If 1 card revealed and we have 2 unrevealed, placing matching could start a column
                        if len(revealed_in_col) == 1 and len(unrevealed_in_col) == 2:
                            if revealed_in_col[0][1]['value'] == card_value:
                                # Check if third card likely available
                                if remaining_cards.get(card_value, 0) >= 1:
                                    should_place = True
                                    place_index = unrevealed_in_col[0]
                                    break
    
    # Execute decision
    if should_place and place_index is not None:
        place_card(game, bot, place_index)
        emit('card_placed', {
            'player_id': bot.id,
            'player_name': bot.name
        }, room=code, namespace='/')
    else:
        # Discard and reveal
        discard_held_card(game, bot)
        
        # Choose which card to reveal
        reveal_index = None
        
        if difficulty in ['medium', 'hard'] and unrevealed_indices:
            # Check for columns with 2 matching revealed cards
            for col in range(4):
                col_indices = [col, col + 4, col + 8]
                if all(i < len(cards) for i in col_indices):
                    revealed_in_col = [cards[i] for i in col_indices if cards[i].get('revealed') and not cards[i].get('eliminated')]
                    unrevealed_in_col = [i for i in col_indices if not cards[i].get('revealed') and not cards[i].get('eliminated')]
                    
                    if len(revealed_in_col) == 2 and len(unrevealed_in_col) == 1:
                        if revealed_in_col[0]['value'] == revealed_in_col[1]['value']:
                            reveal_index = unrevealed_in_col[0]
                            break
        
        if reveal_index is None and unrevealed_indices:
            if difficulty == 'hard':
                # Hard: reveal card in column that has best chance of matching
                best_reveal = None
                best_prob = 0
                
                for idx in unrevealed_indices:
                    col = idx % 4
                    col_indices = [col, col + 4, col + 8]
                    revealed_in_col = [cards[i] for i in col_indices if i < len(cards) and cards[i].get('revealed') and not cards[i].get('eliminated')]
                    
                    if len(revealed_in_col) == 1:
                        # Calculate probability of getting matching cards
                        match_val = revealed_in_col[0]['value']
                        prob = remaining_cards.get(match_val, 0) / max(1, total_remaining)
                        if prob > best_prob:
                            best_prob = prob
                            best_reveal = idx
                
                reveal_index = best_reveal if best_reveal is not None else random.choice(unrevealed_indices)
            else:
                reveal_index = random.choice(unrevealed_indices)
        
        if reveal_index is not None:
            reveal_card(game, bot, reveal_index)
            emit('card_revealed', {
                'player_id': bot.id,
                'player_name': bot.name
            }, room=code, namespace='/')
    
    emit('game_state', game.to_dict(include_players=True), room=code, namespace='/')
    
    # Check round end
    if check_round_end(game, bot):
        handle_round_end(game, code)
    else:
        next_player = next_turn(game)
        emit('turn_changed', {
            'current_player_id': next_player.id,
            'current_player_name': next_player.name
        }, room=code, namespace='/')
        
        if next_player.is_bot:
            process_bot_turn(game, next_player)


def broadcast_game_update(game):
    """Broadcast game state to all players in a room."""
    emit('game_state', game.to_dict(include_players=True), 
         room=game.code, namespace='/')
