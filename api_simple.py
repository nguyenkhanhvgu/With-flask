"""
Simplified REST API for Mobile App Integration
"""

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import jwt
import datetime

# Create API Blueprint
api = Blueprint('api', __name__, url_prefix='/api/v1')

# JWT Token utilities
def generate_token(user_id):
    """Generate JWT token for user authentication"""
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_token(token):
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require JWT token authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from app import User, db
        
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        user_id = verify_token(token)
        if user_id is None:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Get user and add to request context
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user') or not request.current_user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated

# Helper functions for JSON serialization
def user_to_dict(user, include_email=False):
    """Convert User object to dictionary"""
    data = {
        'id': user.id,
        'username': user.username,
        'avatar': f"/static/uploads/avatars/{user.avatar_filename}" if user.avatar_filename else None,
        'is_admin': user.is_admin,
        'created_at': user.created_at.isoformat(),
        'posts_count': len(user.posts),
        'comments_count': len(user.comments)
    }
    if include_email:
        data['email'] = user.email
    return data

def post_to_dict(post, include_content=True):
    """Convert Post object to dictionary"""
    data = {
        'id': post.id,
        'title': post.title,
        'author': user_to_dict(post.author),
        'category': {'id': post.category.id, 'name': post.category.name} if post.category else None,
        'image': f"/static/uploads/posts/{post.image_filename}" if post.image_filename else None,
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat(),
        'comments_count': len(post.comments)
    }
    if include_content:
        data['content'] = post.content
    return data

def comment_to_dict(comment):
    """Convert Comment object to dictionary"""
    return {
        'id': comment.id,
        'content': comment.content,
        'author': user_to_dict(comment.author),
        'post_id': comment.post_id,
        'created_at': comment.created_at.isoformat()
    }

def category_to_dict(category):
    """Convert Category object to dictionary"""
    return {
        'id': category.id,
        'name': category.name,
        'description': category.description,
        'posts_count': len(category.posts)
    }

# Health check endpoint
@api.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'timestamp': datetime.datetime.utcnow().isoformat()
    }), 200

# Authentication Endpoints
@api.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        from app import User, db
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user': user_to_dict(user, include_email=True)
        }), 201
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@api.route('/auth/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    try:
        from app import User
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Generate token
        token = generate_token(user.id)
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user_to_dict(user, include_email=True)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@api.route('/auth/verify', methods=['GET'])
@token_required
def verify_token_endpoint():
    """Verify if token is valid and return user info"""
    return jsonify({
        'valid': True,
        'user': user_to_dict(request.current_user, include_email=True)
    }), 200

# Posts Endpoints
@api.route('/posts', methods=['GET'])
def get_posts():
    """Get list of posts with optional filtering"""
    try:
        from app import Post
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        category_id = request.args.get('category_id', type=int)
        author_id = request.args.get('author_id', type=int)
        search = request.args.get('search', '').strip()
        
        query = Post.query
        
        # Apply filters
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        if author_id:
            query = query.filter_by(user_id=author_id)
        
        if search:
            query = query.filter(
                (Post.title.contains(search)) | 
                (Post.content.contains(search))
            )
        
        posts = query.order_by(Post.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'posts': [post_to_dict(post, include_content=False) for post in posts.items],
            'pagination': {
                'page': posts.page,
                'pages': posts.pages,
                'per_page': posts.per_page,
                'total': posts.total
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch posts: {str(e)}'}), 500

@api.route('/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Get specific post by ID with full content"""
    try:
        from app import Post
        
        post = Post.query.get_or_404(post_id)
        return jsonify({'post': post_to_dict(post)}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch post: {str(e)}'}), 500

@api.route('/posts', methods=['POST'])
@token_required
def create_post():
    """Create a new post"""
    try:
        from app import Post, Category, db
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        category_id = data.get('category_id')
        
        if not title or not content:
            return jsonify({'error': 'Title and content are required'}), 400
        
        # Validate category if provided
        if category_id:
            category = Category.query.get(category_id)
            if not category:
                return jsonify({'error': 'Invalid category'}), 400
        
        # Create post
        post = Post(
            title=title,
            content=content,
            user_id=request.current_user.id,
            category_id=category_id
        )
        
        db.session.add(post)
        db.session.commit()
        
        return jsonify({
            'message': 'Post created successfully',
            'post': post_to_dict(post)
        }), 201
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'error': f'Failed to create post: {str(e)}'}), 500

# Comments Endpoints
@api.route('/posts/<int:post_id>/comments', methods=['GET'])
def get_post_comments(post_id):
    """Get comments for a specific post"""
    try:
        from app import Post, Comment
        
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        post = Post.query.get_or_404(post_id)
        
        comments = Comment.query.filter_by(post_id=post_id).order_by(
            Comment.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'comments': [comment_to_dict(comment) for comment in comments.items],
            'pagination': {
                'page': comments.page,
                'pages': comments.pages,
                'per_page': comments.per_page,
                'total': comments.total
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch comments: {str(e)}'}), 500

@api.route('/posts/<int:post_id>/comments', methods=['POST'])
@token_required
def create_comment(post_id):
    """Create a new comment on a post"""
    try:
        from app import Post, Comment, db, send_comment_notification
        
        post = Post.query.get_or_404(post_id)
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content = data.get('content', '').strip()
        if not content:
            return jsonify({'error': 'Comment content is required'}), 400
        
        # Create comment
        comment = Comment(
            content=content,
            post_id=post_id,
            user_id=request.current_user.id
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # Send email notification to post author
        send_comment_notification(post, comment)
        
        return jsonify({
            'message': 'Comment created successfully',
            'comment': comment_to_dict(comment)
        }), 201
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'error': f'Failed to create comment: {str(e)}'}), 500

# Categories Endpoints
@api.route('/categories', methods=['GET'])
def get_categories():
    """Get list of all categories"""
    try:
        from app import Category
        
        categories = Category.query.order_by(Category.name).all()
        return jsonify({
            'categories': [category_to_dict(category) for category in categories]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch categories: {str(e)}'}), 500

# User Endpoints
@api.route('/users/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user's profile"""
    return jsonify({'user': user_to_dict(request.current_user, include_email=True)}), 200

# File Upload Endpoints
@api.route('/upload/avatar', methods=['POST'])
@token_required
def upload_avatar():
    """Upload user avatar"""
    try:
        from app import save_uploaded_file, db
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = save_uploaded_file(file, 'avatars')
        if not filename:
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Update user avatar
        user = request.current_user
        user.avatar_filename = filename
        db.session.commit()
        
        return jsonify({
            'message': 'Avatar uploaded successfully',
            'avatar_url': f"/static/uploads/avatars/{filename}"
        }), 200
        
    except Exception as e:
        from app import db
        db.session.rollback()
        return jsonify({'error': f'Failed to upload avatar: {str(e)}'}), 500

# Error handlers
@api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@api.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
