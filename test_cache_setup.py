#!/usr/bin/env python3
"""
Test script to verify Redis caching infrastructure setup.

This script tests the basic functionality of the Redis caching system
to ensure it's properly configured and working.
"""

import os
import sys
import time

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.extensions import cache
from app.utils.cache_utils import CacheKeyGenerator, CacheInvalidator
from app.middleware.caching import CacheManager


def test_cache_connection():
    """Test basic cache connection and operations."""
    print("Testing cache connection...")
    
    try:
        # Test basic set/get operations
        test_key = "test:connection"
        test_value = "Hello, Redis!"
        
        cache.set(test_key, test_value, timeout=60)
        retrieved_value = cache.get(test_key)
        
        if retrieved_value == test_value:
            print("✓ Cache connection successful")
            cache.delete(test_key)  # Clean up
            return True
        else:
            print("✗ Cache connection failed - value mismatch")
            return False
            
    except Exception as e:
        print(f"✗ Cache connection failed: {e}")
        print("  Note: This might be because Redis is not running.")
        print("  For testing purposes, the app will fall back to SimpleCache.")
        return False


def test_cache_key_generation():
    """Test cache key generation utilities."""
    print("Testing cache key generation...")
    
    try:
        # Test various key generation methods
        user_key = CacheKeyGenerator.user_key(123)
        post_key = CacheKeyGenerator.post_key(456)
        posts_list_key = CacheKeyGenerator.posts_list_key(page=2, per_page=10)
        
        expected_user_key = "user:123"
        expected_post_key = "post:456"
        expected_posts_key = "posts:page:2:per_page:10"
        
        if (user_key == expected_user_key and 
            post_key == expected_post_key and 
            posts_list_key == expected_posts_key):
            print("✓ Cache key generation working correctly")
            return True
        else:
            print("✗ Cache key generation failed")
            print(f"  Expected user key: {expected_user_key}, got: {user_key}")
            print(f"  Expected post key: {expected_post_key}, got: {post_key}")
            print(f"  Expected posts key: {expected_posts_key}, got: {posts_list_key}")
            return False
            
    except Exception as e:
        print(f"✗ Cache key generation failed: {e}")
        return False


def test_cache_operations():
    """Test cache operations with different data types."""
    print("Testing cache operations...")
    
    try:
        # Test string caching
        cache.set("test:string", "test_value", timeout=60)
        
        # Test dict caching
        test_dict = {"name": "John", "age": 30, "posts": [1, 2, 3]}
        cache.set("test:dict", test_dict, timeout=60)
        
        # Test list caching
        test_list = ["item1", "item2", "item3"]
        cache.set("test:list", test_list, timeout=60)
        
        # Retrieve and verify
        string_result = cache.get("test:string")
        dict_result = cache.get("test:dict")
        list_result = cache.get("test:list")
        
        if (string_result == "test_value" and 
            dict_result == test_dict and 
            list_result == test_list):
            print("✓ Cache operations working correctly")
            
            # Clean up
            cache.delete("test:string")
            cache.delete("test:dict")
            cache.delete("test:list")
            return True
        else:
            print("✗ Cache operations failed")
            return False
            
    except Exception as e:
        print(f"✗ Cache operations failed: {e}")
        return False


def test_cache_expiration():
    """Test cache expiration functionality."""
    print("Testing cache expiration...")
    
    try:
        # Set a key with short expiration
        cache.set("test:expiration", "expires_soon", timeout=2)
        
        # Verify it exists
        if cache.get("test:expiration") != "expires_soon":
            print("✗ Cache expiration test failed - key not set")
            return False
        
        # Wait for expiration
        print("  Waiting for cache expiration (3 seconds)...")
        time.sleep(3)
        
        # Verify it's expired
        if cache.get("test:expiration") is None:
            print("✓ Cache expiration working correctly")
            return True
        else:
            print("✗ Cache expiration failed - key still exists")
            return False
            
    except Exception as e:
        print(f"✗ Cache expiration test failed: {e}")
        return False


def test_cache_manager():
    """Test cache manager functionality."""
    print("Testing cache manager...")
    
    try:
        # Set some test data
        cache.set("test:manager:1", "value1", timeout=60)
        cache.set("test:manager:2", "value2", timeout=60)
        
        # Test cache info
        info = CacheManager.get_info()
        if isinstance(info, dict):
            print("✓ Cache manager info retrieval working")
        else:
            print("✗ Cache manager info retrieval failed")
            return False
        
        # Clean up test data
        cache.delete("test:manager:1")
        cache.delete("test:manager:2")
        
        return True
        
    except Exception as e:
        print(f"✗ Cache manager test failed: {e}")
        return False


def main():
    """Run all cache tests."""
    print("Redis Caching Infrastructure Test")
    print("=" * 40)
    
    # Create Flask app for testing
    app = create_app('testing')
    
    with app.app_context():
        tests = [
            test_cache_connection,
            test_cache_key_generation,
            test_cache_operations,
            test_cache_expiration,
            test_cache_manager,
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            print()
        
        print("=" * 40)
        print(f"Tests passed: {passed}/{total}")
        
        if passed == total:
            print("✓ All cache tests passed! Redis caching infrastructure is working correctly.")
            return True
        else:
            print("✗ Some cache tests failed. Please check your Redis configuration.")
            return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)