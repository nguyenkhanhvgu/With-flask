"""
Logging Middleware

This module implements comprehensive logging middleware for Flask applications,
demonstrating request/response tracking, structured logging, and performance monitoring.
It provides educational examples of Flask request lifecycle hooks and logging best practices.
"""

import logging
import time
import uuid
from datetime import datetime
from flask import request, g, current_app
from functools import wraps
import json


class RequestLoggingMiddleware:
    """
    Middleware class for handling request/response logging with timing information.
    
    This class demonstrates how to implement middleware in Flask using before_request
    and after_request hooks to track the complete request lifecycle.
    """
    
    def __init__(self, app=None):
        """
        Initialize the logging middleware.
        
        Args:
            app (Flask, optional): Flask application instance
        """
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize the middleware with a Flask application.
        
        Args:
            app (Flask): Flask application instance
            
        This method demonstrates the Flask extension pattern for initialization.
        """
        # Configure structured logging
        self._configure_logging(app)
        
        # Register request hooks
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_request(self._teardown_request)
        
        # Store reference to app
        self.app = app
    
    def _configure_logging(self, app):
        """
        Configure structured logging with different levels and formatters.
        
        Args:
            app (Flask): Flask application instance
            
        This method demonstrates how to set up comprehensive logging configuration
        with different handlers for different log levels and structured output.
        """
        # Create custom logger for request tracking
        logger = logging.getLogger('flask_blog.requests')
        logger.setLevel(logging.DEBUG)
        
        # Prevent duplicate logs if logger already configured
        if logger.handlers:
            return
        
        # Create formatter for structured logging
        formatter = StructuredFormatter()
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler for persistent logging
        if app.config.get('LOG_FILE'):
            file_handler = logging.FileHandler(app.config['LOG_FILE'])
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # Error handler for critical issues
        error_handler = logging.FileHandler('logs/errors.log')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        # Store logger reference
        app.logger_requests = logger
    
    def _before_request(self):
        """
        Hook executed before each request.
        
        This method demonstrates how to use Flask's before_request hook
        to initialize request tracking and generate unique request IDs.
        """
        # Generate unique request ID for tracking
        g.request_id = str(uuid.uuid4())
        g.start_time = time.time()
        g.request_start = datetime.utcnow()
        
        # Log request start
        self._log_request_start()
    
    def _after_request(self, response):
        """
        Hook executed after each request.
        
        Args:
            response: Flask response object
            
        Returns:
            response: Modified Flask response object
            
        This method demonstrates how to use Flask's after_request hook
        to log response information and calculate request timing.
        """
        # Calculate request duration
        if hasattr(g, 'start_time'):
            g.duration = time.time() - g.start_time
        else:
            g.duration = 0
        
        # Add request ID to response headers for debugging
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        # Log request completion
        self._log_request_end(response)
        
        return response
    
    def _teardown_request(self, exception):
        """
        Hook executed at the end of request processing.
        
        Args:
            exception: Any exception that occurred during request processing
            
        This method demonstrates how to handle request cleanup and error logging.
        """
        if exception:
            self._log_request_error(exception)
    
    def _log_request_start(self):
        """
        Log the start of a request with relevant information.
        
        This method demonstrates structured logging for request tracking
        and shows how to capture relevant request metadata.
        """
        logger = getattr(current_app, 'logger_requests', None)
        if not logger:
            logger = logging.getLogger('flask_blog.requests')
        
        # Gather request information
        request_data = {
            'event': 'request_start',
            'request_id': getattr(g, 'request_id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat(),
            'method': request.method,
            'url': request.url,
            'path': request.path,
            'remote_addr': self._get_client_ip(),
            'user_agent': request.headers.get('User-Agent', ''),
            'referrer': request.headers.get('Referer', ''),
            'content_length': request.content_length,
            'content_type': request.content_type,
        }
        
        # Add user information if available
        if hasattr(request, 'user') and request.user:
            request_data['user_id'] = getattr(request.user, 'id', None)
            request_data['username'] = getattr(request.user, 'username', None)
        
        logger.info('Request started', extra={'structured_data': request_data})
    
    def _log_request_end(self, response):
        """
        Log the completion of a request with timing and response information.
        
        Args:
            response: Flask response object
            
        This method demonstrates how to log response information and
        calculate performance metrics for monitoring.
        """
        logger = getattr(current_app, 'logger_requests', None)
        if not logger:
            logger = logging.getLogger('flask_blog.requests')
        
        # Gather response information
        response_data = {
            'event': 'request_end',
            'request_id': getattr(g, 'request_id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat(),
            'method': request.method,
            'url': request.url,
            'path': request.path,
            'status_code': response.status_code,
            'content_length': response.content_length,
            'content_type': response.content_type,
            'duration_ms': round(getattr(g, 'duration', 0) * 1000, 2),
            'remote_addr': self._get_client_ip(),
        }
        
        # Add user information if available
        if hasattr(request, 'user') and request.user:
            response_data['user_id'] = getattr(request.user, 'id', None)
            response_data['username'] = getattr(request.user, 'username', None)
        
        # Determine log level based on status code
        if response.status_code >= 500:
            logger.error('Request completed with server error', 
                        extra={'structured_data': response_data})
        elif response.status_code >= 400:
            logger.warning('Request completed with client error', 
                          extra={'structured_data': response_data})
        else:
            logger.info('Request completed successfully', 
                       extra={'structured_data': response_data})
    
    def _log_request_error(self, exception):
        """
        Log request errors with exception information.
        
        Args:
            exception: Exception that occurred during request processing
            
        This method demonstrates error logging and exception tracking
        for debugging and monitoring purposes.
        """
        logger = getattr(current_app, 'logger_requests', None)
        if not logger:
            logger = logging.getLogger('flask_blog.requests')
        
        # Gather error information
        error_data = {
            'event': 'request_error',
            'request_id': getattr(g, 'request_id', 'unknown'),
            'timestamp': datetime.utcnow().isoformat(),
            'method': request.method,
            'url': request.url,
            'path': request.path,
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'duration_ms': round(getattr(g, 'duration', 0) * 1000, 2),
            'remote_addr': self._get_client_ip(),
        }
        
        # Add user information if available
        if hasattr(request, 'user') and request.user:
            error_data['user_id'] = getattr(request.user, 'id', None)
            error_data['username'] = getattr(request.user, 'username', None)
        
        logger.error('Request failed with exception', 
                    extra={'structured_data': error_data}, 
                    exc_info=True)
    
    def _get_client_ip(self):
        """
        Get the client IP address, handling proxy headers.
        
        Returns:
            str: Client IP address
            
        This method demonstrates how to properly extract client IP addresses
        when the application is behind proxies or load balancers.
        """
        # Check for forwarded headers (when behind proxy/load balancer)
        if request.headers.get('X-Forwarded-For'):
            # X-Forwarded-For can contain multiple IPs, take the first one
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'


class StructuredFormatter(logging.Formatter):
    """
    Custom logging formatter for structured JSON output.
    
    This class demonstrates how to create custom log formatters
    for structured logging that's easy to parse and analyze.
    """
    
    def format(self, record):
        """
        Format log record as structured JSON.
        
        Args:
            record: LogRecord instance
            
        Returns:
            str: Formatted log message
            
        This method shows how to create structured log output
        that includes both standard log fields and custom data.
        """
        # Create base log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add structured data if available
        if hasattr(record, 'structured_data'):
            log_entry.update(record.structured_data)
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, default=str)


def log_performance(threshold_ms=1000):
    """
    Decorator for logging slow function execution.
    
    Args:
        threshold_ms (int): Threshold in milliseconds for logging slow operations
        
    Returns:
        function: Decorated function
        
    This decorator demonstrates how to create performance monitoring
    decorators for identifying slow operations in the application.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = (time.time() - start_time) * 1000
                
                if duration > threshold_ms:
                    logger = logging.getLogger('flask_blog.performance')
                    logger.warning(
                        f'Slow operation detected: {func.__name__} took {duration:.2f}ms',
                        extra={
                            'structured_data': {
                                'function': func.__name__,
                                'module': func.__module__,
                                'duration_ms': round(duration, 2),
                                'threshold_ms': threshold_ms,
                                'args_count': len(args),
                                'kwargs_count': len(kwargs),
                            }
                        }
                    )
        
        return wrapper
    return decorator


def get_request_id():
    """
    Get the current request ID from Flask's g object.
    
    Returns:
        str: Current request ID or 'unknown' if not available
        
    This utility function demonstrates how to access request-specific
    data from anywhere in the application.
    """
    return getattr(g, 'request_id', 'unknown')


def log_user_action(action, details=None):
    """
    Log user actions for audit and analytics purposes.
    
    Args:
        action (str): Description of the user action
        details (dict, optional): Additional details about the action
        
    This function demonstrates how to create audit logs for user actions
    that can be used for analytics and security monitoring.
    """
    logger = logging.getLogger('flask_blog.user_actions')
    
    # Gather action information
    action_data = {
        'event': 'user_action',
        'action': action,
        'request_id': get_request_id(),
        'timestamp': datetime.utcnow().isoformat(),
        'url': request.url if request else 'unknown',
        'method': request.method if request else 'unknown',
        'remote_addr': request.remote_addr if request else 'unknown',
    }
    
    # Add user information if available
    if hasattr(request, 'user') and request.user:
        action_data['user_id'] = getattr(request.user, 'id', None)
        action_data['username'] = getattr(request.user, 'username', None)
    
    # Add additional details
    if details:
        action_data['details'] = details
    
    logger.info(f'User action: {action}', extra={'structured_data': action_data})