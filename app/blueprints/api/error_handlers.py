"""
Error handlers for the API blueprint
"""

from flask import jsonify
from . import bp


@bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({'error': 'Bad request'}), 400


@bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({'error': 'Unauthorized'}), 401


@bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden errors"""
    return jsonify({'error': 'Forbidden'}), 403


@bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({'error': 'Resource not found'}), 404


@bp.errorhandler(405)
def method_not_allowed(error):
    """Handle method not allowed errors"""
    return jsonify({'error': 'Method not allowed'}), 405


@bp.errorhandler(500)
def internal_error(error):
    """Handle internal server errors"""
    return jsonify({'error': 'Internal server error'}), 500


@bp.errorhandler(Exception)
def handle_exception(error):
    """Handle unexpected exceptions"""
    return jsonify({'error': 'An unexpected error occurred'}), 500