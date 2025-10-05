"""Add performance indexes for analytics models

Revision ID: 71d7b82cc978
Revises: 335895c3add1
Create Date: 2025-10-05 10:20:34.262501

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '71d7b82cc978'
down_revision = '335895c3add1'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add additional performance indexes for analytics and social features.
    
    This migration demonstrates:
    - Adding indexes for high-volume analytics queries
    - Optimizing social media feature queries (follows, notifications)
    - Creating composite indexes for common query patterns
    - Performance optimization strategies for Flask applications
    """
    
    # Additional indexes for PostView analytics queries
    # These indexes optimize common analytics queries that weren't covered in the initial migration
    
    # Index for time-based analytics queries (last 24 hours, last week, etc.)
    op.create_index(
        'idx_postview_time_analytics', 
        'post_view', 
        ['created_at', 'post_id', 'is_unique_view']
    )
    
    # Index for user engagement analytics
    op.create_index(
        'idx_postview_engagement', 
        'post_view', 
        ['post_id', 'time_spent', 'scroll_depth']
    )
    
    # Index for geographic analytics aggregation
    op.create_index(
        'idx_postview_geo_analytics', 
        'post_view', 
        ['country_code', 'city', 'created_at']
    )
    
    # Additional indexes for Follow model social features
    
    # Index for mutual connections queries
    op.create_index(
        'idx_follow_mutual_connections', 
        'follow', 
        ['followed_id', 'follower_id']
    )
    
    # Index for follower count aggregations
    op.create_index(
        'idx_follow_count_optimization', 
        'follow', 
        ['followed_id']
    )
    
    # Index for following count aggregations  
    op.create_index(
        'idx_follow_following_count', 
        'follow', 
        ['follower_id']
    )
    
    # Additional indexes for Notification model
    
    # Index for notification cleanup operations
    op.create_index(
        'idx_notification_cleanup', 
        'notification', 
        ['expires_at', 'is_read']
    )
    
    # Index for notification feed queries (recent notifications for user)
    op.create_index(
        'idx_notification_feed', 
        'notification', 
        ['user_id', 'created_at', 'priority', 'is_read']
    )
    
    # Index for notification type analytics
    op.create_index(
        'idx_notification_type_analytics', 
        'notification', 
        ['notification_type', 'created_at', 'is_read']
    )
    
    # Additional indexes for User model to support new features
    
    # Index for user search and discovery
    op.create_index(
        'idx_user_discovery', 
        'user', 
        ['is_active', 'email_confirmed', 'last_seen']
    )
    
    # Index for role-based queries
    op.create_index(
        'idx_user_role_queries', 
        'user', 
        ['role_id', 'is_active', 'created_at']
    )


def downgrade():
    """
    Remove the performance indexes added in this migration.
    
    This demonstrates proper cleanup of database objects during rollback.
    """
    
    # Drop User model indexes
    op.drop_index('idx_user_role_queries', 'user')
    op.drop_index('idx_user_discovery', 'user')
    
    # Drop Notification model indexes
    op.drop_index('idx_notification_type_analytics', 'notification')
    op.drop_index('idx_notification_feed', 'notification')
    op.drop_index('idx_notification_cleanup', 'notification')
    
    # Drop Follow model indexes
    op.drop_index('idx_follow_following_count', 'follow')
    op.drop_index('idx_follow_count_optimization', 'follow')
    op.drop_index('idx_follow_mutual_connections', 'follow')
    
    # Drop PostView model indexes
    op.drop_index('idx_postview_geo_analytics', 'post_view')
    op.drop_index('idx_postview_engagement', 'post_view')
    op.drop_index('idx_postview_time_analytics', 'post_view')
