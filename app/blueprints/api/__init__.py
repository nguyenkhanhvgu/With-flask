"""
API Blueprint

This blueprint handles all REST API functionality for external
access to the blog application data and functionality.
"""

from flask import Blueprint

# Create the API blueprint
bp = Blueprint('api', __name__)

# Import routes to register them with the blueprint
from app.blueprints.api import routes