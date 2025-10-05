"""
Rate Limiting Middleware

This module implements rate limiting functionality using Redis for storage.
It demonstrates how to implement security measures to prevent abuse of
authentication endpoints and other sensitive operations.
"""

import time
from functools import wraps
from flask import request, jsonify, current_app, g
from app.extensions import cache
import redis


class RateLimiter:
    """
    Rate limiter class using Redis for distributed rate limiting.
    
    This class demonstrates sliding window rate limiting with Redis,
    which is more accurate than fixed window approaches.
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize the rate limiter.
        
        Args:
            redis_client: Redis client instance (optional)
        """
        self.redis_client = redis_client or self._get_redis_client()
    
    def _get_redis_client(self):
        """Get Redis client from Flask-Caching or create new one."""
        try:
            # Try to get Redis client from Flask-Caching
            if hasattr(cache.cache, '_write_client'):
                return cache.cache._write_client
            elif hasattr(cache.cache, 'cache'):
                return cache.cache.cache._write_client
            else:
                # Fallback to creating new Redis client
                import redis
                return redis.Redis(
                    host=current_app.config.get('CACHE_REDIS_HOST', 'localhost'),
                    port=current_app.config.get('CACHE_REDIS_PORT', 6379),
                    db=current_app.config.get('CACHE_REDIS_DB', 0),
                    password=current_app.config.get('CACHE_REDIS_PASSWORD'),
                    decode_responses=True
                )
        except Exception as e:
            current_app.logger.warning(f'Could not connect to Redis for rate limiting: {e}')
            return None
    
    def is_allowed(self, key, limit, window, cost=1):
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key (str): Unique identifier for the rate limit (e.g., IP address)
            limit (int): Maximum number of requests allowed
            window (int): Time window in seconds
            cost (int): Cost of this request (default: 1)
            
        Returns:
            tuple: (allowed: bool, retry_after: int)
            
        This implements a sliding window rate limiter using Redis.
        """
        if not self.redis_client:
            # If Redis is not available, allow all requests
            current_app.logger.warning('Rate limiting disabled: Redis not available')
            return True, 0
        
        try:
            current_time = time.time()
            pipeline = self.redis_client.pipeline()
            
            # Remove expired entries
            pipeline.zremrangebyscore(key, 0, current_time - window)
            
            # Count current requests in window
            pipeline.zcard(key)
            
            # Add current request
            pipeline.zadd(key, {str(current_time): current_time})
            
            # Set expiration for cleanup
            pipeline.expire(key, window + 1)
            
            results = pipeline.execute()
            current_count = results[1]
            
            if current_count < limit:
                return True, 0
            else:
                # Calculate retry after time
                oldest_request = self.redis_client.zrange(key, 0, 0, withscores=True)
                if oldest_request:
                    retry_after = int(window - (current_time - oldest_request[0][1])) + 1
                else:
                    retry_after = window
                
                # Remove the request we just added since it's not allowed
                self.redis_client.zrem(key, str(current_time))
                
                return False, max(retry_after, 1)
                
        except Exception as e:
            current_app.logger.error(f'Rate limiting error: {e}')
            # On error, allow the request to avoid blocking legitimate users
            return True, 0


# Global rate limiter instance (initialized lazily)
rate_limiter = None


def get_rate_limiter():
    """Get or create the global rate limiter instance."""
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = RateLimiter()
    return rate_limiter


def rate_limit(limit=60, window=60, per='ip', key_func=None, error_message=None):
    """
    Rate limiting decorator.
    
    Args:
        limit (int): Maximum number of requests allowed (default: 60)
        window (int): Time window in seconds (default: 60)
        per (str): Rate limit per 'ip' or 'user' (default: 'ip')
        key_func (callable): Custom function to generate rate limit key
        error_message (str): Custom error message for rate limit exceeded
        
    Returns:
        decorator: Rate limiting decorator function
        
    This decorator demonstrates how to implement rate limiting for Flask routes.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate rate limit key
            if key_func:
                key = key_func()
            elif per == 'user':
                from flask_login import current_user
                if current_user.is_authenticated:
                    key = f"rate_limit:user:{current_user.id}:{f.__name__}"
                else:
                    key = f"rate_limit:ip:{request.remote_addr}:{f.__name__}"
            else:  # per == 'ip'
                key = f"rate_limit:ip:{request.remote_addr}:{f.__name__}"
            
            # Check rate limit
            allowed, retry_after = get_rate_limiter().is_allowed(key, limit, window)
            
            if not allowed:
                current_app.logger.warning(
                    f'Rate limit exceeded for {key}: {limit} requests per {window}s'
                )
                
                # Store rate limit info in g for potential use in error handlers
                g.rate_limit_exceeded = True
                g.retry_after = retry_after
                
                if request.is_json:
                    return jsonify({
                        'error': error_message or 'Rate limit exceeded',
                        'retry_after': retry_after
                    }), 429
                else:
                    from flask import flash, redirect, url_for
                    flash(
                        error_message or f'Too many requests. Please try again in {retry_after} seconds.',
                        'error'
                    )
                    return redirect(request.referrer or url_for('main.home'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def auth_rate_limit(limit=5, window=300):
    """
    Specialized rate limiter for authentication endpoints.
    
    Args:
        limit (int): Maximum number of attempts (default: 5)
        window (int): Time window in seconds (default: 300 = 5 minutes)
        
    Returns:
        decorator: Authentication rate limiting decorator
        
    This provides stricter rate limiting for sensitive authentication operations.
    """
    return rate_limit(
        limit=limit,
        window=window,
        per='ip',
        error_message=f'Too many authentication attempts. Please try again in {window//60} minutes.'
    )


def api_rate_limit(limit=100, window=3600):
    """
    Rate limiter for API endpoints.
    
    Args:
        limit (int): Maximum number of requests (default: 100)
        window (int): Time window in seconds (default: 3600 = 1 hour)
        
    Returns:
        decorator: API rate limiting decorator
        
    This provides rate limiting for API endpoints with higher limits.
    """
    return rate_limit(
        limit=limit,
        window=window,
        per='user',
        error_message='API rate limit exceeded. Please try again later.'
    )


def get_rate_limit_status(key, limit, window):
    """
    Get current rate limit status for a key.
    
    Args:
        key (str): Rate limit key
        limit (int): Rate limit
        window (int): Time window
        
    Returns:
        dict: Rate limit status information
        
    This function allows checking rate limit status without consuming a request.
    """
    if not get_rate_limiter().redis_client:
        return {
            'limit': limit,
            'remaining': limit,
            'reset_time': int(time.time() + window),
            'retry_after': 0
        }
    
    try:
        current_time = time.time()
        
        # Clean up expired entries
        get_rate_limiter().redis_client.zremrangebyscore(key, 0, current_time - window)
        
        # Get current count
        current_count = get_rate_limiter().redis_client.zcard(key)
        remaining = max(0, limit - current_count)
        
        # Calculate reset time
        if current_count > 0:
            oldest_request = get_rate_limiter().redis_client.zrange(key, 0, 0, withscores=True)
            if oldest_request:
                reset_time = int(oldest_request[0][1] + window)
            else:
                reset_time = int(current_time + window)
        else:
            reset_time = int(current_time + window)
        
        retry_after = max(0, reset_time - int(current_time)) if remaining == 0 else 0
        
        return {
            'limit': limit,
            'remaining': remaining,
            'reset_time': reset_time,
            'retry_after': retry_after
        }
        
    except Exception as e:
        current_app.logger.error(f'Error getting rate limit status: {e}')
        return {
            'limit': limit,
            'remaining': limit,
            'reset_time': int(time.time() + window),
            'retry_after': 0
        }


def clear_rate_limit(key):
    """
    Clear rate limit for a specific key.
    
    Args:
        key (str): Rate limit key to clear
        
    Returns:
        bool: True if cleared successfully, False otherwise
        
    This function allows administrators to clear rate limits if needed.
    """
    if not get_rate_limiter().redis_client:
        return False
    
    try:
        get_rate_limiter().redis_client.delete(key)
        current_app.logger.info(f'Rate limit cleared for key: {key}')
        return True
    except Exception as e:
        current_app.logger.error(f'Error clearing rate limit for {key}: {e}')
        return False