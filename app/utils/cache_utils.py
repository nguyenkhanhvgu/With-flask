"""
Cache Utilities for Flask Blog Application

This module provides utilities for cache key generation, cache invalidation,
and cache management. It demonstrates best practices for caching in Flask
applications and provides reusable functions for common caching patterns.
"""

import hashlib
import json
from functools import wraps
from flask import request, current_app
from app.extensions import cache


class CacheKeyGenerator:
    """
    Utility class for generating consistent cache keys.
    
    This class provides methods to generate cache keys for different types
    of data and operations, ensuring consistency across the application.
    """
    
    @staticmethod
    def user_key(user_id):
        """Generate cache key for user data."""
        return f"user:{user_id}"
    
    @staticmethod
    def post_key(post_id):
        """Generate cache key for post data."""
        return f"post:{post_id}"
    
    @staticmethod
    def posts_list_key(page=1, per_page=5, category_id=None, user_id=None):
        """Generate cache key for posts list with pagination and filters."""
        key_parts = [f"posts:page:{page}:per_page:{per_page}"]
        if category_id:
            key_parts.append(f"category:{category_id}")
        if user_id:
            key_parts.append(f"user:{user_id}")
        return ":".join(key_parts)
    
    @staticmethod
    def user_posts_key(user_id, page=1, per_page=5):
        """Generate cache key for user's posts."""
        return f"user:{user_id}:posts:page:{page}:per_page:{per_page}"
    
    @staticmethod
    def category_posts_key(category_id, page=1, per_page=5):
        """Generate cache key for category posts."""
        return f"category:{category_id}:posts:page:{page}:per_page:{per_page}"
    
    @staticmethod
    def trending_posts_key(limit=10):
        """Generate cache key for trending posts."""
        return f"trending:posts:limit:{limit}"
    
    @staticmethod
    def user_profile_key(user_id):
        """Generate cache key for user profile data."""
        return f"profile:{user_id}"
    
    @staticmethod
    def post_comments_key(post_id, page=1, per_page=10):
        """Generate cache key for post comments."""
        return f"post:{post_id}:comments:page:{page}:per_page:{per_page}"
    
    @staticmethod
    def search_results_key(query, page=1, per_page=5):
        """Generate cache key for search results."""
        # Hash the query to handle special characters and long queries
        query_hash = hashlib.md5(query.encode('utf-8')).hexdigest()
        return f"search:{query_hash}:page:{page}:per_page:{per_page}"
    
    @staticmethod
    def api_endpoint_key(endpoint, **kwargs):
        """Generate cache key for API endpoints with parameters."""
        # Sort kwargs for consistent key generation
        sorted_params = sorted(kwargs.items())
        params_str = ":".join([f"{k}:{v}" for k, v in sorted_params])
        if params_str:
            return f"api:{endpoint}:{params_str}"
        return f"api:{endpoint}"
    
    @staticmethod
    def request_key(include_args=True, include_user=False):
        """
        Generate cache key based on current request.
        
        Args:
            include_args (bool): Include request arguments in key
            include_user (bool): Include current user ID in key
            
        Returns:
            str: Generated cache key
        """
        key_parts = [request.endpoint or 'unknown']
        
        if include_args and request.args:
            # Sort args for consistent key generation
            sorted_args = sorted(request.args.items())
            args_str = ":".join([f"{k}:{v}" for k, v in sorted_args])
            key_parts.append(f"args:{args_str}")
        
        if include_user:
            from flask_login import current_user
            if current_user.is_authenticated:
                key_parts.append(f"user:{current_user.id}")
            else:
                key_parts.append("user:anonymous")
        
        return ":".join(key_parts)


class CacheInvalidator:
    """
    Utility class for cache invalidation operations.
    
    This class provides methods to invalidate related cache entries
    when data is modified, ensuring cache consistency.
    """
    
    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache entries related to a user."""
        patterns = [
            CacheKeyGenerator.user_key(user_id),
            CacheKeyGenerator.user_profile_key(user_id),
            f"user:{user_id}:*",  # All user-related keys
        ]
        
        for pattern in patterns:
            if '*' in pattern:
                CacheInvalidator._delete_pattern(pattern)
            else:
                cache.delete(pattern)
    
    @staticmethod
    def invalidate_post_cache(post_id, user_id=None, category_id=None):
        """Invalidate all cache entries related to a post."""
        patterns = [
            CacheKeyGenerator.post_key(post_id),
            f"post:{post_id}:*",  # All post-related keys
            "posts:*",  # All posts lists
            "trending:*",  # Trending posts
        ]
        
        if user_id:
            patterns.append(f"user:{user_id}:posts:*")
        
        if category_id:
            patterns.append(f"category:{category_id}:*")
        
        for pattern in patterns:
            if '*' in pattern:
                CacheInvalidator._delete_pattern(pattern)
            else:
                cache.delete(pattern)
    
    @staticmethod
    def invalidate_posts_lists():
        """Invalidate all posts list caches."""
        patterns = [
            "posts:*",
            "trending:*",
            "search:*",
        ]
        
        for pattern in patterns:
            CacheInvalidator._delete_pattern(pattern)
    
    @staticmethod
    def invalidate_category_cache(category_id):
        """Invalidate cache entries related to a category."""
        patterns = [
            f"category:{category_id}:*",
            "posts:*",  # Category changes affect posts lists
        ]
        
        for pattern in patterns:
            CacheInvalidator._delete_pattern(pattern)
    
    @staticmethod
    def invalidate_search_cache():
        """Invalidate all search result caches."""
        CacheInvalidator._delete_pattern("search:*")
    
    @staticmethod
    def _delete_pattern(pattern):
        """
        Delete cache keys matching a pattern.
        
        Note: This is a simplified implementation. In production,
        you might want to use Redis SCAN command for better performance.
        """
        try:
            # Check if we're using Redis cache
            if hasattr(cache.cache, '_write_client'):
                # Redis implementation
                redis_client = cache.cache._write_client
                
                # Use Redis SCAN to find matching keys
                cursor = 0
                prefix = current_app.config.get('CACHE_KEY_PREFIX', 'flask_blog:')
                full_pattern = f"{prefix}{pattern}"
                
                while True:
                    cursor, keys = redis_client.scan(cursor, match=full_pattern, count=100)
                    if keys:
                        redis_client.delete(*keys)
                    if cursor == 0:
                        break
            else:
                # For SimpleCache or other cache types, clear all cache
                # This is a limitation of non-Redis cache backends
                current_app.logger.warning(f"Pattern deletion not supported for {type(cache.cache).__name__}, clearing all cache")
                cache.clear()
                    
        except Exception as e:
            current_app.logger.warning(f"Failed to delete cache pattern {pattern}: {e}")


def cache_key(*args, **kwargs):
    """
    Decorator to generate cache keys for functions.
    
    Usage:
        @cache_key('user', 'posts')
        def get_user_posts(user_id, page=1):
            return f"user:{user_id}:posts:page:{page}"
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*func_args, **func_kwargs):
            # Generate key based on function arguments
            key_parts = list(args)
            
            # Add function arguments to key
            if func_args:
                key_parts.extend([str(arg) for arg in func_args])
            
            # Add keyword arguments to key
            if func_kwargs:
                sorted_kwargs = sorted(func_kwargs.items())
                key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
            
            return ":".join(key_parts)
        
        return wrapper
    return decorator


def cached_function(timeout=None, key_prefix=None):
    """
    Decorator to cache function results.
    
    Args:
        timeout (int): Cache timeout in seconds
        key_prefix (str): Prefix for cache key
    
    Usage:
        @cached_function(timeout=300, key_prefix='expensive_operation')
        def expensive_operation(param1, param2):
            # Expensive computation
            return result
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            
            if args:
                key_parts.extend([str(arg) for arg in args])
            
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())
                key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            
            return result
        
        return wrapper
    return decorator


def warm_cache():
    """
    Warm up the cache with frequently accessed data.
    
    This function can be called during application startup or
    periodically to pre-populate the cache with commonly requested data.
    """
    try:
        # Import here to avoid circular imports
        from app.services.blog_service import BlogService
        
        # Use BlogService for comprehensive cache warming
        return BlogService.warm_popular_content()
        
    except Exception as e:
        current_app.logger.error(f"Failed to warm cache: {e}")
        return False


def get_cache_stats():
    """
    Get cache statistics for monitoring.
    
    Returns:
        dict: Cache statistics including hit rate, memory usage, etc.
    """
    try:
        # Check if we're using Redis cache
        if hasattr(cache.cache, '_write_client'):
            redis_client = cache.cache._write_client
            info = redis_client.info()
            
            return {
                'cache_type': 'Redis',
                'connected_clients': info.get('connected_clients', 0),
                'used_memory': info.get('used_memory_human', '0B'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': _calculate_hit_rate(
                    info.get('keyspace_hits', 0),
                    info.get('keyspace_misses', 0)
                )
            }
        else:
            # For SimpleCache or other cache types
            cache_type = type(cache.cache).__name__
            return {
                'cache_type': cache_type,
                'status': 'active',
                'note': f'Using {cache_type} - detailed stats not available'
            }
    except Exception as e:
        current_app.logger.error(f"Failed to get cache stats: {e}")
        return {
            'cache_type': 'unknown',
            'status': 'error',
            'error': str(e)
        }


def _calculate_hit_rate(hits, misses):
    """Calculate cache hit rate percentage."""
    total = hits + misses
    if total == 0:
        return 0.0
    return round((hits / total) * 100, 2)