"""
Flask Extensions Initialization

This module demonstrates the proper way to initialize Flask extensions
using the application factory pattern. Extensions are created here but
not bound to any specific application instance, allowing them to be
initialized later with different app configurations.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO
from flask_caching import Cache

# Initialize extensions
# These are created without being bound to a specific app instance
# They will be initialized with the app in the create_app() factory function

# Database extension for SQLAlchemy ORM
db = SQLAlchemy()

# Database migration extension
migrate = Migrate()

# User session management extension
login_manager = LoginManager()

# Email sending extension
mail = Mail()

# WebSocket support extension
socketio = SocketIO()

# Caching extension for performance optimization
cache = Cache()

# Note: This pattern allows extensions to be configured before the app is created
# and enables easy testing with different configurations