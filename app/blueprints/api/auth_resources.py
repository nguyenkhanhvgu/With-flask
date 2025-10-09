"""
Authentication resources for the API
"""

from flask import request
from flask_restful import Resource
from app.models import User
from app.extensions import db
from app.middleware import auth_rate_limit, api_rate_limit
from .base import BaseResource, generate_token, token_required, user_to_dict


class RegisterResource(BaseResource):
    """User registration resource"""
    
    @auth_rate_limit(limit=3, window=300)  # 3 registration attempts per 5 minutes
    def post(self):
        """Register a new user"""
        try:
            data = request.get_json(force=True, silent=True)
            
            if data is None:
                return {'error': 'No JSON data provided'}, 400
            
            if not data:
                return {'error': 'Empty data provided'}, 400
            
            username = data.get('username', '').strip()
            email = data.get('email', '').strip()
            password = data.get('password', '')
            
            # Validation
            if not username or not email or not password:
                return {'error': 'Username, email, and password are required'}, 400
            
            if len(password) < 6:
                return {'error': 'Password must be at least 6 characters long'}, 400
            
            # Check if user already exists
            if User.query.filter_by(username=username).first():
                return {'error': 'Username already exists'}, 400
            
            if User.query.filter_by(email=email).first():
                return {'error': 'Email already exists'}, 400
            
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Generate token
            token = generate_token(user.id)
            
            return {
                'message': 'User registered successfully',
                'token': token,
                'user': user_to_dict(user, include_email=True)
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Registration failed: {str(e)}'}, 500


class LoginResource(BaseResource):
    """User login resource"""
    
    @auth_rate_limit(limit=5, window=300)  # 5 login attempts per 5 minutes
    def post(self):
        """Authenticate user and return JWT token"""
        try:
            data = request.get_json(force=True, silent=True)
            
            if data is None:
                return {'error': 'No JSON data provided'}, 400
            
            if not data:
                return {'error': 'Empty data provided'}, 400
            
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            if not username or not password:
                return {'error': 'Username and password are required'}, 400
            
            # Find user by username or email
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if not user or not user.check_password(password):
                return {'error': 'Invalid credentials'}, 401
            
            if not user.is_active:
                return {'error': 'Account is deactivated'}, 401
            
            # Generate token
            token = generate_token(user.id)
            
            return {
                'message': 'Login successful',
                'token': token,
                'user': user_to_dict(user, include_email=True)
            }, 200
            
        except Exception as e:
            return {'error': f'Login failed: {str(e)}'}, 500


class VerifyTokenResource(BaseResource):
    """Token verification resource"""
    
    @api_rate_limit(limit=100, window=3600)  # 100 token verifications per hour
    @token_required
    def get(self):
        """Verify if token is valid and return user info"""
        return {
            'valid': True,
            'user': user_to_dict(self.current_user, include_email=True)
        }, 200