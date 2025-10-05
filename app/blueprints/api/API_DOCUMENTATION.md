# Flask Blog API Documentation

## Overview

The Flask Blog API provides comprehensive REST endpoints for managing blog content, user authentication, and administrative functions. The API is built using Flask-RESTX and includes interactive Swagger documentation.

## API Documentation Access

### Interactive Documentation (Swagger UI)
- **URL**: `/api/v1/docs/`
- **Description**: Interactive API documentation with request/response examples
- **Features**: 
  - Try out API endpoints directly from the browser
  - View request/response schemas
  - Authentication testing
  - Example requests and responses

### API Specification
- **Format**: OpenAPI 3.0 (Swagger)
- **URL**: `/api/v1/swagger.json`
- **Description**: Machine-readable API specification

## Authentication

The API uses JWT (JSON Web Token) authentication for protected endpoints.

### Getting a Token

1. **Register a new account**:
   ```bash
   POST /api/v1/auth/register
   ```

2. **Login with existing credentials**:
   ```bash
   POST /api/v1/auth/login
   ```

Both endpoints return a JWT token in the response.

### Using the Token

Include the JWT token in the Authorization header for protected endpoints:

```bash
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### Token Management

- **Verify Token**: `GET /api/v1/auth/verify`
- **Logout**: `POST /api/v1/auth/logout`
- **Token Expiration**: 7 days (configurable)

## API Versioning

The API implements versioning to ensure backward compatibility:

- **Current Version**: v1
- **Base URL**: `/api/v1/`
- **Version Header**: `Accept: application/vnd.api+json;version=1`

### Version Strategy

- **URL Versioning**: Primary method (`/api/v1/`, `/api/v2/`)
- **Header Versioning**: Alternative method for clients that prefer headers
- **Backward Compatibility**: Previous versions maintained for 12 months

## Rate Limiting

API endpoints are protected by rate limiting to prevent abuse:

- **Default Limit**: 100 requests per hour per IP
- **Authenticated Users**: 1000 requests per hour
- **Headers**: Rate limit information included in response headers
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when the rate limit resets

## API Endpoints Overview

### Authentication (`/auth`)
- `POST /auth/register` - Register new user account
- `POST /auth/login` - Authenticate user and get token
- `GET /auth/verify` - Verify token validity
- `POST /auth/logout` - Logout user

### Posts (`/posts`)
- `GET /posts` - List all posts (with pagination and filtering)
- `POST /posts` - Create new post (authenticated)
- `GET /posts/{id}` - Get specific post
- `PUT /posts/{id}` - Update post (author/admin only)
- `DELETE /posts/{id}` - Delete post (author/admin only)

### Users (`/users`)
- `GET /users` - List all users (admin only)
- `GET /users/{id}` - Get user profile
- `PUT /users/{id}` - Update user profile (self/admin only)
- `DELETE /users/{id}` - Delete user account (admin only)

### Comments (`/comments`)
- `GET /posts/{id}/comments` - Get comments for a post
- `POST /posts/{id}/comments` - Add comment to post (authenticated)
- `PUT /comments/{id}` - Update comment (author/admin only)
- `DELETE /comments/{id}` - Delete comment (author/admin only)

### Categories (`/categories`)
- `GET /categories` - List all categories
- `POST /categories` - Create category (admin only)
- `PUT /categories/{id}` - Update category (admin only)
- `DELETE /categories/{id}` - Delete category (admin only)

### Admin (`/admin`)
- `GET /admin/stats` - Get system statistics (admin only)
- `GET /admin/users` - Advanced user management (admin only)
- `POST /admin/users/{id}/activate` - Activate user account (admin only)
- `POST /admin/users/{id}/deactivate` - Deactivate user account (admin only)

### Utilities (`/utils`)
- `GET /utils/health` - System health check
- `GET /utils/version` - API version information
- `POST /utils/upload/avatar` - Upload user avatar (authenticated)
- `POST /utils/upload/post-image` - Upload post image (authenticated)

## Request/Response Format

### Content Types
- **Request**: `application/json`
- **Response**: `application/json`
- **File Upload**: `multipart/form-data`

### Standard Response Format

#### Success Response
```json
{
  "data": {
    // Response data
  },
  "pagination": {
    // Pagination info (for list endpoints)
  }
}
```

#### Error Response
```json
{
  "error": "Error Type",
  "message": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {
    // Additional error details
  }
}
```

### Pagination

List endpoints support pagination with the following parameters:

- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10, max: 100)

Pagination information is included in the response:

```json
{
  "pagination": {
    "page": 1,
    "pages": 5,
    "per_page": 10,
    "total": 42,
    "has_next": true,
    "has_prev": false
  }
}
```

### Filtering and Sorting

Many endpoints support filtering and sorting:

#### Posts Filtering
- `category`: Filter by category ID
- `author`: Filter by author username
- `search`: Search in title and content
- `sort`: Sort order (newest, oldest, popular)

#### Example
```bash
GET /api/v1/posts?category=1&sort=popular&search=flask&page=2
```

## Error Handling

### HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource already exists
- `413 Payload Too Large`: File upload too large
- `422 Unprocessable Entity`: Validation errors
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

### Error Codes

Custom error codes for specific scenarios:

- `INVALID_CREDENTIALS`: Login failed
- `TOKEN_EXPIRED`: JWT token has expired
- `INSUFFICIENT_PERMISSIONS`: User lacks required permissions
- `RESOURCE_NOT_FOUND`: Requested resource doesn't exist
- `VALIDATION_ERROR`: Request data validation failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `FILE_TOO_LARGE`: Uploaded file exceeds size limit
- `INVALID_FILE_TYPE`: Unsupported file format

## File Uploads

### Avatar Upload
- **Endpoint**: `POST /utils/upload/avatar`
- **Max Size**: 5MB
- **Formats**: PNG, JPG, JPEG, GIF
- **Dimensions**: Recommended 200x200px

### Post Image Upload
- **Endpoint**: `POST /utils/upload/post-image`
- **Max Size**: 10MB
- **Formats**: PNG, JPG, JPEG, GIF, WebP
- **Dimensions**: Recommended max 1920x1080px

### Upload Response
```json
{
  "success": true,
  "filename": "avatar_user123_20231201.jpg",
  "url": "/static/uploads/avatars/avatar_user123_20231201.jpg",
  "message": "File uploaded successfully"
}
```

## Security

### Authentication Security
- JWT tokens with configurable expiration
- Secure password hashing (bcrypt)
- Account lockout after failed attempts
- Email verification for new accounts

### API Security
- Rate limiting to prevent abuse
- Input validation and sanitization
- SQL injection prevention
- XSS protection
- CSRF protection for web interface

### File Upload Security
- File type validation
- File size limits
- Secure filename generation
- Virus scanning (recommended for production)

## Development and Testing

### Local Development
1. Start the Flask development server
2. Access Swagger UI at `http://localhost:5000/api/v1/docs/`
3. Use the interactive documentation to test endpoints

### API Testing Tools
- **Swagger UI**: Built-in interactive testing
- **Postman**: Import OpenAPI specification
- **curl**: Command-line testing
- **HTTPie**: User-friendly HTTP client

### Example curl Commands

```bash
# Register new user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123","confirm_password":"password123"}'

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"password123"}'

# Get posts (with token)
curl -X GET http://localhost:5000/api/v1/posts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Create post
curl -X POST http://localhost:5000/api/v1/posts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Post","content":"Post content here","category_id":1}'
```

## Production Considerations

### Performance
- Enable response caching for read-heavy endpoints
- Use database connection pooling
- Implement CDN for static file uploads
- Monitor API response times

### Monitoring
- Health check endpoint for load balancers
- Structured logging for debugging
- Error tracking and alerting
- API usage analytics

### Scaling
- Horizontal scaling with load balancers
- Database read replicas for read-heavy operations
- Redis clustering for session storage
- Microservices architecture for large deployments

## Support and Resources

### Documentation
- **Interactive Docs**: `/api/v1/docs/`
- **OpenAPI Spec**: `/api/v1/swagger.json`
- **This Guide**: `/api/v1/docs/guide`

### Contact
- **Email**: api-support@example.com
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

### Changelog
- **v1.0**: Initial API release with core functionality
- **v1.1**: Added file upload endpoints
- **v1.2**: Enhanced authentication and security features