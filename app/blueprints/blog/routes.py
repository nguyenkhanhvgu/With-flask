"""
Blog Blueprint Routes

This module contains routes for blog functionality including
post viewing, creation, commenting, and category management.
"""

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.blueprints.blog import bp


@bp.route('/')
def index():
    """Display all blog posts"""
    # Import here to avoid circular imports
    from app.models.blog import Post
    from app.extensions import db
    
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    
    if search_query:
        # Search in title and content
        posts = Post.query.filter(
            db.or_(
                Post.title.contains(search_query),
                Post.content.contains(search_query)
            )
        ).order_by(Post.created_at.desc()).paginate(
            page=page, per_page=5, error_out=False
        )
    else:
        posts = Post.query.order_by(Post.created_at.desc()).paginate(
            page=page, per_page=5, error_out=False
        )
    
    return render_template('blog.html', title='Blog', posts=posts, search_query=search_query)


@bp.route('/post/<int:id>', methods=['GET', 'POST'])
def post_detail(id):
    """Display single post with comments and handle new comments"""
    # Import here to avoid circular imports
    from app.models.blog import Post, Comment
    from app.extensions import db, socketio
    import threading
    
    post = Post.query.get_or_404(id)
    
    if request.method == 'POST' and current_user.is_authenticated:
        content = request.form.get('content')
        if content and content.strip():
            # Create new comment
            comment = Comment(
                content=content.strip(),
                post_id=post.id,
                user_id=current_user.id
            )
            db.session.add(comment)
            db.session.commit()
            
            # TODO: Add email notification and WebSocket broadcasting
            # This will be implemented in later tasks
            
            flash('Your comment has been added!', 'success')
            return redirect(url_for('blog.post_detail', id=id))
        else:
            flash('Please enter a comment.', 'error')
    
    comments = Comment.query.filter_by(post_id=id).order_by(Comment.created_at.desc()).all()
    return render_template('post_detail.html', title=post.title, post=post, comments=comments)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new blog post"""
    if request.method == 'POST':
        # Import here to avoid circular imports
        from app.models.blog import Post, Category
        from app.extensions import db
        from app.utils.file_helpers import save_uploaded_file
        
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        image_file = request.files.get('image')
        
        if title and content:
            # Handle image upload
            image_filename = None
            if image_file and image_file.filename:
                image_filename = save_uploaded_file(image_file, 'posts')
                if not image_filename:
                    flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
                    categories = Category.query.all()
                    return render_template('create_post.html', title='Create Post', categories=categories)
            
            # Create new post
            post = Post(
                title=title,
                content=content,
                image_filename=image_filename,
                user_id=current_user.id,
                category_id=category_id if category_id else None
            )
            db.session.add(post)
            db.session.commit()
            
            flash('Post created successfully!', 'success')
            return redirect(url_for('blog.index'))
        else:
            flash('Please fill in all required fields.', 'error')
    
    from app.models.blog import Category
    categories = Category.query.all()
    return render_template('create_post.html', title='Create Post', categories=categories)


@bp.route('/categories')
def categories():
    """Display all categories"""
    from app.models.blog import Category
    categories = Category.query.all()
    return render_template('categories.html', title='Categories', categories=categories)


@bp.route('/category/<int:id>')
def category_posts(id):
    """Display posts in a specific category"""
    from app.models.blog import Category, Post
    
    category = Category.query.get_or_404(id)
    posts = Post.query.filter_by(category_id=id).order_by(Post.created_at.desc()).all()
    return render_template('category_posts.html', title=f'Category: {category.name}', 
                         category=category, posts=posts)