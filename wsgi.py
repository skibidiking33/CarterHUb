
import sys
import os

# Add your project directory to Python path if needed
# sys.path.insert(0, '/home/yourusername/mysite/')

from app import app

# WSGI callable
application = app

if __name__ == "__main__":
    application.run()
