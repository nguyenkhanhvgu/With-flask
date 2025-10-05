# Role-Based Access Control Decorators Guide

This guide explains how to use the comprehensive set of role-based access control (RBAC) decorators implemented for the Flask blog application.

## Overview

The RBAC system provides fine-grained access control through:
- **Roles**: Groups of permissions (Administrator, Moderator, Editor, User)
- **Permissions**: Specific actions (create_posts, edit_all_posts, admin_access, etc.)
- **User Status**: Account states (active, confirmed, etc.)

## Available Decorators

### Basic Role Decorators

#### `@admin_required`
Requires administrator privileges (admin_access permission or legacy is_admin flag).

```python
from app.utils import admin_required

@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')
```

#### `@moderator_required`
Requires moderator privileges or higher (moderate_comments permission).

```python
from app.utils import moderator_required

@moderator_required
def moderate_comments():
    return render_template('admin/moderate.html')
```

### Permission-Based Decorators

#### `@permission_required(permission_name)`
Requires a specific permission.

```python
from app.utils import permission_required

@permission_required('create_posts')
def create_post():
    return render_template('blog/create_post.html')

@permission_required('edit_all_posts')
def edit_any_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('blog/edit_post.html', post=post)
```

#### `@multiple_permissions_required(*permissions, require_all=True)`
Requires multiple permissions with AND/OR logic.

```python
from app.utils import multiple_permissions_required

# User needs BOTH permissions
@multiple_permissions_required('create_posts', 'upload_files')
def create_post_with_image():
    return render_template('blog/create_post_with_image.html')

# User needs EITHER permission
@multiple_permissions_required('edit_own_posts', 'edit_all_posts', require_all=False)
def edit_post(post_id):
    return render_template('blog/edit_post.html')
```

### Role-Based Decorators

#### `@role_required(role_name)`
Requires a specific role.

```python
from app.utils import role_required

@role_required('Editor')
def editor_dashboard():
    return render_template('editor/dashboard.html')

@role_required('Administrator')
def system_settings():
    return render_template('admin/settings.html')
```

### User Status Decorators

#### `@active_required`
Requires an active user account.

```python
from app.utils import active_required

@active_required
def user_profile():
    return render_template('user/profile.html')
```

#### `@confirmed_required`
Requires email confirmation.

```python
from app.utils import confirmed_required

@confirmed_required
def premium_feature():
    return render_template('premium/feature.html')
```

#### `@active_and_confirmed_required`
Requires both active and confirmed status.

```python
from app.utils import active_and_confirmed_required

@active_and_confirmed_required
def sensitive_operation():
    return render_template('user/sensitive.html')
```

### API-Specific Decorators

#### `@api_permission_required(permission_name)`
For API endpoints - returns JSON responses instead of redirects.

```python
from app.utils import api_permission_required
from flask import jsonify

@api_permission_required('api_access')
def api_get_posts():
    posts = Post.query.all()
    return jsonify([post.to_dict() for post in posts])
```

#### `@api_role_required(role_name)`
For API endpoints requiring specific roles.

```python
from app.utils import api_role_required

@api_role_required('Administrator')
def api_admin_stats():
    return jsonify({'users': User.query.count(), 'posts': Post.query.count()})
```

### Advanced Access Control

#### `@owner_or_permission_required(permission_name, get_owner_id)`
Allows access if user owns the resource OR has permission.

```python
from app.utils import owner_or_permission_required

@owner_or_permission_required('edit_all_posts', 
                             lambda: Post.query.get(post_id).user_id)
def edit_post(post_id):
    # User can edit if they own the post OR have edit_all_posts permission
    post = Post.query.get_or_404(post_id)
    return render_template('blog/edit_post.html', post=post)
```

### Enhanced Login Decorator

#### `@login_required_with_message(message, category)`
Custom login required with personalized messages.

```python
from app.utils import login_required_with_message

@login_required_with_message("Please log in to create posts.", "info")
def create_post():
    return render_template('blog/create_post.html')
```

## Usage Examples

### Blog Post Management

```python
from flask import Blueprint, render_template, request, flash, redirect, url_for
from app.utils import permission_required, owner_or_permission_required
from app.models import Post

blog = Blueprint('blog', __name__)

@blog.route('/posts/create', methods=['GET', 'POST'])
@permission_required('create_posts')
def create_post():
    if request.method == 'POST':
        # Create post logic
        pass
    return render_template('blog/create_post.html')

@blog.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@owner_or_permission_required('edit_all_posts', 
                             lambda: Post.query.get(post_id).user_id)
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if request.method == 'POST':
        # Edit post logic
        pass
    return render_template('blog/edit_post.html', post=post)

@blog.route('/posts/<int:post_id>/delete', methods=['POST'])
@owner_or_permission_required('delete_all_posts',
                             lambda: Post.query.get(post_id).user_id)
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    # Delete post logic
    return redirect(url_for('blog.posts'))
```

### Admin Panel

```python
from flask import Blueprint
from app.utils import admin_required, moderator_required, permission_required

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/dashboard')
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

@admin.route('/users')
@permission_required('manage_users')
def manage_users():
    return render_template('admin/users.html')

@admin.route('/moderate')
@moderator_required
def moderate_content():
    return render_template('admin/moderate.html')
```

### API Endpoints

```python
from flask import Blueprint, jsonify
from app.utils import api_permission_required, api_role_required

api = Blueprint('api', __name__, url_prefix='/api/v1')

@api.route('/posts')
@api_permission_required('api_access')
def get_posts():
    posts = Post.query.all()
    return jsonify([post.to_dict() for post in posts])

@api.route('/admin/stats')
@api_role_required('Administrator')
def admin_stats():
    return jsonify({
        'users': User.query.count(),
        'posts': Post.query.count(),
        'comments': Comment.query.count()
    })
```

## Default Permissions

The system includes these default permissions:

- `read_posts` - Can read blog posts
- `create_posts` - Can create blog posts
- `edit_own_posts` - Can edit own blog posts
- `edit_all_posts` - Can edit any blog post
- `delete_own_posts` - Can delete own blog posts
- `delete_all_posts` - Can delete any blog post
- `create_comments` - Can create comments
- `edit_own_comments` - Can edit own comments
- `edit_all_comments` - Can edit any comment
- `delete_own_comments` - Can delete own comments
- `delete_all_comments` - Can delete any comment
- `moderate_comments` - Can moderate comments
- `manage_categories` - Can manage post categories
- `manage_users` - Can manage user accounts
- `view_analytics` - Can view site analytics
- `admin_access` - Full administrative access
- `api_access` - Can access API endpoints
- `upload_files` - Can upload files
- `manage_roles` - Can manage roles and permissions
- `send_notifications` - Can send notifications to users

## Default Roles

The system includes these default roles:

### User (Default)
- `read_posts`, `create_posts`, `edit_own_posts`, `delete_own_posts`
- `create_comments`, `edit_own_comments`, `delete_own_comments`
- `upload_files`

### Moderator
- All User permissions plus:
- `edit_all_comments`, `delete_all_comments`, `moderate_comments`
- `view_analytics`

### Editor
- All Moderator permissions plus:
- `edit_all_posts`, `manage_categories`
- `api_access`

### Administrator
- All permissions (full access)

## Error Handling

The decorators provide appropriate error responses:

### Web Requests
- Redirects to login page for unauthenticated users
- Redirects to home page with error message for insufficient permissions
- Flash messages explain the required permissions/roles

### API Requests
- Returns JSON error responses with appropriate HTTP status codes
- 401 for authentication required
- 403 for insufficient permissions
- Includes details about required permissions/roles

## Best Practices

1. **Use Permission-Based Decorators**: Prefer `@permission_required()` over role-based decorators for flexibility.

2. **Combine with Owner Checks**: Use `@owner_or_permission_required()` for resources users can modify their own content.

3. **API vs Web Decorators**: Use `@api_permission_required()` for API endpoints to get JSON responses.

4. **Multiple Permissions**: Use `@multiple_permissions_required()` when operations need multiple capabilities.

5. **User Status Checks**: Always use `@active_required` or `@active_and_confirmed_required` for sensitive operations.

6. **Graceful Degradation**: Provide clear error messages and appropriate redirects.

## Testing

The decorators can be tested using Flask's test client:

```python
def test_admin_required(client, admin_user):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_user.id)
    
    response = client.get('/admin/dashboard')
    assert response.status_code == 200

def test_permission_required(client, user_with_permission):
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_with_permission.id)
    
    response = client.post('/posts/create')
    assert response.status_code == 200
```

This comprehensive RBAC system provides fine-grained access control while maintaining flexibility and ease of use.