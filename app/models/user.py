"""
User Model

This module contains the User model for authentication and user management.
It demonstrates SQLAlchemy model patterns and Flask-Login integration.
"""

from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, and_
from app.extensions import db
from app.models.base import BaseModel


class User(BaseModel, UserMixin):
    """
    User model for blog authors and commenters.
    
    This model demonstrates:
    - SQLAlchemy model definition with base class inheritance
    - Flask-Login integration with UserMixin
    - Password hashing and verification
    - Model relationships including self-referential relationships
    - Hybrid properties and class methods
    - Performance optimization with indexes
    - Role-based access control
    - Common model functionality through BaseModel
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_filename = db.Column(db.String(255), nullable=True, default='default-avatar.png')
    
    # Enhanced fields for advanced features
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    email_confirmed = db.Column(db.Boolean, default=False, nullable=False)
    email_confirmation_token = db.Column(db.String(128))
    password_reset_token = db.Column(db.String(128))
    password_reset_expires = db.Column(db.DateTime)
    
    # Role-based permissions
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), index=True)
    
    # Legacy admin field (kept for backward compatibility)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Bio and profile information
    bio = db.Column(db.Text)
    location = db.Column(db.String(128))
    website = db.Column(db.String(256))
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')
    
    # Self-referential relationships for following system
    followers = db.relationship('Follow', 
                               foreign_keys='Follow.followed_id',
                               backref=db.backref('followed', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    
    following = db.relationship('Follow',
                               foreign_keys='Follow.follower_id', 
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               cascade='all, delete-orphan')
    
    # Table-level constraints and indexes for performance optimization
    __table_args__ = (
        # Composite indexes for common query patterns
        # This index optimizes queries filtering by active status and ordering by last_seen
        db.Index('idx_user_active_last_seen', 'is_active', 'last_seen'),
        
        # This index optimizes role-based queries with active status filtering
        db.Index('idx_user_role_active', 'role_id', 'is_active'),
        
        # This index optimizes queries for confirmed and active users
        db.Index('idx_user_email_confirmed', 'email_confirmed', 'is_active'),
        
        # Partial indexes for performance (PostgreSQL specific, gracefully ignored by other DBs)
        # These indexes only include rows that match the WHERE condition, saving space
        db.Index('idx_user_active_users', 'username', postgresql_where=db.text('is_active = true')),
        db.Index('idx_user_confirmed_users', 'email', postgresql_where=db.text('email_confirmed = true')),
    )
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        # Assign default role if no role is specified and tables exist
        if self.role is None:
            try:
                from app.models.role import Role
                self.role = Role.get_default_role()
            except Exception:
                # Tables might not exist yet (during migrations or testing)
                pass
    
    def set_password(self, password):
        """
        Hash and set the user's password.
        
        Args:
            password (str): The plain text password to hash
            
        This method demonstrates secure password handling using Werkzeug's
        password hashing utilities.
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Check if the provided password matches the hash.
        
        Args:
            password (str): The plain text password to verify
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """
        Required by Flask-Login to get the user ID.
        
        Returns:
            str: The user ID as a string
        """
        return str(self.id)
    
    # Hybrid properties for learning SQLAlchemy patterns
    @hybrid_property
    def full_name(self):
        """
        Get the user's full name.
        
        Returns:
            str: The full name or username if names are not set
            
        This demonstrates hybrid properties that work both in Python
        and in SQL queries.
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.username
    
    @full_name.expression
    def full_name(cls):
        """SQL expression for full_name hybrid property."""
        return func.coalesce(
            func.concat(cls.first_name, ' ', cls.last_name),
            cls.first_name,
            cls.username
        )
    
    @hybrid_property
    def follower_count(self):
        """
        Get the number of followers.
        
        Returns:
            int: Number of users following this user
        """
        return self.followers.count()
    
    @follower_count.expression
    def follower_count(cls):
        """SQL expression for follower_count hybrid property."""
        from app.models.follow import Follow
        return (db.session.query(func.count(Follow.id))
                .filter(Follow.followed_id == cls.id)
                .scalar_subquery())
    
    @hybrid_property
    def following_count(self):
        """
        Get the number of users this user is following.
        
        Returns:
            int: Number of users this user is following
        """
        return self.following.count()
    
    @following_count.expression
    def following_count(cls):
        """SQL expression for following_count hybrid property."""
        from app.models.follow import Follow
        return (db.session.query(func.count(Follow.id))
                .filter(Follow.follower_id == cls.id)
                .scalar_subquery())
    
    @hybrid_property
    def post_count(self):
        """
        Get the number of posts by this user.
        
        Returns:
            int: Number of posts authored by this user
        """
        return len(self.posts)
    
    @post_count.expression
    def post_count(cls):
        """SQL expression for post_count hybrid property."""
        from app.models.blog import Post
        return (db.session.query(func.count(Post.id))
                .filter(Post.user_id == cls.id)
                .scalar_subquery())
    
    # Following system methods
    def follow(self, user):
        """
        Follow another user.
        
        Args:
            user (User): The user to follow
            
        Returns:
            bool: True if follow was successful, False if already following
        """
        from app.models.follow import Follow
        if not self.is_following(user):
            follow = Follow.follow(self, user)
            if follow:
                db.session.add(follow)
                return True
        return False
    
    def unfollow(self, user):
        """
        Unfollow a user.
        
        Args:
            user (User): The user to unfollow
            
        Returns:
            bool: True if unfollow was successful, False if not following
        """
        from app.models.follow import Follow
        return Follow.unfollow(self, user)
    
    def is_following(self, user):
        """
        Check if this user is following another user.
        
        Args:
            user (User): The user to check
            
        Returns:
            bool: True if following, False otherwise
        """
        from app.models.follow import Follow
        return Follow.is_following(self, user)
    
    def is_followed_by(self, user):
        """
        Check if this user is followed by another user.
        
        Args:
            user (User): The user to check
            
        Returns:
            bool: True if followed by user, False otherwise
        """
        from app.models.follow import Follow
        return Follow.is_following(user, self)
    
    def get_followed_posts(self):
        """
        Get posts from users that this user follows.
        
        Returns:
            Query: SQLAlchemy query for posts from followed users
            
        This demonstrates complex query construction with joins
        and is useful for creating personalized feeds.
        """
        from app.models.blog import Post
        from app.models.follow import Follow
        
        return Post.query.join(
            Follow, Follow.followed_id == Post.user_id
        ).filter(
            Follow.follower_id == self.id
        ).order_by(Post.created_at.desc())
    
    # Role and permission methods
    def can(self, permission_name):
        """
        Check if user has a specific permission.
        
        Args:
            permission_name (str): Name of the permission to check
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        if self.role is None:
            return False
        
        from app.models.role import Permission
        permission = Permission.query.filter_by(name=permission_name).first()
        return permission is not None and self.role.has_permission(permission)
    
    def is_administrator(self):
        """
        Check if user is an administrator.
        
        Returns:
            bool: True if user is admin, False otherwise
        """
        return self.can('admin_access') or self.is_admin
    
    def is_moderator(self):
        """
        Check if user is a moderator or higher.
        
        Returns:
            bool: True if user can moderate, False otherwise
        """
        return self.can('moderate_comments') or self.is_administrator()
    
    # Activity tracking methods
    def ping(self):
        """
        Update the user's last seen timestamp.
        
        This method should be called whenever the user performs an action
        to track their activity and online status.
        """
        self.last_seen = datetime.utcnow()
        db.session.add(self)
    
    def is_online(self, threshold_minutes=5):
        """
        Check if user is currently online.
        
        Args:
            threshold_minutes (int): Minutes to consider user online
            
        Returns:
            bool: True if user was seen recently, False otherwise
        """
        if self.last_seen is None:
            return False
        
        threshold = datetime.utcnow() - timedelta(minutes=threshold_minutes)
        return self.last_seen > threshold
    
    # Class methods for learning SQLAlchemy patterns
    @classmethod
    def get_active_users(cls, limit=None):
        """
        Get all active users.
        
        Args:
            limit (int, optional): Maximum number of users to return
            
        Returns:
            Query: SQLAlchemy query for active users
        """
        query = cls.query.filter_by(is_active=True)
        if limit:
            query = query.limit(limit)
        return query
    
    @classmethod
    def get_recent_users(cls, days=30, limit=10):
        """
        Get users who joined recently.
        
        Args:
            days (int): Number of days to look back
            limit (int): Maximum number of users to return
            
        Returns:
            Query: SQLAlchemy query for recent users
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return cls.query.filter(
            cls.created_at >= cutoff_date
        ).order_by(cls.created_at.desc()).limit(limit)
    
    @classmethod
    def get_popular_users(cls, limit=10):
        """
        Get users with the most followers.
        
        Args:
            limit (int): Maximum number of users to return
            
        Returns:
            Query: SQLAlchemy query for popular users
        """
        return cls.query.order_by(cls.follower_count.desc()).limit(limit)
    
    @classmethod
    def search_users(cls, search_term):
        """
        Search users by username, email, or full name.
        
        Args:
            search_term (str): Term to search for
            
        Returns:
            Query: SQLAlchemy query for matching users
        """
        search_pattern = f"%{search_term}%"
        return cls.query.filter(
            db.or_(
                cls.username.ilike(search_pattern),
                cls.email.ilike(search_pattern),
                cls.full_name.ilike(search_pattern)
            )
        )
    
    @classmethod
    def get_by_email(cls, email):
        """
        Get user by email address.
        
        Args:
            email (str): Email address to search for
            
        Returns:
            User or None: User if found, None otherwise
        """
        return cls.query.filter_by(email=email).first()
    
    @classmethod
    def get_by_username(cls, username):
        """
        Get user by username.
        
        Args:
            username (str): Username to search for
            
        Returns:
            User or None: User if found, None otherwise
        """
        return cls.query.filter_by(username=username).first()
    
    def __repr__(self):
        """String representation of the User object."""
        return f'<User {self.username}>'