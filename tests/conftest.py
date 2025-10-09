"""
Pytest configuration and fixtures for Flask blog application testing.

This module provides shared fixtures and configuration for all test modules,
including application setup, database management, and test data factories.
"""

import os
import tempfile
import pytest
from app import create_app, db
from app.models import User, Post, Comment, Category, Role, Permission
from tests.factories import UserFactory, PostFactory, CommentFactory, CategoryFactory, NotificationFactory


@pytest.fixture(scope='session')
def app():
    """
    Create and configure a new app instance for each test session.
    
    This fixture creates a Flask application configured for testing,
    with a temporary SQLite database that's isolated from the main database.
    """
    # Configure the app for testing with in-memory database
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SECRET_KEY': 'test-secret-key',
        'MAIL_SUPPRESS_SEND': True,
        'CACHE_TYPE': 'simple',  # Use simple cache for testing
        'REDIS_URL': None,  # Disable Redis for testing
    }
    
    # Create the app with test configuration
    app = create_app(test_config)
    
    # Create application context
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        # Create default roles and permissions for testing
        _create_default_roles()
        
        yield app
        
        # Cleanup: drop all tables and close connections
        db.drop_all()
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    """
    Create a test client for the Flask application.
    
    This fixture provides a test client that can be used to make
    requests to the application during testing.
    """
    return app.test_client()


@pytest.fixture
def runner(app):
    """
    Create a test runner for the Flask application.
    
    This fixture provides a test runner for testing CLI commands.
    """
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """
    Create a database session for testing.
    
    This fixture provides a database session that's automatically
    rolled back after each test to ensure test isolation.
    """
    with app.app_context():
        yield db.session


@pytest.fixture
def user(db_session):
    """
    Create a test user.
    
    This fixture creates a basic user for testing purposes.
    """
    user = UserFactory()
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def admin_user(db_session):
    """
    Create a test admin user.
    
    This fixture creates an admin user with elevated privileges.
    """
    admin_role = Role.query.filter_by(name='admin').first()
    user = UserFactory(role=admin_role, is_active=True, email_confirmed=True)
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def authenticated_user(client, user):
    """
    Create an authenticated user session.
    
    This fixture logs in a user and provides the authenticated session.
    """
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user.id)
        sess['_fresh'] = True
    return user


@pytest.fixture
def category(db_session):
    """
    Create a test category.
    
    This fixture creates a basic category for testing blog posts.
    """
    category = CategoryFactory()
    db_session.add(category)
    db_session.commit()
    return category


@pytest.fixture
def post(db_session, user, category):
    """
    Create a test blog post.
    
    This fixture creates a blog post with associated user and category.
    """
    post = PostFactory()
    post.user_id = user.id
    post.category_id = category.id
    db_session.add(post)
    db_session.commit()
    return post


@pytest.fixture
def comment(db_session, user, post):
    """
    Create a test comment.
    
    This fixture creates a comment associated with a user and post.
    """
    comment = CommentFactory()
    comment.user_id = user.id
    comment.post_id = post.id
    db_session.add(comment)
    db_session.commit()
    return comment


@pytest.fixture
def multiple_users(db_session):
    """
    Create multiple test users.
    
    This fixture creates a list of users for testing scenarios
    that require multiple users.
    """
    users = UserFactory.create_batch(5)
    for user in users:
        db_session.add(user)
    db_session.commit()
    return users


@pytest.fixture
def multiple_posts(db_session, user, category):
    """
    Create multiple test posts.
    
    This fixture creates a list of posts for testing scenarios
    that require multiple posts.
    """
    posts = PostFactory.create_batch(10)
    for post in posts:
        post.user_id = user.id
        post.category_id = category.id
        db_session.add(post)
    db_session.commit()
    return posts


def _create_default_roles():
    """
    Create default roles and permissions for testing.
    
    This helper function creates the basic role structure
    needed for testing role-based access control.
    """
    # Create permissions
    permissions = [
        Permission(name='read_posts', description='Can read posts'),
        Permission(name='write_posts', description='Can create posts'),
        Permission(name='edit_posts', description='Can edit posts'),
        Permission(name='delete_posts', description='Can delete posts'),
        Permission(name='manage_users', description='Can manage users'),
        Permission(name='admin_access', description='Can access admin panel'),
    ]
    
    for permission in permissions:
        db.session.add(permission)
    
    # Create roles
    user_role = Role(name='user', description='Regular user')
    moderator_role = Role(name='moderator', description='Content moderator')
    admin_role = Role(name='admin', description='Administrator')
    
    # Assign permissions to roles
    user_role.permissions = [permissions[0], permissions[1]]  # read, write
    moderator_role.permissions = permissions[:4]  # read, write, edit, delete
    admin_role.permissions = permissions  # all permissions
    
    db.session.add_all([user_role, moderator_role, admin_role])
    db.session.commit()


# Custom pytest markers for better test organization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.functional = pytest.mark.functional
pytest.mark.slow = pytest.mark.slow
pytest.mark.auth = pytest.mark.auth
pytest.mark.blog = pytest.mark.blog
pytest.mark.api = pytest.mark.api
pytest.mark.cache = pytest.mark.cache