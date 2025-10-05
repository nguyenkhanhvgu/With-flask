"""
Test script for Flask-RESTX API implementation

This script tests the basic functionality of the Flask-RESTX API
to ensure proper setup and documentation generation.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.blog import Category, Post
from werkzeug.security import generate_password_hash
import json


def test_restx_api():
    """Test Flask-RESTX API endpoints and documentation"""
    
    # Create test app
    app = create_app('testing')
    
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create test data
        create_test_data()
        
        # Test client
        client = app.test_client()
        
        print("Testing Flask-RESTX API Implementation...")
        print("=" * 50)
        
        # Test 1: Health check endpoint
        print("\n1. Testing health check endpoint...")
        response = client.get('/api/v1/utils/health')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"Health Status: {data.get('status')}")
            print("✓ Health check working")
        else:
            print("✗ Health check failed")
        
        # Test 2: API documentation endpoint
        print("\n2. Testing API documentation endpoint...")
        response = client.get('/api/v1/docs/')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✓ Swagger UI accessible")
        else:
            print("✗ Swagger UI not accessible")
        
        # Test 3: OpenAPI specification
        print("\n3. Testing OpenAPI specification...")
        response = client.get('/api/v1/swagger.json')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            spec = json.loads(response.data)
            print(f"API Title: {spec.get('info', {}).get('title')}")
            print(f"API Version: {spec.get('info', {}).get('version')}")
            print(f"Paths Count: {len(spec.get('paths', {}))}")
            print("✓ OpenAPI specification generated")
        else:
            print("✗ OpenAPI specification not available")
        
        # Test 4: User registration
        print("\n4. Testing user registration...")
        user_data = {
            'username': 'testuser_api',
            'email': 'testapi@example.com',
            'password': 'testpassword123',
            'confirm_password': 'testpassword123'
        }
        response = client.post('/api/v1/auth/register', 
                             json=user_data,
                             content_type='application/json')
        print(f"Status: {response.status_code}")
        if response.status_code == 201:
            data = json.loads(response.data)
            token = data.get('access_token') or data.get('token')
            print(f"User created: {data.get('user', {}).get('username')}")
            print(f"Registration response: {data}")
            print("✓ User registration working")
            
            headers = None
            if token:
                # Test 5: Token verification
                print("\n5. Testing token verification...")
                print(f"Token: {token[:50]}...")
                headers = {'Authorization': f'Bearer {token}'}
                response = client.get('/api/v1/auth/verify', headers=headers)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = json.loads(response.data)
                    print(f"Verified user: {data.get('username')}")
                    print("✓ Token verification working")
                else:
                    error_data = json.loads(response.data)
                    print(f"Error: {error_data}")
                    print("✗ Token verification failed")
            else:
                print("\n5. No token received from registration")
                print("✗ Token verification failed")
            
            # Test 6: Get posts
            print("\n6. Testing posts endpoint...")
            response = client.get('/api/v1/posts')
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = json.loads(response.data)
                print(f"Posts count: {len(data.get('posts', []))}")
                print(f"Pagination: {data.get('pagination', {})}")
                print("✓ Posts endpoint working")
            else:
                print("✗ Posts endpoint failed")
            
            # Test 7: Create post
            print("\n7. Testing post creation...")
            post_data = {
                'title': 'Test API Post',
                'content': 'This is a test post created via API',
                'category_id': 1
            }
            if headers:
                response = client.post('/api/v1/posts',
                                     json=post_data,
                                     headers=headers,
                                     content_type='application/json')
                print(f"Status: {response.status_code}")
                if response.status_code == 201:
                    data = json.loads(response.data)
                    print(f"Created post: {data.get('title')}")
                    print("✓ Post creation working")
                else:
                    print("✗ Post creation failed")
            else:
                print("No token available for post creation")
                print("✗ Post creation failed")
                
        else:
            print("✗ User registration failed")
        
        # Test 8: Version endpoint
        print("\n8. Testing version endpoint...")
        response = client.get('/api/v1/utils/version')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = json.loads(response.data)
            print(f"API Version: {data.get('api_version')}")
            print(f"Flask Version: {data.get('flask_version')}")
            print("✓ Version endpoint working")
        else:
            print("✗ Version endpoint failed")
        
        print("\n" + "=" * 50)
        print("Flask-RESTX API Test Complete!")
        print("\nTo access the interactive documentation:")
        print("1. Start the Flask development server: python run.py")
        print("2. Open your browser to: http://localhost:5000/api/v1/docs/")
        print("3. Explore the API endpoints and try them out!")


def create_test_data():
    """Create test data for API testing"""
    
    # Create test category
    category = Category(
        name='Technology',
        description='Posts about technology and programming'
    )
    db.session.add(category)
    
    # Create test user
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash=generate_password_hash('password123'),
        is_admin=False
    )
    db.session.add(user)
    
    # Commit to get IDs
    db.session.commit()
    
    # Create test post
    post = Post(
        title='Welcome to the API',
        content='This is a test post for the Flask-RESTX API implementation.',
        user_id=user.id,
        category_id=category.id
    )
    db.session.add(post)
    db.session.commit()


if __name__ == '__main__':
    test_restx_api()