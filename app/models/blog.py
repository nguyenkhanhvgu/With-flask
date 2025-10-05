"""
Blog Models

This module contains models for blog functionality including posts,
comments, and categories. It demonstrates SQLAlchemy relationships
and model organization patterns.
"""

from datetime import datetime
from app.extensions import db
from app.models.base import BaseModel


class Category(BaseModel):
    """
    Category model for organizing posts.
    
    This model demonstrates:
    - Simple model definition with base class inheritance
    - One-to-many relationships
    - Model methods and properties
    - Common functionality through BaseModel
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    posts = db.relationship('Post', backref='category', lazy=True)
    
    def __repr__(self):
        """String representation of the Category object."""
        return f'<Category {self.name}>'


class Post(BaseModel):
    """
    Blog post model.
    
    This model demonstrates:
    - Complex model with multiple relationships
    - Foreign key relationships
    - Automatic timestamp handling through BaseModel
    - File upload integration
    - Model inheritance patterns
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        """String representation of the Post object."""
        return f'<Post {self.title}>'


class Comment(BaseModel):
    """
    Comment model for post feedback.
    
    This model demonstrates:
    - Simple relationship model with base class inheritance
    - Multiple foreign key relationships
    - Cascade deletion handling
    - Automatic timestamp management through BaseModel
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    content = db.Column(db.Text, nullable=False)
    
    # Foreign keys
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        """String representation of the Comment object."""
        return f'<Comment {self.id}>'