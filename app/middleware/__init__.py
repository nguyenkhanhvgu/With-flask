"""
Middleware Package

This package contains custom middleware components for handling
cross-cutting concerns like logging, rate limiting, and caching.
Middleware demonstrates how to process requests and responses
at the application level.
"""

from .logging import RequestLoggingMiddleware, log_performance, log_user_action, get_request_id

__all__ = [
    'RequestLoggingMiddleware',
    'log_performance', 
    'log_user_action',
    'get_request_id'
]