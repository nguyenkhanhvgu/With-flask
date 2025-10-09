"""
Post resources for the API
"""

from flask import request
from flask_restful import Resource
from app.models import Post, Category
from app.extensions import db
from app.middleware import api_rate_limit, rate_limit
from .base import BaseResource, token_required, post_to_dict
import datetime


class PostListResource(BaseResource):
    """Resource for handling multiple posts"""
    
    @api_rate_limit(limit=200, window=3600)  # 200 requests per hour for listing posts
    def get(self):
        """Get list of posts with optional filtering"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            category_id = request.args.get('category_id', type=int)
            author_id = request.args.get('author_id', type=int)
            search = request.args.get('search', '').strip()
            
            query = Post.query
            
            # Apply filters
            if category_id:
                query = query.filter_by(category_id=category_id)
            
            if author_id:
                query = query.filter_by(user_id=author_id)
            
            if search:
                query = query.filter(
                    (Post.title.contains(search)) | 
                    (Post.content.contains(search))
                )
            
            posts = query.order_by(Post.created_at.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'posts': [post_to_dict(post, include_content=False) for post in posts.items],
                'pagination': {
                    'page': posts.page,
                    'pages': posts.pages,
                    'per_page': posts.per_page,
                    'total': posts.total
                }
            }, 200
            
        except Exception as e:
            return {'error': f'Failed to fetch posts: {str(e)}'}, 500
    
    @api_rate_limit(limit=10, window=3600)  # 10 post creations per hour
    @token_required
    def post(self):
        """Create a new post"""
        try:
            data = request.get_json()
            
            if not data:
                return {'error': 'No data provided'}, 400
            
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            category_id = data.get('category_id')
            
            if not title or not content:
                return {'error': 'Title and content are required'}, 400
            
            # Validate category if provided
            if category_id:
                category = Category.query.get(category_id)
                if not category:
                    return {'error': 'Invalid category'}, 400
            
            # Create post
            post = Post(
                title=title,
                content=content,
                user_id=self.current_user.id,
                category_id=category_id
            )
            
            db.session.add(post)
            db.session.commit()
            
            return {
                'message': 'Post created successfully',
                'post': post_to_dict(post)
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to create post: {str(e)}'}, 500


class PostResource(BaseResource):
    """Resource for handling individual posts"""
    
    @api_rate_limit(limit=300, window=3600)  # 300 individual post views per hour
    def get(self, post_id):
        """Get specific post by ID with full content"""
        try:
            post = Post.query.get_or_404(post_id)
            return {'post': post_to_dict(post)}, 200
            
        except Exception as e:
            return {'error': f'Failed to fetch post: {str(e)}'}, 500
    
    @api_rate_limit(limit=20, window=3600)  # 20 post updates per hour
    @token_required
    def put(self, post_id):
        """Update an existing post"""
        try:
            post = Post.query.get_or_404(post_id)
            
            # Check if user owns the post or is admin
            if post.user_id != self.current_user.id and not self.current_user.is_admin:
                return {'error': 'Permission denied'}, 403
            
            data = request.get_json()
            
            if 'title' in data:
                title = data['title'].strip()
                if not title:
                    return {'error': 'Title cannot be empty'}, 400
                post.title = title
            
            if 'content' in data:
                content = data['content'].strip()
                if not content:
                    return {'error': 'Content cannot be empty'}, 400
                post.content = content
            
            if 'category_id' in data:
                category_id = data['category_id']
                if category_id:
                    category = Category.query.get(category_id)
                    if not category:
                        return {'error': 'Invalid category'}, 400
                post.category_id = category_id
            
            post.updated_at = datetime.datetime.utcnow()
            db.session.commit()
            
            return {
                'message': 'Post updated successfully',
                'post': post_to_dict(post)
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update post: {str(e)}'}, 500
    
    @api_rate_limit(limit=5, window=3600)  # 5 post deletions per hour
    @token_required
    def delete(self, post_id):
        """Delete a post"""
        try:
            post = Post.query.get_or_404(post_id)
            
            # Check if user owns the post or is admin
            if post.user_id != self.current_user.id and not self.current_user.is_admin:
                return {'error': 'Permission denied'}, 403
            
            db.session.delete(post)
            db.session.commit()
            
            return {'message': 'Post deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to delete post: {str(e)}'}, 500