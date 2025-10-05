# Flask-RESTful API Documentation

This directory contains the Flask-RESTful API implementation for the blog application. The API provides a clean, RESTful interface for all blog functionality with proper HTTP status codes, error handling, and JWT authentication.

## Architecture

The API is organized using Flask-RESTful resources with the following structure:

```
app/blueprints/api/
├── __init__.py              # Blueprint registration and resource routing
├── base.py                  # Base classes and utilities
├── auth_resources.py        # Authentication endpoints
├── user_resources.py        # User management endpoints
├── post_resources.py        # Blog post endpoints
├── comment_resources.py     # Comment endpoints
├── category_resources.py    # Category endpoints
├── admin_resources.py       # Admin-only endpoints
├── utility_resources.py     # File uploads and utilities
├── error_handlers.py        # API error handlers
└── README.md               # This documentation
```

## Key Features

### 1. RESTful Design
- Proper HTTP methods (GET, POST, PUT, DELETE)
- Consistent URL patterns
- Appropriate HTTP status codes
- JSON request/response format

### 2. Authentication
- JWT token-based authentication
- Token verification middleware
- Role-based access control
- Secure password handling

### 3. Error Handling
- Consistent error response format
- Proper HTTP status codes
- Detailed error messages
- Exception handling

### 4. Input Validation
- Request data validation
- JSON schema validation
- Sanitized input handling
- Proper error responses for invalid data

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/verify` - Token verification

### Users
- `GET /api/v1/users` - List all users (paginated)
- `GET /api/v1/users/<id>` - Get specific user
- `GET /api/v1/users/profile` - Get current user profile (authenticated)
- `PUT /api/v1/users/profile` - Update current user profile (authenticated)

### Posts
- `GET /api/v1/posts` - List all posts (paginated, filterable)
- `GET /api/v1/posts/<id>` - Get specific post
- `POST /api/v1/posts` - Create new post (authenticated)
- `PUT /api/v1/posts/<id>` - Update post (authenticated, owner/admin)
- `DELETE /api/v1/posts/<id>` - Delete post (authenticated, owner/admin)

### Comments
- `GET /api/v1/posts/<id>/comments` - Get comments for a post
- `POST /api/v1/posts/<id>/comments` - Add comment to post (authenticated)
- `DELETE /api/v1/comments/<id>` - Delete comment (authenticated, owner/admin)

### Categories
- `GET /api/v1/categories` - List all categories
- `POST /api/v1/categories` - Create category (admin only)

### Admin
- `GET /api/v1/admin/stats` - Get dashboard statistics (admin only)

### Utilities
- `GET /api/v1/health` - API health check
- `POST /api/v1/upload/avatar` - Upload user avatar (authenticated)
- `POST /api/v1/upload/post-image` - Upload post image (authenticated)

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. To access protected endpoints:

1. Register or login to get a JWT token
2. Include the token in the Authorization header: `Bearer <token>`
3. The token is valid for 7 days

Example:
```bash
# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# Use token for authenticated requests
curl -X GET http://localhost:5000/api/v1/users/profile \
  -H "Authorization: Bearer <your-jwt-token>"
```

## Error Responses

All errors follow a consistent format:

```json
{
  "error": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation errors)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

## Pagination

List endpoints support pagination with query parameters:
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20, max: 100)

Response includes pagination metadata:
```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "pages": 5,
    "per_page": 20,
    "total": 100
  }
}
```

## Filtering

Posts endpoint supports filtering:
- `category_id` - Filter by category
- `author_id` - Filter by author
- `search` - Search in title and content

Example: `GET /api/v1/posts?category_id=1&search=flask`

## Learning Objectives

This API implementation demonstrates:

1. **Flask-RESTful Usage**: How to structure APIs using Flask-RESTful resources
2. **Authentication Patterns**: JWT token implementation and middleware
3. **Error Handling**: Consistent error responses and HTTP status codes
4. **Input Validation**: Proper request validation and sanitization
5. **Code Organization**: Modular resource organization and separation of concerns
6. **Security Best Practices**: Token-based auth, permission checks, input validation
7. **API Design**: RESTful principles and consistent interface design

## Migration from Old API

The old API (`api.py`) has been replaced with this new Flask-RESTful structure. Key improvements:

1. **Better Organization**: Resources are organized in separate files by functionality
2. **Consistent Error Handling**: All endpoints use the same error response format
3. **Proper HTTP Methods**: Resources use appropriate HTTP methods for different operations
4. **Improved Validation**: Better input validation and error messages
5. **Modular Design**: Easier to extend and maintain

The old API endpoints remain functional but should be migrated to use the new structure for better maintainability and consistency.