"""
API Blueprint for RESTful endpoints
Provides REST API endpoints using Flask-RESTful for the Flask blog application
"""

from flask import Blueprint
from flask_restful import Api

# Create API Blueprint
bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Create Flask-RESTful API instance
api = Api(bp)

# Import resources to register them
from . import auth_resources, user_resources, post_resources, comment_resources, category_resources, admin_resources

# Register authentication resources
api.add_resource(auth_resources.RegisterResource, '/auth/register')
api.add_resource(auth_resources.LoginResource, '/auth/login')
api.add_resource(auth_resources.VerifyTokenResource, '/auth/verify')

# Register user resources
api.add_resource(user_resources.UserListResource, '/users')
api.add_resource(user_resources.UserResource, '/users/<int:user_id>')
api.add_resource(user_resources.UserProfileResource, '/users/profile')

# Register post resources
api.add_resource(post_resources.PostListResource, '/posts')
api.add_resource(post_resources.PostResource, '/posts/<int:post_id>')

# Register comment resources
api.add_resource(comment_resources.PostCommentsResource, '/posts/<int:post_id>/comments')
api.add_resource(comment_resources.CommentResource, '/comments/<int:comment_id>')

# Register category resources
api.add_resource(category_resources.CategoryListResource, '/categories')

# Register admin resources
api.add_resource(admin_resources.AdminStatsResource, '/admin/stats')

# Register utility resources
from . import utility_resources
api.add_resource(utility_resources.HealthCheckResource, '/health')
api.add_resource(utility_resources.UploadAvatarResource, '/upload/avatar')
api.add_resource(utility_resources.UploadPostImageResource, '/upload/post-image')

# Register error handlers
from . import error_handlers