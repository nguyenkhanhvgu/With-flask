"""
Flask Blog Application Factory

This module implements the application factory pattern for the Flask blog application.
The factory pattern allows for better configuration management, testing, and deployment
by creating the Flask app instance dynamically with different configurations.
"""

from flask import Flask
from app.extensions import db, migrate, login_manager, mail, socketio
from app.config import config


def create_app(config_name='development'):
    """
    Application factory function that creates and configures a Flask application instance.
    
    Args:
        config_name (str): The configuration environment to use ('development', 'testing', 'production')
        
    Returns:
        Flask: Configured Flask application instance
        
    This function demonstrates the application factory pattern, which is a Flask best practice
    for creating applications that can be easily configured for different environments.
    """
    # Create Flask application instance
    app = Flask(__name__)
    
    # Load configuration based on environment
    app.config.from_object(config[config_name])
    
    # Initialize Flask extensions with the app instance
    # This pattern allows extensions to be configured before the app is created
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register user loader for Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID for Flask-Login"""
        return User.query.get(int(user_id))
    
    # Register blueprints
    # Blueprints allow for modular organization of routes and functionality
    register_blueprints(app)
    
    # Register template filters
    register_template_filters(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def register_blueprints(app):
    """
    Register all application blueprints.
    
    Args:
        app (Flask): The Flask application instance
        
    This function demonstrates how to organize a Flask application using blueprints,
    which provide a way to group related functionality and routes.
    """
    # Import blueprints here to avoid circular imports
    from app.blueprints.main import bp as main_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.blog import bp as blog_bp
    from app.blueprints.admin import bp as admin_bp
    from app.blueprints.api import bp as api_bp
    
    # Register blueprints with URL prefixes
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api/v1')


def register_template_filters(app):
    """
    Register custom Jinja2 template filters.
    
    Args:
        app (Flask): The Flask application instance
    """
    @app.template_filter('nl2br')
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks"""
        return text.replace('\n', '<br>\n') if text else ''


def register_error_handlers(app):
    """
    Register custom error handlers for the application.
    
    Args:
        app (Flask): The Flask application instance
    """
    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        from app.extensions import db
        db.session.rollback()
        return render_template('errors/500.html'), 500