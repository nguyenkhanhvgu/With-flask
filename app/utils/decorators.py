"""
Custom Decorators

This module contains custom decorators for common functionality
like access control, validation, and request processing.
It demonstrates advanced Flask patterns including role-based access control,
permission checking, and user status validation.
"""

from functools import wraps
from flask import flash, redirect, url_for, abort, request, jsonify
from flask_login import current_user


def login_required_with_message(message="Please log in to access this page.", category="info"):
    """
    Enhanced login required decorator with custom message.
    
    Args:
        message (str): Custom message to display
        category (str): Flash message category
        
    Returns:
        function: Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash(message, category)
                return redirect(url_for('auth.login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def permission_required(permission_name, redirect_url=None, api_response=False):
    """
    Decorator to require a specific permission.
    
    This decorator demonstrates permission-based access control using
    the Role and Permission models.
    
    Args:
        permission_name (str): Name of the required permission
        redirect_url (str, optional): URL to redirect to on failure
        api_response (bool): Whether to return JSON response for API endpoints
        
    Returns:
        function: Decorator function
        
    Example:
        @permission_required('edit_all_posts')
        def edit_post(post_id):
            # Only users with 'edit_all_posts' permission can access
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_response:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.can(permission_name):
                if api_response:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                flash(f'Access denied. Required permission: {permission_name}', 'error')
                if redirect_url:
                    return redirect(redirect_url)
                return redirect(url_for('main.home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to require admin access.
    
    This decorator uses the new role-based permission system while
    maintaining backward compatibility with the legacy is_admin field.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_administrator():
            flash('Access denied. Administrator privileges required.', 'error')
            return redirect(url_for('main.home'))
        
        return f(*args, **kwargs)
    return decorated_function


def moderator_required(f):
    """
    Decorator to require moderator access or higher.
    
    This decorator allows access to users with moderator permissions
    or administrator privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_moderator():
            flash('Access denied. Moderator privileges required.', 'error')
            return redirect(url_for('main.home'))
        
        return f(*args, **kwargs)
    return decorated_function


def role_required(role_name, redirect_url=None, api_response=False):
    """
    Decorator to require a specific role.
    
    Args:
        role_name (str): Name of the required role
        redirect_url (str, optional): URL to redirect to on failure
        api_response (bool): Whether to return JSON response for API endpoints
        
    Returns:
        function: Decorator function
        
    Example:
        @role_required('Editor')
        def edit_content():
            # Only users with 'Editor' role can access
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_response:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.role or current_user.role.name != role_name:
                if api_response:
                    return jsonify({'error': f'Role {role_name} required'}), 403
                flash(f'Access denied. Required role: {role_name}', 'error')
                if redirect_url:
                    return redirect(redirect_url)
                return redirect(url_for('main.home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def active_required(f):
    """
    Decorator to require an active user account.
    
    This decorator checks if the user account is active and not suspended.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'error')
            return redirect(url_for('auth.logout'))
        
        return f(*args, **kwargs)
    return decorated_function


def confirmed_required(f):
    """
    Decorator to require email confirmation.
    
    This decorator ensures the user has confirmed their email address
    before accessing certain features.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.email_confirmed:
            flash('Please confirm your email address to access this feature.', 'warning')
            return redirect(url_for('auth.unconfirmed'))
        
        return f(*args, **kwargs)
    return decorated_function


def active_and_confirmed_required(f):
    """
    Decorator to require both active and confirmed user status.
    
    This combines the active_required and confirmed_required checks
    for convenience.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login', next=request.url))
        
        if not current_user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'error')
            return redirect(url_for('auth.logout'))
        
        if not current_user.email_confirmed:
            flash('Please confirm your email address to access this feature.', 'warning')
            return redirect(url_for('auth.unconfirmed'))
        
        return f(*args, **kwargs)
    return decorated_function


def api_permission_required(permission_name):
    """
    Decorator specifically for API endpoints that require permissions.
    
    This decorator returns JSON responses instead of redirects,
    making it suitable for API endpoints.
    
    Args:
        permission_name (str): Name of the required permission
        
    Returns:
        function: Decorator function
        
    Example:
        @api_permission_required('api_access')
        def api_endpoint():
            return jsonify({'data': 'sensitive_data'})
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            if not current_user.can(permission_name):
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_permission': permission_name
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def api_role_required(role_name):
    """
    Decorator specifically for API endpoints that require specific roles.
    
    Args:
        role_name (str): Name of the required role
        
    Returns:
        function: Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            if not current_user.role or current_user.role.name != role_name:
                return jsonify({
                    'error': 'Insufficient role',
                    'required_role': role_name,
                    'current_role': current_user.role.name if current_user.role else None
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def owner_or_permission_required(permission_name, get_owner_id=None):
    """
    Decorator that allows access if user owns the resource OR has permission.
    
    This is useful for endpoints where users can edit their own content
    or administrators can edit any content.
    
    Args:
        permission_name (str): Permission name for non-owners
        get_owner_id (callable): Function to extract owner ID from request
        
    Returns:
        function: Decorator function
        
    Example:
        @owner_or_permission_required('edit_all_posts', 
                                     lambda: Post.query.get(post_id).user_id)
        def edit_post(post_id):
            # User can edit if they own the post OR have edit_all_posts permission
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check if user has the permission (e.g., admin/moderator)
            if current_user.can(permission_name):
                return f(*args, **kwargs)
            
            # Check if user owns the resource
            if get_owner_id:
                try:
                    owner_id = get_owner_id()
                    if owner_id == current_user.id:
                        return f(*args, **kwargs)
                except Exception:
                    # If we can't determine ownership, deny access
                    pass
            
            flash('Access denied. You can only modify your own content.', 'error')
            return redirect(url_for('main.home'))
        
        return decorated_function
    return decorator


def multiple_permissions_required(*permission_names, require_all=True, api_response=False):
    """
    Decorator to require multiple permissions.
    
    Args:
        *permission_names: Variable number of permission names
        require_all (bool): If True, user must have ALL permissions.
                           If False, user needs ANY of the permissions.
        api_response (bool): Whether to return JSON response for API endpoints
        
    Returns:
        function: Decorator function
        
    Example:
        @multiple_permissions_required('create_posts', 'upload_files')
        def create_post_with_image():
            # User needs both permissions
            pass
            
        @multiple_permissions_required('edit_own_posts', 'edit_all_posts', 
                                      require_all=False)
        def edit_post():
            # User needs either permission
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if api_response:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'info')
                return redirect(url_for('auth.login', next=request.url))
            
            user_permissions = [perm for perm in permission_names 
                              if current_user.can(perm)]
            
            if require_all:
                has_access = len(user_permissions) == len(permission_names)
                missing_permissions = [perm for perm in permission_names 
                                     if perm not in user_permissions]
            else:
                has_access = len(user_permissions) > 0
                missing_permissions = list(permission_names) if not has_access else []
            
            if not has_access:
                if api_response:
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'required_permissions': list(permission_names),
                        'missing_permissions': missing_permissions,
                        'require_all': require_all
                    }), 403
                
                if require_all:
                    message = f'Access denied. Required permissions: {", ".join(permission_names)}'
                else:
                    message = f'Access denied. Need any of: {", ".join(permission_names)}'
                
                flash(message, 'error')
                return redirect(url_for('main.home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator