"""
Comment resources for the API
"""

from flask import request
from flask_restful import Resource
from app.models import Post, Comment
from app.extensions import db
from .base import BaseResource, token_required, comment_to_dict


class PostCommentsResource(BaseResource):
    """Resource for handling comments on a specific post"""
    
    def get(self, post_id):
        """Get comments for a specific post"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 50, type=int), 100)
            
            post = Post.query.get_or_404(post_id)
            
            comments = Comment.query.filter_by(post_id=post_id).order_by(
                Comment.created_at.desc()
            ).paginate(page=page, per_page=per_page, error_out=False)
            
            return {
                'comments': [comment_to_dict(comment) for comment in comments.items],
                'pagination': {
                    'page': comments.page,
                    'pages': comments.pages,
                    'per_page': comments.per_page,
                    'total': comments.total
                }
            }, 200
            
        except Exception as e:
            return {'error': f'Failed to fetch comments: {str(e)}'}, 500
    
    @token_required
    def post(self, post_id):
        """Create a new comment on a post"""
        try:
            post = Post.query.get_or_404(post_id)
            
            data = request.get_json()
            if not data:
                return {'error': 'No data provided'}, 400
            
            content = data.get('content', '').strip()
            if not content:
                return {'error': 'Comment content is required'}, 400
            
            # Create comment
            comment = Comment(
                content=content,
                post_id=post_id,
                user_id=self.current_user.id
            )
            
            db.session.add(comment)
            db.session.commit()
            
            # Note: Email notification would be handled by a service layer
            # For now, we'll skip it to keep the resource focused on REST operations
            
            return {
                'message': 'Comment created successfully',
                'comment': comment_to_dict(comment)
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to create comment: {str(e)}'}, 500


class CommentResource(BaseResource):
    """Resource for handling individual comments"""
    
    @token_required
    def delete(self, comment_id):
        """Delete a comment"""
        try:
            comment = Comment.query.get_or_404(comment_id)
            
            # Check if user owns the comment or is admin
            if comment.user_id != self.current_user.id and not self.current_user.is_admin:
                return {'error': 'Permission denied'}, 403
            
            db.session.delete(comment)
            db.session.commit()
            
            return {'message': 'Comment deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to delete comment: {str(e)}'}, 500