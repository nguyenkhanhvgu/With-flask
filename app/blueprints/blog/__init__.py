"""
Blog Blueprint

This blueprint handles all blog-related functionality including:
- Post CRUD operations
- Comment management
- Category browsing
- Search functionality
- Pagination

This demonstrates Flask blueprint organization and modular design.
"""

from flask import Blueprint

# Create the blog blueprint
bp = Blueprint('blog', __name__, url_prefix='/blog')

# Import routes to register them with the blueprint
from app.blueprints.blog import routes