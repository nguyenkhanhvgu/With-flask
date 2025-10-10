"""
Blog Routes

This module contains all blog-related routes including:
- Post listing and detail views
- Post creation and editing
- Comment functionality
- Category browsing
- Search functionality

This demonstrates Flask blueprint route organization and proper
separation of concerns in a modular application structure.
"""

from flask import render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
import threading
from PIL import Image

from app.blueprints.blog import bp
from app.extensions import db, socketio
from app.models.blog import Post, Comment, Category
from app.models.user import User
from app.models.like import PostLike
from app.models.follow import Follow


# Utility functions for file handling
def allowed_file(filename):
    """Check if the file extension is allowed"""
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in [ext[1:] for ext in allowed_extensions]


def save_uploaded_file(file, upload_type='posts'):
    """Save uploaded file with unique name and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_ext = os.path.splitext(secure_filename(file.filename))[1]
        unique_filename = str(uuid.uuid4()) + file_ext
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(current_app.config['UPLOAD_PATH'], upload_type)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save original file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Resize image if it's too large
        try:
            with Image.open(file_path) as img:
                # Resize for posts (max 800px width) or avatars (max 300px)
                max_size = (300, 300) if upload_type == 'avatars' else (800, 600)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(file_path, optimize=True, quality=85)
        except Exception as e:
            print(f"Error resizing image: {e}")
        
        return unique_filename
    return None


def send_comment_notification(post, comment):
    """Send email notification to post author when someone comments"""
    # Import here to avoid circular imports
    from app.utils.email import send_email
    
    if post.author.email and post.author.email != comment.author.email:
        subject = f'New comment on your post: "{post.title}"'
        
        text_body = f'''Hi {post.author.username},

Someone left a comment on your post "{post.title}".

Comment by: {comment.author.username}
Comment: {comment.content[:200]}{'...' if len(comment.content) > 200 else ''}

View the full comment and reply at: {url_for('blog.post_detail', id=post.id, _external=True)}

Best regards,
Flask Blog Team
'''
        
        html_body = f'''
        <h3>New comment on your post!</h3>
        <p>Hi <strong>{post.author.username}</strong>,</p>
        <p>Someone left a comment on your post "<strong>{post.title}</strong>".</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
            <p><strong>Comment by:</strong> {comment.author.username}</p>
            <p><strong>Comment:</strong></p>
            <p style="font-style: italic;">"{comment.content[:200]}{'...' if len(comment.content) > 200 else ''}"</p>
        </div>
        
        <p><a href="{url_for('blog.post_detail', id=post.id, _external=True)}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Comment & Reply</a></p>
        
        <p>Best regards,<br>Flask Blog Team</p>
        '''
        
        send_email(subject, [post.author.email], text_body, html_body)


# Blog Routes
@bp.route('/')
def index():
    """Display all blog posts with pagination and search"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    category_id = request.args.get('category', type=int)
    per_page = 5  # Posts per page
    
    # Import BlogService here to avoid circular imports
    from app.services.blog_service import BlogService
    
    if search_query:
        # Use cached search for search queries
        result = BlogService.search_posts_with_caching(
            query=search_query,
            page=page,
            per_page=per_page
        )
        posts_data = result['posts']
        pagination_data = result['pagination']
        
        # Create a mock pagination object for template compatibility
        class MockPagination:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
                self.items = posts_data
        
        posts = MockPagination(pagination_data)
    else:
        # Use cached posts listing
        result = BlogService.get_posts_with_caching(
            page=page,
            per_page=per_page,
            category_id=category_id
        )
        posts_data = result['posts']
        pagination_data = result['pagination']
        
        # Create a mock pagination object for template compatibility
        class MockPagination:
            def __init__(self, data):
                for key, value in data.items():
                    setattr(self, key, value)
                self.items = posts_data
        
        posts = MockPagination(pagination_data)
    
    # Get categories for filter dropdown (could also be cached)
    categories = Category.query.order_by(Category.name).all()
    
    return render_template('blog/index.html', 
                         title='Blog', 
                         posts=posts, 
                         search_query=search_query,
                         categories=categories,
                         selected_category=category_id)


@bp.route('/search')
def search():
    """Search posts by title and content"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if query:
        posts = Post.query.filter(
            db.or_(
                Post.title.contains(query),
                Post.content.contains(query)
            )
        ).order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    else:
        # Empty result for no query
        posts = Post.query.filter(Post.id == -1).paginate(
            page=1, per_page=per_page, error_out=False
        )
    
    return render_template('blog/search_results.html', 
                         title=f'Search Results for "{query}"', 
                         posts=posts, 
                         query=query)


@bp.route('/post/<int:id>', methods=['GET', 'POST'])
def post_detail(id):
    """Display single post with comments and handle new comments"""
    # Import BlogService here to avoid circular imports
    from app.services.blog_service import BlogService
    
    # Get post with caching
    post = BlogService.get_post_with_caching(id)
    if not post:
        abort(404)
    
    # Increment view count for non-author views (using service method)
    if not current_user.is_authenticated or current_user.id != post.user_id:
        BlogService.increment_post_views(id)
    
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
            
            # Send email notification to post author (in background)
            threading.Thread(
                target=send_comment_notification, 
                args=(post, comment)
            ).start()
            
            # Broadcast new comment via WebSocket
            comment_data = {
                'id': comment.id,
                'content': comment.content,
                'author': {
                    'id': current_user.id,
                    'username': current_user.username,
                    'avatar': f"/static/uploads/avatars/{current_user.avatar_filename}" if current_user.avatar_filename else "/static/uploads/avatars/default-avatar.png"
                },
                'created_at': comment.created_at.strftime('%B %d, %Y at %I:%M %p'),
                'created_at_iso': comment.created_at.isoformat()
            }
            
            # Emit to all connected clients in this post's room
            room = f"post_{id}"
            socketio.emit('comment_added', {
                'comment': comment_data,
                'post_id': id
            }, room=room)
            
            flash('Your comment has been added!', 'success')
            return redirect(url_for('blog.post_detail', id=id))
        else:
            flash('Please enter a comment.', 'error')
    
    # Get comments with caching
    comments_result = BlogService.get_post_comments_with_caching(id, page=1, per_page=50)
    comments = comments_result['comments']
    
    # Get social sharing data
    social_data = post.get_social_share_data()
    
    # Check if current user likes this post
    user_likes_post = post.is_liked_by(current_user) if current_user.is_authenticated else False
    
    # Check if current user follows the post author
    user_follows_author = (current_user.is_following(post.author) 
                          if current_user.is_authenticated and current_user.id != post.user_id 
                          else False)
    
    return render_template('blog/post_detail.html', 
                         title=post.title, 
                         post=post, 
                         comments=comments,
                         social_data=social_data,
                         user_likes_post=user_likes_post,
                         user_follows_author=user_follows_author)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new blog post"""
    if request.method == 'POST':
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
                    return render_template('blog/create_post.html', 
                                         title='Create Post', 
                                         categories=categories)
            
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
    
    categories = Category.query.all()
    return render_template('blog/create_post.html', 
                         title='Create Post', 
                         categories=categories)


@bp.route('/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    """Edit an existing blog post"""
    post = Post.query.get_or_404(id)
    
    # Check if user owns the post or is admin
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You can only edit your own posts.', 'error')
        return redirect(url_for('blog.post_detail', id=id))
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        image_file = request.files.get('image')
        
        if title and content:
            # Handle image upload
            if image_file and image_file.filename:
                image_filename = save_uploaded_file(image_file, 'posts')
                if image_filename:
                    post.image_filename = image_filename
                else:
                    flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
                    categories = Category.query.all()
                    return render_template('blog/edit_post.html', 
                                         title='Edit Post', 
                                         post=post,
                                         categories=categories)
            
            # Update post
            post.title = title
            post.content = content
            post.category_id = category_id if category_id else None
            post.updated_at = datetime.utcnow()
            db.session.commit()
            
            flash('Post updated successfully!', 'success')
            return redirect(url_for('blog.post_detail', id=id))
        else:
            flash('Please fill in all required fields.', 'error')
    
    categories = Category.query.all()
    return render_template('blog/edit_post.html', 
                         title='Edit Post', 
                         post=post,
                         categories=categories)


@bp.route('/post/<int:id>/delete', methods=['POST'])
@login_required
def delete_post(id):
    """Delete a blog post"""
    post = Post.query.get_or_404(id)
    
    # Check if user owns the post or is admin
    if post.user_id != current_user.id and not current_user.is_admin:
        flash('You can only delete your own posts.', 'error')
        return redirect(url_for('blog.post_detail', id=id))
    
    post_title = post.title
    db.session.delete(post)
    db.session.commit()
    
    flash(f'Post "{post_title}" has been deleted.', 'success')
    return redirect(url_for('blog.index'))


@bp.route('/categories')
def categories():
    """Display all categories with post counts"""
    categories = Category.query.all()
    
    # Add post count to each category
    for category in categories:
        category.post_count = Post.query.filter_by(category_id=category.id).count()
    
    return render_template('blog/categories.html', 
                         title='Categories', 
                         categories=categories)


@bp.route('/category/<int:id>')
def category_posts(id):
    """Display posts in a specific category with pagination"""
    category = Category.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = 5
    
    posts = Post.query.filter_by(category_id=id).order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('blog/category_posts.html', 
                         title=f'Category: {category.name}', 
                         category=category, 
                         posts=posts)


@bp.route('/comment/<int:id>/delete', methods=['POST'])
@login_required
def delete_comment(id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(id)
    post_id = comment.post_id
    
    # Check if user owns the comment, owns the post, or is admin
    if (comment.user_id != current_user.id and 
        comment.post.user_id != current_user.id and 
        not current_user.is_admin):
        flash('You can only delete your own comments.', 'error')
        return redirect(url_for('blog.post_detail', id=post_id))
    
    db.session.delete(comment)
    db.session.commit()
    
    flash('Comment has been deleted.', 'success')
    return redirect(url_for('blog.post_detail', id=post_id))


# Social Features Routes

@bp.route('/post/<int:id>/like', methods=['POST'])
@login_required
def like_post(id):
    """Like or unlike a post via AJAX"""
    from flask import jsonify
    
    post = Post.query.get_or_404(id)
    
    # Check if already liked
    if post.is_liked_by(current_user):
        # Unlike the post
        success = PostLike.unlike_post(current_user, post)
        if success:
            db.session.commit()
            return jsonify({
                'success': True,
                'liked': False,
                'like_count': post.like_count,
                'message': 'Post unliked successfully'
            })
    else:
        # Like the post
        like = PostLike.like_post(current_user, post)
        if like:
            db.session.commit()
            return jsonify({
                'success': True,
                'liked': True,
                'like_count': post.like_count,
                'message': 'Post liked successfully'
            })
    
    return jsonify({
        'success': False,
        'message': 'Unable to process like/unlike'
    }), 400


@bp.route('/user/<username>/follow', methods=['POST'])
@login_required
def follow_user(username):
    """Follow or unfollow a user via AJAX"""
    from flask import jsonify
    
    user = User.query.filter_by(username=username).first_or_404()
    
    # Prevent self-following
    if user.id == current_user.id:
        return jsonify({
            'success': False,
            'message': 'You cannot follow yourself'
        }), 400
    
    # Check if already following
    if current_user.is_following(user):
        # Unfollow the user
        success = current_user.unfollow(user)
        if success:
            return jsonify({
                'success': True,
                'following': False,
                'follower_count': user.follower_count,
                'message': f'You are no longer following {user.username}'
            })
    else:
        # Follow the user
        success = current_user.follow(user)
        if success:
            db.session.commit()
            return jsonify({
                'success': True,
                'following': True,
                'follower_count': user.follower_count,
                'message': f'You are now following {user.username}'
            })
    
    return jsonify({
        'success': False,
        'message': 'Unable to process follow/unfollow'
    }), 400


@bp.route('/feed')
@login_required
def feed():
    """Display personalized feed based on followed users"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get posts from followed users
    followed_posts = current_user.get_followed_posts()
    
    # If user doesn't follow anyone, show popular posts
    if followed_posts.count() == 0:
        # For popular posts, we need to create a proper query for pagination
        posts_query = Post.query.order_by(Post.like_count.desc())
        feed_type = 'popular'
        message = "You're not following anyone yet. Here are some popular posts to get you started!"
    else:
        posts_query = followed_posts
        feed_type = 'personalized'
        message = None
    
    # Apply pagination
    posts = posts_query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get follow suggestions
    suggestions = Follow.get_follow_suggestions(current_user, limit=5).all()
    
    return render_template('blog/feed.html',
                         title='Your Feed',
                         posts=posts,
                         feed_type=feed_type,
                         message=message,
                         suggestions=suggestions)


@bp.route('/trending')
def trending_posts():
    """Display trending posts with caching"""
    page = request.args.get('page', 1, type=int)
    days = request.args.get('days', 7, type=int)
    per_page = 10
    
    # Validate days parameter
    if days not in [1, 7, 30]:
        days = 7
    
    # Import BlogService here to avoid circular imports
    from app.services.blog_service import BlogService
    
    # Use cached trending posts
    trending_posts_list = BlogService.get_trending_posts(days=days, limit=per_page * 5)
    
    # Manual pagination for cached results
    total = len(trending_posts_list)
    start = (page - 1) * per_page
    end = start + per_page
    posts_for_page = trending_posts_list[start:end]
    
    # Create a mock pagination object for template compatibility
    class MockPagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None
    
    posts = MockPagination(posts_for_page, page, per_page, total)
    
    return render_template('blog/trending.html',
                         title=f'Trending Posts (Last {days} days)',
                         posts=posts,
                         days=days)


@bp.route('/post/<slug>')
def post_by_slug(slug):
    """Display post by slug for SEO-friendly URLs"""
    post = Post.query.filter_by(slug=slug).first_or_404()
    
    # Increment view count
    post.view_count += 1
    db.session.commit()
    
    # Redirect to the main post detail view with the ID
    return redirect(url_for('blog.post_detail', id=post.id))