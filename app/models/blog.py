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
    - Social features (likes, sharing)
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    
    # Social features
    like_count = db.Column(db.Integer, default=0, nullable=False, index=True)
    view_count = db.Column(db.Integer, default=0, nullable=False)
    
    # SEO and sharing
    slug = db.Column(db.String(255), unique=True, nullable=True, index=True)
    meta_description = db.Column(db.Text, nullable=True)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    
    # Table-level constraints and indexes
    __table_args__ = (
        # Composite indexes for common query patterns
        db.Index('idx_post_user_created', 'user_id', 'created_at'),
        db.Index('idx_post_category_created', 'category_id', 'created_at'),
        db.Index('idx_post_likes_created', 'like_count', 'created_at'),
    )
    
    def __init__(self, **kwargs):
        super(Post, self).__init__(**kwargs)
        # Generate slug if not provided
        if not self.slug and self.title:
            self.slug = self.generate_slug(self.title)
    
    def generate_slug(self, title):
        """
        Generate a URL-friendly slug from the post title.
        
        Args:
            title (str): The post title
            
        Returns:
            str: URL-friendly slug
        """
        import re
        import unicodedata
        
        # Normalize unicode characters
        slug = unicodedata.normalize('NFKD', title)
        slug = slug.encode('ascii', 'ignore').decode('ascii')
        
        # Convert to lowercase and replace spaces/special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        
        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while Post.query.filter_by(slug=slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def get_absolute_url(self):
        """Get the absolute URL for this post."""
        from flask import url_for
        return url_for('blog.post_detail', id=self.id, _external=True)
    
    def get_slug_url(self):
        """Get the slug-based URL for this post."""
        from flask import url_for
        if self.slug:
            return url_for('blog.post_by_slug', slug=self.slug, _external=True)
        return self.get_absolute_url()
    
    def get_excerpt(self, length=150):
        """
        Get a truncated excerpt of the post content.
        
        Args:
            length (int): Maximum length of excerpt
            
        Returns:
            str: Truncated content with ellipsis if needed
        """
        if len(self.content) <= length:
            return self.content
        
        # Find the last complete word within the length limit
        excerpt = self.content[:length]
        last_space = excerpt.rfind(' ')
        if last_space > 0:
            excerpt = excerpt[:last_space]
        
        return excerpt + '...'
    
    def get_reading_time(self):
        """
        Estimate reading time in minutes based on content length.
        
        Returns:
            int: Estimated reading time in minutes
        """
        words_per_minute = 200
        word_count = len(self.content.split())
        reading_time = max(1, round(word_count / words_per_minute))
        return reading_time
    
    def is_liked_by(self, user):
        """
        Check if this post is liked by a specific user.
        
        Args:
            user (User): The user to check
            
        Returns:
            bool: True if post is liked by user, False otherwise
        """
        if not user or not user.is_authenticated:
            return False
        
        from app.models.like import PostLike
        return PostLike.is_liked_by(self, user)
    
    def get_social_share_data(self):
        """
        Get data for social media sharing.
        
        Returns:
            dict: Social sharing metadata
        """
        return {
            'title': self.title,
            'description': self.meta_description or self.get_excerpt(160),
            'url': self.get_absolute_url(),
            'image': f"/static/uploads/posts/{self.image_filename}" if self.image_filename else None,
            'author': self.author.full_name,
            'published_time': self.created_at.isoformat(),
            'modified_time': self.updated_at.isoformat() if self.updated_at != self.created_at else None,
            'reading_time': self.get_reading_time()
        }
    
    @classmethod
    def get_trending_posts(cls, days=7, limit=10):
        """
        Get trending posts based on likes and comments in recent days.
        
        Args:
            days (int): Number of days to look back
            limit (int): Maximum number of posts to return
            
        Returns:
            Query: SQLAlchemy query for trending posts
        """
        from datetime import timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return cls.query.filter(
            cls.created_at >= cutoff_date
        ).order_by(
            (cls.like_count * 2 + func.count(Comment.id)).desc()
        ).join(Comment, Comment.post_id == cls.id, isouter=True).group_by(cls.id).limit(limit)
    
    @classmethod
    def get_popular_posts(cls, limit=10):
        """
        Get most popular posts by like count.
        
        Args:
            limit (int): Maximum number of posts to return
            
        Returns:
            Query: SQLAlchemy query for popular posts
        """
        return cls.query.order_by(cls.like_count.desc()).limit(limit)
    
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