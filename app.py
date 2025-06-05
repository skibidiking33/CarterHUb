import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
socketio = SocketIO()

# Create the app
app = Flask(__name__)
app.secret_key = "carterhub_development_secret_key_very_secure_2024"
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///carterhub.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)
socketio.init_app(app, cors_allowed_origins="*")

with app.app_context():
    # Import models and routes
    import models
    import routes
    
    # Create all database tables
    db.create_all()
    
    # Create default admin user if it doesn't exist
    admin_user = models.Admin.query.filter_by(username='admin').first()
    if not admin_user:
        from werkzeug.security import generate_password_hash
        admin = models.Admin(
            username='admin',
            password_hash=generate_password_hash('admin123')
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin created: username=admin, password=admin123")
    
    # Create default categories if they don't exist
    if models.Category.query.count() == 0:
        default_categories = [
            {
                'title': 'Action Games',
                'description': 'Fast-paced action and adventure games',
                'game_url': 'https://scratch.mit.edu/projects/embed/104295354/',
                'is_chat': False
            },
            {
                'title': 'Puzzle Games',
                'description': 'Brain teasers and puzzle challenges',
                'game_url': 'https://scratch.mit.edu/projects/embed/287880715/',
                'is_chat': False
            },
            {
                'title': 'CarterHub Chat',
                'description': 'Connect and chat with your classmates',
                'game_url': '',
                'is_chat': True
            },
            {
                'title': 'Educational Games',
                'description': 'Learn while you play with educational content',
                'game_url': 'https://scratch.mit.edu/projects/embed/276887974/',
                'is_chat': False
            }
        ]
        
        for cat_data in default_categories:
            category = models.Category(**cat_data)
            db.session.add(category)
        
        db.session.commit()
        print("Default categories created")

# WSGI applications don't need the if __name__ == '__main__' block
# The WSGI server will import and use the 'app' object directly
