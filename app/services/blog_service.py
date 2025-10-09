"""
Blog Service

This module contains the BlogService class that encapsulates all blog-related
business logic. It demonstrates the service layer pattern and implements
caching for expensive operations like trending posts, user profiles,
and frequently accessed content.
"""

from datetime import datetime, timedelta
from flask import current_app
from sqlalchemy import func, desc, and_
from app.extensions import db, cache
from app.models.blog import Post, Comment, Category
from app.models.user import User
from app.utils.cache_utils import CacheKeyGenerator, CacheInvalidator, cached_function
from app.middleware.caching import CacheManager


class BlogService:
    """
    Service class for handling blog operations with caching.
    
    This class demonstrates:
    - Service layer pattern for business logic separation
    - Caching strategies for expensive database operations
    - Cache invalidation patterns
    - Performance optimization techniques
    """
    
    @staticmethod
    @cached_function(timeout=600, key_prefix='trending_posts')
    def get_trending_posts(days=7, limit=10):
        """
        Get trending posts based on likes, comments, and views.
        
        Args:
            days (int): Number of days to look back for trending calculation
            limit (int): Maximum number of posts to return
            
        Returns:
            list: List of trending Post objects
            
        This method demonstrates caching of expensive analytical queries.
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Complex query to calculate trending score
            # Score = (likes * 3) + (comments * 2) + (views * 1)
            trending_posts = db.session.query(
                Post,
                (
                    (Post.like_count * 3) + 
                    (func.count(Comment.id) * 2) + 
                    (Post.view_count * 1)
                ).label('trending_score')
            ).outerjoin(
                Comment, Comment.post_id == Post.id
            ).filter(
                Post.created_at >= cutoff_date
            ).group_by(
                Post.id
            ).order_by(
                desc('trending_score')
            ).limit(limit).all()
            
            # Extract just the Post objects
            posts = [post for post, score in trending_posts]
            
            current_app.logger.info(f"Retrieved {len(posts)} trending posts")
            return posts
            
        except Exception as e:
            current_app.logger.error(f"Error getting trending posts: {e}")
            return []
    
    @staticmethod
    @cached_function(timeout=300, key_prefix='popular_posts')
    def get_popular_posts(limit=10):
        """
        Get most popular posts by like count.
        
        Args:
            limit (int): Maximum number of posts to return
            
        Returns:
            list: List of popular Post objects
        """
        try:
            posts = Post.query.order_by(
                desc(Post.like_count)
            ).limit(limit).all()
            
            current_app.logger.info(f"Retrieved {len(posts)} popular posts")
            return posts
            
        except Exception as e:
            current_app.logger.error(f"Error getting popular posts: {e}")
            return []
    
    @staticmethod
    def get_posts_with_caching(page=1, per_page=5, category_id=None, user_id=None):
        """
        Get paginated posts with caching.
        
        Args:
            page (int): Page number
            per_page (int): Posts per page
            category_id (int, optional): Filter by category
            user_id (int, optional): Filter by user
            
        Returns:
            dict: Pagination object and posts data
        """
        try:
            # Generate cache key
            cache_key = CacheKeyGenerator.posts_list_key(
                page=page, 
                per_page=per_page, 
                category_id=category_id, 
                user_id=user_id
            )
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result:
                current_app.logger.debug(f"Cache hit for posts list: {cache_key}")
                return cached_result
            
            # Build query
            query = Post.query
            
            if category_id:
                query = query.filter(Post.category_id == category_id)
            
            if user_id:
                query = query.filter(Post.user_id == user_id)
            
            # Execute paginated query
            pagination = query.order_by(
                desc(Post.created_at)
            ).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            result = {
                'posts': pagination.items,
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev,
                    'next_num': pagination.next_num,
                    'prev_num': pagination.prev_num
                }
            }
            
            # Cache the result for 5 minutes
            cache.set(cache_key, result, timeout=300)
            
            current_app.logger.info(f"Retrieved {len(pagination.items)} posts for page {page}")
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error getting posts: {e}")
            return {
                'posts': [],
                'pagination': {
                    'page': 1, 'pages': 0, 'per_page': per_page,
                    'total': 0, 'has_next': False, 'has_prev': False,
                    'next_num': None, 'prev_num': None
                }
            }
    
    @staticmethod
    def get_post_with_caching(post_id):
        """
        Get a single post with caching.
        
        Args:
            post_id (int): Post ID
            
        Returns:
            Post or None: Post object if found
        """
        try:
            cache_key = CacheKeyGenerator.post_key(post_id)
            
            # Try to get from cache
            cached_post = cache.get(cache_key)
            if cached_post:
                current_app.logger.debug(f"Cache hit for post: {cache_key}")
                return cached_post
            
            # Get from database
            post = Post.query.get(post_id)
            
            if post:
                # Cache for 10 minutes
                cache.set(cache_key, post, timeout=600)
                current_app.logger.debug(f"Cached post: {cache_key}")
            
            return post
            
        except Exception as e:
            current_app.logger.error(f"Error getting post {post_id}: {e}")
            return None
    
    @staticmethod
    def get_user_profile_with_caching(user_id):
        """
        Get user profile data with caching.
        
        Args:
            user_id (int): User ID
            
        Returns:
            dict: User profile data including stats
        """
        try:
            cache_key = CacheKeyGenerator.user_profile_key(user_id)
            
            # Try to get from cache
            cached_profile = cache.get(cache_key)
            if cached_profile:
                current_app.logger.debug(f"Cache hit for user profile: {cache_key}")
                return cached_profile
            
            # Get user from database
            user = User.query.get(user_id)
            if not user:
                return None
            
            # Calculate user statistics
            post_count = Post.query.filter_by(user_id=user_id).count()
            comment_count = Comment.query.filter_by(user_id=user_id).count()
            
            # Get total likes on user's posts
            total_likes = db.session.query(
                func.sum(Post.like_count)
            ).filter(Post.user_id == user_id).scalar() or 0
            
            # Get recent posts
            recent_posts = Post.query.filter_by(
                user_id=user_id
            ).order_by(
                desc(Post.created_at)
            ).limit(5).all()
            
            profile_data = {
                'user': user,
                'stats': {
                    'post_count': post_count,
                    'comment_count': comment_count,
                    'total_likes': total_likes,
                    'follower_count': user.follower_count,
                    'following_count': user.following_count
                },
                'recent_posts': recent_posts
            }
            
            # Cache for 15 minutes
            cache.set(cache_key, profile_data, timeout=900)
            
            current_app.logger.info(f"Generated profile data for user {user_id}")
            return profile_data
            
        except Exception as e:
            current_app.logger.error(f"Error getting user profile {user_id}: {e}")
            return None
    
    @staticmethod
    def get_post_comments_with_caching(post_id, page=1, per_page=10):
        """
        Get post comments with caching.
        
        Args:
            post_id (int): Post ID
            page (int): Page number
            per_page (int): Comments per page
            
        Returns:
            dict: Comments and pagination data
        """
        try:
            cache_key = CacheKeyGenerator.post_comments_key(
                post_id=post_id, 
                page=page, 
                per_page=per_page
            )
            
            # Try to get from cache
            cached_comments = cache.get(cache_key)
            if cached_comments:
                current_app.logger.debug(f"Cache hit for post comments: {cache_key}")
                return cached_comments
            
            # Get comments from database
            pagination = Comment.query.filter_by(
                post_id=post_id
            ).order_by(
                desc(Comment.created_at)
            ).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            result = {
                'comments': pagination.items,
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev,
                    'next_num': pagination.next_num,
                    'prev_num': pagination.prev_num
                }
            }
            
            # Cache for 5 minutes
            cache.set(cache_key, result, timeout=300)
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error getting comments for post {post_id}: {e}")
            return {
                'comments': [],
                'pagination': {
                    'page': 1, 'pages': 0, 'per_page': per_page,
                    'total': 0, 'has_next': False, 'has_prev': False,
                    'next_num': None, 'prev_num': None
                }
            }
    
    @staticmethod
    def create_post(user_id, title, content, category_id=None, image_filename=None):
        """
        Create a new post and invalidate related caches.
        
        Args:
            user_id (int): Author's user ID
            title (str): Post title
            content (str): Post content
            category_id (int, optional): Category ID
            image_filename (str, optional): Image filename
            
        Returns:
            dict: Result with success status and post data
        """
        try:
            # Create new post
            post = Post(
                title=title,
                content=content,
                user_id=user_id,
                category_id=category_id,
                image_filename=image_filename
            )
            
            db.session.add(post)
            db.session.commit()
            
            # Invalidate related caches
            CacheInvalidator.invalidate_post_cache(
                post.id, 
                user_id=user_id, 
                category_id=category_id
            )
            CacheInvalidator.invalidate_posts_lists()
            CacheInvalidator.invalidate_user_cache(user_id)
            
            current_app.logger.info(f"Created post {post.id}: {title}")
            
            return {
                'success': True,
                'post': post,
                'message': 'Post created successfully!'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating post: {e}")
            return {
                'success': False,
                'error': 'post_creation_failed',
                'message': 'Failed to create post. Please try again.'
            }
    
    @staticmethod
    def update_post(post_id, title=None, content=None, category_id=None, image_filename=None):
        """
        Update a post and invalidate related caches.
        
        Args:
            post_id (int): Post ID to update
            title (str, optional): New title
            content (str, optional): New content
            category_id (int, optional): New category ID
            image_filename (str, optional): New image filename
            
        Returns:
            dict: Result with success status and post data
        """
        try:
            post = Post.query.get(post_id)
            if not post:
                return {
                    'success': False,
                    'error': 'post_not_found',
                    'message': 'Post not found.'
                }
            
            old_category_id = post.category_id
            
            # Update fields if provided
            if title is not None:
                post.title = title
            if content is not None:
                post.content = content
            if category_id is not None:
                post.category_id = category_id
            if image_filename is not None:
                post.image_filename = image_filename
            
            post.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Invalidate related caches
            CacheInvalidator.invalidate_post_cache(
                post_id, 
                user_id=post.user_id, 
                category_id=post.category_id
            )
            
            # Also invalidate old category cache if category changed
            if old_category_id and old_category_id != post.category_id:
                CacheInvalidator.invalidate_category_cache(old_category_id)
            
            CacheInvalidator.invalidate_posts_lists()
            
            current_app.logger.info(f"Updated post {post_id}")
            
            return {
                'success': True,
                'post': post,
                'message': 'Post updated successfully!'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating post {post_id}: {e}")
            return {
                'success': False,
                'error': 'post_update_failed',
                'message': 'Failed to update post. Please try again.'
            }
    
    @staticmethod
    def delete_post(post_id):
        """
        Delete a post and invalidate related caches.
        
        Args:
            post_id (int): Post ID to delete
            
        Returns:
            dict: Result with success status
        """
        try:
            post = Post.query.get(post_id)
            if not post:
                return {
                    'success': False,
                    'error': 'post_not_found',
                    'message': 'Post not found.'
                }
            
            user_id = post.user_id
            category_id = post.category_id
            
            db.session.delete(post)
            db.session.commit()
            
            # Invalidate related caches
            CacheInvalidator.invalidate_post_cache(
                post_id, 
                user_id=user_id, 
                category_id=category_id
            )
            CacheInvalidator.invalidate_posts_lists()
            CacheInvalidator.invalidate_user_cache(user_id)
            
            current_app.logger.info(f"Deleted post {post_id}")
            
            return {
                'success': True,
                'message': 'Post deleted successfully!'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting post {post_id}: {e}")
            return {
                'success': False,
                'error': 'post_deletion_failed',
                'message': 'Failed to delete post. Please try again.'
            }
    
    @staticmethod
    def increment_post_views(post_id):
        """
        Increment post view count with caching considerations.
        
        Args:
            post_id (int): Post ID
            
        Returns:
            bool: Success status
        """
        try:
            # Use raw SQL for better performance
            db.session.execute(
                "UPDATE post SET view_count = view_count + 1 WHERE id = :post_id",
                {'post_id': post_id}
            )
            db.session.commit()
            
            # Invalidate post cache to reflect new view count
            cache.delete(CacheKeyGenerator.post_key(post_id))
            
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error incrementing views for post {post_id}: {e}")
            return False
    
    @staticmethod
    def search_posts_with_caching(query, page=1, per_page=5):
        """
        Search posts with caching.
        
        Args:
            query (str): Search query
            page (int): Page number
            per_page (int): Results per page
            
        Returns:
            dict: Search results and pagination data
        """
        try:
            cache_key = CacheKeyGenerator.search_results_key(
                query=query, 
                page=page, 
                per_page=per_page
            )
            
            # Try to get from cache
            cached_results = cache.get(cache_key)
            if cached_results:
                current_app.logger.debug(f"Cache hit for search: {cache_key}")
                return cached_results
            
            # Perform search
            search_pattern = f"%{query}%"
            pagination = Post.query.filter(
                db.or_(
                    Post.title.ilike(search_pattern),
                    Post.content.ilike(search_pattern)
                )
            ).order_by(
                desc(Post.created_at)
            ).paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            result = {
                'posts': pagination.items,
                'query': query,
                'pagination': {
                    'page': pagination.page,
                    'pages': pagination.pages,
                    'per_page': pagination.per_page,
                    'total': pagination.total,
                    'has_next': pagination.has_next,
                    'has_prev': pagination.has_prev,
                    'next_num': pagination.next_num,
                    'prev_num': pagination.prev_num
                }
            }
            
            # Cache search results for 10 minutes
            cache.set(cache_key, result, timeout=600)
            
            current_app.logger.info(f"Search for '{query}' returned {len(pagination.items)} results")
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error searching posts: {e}")
            return {
                'posts': [],
                'query': query,
                'pagination': {
                    'page': 1, 'pages': 0, 'per_page': per_page,
                    'total': 0, 'has_next': False, 'has_prev': False,
                    'next_num': None, 'prev_num': None
                }
            }
    
    @staticmethod
    def warm_popular_content():
        """
        Warm cache with popular content.
        
        This method pre-loads frequently accessed content into the cache
        to improve performance for common requests.
        """
        try:
            current_app.logger.info("Starting cache warming for popular content")
            
            # Warm trending posts
            BlogService.get_trending_posts(days=7, limit=10)
            BlogService.get_trending_posts(days=30, limit=10)
            
            # Warm popular posts
            BlogService.get_popular_posts(limit=10)
            
            # Warm recent posts for homepage
            BlogService.get_posts_with_caching(page=1, per_page=5)
            
            # Warm user profiles for active users
            active_users = User.query.filter_by(is_active=True).limit(10).all()
            for user in active_users:
                BlogService.get_user_profile_with_caching(user.id)
            
            # Warm recent posts by category
            categories = Category.query.limit(5).all()
            for category in categories:
                BlogService.get_posts_with_caching(
                    page=1, 
                    per_page=5, 
                    category_id=category.id
                )
            
            current_app.logger.info("Cache warming completed successfully")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error warming cache: {e}")
            return False