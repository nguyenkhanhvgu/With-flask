"""
Utilities Package

This package contains utility functions, decorators, and helper
classes that are used throughout the application. Utilities
provide reusable functionality that doesn't fit into specific
models or services.
"""

from .decorators import (
    # Authentication decorators
    login_required_with_message,
    
    # Permission-based decorators
    permission_required,
    multiple_permissions_required,
    
    # Role-based decorators
    admin_required,
    moderator_required,
    role_required,
    
    # User status decorators
    active_required,
    confirmed_required,
    active_and_confirmed_required,
    
    # API-specific decorators
    api_permission_required,
    api_role_required,
    
    # Advanced access control decorators
    owner_or_permission_required,
)

__all__ = [
    # Authentication decorators
    'login_required_with_message',
    
    # Permission-based decorators
    'permission_required',
    'multiple_permissions_required',
    
    # Role-based decorators
    'admin_required',
    'moderator_required',
    'role_required',
    
    # User status decorators
    'active_required',
    'confirmed_required',
    'active_and_confirmed_required',
    
    # API-specific decorators
    'api_permission_required',
    'api_role_required',
    
    # Advanced access control decorators
    'owner_or_permission_required',
]