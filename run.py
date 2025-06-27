# run.py - Application Runner
import os
from app import create_app, socketio

config_name = os.getenv('FLASK_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    socketio.run(
        app,
        debug=app.config.get('DEBUG', False),
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )