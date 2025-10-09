"""
Admin Cache Management Routes

This module provides administrative interface for cache management,
demonstrating cache monitoring, invalidation, and warming operations.
"""

from flask import render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_required
from app.blueprints.admin import bp
from app.utils.decorators import admin_required, timing_decorator
from app.extensions import cache
from app.utils.cache_utils import get_cache_stats, warm_cache, CacheInvalidator
from app.services.blog_service import BlogService
from app.middleware.caching import CacheManager
import json


@bp.route('/cache')
@login_required
@admin_required
@timing_decorator()
def cache_dashboard():
    """
    Display cache management dashboard.
    
    This view demonstrates cache monitoring and provides
    an interface for cache management operations.
    """
    try:
        # Get cache statistics
        cache_stats = get_cache_stats()
        
        # Get cache configuration
        cache_config = {
            'type': current_app.config.get('CACHE_TYPE', 'Unknown'),
            'default_timeout': current_app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
            'key_prefix': current_app.config.get('CACHE_KEY_PREFIX', 'flask_blog:'),
            'redis_host': current_app.config.get('CACHE_REDIS_HOST', 'localhost'),
            'redis_port': current_app.config.get('CACHE_REDIS_PORT', 6379),
            'redis_db': current_app.config.get('CACHE_REDIS_DB', 0)
        }
        
        return render_template(
            'admin/cache_dashboard.html',
            cache_stats=cache_stats,
            cache_config=cache_config,
            title='Cache Management'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error loading cache dashboard: {e}")
        flash('Error loading cache dashboard.', 'error')
        return redirect(url_for('admin.dashboard'))


@bp.route('/cache/clear', methods=['POST'])
@login_required
@admin_required
def clear_cache():
    """
    Clear all cache entries.
    
    This endpoint demonstrates cache invalidation operations
    and provides feedback on the operation status.
    """
    try:
        success = CacheManager.clear_all()
        
        if success:
            flash('All cache entries cleared successfully.', 'success')
            current_app.logger.info(f'Cache cleared by admin user {current_user.username}')
        else:
            flash('Failed to clear cache entries.', 'error')
        
        if request.is_json:
            return jsonify({
                'success': success,
                'message': 'Cache cleared successfully' if success else 'Failed to clear cache'
            })
        
        return redirect(url_for('admin.cache_dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Error clearing cache: {e}")
        flash('An error occurred while clearing the cache.', 'error')
        
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        
        return redirect(url_for('admin.cache_dashboard'))


@bp.route('/cache/warm', methods=['POST'])
@login_required
@admin_required
def warm_cache():
    """
    Warm cache with popular content.
    
    This endpoint demonstrates cache warming strategies
    for improving application performance.
    """
    try:
        # Warm cache using blog service
        success = BlogService.warm_popular_content()
        
        if success:
            flash('Cache warmed successfully with popular content.', 'success')
            current_app.logger.info(f'Cache warmed by admin user {current_user.username}')
        else:
            flash('Failed to warm cache.', 'error')
        
        if request.is_json:
            return jsonify({
                'success': success,
                'message': 'Cache warmed successfully' if success else 'Failed to warm cache'
            })
        
        return redirect(url_for('admin.cache_dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Error warming cache: {e}")
        flash('An error occurred while warming the cache.', 'error')
        
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        
        return redirect(url_for('admin.cache_dashboard'))


@bp.route('/cache/invalidate', methods=['POST'])
@login_required
@admin_required
def invalidate_cache():
    """
    Invalidate specific cache patterns.
    
    This endpoint allows selective cache invalidation
    based on patterns or specific keys.
    """
    try:
        pattern = request.form.get('pattern') or request.json.get('pattern') if request.is_json else None
        
        if not pattern:
            flash('Please specify a cache pattern to invalidate.', 'error')
            if request.is_json:
                return jsonify({'success': False, 'error': 'Pattern required'}), 400
            return redirect(url_for('admin.cache_dashboard'))
        
        # Predefined safe patterns
        safe_patterns = {
            'posts': 'posts:*',
            'users': 'user:*',
            'trending': 'trending:*',
            'search': 'search:*',
            'api': 'api:*',
            'profiles': 'profile:*'
        }
        
        if pattern in safe_patterns:
            cache_pattern = safe_patterns[pattern]
            CacheInvalidator._delete_pattern(cache_pattern)
            
            flash(f'Cache pattern "{pattern}" invalidated successfully.', 'success')
            current_app.logger.info(f'Cache pattern "{pattern}" invalidated by admin user {current_user.username}')
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': f'Pattern "{pattern}" invalidated successfully'
                })
        else:
            flash('Invalid cache pattern specified.', 'error')
            if request.is_json:
                return jsonify({'success': False, 'error': 'Invalid pattern'}), 400
        
        return redirect(url_for('admin.cache_dashboard'))
        
    except Exception as e:
        current_app.logger.error(f"Error invalidating cache pattern: {e}")
        flash('An error occurred while invalidating cache.', 'error')
        
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        
        return redirect(url_for('admin.cache_dashboard'))


@bp.route('/cache/stats')
@login_required
@admin_required
def cache_stats_api():
    """
    Get cache statistics as JSON.
    
    This endpoint provides real-time cache statistics
    for monitoring and dashboard updates.
    """
    try:
        stats = get_cache_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting cache stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/cache/keys')
@login_required
@admin_required
def cache_keys():
    """
    List cache keys (limited for performance).
    
    This endpoint provides a sample of cache keys
    for debugging and monitoring purposes.
    """
    try:
        # This is a simplified implementation
        # In production, you'd want to use Redis SCAN for better performance
        sample_keys = []
        
        if hasattr(cache.cache, '_write_client'):
            # Redis implementation
            redis_client = cache.cache._write_client
            prefix = current_app.config.get('CACHE_KEY_PREFIX', 'flask_blog:')
            
            # Get a sample of keys (limited to 100 for performance)
            cursor = 0
            count = 0
            while cursor != 0 or count == 0:
                cursor, keys = redis_client.scan(cursor, match=f"{prefix}*", count=20)
                sample_keys.extend([key.decode() if isinstance(key, bytes) else key for key in keys])
                count += 1
                if count >= 5 or len(sample_keys) >= 100:  # Limit to prevent performance issues
                    break
        
        return jsonify({
            'success': True,
            'keys': sample_keys[:100],  # Limit to 100 keys
            'total_shown': len(sample_keys[:100]),
            'note': 'Showing sample of cache keys (limited for performance)'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting cache keys: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/cache/test')
@login_required
@admin_required
def test_cache():
    """
    Test cache functionality.
    
    This endpoint tests basic cache operations
    to verify cache is working correctly.
    """
    try:
        import time
        
        test_key = 'cache_test_key'
        test_value = f'test_value_{int(time.time())}'
        
        # Test cache set
        cache.set(test_key, test_value, timeout=60)
        
        # Test cache get
        retrieved_value = cache.get(test_key)
        
        # Test cache delete
        cache.delete(test_key)
        
        # Verify deletion
        deleted_value = cache.get(test_key)
        
        test_results = {
            'set_operation': 'success',
            'get_operation': 'success' if retrieved_value == test_value else 'failed',
            'delete_operation': 'success' if deleted_value is None else 'failed',
            'test_value': test_value,
            'retrieved_value': retrieved_value,
            'after_delete': deleted_value
        }
        
        overall_success = all(result == 'success' for result in [
            test_results['set_operation'],
            test_results['get_operation'],
            test_results['delete_operation']
        ])
        
        return jsonify({
            'success': overall_success,
            'test_results': test_results,
            'message': 'Cache test completed successfully' if overall_success else 'Cache test failed'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error testing cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Cache test failed with exception'
        }), 500


@bp.route('/cache/performance')
@login_required
@admin_required
def cache_performance():
    """
    Get cache performance metrics.
    
    This endpoint provides performance-related cache metrics
    for monitoring and optimization.
    """
    try:
        import time
        
        # Test cache performance
        test_iterations = 100
        start_time = time.time()
        
        for i in range(test_iterations):
            test_key = f'perf_test_{i}'
            cache.set(test_key, f'value_{i}', timeout=60)
            cache.get(test_key)
            cache.delete(test_key)
        
        total_time = time.time() - start_time
        avg_operation_time = (total_time / (test_iterations * 3)) * 1000  # ms per operation
        
        performance_metrics = {
            'test_iterations': test_iterations,
            'total_operations': test_iterations * 3,  # set, get, delete
            'total_time_seconds': round(total_time, 4),
            'average_operation_time_ms': round(avg_operation_time, 4),
            'operations_per_second': round((test_iterations * 3) / total_time, 2)
        }
        
        return jsonify({
            'success': True,
            'performance_metrics': performance_metrics,
            'message': 'Performance test completed successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error testing cache performance: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Performance test failed'
        }), 500