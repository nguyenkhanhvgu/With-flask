"""
Main Blueprint

This blueprint handles the main application routes including the home page,
about page, contact page, and other general functionality that doesn't fit
into more specific blueprints.
"""

from flask import Blueprint

# Create the main blueprint
bp = Blueprint('main', __name__)

# Import routes to register them with the blueprint
from app.blueprints.main import routes