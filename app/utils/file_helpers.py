"""
File Upload Helpers

This module contains utility functions for handling file uploads
including validation, saving, and image processing.
"""

import os
import uuid
from PIL import Image
from flask import current_app
from werkzeug.utils import secure_filename


def allowed_file(filename):
    """
    Check if the file extension is allowed.
    
    Args:
        filename (str): The filename to check
        
    Returns:
        bool: True if the file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in [ext[1:] for ext in current_app.config['UPLOAD_EXTENSIONS']]


def save_uploaded_file(file, upload_type='posts'):
    """
    Save uploaded file with unique name and return filename.
    
    Args:
        file: The uploaded file object
        upload_type (str): The type of upload ('posts' or 'avatars')
        
    Returns:
        str: The unique filename if successful, None otherwise
        
    This function demonstrates file handling best practices including
    unique filename generation and image resizing.
    """
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_ext = os.path.splitext(secure_filename(file.filename))[1]
        unique_filename = str(uuid.uuid4()) + file_ext
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_PATH'], upload_type)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save original file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Resize image if it's too large
        try:
            with Image.open(file_path) as img:
                # Resize for posts (max 800px width) or avatars (max 300px)
                max_size = (300, 300) if upload_type == 'avatars' else (800, 600)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(file_path, optimize=True, quality=85)
        except Exception as e:
            print(f"Error resizing image: {e}")
        
        return unique_filename
    return None