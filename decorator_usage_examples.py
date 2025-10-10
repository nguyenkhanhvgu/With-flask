#!/usr/bin/env python3
"""
Comprehensive examples of using performance and caching decorators.

This file demonstrates how to use all the performance and caching decorators
implemented in app/utils/decorators.py with practical examples.
"""

from flask import Flask, request, jsonify, render_template_string
from app.utils.decorators import (
    cache_result,
    cache_page,
    invalidate_cache,
    timing_decorator,
    performance_monitor,
    validate_json_input,
    sanitize_input,
    rate_limit_per_user,
    memoize,
    cache_control,
    compress_response
)
import time
import logging

# Configure logging to see timing information
logging.basicConfig(level=logging.INFO)

# Example 1: Caching expensive database queries
@cache_result(timeout=600, key_prefix='user_posts')
@timing_decorator(include_args=True)
def get_user_posts(user_id):
    """
    Example of caching expensive database operations.
    In a real app, this would query the database.
    """
    # Simulate expensive database query
    time.sleep(0.1)
    return [
        {'id': 1, 'title': f'Post 1 by user {user_id}', 'content': 'Content 1'},
        {'id': 2, 'title': f'Post 2 by user {user_id}', 'content': 'Content 2'}
    ]


# Example 2: Performance monitoring with alerts
def slow_query_alert(func_name, execution_time):
    """Alert callback for slow operations."""
    print(f"🚨 ALERT: {func_name} took {execution_time:.2f}s (too slow!)")

@performance_monitor(threshold=0.05, alert_callback=slow_query_alert)
@timing_decorator()
def complex_analytics(data_size=1000):
    """
    Example of performance monitoring for complex operations.
    """
    # Simulate complex calculation
    total = sum(range(data_size))
    time.sleep(0.1)  # This will trigger the alert
    return {'total': total, 'processed': data_size}


# Example 3: Memoization for recursive functions
@memoize(timeout=3600)
def fibonacci(n):
    """
    Example of memoization for expensive recursive calculations.
    """
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)


# Example 4: Input validation and sanitization
@validate_json_input(required_fields=['title', 'content'])
@sanitize_input(fields=['title', 'content'], strip_html=True, max_length=200)
def create_blog_post():
    """
    Example API endpoint with input validation and sanitization.
    """
    from flask import g
    data = g.sanitized_json
    
    # Process the clean, validated data
    return {
        'status': 'success',
        'post': {
            'title': data['title'],
            'content': data['content'],
            'created_at': time.time()
        }
    }


# Example 5: Rate limiting for user actions
@rate_limit_per_user(max_requests=5, per_seconds=60)
@timing_decorator()
def send_email_notification(user_id, message):
    """
    Example of rate-limited operation (email sending).
    """
    # Simulate email sending
    time.sleep(0.05)
    return {'status': 'email_sent', 'user_id': user_id, 'message': message}


# Example 6: Page caching with user-specific content
@cache_page(timeout=300, key_prefix='dashboard', vary_on_user=True)
@cache_control(max_age=300, public=False)
def user_dashboard(user_id):
    """
    Example of caching user-specific pages.
    """
    # Simulate expensive page rendering
    time.sleep(0.1)
    
    user_data = get_user_posts(user_id)  # This will use cached result
    
    return f"""
    <html>
        <head><title>Dashboard for User {user_id}</title></head>
        <body>
            <h1>User {user_id} Dashboard</h1>
            <p>Posts: {len(user_data)}</p>
            <p>Generated at: {time.time()}</p>
        </body>
    </html>
    """


# Example 7: Cache invalidation after data changes
@invalidate_cache(cache_keys=['user_posts:get_user_posts'])
@timing_decorator()
def update_user_post(user_id, post_id, new_content):
    """
    Example of cache invalidation after data modification.
    """
    # Simulate database update
    time.sleep(0.05)
    
    # After updating, the cache for user posts is invalidated
    return {
        'status': 'updated',
        'user_id': user_id,
        'post_id': post_id,
        'content': new_content
    }


# Example 8: Response compression for large data
@compress_response(compression_level=6, min_size=500)
@cache_result(timeout=1800, key_prefix='large_dataset')
def get_large_dataset():
    """
    Example of response compression for large API responses.
    """
    # Generate large dataset
    data = {
        'items': [
            {'id': i, 'name': f'Item {i}', 'description': f'Description for item {i}' * 10}
            for i in range(100)
        ],
        'metadata': {
            'total': 100,
            'generated_at': time.time(),
            'version': '1.0'
        }
    }
    return data


# Example 9: Combining multiple decorators
@cache_result(timeout=300, key_prefix='user_stats')
@timing_decorator(include_args=True)
@performance_monitor(threshold=0.2)
def get_user_statistics(user_id):
    """
    Example combining caching, timing, and performance monitoring.
    """
    # Simulate complex statistics calculation
    time.sleep(0.1)
    
    posts = get_user_posts(user_id)  # Uses cached result
    
    return {
        'user_id': user_id,
        'total_posts': len(posts),
        'avg_post_length': sum(len(post['content']) for post in posts) / len(posts) if posts else 0,
        'calculated_at': time.time()
    }


# Example 10: Schema-based validation
post_schema = {
    'title': {'type': 'string', 'maxlength': 100, 'required': True},
    'content': {'type': 'string', 'minlength': 10, 'required': True},
    'category': {'type': 'string', 'maxlength': 50},
    'tags': {'type': 'list'}
}

@validate_json_input(schema=post_schema)
@sanitize_input(fields=['title', 'content', 'category'], max_length=1000)
def create_validated_post():
    """
    Example with comprehensive schema validation.
    """
    from flask import g
    data = g.sanitized_json
    
    return {
        'status': 'created',
        'post': data,
        'validation': 'passed'
    }


def demonstrate_decorators():
    """
    Demonstrate all the decorators with example usage.
    """
    print("🚀 Demonstrating Performance and Caching Decorators\n")
    
    # Example 1: Caching
    print("1. Testing cache_result decorator:")
    start_time = time.time()
    result1 = get_user_posts(123)
    first_call_time = time.time() - start_time
    
    start_time = time.time()
    result2 = get_user_posts(123)  # Should be cached
    second_call_time = time.time() - start_time
    
    print(f"   First call: {first_call_time:.3f}s")
    print(f"   Second call: {second_call_time:.3f}s (cached)")
    print(f"   Speed improvement: {first_call_time/second_call_time:.1f}x\n")
    
    # Example 2: Performance monitoring
    print("2. Testing performance_monitor decorator:")
    analytics_result = complex_analytics(5000)
    print(f"   Result: {analytics_result}\n")
    
    # Example 3: Memoization
    print("3. Testing memoize decorator:")
    start_time = time.time()
    fib_result = fibonacci(10)
    fib_time = time.time() - start_time
    print(f"   fibonacci(10) = {fib_result} (calculated in {fib_time:.3f}s)\n")
    
    # Example 4: Statistics with multiple decorators
    print("4. Testing combined decorators:")
    stats = get_user_statistics(123)
    print(f"   User stats: {stats}\n")
    
    # Example 5: Large dataset with compression
    print("5. Testing compress_response decorator:")
    large_data = get_large_dataset()
    print(f"   Generated dataset with {len(large_data['items'])} items\n")
    
    print("✅ All decorator demonstrations completed successfully!")
    print("\nImplemented decorators provide:")
    print("   • Intelligent caching for performance optimization")
    print("   • Comprehensive performance monitoring and alerting")
    print("   • Robust input validation and sanitization")
    print("   • Flexible rate limiting capabilities")
    print("   • HTTP caching and response compression")
    print("   • Memoization for expensive calculations")


if __name__ == '__main__':
    demonstrate_decorators()