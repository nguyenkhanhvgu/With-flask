"""
Configuration Management for Flask Blog Application

This module demonstrates Flask configuration best practices by providing
environment-specific configuration classes. This approach allows for
easy switching between development, testing, and production environments.
"""

import os
from datetime import timedelta


class Config:
    """
    Base configuration class containing common settings.
    
    This class contains configuration that is shared across all environments.
    Environment-specific classes inherit from this base class and override
    or add settings as needed.
    """
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-flask-learning-app-2024'
    
    # Session Configuration
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'flask_session'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST = True
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    
    # Database Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'Flask Blog <noreply@flaskblog.com>')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@flaskblog.com')
    
    # Application Configuration
    POSTS_PER_PAGE = 5
    COMMENTS_PER_PAGE = 10
    USERS_PER_PAGE = 20
    
    @staticmethod
    def init_app(app):
        """
        Initialize application-specific configuration.
        
        Args:
            app (Flask): The Flask application instance
            
        This method can be overridden in subclasses to perform
        environment-specific initialization.
        """
        pass


class DevelopmentConfig(Config):
    """
    Development environment configuration.
    
    This configuration is optimized for development with debug mode enabled,
    detailed logging, and a local SQLite database.
    """
    
    DEBUG = True
    
    # Database Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f'sqlite:///{os.path.join(basedir, "..", "blog.db")}'
    
    # Upload Path Configuration
    UPLOAD_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'static', 'uploads')
    
    # Development-specific settings
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries in console
    WTF_CSRF_ENABLED = True
    
    @staticmethod
    def init_app(app):
        """Initialize development-specific configuration."""
        Config.init_app(app)
        
        # Ensure upload directories exist
        upload_path = app.config['UPLOAD_PATH']
        os.makedirs(os.path.join(upload_path, 'posts'), exist_ok=True)
        os.makedirs(os.path.join(upload_path, 'avatars'), exist_ok=True)


class TestingConfig(Config):
    """
    Testing environment configuration.
    
    This configuration is optimized for running tests with an in-memory
    database and disabled CSRF protection for easier testing.
    """
    
    TESTING = True
    DEBUG = True
    
    # Use in-memory SQLite database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF protection for testing
    WTF_CSRF_ENABLED = False
    
    # Disable email sending during tests
    MAIL_SUPPRESS_SEND = True
    
    # Fast password hashing for tests
    BCRYPT_LOG_ROUNDS = 4
    
    # Upload Path Configuration (use temp directory)
    import tempfile
    UPLOAD_PATH = tempfile.mkdtemp()
    
    @staticmethod
    def init_app(app):
        """Initialize testing-specific configuration."""
        Config.init_app(app)


class ProductionConfig(Config):
    """
    Production environment configuration.
    
    This configuration is optimized for production deployment with
    security enhancements and performance optimizations.
    """
    
    DEBUG = False
    
    # Database Configuration (use environment variable)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///blog.db'
    
    # Security Configuration
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    SESSION_COOKIE_HTTPONLY = True
    
    # Upload Path Configuration
    UPLOAD_PATH = os.environ.get('UPLOAD_PATH') or \
        os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'static', 'uploads')
    
    # Performance Configuration
    SQLALCHEMY_RECORD_QUERIES = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    @staticmethod
    def init_app(app):
        """Initialize production-specific configuration."""
        Config.init_app(app)
        
        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


# Configuration dictionary for easy access
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}