"""
Authentication Blueprint

This blueprint handles all authentication-related functionality including
user registration, login, logout, and profile management.
"""

from flask import Blueprint

# Create the auth blueprint
bp = Blueprint('auth', __name__)

# Import routes to register them with the blueprint
from app.blueprints.auth import routes