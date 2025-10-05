"""
Authentication Blueprint Routes

This module contains routes for user authentication functionality
including registration, login, logout, and profile management.
"""

from flask import render_template, request, flash, redirect, url_for, session, current_app
from flask_login import login_required, current_user
from datetime import datetime
from app.blueprints.auth import bp
from app.blueprints.auth.forms import (
    RegistrationForm, LoginForm, ProfileForm, 
    PasswordResetRequestForm, PasswordResetForm, ResendConfirmationForm
)
from app.middleware.rate_limiting import auth_rate_limit, rate_limit


@bp.route('/register', methods=['GET', 'POST'])
@auth_rate_limit(limit=3, window=300)  # 3 attempts per 5 minutes
def register():
    """
    User registration with form validation.
    
    This route demonstrates:
    - WTForms integration for better validation
    - Service layer integration for business logic
    - Proper error handling and user feedback
    - Redirect patterns for authenticated users
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Use AuthService for registration logic
        from app.services import AuthService
        
        result = AuthService.register_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        
        if result['success']:
            if result['email_sent']:
                flash(result['message'], 'success')
            else:
                flash(
                    'Registration successful, but we could not send the confirmation email. Please contact support.',
                    'warning'
                )
            return redirect(url_for('auth.login'))
        else:
            flash(result['message'], 'error')
    
    return render_template('register.html', title='Register', form=form)


@bp.route('/login', methods=['GET', 'POST'])
@auth_rate_limit(limit=5, window=300)  # 5 attempts per 5 minutes
def login():
    """
    User login with form validation and security features.
    
    This route demonstrates:
    - Form-based authentication
    - Service layer integration for business logic
    - Session management
    - Redirect handling for protected pages
    - Security logging
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Use AuthService for authentication logic
        from app.services import AuthService
        
        result = AuthService.authenticate_user(
            username=form.username.data,
            password=form.password.data,
            remember_me=form.remember.data
        )
        
        if result['success']:
            flash(result['message'], 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            if result['error'] == 'email_not_confirmed':
                flash(
                    result['message'] + ' '
                    '<a href="' + url_for('auth.resend_confirmation') + '">Resend confirmation email</a>',
                    'warning'
                )
            else:
                flash(result['message'], 'error')
    
    return render_template('login.html', title='Login', form=form)


@bp.route('/logout')
@login_required
def logout():
    """
    User logout with proper session cleanup.
    
    This route demonstrates:
    - Service layer integration for business logic
    - Secure logout procedures
    - Session cleanup
    - User feedback
    - Security logging
    """
    # Use AuthService for logout logic
    from app.services import AuthService
    
    result = AuthService.logout_user(current_user)
    
    # Clear session data for security
    session.clear()
    
    if result['success']:
        flash(result['message'], 'info')
    else:
        flash(result['message'], 'error')
    
    return redirect(url_for('main.home'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    User profile page with avatar upload and profile management.
    
    This route demonstrates:
    - File upload handling with validation
    - Form processing with WTForms
    - Database updates with error handling
    - User data display
    """
    form = ProfileForm()
    
    if form.validate_on_submit():
        try:
            # Import here to avoid circular imports
            from app.extensions import db
            from app.utils.file_helpers import save_uploaded_file
            
            if form.avatar.data:
                # Save new avatar
                avatar_filename = save_uploaded_file(form.avatar.data, 'avatars')
                if avatar_filename:
                    # Update user's avatar
                    old_avatar = current_user.avatar_filename
                    current_user.avatar_filename = avatar_filename
                    db.session.commit()
                    
                    current_app.logger.info(f'Avatar updated for user: {current_user.username}')
                    flash('Avatar updated successfully!', 'success')
                    
                    # TODO: Clean up old avatar file if it's not the default
                    # This would be implemented in a production system
                else:
                    flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
            
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Profile update error for user {current_user.username}: {str(e)}')
            flash('An error occurred while updating your profile. Please try again.', 'error')
    
    # Get user's posts for display
    from app.models.blog import Post
    user_posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
    
    return render_template('profile.html', 
                         title='My Profile', 
                         user=current_user, 
                         posts=user_posts,
                         form=form)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Change user password route.
    
    This route demonstrates:
    - Service layer integration for business logic
    - Password change functionality
    - Current password verification
    - Security best practices for password updates
    """
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not current_password or not new_password or not confirm_password:
            flash('Please fill in all fields.', 'error')
        elif new_password != confirm_password:
            flash('New passwords do not match.', 'error')
        else:
            # Use AuthService for password change logic
            from app.services import AuthService
            
            result = AuthService.change_password(
                user=current_user,
                current_password=current_password,
                new_password=new_password
            )
            
            if result['success']:
                flash(result['message'], 'success')
                return redirect(url_for('auth.profile'))
            else:
                flash(result['message'], 'error')
    
    return render_template('auth/change_password.html', title='Change Password')


@bp.before_request
def before_request():
    """
    Before request handler for the auth blueprint.
    
    This function demonstrates:
    - Request preprocessing
    - User activity tracking
    - Security checks
    """
    if current_user.is_authenticated:
        # Update last seen timestamp for active users
        from datetime import datetime
        from app.extensions import db
        
        try:
            current_user.last_seen = datetime.utcnow()
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Error updating last_seen for user {current_user.username}: {str(e)}')


@bp.route('/confirm/<token>')
def confirm_email(token):
    """
    Email confirmation route.
    
    This route demonstrates:
    - Service layer integration for business logic
    - Token verification and validation
    - Email confirmation workflow
    - User feedback and error handling
    """
    # Use AuthService for email confirmation logic
    from app.services import AuthService
    
    result = AuthService.confirm_email(token)
    
    if result['success']:
        if result.get('already_confirmed'):
            flash(result['message'], 'info')
            return redirect(url_for('auth.login'))
        else:
            return render_template('auth/confirm_email.html', success=True)
    else:
        return render_template('auth/confirm_email.html', 
                             success=False, 
                             error_message=result['message'])


@bp.route('/resend-confirmation', methods=['GET', 'POST'])
@login_required
@rate_limit(limit=3, window=300)  # 3 attempts per 5 minutes
def resend_confirmation():
    """
    Resend email confirmation route.
    
    This route demonstrates:
    - Service layer integration for business logic
    - Rate limiting for email sending
    - User authentication checks
    - Email resending workflow
    """
    if current_user.email_confirmed:
        flash('Your email is already confirmed.', 'info')
        return redirect(url_for('main.home'))
    
    form = ResendConfirmationForm()
    
    if form.validate_on_submit():
        # Use AuthService for resending confirmation email
        from app.services import AuthService
        
        result = AuthService.resend_confirmation_email(current_user)
        
        if result['success']:
            flash(result['message'], 'success')
        else:
            flash(result['message'], 'error')
        
        return redirect(url_for('main.home'))
    
    return render_template('auth/resend_confirmation.html', title='Resend Confirmation', form=form)


@bp.route('/reset-password-request', methods=['GET', 'POST'])
@auth_rate_limit(limit=3, window=300)  # 3 attempts per 5 minutes
def reset_password_request():
    """
    Password reset request route.
    
    This route demonstrates:
    - Service layer integration for business logic
    - Password reset initiation
    - Email validation and sending
    - Rate limiting for security
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = PasswordResetRequestForm()
    
    if form.validate_on_submit():
        # Use AuthService for password reset request logic
        from app.services import AuthService
        
        result = AuthService.request_password_reset(form.email.data)
        
        if result['success']:
            flash(result['message'], 'info')
        else:
            flash(result['message'], 'error')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', 
                         title='Reset Password', form=form)


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@auth_rate_limit(limit=5, window=300)  # 5 attempts per 5 minutes
def reset_password(token):
    """
    Password reset route.
    
    This route demonstrates:
    - Service layer integration for business logic
    - Token verification for password reset
    - Secure password updating
    - Session invalidation for security
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        # Use AuthService for password reset logic
        from app.services import AuthService
        
        result = AuthService.reset_password(token, form.password.data)
        
        if result['success']:
            flash(result['message'], 'success')
            return redirect(url_for('auth.login'))
        else:
            if result['error'] in ['invalid_token', 'token_expired', 'user_not_found']:
                flash(result['message'], 'error')
                return redirect(url_for('auth.reset_password_request'))
            else:
                flash(result['message'], 'error')
    
    return render_template('auth/reset_password.html', title='Reset Password', form=form)


@bp.after_request
def after_request(response):
    """
    After request handler for the auth blueprint.
    
    This function demonstrates:
    - Response processing
    - Security headers
    - Logging
    """
    # Add security headers for auth routes
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response