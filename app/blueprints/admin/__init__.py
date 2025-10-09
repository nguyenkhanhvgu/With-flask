"""
Admin Blueprint

This blueprint handles all administrative functionality including
user management, content moderation, and site analytics.
"""

from flask import Blueprint

# Create the admin blueprint
bp = Blueprint('admin', __name__)

# Import routes to register them with the blueprint
from app.blueprints.admin import routes, cache_routes