"""
Database Models Package

This package contains all SQLAlchemy database models for the Flask blog application.
Models are organized into separate files for better maintainability and to demonstrate
proper code organization in larger Flask applications.

The package includes:
- BaseModel: Abstract base class with common functionality
- User: User authentication and profile management
- Post, Comment, Category: Blog content models
- Role, Permission: Role-based access control models
- Follow: User relationship tracking
- PostView, Notification: Analytics and notification models
"""

# Import base model first
from app.models.base import BaseModel

# Import all models here for easy access
from app.models.user import User
from app.models.blog import Post, Comment, Category
from app.models.role import Role, Permission
from app.models.follow import Follow
from app.models.analytics import PostView, Notification

# Make models available at package level
__all__ = [
    'BaseModel', 'User', 'Post', 'Comment', 'Category', 
    'Role', 'Permission', 'Follow', 'PostView', 'Notification'
]