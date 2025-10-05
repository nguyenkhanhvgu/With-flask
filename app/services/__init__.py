"""
Services Package

This package contains business logic services that handle the core
functionality of the application. Services provide a layer between
the routes and the database models, making the code more maintainable
and testable.
"""

from .auth_service import AuthService

__all__ = ['AuthService']