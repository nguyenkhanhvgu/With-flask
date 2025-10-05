"""
API Blueprint Routes

This module contains REST API routes for external access
to the blog application data and functionality.
"""

from flask import jsonify, request
from app.blueprints.api import bp


@bp.route('/posts', methods=['GET'])
def get_posts():
    """Get all posts via API"""
    # Import here to avoid circular imports
    from app.models.blog import Post
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'posts': [{
            'id': post.id,
            'title': post.title,
            'content': post.content,
            'created_at': post.created_at.isoformat(),
            'author': post.author.username,
            'category': post.category.name if post.category else None
        } for post in posts.items],
        'pagination': {
            'page': posts.page,
            'pages': posts.pages,
            'per_page': posts.per_page,
            'total': posts.total
        }
    })


@bp.route('/posts/<int:id>', methods=['GET'])
def get_post(id):
    """Get a single post via API"""
    from app.models.blog import Post
    
    post = Post.query.get_or_404(id)
    
    return jsonify({
        'id': post.id,
        'title': post.title,
        'content': post.content,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat(),
        'author': {
            'id': post.author.id,
            'username': post.author.username
        },
        'category': {
            'id': post.category.id,
            'name': post.category.name
        } if post.category else None,
        'comments': [{
            'id': comment.id,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'author': comment.author.username
        } for comment in post.comments]
    })


@bp.route('/users', methods=['GET'])
def get_users():
    """Get all users via API"""
    from app.models.user import User
    
    users = User.query.all()
    
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'created_at': user.created_at.isoformat(),
            'is_admin': user.is_admin,
            'is_active': user.is_active
        } for user in users]
    })


@bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories via API"""
    from app.models.blog import Category
    
    categories = Category.query.all()
    
    return jsonify({
        'categories': [{
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'post_count': len(category.posts)
        } for category in categories]
    })