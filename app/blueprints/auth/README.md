# Authentication Blueprint

This blueprint handles all authentication-related functionality for the Flask blog application. It demonstrates Flask blueprint organization, form handling, security best practices, and user management.

## Structure

```
app/blueprints/auth/
├── __init__.py          # Blueprint initialization
├── routes.py            # Authentication routes
├── forms.py             # WTForms form classes
├── errors.py            # Blueprint-specific error handlers
├── utils.py             # Authentication utility functions
└── README.md            # This documentation
```

## Routes

### Public Routes
- `GET/POST /auth/register` - User registration
- `GET/POST /auth/login` - User login

### Protected Routes (require authentication)
- `GET /auth/logout` - User logout
- `GET/POST /auth/profile` - User profile management
- `GET/POST /auth/change-password` - Password change functionality

## Features Demonstrated

### 1. Blueprint Organization
- Modular route organization
- Blueprint-specific error handlers
- URL prefixes (`/auth/`)
- Template organization

### 2. Form Handling with WTForms
- Form validation (client and server-side)
- CSRF protection
- Custom validators
- File upload handling

### 3. Security Best Practices
- Password hashing with Werkzeug
- Session management with Flask-Login
- Secure file uploads
- Input validation and sanitization
- Security headers
- Safe URL redirects

### 4. User Management
- User registration with validation
- Login with remember me functionality
- Profile management with avatar uploads
- Password change functionality
- User activity tracking (last_seen)

### 5. Error Handling
- Blueprint-specific error handlers
- Graceful error recovery
- User-friendly error messages
- Logging for debugging

## Educational Concepts

### Flask Blueprints
This blueprint demonstrates how to organize a Flask application using blueprints:
- Separation of concerns
- Modular architecture
- URL prefixes
- Blueprint registration

### Authentication Patterns
- Application factory pattern integration
- User loader functions
- Login/logout workflows
- Session management

### Form Processing
- WTForms integration
- Form validation patterns
- File upload handling
- CSRF protection

### Security Considerations
- Password security
- Session security
- File upload security
- Input validation

## Usage

The auth blueprint is automatically registered in the application factory with the URL prefix `/auth/`. All authentication routes are accessible under this prefix:

- Registration: `/auth/register`
- Login: `/auth/login`
- Logout: `/auth/logout`
- Profile: `/auth/profile`
- Change Password: `/auth/change-password`

## Templates

The auth blueprint uses the following templates:
- `templates/register.html` - Registration form
- `templates/login.html` - Login form
- `templates/profile.html` - User profile page
- `templates/auth/change_password.html` - Password change form

## Future Enhancements

The auth blueprint includes placeholder functionality for:
- Email confirmation
- Password reset via email
- Two-factor authentication
- Account lockout after failed attempts
- OAuth integration

These features demonstrate how the blueprint can be extended while maintaining clean organization.