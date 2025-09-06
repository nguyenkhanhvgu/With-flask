# Flask Learning Project

A comprehensive Flask web application for learning Python web development with database integration.

## Project Structure

```
flask-learning/
├── app.py                 # Main Flask application with database
├── blog.db                # SQLite database (created after running)
├── requirements.txt       # Python dependencies
├── DATABASE_GUIDE.md      # Database design guide
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── index.html        # Homepage with recent posts
│   ├── blog.html         # Blog listing with pagination
│   ├── post_detail.html  # Individual post view
│   ├── create_post.html  # Create new post form
│   ├── categories.html   # Categories listing
│   ├── category_posts.html # Posts in category
│   ├── users.html        # Users listing
│   ├── user_profile.html # User profile with posts
│   ├── about.html        # About page
│   ├── contact.html      # Contact form
│   ├── 404.html          # 404 error page
│   └── 500.html          # 500 error page
├── static/               # Static files
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   └── js/
│       └── main.js       # Main JavaScript file
└── README.md             # This file
```

## Features Demonstrated

### Flask Web Development Concepts
- Route handling (GET/POST)
- Template rendering with Jinja2
- Static file serving
- Form handling and validation
- Session management
- Error handling (404, 500)
- Flash messages
- Template inheritance and filters

### Database Integration
- SQLAlchemy ORM models
- Database relationships (One-to-Many)
- CRUD operations (Create, Read, Update, Delete)
- Database initialization with sample data
- Query operations and filtering
- Pagination

### Database Models
- **User**: Blog authors and commenters
- **Category**: Post organization
- **Post**: Blog articles with content
- **Comment**: User feedback on posts

### Database Relationships
- User → Posts (One-to-Many)
- User → Comments (One-to-Many)
- Category → Posts (One-to-Many)
- Post → Comments (One-to-Many)

## Setup Instructions

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   ```

2. **Activate the virtual environment**:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Initialize the database with sample data**:
   - Go to `http://127.0.0.1:5000/init_db` in your browser
   - Or the application will create empty tables automatically

6. **Open your browser** and go to `http://127.0.0.1:5000`

## Learning Path

### Getting Started
1. Run the application with `python app.py`
2. Initialize sample data by visiting `/init_db`
3. Explore the different sections: Blog, Categories, Users
4. Try creating new posts and exploring relationships

### Understanding the Code
1. Study the database models in `app.py`
2. Understand the relationships between User, Post, Category, and Comment
3. Explore how templates display database data
4. Learn about CRUD operations in the route handlers

### Advanced Topics (For Further Learning)
- User authentication and authorization
- RESTful API development
- Database migrations with Flask-Migrate
- Testing with pytest
- Deployment to production
- Caching and performance optimization

## Database Design Concepts

Read `DATABASE_GUIDE.md` for detailed information about:
- Database design principles
- Entity-Relationship modeling
- Normalization
- SQLAlchemy ORM usage
- Relationship types and implementations

## Next Steps

This project provides a solid foundation for Flask development. Consider expanding it with:
- User authentication (login/logout)
- User registration
- Password hashing
- CSRF protection
- RESTful APIs
- File uploads
- Email integration
- Unit and integration tests
- Deployment configurations
