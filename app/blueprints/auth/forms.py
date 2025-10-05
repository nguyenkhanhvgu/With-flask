"""
Authentication Forms

This module contains WTForms form classes for authentication functionality.
Using WTForms provides better validation, CSRF protection, and form rendering.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User


class RegistrationForm(FlaskForm):
    """
    User registration form with validation.
    
    This form demonstrates WTForms validation patterns and custom validators.
    """
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters.')
    ])
    
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Custom validator to check if username already exists."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different one.')
    
    def validate_email(self, email):
        """Custom validator to check if email already exists."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email.')


class LoginForm(FlaskForm):
    """
    User login form with validation.
    
    This form demonstrates basic authentication form patterns.
    """
    username = StringField('Username', validators=[
        DataRequired(message='Username is required.')
    ])
    
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required.')
    ])
    
    remember = BooleanField('Remember Me')
    
    submit = SubmitField('Login')


class ProfileForm(FlaskForm):
    """
    User profile update form.
    
    This form demonstrates file upload handling with WTForms.
    """
    avatar = FileField('Update Avatar', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    
    submit = SubmitField('Update Profile')


class PasswordResetRequestForm(FlaskForm):
    """
    Password reset request form.
    
    This form handles password reset requests with email validation.
    """
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address.')
    ])
    
    submit = SubmitField('Send Reset Link')
    
    def validate_email(self, email):
        """Custom validator to check if email exists."""
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account found with that email address.')


class PasswordResetForm(FlaskForm):
    """
    Password reset form.
    
    This form handles setting a new password after email verification.
    """
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')
    ])
    
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    
    submit = SubmitField('Reset Password')


class ResendConfirmationForm(FlaskForm):
    """
    Form to resend email confirmation.
    
    This form allows users to request a new confirmation email.
    """
    submit = SubmitField('Resend Confirmation Email')