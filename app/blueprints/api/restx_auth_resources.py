"""
Flask-RESTX Authentication Resources

This module contains authentication-related API endpoints with
comprehensive documentation using Flask-RESTX decorators.
"""

from flask import request, current_app
from flask_restx import Resource
from werkzeug.security import check_password_hash, generate_password_hash
from app.models.user import User
from app.extensions import db
from .restx_api import auth_ns
from .models import (
    login_model, register_model, token_response_model, 
    user_profile_model, error_model, success_model
)
from .base import generate_token, verify_token, token_required


@auth_ns.route('/register')
class RegisterResource(Resource):
    """User registration endpoint"""
    
    @auth_ns.doc('register_user')
    @auth_ns.expect(register_model, validate=True)
    @auth_ns.response(201, 'User registered successfully', token_response_model)
    @auth_ns.response(400, 'Validation error', error_model)
    @auth_ns.response(409, 'User already exists', error_model)
    def post(self):
        """
        Register a new user account
        
        Creates a new user account with the provided credentials.
        Returns a JWT token for immediate authentication.
        
        **Example Request:**
        ```json
        {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "secure_password123",
            "confirm_password": "secure_password123"
        }
        ```
        
        **Example Response:**
        ```json
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "Bearer",
            "expires_in": 604800,
            "user": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "is_admin": false
            }
        }
        ```
        """
        data = request.get_json()
        
        # Validate password confirmation
        if data['password'] != data['confirm_password']:
            return {'error': 'Bad Request', 'message': 'Passwords do not match'}, 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return {'error': 'Conflict', 'message': 'Username already exists'}, 409
        
        if User.query.filter_by(email=data['email']).first():
            return {'error': 'Conflict', 'message': 'Email already registered'}, 409
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password'])
        )
        
        try:
            db.session.add(user)
            db.session.commit()
            
            # Generate token
            token = generate_token(user.id)
            
            return {
                'access_token': token,
                'token_type': 'Bearer',
                'expires_in': 604800,  # 7 days
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_admin': user.is_admin,
                    'created_at': user.created_at.isoformat()
                }
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': 'Internal Server Error', 'message': 'Registration failed'}, 500


@auth_ns.route('/login')
class LoginResource(Resource):
    """User login endpoint"""
    
    @auth_ns.doc('login_user')
    @auth_ns.expect(login_model, validate=True)
    @auth_ns.response(200, 'Login successful', token_response_model)
    @auth_ns.response(401, 'Invalid credentials', error_model)
    @auth_ns.response(403, 'Account inactive', error_model)
    def post(self):
        """
        Authenticate user and return JWT token
        
        Validates user credentials and returns a JWT token for API access.
        The token should be included in the Authorization header for protected endpoints.
        
        **Example Request:**
        ```json
        {
            "username": "john_doe",
            "password": "secure_password123"
        }
        ```
        
        **Example Response:**
        ```json
        {
            "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "token_type": "Bearer",
            "expires_in": 604800,
            "user": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com"
            }
        }
        ```
        
        **Usage:**
        Include the token in subsequent requests:
        ```
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
        ```
        """
        data = request.get_json()
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == data['username']) | 
            (User.email == data['username'])
        ).first()
        
        if not user or not check_password_hash(user.password_hash, data['password']):
            return {'error': 'Unauthorized', 'message': 'Invalid credentials'}, 401
        
        if not user.is_active:
            return {'error': 'Forbidden', 'message': 'Account is inactive'}, 403
        
        # Update last seen
        from datetime import datetime
        user.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id)
        
        return {
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': 604800,  # 7 days
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_admin': user.is_admin,
                'last_seen': user.last_seen.isoformat()
            }
        }, 200


@auth_ns.route('/verify')
class VerifyTokenResource(Resource):
    """Token verification endpoint"""
    
    @auth_ns.doc('verify_token')
    @auth_ns.doc(security='Bearer')
    @auth_ns.response(200, 'Token is valid', user_profile_model)
    @auth_ns.response(401, 'Invalid or expired token', error_model)
    @token_required
    def get(self):
        """
        Verify JWT token and return user information
        
        Validates the provided JWT token and returns the associated user information.
        This endpoint can be used to check if a token is still valid and get current user data.
        
        **Headers Required:**
        ```
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
        ```
        
        **Example Response:**
        ```json
        {
            "id": 1,
            "username": "john_doe",
            "email": "john@example.com",
            "is_admin": false,
            "is_active": true,
            "created_at": "2023-01-15T10:30:00Z",
            "last_seen": "2023-12-01T15:45:00Z",
            "posts_count": 5,
            "comments_count": 12
        }
        ```
        """
        return {
            'id': self.current_user.id,
            'username': self.current_user.username,
            'email': self.current_user.email,
            'is_admin': self.current_user.is_admin,
            'is_active': self.current_user.is_active,
            'created_at': self.current_user.created_at.isoformat(),
            'last_seen': self.current_user.last_seen.isoformat() if self.current_user.last_seen else None,
            'posts_count': len(self.current_user.posts),
            'comments_count': len(self.current_user.comments)
        }, 200


@auth_ns.route('/logout')
class LogoutResource(Resource):
    """User logout endpoint"""
    
    @auth_ns.doc('logout_user')
    @auth_ns.doc(security='Bearer')
    @auth_ns.response(200, 'Logout successful', success_model)
    @auth_ns.response(401, 'Invalid token', error_model)
    @token_required
    def post(self):
        """
        Logout user (invalidate token)
        
        Logs out the current user. Note: Since JWT tokens are stateless,
        this endpoint primarily serves to update the user's last seen time.
        In a production environment, you might implement token blacklisting.
        
        **Headers Required:**
        ```
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
        ```
        
        **Example Response:**
        ```json
        {
            "success": true,
            "message": "Logout successful"
        }
        ```
        
        **Note:** After logout, the client should discard the JWT token.
        """
        # Update last seen time
        from datetime import datetime
        self.current_user.last_seen = datetime.utcnow()
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Logout successful'
        }, 200