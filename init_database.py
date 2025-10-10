#!/usr/bin/env python3
"""
Database Initialization Script

This script creates all database tables and sets up initial data
for the Flask blog application.
"""

import os
import sys
from flask import Flask
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.blog import Post, Comment, Category
from app.models.role import Role, Permission
from app.models.follow import Follow


def init_database():
    """Initialize the database with tables and default data."""
    
    print("Initializing database...")
    
    # Create Flask app instance
    app = create_app('development')
    
    with app.app_context():
        try:
            # Drop all tables (be careful in production!)
            print("Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            
            # Create default permissions and roles
            print("Creating default permissions...")
            Permission.create_default_permissions()
            
            print("Creating default roles...")
            Role.create_default_roles()
            
            # Create default categories
            print("Creating default categories...")
            categories = [
                Category(name='Technology', description='Posts about technology and programming'),
                Category(name='Lifestyle', description='Posts about lifestyle and personal experiences'),
                Category(name='Travel', description='Posts about travel and adventures'),
                Category(name='Food', description='Posts about food and cooking'),
                Category(name='Health', description='Posts about health and wellness'),
            ]
            
            for category in categories:
                existing = Category.query.filter_by(name=category.name).first()
                if not existing:
                    db.session.add(category)
            
            # Create admin user
            print("Creating admin user...")
            admin_role = Role.get_by_name('Administrator')
            admin_user = User.query.filter_by(username='admin').first()
            
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@example.com',
                    first_name='Admin',
                    last_name='User',
                    role=admin_role,
                    is_admin=True,
                    email_confirmed=True,
                    bio='System administrator account'
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
            
            # Create sample users
            print("Creating sample users...")
            user_role = Role.get_by_name('User')
            sample_users = [
                {
                    'username': 'john_doe',
                    'email': 'john@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'bio': 'Tech enthusiast and blogger'
                },
                {
                    'username': 'jane_smith',
                    'email': 'jane@example.com',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'bio': 'Travel blogger and photographer'
                },
                {
                    'username': 'mike_wilson',
                    'email': 'mike@example.com',
                    'first_name': 'Mike',
                    'last_name': 'Wilson',
                    'bio': 'Food lover and recipe creator'
                }
            ]
            
            created_users = []
            for user_data in sample_users:
                existing_user = User.query.filter_by(username=user_data['username']).first()
                if not existing_user:
                    user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        first_name=user_data['first_name'],
                        last_name=user_data['last_name'],
                        bio=user_data['bio'],
                        role=user_role,
                        email_confirmed=True
                    )
                    user.set_password('password123')
                    db.session.add(user)
                    created_users.append(user)
            
            # Commit users first so we can reference them
            db.session.commit()
            
            # Create sample posts
            print("Creating sample posts...")
            tech_category = Category.query.filter_by(name='Technology').first()
            travel_category = Category.query.filter_by(name='Travel').first()
            food_category = Category.query.filter_by(name='Food').first()
            
            sample_posts = [
                {
                    'title': 'Getting Started with Flask',
                    'content': '''Flask is a lightweight and flexible Python web framework that provides useful tools and features for creating web applications. In this post, we'll explore the basics of Flask and how to get started with your first web application.

Flask follows the WSGI (Web Server Gateway Interface) standard and is designed to be simple and easy to use. It doesn't make many decisions for you, which means you have the flexibility to structure your application as you see fit.

## Key Features of Flask

1. **Lightweight and Minimalist**: Flask provides the core functionality needed for web development without imposing a specific project structure.

2. **Flexible**: You can choose your own database, templating engine, and other components.

3. **Extensible**: Flask has a rich ecosystem of extensions that add functionality like database integration, form handling, and authentication.

4. **Built-in Development Server**: Flask comes with a development server that makes it easy to test your applications locally.

## Creating Your First Flask App

Here's a simple example of a Flask application:

```python
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)
```

This creates a basic web application that responds with "Hello, World!" when you visit the root URL.

Flask is an excellent choice for both beginners learning web development and experienced developers who want full control over their application architecture.''',
                    'author': admin_user,
                    'category': tech_category,
                    'meta_description': 'Learn the basics of Flask, a lightweight Python web framework perfect for beginners and experienced developers alike.'
                },
                {
                    'title': 'Exploring the Mountains of Switzerland',
                    'content': '''Switzerland is renowned for its breathtaking mountain landscapes, pristine lakes, and charming alpine villages. During my recent trip to this beautiful country, I had the opportunity to explore some of the most stunning mountain regions.

## The Matterhorn Experience

The iconic Matterhorn, standing at 4,478 meters, is one of the most photographed mountains in the world. The journey to Zermatt, the car-free village at the base of the Matterhorn, is an adventure in itself. The train ride through the Swiss countryside offers spectacular views of rolling hills, traditional chalets, and snow-capped peaks.

## Jungfraujoch - Top of Europe

Another highlight of my trip was visiting Jungfraujoch, known as the "Top of Europe." The journey involves taking a series of trains, including the famous Jungfrau Railway, which takes you through tunnels carved into the Eiger and Mönch mountains.

At 3,454 meters above sea level, Jungfraujoch offers:
- Stunning panoramic views of the Aletsch Glacier
- The Ice Palace with intricate ice sculptures
- Research stations studying climate and glaciology
- Restaurants with incredible mountain views

## Hiking Adventures

Switzerland offers hiking trails for all skill levels. Some of my favorite experiences included:

1. **The Five Lakes Walk near Zermatt**: A moderate hike that takes you past five pristine mountain lakes, each offering perfect reflections of the Matterhorn.

2. **Lauterbrunnen Valley**: Known as the "Valley of 72 Waterfalls," this area offers easy walks with spectacular waterfall views.

3. **Grindelwald First**: The cliff walk and mountain cart rides provide thrilling experiences with incredible views.

## Tips for Mountain Travel in Switzerland

- **Swiss Travel Pass**: Consider purchasing a Swiss Travel Pass for convenient and cost-effective transportation.
- **Weather**: Mountain weather can change quickly, so pack layers and waterproof clothing.
- **Altitude**: Take time to acclimatize, especially when visiting high-altitude locations.
- **Reservations**: Book accommodations and popular attractions in advance, especially during peak season.

Switzerland's mountains offer an unforgettable experience that combines natural beauty, adventure, and Swiss hospitality. Whether you're an experienced mountaineer or a casual traveler, there's something magical about the Swiss Alps that will leave you planning your next visit before you've even left.''',
                    'author': User.query.filter_by(username='jane_smith').first() or admin_user,
                    'category': travel_category,
                    'meta_description': 'Discover the breathtaking beauty of Swiss mountains, from the iconic Matterhorn to the stunning Jungfraujoch, with practical travel tips.'
                },
                {
                    'title': 'The Art of Italian Pasta Making',
                    'content': '''There's something truly magical about making pasta from scratch. The simple combination of flour, eggs, and a pinch of salt transforms into silky, delicious strands that form the foundation of countless Italian dishes. Today, I'll share my journey into the art of pasta making and some tips I've learned along the way.

## The Foundation: Understanding Pasta Dough

Traditional Italian pasta dough, or "pasta fresca," requires just a few ingredients:
- 400g of 00 flour (or all-purpose flour as a substitute)
- 4 large eggs
- A pinch of salt
- Sometimes a drizzle of olive oil

The key to great pasta is in the technique, not exotic ingredients.

## The Process

### 1. Creating the Well
Start by creating a well with your flour on a clean work surface. Crack the eggs into the center and add your salt. Using a fork, gradually incorporate the flour into the eggs, working from the inside out.

### 2. Kneading
Once the dough comes together, it's time to knead. This is where the magic happens. Knead for about 10 minutes until the dough becomes smooth and elastic. The dough should feel slightly tacky but not sticky.

### 3. Resting
Wrap the dough in plastic wrap and let it rest for at least 30 minutes. This allows the gluten to relax, making the dough easier to roll out.

### 4. Rolling and Shaping
Whether using a pasta machine or rolling pin, work with small portions of dough at a time. Keep unused portions covered to prevent drying out.

## Popular Pasta Shapes to Try

### Fettuccine
Perfect for rich, creamy sauces like Alfredo or carbonara. The wide, flat noodles hold sauce beautifully.

### Ravioli
These stuffed pasta parcels can be filled with ricotta and spinach, butternut squash, or even lobster for special occasions.

### Pappardelle
These wide ribbon noodles are ideal for hearty meat sauces like Bolognese or wild boar ragu.

## Sauce Pairing Tips

The Italians have a saying: "La pasta non aspetta nessuno" (pasta waits for no one). Here are some classic pairings:

- **Thin pasta** (spaghetti, angel hair): Light oil-based or tomato sauces
- **Thick pasta** (pappardelle, fettuccine): Rich, creamy, or meat-based sauces
- **Stuffed pasta** (ravioli, tortellini): Simple butter and sage or light cream sauces

## Common Mistakes to Avoid

1. **Over-flouring**: Too much flour makes the dough tough
2. **Under-kneading**: Results in pasta that falls apart when cooked
3. **Not resting the dough**: Makes rolling difficult and can result in tough pasta
4. **Overcooking**: Fresh pasta cooks much faster than dried pasta

## The Reward

There's nothing quite like the satisfaction of twirling your fork around pasta you've made with your own hands. The texture is incomparable to store-bought pasta – silky, tender, and with just the right amount of bite.

Making pasta from scratch is both an art and a meditation. It connects you to generations of Italian cooks who have perfected this craft. While it takes practice to master, even your first attempts will be delicious and rewarding.

So roll up your sleeves, dust your countertop with flour, and embark on your own pasta-making adventure. Buon appetito!''',
                    'author': User.query.filter_by(username='mike_wilson').first() or admin_user,
                    'category': food_category,
                    'meta_description': 'Master the art of making fresh Italian pasta from scratch with this comprehensive guide, including tips, techniques, and sauce pairings.'
                }
            ]
            
            for post_data in sample_posts:
                existing_post = Post.query.filter_by(title=post_data['title']).first()
                if not existing_post:
                    post = Post(
                        title=post_data['title'],
                        content=post_data['content'],
                        user_id=post_data['author'].id,
                        category_id=post_data['category'].id if post_data['category'] else None,
                        meta_description=post_data['meta_description']
                    )
                    db.session.add(post)
            
            # Commit all changes
            db.session.commit()
            
            print("✅ Database initialization completed successfully!")
            print("\nDefault accounts created:")
            print("- Admin: admin@example.com / admin123")
            print("- User: john@example.com / password123")
            print("- User: jane@example.com / password123")
            print("- User: mike@example.com / password123")
            print("\nYou can now access pgAdmin at http://localhost:8081")
            print("pgAdmin login: admin@example.com / admin123")
            
        except Exception as e:
            print(f"❌ Error initializing database: {str(e)}")
            db.session.rollback()
            return False
    
    return True


if __name__ == '__main__':
    init_database()