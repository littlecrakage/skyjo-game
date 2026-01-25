import random
import string
from datetime import datetime
from app import db


class Game(db.Model):
    """Represents a Skyjo game room."""
    __tablename__ = 'games'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(6), unique=True, nullable=False, index=True)
    
    # Game settings (set by host)
    max_players = db.Column(db.Integer, default=4)  # 2-8 players
    is_public = db.Column(db.Boolean, default=True)  # Visible in lobby list
    turn_timer = db.Column(db.Integer, default=60)  # Seconds per turn (0 = unlimited)
    finish_round = db.Column(db.Boolean, default=True)  # True = finish round, False = stop immediately
    
    # Game state
    status = db.Column(db.String(20), default='waiting')  # waiting, playing, finished
    current_player_index = db.Column(db.Integer, default=0)
    round_number = db.Column(db.Integer, default=1)
    
    # Card piles (stored as JSON strings)
    draw_pile = db.Column(db.Text, default='[]')  # JSON array of card values
    discard_pile = db.Column(db.Text, default='[]')  # JSON array of card values
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    players = db.relationship('Player', backref='game', lazy='dynamic', cascade='all, delete-orphan')
    
    @staticmethod
    def generate_code():
        """Generate a unique 6-character room code."""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Game.query.filter_by(code=code).first():
                return code
    
    def get_draw_pile(self):
        """Get draw pile as a list."""
        import json
        return json.loads(self.draw_pile) if self.draw_pile else []
    
    def set_draw_pile(self, cards):
        """Set draw pile from a list."""
        import json
        self.draw_pile = json.dumps(cards)
    
    def get_discard_pile(self):
        """Get discard pile as a list."""
        import json
        return json.loads(self.discard_pile) if self.discard_pile else []
    
    def set_discard_pile(self, cards):
        """Set discard pile from a list."""
        import json
        self.discard_pile = json.dumps(cards)
    
    def player_count(self):
        """Get current number of players."""
        return self.players.count()
    
    def is_full(self):
        """Check if game is full."""
        return self.player_count() >= self.max_players
    
    def get_host(self):
        """Get the host player."""
        return self.players.filter_by(is_host=True).first()
    
    def get_current_player(self):
        """Get the player whose turn it is."""
        players = self.players.order_by(Player.turn_order).all()
        if players and 0 <= self.current_player_index < len(players):
            return players[self.current_player_index]
        return None
    
    def to_dict(self, include_players=False):
        """Convert to dictionary for JSON response."""
        data = {
            'id': self.id,
            'code': self.code,
            'max_players': self.max_players,
            'is_public': self.is_public,
            'turn_timer': self.turn_timer,
            'finish_round': self.finish_round,
            'status': self.status,
            'current_player_index': self.current_player_index,
            'round_number': self.round_number,
            'player_count': self.player_count(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_players:
            data['players'] = [p.to_dict() for p in self.players.order_by(Player.turn_order).all()]
        return data
    
    def __repr__(self):
        return f'<Game {self.code}>'


class Player(db.Model):
    """Represents a player in a Skyjo game."""
    __tablename__ = 'players'
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    
    # Player identity
    name = db.Column(db.String(50), nullable=False)
    session_id = db.Column(db.String(100), nullable=True)  # For reconnection (guests)
    
    # Player role
    is_host = db.Column(db.Boolean, default=False)
    is_bot = db.Column(db.Boolean, default=False)
    bot_difficulty = db.Column(db.String(20), nullable=True)  # easy, medium, hard
    
    # Game state
    turn_order = db.Column(db.Integer, default=0)
    score = db.Column(db.Integer, default=0)  # Total score across rounds
    round_score = db.Column(db.Integer, default=0)  # Score for current round
    is_connected = db.Column(db.Boolean, default=True)
    
    # Cards (4 columns x 3 rows = 12 cards, stored as JSON)
    # Format: [{"value": 5, "revealed": false}, ...]
    cards = db.Column(db.Text, default='[]')
    
    # The card player is currently holding (from draw or discard pile)
    held_card = db.Column(db.Integer, nullable=True)
    
    # Did this player trigger the end of the round?
    triggered_end = db.Column(db.Boolean, default=False)
    
    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_cards(self):
        """Get cards as a list of dicts."""
        import json
        return json.loads(self.cards) if self.cards else []
    
    def set_cards(self, cards):
        """Set cards from a list of dicts."""
        import json
        self.cards = json.dumps(cards)
    
    def revealed_count(self):
        """Count how many cards are revealed."""
        return sum(1 for card in self.get_cards() if card.get('revealed', False))
    
    def all_revealed(self):
        """Check if all cards are revealed."""
        cards = self.get_cards()
        return len(cards) > 0 and all(card.get('revealed', False) for card in cards)
    
    def calculate_score(self):
        """Calculate score from revealed cards."""
        return sum(card['value'] for card in self.get_cards() if card.get('revealed', False))
    
    def to_dict(self, show_hidden=False):
        """Convert to dictionary for JSON response.
        
        Args:
            show_hidden: If True, show all card values. If False, hide unrevealed cards.
        """
        cards = self.get_cards()
        
        # For display, hide unrevealed card values unless show_hidden is True
        if not show_hidden:
            cards = [
                {'value': card['value'], 'revealed': True} if card.get('revealed') 
                else {'value': None, 'revealed': False}
                for card in cards
            ]
        
        return {
            'id': self.id,
            'name': self.name,
            'is_host': self.is_host,
            'is_bot': self.is_bot,
            'bot_difficulty': self.bot_difficulty,
            'turn_order': self.turn_order,
            'score': self.score,
            'round_score': self.round_score,
            'is_connected': self.is_connected,
            'cards': cards,
            'held_card': self.held_card,
            'triggered_end': self.triggered_end,
            'revealed_count': self.revealed_count()
        }
    
    def __repr__(self):
        return f'<Player {self.name} in Game {self.game_id}>'
