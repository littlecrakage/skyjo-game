from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from config import config
from apscheduler.schedulers.background import BackgroundScheduler
from app.routes.webhook import webhook_bp

# Initialize extensions (without app)
db = SQLAlchemy()
socketio = SocketIO()
scheduler = BackgroundScheduler()


def create_app(config_name='default'):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.game import game_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(game_bp)
    app.register_blueprint(webhook_bp)
    
    # Import socket events to register them
    from app.routes import socket_events  # noqa
    
    # Import models so they are registered with SQLAlchemy
    from app.models import Game, Player
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Start the scheduler with cleanup job if not already running
        if not scheduler.running:
            from app.routes.socket_events import cleanup_empty_games
            scheduler.add_job(cleanup_empty_games, 'interval', minutes=20, id='cleanup_games', replace_existing=True, args=[app])
            scheduler.start()
            print("[CLEANUP] Scheduler started with cleanup job (runs every 20 minutes)")
    
    return app
