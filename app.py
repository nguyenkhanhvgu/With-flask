from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from PIL import Image
import os
import uuid
import threading

# Create Flask application instance
app = Flask(__name__)

# Enhanced session configuration for proper authentication
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production-flask-learning-app-2024'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_NAME'] = 'flask_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# File upload configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['UPLOAD_PATH'] = os.path.join(basedir, 'static', 'uploads')

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'Flask Blog <noreply@flaskblog.com>')
app.config['ADMIN_EMAIL'] = os.environ.get('ADMIN_EMAIL', 'admin@flaskblog.com')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "blog.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database and migration
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize Flask-Mail
mail = Mail(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    print(f"DEBUG: user_loader called with user_id: {user_id}")
    user = User.query.get(int(user_id))
    print(f"DEBUG: user_loader found user: {bool(user)}")
    if user:
        print(f"DEBUG: user_loader username: {user.username}")
    return user

# Template filters
@app.template_filter('nl2br')
def nl2br_filter(text):
    """Convert newlines to HTML line breaks"""
    return text.replace('\n', '<br>\n') if text else ''

app.jinja_env.filters['nl2br'] = nl2br_filter

# File upload utility functions
def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in [ext[1:] for ext in app.config['UPLOAD_EXTENSIONS']]

def save_uploaded_file(file, upload_type='posts'):
    """Save uploaded file with unique name and return filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        file_ext = os.path.splitext(secure_filename(file.filename))[1]
        unique_filename = str(uuid.uuid4()) + file_ext
        
        # Create upload directory if it doesn't exist
        upload_dir = os.path.join(app.config['UPLOAD_PATH'], upload_type)
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save original file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # Resize image if it's too large
        try:
            with Image.open(file_path) as img:
                # Resize for posts (max 800px width) or avatars (max 300px)
                max_size = (300, 300) if upload_type == 'avatars' else (800, 600)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                img.save(file_path, optimize=True, quality=85)
        except Exception as e:
            print(f"Error resizing image: {e}")
        
        return unique_filename
    return None

# Admin utility functions
def admin_required(f):
    """Decorator to require admin access"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Email utility functions
def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        try:
            mail.send(msg)
            print(f"Email sent successfully to {msg.recipients}")
        except Exception as e:
            print(f"Failed to send email: {e}")

def send_email(subject, recipients, text_body, html_body=None):
    """Send email with optional HTML body"""
    if not app.config['MAIL_USERNAME']:
        print("Email not configured - skipping email notification")
        return
    
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    if html_body:
        msg.html = html_body
    
    # Send email in background thread
    thread = threading.Thread(target=send_async_email, args=(app, msg))
    thread.start()

def send_comment_notification(post, comment):
    """Send email notification to post author when someone comments"""
    if post.author.email and post.author.email != comment.author.email:
        subject = f'New comment on your post: "{post.title}"'
        
        text_body = f'''Hi {post.author.username},

Someone left a comment on your post "{post.title}".

Comment by: {comment.author.username}
Comment: {comment.content[:200]}{'...' if len(comment.content) > 200 else ''}

View the full comment and reply at: {url_for('post_detail', id=post.id, _external=True)}

Best regards,
Flask Blog Team
'''
        
        html_body = f'''
        <h3>New comment on your post!</h3>
        <p>Hi <strong>{post.author.username}</strong>,</p>
        <p>Someone left a comment on your post "<strong>{post.title}</strong>".</p>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
            <p><strong>Comment by:</strong> {comment.author.username}</p>
            <p><strong>Comment:</strong></p>
            <p style="font-style: italic;">"{comment.content[:200]}{'...' if len(comment.content) > 200 else ''}"</p>
        </div>
        
        <p><a href="{url_for('post_detail', id=post.id, _external=True)}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Comment & Reply</a></p>
        
        <p>Best regards,<br>Flask Blog Team</p>
        '''
        
        send_email(subject, [post.author.email], text_body, html_body)

# Database Models
class User(db.Model, UserMixin):
    """User model for blog authors and commenters"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar_filename = db.Column(db.String(255), nullable=True, default='default-avatar.png')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set the user's password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Required by Flask-Login"""
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Category(db.Model):
    """Category model for organizing posts"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    posts = db.relationship('Post', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Post(db.Model):
    """Blog post model"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Post {self.title}>'

class Comment(db.Model):
    """Comment model for post feedback"""
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Comment {self.id}>'

# Routes
@app.route('/')
def home():
    """Render the home page with recent posts"""
    # Get recent posts from database
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    return render_template('index.html', title='Flask Learning App', posts=recent_posts)

# Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not email or not password:
            flash('Please fill in all fields.', 'error')
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
        elif User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
        else:
            # Create new user
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))
    
    return render_template('register.html', title='Register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        print(f"DEBUG: User already authenticated: {current_user.username}")
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        print(f"DEBUG: Login attempt - Username: {username}, Password provided: {bool(password)}")
        
        if not username or not password:
            flash('Please provide both username and password.', 'error')
        else:
            user = User.query.filter_by(username=username).first()
            print(f"DEBUG: User found: {bool(user)}")
            
            if user:
                print(f"DEBUG: User password hash exists: {bool(user.password_hash)}")
                password_check = user.check_password(password)
                print(f"DEBUG: Password check result: {password_check}")
                
                if password_check:
                    # Make session permanent for persistent login
                    session.permanent = True
                    login_user(user, remember=remember, duration=timedelta(days=7))
                    print(f"DEBUG: User logged in successfully: {current_user.is_authenticated}")
                    print(f"DEBUG: Session permanent: {session.permanent}")
                    print(f"DEBUG: Session contents: {dict(session)}")
                    
                    next_page = request.args.get('next')
                    flash(f'Welcome back, {user.username}!', 'success')
                    return redirect(next_page) if next_page else redirect(url_for('home'))
                else:
                    print(f"DEBUG: Password check failed for user: {username}")
                    flash('Invalid username or password.', 'error')
            else:
                print(f"DEBUG: No user found with username: {username}")
                flash('Invalid username or password.', 'error')
    
    return render_template('login.html', title='Login')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username
    logout_user()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page with avatar upload"""
    if request.method == 'POST':
        avatar_file = request.files.get('avatar')
        
        if avatar_file and avatar_file.filename:
            # Save new avatar
            avatar_filename = save_uploaded_file(avatar_file, 'avatars')
            if avatar_filename:
                # Update user's avatar
                current_user.avatar_filename = avatar_filename
                db.session.commit()
                flash('Avatar updated successfully!', 'success')
            else:
                flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
        
        return redirect(url_for('profile'))
    
    # Get user's posts
    user_posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.created_at.desc()).all()
    
    return render_template('profile.html', title='My Profile', user=current_user, posts=user_posts)

# Admin Routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with site statistics"""
    # Get statistics
    total_users = User.query.count()
    total_posts = Post.query.count()
    total_comments = Comment.query.count()
    total_categories = Category.query.count()
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_posts = Post.query.order_by(Post.created_at.desc()).limit(5).all()
    recent_comments = Comment.query.order_by(Comment.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         title='Admin Dashboard',
                         total_users=total_users,
                         total_posts=total_posts,
                         total_comments=total_comments,
                         total_categories=total_categories,
                         recent_users=recent_users,
                         recent_posts=recent_posts,
                         recent_comments=recent_comments)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/users.html', title='Manage Users', users=users)

@app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def toggle_user_admin(user_id):
    """Toggle admin status for a user"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot change your own admin status.', 'error')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        status = 'promoted to admin' if user.is_admin else 'removed from admin'
        flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/toggle-active', methods=['POST'])
@login_required
@admin_required
def toggle_user_active(user_id):
    """Toggle active status for a user"""
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own account.', 'error')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/posts')
@login_required
@admin_required
def admin_posts():
    """Manage posts"""
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/posts.html', title='Manage Posts', posts=posts)

@app.route('/admin/posts/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_post(post_id):
    """Delete a post"""
    post = Post.query.get_or_404(post_id)
    post_title = post.title
    db.session.delete(post)
    db.session.commit()
    flash(f'Post "{post_title}" has been deleted.', 'success')
    return redirect(url_for('admin_posts'))

@app.route('/admin/comments')
@login_required
@admin_required
def admin_comments():
    """Manage comments"""
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.order_by(Comment.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )
    return render_template('admin/comments.html', title='Manage Comments', comments=comments)

@app.route('/admin/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_comment(comment_id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment has been deleted.', 'success')
    return redirect(url_for('admin_comments'))

@app.route('/admin/categories')
@login_required
@admin_required
def admin_categories():
    """Manage categories"""
    categories = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', title='Manage Categories', categories=categories)

@app.route('/admin/categories/create', methods=['POST'])
@login_required
@admin_required
def admin_create_category():
    """Create a new category"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    if name:
        # Check if category already exists
        existing = Category.query.filter_by(name=name).first()
        if existing:
            flash(f'Category "{name}" already exists.', 'error')
        else:
            category = Category(name=name, description=description)
            db.session.add(category)
            db.session.commit()
            flash(f'Category "{name}" has been created.', 'success')
    else:
        flash('Category name is required.', 'error')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_category(category_id):
    """Delete a category"""
    category = Category.query.get_or_404(category_id)
    category_name = category.name
    
    # Check if category has posts
    if category.posts:
        flash(f'Cannot delete category "{category_name}" because it contains posts.', 'error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category_name}" has been deleted.', 'success')
    
    return redirect(url_for('admin_categories'))

@app.route('/about')
def about():
    """Render the about page"""
    return render_template('about.html', title='About - Flask Learning App')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Handle contact form"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Simple form validation
        if name and email and message:
            flash(f'Thank you {name}! Your message has been received.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Please fill in all fields.', 'error')
    
    return render_template('contact.html', title='Contact - Flask Learning App')

@app.route('/blog')
def blog():
    """Display all blog posts"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '')
    
    if search_query:
        # Search in title and content
        posts = Post.query.filter(
            db.or_(
                Post.title.contains(search_query),
                Post.content.contains(search_query)
            )
        ).order_by(Post.created_at.desc()).paginate(
            page=page, per_page=5, error_out=False
        )
    else:
        posts = Post.query.order_by(Post.created_at.desc()).paginate(
            page=page, per_page=5, error_out=False
        )
    
    return render_template('blog.html', title='Blog', posts=posts, search_query=search_query)

@app.route('/search')
def search():
    """Search posts by title and content"""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    if query:
        posts = Post.query.filter(
            db.or_(
                Post.title.contains(query),
                Post.content.contains(query)
            )
        ).order_by(Post.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
    else:
        posts = Post.query.filter(Post.id == -1).paginate(page=1, per_page=10, error_out=False)  # Empty result
    
    return render_template('search_results.html', title=f'Search Results for "{query}"', posts=posts, query=query)

@app.route('/post/<int:id>', methods=['GET', 'POST'])
def post_detail(id):
    """Display single post with comments and handle new comments"""
    post = Post.query.get_or_404(id)
    
    if request.method == 'POST' and current_user.is_authenticated:
        content = request.form.get('content')
        if content and content.strip():
            # Create new comment
            comment = Comment(
                content=content.strip(),
                post_id=post.id,
                user_id=current_user.id
            )
            db.session.add(comment)
            db.session.commit()
            
            # Send email notification to post author
            send_comment_notification(post, comment)
            
            flash('Your comment has been added!', 'success')
            return redirect(url_for('post_detail', id=id))
        else:
            flash('Please enter a comment.', 'error')
    
    comments = Comment.query.filter_by(post_id=id).order_by(Comment.created_at.desc()).all()
    return render_template('post_detail.html', title=post.title, post=post, comments=comments)

@app.route('/create_post', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create a new blog post"""
    print(f"DEBUG: create_post route accessed")
    print(f"DEBUG: current_user.is_authenticated: {current_user.is_authenticated}")
    print(f"DEBUG: current_user: {current_user}")
    if hasattr(current_user, 'username'):
        print(f"DEBUG: current_user.username: {current_user.username}")
    
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id')
        image_file = request.files.get('image')
        
        if title and content:
            # Handle image upload
            image_filename = None
            if image_file and image_file.filename:
                image_filename = save_uploaded_file(image_file, 'posts')
                if not image_filename:
                    flash('Invalid image file. Please upload JPG, PNG, or GIF files only.', 'error')
                    categories = Category.query.all()
                    return render_template('create_post.html', title='Create Post', categories=categories)
            
            # Use the current logged-in user
            post = Post(
                title=title,
                content=content,
                image_filename=image_filename,
                user_id=current_user.id,
                category_id=category_id if category_id else None
            )
            db.session.add(post)
            db.session.commit()
            
            flash('Post created successfully!', 'success')
            return redirect(url_for('blog'))
        else:
            flash('Please fill in all required fields.', 'error')
    
    categories = Category.query.all()
    return render_template('create_post.html', title='Create Post', categories=categories)

@app.route('/categories')
def categories():
    """Display all categories"""
    categories = Category.query.all()
    return render_template('categories.html', title='Categories', categories=categories)

@app.route('/category/<int:id>')
def category_posts(id):
    """Display posts in a specific category"""
    category = Category.query.get_or_404(id)
    posts = Post.query.filter_by(category_id=id).order_by(Post.created_at.desc()).all()
    return render_template('category_posts.html', title=f'Category: {category.name}', 
                         category=category, posts=posts)

@app.route('/users')
def users():
    """Display all users"""
    users = User.query.all()
    return render_template('users.html', title='Users', users=users)

@app.route('/user/<username>')
def user_profile(username):
    """Display user profile with their posts"""
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    return render_template('user_profile.html', title=f'{username} - Profile', 
                         user=user, posts=posts)

@app.route('/init_db')
def init_db():
    """Initialize database with sample data"""
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    
    # No need to check if data exists since we just dropped everything
    
    # Create sample categories
    categories = [
        Category(name='Python', description='Python programming tutorials'),
        Category(name='Flask', description='Flask web development'),
        Category(name='Database', description='Database design and management'),
        Category(name='Web Development', description='General web development topics')
    ]
    
    for category in categories:
        db.session.add(category)
    
    # Create sample users with passwords
    users_data = [
        {'username': 'alice', 'email': 'alice@example.com', 'password': 'password123'},
        {'username': 'bob', 'email': 'bob@example.com', 'password': 'password123'},
        {'username': 'charlie', 'email': 'charlie@example.com', 'password': 'password123'}
    ]
    
    for user_data in users_data:
        user = User(username=user_data['username'], email=user_data['email'])
        user.set_password(user_data['password'])
        db.session.add(user)
    
    db.session.commit()
    
    # Create sample posts
    posts = [
        Post(title='Getting Started with Flask', 
             content='Flask is a micro web framework written in Python...', 
             user_id=1, category_id=2),
        Post(title='Database Design Principles', 
             content='When designing a database, consider normalization...', 
             user_id=2, category_id=3),
        Post(title='Python Best Practices', 
             content='Writing clean and maintainable Python code...', 
             user_id=1, category_id=1),
        Post(title='Building RESTful APIs', 
             content='REST APIs are a great way to build web services...', 
             user_id=3, category_id=4)
    ]
    
    for post in posts:
        db.session.add(post)
    
    db.session.commit()
    
    # Create sample comments
    comments = [
        Comment(content='Great tutorial! Very helpful.', post_id=1, user_id=2),
        Comment(content='Could you add more examples?', post_id=1, user_id=3),
        Comment(content='Excellent explanation of normalization.', post_id=2, user_id=1),
        Comment(content='This helped me understand REST better.', post_id=4, user_id=1)
    ]
    
    for comment in comments:
        db.session.add(comment)
    
    db.session.commit()
    
    flash('Database initialized with sample data!', 'success')
    return redirect(url_for('home'))

# Session example
@app.route('/session-demo')
def session_demo():
    """Demonstrate session usage"""
    if 'visit_count' in session:
        session['visit_count'] -= 1
    else:
        session['visit_count'] = 1
    
    return f'You have visited this page {session["visit_count"]} times!'

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('404.html', title='Page Not Found'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template('500.html', title='Server Error'), 500

if __name__ == '__main__':
    # Register API Blueprint
    from api_simple import api
    app.register_blueprint(api)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Run the application in debug mode for development
    app.run(debug=True, host='127.0.0.1', port=5002)
