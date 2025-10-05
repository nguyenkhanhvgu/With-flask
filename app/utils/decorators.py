"""
Custom Decorators

This module contains custom decorators for common functionality
like access control, validation, and request processing.
"""

from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    """
    Decorator to require admin access.
    
    This decorator demonstrates how to create custom access control
    decorators in Flask applications.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function