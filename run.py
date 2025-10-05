"""
Flask Blog Application Entry Point

This is the main entry point for the Flask blog application using
the application factory pattern. This file demonstrates how to
create and run a Flask application with proper configuration.
"""

import os
from app import create_app
from app.extensions import db, socketio

# Create application instance using the factory pattern
# The configuration is determined by the FLASK_ENV environment variable
config_name = os.environ.get('FLASK_ENV', 'development')
app = create_app(config_name)


@app.shell_context_processor
def make_shell_context():
    """
    Make database models available in Flask shell.
    
    This function is called when running 'flask shell' and makes
    common objects available without importing them manually.
    """
    from app.models import User, Post, Comment, Category
    return {
        'db': db,
        'User': User,
        'Post': Post,
        'Comment': Comment,
        'Category': Category
    }


@app.cli.command()
def init_db():
    """
    Initialize the database with sample data.
    
    This CLI command can be run with 'flask init-db' to set up
    the database with initial data for development and testing.
    """
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    
    # Import models
    from app.models import User, Post, Comment, Category
    
    # Create sample categories
    categories = [
        Category(name='Python', description='Python programming tutorials'),
        Category(name='Flask', description='Flask web development'),
        Category(name='Database', description='Database design and management'),
        Category(name='Frontend', description='HTML, CSS, and JavaScript'),
        Category(name='DevOps', description='Deployment and operations')
    ]
    
    for category in categories:
        db.session.add(category)
    
    # Create admin user
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create regular user
    user = User(username='john_doe', email='john@example.com')
    user.set_password('password123')
    db.session.add(user)
    
    # Commit users and categories first to get their IDs
    db.session.commit()
    
    # Create sample posts
    posts = [
        Post(
            title='Welcome to Flask Learning!',
            content='This is your first post in the Flask learning application. Flask is a lightweight and powerful web framework for Python.',
            user_id=admin.id,
            category_id=categories[1].id  # Flask category
        ),
        Post(
            title='Getting Started with Python',
            content='Python is an excellent programming language for beginners and experts alike. In this post, we\'ll explore the basics.',
            user_id=user.id,
            category_id=categories[0].id  # Python category
        ),
        Post(
            title='Database Design Principles',
            content='Good database design is crucial for any web application. Let\'s discuss some fundamental principles.',
            user_id=admin.id,
            category_id=categories[2].id  # Database category
        )
    ]
    
    for post in posts:
        db.session.add(post)
    
    # Commit posts to get their IDs
    db.session.commit()
    
    # Create sample comments
    comments = [
        Comment(
            content='Great introduction! Looking forward to learning more about Flask.',
            post_id=posts[0].id,
            user_id=user.id
        ),
        Comment(
            content='Thanks for sharing this. Very helpful for beginners.',
            post_id=posts[1].id,
            user_id=admin.id
        )
    ]
    
    for comment in comments:
        db.session.add(comment)
    
    db.session.commit()
    print('Database initialized with sample data!')


if __name__ == '__main__':
    # Run the application with SocketIO support
    # In production, use a proper WSGI server like Gunicorn
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)