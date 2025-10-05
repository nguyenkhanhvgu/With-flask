# Email Authentication Guide

This guide explains the email confirmation and password reset functionality implemented in the Flask blog application.

## Features Implemented

### 1. Email Confirmation Workflow
- **Registration**: New users must confirm their email before logging in
- **Token Generation**: Secure JWT tokens with 24-hour expiration
- **Email Templates**: Professional HTML and text email templates
- **Resend Functionality**: Users can request new confirmation emails
- **Rate Limiting**: Protection against spam (3 attempts per 5 minutes)

### 2. Password Reset Functionality
- **Reset Request**: Users can request password reset via email
- **Secure Tokens**: JWT tokens with 1-hour expiration for security
- **Email Notifications**: Users receive confirmation when password is changed
- **Rate Limiting**: Protection against abuse (3 attempts per 5 minutes)

### 3. Security Features
- **Rate Limiting**: Redis-based rate limiting for authentication endpoints
- **Token Validation**: Secure token generation and verification
- **Email Verification**: Prevents unauthorized account access
- **Session Management**: Proper session handling and cleanup

## Configuration

### Email Settings
Configure email settings in your `.env` file:

```bash
# Gmail Configuration (recommended for development)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password  # Use App Password, not regular password
MAIL_DEFAULT_SENDER=Flask Blog <your-email@gmail.com>
ADMIN_EMAIL=admin@yourdomain.com
```

### Gmail Setup
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password (not your regular password)
3. Use the App Password in `MAIL_PASSWORD`

### Redis Configuration (for Rate Limiting)
```bash
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=  # Leave empty if no password
```

## Usage

### User Registration Flow
1. User fills out registration form
2. Account is created but `email_confirmed=False`
3. Confirmation email is sent automatically
4. User clicks confirmation link in email
5. Email is confirmed, user can now log in

### Password Reset Flow
1. User clicks "Forgot Password" on login page
2. User enters email address
3. Password reset email is sent (if account exists)
4. User clicks reset link in email
5. User sets new password
6. Confirmation email is sent
7. User can log in with new password

### Email Templates
The following email templates are included:

- **Email Confirmation** (`templates/emails/confirm_email.html`)
- **Password Reset** (`templates/emails/reset_password.html`)
- **Password Changed** (`templates/emails/password_changed.html`)
- **Welcome Email** (`templates/emails/welcome.html`)

Each template has both HTML and text versions for compatibility.

## API Endpoints

### New Authentication Routes
- `GET/POST /auth/reset-password-request` - Request password reset
- `GET/POST /auth/reset-password/<token>` - Reset password with token
- `GET /auth/confirm/<token>` - Confirm email address
- `GET/POST /auth/resend-confirmation` - Resend confirmation email

### Rate Limiting
All authentication endpoints are protected with rate limiting:
- **Registration**: 3 attempts per 5 minutes
- **Login**: 5 attempts per 5 minutes
- **Password Reset**: 3 attempts per 5 minutes
- **Email Resend**: 3 attempts per 5 minutes

## Testing

### Development Testing
For development without real email sending:
1. Leave `MAIL_USERNAME` empty in `.env`
2. Check application logs for email content
3. Use the test script: `python test_email_auth.py`

### Production Testing
1. Configure real email settings
2. Register a test account
3. Check email delivery
4. Test all workflows end-to-end

## Security Considerations

### Token Security
- JWT tokens are signed with the application secret key
- Tokens include expiration times and purpose validation
- Tokens are invalidated after use (for password reset)

### Rate Limiting
- Redis-based sliding window rate limiting
- IP-based and user-based limits
- Graceful fallback if Redis is unavailable

### Email Security
- HTML and text versions prevent rendering issues
- No sensitive information in email content
- Clear expiration times communicated to users

## Troubleshooting

### Common Issues

#### Email Not Sending
1. Check email configuration in `.env`
2. Verify Gmail App Password (not regular password)
3. Check application logs for error messages
4. Test with `python test_email_auth.py`

#### Rate Limiting Issues
1. Ensure Redis is running
2. Check Redis connection settings
3. Clear rate limits if needed (admin function)

#### Token Issues
1. Check token expiration times
2. Verify secret key consistency
3. Check for clock synchronization issues

### Debug Commands
```bash
# Test email configuration
python -c "from app.utils.email import send_confirmation_email; print('Email utils OK')"

# Test rate limiting
python -c "from app.middleware.rate_limiting import auth_rate_limit; print('Rate limiting OK')"

# Run full test suite
python test_email_auth.py
```

## Code Examples

### Using Rate Limiting Decorator
```python
from app.middleware.rate_limiting import auth_rate_limit, rate_limit

@bp.route('/sensitive-endpoint')
@auth_rate_limit(limit=3, window=300)  # 3 attempts per 5 minutes
def sensitive_endpoint():
    # Your code here
    pass

@bp.route('/api-endpoint')
@rate_limit(limit=100, window=3600, per='user')  # 100 requests per hour per user
def api_endpoint():
    # Your code here
    pass
```

### Sending Custom Emails
```python
from app.utils.email import send_email

# Send custom email
success = send_email(
    to='user@example.com',
    subject='Custom Subject',
    template='custom_template',  # templates/emails/custom_template.html
    user=user_object,
    custom_var='custom_value'
)
```

### Checking Rate Limit Status
```python
from app.middleware.rate_limiting import get_rate_limit_status

status = get_rate_limit_status('rate_limit:ip:127.0.0.1:login', 5, 300)
print(f"Remaining attempts: {status['remaining']}")
print(f"Reset time: {status['reset_time']}")
```

## Integration with Existing Code

The email authentication features integrate seamlessly with the existing Flask blog application:

- **User Model**: Enhanced with email confirmation fields
- **Authentication Routes**: Extended with new endpoints
- **Templates**: New templates added, existing ones updated
- **Configuration**: Email settings added to config system
- **Middleware**: Rate limiting integrated with Flask request cycle

All existing functionality remains unchanged and fully compatible.