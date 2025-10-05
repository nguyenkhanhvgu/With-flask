# Flask-RESTful API Documentation

## Overview

This REST API provides comprehensive mobile app integration for the Flask blog application. The API has been completely restructured using Flask-RESTful for better organization, consistency, and maintainability. It uses JWT (JSON Web Tokens) for authentication and follows RESTful conventions with proper HTTP status codes and error handling.

**Base URL:** `http://localhost:5000/api/v1`

> **Note**: The API has been migrated from the old single-file implementation (`api.py`) to a new Flask-RESTful structure. All endpoints remain backward compatible, but the new implementation provides better error handling, validation, and maintainability.

## New Flask-RESTful Architecture

The API has been completely restructured using Flask-RESTful for better maintainability and consistency:

### Architecture Improvements

- **Flask-RESTful Resources**: Each endpoint is implemented as a proper RESTful resource class
- **Modular Organization**: Resources are organized by functionality in separate files:
  - `auth_resources.py` - Authentication endpoints
  - `user_resources.py` - User management
  - `post_resources.py` - Blog post operations
  - `comment_resources.py` - Comment management
  - `category_resources.py` - Category operations
  - `admin_resources.py` - Admin-only endpoints
  - `utility_resources.py` - File uploads and utilities
- **Base Resource Class**: Common functionality shared across all resources
- **Consistent Error Handling**: Standardized error responses with proper HTTP status codes
- **Enhanced Validation**: Improved input validation with detailed error messages
- **Security Enhancements**: Better JWT token handling and permission checks

### Key Benefits

1. **Better Code Organization**: Easier to maintain and extend
2. **Consistent API Design**: All endpoints follow the same patterns
3. **Improved Error Handling**: More informative error messages
4. **Enhanced Security**: Better authentication and authorization
5. **Educational Value**: Demonstrates Flask-RESTful best practices

## Authentication

The API uses JWT tokens for authentication with improved security and error handling. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

### Token Features

- **Expiration**: Tokens are valid for 7 days
- **Security**: Tokens are signed with the application's secret key
- **Validation**: Comprehensive token validation with proper error messages
- **User Context**: Tokens include user ID and are validated against active users

### Obtaining a Token

Use the `/auth/login` endpoint to get a JWT token after registering. The new implementation provides better error messages and validation.

## API Endpoints

### Authentication Endpoints

#### Register User
- **POST** `/auth/register`
- **Description:** Register a new user account
- **Auth Required:** No

**Request Body:**
```json
{
    "username": "string (required)",
    "email": "string (required)",
    "password": "string (required, min 6 chars)"
}
```

**Response (201):**
```json
{
    "message": "User registered successfully",
    "token": "jwt-token-string",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "avatar": null,
        "is_admin": false,
        "created_at": "2024-01-01T12:00:00",
        "posts_count": 0,
        "comments_count": 0
    }
}
```

#### Login
- **POST** `/auth/login`
- **Description:** Authenticate and get JWT token
- **Auth Required:** No

**Request Body:**
```json
{
    "username": "string (username or email)",
    "password": "string"
}
```

**Response (200):**
```json
{
    "message": "Login successful",
    "token": "jwt-token-string",
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "avatar": "/static/uploads/avatars/avatar.jpg",
        "is_admin": false,
        "created_at": "2024-01-01T12:00:00",
        "posts_count": 5,
        "comments_count": 12
    }
}
```

#### Verify Token
- **GET** `/auth/verify`
- **Description:** Verify if token is valid
- **Auth Required:** Yes

**Response (200):**
```json
{
    "valid": true,
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "avatar": "/static/uploads/avatars/avatar.jpg",
        "is_admin": false,
        "created_at": "2024-01-01T12:00:00",
        "posts_count": 5,
        "comments_count": 12
    }
}
```

### User Endpoints

#### Get All Users
- **GET** `/users`
- **Description:** Get paginated list of active users
- **Auth Required:** No
- **Query Parameters:**
  - `page` (int, default: 1)
  - `per_page` (int, default: 20, max: 100)

**Response (200):**
```json
{
    "users": [
        {
            "id": 1,
            "username": "john_doe",
            "avatar": "/static/uploads/avatars/avatar.jpg",
            "is_admin": false,
            "created_at": "2024-01-01T12:00:00",
            "posts_count": 5,
            "comments_count": 12
        }
    ],
    "pagination": {
        "page": 1,
        "pages": 3,
        "per_page": 20,
        "total": 50
    }
}
```

#### Get User by ID
- **GET** `/users/{user_id}`
- **Description:** Get specific user information
- **Auth Required:** No

**Response (200):**
```json
{
    "user": {
        "id": 1,
        "username": "john_doe",
        "avatar": "/static/uploads/avatars/avatar.jpg",
        "is_admin": false,
        "created_at": "2024-01-01T12:00:00",
        "posts_count": 5,
        "comments_count": 12
    }
}
```

#### Get Current User Profile
- **GET** `/users/profile`
- **Description:** Get current user's profile
- **Auth Required:** Yes

**Response (200):**
```json
{
    "user": {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "avatar": "/static/uploads/avatars/avatar.jpg",
        "is_admin": false,
        "created_at": "2024-01-01T12:00:00",
        "posts_count": 5,
        "comments_count": 12
    }
}
```

#### Update Profile
- **PUT** `/users/profile`
- **Description:** Update current user's profile
- **Auth Required:** Yes

**Request Body:**
```json
{
    "username": "new_username (optional)",
    "email": "new@email.com (optional)"
}
```

**Response (200):**
```json
{
    "message": "Profile updated successfully",
    "user": {
        "id": 1,
        "username": "new_username",
        "email": "new@email.com",
        "avatar": "/static/uploads/avatars/avatar.jpg",
        "is_admin": false,
        "created_at": "2024-01-01T12:00:00",
        "posts_count": 5,
        "comments_count": 12
    }
}
```

### Post Endpoints

#### Get All Posts
- **GET** `/posts`
- **Description:** Get paginated list of posts with filtering
- **Auth Required:** No
- **Query Parameters:**
  - `page` (int, default: 1)
  - `per_page` (int, default: 20, max: 100)
  - `category_id` (int, optional)
  - `author_id` (int, optional)
  - `search` (string, optional)

**Response (200):**
```json
{
    "posts": [
        {
            "id": 1,
            "title": "My First Post",
            "author": {
                "id": 1,
                "username": "john_doe",
                "avatar": "/static/uploads/avatars/avatar.jpg",
                "is_admin": false,
                "created_at": "2024-01-01T12:00:00",
                "posts_count": 5,
                "comments_count": 12
            },
            "category": {
                "id": 1,
                "name": "Technology"
            },
            "image": "/static/uploads/posts/image.jpg",
            "created_at": "2024-01-01T12:00:00",
            "updated_at": "2024-01-01T12:00:00",
            "comments_count": 3
        }
    ],
    "pagination": {
        "page": 1,
        "pages": 5,
        "per_page": 20,
        "total": 95
    }
}
```

#### Get Post by ID
- **GET** `/posts/{post_id}`
- **Description:** Get specific post with full content
- **Auth Required:** No

**Response (200):**
```json
{
    "post": {
        "id": 1,
        "title": "My First Post",
        "content": "This is the full content of the post...",
        "author": {
            "id": 1,
            "username": "john_doe",
            "avatar": "/static/uploads/avatars/avatar.jpg",
            "is_admin": false,
            "created_at": "2024-01-01T12:00:00",
            "posts_count": 5,
            "comments_count": 12
        },
        "category": {
            "id": 1,
            "name": "Technology"
        },
        "image": "/static/uploads/posts/image.jpg",
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:00:00",
        "comments_count": 3
    }
}
```

#### Create Post
- **POST** `/posts`
- **Description:** Create a new blog post
- **Auth Required:** Yes

**Request Body:**
```json
{
    "title": "string (required)",
    "content": "string (required)",
    "category_id": "int (optional)"
}
```

**Response (201):**
```json
{
    "message": "Post created successfully",
    "post": {
        "id": 2,
        "title": "New Post",
        "content": "Post content...",
        "author": {
            "id": 1,
            "username": "john_doe",
            "avatar": "/static/uploads/avatars/avatar.jpg",
            "is_admin": false,
            "created_at": "2024-01-01T12:00:00",
            "posts_count": 6,
            "comments_count": 12
        },
        "category": {
            "id": 1,
            "name": "Technology"
        },
        "image": null,
        "created_at": "2024-01-01T13:00:00",
        "updated_at": "2024-01-01T13:00:00",
        "comments_count": 0
    }
}
```

#### Update Post
- **PUT** `/posts/{post_id}`
- **Description:** Update existing post (owner or admin only)
- **Auth Required:** Yes

**Request Body:**
```json
{
    "title": "string (optional)",
    "content": "string (optional)",
    "category_id": "int (optional)"
}
```

**Response (200):**
```json
{
    "message": "Post updated successfully",
    "post": {
        "id": 1,
        "title": "Updated Post Title",
        "content": "Updated content...",
        "author": {
            "id": 1,
            "username": "john_doe",
            "avatar": "/static/uploads/avatars/avatar.jpg",
            "is_admin": false,
            "created_at": "2024-01-01T12:00:00",
            "posts_count": 6,
            "comments_count": 12
        },
        "category": {
            "id": 2,
            "name": "Programming"
        },
        "image": "/static/uploads/posts/image.jpg",
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T14:00:00",
        "comments_count": 3
    }
}
```

#### Delete Post
- **DELETE** `/posts/{post_id}`
- **Description:** Delete a post (owner or admin only)
- **Auth Required:** Yes

**Response (200):**
```json
{
    "message": "Post deleted successfully"
}
```

### Comment Endpoints

#### Get Post Comments
- **GET** `/posts/{post_id}/comments`
- **Description:** Get paginated comments for a specific post
- **Auth Required:** No
- **Query Parameters:**
  - `page` (int, default: 1)
  - `per_page` (int, default: 50, max: 100)

**Response (200):**
```json
{
    "comments": [
        {
            "id": 1,
            "content": "Great post!",
            "author": {
                "id": 2,
                "username": "jane_doe",
                "avatar": "/static/uploads/avatars/jane.jpg",
                "is_admin": false,
                "created_at": "2024-01-01T11:00:00",
                "posts_count": 2,
                "comments_count": 8
            },
            "post_id": 1,
            "created_at": "2024-01-01T13:30:00"
        }
    ],
    "pagination": {
        "page": 1,
        "pages": 1,
        "per_page": 50,
        "total": 3
    }
}
```

#### Create Comment
- **POST** `/posts/{post_id}/comments`
- **Description:** Add a new comment to a post
- **Auth Required:** Yes

**Request Body:**
```json
{
    "content": "string (required)"
}
```

**Response (201):**
```json
{
    "message": "Comment created successfully",
    "comment": {
        "id": 2,
        "content": "This is my comment",
        "author": {
            "id": 1,
            "username": "john_doe",
            "avatar": "/static/uploads/avatars/avatar.jpg",
            "is_admin": false,
            "created_at": "2024-01-01T12:00:00",
            "posts_count": 6,
            "comments_count": 13
        },
        "post_id": 1,
        "created_at": "2024-01-01T15:00:00"
    }
}
```

#### Delete Comment
- **DELETE** `/comments/{comment_id}`
- **Description:** Delete a comment (owner or admin only)
- **Auth Required:** Yes

**Response (200):**
```json
{
    "message": "Comment deleted successfully"
}
```

### Category Endpoints

#### Get All Categories
- **GET** `/categories`
- **Description:** Get list of all categories
- **Auth Required:** No

**Response (200):**
```json
{
    "categories": [
        {
            "id": 1,
            "name": "Technology",
            "description": "Posts about technology and programming",
            "posts_count": 15
        },
        {
            "id": 2,
            "name": "Lifestyle",
            "description": "Posts about lifestyle and personal experiences",
            "posts_count": 8
        }
    ]
}
```

#### Create Category
- **POST** `/categories`
- **Description:** Create a new category (admin only)
- **Auth Required:** Yes (Admin)

**Request Body:**
```json
{
    "name": "string (required)",
    "description": "string (optional)"
}
```

**Response (201):**
```json
{
    "message": "Category created successfully",
    "category": {
        "id": 3,
        "name": "Science",
        "description": "Scientific articles and discoveries",
        "posts_count": 0
    }
}
```

### File Upload Endpoints

#### Upload Avatar
- **POST** `/upload/avatar`
- **Description:** Upload user avatar image
- **Auth Required:** Yes
- **Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: Image file (jpg, jpeg, png, gif, webp)

**Response (200):**
```json
{
    "message": "Avatar uploaded successfully",
    "avatar_url": "/static/uploads/avatars/uuid-filename.jpg"
}
```

#### Upload Post Image
- **POST** `/upload/post-image`
- **Description:** Upload image for blog post
- **Auth Required:** Yes
- **Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: Image file (jpg, jpeg, png, gif, webp)

**Response (200):**
```json
{
    "message": "Image uploaded successfully",
    "image_url": "/static/uploads/posts/uuid-filename.jpg",
    "filename": "uuid-filename.jpg"
}
```

### Admin Endpoints

#### Get Admin Stats
- **GET** `/admin/stats`
- **Description:** Get dashboard statistics (admin only)
- **Auth Required:** Yes (Admin)

**Response (200):**
```json
{
    "stats": {
        "total_users": 50,
        "active_users": 48,
        "total_posts": 95,
        "total_comments": 287,
        "total_categories": 5,
        "recent_users": [
            {
                "id": 50,
                "username": "new_user",
                "avatar": null,
                "is_admin": false,
                "created_at": "2024-01-01T14:00:00",
                "posts_count": 0,
                "comments_count": 0
            }
        ],
        "recent_posts": [
            {
                "id": 95,
                "title": "Latest Post",
                "author": {
                    "id": 10,
                    "username": "author",
                    "avatar": "/static/uploads/avatars/author.jpg",
                    "is_admin": false,
                    "created_at": "2024-01-01T10:00:00",
                    "posts_count": 12,
                    "comments_count": 45
                },
                "category": {
                    "id": 1,
                    "name": "Technology"
                },
                "image": null,
                "created_at": "2024-01-01T15:30:00",
                "updated_at": "2024-01-01T15:30:00",
                "comments_count": 0
            }
        ]
    }
}
```

### Utility Endpoints

#### Health Check
- **GET** `/health`
- **Description:** API health check
- **Auth Required:** No

**Response (200):**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-01-01T12:00:00"
}
```

## Error Responses

All endpoints return consistent error responses with improved messaging:

**400 Bad Request:**
```json
{
    "error": "No JSON data provided" | "Empty data provided" | "Username, email, and password are required" | "Title and content are required"
}
```

**401 Unauthorized:**
```json
{
    "error": "Token is missing" | "Token is invalid or expired" | "Invalid credentials" | "Invalid token format" | "User not found or inactive"
}
```

**403 Forbidden:**
```json
{
    "error": "Permission denied" | "Admin privileges required"
}
```

**404 Not Found:**
```json
{
    "error": "Resource not found"
}
```

**405 Method Not Allowed:**
```json
{
    "error": "Method not allowed"
}
```

**500 Internal Server Error:**
```json
{
    "error": "Internal server error" | "Registration failed: <details>" | "Login failed: <details>" | "Failed to create post: <details>"
}
```

## Improved Error Handling

The new Flask-RESTful implementation provides:

- **Consistent Format**: All errors follow the same JSON structure
- **Detailed Messages**: More specific error descriptions for better debugging
- **Proper Status Codes**: Appropriate HTTP status codes for different error types
- **Exception Handling**: Graceful handling of unexpected errors with rollback
- **Validation Errors**: Clear messages for input validation failures
- **Security**: Sanitized error messages that don't expose sensitive information

## Rate Limiting

Currently, there are no rate limits implemented. In production, consider implementing rate limiting based on:
- IP address
- User ID
- API key

## Security Considerations

1. **JWT Tokens**: Tokens expire after 7 days by default
2. **Password Security**: Passwords are hashed using Werkzeug's security functions
3. **File Uploads**: Only specific image formats are allowed
4. **Input Validation**: All inputs are validated and sanitized
5. **HTTPS**: Use HTTPS in production
6. **CORS**: Configure CORS headers for cross-origin requests

## Sample Mobile App Integration

### JavaScript/React Native Example

```javascript
class BlogAPI {
    constructor(baseURL = 'http://localhost:5000/api/v1') {
        this.baseURL = baseURL;
        this.token = null;
    }

    setToken(token) {
        this.token = token;
    }

    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        const response = await fetch(url, {
            ...options,
            headers
        });

        return response.json();
    }

    // Authentication
    async login(username, password) {
        const response = await this.request('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        if (response.token) {
            this.setToken(response.token);
        }
        
        return response;
    }

    async register(username, email, password) {
        return this.request('/auth/register', {
            method: 'POST',
            body: JSON.stringify({ username, email, password })
        });
    }

    // Posts
    async getPosts(page = 1, filters = {}) {
        const params = new URLSearchParams({ page, ...filters });
        return this.request(`/posts?${params}`);
    }

    async getPost(postId) {
        return this.request(`/posts/${postId}`);
    }

    async createPost(postData) {
        return this.request('/posts', {
            method: 'POST',
            body: JSON.stringify(postData)
        });
    }

    // Comments
    async getComments(postId, page = 1) {
        return this.request(`/posts/${postId}/comments?page=${page}`);
    }

    async createComment(postId, content) {
        return this.request(`/posts/${postId}/comments`, {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }

    // File Upload
    async uploadAvatar(file) {
        const formData = new FormData();
        formData.append('file', file);

        return this.request('/upload/avatar', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
                // Don't set Content-Type, let browser set it for FormData
            },
            body: formData
        });
    }
}

// Usage
const api = new BlogAPI();

// Login
api.login('username', 'password').then(response => {
    console.log('Logged in:', response.user);
});

// Get posts
api.getPosts(1, { category_id: 1 }).then(response => {
    console.log('Posts:', response.posts);
});
```

## Testing the API

You can test the API using tools like:
- **Postman**: Import the endpoints and test them
- **cURL**: Command-line testing
- **HTTPie**: User-friendly HTTP client
- **Insomnia**: API testing tool

### Example cURL Commands

```bash
# Register
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'

# Get posts (with token)
curl -X GET http://localhost:5000/api/v1/posts \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Create post
curl -X POST http://localhost:5000/api/v1/posts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"title": "My Post", "content": "Post content here"}'

# Health check (new endpoint)
curl -X GET http://localhost:5000/api/v1/health
```

## Migration from Legacy API

The API has been migrated from the old `api.py` implementation to a new Flask-RESTful structure. Here are the key changes:

### What's New

1. **Flask-RESTful Implementation**: All endpoints now use proper RESTful resource classes
2. **Better Error Handling**: More specific error messages and proper HTTP status codes
3. **Improved Validation**: Enhanced input validation with detailed feedback
4. **Modular Structure**: Code is organized in separate files by functionality
5. **Enhanced Security**: Better JWT token handling and permission checks
6. **Health Check Endpoint**: New `/health` endpoint for monitoring
7. **Consistent Response Format**: All endpoints follow the same response patterns

### Backward Compatibility

- All existing endpoints remain functional
- Request/response formats are unchanged
- Authentication mechanism is the same
- No breaking changes for existing clients

### Recommended Migration

While the old API endpoints still work, it's recommended to:
1. Update base URLs if needed
2. Implement proper error handling for the new error formats
3. Take advantage of the improved validation messages
4. Use the new health check endpoint for monitoring

This REST API provides comprehensive mobile app integration capabilities while maintaining security and following modern Flask development best practices.
