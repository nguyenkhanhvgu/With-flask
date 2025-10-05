"""
Flask-RESTX Utility Resources

This module contains utility API endpoints like health checks
and file uploads with comprehensive documentation.
"""

from flask import request, current_app
from flask_restx import Resource
from datetime import datetime
from app.extensions import db
from .restx_api import utils_ns
from .models import health_check_model, upload_response_model, error_model
from .base import token_required
import os
from werkzeug.utils import secure_filename


@utils_ns.route('/health')
class HealthCheckResource(Resource):
    """System health check endpoint"""
    
    @utils_ns.doc('health_check')
    @utils_ns.response(200, 'System is healthy', health_check_model)
    @utils_ns.response(503, 'System is unhealthy', error_model)
    def get(self):
        """
        Check system health status
        
        Returns the current health status of the API and its dependencies.
        This endpoint can be used for monitoring and load balancer health checks.
        
        **Example Response (Healthy):**
        ```json
        {
            "status": "healthy",
            "timestamp": "2023-12-01T10:30:00Z",
            "version": "1.0",
            "database": "connected",
            "cache": "connected"
        }
        ```
        
        **Example Response (Unhealthy):**
        ```json
        {
            "status": "unhealthy",
            "timestamp": "2023-12-01T10:30:00Z",
            "version": "1.0",
            "database": "disconnected",
            "cache": "connected"
        }
        ```
        
        **Status Codes:**
        - `200`: All systems operational
        - `503`: One or more systems are down
        """
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': '1.0',
            'database': 'unknown',
            'cache': 'unknown'
        }
        
        # Check database connection
        try:
            db.session.execute('SELECT 1')
            health_status['database'] = 'connected'
        except Exception:
            health_status['database'] = 'disconnected'
            health_status['status'] = 'unhealthy'
        
        # Check cache connection (if Redis is configured)
        try:
            from app.extensions import cache
            if hasattr(cache, 'cache') and cache.cache:
                # Try to set and get a test value
                cache.set('health_check', 'ok', timeout=1)
                if cache.get('health_check') == 'ok':
                    health_status['cache'] = 'connected'
                else:
                    health_status['cache'] = 'disconnected'
            else:
                health_status['cache'] = 'not_configured'
        except Exception:
            health_status['cache'] = 'disconnected'
        
        # Return appropriate status code
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        return health_status, status_code


@utils_ns.route('/version')
class VersionResource(Resource):
    """API version information endpoint"""
    
    @utils_ns.doc('get_version')
    @utils_ns.response(200, 'Version information retrieved')
    def get(self):
        """
        Get API version information
        
        Returns detailed version information about the API including
        build information and supported features.
        
        **Example Response:**
        ```json
        {
            "api_version": "1.0",
            "build_date": "2023-12-01",
            "flask_version": "2.3.2",
            "python_version": "3.9.0",
            "features": [
                "authentication",
                "file_upload",
                "real_time_notifications",
                "caching"
            ]
        }
        ```
        """
        import sys
        import flask
        
        return {
            'api_version': '1.0',
            'build_date': '2023-12-01',
            'flask_version': flask.__version__,
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'features': [
                'authentication',
                'file_upload',
                'real_time_notifications',
                'caching',
                'rate_limiting',
                'api_documentation'
            ]
        }, 200


@utils_ns.route('/upload/avatar')
class UploadAvatarResource(Resource):
    """Avatar upload endpoint"""
    
    @utils_ns.doc('upload_avatar')
    @utils_ns.doc(security='Bearer')
    @utils_ns.response(200, 'Avatar uploaded successfully', upload_response_model)
    @utils_ns.response(400, 'Invalid file', error_model)
    @utils_ns.response(401, 'Authentication required', error_model)
    @utils_ns.response(413, 'File too large', error_model)
    @token_required
    def post(self):
        """
        Upload user avatar image
        
        Uploads and sets a new avatar image for the authenticated user.
        Supports common image formats (JPEG, PNG, GIF) with size limits.
        
        **Headers Required:**
        ```
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
        Content-Type: multipart/form-data
        ```
        
        **Form Data:**
        - `file`: Image file (JPEG, PNG, GIF)
        - Maximum file size: 5MB
        - Recommended dimensions: 200x200 pixels
        
        **Example Response:**
        ```json
        {
            "success": true,
            "filename": "avatar_user123_20231201.jpg",
            "url": "/static/uploads/avatars/avatar_user123_20231201.jpg",
            "message": "Avatar uploaded successfully"
        }
        ```
        
        **Error Responses:**
        - `400`: Invalid file format or missing file
        - `413`: File size exceeds limit (5MB)
        """
        if 'file' not in request.files:
            return {'error': 'Bad Request', 'message': 'No file provided'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': 'Bad Request', 'message': 'No file selected'}, 400
        
        # Check file extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return {'error': 'Bad Request', 'message': 'Invalid file format. Allowed: PNG, JPG, JPEG, GIF'}, 400
        
        # Check file size (5MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 5 * 1024 * 1024:  # 5MB
            return {'error': 'Payload Too Large', 'message': 'File size exceeds 5MB limit'}, 413
        
        try:
            # Generate secure filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"avatar_{self.current_user.id}_{timestamp}.{file.filename.rsplit('.', 1)[1].lower()}"
            filename = secure_filename(filename)
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.static_folder, 'uploads', 'avatars')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            # Update user avatar filename
            self.current_user.avatar_filename = filename
            db.session.commit()
            
            return {
                'success': True,
                'filename': filename,
                'url': f"/static/uploads/avatars/{filename}",
                'message': 'Avatar uploaded successfully'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': 'Internal Server Error', 'message': 'Failed to upload avatar'}, 500


@utils_ns.route('/upload/post-image')
class UploadPostImageResource(Resource):
    """Post image upload endpoint"""
    
    @utils_ns.doc('upload_post_image')
    @utils_ns.doc(security='Bearer')
    @utils_ns.response(200, 'Image uploaded successfully', upload_response_model)
    @utils_ns.response(400, 'Invalid file', error_model)
    @utils_ns.response(401, 'Authentication required', error_model)
    @utils_ns.response(413, 'File too large', error_model)
    @token_required
    def post(self):
        """
        Upload image for blog post
        
        Uploads an image that can be used in blog posts. The uploaded image
        can be referenced in post content or used as a featured image.
        
        **Headers Required:**
        ```
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
        Content-Type: multipart/form-data
        ```
        
        **Form Data:**
        - `file`: Image file (JPEG, PNG, GIF, WebP)
        - Maximum file size: 10MB
        - Recommended max dimensions: 1920x1080 pixels
        
        **Example Response:**
        ```json
        {
            "success": true,
            "filename": "post_img_20231201_143022.jpg",
            "url": "/static/uploads/posts/post_img_20231201_143022.jpg",
            "message": "Image uploaded successfully"
        }
        ```
        
        **Usage in Posts:**
        The returned URL can be used in post content:
        ```markdown
        ![Image description](/static/uploads/posts/post_img_20231201_143022.jpg)
        ```
        """
        if 'file' not in request.files:
            return {'error': 'Bad Request', 'message': 'No file provided'}, 400
        
        file = request.files['file']
        if file.filename == '':
            return {'error': 'Bad Request', 'message': 'No file selected'}, 400
        
        # Check file extension
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return {'error': 'Bad Request', 'message': 'Invalid file format. Allowed: PNG, JPG, JPEG, GIF, WebP'}, 400
        
        # Check file size (10MB limit for post images)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 10 * 1024 * 1024:  # 10MB
            return {'error': 'Payload Too Large', 'message': 'File size exceeds 10MB limit'}, 413
        
        try:
            # Generate secure filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            extension = file.filename.rsplit('.', 1)[1].lower()
            filename = f"post_img_{timestamp}.{extension}"
            filename = secure_filename(filename)
            
            # Create upload directory if it doesn't exist
            upload_dir = os.path.join(current_app.static_folder, 'uploads', 'posts')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            
            return {
                'success': True,
                'filename': filename,
                'url': f"/static/uploads/posts/{filename}",
                'message': 'Image uploaded successfully'
            }, 200
            
        except Exception as e:
            return {'error': 'Internal Server Error', 'message': 'Failed to upload image'}, 500