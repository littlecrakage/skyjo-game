"""Gunicorn configuration for production deployment."""
import os

# Binding
bind = f"0.0.0.0:{os.environ.get('PORT', 10000)}"

# Workers
workers = int(os.environ.get('GUNICORN_WORKERS', 4))
worker_class = 'eventlet'  # Required for WebSocket support
worker_connections = 1000

# Timeout
timeout = 120
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Process naming
proc_name = 'skyjo_game'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = None
# certfile = None
