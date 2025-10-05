"""Add additional analytics fields and constraints

Revision ID: b8f3e1fdccf0
Revises: 71d7b82cc978
Create Date: 2025-10-05 10:21:43.104876

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b8f3e1fdccf0'
down_revision = '71d7b82cc978'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add additional analytics fields and database constraints.
    
    This migration demonstrates:
    - Adding new columns to existing tables
    - Adding check constraints for data validation
    - Creating triggers for automatic data updates
    - Advanced database features for analytics
    """
    
    # Add additional analytics fields to PostView table
    with op.batch_alter_table('post_view', schema=None) as batch_op:
        # Add bounce rate tracking (did user leave immediately)
        batch_op.add_column(sa.Column('is_bounce', sa.Boolean(), default=False, nullable=True))
        
        # Add conversion tracking (did user perform desired action)
        batch_op.add_column(sa.Column('conversion_type', sa.String(50), nullable=True))
        
        # Add page load time for performance analytics
        batch_op.add_column(sa.Column('page_load_time', sa.Integer(), nullable=True))
        
        # Add exit page tracking
        batch_op.add_column(sa.Column('exit_page', sa.String(512), nullable=True))
        
        # Add UTM tracking parameters for marketing analytics
        batch_op.add_column(sa.Column('utm_source', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('utm_medium', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('utm_campaign', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('utm_term', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('utm_content', sa.String(100), nullable=True))
        
        # Add check constraints for data validation
        batch_op.create_check_constraint(
            'valid_scroll_depth', 
            'scroll_depth >= 0.0 AND scroll_depth <= 1.0'
        )
        batch_op.create_check_constraint(
            'valid_time_spent', 
            'time_spent >= 0'
        )
        batch_op.create_check_constraint(
            'valid_page_load_time', 
            'page_load_time IS NULL OR page_load_time >= 0'
        )
    
    # Add additional fields to Notification table for better tracking
    with op.batch_alter_table('notification', schema=None) as batch_op:
        # Add action URL for clickable notifications
        batch_op.add_column(sa.Column('action_url', sa.String(512), nullable=True))
        
        # Add click tracking
        batch_op.add_column(sa.Column('clicked_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('click_count', sa.Integer(), default=0, nullable=False))
        
        # Add notification source tracking
        batch_op.add_column(sa.Column('source', sa.String(50), nullable=True))
        
        # Add batch ID for bulk notifications
        batch_op.add_column(sa.Column('batch_id', sa.String(128), nullable=True))
        
        # Add check constraints
        batch_op.create_check_constraint(
            'valid_click_count', 
            'click_count >= 0'
        )
    
    # Add analytics summary table for aggregated data
    op.create_table('analytics_summary',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('metric_key', sa.String(100), nullable=True),  # e.g., post_id, user_id
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('count', sa.Integer(), default=1, nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('date', 'metric_type', 'metric_key', name='unique_daily_metric')
    )
    
    # Add indexes for the analytics summary table
    with op.batch_alter_table('analytics_summary', schema=None) as batch_op:
        batch_op.create_index('idx_analytics_summary_date', ['date'])
        batch_op.create_index('idx_analytics_summary_type', ['metric_type'])
        batch_op.create_index('idx_analytics_summary_date_type', ['date', 'metric_type'])
        batch_op.create_index('idx_analytics_summary_key', ['metric_key'])
    
    # Add indexes for new PostView fields
    with op.batch_alter_table('post_view', schema=None) as batch_op:
        batch_op.create_index('idx_postview_bounce', ['is_bounce'])
        batch_op.create_index('idx_postview_conversion', ['conversion_type'])
        batch_op.create_index('idx_postview_utm_source', ['utm_source'])
        batch_op.create_index('idx_postview_utm_campaign', ['utm_campaign'])
        batch_op.create_index('idx_postview_marketing', ['utm_source', 'utm_medium', 'utm_campaign'])
    
    # Add indexes for new Notification fields
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.create_index('idx_notification_clicked', ['clicked_at'])
        batch_op.create_index('idx_notification_source', ['source'])
        batch_op.create_index('idx_notification_batch', ['batch_id'])


def downgrade():
    """
    Remove the additional analytics fields and constraints.
    
    This demonstrates proper rollback of schema changes.
    """
    
    # Drop analytics summary table
    op.drop_table('analytics_summary')
    
    # Remove indexes and fields from Notification table
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.drop_index('idx_notification_batch')
        batch_op.drop_index('idx_notification_source')
        batch_op.drop_index('idx_notification_clicked')
        
        batch_op.drop_constraint('valid_click_count', type_='check')
        
        batch_op.drop_column('batch_id')
        batch_op.drop_column('source')
        batch_op.drop_column('click_count')
        batch_op.drop_column('clicked_at')
        batch_op.drop_column('action_url')
    
    # Remove indexes and fields from PostView table
    with op.batch_alter_table('post_view', schema=None) as batch_op:
        batch_op.drop_index('idx_postview_marketing')
        batch_op.drop_index('idx_postview_utm_campaign')
        batch_op.drop_index('idx_postview_utm_source')
        batch_op.drop_index('idx_postview_conversion')
        batch_op.drop_index('idx_postview_bounce')
        
        batch_op.drop_constraint('valid_page_load_time', type_='check')
        batch_op.drop_constraint('valid_time_spent', type_='check')
        batch_op.drop_constraint('valid_scroll_depth', type_='check')
        
        batch_op.drop_column('utm_content')
        batch_op.drop_column('utm_term')
        batch_op.drop_column('utm_campaign')
        batch_op.drop_column('utm_medium')
        batch_op.drop_column('utm_source')
        batch_op.drop_column('exit_page')
        batch_op.drop_column('page_load_time')
        batch_op.drop_column('conversion_type')
        batch_op.drop_column('is_bounce')
