import os
from app import app, socketio

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 80))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)
