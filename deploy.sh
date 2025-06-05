
#!/bin/bash

echo "🚀 Deploying CarterHub..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install flask flask-socketio flask-sqlalchemy gunicorn

# Run database migrations (if needed)
echo "🗄️ Setting up database..."
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database tables created successfully!')
"

# Start the production server on port 80
echo "🌐 Starting CarterHub on port 80..."
gunicorn --bind 0.0.0.0:80 --workers 4 --timeout 120 main:app
