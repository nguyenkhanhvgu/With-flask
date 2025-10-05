"""
Flask-RESTX API Blueprint Initialization

This module initializes the Flask-RESTX API with all resources
and provides comprehensive API documentation with Swagger UI.
"""

from .restx_api import restx_bp, api, auth_ns, users_ns, posts_ns, comments_ns, categories_ns, admin_ns, utils_ns

# Import and register authentication resources
from .restx_auth_resources import RegisterResource, LoginResource, VerifyTokenResource, LogoutResource

auth_ns.add_resource(RegisterResource, '/register')
auth_ns.add_resource(LoginResource, '/login')
auth_ns.add_resource(VerifyTokenResource, '/verify')
auth_ns.add_resource(LogoutResource, '/logout')

# Import and register post resources
from .restx_post_resources import PostListResource, PostResource

posts_ns.add_resource(PostListResource, '')
posts_ns.add_resource(PostResource, '/<int:post_id>')

# Import and register utility resources
from .restx_utils_resources import HealthCheckResource, VersionResource, UploadAvatarResource, UploadPostImageResource

utils_ns.add_resource(HealthCheckResource, '/health')
utils_ns.add_resource(VersionResource, '/version')
utils_ns.add_resource(UploadAvatarResource, '/upload/avatar')
utils_ns.add_resource(UploadPostImageResource, '/upload/post-image')

# TODO: Add other resource imports and registrations as they are created
# from .restx_user_resources import UserListResource, UserResource
# from .restx_comment_resources import CommentListResource, CommentResource
# from .restx_category_resources import CategoryListResource, CategoryResource
# from .restx_admin_resources import AdminStatsResource

# users_ns.add_resource(UserListResource, '')
# users_ns.add_resource(UserResource, '/<int:user_id>')

# comments_ns.add_resource(CommentListResource, '')
# comments_ns.add_resource(CommentResource, '/<int:comment_id>')

# categories_ns.add_resource(CategoryListResource, '')
# categories_ns.add_resource(CategoryResource, '/<int:category_id>')

# admin_ns.add_resource(AdminStatsResource, '/stats')

# Export the blueprint for registration in the main app
__all__ = ['restx_bp']