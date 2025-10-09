# Performance and Caching Decorators Guide

This guide explains how to use the performance and caching decorators implemented in `app/utils/decorators.py`. These decorators provide essential functionality for building scalable Flask applications with proper caching, performance monitoring, and input validation.

## Overview

The decorators are organized into three main categories:

1. **Caching Decorators** - For improving performance through caching
2. **Performance Monitoring Decorators** - For tracking and alerting on performance
3. **Input Validation Decorators** - For sanitizing and validating user input

## Caching Decorators

### `@cache_result(timeout=300, key_prefix=None, unless=None)`

Caches function results using Flask-Caching. Ideal for expensive database queries or calculations.

**Parameters:**
- `timeout` (int): Cache timeout in seconds (default: 5 minutes)
- `key_prefix` (str): Custom prefix for cache key
- `unless` (callable): Function that returns True to skip caching

**Example:**
```python
@cache_result(timeout=600, key_prefix='user_posts')
def get_user_posts(user_id):
    return Post.query.filter_by(user_id=user_id).all()

# Only cache for anonymous users
@cache_result(timeout=300, unless=lambda: current_user.is_authenticated)
def get_public_posts():
    return Post.query.filter_by(published=True).all()
```

### `@cache_page(timeout=300, key_prefix='page', vary_on_user=False)`

Caches entire page responses including headers. Perfect for expensive page renders.

**Parameters:**
- `timeout` (int): Cache timeout in seconds
- `key_prefix` (str): Prefix for cache key
- `vary_on_user` (bool): Include user ID in cache key

**Example:**
```python
@cache_page(timeout=1800, key_prefix='category')
def category_view(category_id):
    # Expensive page rendering
    return render_template('category.html', posts=posts)
```

### `@invalidate_cache(cache_keys=None, key_patterns=None)`

Invalidates cache entries after function execution. Use when data changes.

**Parameters:**
- `cache_keys` (list): Specific cache keys to invalidate
- `key_patterns` (list): Cache key patterns to match and delete

**Example:**
```python
@invalidate_cache(cache_keys=['trending_posts:get_trending_posts'])
def create_post(title, content):
    post = Post(title=title, content=content)
    db.session.add(post)
    db.session.commit()
    return post
```

## Performance Monitoring Decorators

### `@timing_decorator(log_level=logging.INFO, include_args=False)`

Measures and logs function execution time for performance analysis.

**Parameters:**
- `log_level` (int): Logging level for timing information
- `include_args` (bool): Whether to include function arguments in log

**Example:**
```python
@timing_decorator(include_args=True)
def search_posts(query):
    return Post.query.filter(Post.title.contains(query)).all()
```

### `@performance_monitor(threshold=1.0, alert_callback=None)`

Monitors function performance and alerts when execution exceeds thresholds.

**Parameters:**
- `threshold` (float): Time threshold in seconds to trigger alert
- `alert_callback` (callable): Function to call when threshold exceeded

**Example:**
```python
def slow_query_alert(func_name, execution_time):
    # Send alert to monitoring system
    logger.warning(f"Slow query: {func_name} took {execution_time}s")

@performance_monitor(threshold=2.0, alert_callback=slow_query_alert)
def complex_analytics():
    # Complex database operations
    return analytics_data
```

## Input Validation Decorators

### `@validate_json_input(schema=None, required_fields=None)`

Validates JSON input for API endpoints with schema validation or required field checking.

**Parameters:**
- `schema` (dict): JSON schema to validate against
- `required_fields` (list): List of required field names

**Example:**
```python
# Simple required fields validation
@validate_json_input(required_fields=['title', 'content'])
def create_post():
    data = request.get_json()
    return create_post_from_data(data)

# Schema-based validation
post_schema = {
    'title': {'type': 'string', 'maxlength': 200, 'required': True},
    'content': {'type': 'string', 'minlength': 10}
}

@validate_json_input(schema=post_schema)
def update_post():
    data = request.get_json()
    # Data is validated against schema
    return update_post_data(data)
```

### `@sanitize_input(fields=None, strip_html=True, max_length=None)`

Sanitizes form and JSON input data by cleaning potentially dangerous content.

**Parameters:**
- `fields` (list): Specific fields to sanitize (None for all)
- `strip_html` (bool): Whether to strip HTML tags
- `max_length` (int): Maximum length for string fields

**Example:**
```python
@sanitize_input(fields=['title', 'content'], max_length=1000)
def create_post():
    # Input data has been sanitized
    data = g.sanitized_json  # For JSON requests
    return process_clean_data(data)
```

### `@rate_limit_per_user(max_requests=100, per_seconds=3600, key_func=None)`

Implements per-user rate limiting to prevent abuse.

**Parameters:**
- `max_requests` (int): Maximum number of requests allowed
- `per_seconds` (int): Time window in seconds
- `key_func` (callable): Function to generate custom rate limit key

**Example:**
```python
# Basic rate limiting
@rate_limit_per_user(max_requests=10, per_seconds=60)
def create_post():
    # Users can create max 10 posts per minute
    return create_new_post()

# Custom rate limiting per resource
@rate_limit_per_user(
    max_requests=5, 
    per_seconds=300,
    key_func=lambda: f"comment_{request.view_args['post_id']}"
)
def add_comment(post_id):
    # Users can comment max 5 times per post per 5 minutes
    return add_comment_to_post(post_id)
```

## Combining Decorators

Decorators can be combined for comprehensive functionality:

```python
@cache_result(timeout=300, key_prefix='user_stats')
@timing_decorator()
@performance_monitor(threshold=1.5)
def get_user_statistics(user_id):
    # Function with caching, timing, and performance monitoring
    return calculate_user_stats(user_id)

@validate_json_input(required_fields=['email'])
@sanitize_input(fields=['username'], max_length=50)
@rate_limit_per_user(max_requests=3, per_seconds=3600)
def update_profile():
    # API endpoint with validation, sanitization, and rate limiting
    return update_user_profile()
```

## Best Practices

### Caching
- Use appropriate timeout values based on data freshness requirements
- Cache expensive operations like complex queries or calculations
- Use `unless` parameter to skip caching for authenticated users when needed
- Invalidate caches when underlying data changes

### Performance Monitoring
- Set realistic thresholds based on expected performance
- Use timing decorators during development to identify bottlenecks
- Implement alert callbacks for production monitoring
- Monitor both successful and failed operations

### Input Validation
- Always validate and sanitize user input in API endpoints
- Use schema validation for complex data structures
- Implement rate limiting on resource-intensive operations
- Combine decorators for comprehensive input handling

### Error Handling
- All decorators include error handling to prevent application crashes
- Failed cache operations don't block function execution
- Validation errors return appropriate HTTP status codes
- Rate limiting provides clear error messages

## Configuration

The decorators use Flask-Caching which should be configured in your application:

```python
# app/config.py
class Config:
    CACHE_TYPE = 'redis'
    CACHE_REDIS_URL = 'redis://localhost:6379/0'
    CACHE_DEFAULT_TIMEOUT = 300

# app/__init__.py
from flask_caching import Cache
cache = Cache()

def create_app():
    app = Flask(__name__)
    cache.init_app(app)
    return app
```

## Testing

The decorators include comprehensive logging and error handling. Use the provided test script to verify functionality:

```bash
python test_performance_decorators.py
```

This will test basic decorator functionality and demonstrate their usage patterns.

## Educational Value

These decorators demonstrate several important Flask and Python concepts:

- **Decorator Pattern**: Advanced use of Python decorators with parameters
- **Caching Strategies**: Different approaches to caching in web applications
- **Performance Monitoring**: Techniques for measuring and alerting on performance
- **Input Validation**: Best practices for handling user input securely
- **Error Handling**: Graceful degradation when external services fail
- **Logging**: Structured logging for debugging and monitoring

Each decorator includes extensive documentation and examples to help understand both the implementation and usage patterns.