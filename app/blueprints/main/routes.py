"""
Main Blueprint Routes

This module contains routes for general application functionality
that doesn't belong to specific feature areas.
"""

from flask import render_template, request, flash, redirect, url_for
from app.blueprints.main import bp


@bp.route('/')
def home():
    """Render the home page with recent posts"""
    # Import here to avoid circular imports
    from app.models.blog import Post
    
    # Get recent posts from database
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return render_template('index.html', title='Flask Learning App', posts=recent_posts)


@bp.route('/about')
def about():
    """Render the about page"""
    return render_template('about.html', title='About - Flask Learning App')


@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Handle contact form"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Simple form validation
        if name and email and message:
            flash(f'Thank you {name}! Your message has been received.', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Please fill in all fields.', 'error')
    
    return render_template('contact.html', title='Contact - Flask Learning App')