"""
Custom Decorators

This module contains custom decorators for common functionality
like access control, validation, request processing, caching, and performance monitoring.
It demonstrates advanced Flask patterns including role-based access control,
permission checking, user status validation, caching strategies, and performance optimization.
"""

import time
import hashlib
import json
from functools import wraps
from flask import flash, redirect, url_for, abort, request, jsonify, current_app, g
from flask_login import current_user
from app.extensions import cache
import logging


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

# =============================================================================
# PERFORMANCE AND CACHING DECORATORS
# =============================================================================

def cache_result(timeout=300, key_prefix=None, unless=None):
    """
    Decorator to cache function results using Flask-Caching.
    
    This decorator demonstrates caching strategies for expensive operations
    like database queries, API calls, or complex calculations.
    
    Args:
        timeout (int): Cache timeout in seconds (default: 5 minutes)
        key_prefix (str): Custom prefix for cache key
        unless (callable): Function that returns True to skip caching
        
    Returns:
        function: Decorator function
        
    Example:
        @cache_result(timeout=600, key_prefix='user_posts')
        def get_user_posts(user_id):
            # Expensive database query
            return Post.query.filter_by(user_id=user_id).all()
            
        @cache_result(timeout=300, unless=lambda: current_user.is_authenticated)
        def get_public_posts():
            # Only cache for anonymous users
            return Post.query.filter_by(published=True).all()
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if caching should be skipped
            if unless and unless():
                return f(*args, **kwargs)
            
            # Generate cache key
            if key_prefix:
                cache_key = f"{key_prefix}:{f.__name__}"
            else:
                cache_key = f"func:{f.__module__}.{f.__name__}"
            
            # Add arguments to cache key
            if args or kwargs:
                args_str = str(args) + str(sorted(kwargs.items()))
                args_hash = hashlib.md5(args_str.encode()).hexdigest()
                cache_key = f"{cache_key}:{args_hash}"
            
            # Try to get from cache
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    current_app.logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_result
            except Exception as e:
                current_app.logger.warning(f"Cache get failed: {e}")
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            
            try:
                cache.set(cache_key, result, timeout=timeout)
                current_app.logger.debug(f"Cached result for key: {cache_key}")
            except Exception as e:
                current_app.logger.warning(f"Cache set failed: {e}")
            
            return result
        return decorated_function
    return decorator


def cache_page(timeout=300, key_prefix='page', vary_on_user=False):
    """
    Decorator to cache entire page responses.
    
    This decorator caches the complete response including headers,
    useful for expensive page renders or API responses.
    
    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Prefix for cache key
        vary_on_user (bool): Include user ID in cache key
        
    Returns:
        function: Decorator function
        
    Example:
        @cache_page(timeout=600, vary_on_user=True)
        def user_dashboard():
            # Expensive dashboard rendering
            return render_template('dashboard.html')
            
        @cache_page(timeout=1800, key_prefix='api_posts')
        def api_get_posts():
            # Cache API response for 30 minutes
            return jsonify(posts_data)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{request.endpoint}"
            
            # Add URL arguments to cache key
            if request.view_args:
                args_str = str(sorted(request.view_args.items()))
                cache_key += f":{hashlib.md5(args_str.encode()).hexdigest()}"
            
            # Add query parameters to cache key
            if request.args:
                query_str = str(sorted(request.args.items()))
                cache_key += f":{hashlib.md5(query_str.encode()).hexdigest()}"
            
            # Add user ID to cache key if requested
            if vary_on_user and current_user.is_authenticated:
                cache_key += f":user_{current_user.id}"
            
            # Try to get from cache
            try:
                cached_response = cache.get(cache_key)
                if cached_response is not None:
                    current_app.logger.debug(f"Page cache hit for: {cache_key}")
                    return cached_response
            except Exception as e:
                current_app.logger.warning(f"Page cache get failed: {e}")
            
            # Execute function and cache response
            response = f(*args, **kwargs)
            
            try:
                cache.set(cache_key, response, timeout=timeout)
                current_app.logger.debug(f"Cached page response for: {cache_key}")
            except Exception as e:
                current_app.logger.warning(f"Page cache set failed: {e}")
            
            return response
        return decorated_function
    return decorator


def invalidate_cache(cache_keys=None, key_patterns=None):
    """
    Decorator to invalidate cache entries after function execution.
    
    This decorator is useful for functions that modify data and need
    to clear related cached entries.
    
    Args:
        cache_keys (list): Specific cache keys to invalidate
        key_patterns (list): Cache key patterns to match and delete
        
    Returns:
        function: Decorator function
        
    Example:
        @invalidate_cache(cache_keys=['user_posts:123', 'trending_posts'])
        def create_post(user_id, title, content):
            # Create post and invalidate related caches
            post = Post(user_id=user_id, title=title, content=content)
            db.session.add(post)
            db.session.commit()
            return post
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function first
            result = f(*args, **kwargs)
            
            # Invalidate specific cache keys
            if cache_keys:
                for key in cache_keys:
                    try:
                        cache.delete(key)
                        current_app.logger.debug(f"Invalidated cache key: {key}")
                    except Exception as e:
                        current_app.logger.warning(f"Cache invalidation failed for {key}: {e}")
            
            # Invalidate cache keys matching patterns
            if key_patterns:
                for pattern in key_patterns:
                    try:
                        # This would require Redis-specific implementation
                        # For now, we'll log the pattern
                        current_app.logger.debug(f"Would invalidate pattern: {pattern}")
                    except Exception as e:
                        current_app.logger.warning(f"Pattern invalidation failed for {pattern}: {e}")
            
            return result
        return decorated_function
    return decorator


def timing_decorator(log_level=logging.INFO, include_args=False):
    """
    Decorator to measure and log function execution time.
    
    This decorator helps with performance monitoring by tracking
    how long functions take to execute.
    
    Args:
        log_level (int): Logging level for timing information
        include_args (bool): Whether to include function arguments in log
        
    Returns:
        function: Decorator function
        
    Example:
        @timing_decorator(log_level=logging.DEBUG, include_args=True)
        def expensive_calculation(data):
            # Complex calculation
            return process_data(data)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Prepare log message
                log_msg = f"Function {f.__module__}.{f.__name__} executed in {execution_time:.4f}s"
                
                if include_args and (args or kwargs):
                    args_info = f"args={args[:3]}{'...' if len(args) > 3 else ''}"
                    kwargs_info = f"kwargs={dict(list(kwargs.items())[:3])}{'...' if len(kwargs) > 3 else ''}"
                    log_msg += f" with {args_info}, {kwargs_info}"
                
                current_app.logger.log(log_level, log_msg)
                
                # Store timing in Flask's g object for potential use in templates
                if not hasattr(g, 'function_timings'):
                    g.function_timings = {}
                g.function_timings[f.__name__] = execution_time
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                current_app.logger.error(
                    f"Function {f.__module__}.{f.__name__} failed after {execution_time:.4f}s: {str(e)}"
                )
                raise
                
        return decorated_function
    return decorator


def performance_monitor(threshold=1.0, alert_callback=None):
    """
    Decorator to monitor function performance and alert on slow execution.
    
    This decorator tracks execution time and can trigger alerts
    when functions exceed performance thresholds.
    
    Args:
        threshold (float): Time threshold in seconds to trigger alert
        alert_callback (callable): Function to call when threshold exceeded
        
    Returns:
        function: Decorator function
        
    Example:
        def slow_function_alert(func_name, execution_time):
            # Send alert to monitoring system
            pass
            
        @performance_monitor(threshold=2.0, alert_callback=slow_function_alert)
        def database_query():
            # Database operation that should complete quickly
            return query_results
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Check if execution time exceeds threshold
                if execution_time > threshold:
                    warning_msg = (
                        f"PERFORMANCE WARNING: {f.__module__}.{f.__name__} "
                        f"took {execution_time:.4f}s (threshold: {threshold}s)"
                    )
                    current_app.logger.warning(warning_msg)
                    
                    # Call alert callback if provided
                    if alert_callback:
                        try:
                            alert_callback(f.__name__, execution_time)
                        except Exception as e:
                            current_app.logger.error(f"Alert callback failed: {e}")
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                current_app.logger.error(
                    f"Function {f.__module__}.{f.__name__} failed after {execution_time:.4f}s: {str(e)}"
                )
                raise
                
        return decorated_function
    return decorator


def validate_json_input(schema=None, required_fields=None):
    """
    Decorator to validate JSON input for API endpoints.
    
    This decorator validates incoming JSON data against a schema
    or checks for required fields, providing input sanitization.
    
    Args:
        schema (dict): JSON schema to validate against
        required_fields (list): List of required field names
        
    Returns:
        function: Decorator function
        
    Example:
        @validate_json_input(required_fields=['title', 'content'])
        def create_post():
            data = request.get_json()
            # data is guaranteed to have title and content
            return create_post_from_data(data)
            
        post_schema = {
            'title': {'type': 'string', 'maxlength': 200},
            'content': {'type': 'string', 'required': True}
        }
        
        @validate_json_input(schema=post_schema)
        def update_post():
            # JSON validated against schema
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if request has JSON data
            if not request.is_json:
                return jsonify({'error': 'Request must contain JSON data'}), 400
            
            try:
                data = request.get_json()
            except Exception:
                return jsonify({'error': 'Invalid JSON format'}), 400
            
            if data is None:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            # Validate required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400
            
            # Basic schema validation (simplified)
            if schema:
                validation_errors = []
                
                for field, rules in schema.items():
                    if field in data:
                        value = data[field]
                        
                        # Type validation
                        if 'type' in rules:
                            expected_type = rules['type']
                            if expected_type == 'string' and not isinstance(value, str):
                                validation_errors.append(f"Field '{field}' must be a string")
                            elif expected_type == 'integer' and not isinstance(value, int):
                                validation_errors.append(f"Field '{field}' must be an integer")
                        
                        # Length validation
                        if 'maxlength' in rules and isinstance(value, str):
                            if len(value) > rules['maxlength']:
                                validation_errors.append(f"Field '{field}' exceeds maximum length of {rules['maxlength']}")
                        
                        if 'minlength' in rules and isinstance(value, str):
                            if len(value) < rules['minlength']:
                                validation_errors.append(f"Field '{field}' is below minimum length of {rules['minlength']}")
                    
                    elif rules.get('required', False):
                        validation_errors.append(f"Required field '{field}' is missing")
                
                if validation_errors:
                    return jsonify({
                        'error': 'Validation failed',
                        'validation_errors': validation_errors
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def rate_limit_decorator(max_requests=100, per_seconds=3600, key_func=None):
    """
    Decorator to implement rate limiting for functions.
    
    This decorator limits the number of times a function can be called
    within a time window, useful for API endpoints and expensive operations.
    
    Args:
        max_requests (int): Maximum number of requests allowed
        per_seconds (int): Time window in seconds
        key_func (callable): Function to generate rate limit key
        
    Returns:
        function: Decorator function
        
    Example:
        @rate_limit_decorator(max_requests=10, per_seconds=60)
        def expensive_api_call():
            # Limited to 10 calls per minute
            return api_response
            
        @rate_limit_decorator(max_requests=5, per_seconds=300, 
                             key_func=lambda: f"user_{current_user.id}")
        def user_specific_action():
            # 5 calls per 5 minutes per user
            return action_result
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                rate_key = f"rate_limit:{key_func()}"
            else:
                rate_key = f"rate_limit:{f.__module__}.{f.__name__}:{request.remote_addr}"
            
            try:
                # Get current count from cache
                current_count = cache.get(rate_key) or 0
                
                if current_count >= max_requests:
                    if request.is_json or 'api' in request.endpoint:
                        return jsonify({
                            'error': 'Rate limit exceeded',
                            'max_requests': max_requests,
                            'per_seconds': per_seconds
                        }), 429
                    else:
                        flash('Rate limit exceeded. Please try again later.', 'error')
                        return redirect(request.referrer or url_for('main.home'))
                
                # Increment counter
                cache.set(rate_key, current_count + 1, timeout=per_seconds)
                
            except Exception as e:
                current_app.logger.warning(f"Rate limiting failed: {e}")
                # Continue execution if rate limiting fails
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def compress_response(compression_level=6, min_size=1000):
    """
    Decorator to compress response data for better performance.
    
    This decorator compresses response content when it exceeds
    a minimum size threshold, reducing bandwidth usage.
    
    Args:
        compression_level (int): Compression level (1-9)
        min_size (int): Minimum response size to compress
        
    Returns:
        function: Decorator function
        
    Example:
        @compress_response(compression_level=9, min_size=500)
        def large_data_endpoint():
            # Response will be compressed if > 500 bytes
            return jsonify(large_dataset)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Only compress if response is large enough
            if hasattr(response, 'data') and len(response.data) >= min_size:
                try:
                    import gzip
                    
                    # Compress the response data
                    compressed_data = gzip.compress(
                        response.data, 
                        compresslevel=compression_level
                    )
                    
                    # Update response with compressed data
                    response.data = compressed_data
                    response.headers['Content-Encoding'] = 'gzip'
                    response.headers['Content-Length'] = len(compressed_data)
                    
                    current_app.logger.debug(
                        f"Compressed response from {len(response.data)} to {len(compressed_data)} bytes"
                    )
                    
                except Exception as e:
                    current_app.logger.warning(f"Response compression failed: {e}")
            
            return response
        return decorated_function
    return decorator


def memoize(timeout=3600, key_func=None):
    """
    Decorator to memoize function results with automatic cache management.
    
    This decorator provides intelligent caching with automatic key generation
    and cache invalidation based on function arguments.
    
    Args:
        timeout (int): Cache timeout in seconds
        key_func (callable): Custom function to generate cache key
        
    Returns:
        function: Decorator function
        
    Example:
        @memoize(timeout=1800)
        def calculate_user_stats(user_id):
            # Expensive calculation cached for 30 minutes
            return complex_stats_calculation(user_id)
            
        @memoize(key_func=lambda x, y: f"sum_{x}_{y}")
        def add_numbers(x, y):
            # Simple example with custom key
            return x + y
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = f"memoize:{key_func(*args, **kwargs)}"
            else:
                # Create key from function name and arguments
                args_str = str(args) + str(sorted(kwargs.items()))
                args_hash = hashlib.md5(args_str.encode()).hexdigest()
                cache_key = f"memoize:{f.__module__}.{f.__name__}:{args_hash}"
            
            # Try to get from cache
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    current_app.logger.debug(f"Memoize cache hit: {cache_key}")
                    return cached_result
            except Exception as e:
                current_app.logger.warning(f"Memoize cache get failed: {e}")
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            
            try:
                cache.set(cache_key, result, timeout=timeout)
                current_app.logger.debug(f"Memoized result: {cache_key}")
            except Exception as e:
                current_app.logger.warning(f"Memoize cache set failed: {e}")
            
            return result
        return decorated_function
    return decorator


def cache_control(max_age=3600, public=True, must_revalidate=False):
    """
    Decorator to add HTTP cache control headers to responses.
    
    This decorator adds appropriate cache control headers to responses
    for better client-side caching and CDN performance.
    
    Args:
        max_age (int): Maximum age in seconds
        public (bool): Whether response can be cached by public caches
        must_revalidate (bool): Whether cache must revalidate
        
    Returns:
        function: Decorator function
        
    Example:
        @cache_control(max_age=1800, public=True)
        def static_content():
            # Response cached for 30 minutes
            return render_template('static_page.html')
            
        @cache_control(max_age=0, must_revalidate=True)
        def dynamic_content():
            # Always revalidate
            return render_template('user_dashboard.html')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = f(*args, **kwargs)
            
            # Add cache control headers
            if hasattr(response, 'cache_control'):
                response.cache_control.max_age = max_age
                response.cache_control.public = public
                response.cache_control.must_revalidate = must_revalidate
            
            return response
        return decorated_function
    return decorator



def sanitize_input(fields=None, strip_html=True, max_length=None):
    """
    Decorator to sanitize form and JSON input data.
    
    This decorator provides input sanitization by cleaning
    potentially dangerous content from user input.
    
    Args:
        fields (list): Specific fields to sanitize (None for all)
        strip_html (bool): Whether to strip HTML tags
        max_length (int): Maximum length for string fields
        
    Returns:
        function: Decorator function
        
    Example:
        @sanitize_input(fields=['title', 'content'], max_length=1000)
        def create_post():
            # Input data has been sanitized
            data = g.sanitized_json if request.is_json else request.form.to_dict()
            return process_clean_data(data)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get data from request
            if request.is_json:
                data = request.get_json() or {}
            else:
                data = request.form.to_dict()
            
            # Sanitize specified fields or all fields
            fields_to_sanitize = fields if fields else data.keys()
            
            for field in fields_to_sanitize:
                if field in data and isinstance(data[field], str):
                    value = data[field]
                    
                    # Strip HTML tags if requested
                    if strip_html:
                        import re
                        # Simple HTML tag removal (for production, use bleach library)
                        value = re.sub(r'<[^>]+>', '', value)
                    
                    # Trim whitespace
                    value = value.strip()
                    
                    # Enforce maximum length
                    if max_length and len(value) > max_length:
                        value = value[:max_length]
                    
                    # Update the data
                    data[field] = value
            
            # Store sanitized data in request context for the view function
            if request.is_json:
                # For JSON requests, we can't modify request.json directly
                # Store in g object for access in view function
                g.sanitized_json = data
            else:
                # For form requests, update form data
                request.form = request.form.copy()
                for field, value in data.items():
                    if field in request.form:
                        request.form[field] = value
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def rate_limit_per_user(max_requests=100, per_seconds=3600, key_func=None):
    """
    Decorator to implement per-user rate limiting.
    
    This decorator limits the number of requests a user can make
    to a specific endpoint within a time window.
    
    Args:
        max_requests (int): Maximum number of requests allowed
        per_seconds (int): Time window in seconds
        key_func (callable): Function to generate custom rate limit key
        
    Returns:
        function: Decorator function
        
    Example:
        @rate_limit_per_user(max_requests=10, per_seconds=60)
        def create_post():
            # Users can create max 10 posts per minute
            pass
            
        @rate_limit_per_user(max_requests=5, per_seconds=300, 
                            key_func=lambda: f"comment_{request.view_args['post_id']}")
        def add_comment(post_id):
            # Users can comment max 5 times per post per 5 minutes
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                rate_key = key_func()
            else:
                rate_key = f"rate_limit:{f.__name__}"
            
            if current_user.is_authenticated:
                rate_key += f":user_{current_user.id}"
            else:
                rate_key += f":ip_{request.remote_addr}"
            
            # Check current request count
            try:
                current_requests = cache.get(rate_key) or 0
                
                if current_requests >= max_requests:
                    if request.is_json:
                        return jsonify({
                            'error': 'Rate limit exceeded',
                            'max_requests': max_requests,
                            'per_seconds': per_seconds
                        }), 429
                    else:
                        flash(f'Rate limit exceeded. Try again in {per_seconds} seconds.', 'error')
                        return redirect(request.referrer or url_for('main.home'))
                
                # Increment request count
                cache.set(rate_key, current_requests + 1, timeout=per_seconds)
                
            except Exception as e:
                current_app.logger.warning(f"Rate limiting failed: {e}")
                # Continue execution if rate limiting fails
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator