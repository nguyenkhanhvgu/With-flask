"""
Admin resources for the API
"""

from flask_restful import Resource
from app.models import User, Post, Comment, Category
from .base import BaseResource, token_required, admin_required, user_to_dict, post_to_dict


class AdminStatsResource(BaseResource):
    """Resource for admin dashboard statistics"""
    
    @token_required
    @admin_required
    def get(self):
        """Get admin dashboard statistics"""
        try:
            stats = {
                'total_users': User.query.count(),
                'active_users': User.query.filter_by(is_active=True).count(),
                'total_posts': Post.query.count(),
                'total_comments': Comment.query.count(),
                'total_categories': Category.query.count(),
                'recent_users': [
                    user_to_dict(user) for user in 
                    User.query.order_by(User.created_at.desc()).limit(5).all()
                ],
                'recent_posts': [
                    post_to_dict(post, include_content=False) for post in 
                    Post.query.order_by(Post.created_at.desc()).limit(5).all()
                ]
            }
            
            return {'stats': stats}, 200
            
        except Exception as e:
            return {'error': f'Failed to fetch stats: {str(e)}'}, 500