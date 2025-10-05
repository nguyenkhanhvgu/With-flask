"""
User resources for the API
"""

from flask import request
from flask_restful import Resource
from app.models import User
from app.extensions import db
from .base import BaseResource, token_required, user_to_dict


class UserListResource(BaseResource):
    """Resource for handling multiple users"""
    
    def get(self):
        """Get list of all users"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            
            users = User.query.filter_by(is_active=True).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'users': [user_to_dict(user) for user in users.items],
                'pagination': {
                    'page': users.page,
                    'pages': users.pages,
                    'per_page': users.per_page,
                    'total': users.total
                }
            }, 200
            
        except Exception as e:
            return {'error': f'Failed to fetch users: {str(e)}'}, 500


class UserResource(BaseResource):
    """Resource for handling individual users"""
    
    def get(self, user_id):
        """Get specific user by ID"""
        try:
            user = User.query.get_or_404(user_id)
            
            if not user.is_active:
                return {'error': 'User not found'}, 404
            
            return {'user': user_to_dict(user)}, 200
            
        except Exception as e:
            return {'error': f'Failed to fetch user: {str(e)}'}, 500


class UserProfileResource(BaseResource):
    """Resource for handling current user's profile"""
    
    @token_required
    def get(self):
        """Get current user's profile"""
        return {'user': user_to_dict(self.current_user, include_email=True)}, 200
    
    @token_required
    def put(self):
        """Update current user's profile"""
        try:
            data = request.get_json()
            user = self.current_user
            
            if 'username' in data:
                username = data['username'].strip()
                if username != user.username:
                    # Check if username is taken
                    if User.query.filter_by(username=username).first():
                        return {'error': 'Username already exists'}, 400
                    user.username = username
            
            if 'email' in data:
                email = data['email'].strip()
                if email != user.email:
                    # Check if email is taken
                    if User.query.filter_by(email=email).first():
                        return {'error': 'Email already exists'}, 400
                    user.email = email
            
            db.session.commit()
            
            return {
                'message': 'Profile updated successfully',
                'user': user_to_dict(user, include_email=True)
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update profile: {str(e)}'}, 500