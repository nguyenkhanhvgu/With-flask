"""
Email Utilities

This module contains utilities for sending emails including email confirmation
and password reset functionality. It demonstrates Flask-Mail integration and
secure token generation for authentication workflows.
"""

import secrets
from datetime import datetime, timedelta
from flask import current_app, render_template, url_for
from flask_mail import Message
from app.extensions import mail, db
import jwt


def generate_token(user_id, purpose='email_confirmation', expires_in=3600):
    """
    Generate a secure token for email confirmation or password reset.
    
    Args:
        user_id (int): The user ID to encode in the token
        purpose (str): The purpose of the token ('email_confirmation' or 'password_reset')
        expires_in (int): Token expiration time in seconds (default: 1 hour)
        
    Returns:
        str: The generated JWT token
        
    This function demonstrates secure token generation using JWT with expiration.
    """
    payload = {
        'user_id': user_id,
        'purpose': purpose,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow()
    }
    
    return jwt.encode(
        payload,
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )


def verify_token(token, purpose='email_confirmation'):
    """
    Verify and decode a JWT token.
    
    Args:
        token (str): The JWT token to verify
        purpose (str): Expected purpose of the token
        
    Returns:
        int or None: User ID if token is valid, None otherwise
        
    This function demonstrates secure token verification with purpose validation.
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config['SECRET_KEY'],
            algorithms=['HS256']
        )
        
        # Verify the token purpose matches
        if payload.get('purpose') != purpose:
            return None
            
        return payload.get('user_id')
        
    except jwt.ExpiredSignatureError:
        current_app.logger.warning(f'Expired {purpose} token attempted')
        return None
    except jwt.InvalidTokenError:
        current_app.logger.warning(f'Invalid {purpose} token attempted')
        return None


def send_email(to, subject, template, **kwargs):
    """
    Send an email using Flask-Mail.
    
    Args:
        to (str): Recipient email address
        subject (str): Email subject
        template (str): Template name (without .html extension)
        **kwargs: Additional template variables
        
    Returns:
        bool: True if email was sent successfully, False otherwise
        
    This function demonstrates email sending with HTML templates and error handling.
    """
    try:
        msg = Message(
            subject=f"[Flask Blog] {subject}",
            recipients=[to],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Render HTML template
        msg.html = render_template(f'emails/{template}.html', **kwargs)
        
        # Render text template (fallback)
        try:
            msg.body = render_template(f'emails/{template}.txt', **kwargs)
        except:
            # If text template doesn't exist, create a simple text version
            msg.body = f"Please view this email in an HTML-capable email client."
        
        mail.send(msg)
        current_app.logger.info(f'Email sent successfully to {to}: {subject}')
        return True
        
    except Exception as e:
        current_app.logger.error(f'Failed to send email to {to}: {str(e)}')
        return False


def send_confirmation_email(user):
    """
    Send email confirmation email to a user.
    
    Args:
        user (User): The user to send confirmation email to
        
    Returns:
        bool: True if email was sent successfully, False otherwise
        
    This function demonstrates email confirmation workflow implementation.
    """
    try:
        # Generate confirmation token (24 hours expiration)
        token = generate_token(user.id, 'email_confirmation', expires_in=86400)
        
        # Store token in user record for additional security
        user.email_confirmation_token = token
        db.session.commit()
        
        # Generate confirmation URL
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        
        # Send email
        return send_email(
            to=user.email,
            subject='Confirm Your Email Address',
            template='confirm_email',
            user=user,
            confirm_url=confirm_url
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error sending confirmation email to {user.email}: {str(e)}')
        return False


def send_password_reset_email(user):
    """
    Send password reset email to a user.
    
    Args:
        user (User): The user to send password reset email to
        
    Returns:
        bool: True if email was sent successfully, False otherwise
        
    This function demonstrates password reset workflow implementation.
    """
    try:
        # Generate password reset token (1 hour expiration)
        token = generate_token(user.id, 'password_reset', expires_in=3600)
        
        # Store token and expiration in user record
        user.password_reset_token = token
        user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        
        # Generate reset URL
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        # Send email
        return send_email(
            to=user.email,
            subject='Password Reset Request',
            template='reset_password',
            user=user,
            reset_url=reset_url
        )
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error sending password reset email to {user.email}: {str(e)}')
        return False


def send_password_changed_notification(user):
    """
    Send notification email when password is successfully changed.
    
    Args:
        user (User): The user whose password was changed
        
    Returns:
        bool: True if email was sent successfully, False otherwise
        
    This function demonstrates security notification implementation.
    """
    try:
        return send_email(
            to=user.email,
            subject='Password Changed Successfully',
            template='password_changed',
            user=user,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        current_app.logger.error(f'Error sending password change notification to {user.email}: {str(e)}')
        return False


def send_welcome_email(user):
    """
    Send welcome email to newly registered users.
    
    Args:
        user (User): The newly registered user
        
    Returns:
        bool: True if email was sent successfully, False otherwise
        
    This function demonstrates welcome email workflow implementation.
    """
    try:
        return send_email(
            to=user.email,
            subject='Welcome to Flask Blog!',
            template='welcome',
            user=user
        )
        
    except Exception as e:
        current_app.logger.error(f'Error sending welcome email to {user.email}: {str(e)}')
        return False