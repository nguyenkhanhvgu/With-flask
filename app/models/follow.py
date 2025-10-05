"""
Follow Model

This module contains the Follow model for user relationship tracking.
It demonstrates many-to-many self-referential relationships and
social media functionality patterns.
"""

from datetime import datetime
from sqlalchemy import and_
from app.extensions import db
from app.models.base import BaseModel


class Follow(BaseModel):
    """
    Follow model for tracking user relationships.
    
    This model demonstrates:
    - Self-referential many-to-many relationships
    - Social media following patterns
    - Composite unique constraints
    - Class methods for relationship management
    - Performance optimization with indexes
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Table-level constraints and indexes
    __table_args__ = (
        # Ensure a user can't follow the same person twice
        db.UniqueConstraint('follower_id', 'followed_id', name='unique_follow_relationship'),
        
        # Composite indexes for common query patterns
        db.Index('idx_follow_follower_created', 'follower_id', 'created_at'),
        db.Index('idx_follow_followed_created', 'followed_id', 'created_at'),
        
        # Prevent self-following at database level
        db.CheckConstraint('follower_id != followed_id', name='no_self_follow'),
    )
    
    @classmethod
    def follow(cls, follower, followed):
        """
        Create a follow relationship between two users.
        
        Args:
            follower (User): The user who is following
            followed (User): The user being followed
            
        Returns:
            Follow or None: The Follow instance if successful, None if invalid
            
        This method demonstrates relationship creation with validation
        and prevents duplicate relationships and self-following.
        """
        # Prevent self-following
        if follower.id == followed.id:
            return None
        
        # Check if relationship already exists
        if cls.is_following(follower, followed):
            return None
        
        # Create new follow relationship
        follow = cls(follower_id=follower.id, followed_id=followed.id)
        return follow
    
    @classmethod
    def unfollow(cls, follower, followed):
        """
        Remove a follow relationship between two users.
        
        Args:
            follower (User): The user who is unfollowing
            followed (User): The user being unfollowed
            
        Returns:
            bool: True if unfollow was successful, False if relationship didn't exist
        """
        follow = cls.query.filter_by(
            follower_id=follower.id,
            followed_id=followed.id
        ).first()
        
        if follow:
            db.session.delete(follow)
            db.session.commit()
            return True
        
        return False
    
    @classmethod
    def is_following(cls, follower, followed):
        """
        Check if one user is following another.
        
        Args:
            follower (User): The potential follower
            followed (User): The potential followed user
            
        Returns:
            bool: True if follower is following followed, False otherwise
        """
        return cls.query.filter_by(
            follower_id=follower.id,
            followed_id=followed.id
        ).first() is not None
    
    @classmethod
    def get_followers(cls, user, limit=None):
        """
        Get all users following the specified user.
        
        Args:
            user (User): The user whose followers to get
            limit (int, optional): Maximum number of followers to return
            
        Returns:
            Query: SQLAlchemy query for follower users
        """
        from app.models.user import User
        
        query = User.query.join(
            cls, cls.follower_id == User.id
        ).filter(
            cls.followed_id == user.id
        ).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query
    
    @classmethod
    def get_following(cls, user, limit=None):
        """
        Get all users that the specified user is following.
        
        Args:
            user (User): The user whose following list to get
            limit (int, optional): Maximum number of users to return
            
        Returns:
            Query: SQLAlchemy query for followed users
        """
        from app.models.user import User
        
        query = User.query.join(
            cls, cls.followed_id == User.id
        ).filter(
            cls.follower_id == user.id
        ).order_by(cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query
    
    @classmethod
    def get_mutual_follows(cls, user1, user2):
        """
        Get users that both user1 and user2 are following (mutual connections).
        
        Args:
            user1 (User): First user
            user2 (User): Second user
            
        Returns:
            Query: SQLAlchemy query for mutual connections
        """
        from app.models.user import User
        
        # Subquery for users that user1 follows
        user1_following = db.session.query(cls.followed_id).filter_by(follower_id=user1.id)
        
        # Query for users that user2 follows and are also followed by user1
        return User.query.join(
            cls, cls.followed_id == User.id
        ).filter(
            cls.follower_id == user2.id,
            User.id.in_(user1_following)
        )
    
    @classmethod
    def get_follow_suggestions(cls, user, limit=10):
        """
        Get suggested users to follow based on mutual connections.
        
        Args:
            user (User): The user to get suggestions for
            limit (int): Maximum number of suggestions to return
            
        Returns:
            Query: SQLAlchemy query for suggested users
            
        This method demonstrates complex query construction for
        recommendation algorithms.
        """
        from app.models.user import User
        from sqlalchemy import func, text
        
        # Get users followed by people that the current user follows
        # but exclude users already followed and the user themselves
        
        # Subquery: users that the current user follows
        user_following = db.session.query(cls.followed_id).filter_by(follower_id=user.id)
        
        # Subquery: users followed by the people that current user follows
        suggestions_subquery = db.session.query(
            cls.followed_id,
            func.count(cls.id).label('mutual_count')
        ).filter(
            cls.follower_id.in_(user_following),
            cls.followed_id != user.id,  # Exclude self
            ~cls.followed_id.in_(user_following)  # Exclude already followed
        ).group_by(cls.followed_id).subquery()
        
        # Main query: get suggested users ordered by mutual connection count
        return User.query.join(
            suggestions_subquery,
            User.id == suggestions_subquery.c.followed_id
        ).order_by(
            suggestions_subquery.c.mutual_count.desc(),
            User.created_at.desc()
        ).limit(limit)
    
    @classmethod
    def get_recent_followers(cls, user, days=7, limit=10):
        """
        Get users who recently started following the specified user.
        
        Args:
            user (User): The user whose recent followers to get
            days (int): Number of days to look back
            limit (int): Maximum number of followers to return
            
        Returns:
            Query: SQLAlchemy query for recent followers
        """
        from app.models.user import User
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return User.query.join(
            cls, cls.follower_id == User.id
        ).filter(
            cls.followed_id == user.id,
            cls.created_at >= cutoff_date
        ).order_by(cls.created_at.desc()).limit(limit)
    
    def __repr__(self):
        """String representation of the Follow object."""
        return f'<Follow follower_id={self.follower_id} followed_id={self.followed_id}>'