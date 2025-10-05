"""
Authentication Blueprint Error Handlers

This module contains error handlers specific to the authentication blueprint.
It demonstrates how to handle errors at the blueprint level.
"""

from flask import render_template, flash, redirect, url_for
from app.blueprints.auth import bp


@bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors in auth blueprint."""
    flash('Bad request. Please check your input and try again.', 'error')
    return redirect(url_for('auth.login'))


@bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access errors in auth blueprint."""
    flash('Unauthorized access. Please log in to continue.', 'error')
    return redirect(url_for('auth.login'))


@bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden access errors in auth blueprint."""
    flash('Access forbidden. You do not have permission to access this resource.', 'error')
    return redirect(url_for('main.home'))


@bp.errorhandler(429)
def rate_limit_exceeded(error):
    """Handle rate limit exceeded errors in auth blueprint."""
    flash('Too many requests. Please try again later.', 'error')
    return redirect(url_for('auth.login'))