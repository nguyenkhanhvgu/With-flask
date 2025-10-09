#!/usr/bin/env python3
"""
Test Cache Setup

This script tests the caching functionality to ensure it's working correctly.
It demonstrates cache operations and verifies the BlogService caching methods.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import cache
from app.services.blog_service import BlogService
from app.utils.cache_utils import get_cache_stats, warm_cache
from app.middleware.caching import CacheManager


def test_basic_cache_operations():
    """Test basic cache set/get/delete operations."""
    print("Testing basic cache operations...")
    
    # Test cache set
    test_key = 'test_cache_key'
    test_value = 'test_cache_value'
    
    cache.set(test_key, test_value, timeout=60)
    print(f"✓ Set cache key '{test_key}' with value '{test_value}'")
    
    # Test cache get
    retrieved_value = cache.get(test_key)
    if retrieved_value == test_value:
        print(f"✓ Retrieved correct value: '{retrieved_value}'")
    else:
        print(f"✗ Retrieved incorrect value: '{retrieved_value}' (expected: '{test_value}')")
        return False
    
    # Test cache delete
    cache.delete(test_key)
    deleted_value = cache.get(test_key)
    if deleted_value is None:
        print("✓ Cache key deleted successfully")
    else:
        print(f"✗ Cache key not deleted, still contains: '{deleted_value}'")
        return False
    
    return True


def test_blog_service_caching():
    """Test BlogService caching methods."""
    print("\nTesting BlogService caching methods...")
    
    try:
        # Test trending posts caching
        trending_posts = BlogService.get_trending_posts(days=7, limit=5)
        print(f"✓ Retrieved {len(trending_posts)} trending posts")
        
        # Test popular posts caching
        popular_posts = BlogService.get_popular_posts(limit=5)
        print(f"✓ Retrieved {len(popular_posts)} popular posts")
        
        # Test posts listing with caching
        posts_result = BlogService.get_posts_with_caching(page=1, per_page=5)
        posts_count = len(posts_result['posts'])
        print(f"✓ Retrieved {posts_count} posts with pagination")
        
        # Test cache warming
        warm_success = BlogService.warm_popular_content()
        if warm_success:
            print("✓ Cache warming completed successfully")
        else:
            print("✗ Cache warming failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ BlogService caching test failed: {e}")
        return False


def test_cache_stats():
    """Test cache statistics retrieval."""
    print("\nTesting cache statistics...")
    
    try:
        stats = get_cache_stats()
        print(f"✓ Cache type: {stats.get('cache_type', 'Unknown')}")
        print(f"✓ Hit rate: {stats.get('hit_rate', 0)}%")
        
        if 'used_memory' in stats:
            print(f"✓ Memory used: {stats['used_memory']}")
        
        return True
        
    except Exception as e:
        print(f"✗ Cache stats test failed: {e}")
        return False


def test_cache_manager():
    """Test CacheManager operations."""
    print("\nTesting CacheManager operations...")
    
    try:
        # Test cache info
        info = CacheManager.get_info()
        if info:
            print("✓ Cache info retrieved successfully")
        else:
            print("✗ Failed to get cache info")
            return False
        
        # Test cache warming
        warm_success = CacheManager.warm_cache()
        if warm_success:
            print("✓ CacheManager warming completed successfully")
        else:
            print("✗ CacheManager warming failed")
        
        return True
        
    except Exception as e:
        print(f"✗ CacheManager test failed: {e}")
        return False


def main():
    """Run all cache tests."""
    print("=" * 50)
    print("CACHE FUNCTIONALITY TEST")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app('development')
    
    with app.app_context():
        tests = [
            test_basic_cache_operations,
            test_cache_stats,
            test_cache_manager,
            test_blog_service_caching,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    print(f"✗ {test.__name__} failed")
            except Exception as e:
                print(f"✗ {test.__name__} failed with exception: {e}")
        
        print("\n" + "=" * 50)
        print(f"RESULTS: {passed}/{total} tests passed")
        print("=" * 50)
        
        if passed == total:
            print("🎉 All cache tests passed! Caching is working correctly.")
            return True
        else:
            print("❌ Some cache tests failed. Please check the configuration.")
            return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)