"""
Base classes and utilities for API resources
"""

from flask import request, current_app
from flask_restful import Resource
from functools import wraps
import jwt
import datetime
from app.models.user import User


class BaseResource(Resource):
    """Base resource class with common functionality"""
    
    def __init__(self):
        super().__init__()
        self.current_user = None


def generate_token(user_id):
    """Generate JWT token for user authentication"""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def verify_token(token):
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    """Decorator to require JWT token authentication"""
    @wraps(f)
    def decorated(self, *args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return {'error': 'Invalid token format'}, 401
        
        if not token:
            return {'error': 'Token is missing'}, 401
        
        user_id = verify_token(token)
        if user_id is None:
            return {'error': 'Token is invalid or expired'}, 401
        
        # Get user and add to resource instance
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return {'error': 'User not found or inactive'}, 401
        
        self.current_user = user
        return f(self, *args, **kwargs)
    
    return decorated


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(self, *args, **kwargs):
        if not self.current_user or not self.current_user.is_admin:
            return {'error': 'Admin privileges required'}, 403
        return f(self, *args, **kwargs)
    return decorated


# Helper functions for JSON serialization
def user_to_dict(user, include_email=False):
    """Convert User object to dictionary"""
    data = {
        'id': user.id,
        'username': user.username,
        'avatar': f"/static/uploads/avatars/{user.avatar_filename}" if user.avatar_filename else None,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat(),
        'posts_count': len(user.posts),
        'comments_count': len(user.comments)
    }
    if include_email:
        data['email'] = user.email
    return data


def post_to_dict(post, include_content=True):
    """Convert Post object to dictionary"""
    data = {
        'id': post.id,
        'title': post.title,
        'author': user_to_dict(post.author),
        'category': {'id': post.category.id, 'name': post.category.name} if post.category else None,
        'image': f"/static/uploads/posts/{post.image_filename}" if post.image_filename else None,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat(),
        'comments_count': len(post.comments)
    }
    if include_content:
        data['content'] = post.content
    return data


def comment_to_dict(comment):
    """Convert Comment object to dictionary"""
    return {
        'id': comment.id,
        'content': comment.content,
        'author': user_to_dict(comment.author),
        'post_id': comment.post_id,
        'created_at': comment.created_at.isoformat()
    }


def category_to_dict(category):
    """Convert Category object to dictionary"""
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'posts_count': len(category.posts)
    }