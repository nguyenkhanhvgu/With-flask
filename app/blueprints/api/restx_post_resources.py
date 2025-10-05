"""
Flask-RESTX Post Resources

This module contains blog post-related API endpoints with
comprehensive documentation using Flask-RESTX decorators.
"""

from flask import request
from flask_restx import Resource
from sqlalchemy import desc, or_
from app.models.blog import Post, Category
from app.models.user import User
from app.extensions import db
from .restx_api import posts_ns
from .models import (
    post_summary_model, post_detail_model, post_create_model, 
    post_update_model, posts_response_model, error_model, success_model
)
from .base import token_required, admin_required


@posts_ns.route('')
class PostListResource(Resource):
    """Posts collection endpoint"""
    
    @posts_ns.doc('get_posts')
    @posts_ns.param('page', 'Page number', type=int, default=1)
    @posts_ns.param('per_page', 'Posts per page', type=int, default=10)
    @posts_ns.param('category', 'Filter by category ID', type=int)
    @posts_ns.param('author', 'Filter by author username', type=str)
    @posts_ns.param('search', 'Search in title and content', type=str)
    @posts_ns.param('sort', 'Sort order', type=str, enum=['newest', 'oldest', 'popular'], default='newest')
    @posts_ns.response(200, 'Posts retrieved successfully', posts_response_model)
    @posts_ns.response(400, 'Invalid parameters', error_model)
    def get(self):
        """
        Get paginated list of blog posts
        
        Retrieves a paginated list of blog posts with optional filtering and sorting.
        Supports search functionality and category/author filtering.
        
        **Query Parameters:**
        - `page`: Page number (default: 1)
        - `per_page`: Number of posts per page (default: 10, max: 100)
        - `category`: Filter by category ID
        - `author`: Filter by author username
        - `search`: Search term for title and content
        - `sort`: Sort order (newest, oldest, popular)
        
        **Example Request:**
        ```
        GET /api/v1/posts?page=1&per_page=5&category=1&sort=popular
        ```
        
        **Example Response:**
        ```json
        {
            "posts": [
                {
                    "id": 1,
                    "title": "Getting Started with Flask",
                    "excerpt": "Learn the basics of Flask...",
                    "author": {
                        "id": 1,
                        "username": "john_doe",
                        "avatar": "/static/uploads/avatars/avatar.jpg"
                    },
                    "category": {
                        "id": 1,
                        "name": "Technology"
                    },
                    "created_at": "2023-12-01T10:30:00Z",
                    "comments_count": 5,
                    "likes_count": 15
                }
            ],
            "pagination": {
                "page": 1,
                "pages": 3,
                "per_page": 5,
                "total": 15,
                "has_next": true,
                "has_prev": false
            }
        }
        ```
        """
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        category_id = request.args.get('category', type=int)
        author_username = request.args.get('author', type=str)
        search_term = request.args.get('search', type=str)
        sort_order = request.args.get('sort', 'newest', type=str)
        
        # Build query
        query = Post.query
        
        # Apply filters
        if category_id:
            query = query.filter(Post.category_id == category_id)
        
        if author_username:
            author = User.query.filter_by(username=author_username).first()
            if author:
                query = query.filter(Post.user_id == author.id)
            else:
                return {'error': 'Bad Request', 'message': 'Author not found'}, 400
        
        if search_term:
            query = query.filter(
                or_(
                    Post.title.contains(search_term),
                    Post.content.contains(search_term)
                )
            )
        
        # Apply sorting
        if sort_order == 'oldest':
            query = query.order_by(Post.created_at.asc())
        elif sort_order == 'popular':
            # Sort by view count or likes (assuming these fields exist)
            query = query.order_by(desc(Post.id))  # Placeholder for popularity metric
        else:  # newest (default)
            query = query.order_by(desc(Post.created_at))
        
        # Paginate
        try:
            posts_pagination = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
        except Exception:
            return {'error': 'Bad Request', 'message': 'Invalid pagination parameters'}, 400
        
        # Serialize posts
        posts_data = []
        for post in posts_pagination.items:
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'excerpt': post.content[:200] + '...' if len(post.content) > 200 else post.content,
                'author': {
                    'id': post.author.id,
                    'username': post.author.username,
                    'avatar': f"/static/uploads/avatars/{post.author.avatar_filename}" if post.author.avatar_filename else None
                },
                'category': {
                    'id': post.category.id,
                    'name': post.category.name
                } if post.category else None,
                'image': f"/static/uploads/posts/{post.image_filename}" if hasattr(post, 'image_filename') and post.image_filename else None,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
                'comments_count': len(post.comments),
                'likes_count': 0,  # Placeholder for likes functionality
                'views_count': 0   # Placeholder for views functionality
            })
        
        return {
            'posts': posts_data,
            'pagination': {
                'page': posts_pagination.page,
                'pages': posts_pagination.pages,
                'per_page': posts_pagination.per_page,
                'total': posts_pagination.total,
                'has_next': posts_pagination.has_next,
                'has_prev': posts_pagination.has_prev
            }
        }, 200
    
    @posts_ns.doc('create_post')
    @posts_ns.doc(security='Bearer')
    @posts_ns.expect(post_create_model, validate=True)
    @posts_ns.response(201, 'Post created successfully', post_detail_model)
    @posts_ns.response(400, 'Validation error', error_model)
    @posts_ns.response(401, 'Authentication required', error_model)
    @token_required
    def post(self):
        """
        Create a new blog post
        
        Creates a new blog post with the provided data. Requires authentication.
        The authenticated user becomes the author of the post.
        
        **Headers Required:**
        ```
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
        Content-Type: application/json
        ```
        
        **Example Request:**
        ```json
        {
            "title": "My New Blog Post",
            "content": "This is the content of my blog post...",
            "category_id": 1,
            "tags": ["flask", "python", "tutorial"]
        }
        ```
        
        **Example Response:**
        ```json
        {
            "id": 15,
            "title": "My New Blog Post",
            "content": "This is the content of my blog post...",
            "author": {
                "id": 1,
                "username": "john_doe"
            },
            "category": {
                "id": 1,
                "name": "Technology"
            },
            "created_at": "2023-12-01T16:30:00Z",
            "updated_at": "2023-12-01T16:30:00Z"
        }
        ```
        """
        data = request.get_json()
        
        # Validate category if provided
        category = None
        if data.get('category_id'):
            category = Category.query.get(data['category_id'])
            if not category:
                return {'error': 'Bad Request', 'message': 'Category not found'}, 400
        
        # Create new post
        post = Post(
            title=data['title'],
            content=data['content'],
            user_id=self.current_user.id,
            category_id=data.get('category_id')
        )
        
        try:
            db.session.add(post)
            db.session.commit()
            
            # Return created post
            return {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author': {
                    'id': post.author.id,
                    'username': post.author.username,
                    'avatar': f"/static/uploads/avatars/{post.author.avatar_filename}" if post.author.avatar_filename else None
                },
                'category': {
                    'id': post.category.id,
                    'name': post.category.name
                } if post.category else None,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
                'comments_count': 0,
                'likes_count': 0,
                'views_count': 0,
                'tags': data.get('tags', [])
            }, 201
            
        except Exception as e:
            db.session.rollback()
            return {'error': 'Internal Server Error', 'message': 'Failed to create post'}, 500


@posts_ns.route('/<int:post_id>')
class PostResource(Resource):
    """Individual post endpoint"""
    
    @posts_ns.doc('get_post')
    @posts_ns.param('post_id', 'Post ID')
    @posts_ns.response(200, 'Post retrieved successfully', post_detail_model)
    @posts_ns.response(404, 'Post not found', error_model)
    def get(self, post_id):
        """
        Get a specific blog post by ID
        
        Retrieves detailed information about a specific blog post including
        full content, author details, category, and comments count.
        
        **Path Parameters:**
        - `post_id`: The unique identifier of the post
        
        **Example Request:**
        ```
        GET /api/v1/posts/15
        ```
        
        **Example Response:**
        ```json
        {
            "id": 15,
            "title": "Getting Started with Flask",
            "content": "Flask is a lightweight WSGI web application framework...",
            "author": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "avatar": "/static/uploads/avatars/avatar.jpg"
            },
            "category": {
                "id": 1,
                "name": "Technology",
                "description": "Posts about technology"
            },
            "created_at": "2023-12-01T10:30:00Z",
            "updated_at": "2023-12-01T15:45:00Z",
            "comments_count": 5,
            "likes_count": 15,
            "views_count": 120
        }
        ```
        """
        post = Post.query.get_or_404(post_id)
        
        return {
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'author': {
                'id': post.author.id,
                'username': post.author.username,
                'email': post.author.email,
                'avatar': f"/static/uploads/avatars/{post.author.avatar_filename}" if post.author.avatar_filename else None,
                'is_admin': post.author.is_admin
            },
            'category': {
                'id': post.category.id,
                'name': post.category.name,
                'description': post.category.description
            } if post.category else None,
            'image': f"/static/uploads/posts/{post.image_filename}" if hasattr(post, 'image_filename') and post.image_filename else None,
            'created_at': post.created_at.isoformat(),
            'updated_at': post.updated_at.isoformat(),
            'comments_count': len(post.comments),
            'likes_count': 0,  # Placeholder
            'views_count': 0,  # Placeholder
            'tags': []  # Placeholder for tags functionality
        }, 200
    
    @posts_ns.doc('update_post')
    @posts_ns.doc(security='Bearer')
    @posts_ns.param('post_id', 'Post ID')
    @posts_ns.expect(post_update_model, validate=True)
    @posts_ns.response(200, 'Post updated successfully', post_detail_model)
    @posts_ns.response(401, 'Authentication required', error_model)
    @posts_ns.response(403, 'Permission denied', error_model)
    @posts_ns.response(404, 'Post not found', error_model)
    @token_required
    def put(self, post_id):
        """
        Update a blog post
        
        Updates an existing blog post. Only the post author or admin can update a post.
        
        **Path Parameters:**
        - `post_id`: The unique identifier of the post
        
        **Headers Required:**
        ```
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
        Content-Type: application/json
        ```
        
        **Example Request:**
        ```json
        {
            "title": "Updated Post Title",
            "content": "Updated content...",
            "category_id": 2
        }
        ```
        """
        post = Post.query.get_or_404(post_id)
        
        # Check permissions
        if post.user_id != self.current_user.id and not self.current_user.is_admin:
            return {'error': 'Forbidden', 'message': 'Permission denied'}, 403
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            post.title = data['title']
        if 'content' in data:
            post.content = data['content']
        if 'category_id' in data:
            if data['category_id']:
                category = Category.query.get(data['category_id'])
                if not category:
                    return {'error': 'Bad Request', 'message': 'Category not found'}, 400
                post.category_id = data['category_id']
            else:
                post.category_id = None
        
        try:
            db.session.commit()
            
            return {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'author': {
                    'id': post.author.id,
                    'username': post.author.username
                },
                'category': {
                    'id': post.category.id,
                    'name': post.category.name
                } if post.category else None,
                'created_at': post.created_at.isoformat(),
                'updated_at': post.updated_at.isoformat(),
                'comments_count': len(post.comments)
            }, 200
            
        except Exception:
            db.session.rollback()
            return {'error': 'Internal Server Error', 'message': 'Failed to update post'}, 500
    
    @posts_ns.doc('delete_post')
    @posts_ns.doc(security='Bearer')
    @posts_ns.param('post_id', 'Post ID')
    @posts_ns.response(200, 'Post deleted successfully', success_model)
    @posts_ns.response(401, 'Authentication required', error_model)
    @posts_ns.response(403, 'Permission denied', error_model)
    @posts_ns.response(404, 'Post not found', error_model)
    @token_required
    def delete(self, post_id):
        """
        Delete a blog post
        
        Deletes an existing blog post. Only the post author or admin can delete a post.
        This action is irreversible.
        
        **Path Parameters:**
        - `post_id`: The unique identifier of the post
        
        **Headers Required:**
        ```
        Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
        ```
        
        **Example Response:**
        ```json
        {
            "success": true,
            "message": "Post deleted successfully"
        }
        ```
        """
        post = Post.query.get_or_404(post_id)
        
        # Check permissions
        if post.user_id != self.current_user.id and not self.current_user.is_admin:
            return {'error': 'Forbidden', 'message': 'Permission denied'}, 403
        
        try:
            db.session.delete(post)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Post deleted successfully'
            }, 200
            
        except Exception:
            db.session.rollback()
            return {'error': 'Internal Server Error', 'message': 'Failed to delete post'}, 500