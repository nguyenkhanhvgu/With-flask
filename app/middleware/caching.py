"""
Caching Middleware for Flask Blog Application

This module provides caching middleware that demonstrates how to implement
response caching, ETags, and cache control headers in Flask applications.
It shows best practices for HTTP caching and performance optimization.
"""

import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import request, make_response, current_app, g
from app.extensions import cache
from app.utils.cache_utils import CacheKeyGenerator


class CacheManager:
    """
    Cache management utility class for handling cache operations.
    
    This class provides a centralized interface for cache operations
    and demonstrates cache management patterns.
    """
    
    @staticmethod
    def set(key, value, timeout=300):
        """
        Set a cache value.
        
        Args:
            key (str): Cache key
            value: Value to cache
            timeout (int): Cache timeout in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cache.set(key, value, timeout=timeout)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get(key):
        """
        Get a cache value.
        
        Args:
            key (str): Cache key
            
        Returns:
            Value from cache or None if not found
        """
        try:
            return cache.get(key)
        except Exception:
            return None
    
    @staticmethod
    def delete(key):
        """
        Delete a cache key.
        
        Args:
            key (str): Cache key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cache.delete(key)
            return True
        except Exception:
            return False
    
    @staticmethod
    def clear_all():
        """
        Clear all cache entries.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            cache.clear()
            return True
        except Exception:
            return False
    
    @staticmethod
    def warm_cache():
        """
        Warm up the cache with frequently accessed data.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # This would implement cache warming logic
            # For now, just return True
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_info():
        """
        Get cache information and statistics.
        
        Returns:
            dict: Cache statistics or None if not available
        """
        try:
            # This would return actual cache statistics
            # For now, return basic info
            return {
                'status': 'active',
                'backend': 'redis' if hasattr(cache, 'cache') else 'simple',
                'keys_count': 'unknown'
            }
        except Exception:
            return None


class CachingMiddleware:
    """
    Middleware class for handling response caching and HTTP cache headers.
    
    This middleware demonstrates how to implement caching at the application
    level, including ETag generation, cache control headers, and conditional
    requests handling.
    """
    
    def __init__(self, app=None):
        """Initialize caching middleware."""
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Handle cache-related processing before request."""
        # Record request start time for performance monitoring
        g.request_start_time = datetime.utcnow()
        
        # Check for conditional request headers
        if request.method == 'GET':
            self._handle_conditional_request()
    
    def after_request(self, response):
        """Handle cache-related processing after request."""
        # Add cache control headers for static content
        if request.endpoint and 'static' in request.endpoint:
            self._add_static_cache_headers(response)
        
        # Add ETag for cacheable responses
        if self._is_cacheable_response(response):
            self._add_etag(response)
        
        # Add performance headers
        self._add_performance_headers(response)
        
        return response
    
    def _handle_conditional_request(self):
        """Handle If-None-Match and If-Modified-Since headers."""
        # This would be implemented based on specific caching needs
        pass
    
    def _add_static_cache_headers(self, response):
        """Add cache headers for static files."""
        # Cache static files for 1 year
        response.cache_control.max_age = 31536000  # 1 year
        response.cache_control.public = True
        
        # Add expires header
        expires = datetime.utcnow() + timedelta(days=365)
        response.expires = expires
    
    def _add_etag(self, response):
        """Generate and add ETag header."""
        if response.data:
            etag = hashlib.md5(response.data).hexdigest()
            response.set_etag(etag)
    
    def _is_cacheable_response(self, response):
        """Check if response is cacheable."""
        return (
            response.status_code == 200 and
            request.method == 'GET' and
            'text/html' in response.content_type
        )
    
    def _add_performance_headers(self, response):
        """Add performance monitoring headers."""
        if hasattr(g, 'request_start_time'):
            duration = datetime.utcnow() - g.request_start_time
            response.headers['X-Response-Time'] = f"{duration.total_seconds():.3f}s"


def cache_response(timeout=300, key_func=None, unless=None):
    """
    Decorator to cache view function responses.
    
    Args:
        timeout (int): Cache timeout in seconds
        key_func (callable): Function to generate cache key
        unless (callable): Function to determine if caching should be skipped
    
    Usage:
        @cache_response(timeout=600)
        def index():
            return render_template('index.html')
        
        @cache_response(timeout=300, key_func=lambda: f"user:{current_user.id}")
        def profile():
            return render_template('profile.html')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if caching should be skipped
            if unless and unless():
                return func(*args, **kwargs)
            
            # Generate cache key
            if key_func:
                cache_key = key_func()
            else:
                cache_key = CacheKeyGenerator.request_key(
                    include_args=True,
                    include_user=False
                )
            
            # Try to get cached response
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            
            # Execute function and cache response
            response = func(*args, **kwargs)
            
            # Only cache successful responses
            if hasattr(response, 'status_code') and response.status_code == 200:
                cache.set(cache_key, response, timeout=timeout)
            
            return response
        
        return wrapper
    return decorator


def cache_page(timeout=300, key_prefix=None, unless=None):
    """
    Decorator to cache entire page responses.
    
    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Prefix for cache key
        unless (callable): Function to determine if caching should be skipped
    
    Usage:
        @cache_page(timeout=600, key_prefix='homepage')
        def index():
            return render_template('index.html')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if caching should be skipped
            if unless and unless():
                return func(*args, **kwargs)
            
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            
            # Add request path and args
            key_parts.append(request.path)
            if request.args:
                sorted_args = sorted(request.args.items())
                args_str = "&".join([f"{k}={v}" for k, v in sorted_args])
                key_parts.append(args_str)
            
            cache_key = ":".join(key_parts)
            
            # Try to get cached response
            cached_data = cache.get(cache_key)
            if cached_data:
                response = make_response(cached_data['content'])
                response.status_code = cached_data['status_code']
                response.headers.update(cached_data['headers'])
                return response
            
            # Execute function and cache response
            response = func(*args, **kwargs)
            
            # Cache successful responses
            if response.status_code == 200:
                cache_data = {
                    'content': response.get_data(as_text=True),
                    'status_code': response.status_code,
                    'headers': dict(response.headers)
                }
                cache.set(cache_key, cache_data, timeout=timeout)
            
            return response
        
        return wrapper
    return decorator


def cache_template(timeout=300, key_func=None):
    """
    Decorator to cache template rendering results.
    
    Args:
        timeout (int): Cache timeout in seconds
        key_func (callable): Function to generate cache key
    
    Usage:
        @cache_template(timeout=600)
        def render_post_list(posts):
            return render_template('posts.html', posts=posts)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Use function name and arguments as key
                key_parts = [func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
                cache_key = ":".join(key_parts)
            
            # Try to get cached result
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return wrapper
    return decorator


def invalidate_cache_on_change(cache_keys):
    """
    Decorator to invalidate cache entries when data changes.
    
    Args:
        cache_keys (list): List of cache keys or patterns to invalidate
    
    Usage:
        @invalidate_cache_on_change(['posts:*', 'trending:*'])
        def create_post(title, content):
            # Create post logic
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function first
            result = func(*args, **kwargs)
            
            # Invalidate cache entries
            from app.utils.cache_utils import CacheInvalidator
            
            for key in cache_keys:
                if '*' in key:
                    CacheInvalidator._delete_pattern(key)
                else:
                    cache.delete(key)
            
            return result
        
        return wrapper
    return decorator



# Initialize caching middleware
caching_middleware = CachingMiddleware()