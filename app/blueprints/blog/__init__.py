"""
Blog Blueprint

This blueprint handles all blog-related functionality including
post creation, viewing, commenting, and category management.
"""

from flask import Blueprint

# Create the blog blueprint
bp = Blueprint('blog', __name__)

# Import routes to register them with the blueprint
from app.blueprints.blog import routes