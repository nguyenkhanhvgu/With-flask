"""
Authentication Utilities

This module contains utility functions specific to authentication functionality.
It demonstrates how to organize helper functions within a blueprint.
"""

import secrets
import string
from datetime import datetime, timedelta
from flask import current_app, url_for
from flask_mail import Message
from app.extensions import mail


def generate_token(length=32):
    """
    Generate a secure random token for password resets or email confirmation.
    
    Args:
        length (int): Length of the token to generate
        
    Returns:
        str: A secure random token
        
    This function demonstrates secure token generation for authentication purposes.
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def send_password_reset_email(user, token):
    """
    Send password reset email to user.
    
    Args:
        user: User object
        token (str): Password reset token
        
    This function demonstrates email integration for authentication workflows.
    Note: This is a placeholder for future password reset functionality.
    """
    if not current_app.config.get('MAIL_USERNAME'):
        current_app.logger.warning('Email not configured - skipping password reset email')
        return
    
    subject = 'Password Reset Request - Flask Blog'
    
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    
    text_body = f'''Hi {user.username},

You have requested a password reset for your Flask Blog account.

Click the following link to reset your password:
{reset_url}

If you did not request this password reset, please ignore this email.

This link will expire in 1 hour.

Best regards,
Flask Blog Team
'''
    
    html_body = f'''
    <h3>Password Reset Request</h3>
    <p>Hi <strong>{user.username}</strong>,</p>
    <p>You have requested a password reset for your Flask Blog account.</p>
    
    <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
    
    <p>If you did not request this password reset, please ignore this email.</p>
    <p><small>This link will expire in 1 hour.</small></p>
    
    <p>Best regards,<br>Flask Blog Team</p>
    '''
    
    try:
        msg = Message(subject, recipients=[user.email])
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        current_app.logger.info(f'Password reset email sent to {user.email}')
    except Exception as e:
        current_app.logger.error(f'Failed to send password reset email: {str(e)}')


def send_confirmation_email(user, token):
    """
    Send email confirmation email to user.
    
    Args:
        user: User object
        token (str): Email confirmation token
        
    This function demonstrates email confirmation workflow.
    Note: This is a placeholder for future email confirmation functionality.
    """
    if not current_app.config.get('MAIL_USERNAME'):
        current_app.logger.warning('Email not configured - skipping confirmation email')
        return
    
    subject = 'Confirm Your Email - Flask Blog'
    
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    
    text_body = f'''Hi {user.username},

Welcome to Flask Blog! Please confirm your email address by clicking the link below:

{confirm_url}

If you did not create this account, please ignore this email.

Best regards,
Flask Blog Team
'''
    
    html_body = f'''
    <h3>Welcome to Flask Blog!</h3>
    <p>Hi <strong>{user.username}</strong>,</p>
    <p>Welcome to Flask Blog! Please confirm your email address by clicking the button below:</p>
    
    <p><a href="{confirm_url}" style="background-color: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Confirm Email</a></p>
    
    <p>If you did not create this account, please ignore this email.</p>
    
    <p>Best regards,<br>Flask Blog Team</p>
    '''
    
    try:
        msg = Message(subject, recipients=[user.email])
        msg.body = text_body
        msg.html = html_body
        mail.send(msg)
        current_app.logger.info(f'Confirmation email sent to {user.email}')
    except Exception as e:
        current_app.logger.error(f'Failed to send confirmation email: {str(e)}')


def is_safe_url(target):
    """
    Check if a URL is safe for redirects.
    
    Args:
        target (str): The URL to check
        
    Returns:
        bool: True if the URL is safe, False otherwise
        
    This function demonstrates security best practices for URL redirects.
    """
    from urllib.parse import urlparse, urljoin
    from flask import request
    
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def validate_password_strength(password):
    """
    Validate password strength.
    
    Args:
        password (str): Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
        
    This function demonstrates password validation best practices.
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter."
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter."
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit."
    
    # Check for common weak passwords
    weak_passwords = ['password', '123456', 'qwerty', 'abc123', 'password123']
    if password.lower() in weak_passwords:
        return False, "Password is too common. Please choose a stronger password."
    
    return True, "Password is strong."