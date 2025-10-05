# Logging Middleware Guide

This guide explains how to use the comprehensive logging middleware implemented in the Flask blog application.

## Overview

The logging middleware provides:
- **Request/Response Tracking**: Automatic logging of all HTTP requests with timing information
- **Structured Logging**: JSON-formatted logs for easy parsing and analysis
- **Request ID Tracking**: Unique request IDs for debugging and tracing
- **Performance Monitoring**: Detection and logging of slow operations
- **User Action Auditing**: Logging of important user actions for security and analytics

## Features

### 1. Automatic Request Logging

Every HTTP request is automatically logged with:
- Unique request ID
- Request method, URL, and path
- Client IP address and User-Agent
- Request timing (start, end, duration)
- Response status code and content length
- User information (if authenticated)

### 2. Structured JSON Logging

All logs are formatted as structured JSON for easy parsing:

```json
{
  "timestamp": "2025-10-05T12:34:28.823528",
  "level": "INFO",
  "logger": "flask_blog.requests",
  "message": "Request started",
  "event": "request_start",
  "request_id": "c813c644-188e-468e-ad8a-ce9bbb396432",
  "method": "GET",
  "url": "http://127.0.0.1:5001/",
  "path": "/",
  "remote_addr": "127.0.0.1",
  "user_agent": "python-requests/2.32.3"
}
```

### 3. Request ID Tracking

Each request gets a unique UUID that can be used for:
- Debugging issues across multiple log entries
- Tracing requests through the application
- Correlating frontend and backend logs

Access the request ID in your code:
```python
from app.middleware.logging import get_request_id

request_id = get_request_id()
```

### 4. Performance Monitoring

Use the `@log_performance` decorator to monitor slow operations:

```python
from app.middleware.logging import log_performance

@log_performance(threshold_ms=1000)  # Log if operation takes > 1 second
def expensive_operation():
    # Your code here
    pass
```

### 5. User Action Logging

Log important user actions for audit trails:

```python
from app.middleware.logging import log_user_action

# Log user registration
log_user_action('user_registration', {
    'username': user.username,
    'email': user.email,
    'user_id': user.id
})

# Log user login
log_user_action('user_login', {
    'username': user.username,
    'user_id': user.id,
    'remember_me': remember_flag
})
```

## Configuration

### Log Levels

Configure logging levels in your environment config:

```python
# Development
LOG_LEVEL = 'DEBUG'
LOG_FILE = 'logs/development.log'

# Production
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/production.log'

# Testing
LOG_LEVEL = 'WARNING'
LOG_FILE = None  # No file logging during tests
```

### Log Files

The middleware creates several log files:
- `logs/development.log` - All request logs in development
- `logs/production.log` - Request logs in production
- `logs/errors.log` - Error-level logs only

## Usage Examples

### 1. Basic Request Tracking

The middleware automatically tracks all requests. No additional code needed.

### 2. Custom Performance Monitoring

```python
from app.middleware.logging import log_performance

@bp.route('/expensive-operation')
@log_performance(threshold_ms=500)
def expensive_route():
    # This will be logged if it takes > 500ms
    result = perform_complex_calculation()
    return jsonify(result)
```

### 3. User Action Auditing

```python
from app.middleware.logging import log_user_action

@bp.route('/delete-post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    # Log the deletion action
    log_user_action('post_deletion', {
        'post_id': post_id,
        'post_title': post.title,
        'author_id': post.author_id
    })
    
    db.session.delete(post)
    db.session.commit()
    
    return redirect(url_for('blog.posts'))
```

### 4. Request ID in Templates

Access the request ID in Jinja2 templates:

```html
<!-- Add to base template for debugging -->
{% if config.DEBUG %}
<meta name="request-id" content="{{ g.request_id }}">
{% endif %}
```

## Log Analysis

### Parsing JSON Logs

Use tools like `jq` to analyze logs:

```bash
# Find all requests that took longer than 1 second
cat logs/development.log | jq 'select(.duration_ms > 1000)'

# Count requests by status code
cat logs/development.log | jq -r '.status_code' | sort | uniq -c

# Find all user actions
cat logs/development.log | jq 'select(.event == "user_action")'
```

### Log Monitoring

Set up log monitoring with tools like:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Grafana + Loki**
- **Splunk**
- **DataDog**

## Security Considerations

### Sensitive Data

The middleware automatically excludes sensitive data:
- Passwords are never logged
- Session tokens are not included
- Personal data is limited to usernames and IDs

### Log Rotation

Implement log rotation to prevent disk space issues:

```python
# In production config
import logging.handlers

# Rotate logs daily, keep 30 days
handler = logging.handlers.TimedRotatingFileHandler(
    'logs/production.log',
    when='midnight',
    backupCount=30
)
```

## Troubleshooting

### Common Issues

1. **Missing Request IDs**: Ensure middleware is initialized before blueprints
2. **No File Logs**: Check file permissions and directory existence
3. **Performance Impact**: Adjust log levels in production

### Debug Mode

Enable debug logging to see all middleware activity:

```python
# In development config
LOG_LEVEL = 'DEBUG'
SQLALCHEMY_ECHO = True  # Also log SQL queries
```

## Best Practices

1. **Use Structured Data**: Always include relevant context in log_user_action calls
2. **Monitor Performance**: Set appropriate thresholds for performance logging
3. **Rotate Logs**: Implement log rotation in production
4. **Secure Logs**: Protect log files with appropriate permissions
5. **Monitor Disk Space**: Set up alerts for log directory disk usage

## Integration with Monitoring Tools

### Prometheus Metrics

Extend the middleware to export metrics:

```python
from prometheus_client import Counter, Histogram

request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')
```

### Health Checks

Add logging to health check endpoints:

```python
@bp.route('/health')
def health_check():
    log_user_action('health_check', {'status': 'ok'})
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow()})
```

This logging middleware provides a solid foundation for monitoring, debugging, and auditing your Flask application.