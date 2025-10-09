"""
Like Model

This module contains the PostLike model for tracking user likes on posts.
It demonstrates many-to-many relationships and social interaction patterns.
"""

from datetime import datetime
from sqlalchemy import and_
from app.extensions import db
from app.models.base import BaseModel


class PostLike(BaseModel):
    """
    PostLike model for tracking user likes on posts.
    
    This model demonstrates:
    - Many-to-many relationships between users and posts
    - Social interaction tracking
    - Composite unique constraints
    - Class methods for like management
    - Performance optimization with indexes
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, index=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('liked_posts', lazy='dynamic', cascade='all, delete-orphan'))
    post = db.relationship('Post', backref=db.backref('likes', lazy='dynamic', cascade='all, delete-orphan'))
    
    # Table-level constraints and indexes
    __table_args__ = (
        # Ensure a user can't like the same post twice
        db.UniqueConstraint('user_id', 'post_id', name='unique_user_post_like'),
        
        # Composite indexes for common query patterns
        db.Index('idx_like_user_created', 'user_id', 'created_at'),
        db.Index('idx_like_post_created', 'post_id', 'created_at'),
    )
    
    @classmethod
    def like_post(cls, user, post):
        """
        Create a like relationship between a user and post.
        
        Args:
            user (User): The user who is liking
            post (Post): The post being liked
            
        Returns:
            PostLike or None: The PostLike instance if successful, None if already liked
        """
        # Check if relationship already exists
        if cls.is_liked_by(post, user):
            return None
        
        # Create new like relationship
        like = cls(user_id=user.id, post_id=post.id)
        db.session.add(like)
        
        # Update post like count (denormalized for performance)
        post.like_count = post.likes.count() + 1
        
        return like
    
    @classmethod
    def unlike_post(cls, user, post):
        """
        Remove a like relationship between a user and post.
        
        Args:
            user (User): The user who is unliking
            post (Post): The post being unliked
            
        Returns:
            bool: True if unlike was successful, False if not liked
        """
        like = cls.query.filter_by(
            user_id=user.id,
            post_id=post.id
        ).first()
        
        if like:
            db.session.delete(like)
            
            # Update post like count (denormalized for performance)
            post.like_count = max(0, post.likes.count() - 1)
            
            db.session.commit()
            return True
        
        return False
    
    @classmethod
    def is_liked_by(cls, post, user):
        """
        Check if a post is liked by a specific user.
        
        Args:
            post (Post): The post to check
            user (User): The user to check
            
        Returns:
            bool: True if post is liked by user, False otherwise
        """
        return cls.query.filter_by(
            user_id=user.id,
            post_id=post.id
        ).first() is not None
    
    @classmethod
    def get_post_likes(cls, post, limit=None):
        """
        Get all users who liked a specific post.
        
        Args:
            post (Post): The post whose likes to get
            limit (int, optional): Maximum number of likes to return
            
        Returns:
            Query: SQLAlchemy query for users who liked the post
        """
        from app.models.user import User
        
        query = User.query.join(
            cls, cls.user_id == User.id
        ).filter(
            cls.post_id == post.id
        ).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query
    
    @classmethod
    def get_user_likes(cls, user, limit=None):
        """
        Get all posts liked by a specific user.
        
        Args:
            user (User): The user whose likes to get
            limit (int, optional): Maximum number of likes to return
            
        Returns:
            Query: SQLAlchemy query for posts liked by the user
        """
        from app.models.blog import Post
        
        query = Post.query.join(
            cls, cls.post_id == Post.id
        ).filter(
            cls.user_id == user.id
        ).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query
    
    @classmethod
    def get_popular_posts(cls, days=7, limit=10):
        """
        Get posts with the most likes in a given time period.
        
        Args:
            days (int): Number of days to look back
            limit (int): Maximum number of posts to return
            
        Returns:
            Query: SQLAlchemy query for popular posts
        """
        from app.models.blog import Post
        from sqlalchemy import func
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.session.query(
            Post,
            func.count(cls.id).label('like_count')
        ).join(
            cls, cls.post_id == Post.id
        ).filter(
            cls.created_at >= cutoff_date
        ).group_by(Post.id).order_by(
            func.count(cls.id).desc()
        ).limit(limit)
    
    @classmethod
    def get_recent_likes(cls, user, limit=10):
        """
        Get recent likes by users that the specified user follows.
        
        Args:
            user (User): The user whose feed to generate
            limit (int): Maximum number of likes to return
            
        Returns:
            Query: SQLAlchemy query for recent likes from followed users
        """
        from app.models.follow import Follow
        from app.models.blog import Post
        from app.models.user import User
        
        # Get users that the current user follows
        followed_users = db.session.query(Follow.followed_id).filter_by(follower_id=user.id)
        
        return db.session.query(cls, Post, User).join(
            Post, cls.post_id == Post.id
        ).join(
            User, cls.user_id == User.id
        ).filter(
            cls.user_id.in_(followed_users)
        ).order_by(cls.created_at.desc()).limit(limit)
    
    def __repr__(self):
        """String representation of the PostLike object."""
        return f'<PostLike user_id={self.user_id} post_id={self.post_id}>'