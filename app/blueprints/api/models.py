"""
Flask-RESTX API Models for Request/Response Serialization

This module defines all the API models used for request validation
and response serialization in the Flask-RESTX documentation.
"""

from flask_restx import fields
from .restx_api import api

# Base models
pagination_model = api.model('Pagination', {
    'page': fields.Integer(description='Current page number', example=1),
    'pages': fields.Integer(description='Total number of pages', example=5),
    'per_page': fields.Integer(description='Items per page', example=10),
    'total': fields.Integer(description='Total number of items', example=42),
    'has_next': fields.Boolean(description='Whether there is a next page', example=True),
    'has_prev': fields.Boolean(description='Whether there is a previous page', example=False)
})

error_model = api.model('Error', {
    'error': fields.String(description='Error type', example='Bad Request'),
    'message': fields.String(description='Error message', example='Invalid input data')
})

success_model = api.model('Success', {
    'success': fields.Boolean(description='Operation success status', example=True),
    'message': fields.String(description='Success message', example='Operation completed successfully')
})

# Authentication models
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username or email', example='john_doe'),
    'password': fields.String(required=True, description='User password', example='secure_password123')
})

register_model = api.model('Register', {
    'username': fields.String(required=True, description='Unique username', example='john_doe'),
    'email': fields.String(required=True, description='Valid email address', example='john@example.com'),
    'password': fields.String(required=True, description='Password (min 8 characters)', example='secure_password123'),
    'confirm_password': fields.String(required=True, description='Password confirmation', example='secure_password123')
})

token_response_model = api.model('TokenResponse', {
    'access_token': fields.String(description='JWT access token', example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'),
    'token_type': fields.String(description='Token type', example='Bearer'),
    'expires_in': fields.Integer(description='Token expiration time in seconds', example=604800),
    'user': fields.Raw(description='User information')
})

# User models
user_profile_model = api.model('UserProfile', {
    'id': fields.Integer(description='User ID', example=1),
    'username': fields.String(description='Username', example='john_doe'),
    'email': fields.String(description='Email address', example='john@example.com'),
    'avatar': fields.String(description='Avatar URL', example='/static/uploads/avatars/avatar.jpg'),
    'is_admin': fields.Boolean(description='Admin status', example=False),
    'is_active': fields.Boolean(description='Account active status', example=True),
    'created_at': fields.DateTime(description='Account creation date', example='2023-01-15T10:30:00Z'),
    'last_seen': fields.DateTime(description='Last activity date', example='2023-12-01T15:45:00Z'),
    'posts_count': fields.Integer(description='Number of posts created', example=5),
    'comments_count': fields.Integer(description='Number of comments made', example=12),
    'followers_count': fields.Integer(description='Number of followers', example=8),
    'following_count': fields.Integer(description='Number of users following', example=15)
})

user_list_model = api.model('UserList', {
    'id': fields.Integer(description='User ID', example=1),
    'username': fields.String(description='Username', example='john_doe'),
    'avatar': fields.String(description='Avatar URL', example='/static/uploads/avatars/avatar.jpg'),
    'is_admin': fields.Boolean(description='Admin status', example=False),
    'created_at': fields.DateTime(description='Account creation date', example='2023-01-15T10:30:00Z'),
    'posts_count': fields.Integer(description='Number of posts created', example=5)
})

user_update_model = api.model('UserUpdate', {
    'email': fields.String(description='New email address', example='newemail@example.com'),
    'bio': fields.String(description='User biography', example='Software developer and blogger'),
    'location': fields.String(description='User location', example='San Francisco, CA')
})

# Category models
category_model = api.model('Category', {
    'id': fields.Integer(description='Category ID', example=1),
    'name': fields.String(description='Category name', example='Technology'),
    'description': fields.String(description='Category description', example='Posts about technology and programming'),
    'posts_count': fields.Integer(description='Number of posts in category', example=25)
})

category_create_model = api.model('CategoryCreate', {
    'name': fields.String(required=True, description='Category name', example='Technology'),
    'description': fields.String(description='Category description', example='Posts about technology and programming')
})

# Post models
post_summary_model = api.model('PostSummary', {
    'id': fields.Integer(description='Post ID', example=1),
    'title': fields.String(description='Post title', example='Getting Started with Flask'),
    'excerpt': fields.String(description='Post excerpt', example='Learn the basics of Flask web framework...'),
    'author': fields.Raw(description='Post author'),
    'category': fields.Raw(description='Post category'),
    'image': fields.String(description='Featured image URL', example='/static/uploads/posts/image.jpg'),
    'created_at': fields.DateTime(description='Creation date', example='2023-12-01T10:30:00Z'),
    'updated_at': fields.DateTime(description='Last update date', example='2023-12-01T15:45:00Z'),
    'comments_count': fields.Integer(description='Number of comments', example=3),
    'likes_count': fields.Integer(description='Number of likes', example=15),
    'views_count': fields.Integer(description='Number of views', example=120)
})

post_detail_model = api.model('PostDetail', {
    'id': fields.Integer(description='Post ID', example=1),
    'title': fields.String(description='Post title', example='Getting Started with Flask'),
    'content': fields.String(description='Full post content', example='Flask is a lightweight WSGI web application framework...'),
    'author': fields.Raw(description='Post author'),
    'category': fields.Raw(description='Post category'),
    'image': fields.String(description='Featured image URL', example='/static/uploads/posts/image.jpg'),
    'created_at': fields.DateTime(description='Creation date', example='2023-12-01T10:30:00Z'),
    'updated_at': fields.DateTime(description='Last update date', example='2023-12-01T15:45:00Z'),
    'comments_count': fields.Integer(description='Number of comments', example=3),
    'likes_count': fields.Integer(description='Number of likes', example=15),
    'views_count': fields.Integer(description='Number of views', example=120),
    'tags': fields.List(fields.String, description='Post tags', example=['flask', 'python', 'web-development'])
})

post_create_model = api.model('PostCreate', {
    'title': fields.String(required=True, description='Post title', example='Getting Started with Flask'),
    'content': fields.String(required=True, description='Post content', example='Flask is a lightweight WSGI web application framework...'),
    'category_id': fields.Integer(description='Category ID', example=1),
    'tags': fields.List(fields.String, description='Post tags', example=['flask', 'python'])
})

post_update_model = api.model('PostUpdate', {
    'title': fields.String(description='Post title', example='Updated: Getting Started with Flask'),
    'content': fields.String(description='Post content', example='Updated content...'),
    'category_id': fields.Integer(description='Category ID', example=2),
    'tags': fields.List(fields.String, description='Post tags', example=['flask', 'python', 'tutorial'])
})

# Comment models
comment_model = api.model('Comment', {
    'id': fields.Integer(description='Comment ID', example=1),
    'content': fields.String(description='Comment content', example='Great post! Very helpful.'),
    'author': fields.Raw(description='Comment author'),
    'post_id': fields.Integer(description='Post ID', example=1),
    'created_at': fields.DateTime(description='Creation date', example='2023-12-01T16:30:00Z'),
    'likes_count': fields.Integer(description='Number of likes', example=2)
})

comment_create_model = api.model('CommentCreate', {
    'content': fields.String(required=True, description='Comment content', example='Great post! Very helpful.')
})

comment_update_model = api.model('CommentUpdate', {
    'content': fields.String(required=True, description='Updated comment content', example='Updated: Great post! Very helpful.')
})

# Response models with pagination
users_response_model = api.model('UsersResponse', {
    'users': fields.List(fields.Raw, description='List of users'),
    'pagination': fields.Raw(description='Pagination information')
})

posts_response_model = api.model('PostsResponse', {
    'posts': fields.List(fields.Raw, description='List of posts'),
    'pagination': fields.Raw(description='Pagination information')
})

comments_response_model = api.model('CommentsResponse', {
    'comments': fields.List(fields.Raw, description='List of comments'),
    'pagination': fields.Raw(description='Pagination information')
})

categories_response_model = api.model('CategoriesResponse', {
    'categories': fields.List(fields.Raw, description='List of categories')
})

# Admin models
admin_stats_model = api.model('AdminStats', {
    'total_users': fields.Integer(description='Total number of users', example=150),
    'total_posts': fields.Integer(description='Total number of posts', example=75),
    'total_comments': fields.Integer(description='Total number of comments', example=300),
    'total_categories': fields.Integer(description='Total number of categories', example=8),
    'active_users_today': fields.Integer(description='Active users today', example=25),
    'posts_this_month': fields.Integer(description='Posts created this month', example=12),
    'popular_categories': fields.List(fields.Raw, description='Most popular categories')
})

# Upload models
upload_response_model = api.model('UploadResponse', {
    'success': fields.Boolean(description='Upload success status', example=True),
    'filename': fields.String(description='Uploaded filename', example='avatar_123.jpg'),
    'url': fields.String(description='File URL', example='/static/uploads/avatars/avatar_123.jpg'),
    'message': fields.String(description='Upload message', example='File uploaded successfully')
})

# Health check model
health_check_model = api.model('HealthCheck', {
    'status': fields.String(description='Service status', example='healthy'),
    'timestamp': fields.DateTime(description='Check timestamp', example='2023-12-01T10:30:00Z'),
    'version': fields.String(description='API version', example='1.0'),
    'database': fields.String(description='Database status', example='connected'),
    'cache': fields.String(description='Cache status', example='connected')
})