"""
Skyjo game logic - deck creation, dealing, scoring, etc.
"""
import random
from datetime import datetime
from app import db
from app.models.game import Player


# Skyjo deck composition:
# -2: 5 cards
# -1: 10 cards
# 0: 15 cards
# 1-12: 10 cards each
DECK_COMPOSITION = {
    -2: 5,
    -1: 10,
    0: 15,
    1: 10,
    2: 10,
    3: 10,
    4: 10,
    5: 10,
    6: 10,
    7: 10,
    8: 10,
    9: 10,
    10: 10,
    11: 10,
    12: 10,
}


def create_deck():
    """Create a full Skyjo deck (150 cards)."""
    deck = []
    for value, count in DECK_COMPOSITION.items():
        deck.extend([value] * count)
    return deck


def shuffle_deck(deck):
    """Shuffle the deck in place and return it."""
    random.shuffle(deck)
    return deck


def initialize_game(game):
    """
    Initialize the game:
    - Create and shuffle deck
    - Deal 12 cards to each player (4 columns x 3 rows)
    - Each player reveals 2 cards initially
    - Put one card in discard pile
    - Set game status to 'playing'
    - Player with highest revealed total starts
    """
    # Create and shuffle deck
    deck = shuffle_deck(create_deck())
    
    # Deal cards to each player
    players = list(game.players.order_by(Player.turn_order).all())
    
    for player in players:
        # Deal 12 cards (all face down initially)
        player_cards = []
        for _ in range(12):
            card_value = deck.pop()
            player_cards.append({
                'value': card_value,
                'revealed': False
            })
        player.set_cards(player_cards)
        player.held_card = None
        player.round_score = 0
        player.triggered_end = False
        
        # Bots automatically reveal 2 random cards
        if player.is_bot:
            reveal_random_initial_cards(player)
    
    # Put top card in discard pile
    discard_card = deck.pop()
    game.set_discard_pile([discard_card])
    
    # Save remaining deck as draw pile
    game.set_draw_pile(deck)
    
    # Update game status
    game.status = 'playing'
    game.started_at = datetime.utcnow()
    
    # Determine starting player (highest revealed card total)
    # For now, set to 0 - will be updated when all humans reveal their cards
    # Bots have already revealed, so if all players are bots or have revealed, set it now
    game.current_player_index = determine_starting_player(game)
    
    db.session.commit()
    
    return game


def determine_starting_player(game):
    """
    Determine which player starts based on highest revealed card total.
    Returns the turn_order index of the starting player.
    """
    players = list(game.players.order_by(Player.turn_order).all())
    
    highest_total = -100  # Cards can be negative
    starting_index = 0
    
    for i, player in enumerate(players):
        # Calculate sum of revealed cards
        cards = player.get_cards()
        revealed_total = sum(c['value'] for c in cards if c.get('revealed', False))
        revealed_count = sum(1 for c in cards if c.get('revealed', False))
        
        # Only consider players who have revealed their 2 cards
        if revealed_count >= 2:
            if revealed_total > highest_total:
                highest_total = revealed_total
                starting_index = i
    
    return starting_index


def reveal_random_initial_cards(player):
    """Reveal 2 random cards for a bot player."""
    import random
    cards = player.get_cards()
    
    # Pick 2 random indices to reveal
    indices = random.sample(range(len(cards)), 2)
    for idx in indices:
        cards[idx]['revealed'] = True
    
    player.set_cards(cards)


def reveal_initial_cards(game, player, card_indices):
    """
    Player reveals 2 cards at the start of the game.
    card_indices: list of 2 indices (0-11) for cards to reveal
    """
    if len(card_indices) != 2:
        raise ValueError("Must reveal exactly 2 cards")
    
    cards = player.get_cards()
    
    for idx in card_indices:
        if 0 <= idx < len(cards):
            cards[idx]['revealed'] = True
    
    player.set_cards(cards)
    db.session.commit()
    
    return cards


def draw_card(game, player, from_discard=False):
    """
    Player draws a card from draw pile or takes from discard pile.
    Returns the card value.
    """
    if from_discard:
        discard = game.get_discard_pile()
        if not discard:
            raise ValueError("Discard pile is empty")
        card = discard.pop()
        game.set_discard_pile(discard)
    else:
        draw = game.get_draw_pile()
        if not draw:
            # Reshuffle discard pile into draw pile (except top card)
            discard = game.get_discard_pile()
            if len(discard) <= 1:
                raise ValueError("No cards to draw")
            top_card = discard.pop()
            draw = shuffle_deck(discard)
            game.set_draw_pile(draw)
            game.set_discard_pile([top_card])
            draw = game.get_draw_pile()
        card = draw.pop()
        game.set_draw_pile(draw)
    
    player.held_card = card
    db.session.commit()
    
    return card


def place_card(game, player, card_index):
    """
    Player places held card at a position, discarding the card that was there.
    """
    if player.held_card is None:
        raise ValueError("No card in hand")
    
    cards = player.get_cards()
    
    if not (0 <= card_index < len(cards)):
        raise ValueError("Invalid card position")
    
    # Swap cards
    old_card = cards[card_index]['value']
    cards[card_index] = {
        'value': player.held_card,
        'revealed': True
    }
    
    # Add old card to discard pile
    discard = game.get_discard_pile()
    discard.append(old_card)
    game.set_discard_pile(discard)
    
    player.set_cards(cards)
    player.held_card = None
    
    db.session.commit()
    
    # Check for column elimination
    check_column_elimination(game, player)
    
    return cards


def discard_held_card(game, player):
    """
    Player discards the held card (drawn from draw pile) and must reveal a card.
    """
    if player.held_card is None:
        raise ValueError("No card in hand")
    
    # Add to discard pile
    discard = game.get_discard_pile()
    discard.append(player.held_card)
    game.set_discard_pile(discard)
    
    player.held_card = None
    db.session.commit()


def reveal_card(game, player, card_index):
    """
    Player reveals a face-down card (after discarding drawn card).
    """
    cards = player.get_cards()
    
    if not (0 <= card_index < len(cards)):
        raise ValueError("Invalid card position")
    
    if cards[card_index]['revealed']:
        raise ValueError("Card is already revealed")
    
    cards[card_index]['revealed'] = True
    player.set_cards(cards)
    
    db.session.commit()
    
    # Check for column elimination
    check_column_elimination(game, player)
    
    return cards


def check_column_elimination(game, player):
    """
    Check if any column has 3 identical revealed cards.
    If so, mark those cards as eliminated (they don't count in score).
    
    Grid layout (4 columns x 3 rows):
    0  1  2  3
    4  5  6  7
    8  9  10 11
    
    Column 0: indices 0, 4, 8
    Column 1: indices 1, 5, 9
    Column 2: indices 2, 6, 10
    Column 3: indices 3, 7, 11
    """
    cards = player.get_cards()
    
    columns_eliminated = []
    
    for col in range(4):
        # Column indices: col, col+4, col+8
        col_indices = [col, col + 4, col + 8]
        
        # Skip if any index is out of range
        if any(i >= len(cards) for i in col_indices):
            continue
        
        # Skip if any card in this column is already eliminated
        if any(cards[i].get('eliminated', False) for i in col_indices):
            continue
        
        col_cards = [cards[i] for i in col_indices]
        
        # Check if all 3 cards are revealed
        if not all(c.get('revealed', False) for c in col_cards):
            continue
        
        # Check if all same value
        values = [c['value'] for c in col_cards]
        if values[0] == values[1] == values[2]:
            # Mark cards as eliminated
            for i in col_indices:
                cards[i]['eliminated'] = True
            columns_eliminated.append(col)
            
            # Add cards to discard pile
            discard = game.get_discard_pile()
            for i in col_indices:
                discard.append(cards[i]['value'])
            game.set_discard_pile(discard)
    
    if columns_eliminated:
        player.set_cards(cards)
        db.session.commit()
    
    return len(columns_eliminated) > 0


def calculate_player_score(player):
    """Calculate the score for a player's current cards (excluding eliminated)."""
    cards = player.get_cards()
    return sum(
        card['value'] for card in cards 
        if card.get('revealed', False) and not card.get('eliminated', False)
    )


def check_round_end(game, player):
    """
    Check if the round should end.
    Returns True if this player revealed all their cards.
    """
    if player.all_revealed():
        player.triggered_end = True
        db.session.commit()
        return True
    return False


def end_round(game):
    """
    End the round and calculate scores.
    """
    players = list(game.players.all())
    
    # Find who triggered the end
    trigger_player = next((p for p in players if p.triggered_end), None)
    
    # Calculate scores for all players (reveal all remaining cards first)
    for player in players:
        cards = player.get_cards()
        # Reveal all non-eliminated cards
        for card in cards:
            if not card.get('eliminated', False):
                card['revealed'] = True
        player.set_cards(cards)
        
        # Check for any new column eliminations after revealing all
        check_column_elimination(game, player)
    
    db.session.commit()
    
    # Now calculate final scores (after all eliminations)
    for player in players:
        # Calculate round score (only non-eliminated cards)
        round_score = calculate_player_score(player)
        
        # Penalty: if trigger player doesn't have lowest score, double their score
        if trigger_player and player.id == trigger_player.id:
            other_scores = [calculate_player_score(p) for p in players if p.id != player.id]
            if other_scores and round_score >= min(other_scores):
                round_score *= 2
        
        player.round_score = round_score
        player.score += round_score
    
    db.session.commit()


def next_turn(game):
    """Move to the next player's turn."""
    players = list(game.players.order_by(Player.turn_order).all())
    game.current_player_index = (game.current_player_index + 1) % len(players)
    db.session.commit()
    return game.get_current_player()


def check_game_end(game):
    """
    Check if the game should end (a player reached 100+ points).
    """
    for player in game.players:
        if player.score >= 100:
            return True
    return False
