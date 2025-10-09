#!/usr/bin/env python3
"""
Practical Examples of Performance and Caching Decorators

This file demonstrates how to use the new decorators in real blog application scenarios.
These examples show best practices for caching, performance monitoring, and input validation.
"""

from flask import request, jsonify, render_template, g
from flask_login import current_user
from app.utils.decorators import (
    cache_result, cache_page, invalidate_cache, timing_decorator,
    performance_monitor, validate_json_input, sanitize_input, rate_limit_per_user
)
from app.models import Post, User, Comment
from app.extensions import db


# =============================================================================
# CACHING EXAMPLES
# =============================================================================

@cache_result(timeout=600, key_prefix='trending_posts')
def get_trending_posts(limit=10):
    """
    Get trending posts with caching.
    
    This expensive operation calculates trending posts based on views,
    likes, and comments. Results are cached for 10 minutes.
    """
    # Simulate expensive trending algorithm
    posts = Post.query.join(Post.views).group_by(Post.id)\
        .order_by(db.func.count(Post.views).desc())\
        .limit(limit).all()
    return posts


@cache_result(timeout=300, unless=lambda: current_user.is_authenticated)
def get_public_posts_count():
    """
    Cache public post count only for anonymous users.
    
    Authenticated users get real-time counts, while anonymous
    users get cached results for better performance.
    """
    return Post.query.filter_by(published=True).count()


@cache_page(timeout=1800, key_prefix='category_page', vary_on_user=False)
def category_posts_view(category_id):
    """
    Cache entire category page for 30 minutes.
    
    Category pages don't change frequently and can be safely
    cached for all users.
    """
    category = Category.query.get_or_404(category_id)
    posts = Post.query.filter_by(category_id=category_id, published=True)\
        .order_by(Post.created_at.desc()).all()
    return render_template('category_posts.html', category=category, posts=posts)


@invalidate_cache(cache_keys=['trending_posts:get_trending_posts'])
def create_new_post(title, content, user_id):
    """
    Create a new post and invalidate trending posts cache.
    
    When new posts are created, we need to clear the trending
    posts cache so users see updated content.
    """
    post = Post(title=title, content=content, user_id=user_id)
    db.session.add(post)
    db.session.commit()
    return post


# =============================================================================
# PERFORMANCE MONITORING EXAMPLES
# =============================================================================

@timing_decorator(include_args=True)
def search_posts(query, page=1):
    """
    Search posts with execution time logging.
    
    Search operations can be slow, so we monitor their
    performance to identify optimization opportunities.
    """
    posts = Post.query.filter(
        Post.title.contains(query) | Post.content.contains(query)
    ).paginate(page=page, per_page=10)
    return posts


@performance_monitor(threshold=2.0)
def generate_user_analytics(user_id):
    """
    Generate user analytics with performance monitoring.
    
    This operation should complete within 2 seconds.
    If it takes longer, an alert is triggered.
    """
    user = User.query.get(user_id)
    
    # Simulate complex analytics calculation
    analytics = {
        'total_posts': user.posts.count(),
        'total_comments': Comment.query.filter_by(user_id=user_id).count(),
        'avg_post_views': db.session.query(db.func.avg(PostView.id))\
            .join(Post).filter(Post.user_id == user_id).scalar() or 0,
        'follower_count': user.followers.count(),
        'following_count': user.following.count()
    }
    
    return analytics


def slow_operation_alert(func_name, execution_time):
    """
    Alert callback for slow operations.
    
    This function is called when operations exceed performance thresholds.
    In production, this could send alerts to monitoring systems.
    """
    print(f"PERFORMANCE ALERT: {func_name} took {execution_time:.2f} seconds")
    # In production: send to monitoring system, log to file, etc.


@performance_monitor(threshold=1.0, alert_callback=slow_operation_alert)
def complex_database_query():
    """
    Complex query with custom alert handling.
    
    This demonstrates how to use custom alert callbacks
    for different types of operations.
    """
    # Simulate complex query
    result = db.session.execute("""
        SELECT u.username, COUNT(p.id) as post_count, AVG(pv.time_spent) as avg_time
        FROM users u
        LEFT JOIN posts p ON u.id = p.user_id
        LEFT JOIN post_views pv ON p.id = pv.post_id
        GROUP BY u.id, u.username
        ORDER BY post_count DESC
        LIMIT 10
    """).fetchall()
    
    return result


# =============================================================================
# INPUT VALIDATION EXAMPLES
# =============================================================================

@validate_json_input(required_fields=['title', 'content'])
@sanitize_input(fields=['title', 'content'], max_length=1000)
def api_create_post():
    """
    API endpoint for creating posts with validation and sanitization.
    
    This demonstrates combining multiple decorators for comprehensive
    input handling in API endpoints.
    """
    # Get sanitized data from g object (set by sanitize_input decorator)
    data = g.sanitized_json
    
    post = Post(
        title=data['title'],
        content=data['content'],
        user_id=current_user.id
    )
    
    db.session.add(post)
    db.session.commit()
    
    return jsonify({
        'message': 'Post created successfully',
        'post_id': post.id
    })


# Schema for post updates
POST_UPDATE_SCHEMA = {
    'title': {'type': 'string', 'maxlength': 200, 'required': True},
    'content': {'type': 'string', 'minlength': 10, 'required': True},
    'published': {'type': 'boolean'},
    'category_id': {'type': 'integer'}
}

@validate_json_input(schema=POST_UPDATE_SCHEMA)
def api_update_post(post_id):
    """
    API endpoint for updating posts with schema validation.
    
    This demonstrates using a schema for comprehensive
    input validation including type checking and length limits.
    """
    post = Post.query.get_or_404(post_id)
    data = request.get_json()
    
    # Update post with validated data
    post.title = data['title']
    post.content = data['content']
    
    if 'published' in data:
        post.published = data['published']
    
    if 'category_id' in data:
        post.category_id = data['category_id']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Post updated successfully',
        'post': {
            'id': post.id,
            'title': post.title,
            'published': post.published
        }
    })


@sanitize_input(fields=['comment'], strip_html=True, max_length=500)
def add_comment_to_post(post_id):
    """
    Add comment with input sanitization.
    
    Comments need HTML stripping and length limits to prevent
    abuse and maintain data quality.
    """
    post = Post.query.get_or_404(post_id)
    
    # Get sanitized comment from form data
    comment_text = request.form.get('comment', '').strip()
    
    if not comment_text:
        return jsonify({'error': 'Comment cannot be empty'}), 400
    
    comment = Comment(
        content=comment_text,
        post_id=post_id,
        user_id=current_user.id
    )
    
    db.session.add(comment)
    db.session.commit()
    
    return jsonify({
        'message': 'Comment added successfully',
        'comment_id': comment.id
    })


# =============================================================================
# RATE LIMITING EXAMPLES
# =============================================================================

@rate_limit_per_user(max_requests=5, per_seconds=300)
def create_post_endpoint():
    """
    Create post with rate limiting.
    
    Users can create maximum 5 posts per 5 minutes
    to prevent spam and abuse.
    """
    # Post creation logic here
    return jsonify({'message': 'Post created'})


@rate_limit_per_user(
    max_requests=10, 
    per_seconds=60,
    key_func=lambda: f"comment_{request.view_args.get('post_id')}"
)
def add_comment_endpoint(post_id):
    """
    Add comment with per-post rate limiting.
    
    Users can add maximum 10 comments per post per minute.
    This prevents comment spam on individual posts.
    """
    # Comment creation logic here
    return jsonify({'message': 'Comment added'})


@rate_limit_per_user(max_requests=20, per_seconds=3600)
def api_search_posts():
    """
    Search API with rate limiting.
    
    Search operations are expensive, so we limit users
    to 20 searches per hour.
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Search query required'}), 400
    
    # Search logic here
    results = search_posts(query)
    
    return jsonify({
        'query': query,
        'results': [{'id': p.id, 'title': p.title} for p in results.items]
    })


# =============================================================================
# COMBINED DECORATOR EXAMPLES
# =============================================================================

@cache_result(timeout=300, key_prefix='user_stats')
@timing_decorator()
@performance_monitor(threshold=1.5)
def get_user_statistics(user_id):
    """
    Get user statistics with caching, timing, and performance monitoring.
    
    This demonstrates how multiple decorators can be combined
    for comprehensive functionality.
    """
    user = User.query.get(user_id)
    if not user:
        return None
    
    stats = {
        'posts_count': user.posts.count(),
        'comments_count': Comment.query.filter_by(user_id=user_id).count(),
        'followers_count': user.followers.count(),
        'following_count': user.following.count(),
        'total_post_views': sum(post.view_count for post in user.posts)
    }
    
    return stats


@validate_json_input(required_fields=['email', 'username'])
@sanitize_input(fields=['username', 'bio'], max_length=200)
@rate_limit_per_user(max_requests=3, per_seconds=3600)
def update_user_profile():
    """
    Update user profile with validation, sanitization, and rate limiting.
    
    This endpoint combines all input handling decorators for
    comprehensive protection and data quality.
    """
    data = g.sanitized_json
    
    # Update user profile logic
    current_user.username = data['username']
    current_user.email = data['email']
    
    if 'bio' in data:
        current_user.bio = data['bio']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email
        }
    })


if __name__ == '__main__':
    print("Performance and Caching Decorators Usage Examples")
    print("=" * 60)
    print("\nThis file contains practical examples of how to use")
    print("the new decorators in a Flask blog application:")
    print("\n✓ Caching expensive operations (trending posts, analytics)")
    print("✓ Performance monitoring (search, database queries)")
    print("✓ Input validation and sanitization (API endpoints)")
    print("✓ Rate limiting (post creation, comments, search)")
    print("✓ Combined decorator usage for comprehensive functionality")
    print("\nSee the code above for detailed implementation examples.")