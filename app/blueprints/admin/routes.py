"""
Admin Blueprint Routes

This module contains routes for administrative functionality
including user management, content moderation, and analytics.
"""

from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.blueprints.admin import bp
from app.utils.decorators import admin_required


@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard with site statistics"""
    # Import here to avoid circular imports
    from app.models.user import User
    from app.models.blog import Post, Comment, Category
    
    # Get statistics
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_comments = Comment.query.count()
    total_categories = Category.query.count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         title='Admin Dashboard',
                         total_users=total_users,
                         total_posts=total_posts,
                         total_comments=total_comments,
                         total_categories=total_categories,
                         recent_users=recent_users,
                         recent_posts=recent_posts,
                         recent_comments=recent_comments)


@bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users"""
    from app.models.user import User
    
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', title='Manage Users', users=users)


@bp.route('/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_user_admin(user_id):
    """Toggle admin status for a user"""
    from app.models.user import User
    from app.extensions import db
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'error')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        status = 'promoted to admin' if user.is_admin else 'removed from admin'
        flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Toggle active status for a user"""
    from app.models.user import User
    from app.extensions import db
    
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@bp.route('/posts')
@login_required
@admin_required
def posts():
    """Manage posts"""
    from app.models.blog import Post
    
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/posts.html', title='Manage Posts', posts=posts)


@bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_post(post_id):
    """Delete a post"""
    from app.models.blog import Post
    from app.extensions import db
    
    post = Post.query.get_or_404(post_id)
    post_title = post.title
    db.session.delete(post)
    db.session.commit()
    flash(f'Post "{post_title}" has been deleted.', 'success')
    return redirect(url_for('admin.posts'))


@bp.route('/comments')
@login_required
@admin_required
def comments():
    """Manage comments"""
    from app.models.blog import Comment
    
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    return render_template('admin/comments.html', title='Manage Comments', comments=comments)


@bp.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_comment(comment_id):
    """Delete a comment"""
    from app.models.blog import Comment
    from app.extensions import db
    
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment has been deleted.', 'success')
    return redirect(url_for('admin.comments'))


@bp.route('/categories')
@login_required
@admin_required
def categories():
    """Manage categories"""
    from app.models.blog import Category
    
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', title='Manage Categories', categories=categories)


@bp.route('/categories/create', methods=['POST'])
@login_required
@admin_required
def create_category():
    """Create a new category"""
    from app.models.blog import Category
    from app.extensions import db
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if name:
        # Check if category already exists
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash(f'Category "{name}" already exists.', 'error')
        else:
            category = Category(name=name, description=description)
            db.session.add(category)
            db.session.commit()
            flash(f'Category "{name}" has been created.', 'success')
    else:
        flash('Category name is required.', 'error')
    
    return redirect(url_for('admin.categories'))


@bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    """Delete a category"""
    from app.models.blog import Category
    from app.extensions import db
    
    category = Category.query.get_or_404(category_id)
    category_name = category.name
    
    # Check if category has posts
    if category.posts:
        flash(f'Cannot delete category "{category_name}" because it contains posts.', 'error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category_name}" has been deleted.', 'success')
    
    return redirect(url_for('admin.categories'))