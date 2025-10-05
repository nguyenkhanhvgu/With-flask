# Redis Caching Infrastructure Guide

This guide explains how to use the Redis caching infrastructure that has been set up for the Flask blog application.

## Overview

The caching system provides:
- Redis-based caching with Flask-Caching
- Environment-specific cache configurations
- Cache key generation utilities
- Cache invalidation helpers
- Caching middleware and decorators
- CLI commands for cache management

## Prerequisites

### Install Redis

**On Windows:**
1. Download Redis from https://github.com/microsoftarchive/redis/releases
2. Install and start Redis server
3. Default configuration: localhost:6379

**On macOS:**
```bash
brew install redis
brew services start redis
```

**On Linux:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

### Install Python Dependencies

The required dependencies are already added to `requirements.txt`:
```
Flask-Caching==2.1.0
redis==5.0.1
```

Install them with:
```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Add Redis configuration to your `.env` file:
```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
```

### Configuration Classes

The cache is configured differently for each environment:

- **Development**: Uses Redis with 5-minute default timeout
- **Testing**: Uses SimpleCache (in-memory) for faster tests
- **Production**: Uses Redis with 10-minute default timeout

## Usage Examples

### Basic Caching

```python
from app.extensions import cache

# Set a value
cache.set('my_key', 'my_value', timeout=300)

# Get a value
value = cache.get('my_key')

# Delete a value
cache.delete('my_key')
```

### Using Cache Key Generators

```python
from app.utils.cache_utils import CacheKeyGenerator

# Generate consistent cache keys
user_key = CacheKeyGenerator.user_key(123)  # "user:123"
post_key = CacheKeyGenerator.post_key(456)  # "post:456"
posts_list_key = CacheKeyGenerator.posts_list_key(page=2, per_page=10)
```

### Caching Decorators

#### Cache Function Results

```python
from app.utils.cache_utils import cached_function

@cached_function(timeout=600, key_prefix='expensive_operation')
def get_trending_posts():
    # Expensive database query
    return Post.query.order_by(Post.view_count.desc()).limit(10).all()
```

#### Cache View Responses

```python
from app.middleware.caching import cache_response

@cache_response(timeout=300)
def index():
    posts = get_recent_posts()
    return render_template('index.html', posts=posts)
```

#### Cache Pages with Custom Keys

```python
from app.middleware.caching import cache_page

@cache_page(timeout=600, key_prefix='user_profile')
def profile(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('profile.html', user=user)
```

### Cache Invalidation

```python
from app.utils.cache_utils import CacheInvalidator

# Invalidate user-related cache
CacheInvalidator.invalidate_user_cache(user_id=123)

# Invalidate post-related cache
CacheInvalidator.invalidate_post_cache(post_id=456, user_id=123)

# Invalidate all posts lists
CacheInvalidator.invalidate_posts_lists()
```

### Cache Management

```python
from app.middleware.caching import CacheManager

# Clear all cache
CacheManager.clear_all()

# Get cache statistics
stats = CacheManager.get_info()
print(f"Hit rate: {stats['hit_rate']}%")

# Warm cache with popular data
CacheManager.warm_cache()
```

## CLI Commands

The application provides CLI commands for cache management:

```bash
# Clear all cache entries
flask clear-cache

# Warm up cache with popular data
flask warm-cache

# Display cache statistics
flask cache-info
```

## Testing the Setup

Run the cache test script to verify everything is working:

```bash
python test_cache_setup.py
```

This will test:
- Redis connection
- Cache key generation
- Basic cache operations
- Cache expiration
- Cache manager functionality

## Best Practices

### 1. Cache Key Naming

Use consistent, hierarchical key naming:
```python
# Good
"user:123:posts:page:1"
"category:5:posts:recent"

# Avoid
"user123posts"
"cat5_recent"
```

### 2. Cache Timeouts

Choose appropriate timeouts based on data volatility:
- Static content: 1 hour - 1 day
- User profiles: 15-30 minutes
- Post lists: 5-15 minutes
- Real-time data: 1-5 minutes

### 3. Cache Invalidation

Invalidate cache when data changes:
```python
@invalidate_cache_on_change(['posts:*', 'trending:*'])
def create_post(title, content):
    # Create post logic
    pass
```

### 4. Error Handling

Always handle cache failures gracefully:
```python
def get_posts():
    cache_key = CacheKeyGenerator.posts_list_key()
    posts = cache.get(cache_key)
    
    if posts is None:
        # Cache miss or error - fetch from database
        posts = Post.query.all()
        try:
            cache.set(cache_key, posts, timeout=300)
        except Exception as e:
            # Log error but don't fail the request
            current_app.logger.warning(f"Cache set failed: {e}")
    
    return posts
```

## Monitoring

### Cache Statistics

Monitor cache performance:
```python
stats = CacheManager.get_info()
print(f"Hit rate: {stats['hit_rate']}%")
print(f"Memory usage: {stats['used_memory']}")
```

### Performance Headers

The caching middleware adds performance headers:
- `X-Response-Time`: Request processing time

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   - Check if Redis server is running
   - Verify connection settings in `.env`
   - Check firewall settings

2. **Cache Not Working in Tests**
   - Testing config uses SimpleCache by default
   - This is intentional for faster, isolated tests

3. **High Memory Usage**
   - Monitor cache size with `flask cache-info`
   - Adjust timeouts to reduce memory usage
   - Consider cache size limits in production

4. **Cache Invalidation Issues**
   - Use consistent key patterns
   - Test invalidation logic thoroughly
   - Consider using cache tags for complex invalidation

### Debug Mode

Enable cache debugging in development:
```python
# In config.py
CACHE_OPTIONS = {
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': 0,
}

# Enable Redis command logging
import logging
logging.getLogger('redis').setLevel(logging.DEBUG)
```

## Production Considerations

1. **Redis Configuration**
   - Use Redis persistence (RDB/AOF)
   - Configure memory limits
   - Set up Redis monitoring

2. **Security**
   - Use Redis AUTH if exposed
   - Configure firewall rules
   - Use SSL/TLS for remote Redis

3. **High Availability**
   - Consider Redis Sentinel or Cluster
   - Implement cache fallback strategies
   - Monitor cache health

4. **Performance**
   - Use Redis pipelining for bulk operations
   - Monitor cache hit rates
   - Optimize cache key patterns