"""
Utility resources for the API
"""

from flask import request
from flask_restful import Resource
from app.extensions import db
from .base import BaseResource, token_required
import datetime


class HealthCheckResource(BaseResource):
    """API health check resource"""
    
    def get(self):
        """API health check"""
        return {
            'status': 'healthy',
            'version': '1.0.0',
            'timestamp': datetime.datetime.utcnow().isoformat()
        }, 200


class UploadAvatarResource(BaseResource):
    """Resource for avatar uploads"""
    
    @token_required
    def post(self):
        """Upload user avatar"""
        try:
            if 'file' not in request.files:
                return {'error': 'No file provided'}, 400
            
            file = request.files['file']
            if file.filename == '':
                return {'error': 'No file selected'}, 400
            
            # Import save_uploaded_file function
            from app.utils.file_helpers import save_uploaded_file
            
            filename = save_uploaded_file(file, 'avatars')
            if not filename:
                return {'error': 'Invalid file type'}, 400
            
            # Update user avatar
            user = self.current_user
            user.avatar_filename = filename
            db.session.commit()
            
            return {
                'message': 'Avatar uploaded successfully',
                'avatar_url': f"/static/uploads/avatars/{filename}"
            }, 200
            
        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to upload avatar: {str(e)}'}, 500


class UploadPostImageResource(BaseResource):
    """Resource for post image uploads"""
    
    @token_required
    def post(self):
        """Upload image for post"""
        try:
            if 'file' not in request.files:
                return {'error': 'No file provided'}, 400
            
            file = request.files['file']
            if file.filename == '':
                return {'error': 'No file selected'}, 400
            
            # Import save_uploaded_file function
            from app.utils.file_helpers import save_uploaded_file
            
            filename = save_uploaded_file(file, 'posts')
            if not filename:
                return {'error': 'Invalid file type'}, 400
            
            return {
                'message': 'Image uploaded successfully',
                'image_url': f"/static/uploads/posts/{filename}",
                'filename': filename
            }, 200
            
        except Exception as e:
            return {'error': f'Failed to upload image: {str(e)}'}, 500