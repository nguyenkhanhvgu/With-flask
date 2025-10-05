"""
Authentication Service

This module contains the AuthService class that encapsulates all authentication
business logic. It demonstrates the service layer pattern for separating
business logic from route handlers and provides a clean interface for
authentication operations.
"""

from datetime import datetime, timedelta
from flask import current_app
from flask_login import login_user, logout_user
from app.extensions import db
from app.models.user import User
from app.models.role import Role
from app.utils.email import (
    send_confirmation_email, send_password_reset_email,
    send_password_changed_notification, send_welcome_email, verify_token
)
from app.middleware.logging import log_user_action


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class AuthService:
    """
    Service class for handling authentication operations.
    
    This class demonstrates the service layer pattern by encapsulating
    all authentication business logic in a single, testable class.
    It provides methods for user registration, login, password management,
    and email confirmation workflows.
    """
    
    @staticmethod
    def register_user(username, email, password, first_name=None, last_name=None):
        """
        Register a new user with email confirmation workflow.
        
        Args:
            username (str): Desired username
            email (str): User's email address
            password (str): Plain text password
            first_name (str, optional): User's first name
            last_name (str, optional): User's last name
            
        Returns:
            dict: Result dictionary with success status and user data or error message
            
        Raises:
            ValidationError: If validation fails
            
        This method demonstrates:
        - Input validation
        - User creation with proper defaults
        - Email confirmation workflow
        - Transaction management
        - Audit logging
        """
        try:
            # Validate input
            validation_errors = AuthService._validate_registration_data(
                username, email, password
            )
            if validation_errors:
                raise ValidationError(validation_errors)
            
            # Check if user already exists
            if User.get_by_username(username):
                raise ValidationError("Username already exists")
            
            if User.get_by_email(email):
                raise ValidationError("Email address already registered")
            
            # Create new user
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                email_confirmed=False,
                is_active=True
            )
            user.set_password(password)
            
            # Assign default role
            default_role = Role.get_default_role()
            if default_role:
                user.role = default_role
            
            db.session.add(user)
            db.session.commit()
            
            # Send confirmation email
            email_sent = send_confirmation_email(user)
            
            # Log user registration
            log_user_action('user_registration', {
                'username': user.username,
                'email': user.email,
                'user_id': user.id,
                'email_sent': email_sent
            })
            
            current_app.logger.info(f'New user registered: {user.username}')
            
            return {
                'success': True,
                'user': user,
                'email_sent': email_sent,
                'message': 'Registration successful! Please check your email to confirm your account.'
            }
            
        except ValidationError as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'message': str(e)
            }
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {str(e)}')
            return {
                'success': False,
                'error': 'registration_failed',
                'message': 'An error occurred during registration. Please try again.'
            }
    
    @staticmethod
    def authenticate_user(username, password, remember_me=False):
        """
        Authenticate a user and handle login.
        
        Args:
            username (str): Username or email
            password (str): Plain text password
            remember_me (bool): Whether to remember the user
            
        Returns:
            dict: Result dictionary with success status and user data or error message
            
        This method demonstrates:
        - User authentication
        - Account status validation
        - Session management
        - Activity tracking
        - Security logging
        """
        try:
            # Find user by username or email
            user = (User.get_by_username(username) or 
                   User.get_by_email(username))
            
            if not user or not user.check_password(password):
                current_app.logger.warning(f'Failed login attempt for: {username}')
                return {
                    'success': False,
                    'error': 'invalid_credentials',
                    'message': 'Invalid username or password.'
                }
            
            # Check if user account is active
            if not user.is_active:
                current_app.logger.warning(f'Login attempt by deactivated user: {user.username}')
                return {
                    'success': False,
                    'error': 'account_deactivated',
                    'message': 'Your account has been deactivated. Please contact support.'
                }
            
            # Check if email is confirmed
            if not user.email_confirmed:
                current_app.logger.warning(f'Login attempt by unconfirmed user: {user.username}')
                return {
                    'success': False,
                    'error': 'email_not_confirmed',
                    'message': 'Please confirm your email address before logging in.',
                    'user': user
                }
            
            # Log the user in
            login_duration = timedelta(days=7) if remember_me else None
            login_user(user, remember=remember_me, duration=login_duration)
            
            # Update last seen timestamp
            user.ping()
            db.session.commit()
            
            # Log successful login
            log_user_action('user_login', {
                'username': user.username,
                'user_id': user.id,
                'remember_me': remember_me
            })
            
            current_app.logger.info(f'User logged in: {user.username}')
            
            return {
                'success': True,
                'user': user,
                'message': f'Welcome back, {user.username}!'
            }
            
        except Exception as e:
            current_app.logger.error(f'Login error: {str(e)}')
            return {
                'success': False,
                'error': 'login_failed',
                'message': 'An error occurred during login. Please try again.'
            }
    
    @staticmethod
    def logout_user(user):
        """
        Log out a user and clean up session.
        
        Args:
            user (User): The user to log out
            
        Returns:
            dict: Result dictionary with success status and message
            
        This method demonstrates:
        - Secure logout procedures
        - Session cleanup
        - Security logging
        """
        try:
            username = user.username
            user_id = user.id
            
            # Log user action before logout
            log_user_action('user_logout', {
                'username': username,
                'user_id': user_id
            })
            
            current_app.logger.info(f'User logged out: {username}')
            
            # Perform logout
            logout_user()
            
            return {
                'success': True,
                'message': f'Goodbye, {username}! You have been logged out.'
            }
            
        except Exception as e:
            current_app.logger.error(f'Logout error: {str(e)}')
            return {
                'success': False,
                'error': 'logout_failed',
                'message': 'An error occurred during logout.'
            }
    
    @staticmethod
    def change_password(user, current_password, new_password):
        """
        Change a user's password with validation.
        
        Args:
            user (User): The user changing their password
            current_password (str): Current password for verification
            new_password (str): New password to set
            
        Returns:
            dict: Result dictionary with success status and message
            
        This method demonstrates:
        - Password change validation
        - Security checks
        - Notification workflows
        """
        try:
            # Validate current password
            if not user.check_password(current_password):
                return {
                    'success': False,
                    'error': 'invalid_current_password',
                    'message': 'Current password is incorrect.'
                }
            
            # Validate new password
            password_errors = AuthService._validate_password(new_password)
            if password_errors:
                return {
                    'success': False,
                    'error': 'invalid_new_password',
                    'message': password_errors
                }
            
            # Check if new password is different
            if current_password == new_password:
                return {
                    'success': False,
                    'error': 'same_password',
                    'message': 'New password must be different from current password.'
                }
            
            # Update password
            user.set_password(new_password)
            db.session.commit()
            
            # Send notification email
            send_password_changed_notification(user)
            
            # Log password change
            log_user_action('password_changed', {
                'username': user.username,
                'user_id': user.id
            })
            
            current_app.logger.info(f'Password changed for user: {user.username}')
            
            return {
                'success': True,
                'message': 'Password changed successfully!'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Password change error for user {user.username}: {str(e)}')
            return {
                'success': False,
                'error': 'password_change_failed',
                'message': 'An error occurred while changing your password. Please try again.'
            }
    
    @staticmethod
    def request_password_reset(email):
        """
        Initiate password reset workflow.
        
        Args:
            email (str): Email address for password reset
            
        Returns:
            dict: Result dictionary with success status and message
            
        This method demonstrates:
        - Password reset initiation
        - Security considerations (no user enumeration)
        - Email workflow
        """
        try:
            user = User.get_by_email(email)
            
            if user and user.is_active:
                # Send password reset email
                email_sent = send_password_reset_email(user)
                
                if email_sent:
                    # Log password reset request
                    log_user_action('password_reset_requested', {
                        'username': user.username,
                        'email': user.email,
                        'user_id': user.id
                    })
                    
                    current_app.logger.info(f'Password reset requested for: {user.username}')
                else:
                    current_app.logger.error(f'Failed to send password reset email to: {email}')
            
            # Always return success to prevent user enumeration
            return {
                'success': True,
                'message': 'If an account with that email exists, a password reset link has been sent.'
            }
            
        except Exception as e:
            current_app.logger.error(f'Password reset request error: {str(e)}')
            return {
                'success': False,
                'error': 'reset_request_failed',
                'message': 'An error occurred. Please try again later.'
            }
    
    @staticmethod
    def reset_password(token, new_password):
        """
        Complete password reset using token.
        
        Args:
            token (str): Password reset token
            new_password (str): New password to set
            
        Returns:
            dict: Result dictionary with success status and message
            
        This method demonstrates:
        - Token verification
        - Password reset completion
        - Security notifications
        """
        try:
            # Verify token
            user_id = verify_token(token, 'password_reset')
            
            if user_id is None:
                current_app.logger.warning('Invalid password reset token attempted')
                return {
                    'success': False,
                    'error': 'invalid_token',
                    'message': 'The password reset link is invalid or has expired.'
                }
            
            user = User.query.get(user_id)
            if not user:
                current_app.logger.error(f'Password reset: User {user_id} not found')
                return {
                    'success': False,
                    'error': 'user_not_found',
                    'message': 'Invalid password reset link.'
                }
            
            # Verify token matches and hasn't expired
            if (user.password_reset_token != token or 
                user.password_reset_expires is None or 
                user.password_reset_expires < datetime.utcnow()):
                current_app.logger.warning(f'Password reset: Invalid or expired token for user {user.username}')
                return {
                    'success': False,
                    'error': 'token_expired',
                    'message': 'The password reset link is invalid or has expired.'
                }
            
            # Validate new password
            password_errors = AuthService._validate_password(new_password)
            if password_errors:
                return {
                    'success': False,
                    'error': 'invalid_password',
                    'message': password_errors
                }
            
            # Update password and clear reset tokens
            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_expires = None
            db.session.commit()
            
            # Send notification email
            send_password_changed_notification(user)
            
            # Log password reset completion
            log_user_action('password_reset_completed', {
                'username': user.username,
                'email': user.email,
                'user_id': user.id
            })
            
            current_app.logger.info(f'Password reset completed for: {user.username}')
            
            return {
                'success': True,
                'message': 'Your password has been reset successfully. You can now log in.'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Password reset error: {str(e)}')
            return {
                'success': False,
                'error': 'reset_failed',
                'message': 'An error occurred while resetting your password. Please try again.'
            }
    
    @staticmethod
    def confirm_email(token):
        """
        Confirm user email using token.
        
        Args:
            token (str): Email confirmation token
            
        Returns:
            dict: Result dictionary with success status and message
            
        This method demonstrates:
        - Email confirmation workflow
        - Token verification
        - Account activation
        """
        try:
            # Verify token
            user_id = verify_token(token, 'email_confirmation')
            
            if user_id is None:
                current_app.logger.warning('Invalid email confirmation token attempted')
                return {
                    'success': False,
                    'error': 'invalid_token',
                    'message': 'The confirmation link is invalid or has expired.'
                }
            
            user = User.query.get(user_id)
            if not user:
                current_app.logger.error(f'Email confirmation: User {user_id} not found')
                return {
                    'success': False,
                    'error': 'user_not_found',
                    'message': 'User account not found.'
                }
            
            if user.email_confirmed:
                current_app.logger.info(f'Email confirmation: User {user.username} already confirmed')
                return {
                    'success': True,
                    'already_confirmed': True,
                    'message': 'Your email is already confirmed. You can log in now.'
                }
            
            # Verify token matches
            if user.email_confirmation_token != token:
                current_app.logger.warning(f'Email confirmation: Token mismatch for user {user.username}')
                return {
                    'success': False,
                    'error': 'token_mismatch',
                    'message': 'The confirmation link is invalid.'
                }
            
            # Confirm the email
            user.email_confirmed = True
            user.email_confirmation_token = None
            db.session.commit()
            
            # Send welcome email
            send_welcome_email(user)
            
            # Log email confirmation
            log_user_action('email_confirmed', {
                'username': user.username,
                'email': user.email,
                'user_id': user.id
            })
            
            current_app.logger.info(f'Email confirmed for user: {user.username}')
            
            return {
                'success': True,
                'user': user,
                'message': 'Your email has been confirmed successfully! You can now log in.'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Email confirmation error: {str(e)}')
            return {
                'success': False,
                'error': 'confirmation_failed',
                'message': 'An error occurred during confirmation. Please try again.'
            }
    
    @staticmethod
    def resend_confirmation_email(user):
        """
        Resend email confirmation to a user.
        
        Args:
            user (User): The user to resend confirmation to
            
        Returns:
            dict: Result dictionary with success status and message
            
        This method demonstrates:
        - Email resending workflow
        - Rate limiting considerations
        - User status validation
        """
        try:
            if user.email_confirmed:
                return {
                    'success': False,
                    'error': 'already_confirmed',
                    'message': 'Your email is already confirmed.'
                }
            
            # Send confirmation email
            email_sent = send_confirmation_email(user)
            
            if email_sent:
                current_app.logger.info(f'Confirmation email resent to: {user.username}')
                return {
                    'success': True,
                    'message': 'A new confirmation email has been sent to your email address.'
                }
            else:
                current_app.logger.error(f'Failed to resend confirmation email to: {user.username}')
                return {
                    'success': False,
                    'error': 'email_send_failed',
                    'message': 'Could not send confirmation email. Please try again later.'
                }
            
        except Exception as e:
            current_app.logger.error(f'Error resending confirmation email: {str(e)}')
            return {
                'success': False,
                'error': 'resend_failed',
                'message': 'An error occurred. Please try again later.'
            }
    
    @staticmethod
    def _validate_registration_data(username, email, password):
        """
        Validate user registration data.
        
        Args:
            username (str): Username to validate
            email (str): Email to validate
            password (str): Password to validate
            
        Returns:
            str or None: Error message if validation fails, None if valid
        """
        import re
        
        if not username or len(username.strip()) < 3:
            return "Username must be at least 3 characters long"
        
        if not username.replace('_', '').replace('-', '').isalnum():
            return "Username can only contain letters, numbers, hyphens, and underscores"
        
        if not email or '@' not in email:
            return "Please provide a valid email address"
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return "Please provide a valid email address"
        
        password_error = AuthService._validate_password(password)
        if password_error:
            return password_error
        
        return None
    
    @staticmethod
    def _validate_password(password):
        """
        Validate password strength.
        
        Args:
            password (str): Password to validate
            
        Returns:
            str or None: Error message if validation fails, None if valid
        """
        if not password:
            return "Password is required"
        
        if len(password) < 6:
            return "Password must be at least 6 characters long"
        
        if len(password) > 128:
            return "Password must be less than 128 characters long"
        
        # Optional: Add more password strength requirements
        # if not any(c.isupper() for c in password):
        #     return "Password must contain at least one uppercase letter"
        
        # if not any(c.islower() for c in password):
        #     return "Password must contain at least one lowercase letter"
        
        # if not any(c.isdigit() for c in password):
        #     return "Password must contain at least one number"
        
        return None