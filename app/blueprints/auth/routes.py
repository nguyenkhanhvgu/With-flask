"""
Authentication Blueprint Routes

This module contains routes for user authentication functionality
including registration, login, logout, and profile management.
"""

from flask import render_template, request, flash, redirect, url_for, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import timedelta
from app.blueprints.auth import bp


@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        # Import here to avoid circular imports
        from app.models.user import User
        from app.extensions import db
        
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('Please fill in all fields.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
        else:
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('register.html', title='Register')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    if request.method == 'POST':
        # Import here to avoid circular imports
        from app.models.user import User
        
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        if not username or not password:
            flash('Please provide both username and password.', 'error')
        else:
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                # Make session permanent for persistent login
                session.permanent = True
                login_user(user, remember=remember, duration=timedelta(days=7))
                
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('main.home'))
            else:
                flash('Invalid username or password.', 'error')
    
    return render_template('login.html', title='Login')


@bp.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('main.home'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page with avatar upload"""
    if request.method == 'POST':
        # Import here to avoid circular imports
        from app.extensions import db
        from app.utils.file_helpers import save_uploaded_file
        
        avatar_file = request.files.get('avatar')
        
        if avatar_file and avatar_file.filename:
            # Save new avatar
            avatar_filename = save_uploaded_file(avatar_file, 'avatars')
            if avatar_filename:
                # Update user's avatar
                current_user.avatar_filename = avatar_filename
                db.session.commit()
                flash('Avatar updated successfully!', 'success')
            else:
                flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
        
        return redirect(url_for('auth.profile'))
    
    # Get user's posts
    from app.models.blog import Post
    user_posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
    
    return render_template('profile.html', title='My Profile', user=current_user, posts=user_posts)