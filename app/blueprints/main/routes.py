"""
Main Blueprint Routes

This module contains routes for general application functionality
that doesn't belong to specific feature areas.
"""

from flask import render_template, request, flash, redirect, url_for, jsonify
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


@bp.route('/users')
def users():
    """Display all users"""
    # Import here to avoid circular imports
    from app.models.user import User
    
    users = User.query.all()
    return render_template('users.html', title='Users', users=users)


@bp.route('/user/<username>')
def user_profile(username):
    """Display user profile with their posts"""
    # Import here to avoid circular imports
    from app.models.user import User
    from app.models.blog import Post
    
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template('user_profile.html', title=f'{username} - Profile', 
                         user=user, posts=posts)


@bp.route('/health')
def health_check():
    """Health check endpoint for Docker containers and load balancers"""
    try:
        # Import here to avoid circular imports
        from app.extensions import db, cache
        
        # Check database connection
        db.session.execute('SELECT 1')
        db_status = 'healthy'
        
        # Check cache connection (Redis)
        cache_status = 'healthy'
        try:
            cache.get('health_check')
        except Exception:
            cache_status = 'unhealthy'
        
        # Overall health status
        status = 'healthy' if db_status == 'healthy' and cache_status == 'healthy' else 'unhealthy'
        
        response_data = {
            'status': status,
            'timestamp': '2024-01-01T00:00:00Z',  # Would use datetime.utcnow() in real implementation
            'services': {
                'database': db_status,
                'cache': cache_status
            },
            'version': '1.0.0'
        }
        
        status_code = 200 if status == 'healthy' else 503
        return jsonify(response_data), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': '2024-01-01T00:00:00Z',
            'error': str(e),
            'version': '1.0.0'
        }), 503