"""
Flask-RESTX API Documentation Setup

This module sets up Flask-RESTX for interactive API documentation
with Swagger UI and comprehensive API models.
"""

from flask import Blueprint
from flask_restx import Api, Namespace
from werkzeug.exceptions import BadRequest, Unauthorized, Forbidden, NotFound, InternalServerError

# Create API Blueprint for Flask-RESTX
restx_bp = Blueprint('api_docs', __name__, url_prefix='/api/v1')

# Configure Flask-RESTX API with documentation
api = Api(
    restx_bp,
    version='1.0',
    title='Flask Blog API',
    description='A comprehensive REST API for the Flask Blog application with educational features',
    doc='/docs/',  # Swagger UI endpoint
    contact='developer@example.com',
    license='MIT',
    license_url='https://opensource.org/licenses/MIT',
    authorizations={
        'Bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'JWT Authorization header using the Bearer scheme. Example: "Authorization: Bearer {token}"'
        }
    },
    security='Bearer'
)

# Create namespaces for different API sections
auth_ns = Namespace('auth', description='Authentication operations')
users_ns = Namespace('users', description='User management operations')
posts_ns = Namespace('posts', description='Blog post operations')
comments_ns = Namespace('comments', description='Comment operations')
categories_ns = Namespace('categories', description='Category operations')
admin_ns = Namespace('admin', description='Administrative operations')
utils_ns = Namespace('utils', description='Utility operations')

# Add namespaces to API
api.add_namespace(auth_ns)
api.add_namespace(users_ns)
api.add_namespace(posts_ns)
api.add_namespace(comments_ns)
api.add_namespace(categories_ns)
api.add_namespace(admin_ns)
api.add_namespace(utils_ns)

# Error handlers for consistent API responses
@api.errorhandler(BadRequest)
def bad_request(error):
    """Handle 400 Bad Request errors"""
    return {'error': 'Bad request', 'message': str(error)}, 400

@api.errorhandler(Unauthorized)
def unauthorized(error):
    """Handle 401 Unauthorized errors"""
    return {'error': 'Unauthorized', 'message': 'Authentication required'}, 401

@api.errorhandler(Forbidden)
def forbidden(error):
    """Handle 403 Forbidden errors"""
    return {'error': 'Forbidden', 'message': 'Insufficient permissions'}, 403

@api.errorhandler(NotFound)
def not_found(error):
    """Handle 404 Not Found errors"""
    return {'error': 'Not found', 'message': 'Resource not found'}, 404

@api.errorhandler(InternalServerError)
def internal_error(error):
    """Handle 500 Internal Server Error"""
    return {'error': 'Internal server error', 'message': 'An unexpected error occurred'}, 500

@api.errorhandler(Exception)
def default_error_handler(error):
    """Handle all other exceptions"""
    return {'error': 'Internal server error', 'message': 'An unexpected error occurred'}, 500