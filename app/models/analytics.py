"""
Analytics Models

This module contains models for tracking user behavior and analytics.
It demonstrates analytics patterns, data collection, and performance
optimization for high-volume tracking data.
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app.extensions import db
from app.models.base import BaseModel


class PostView(BaseModel):
    """
    PostView model for tracking post analytics and user engagement.
    
    This model demonstrates:
    - Analytics data collection patterns
    - High-volume data handling
    - Performance optimization with indexes
    - User behavior tracking
    - Privacy-conscious data collection
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)  # Nullable for anonymous users
    
    # Request information
    ip_address = db.Column(db.String(45), index=True)  # IPv6 compatible
    user_agent = db.Column(db.Text)
    referer = db.Column(db.String(512))  # Where the user came from
    
    # Engagement metrics
    time_spent = db.Column(db.Integer, default=0)  # Time spent reading in seconds
    scroll_depth = db.Column(db.Float, default=0.0)  # Percentage of post scrolled (0.0-1.0)
    
    # Session information
    session_id = db.Column(db.String(128), index=True)  # Track unique sessions
    is_unique_view = db.Column(db.Boolean, default=True, index=True)  # First view in session
    
    # Geographic information (optional, for analytics)
    country_code = db.Column(db.String(2))  # ISO country code
    city = db.Column(db.String(100))
    
    # Device information
    device_type = db.Column(db.String(20))  # mobile, tablet, desktop
    browser = db.Column(db.String(50))
    operating_system = db.Column(db.String(50))
    
    # Relationships
    post = db.relationship('Post', backref='views')
    user = db.relationship('User', backref='post_views')
    
    # Table-level constraints and indexes for performance
    __table_args__ = (
        # Composite indexes for common analytics queries
        db.Index('idx_postview_post_created', 'post_id', 'created_at'),
        db.Index('idx_postview_user_created', 'user_id', 'created_at'),
        db.Index('idx_postview_session_post', 'session_id', 'post_id'),
        db.Index('idx_postview_unique_created', 'is_unique_view', 'created_at'),
        
        # Index for geographic analytics
        db.Index('idx_postview_country_created', 'country_code', 'created_at'),
        
        # Index for device analytics
        db.Index('idx_postview_device_created', 'device_type', 'created_at'),
        
        # Partial indexes for performance (PostgreSQL specific)
        db.Index('idx_postview_unique_views', 'post_id', 'created_at', 
                postgresql_where=db.text('is_unique_view = true')),
        db.Index('idx_postview_registered_users', 'user_id', 'post_id', 'created_at',
                postgresql_where=db.text('user_id IS NOT NULL')),
    )
    
    @classmethod
    def record_view(cls, post_id, user_id=None, ip_address=None, user_agent=None, 
                   session_id=None, referer=None, **kwargs):
        """
        Record a post view with analytics data.
        
        Args:
            post_id (int): ID of the post being viewed
            user_id (int, optional): ID of the user viewing (None for anonymous)
            ip_address (str, optional): IP address of the viewer
            user_agent (str, optional): User agent string
            session_id (str, optional): Session identifier
            referer (str, optional): Referring URL
            **kwargs: Additional analytics data
            
        Returns:
            PostView: The created view record
            
        This method demonstrates analytics data collection with
        privacy considerations and duplicate detection.
        """
        # Check if this is a unique view for this session/post combination
        is_unique = True
        if session_id:
            existing_view = cls.query.filter_by(
                post_id=post_id,
                session_id=session_id
            ).first()
            is_unique = existing_view is None
        
        # Create view record
        view = cls(
            post_id=post_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            session_id=session_id,
            referer=referer,
            is_unique_view=is_unique,
            **kwargs
        )
        
        db.session.add(view)
        db.session.commit()
        
        return view
    
    @classmethod
    def get_post_analytics(cls, post_id, days=30):
        """
        Get analytics data for a specific post.
        
        Args:
            post_id (int): ID of the post
            days (int): Number of days to analyze
            
        Returns:
            dict: Analytics data including views, unique visitors, etc.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Base query for the time period
        base_query = cls.query.filter(
            cls.post_id == post_id,
            cls.created_at >= cutoff_date
        )
        
        # Calculate various metrics
        total_views = base_query.count()
        unique_views = base_query.filter_by(is_unique_view=True).count()
        registered_views = base_query.filter(cls.user_id.isnot(None)).count()
        anonymous_views = base_query.filter(cls.user_id.is_(None)).count()
        
        # Average time spent (excluding zero values)
        avg_time_spent = db.session.query(func.avg(cls.time_spent)).filter(
            cls.post_id == post_id,
            cls.created_at >= cutoff_date,
            cls.time_spent > 0
        ).scalar() or 0
        
        # Average scroll depth
        avg_scroll_depth = db.session.query(func.avg(cls.scroll_depth)).filter(
            cls.post_id == post_id,
            cls.created_at >= cutoff_date,
            cls.scroll_depth > 0
        ).scalar() or 0
        
        return {
            'total_views': total_views,
            'unique_views': unique_views,
            'registered_views': registered_views,
            'anonymous_views': anonymous_views,
            'avg_time_spent': round(avg_time_spent, 2),
            'avg_scroll_depth': round(avg_scroll_depth, 4),
            'period_days': days
        }
    
    @classmethod
    def get_popular_posts(cls, days=7, limit=10):
        """
        Get most popular posts by view count.
        
        Args:
            days (int): Number of days to analyze
            limit (int): Maximum number of posts to return
            
        Returns:
            Query: SQLAlchemy query for popular posts with view counts
        """
        from app.models.blog import Post
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.session.query(
            Post,
            func.count(cls.id).label('view_count'),
            func.count(func.distinct(cls.session_id)).label('unique_visitors')
        ).join(
            cls, Post.id == cls.post_id
        ).filter(
            cls.created_at >= cutoff_date
        ).group_by(
            Post.id
        ).order_by(
            func.count(cls.id).desc()
        ).limit(limit)
    
    @classmethod
    def get_trending_posts(cls, hours=24, limit=10):
        """
        Get trending posts based on recent view velocity.
        
        Args:
            hours (int): Number of hours to analyze for trending
            limit (int): Maximum number of posts to return
            
        Returns:
            Query: SQLAlchemy query for trending posts
            
        This method demonstrates more complex analytics calculations
        for identifying trending content.
        """
        from app.models.blog import Post
        
        cutoff_date = datetime.utcnow() - timedelta(hours=hours)
        
        # Calculate view velocity (views per hour)
        return db.session.query(
            Post,
            (func.count(cls.id) / hours).label('views_per_hour'),
            func.count(cls.id).label('total_views')
        ).join(
            cls, Post.id == cls.post_id
        ).filter(
            cls.created_at >= cutoff_date
        ).group_by(
            Post.id
        ).having(
            func.count(cls.id) >= 5  # Minimum threshold for trending
        ).order_by(
            (func.count(cls.id) / hours).desc()
        ).limit(limit)
    
    @classmethod
    def get_user_reading_stats(cls, user_id, days=30):
        """
        Get reading statistics for a specific user.
        
        Args:
            user_id (int): ID of the user
            days (int): Number of days to analyze
            
        Returns:
            dict: User reading statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        base_query = cls.query.filter(
            cls.user_id == user_id,
            cls.created_at >= cutoff_date
        )
        
        total_views = base_query.count()
        unique_posts = base_query.with_entities(cls.post_id).distinct().count()
        total_time = db.session.query(func.sum(cls.time_spent)).filter(
            cls.user_id == user_id,
            cls.created_at >= cutoff_date
        ).scalar() or 0
        
        avg_time_per_post = (total_time / unique_posts) if unique_posts > 0 else 0
        
        return {
            'total_views': total_views,
            'unique_posts_read': unique_posts,
            'total_reading_time': total_time,
            'avg_time_per_post': round(avg_time_per_post, 2),
            'period_days': days
        }
    
    @classmethod
    def get_device_analytics(cls, days=30):
        """
        Get device type analytics for the specified period.
        
        Args:
            days (int): Number of days to analyze
            
        Returns:
            list: Device analytics data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.session.query(
            cls.device_type,
            func.count(cls.id).label('view_count'),
            func.count(func.distinct(cls.session_id)).label('unique_sessions')
        ).filter(
            cls.created_at >= cutoff_date,
            cls.device_type.isnot(None)
        ).group_by(
            cls.device_type
        ).order_by(
            func.count(cls.id).desc()
        ).all()
    
    @classmethod
    def get_geographic_analytics(cls, days=30):
        """
        Get geographic analytics for the specified period.
        
        Args:
            days (int): Number of days to analyze
            
        Returns:
            list: Geographic analytics data
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.session.query(
            cls.country_code,
            func.count(cls.id).label('view_count'),
            func.count(func.distinct(cls.session_id)).label('unique_visitors')
        ).filter(
            cls.created_at >= cutoff_date,
            cls.country_code.isnot(None)
        ).group_by(
            cls.country_code
        ).order_by(
            func.count(cls.id).desc()
        ).all()
    
    def update_engagement(self, time_spent=None, scroll_depth=None):
        """
        Update engagement metrics for this view.
        
        Args:
            time_spent (int, optional): Time spent reading in seconds
            scroll_depth (float, optional): Scroll depth percentage (0.0-1.0)
            
        This method allows updating engagement metrics as the user
        interacts with the content.
        """
        if time_spent is not None:
            self.time_spent = max(self.time_spent, time_spent)  # Keep the maximum
        
        if scroll_depth is not None:
            self.scroll_depth = max(self.scroll_depth, scroll_depth)  # Keep the maximum
        
        db.session.commit()
    
    def __repr__(self):
        """String representation of the PostView object."""
        return f'<PostView post_id={self.post_id} user_id={self.user_id}>'


class Notification(BaseModel):
    """
    Notification model for real-time user notifications.
    
    This model demonstrates:
    - Notification system patterns
    - Real-time messaging support
    - User engagement tracking
    - Notification categorization and prioritization
    """
    
    # Note: id, created_at, updated_at are inherited from BaseModel
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Notification content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False, index=True)
    
    # Status tracking
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    
    # Priority and categorization
    priority = db.Column(db.String(20), default='normal', index=True)  # low, normal, high, urgent
    category = db.Column(db.String(50), index=True)  # comment, follow, like, system, etc.
    
    # Related objects (optional, for linking notifications to specific content)
    related_post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=True)
    related_comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    related_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Delivery tracking
    delivery_method = db.Column(db.String(20), default='web')  # web, email, push, sms
    delivered_at = db.Column(db.DateTime, nullable=True)
    
    # Expiration (for temporary notifications)
    expires_at = db.Column(db.DateTime, nullable=True, index=True)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='notifications')
    related_post = db.relationship('Post', foreign_keys=[related_post_id])
    related_comment = db.relationship('Comment', foreign_keys=[related_comment_id])
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    
    # Table-level constraints and indexes
    __table_args__ = (
        # Composite indexes for common notification queries
        db.Index('idx_notification_user_read', 'user_id', 'is_read'),
        db.Index('idx_notification_user_created', 'user_id', 'created_at'),
        db.Index('idx_notification_type_created', 'notification_type', 'created_at'),
        db.Index('idx_notification_priority_created', 'priority', 'created_at'),
        db.Index('idx_notification_category_created', 'category', 'created_at'),
        
        # Index for cleanup of expired notifications
        db.Index('idx_notification_expires', 'expires_at'),
        
        # Partial indexes for performance
        db.Index('idx_notification_unread', 'user_id', 'created_at',
                postgresql_where=db.text('is_read = false')),
        db.Index('idx_notification_high_priority', 'user_id', 'created_at',
                postgresql_where=db.text("priority IN ('high', 'urgent')")),
        
        # Check constraints for data integrity
        db.CheckConstraint("priority IN ('low', 'normal', 'high', 'urgent')", 
                          name='valid_priority'),
        db.CheckConstraint("delivery_method IN ('web', 'email', 'push', 'sms')", 
                          name='valid_delivery_method'),
    )
    
    @classmethod
    def create_notification(cls, user_id, title, message, notification_type, 
                          category=None, priority='normal', related_post_id=None,
                          related_comment_id=None, related_user_id=None,
                          expires_at=None, delivery_method='web'):
        """
        Create a new notification for a user.
        
        Args:
            user_id (int): ID of the user to notify
            title (str): Notification title
            message (str): Notification message
            notification_type (str): Type of notification
            category (str, optional): Notification category
            priority (str): Priority level (low, normal, high, urgent)
            related_post_id (int, optional): Related post ID
            related_comment_id (int, optional): Related comment ID
            related_user_id (int, optional): Related user ID
            expires_at (datetime, optional): Expiration time
            delivery_method (str): Delivery method
            
        Returns:
            Notification: The created notification
        """
        notification = cls(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            category=category or notification_type,
            priority=priority,
            related_post_id=related_post_id,
            related_comment_id=related_comment_id,
            related_user_id=related_user_id,
            expires_at=expires_at,
            delivery_method=delivery_method
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return notification
    
    @classmethod
    def get_user_notifications(cls, user_id, unread_only=False, limit=50):
        """
        Get notifications for a specific user.
        
        Args:
            user_id (int): ID of the user
            unread_only (bool): Whether to return only unread notifications
            limit (int): Maximum number of notifications to return
            
        Returns:
            Query: SQLAlchemy query for user notifications
        """
        query = cls.query.filter_by(user_id=user_id)
        
        if unread_only:
            query = query.filter_by(is_read=False)
        
        # Filter out expired notifications
        query = query.filter(
            or_(cls.expires_at.is_(None), cls.expires_at > datetime.utcnow())
        )
        
        return query.order_by(cls.created_at.desc()).limit(limit)
    
    @classmethod
    def get_unread_count(cls, user_id):
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id (int): ID of the user
            
        Returns:
            int: Number of unread notifications
        """
        return cls.query.filter_by(
            user_id=user_id,
            is_read=False
        ).filter(
            or_(cls.expires_at.is_(None), cls.expires_at > datetime.utcnow())
        ).count()
    
    @classmethod
    def mark_all_read(cls, user_id):
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id (int): ID of the user
            
        Returns:
            int: Number of notifications marked as read
        """
        count = cls.query.filter_by(
            user_id=user_id,
            is_read=False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        
        db.session.commit()
        return count
    
    @classmethod
    def cleanup_expired(cls):
        """
        Remove expired notifications from the database.
        
        Returns:
            int: Number of notifications removed
            
        This method should be called periodically to clean up
        expired notifications and maintain database performance.
        """
        count = cls.query.filter(
            cls.expires_at.isnot(None),
            cls.expires_at <= datetime.utcnow()
        ).delete()
        
        db.session.commit()
        return count
    
    def mark_read(self):
        """Mark this notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
            db.session.commit()
    
    def mark_unread(self):
        """Mark this notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            db.session.commit()
    
    def is_expired(self):
        """
        Check if this notification has expired.
        
        Returns:
            bool: True if expired, False otherwise
        """
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        """String representation of the Notification object."""
        return f'<Notification {self.id}: {self.title}>'