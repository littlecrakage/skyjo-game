import os
from app import create_app, socketio

# Get config from environment variable, default to development
config_name = os.environ.get('FLASK_CONFIG') or 'development'
app = create_app(config_name)

if __name__ == '__main__':
    # Run with SocketIO support
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
