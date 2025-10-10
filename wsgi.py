#!/usr/bin/env python3
"""
WSGI entry point for production deployment with Gunicorn.
This file is used by Gunicorn to serve the Flask application.
"""

import os
import sys
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from app import create_app

# Create the Flask application instance
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == "__main__":
    # This allows running the WSGI file directly for testing
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8000)))