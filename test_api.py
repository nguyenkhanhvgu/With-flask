"""
API Testing Script
Test the REST API endpoints to ensure they work correctly
"""

import requests
import json
import sys

# Configuration
BASE_URL = 'http://localhost:5002/api/v1'
TEST_USER = {
    'username': 'api_test_user',
    'email': 'apitest@example.com',
    'password': 'testpass123'
}

class APITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.session = requests.Session()
    
    def log(self, message, success=True):
        status = "✅" if success else "❌"
        print(f"{status} {message}")
    
    def request(self, method, endpoint, data=None, files=None, auth_required=True):
        """Make API request with proper headers"""
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if auth_required and self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        if data and not files:
            headers['Content-Type'] = 'application/json'
            data = json.dumps(data)
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                data=data,
                files=files,
                headers=headers
            )
            return response
        except requests.exceptions.ConnectionError:
            self.log(f"Failed to connect to {url}. Make sure the Flask app is running.", False)
            return None
    
    def test_health_check(self):
        """Test API health check"""
        print("\n🔍 Testing Health Check...")
        response = self.request('GET', '/health', auth_required=False)
        
        if response and response.status_code == 200:
            data = response.json()
            self.log(f"Health check successful - Status: {data.get('status')}")
            return True
        else:
            self.log("Health check failed", False)
            return False
    
    def test_user_registration(self):
        """Test user registration"""
        print("\n👤 Testing User Registration...")
        response = self.request('POST', '/auth/register', TEST_USER, auth_required=False)
        
        if response:
            if response.status_code == 201:
                data = response.json()
                self.token = data.get('token')
                self.log(f"User registered successfully - Username: {data['user']['username']}")
                return True
            elif response.status_code == 400 and 'already exists' in response.json().get('error', ''):
                self.log("User already exists, proceeding with login test")
                return True
            else:
                self.log(f"Registration failed: {response.json().get('error')}", False)
                return False
        return False
    
    def test_user_login(self):
        """Test user login"""
        print("\n🔐 Testing User Login...")
        login_data = {
            'username': TEST_USER['username'],
            'password': TEST_USER['password']
        }
        response = self.request('POST', '/auth/login', login_data, auth_required=False)
        
        if response and response.status_code == 200:
            data = response.json()
            self.token = data.get('token')
            self.log(f"Login successful - Token received")
            return True
        else:
            error = response.json().get('error') if response else 'Connection failed'
            self.log(f"Login failed: {error}", False)
            return False
    
    def test_token_verification(self):
        """Test token verification"""
        print("\n🎫 Testing Token Verification...")
        response = self.request('GET', '/auth/verify')
        
        if response and response.status_code == 200:
            data = response.json()
            self.log(f"Token verified - User: {data['user']['username']}")
            return True
        else:
            self.log("Token verification failed", False)
            return False
    
    def test_get_posts(self):
        """Test getting posts"""
        print("\n📝 Testing Get Posts...")
        response = self.request('GET', '/posts', auth_required=False)
        
        if response and response.status_code == 200:
            data = response.json()
            posts_count = len(data.get('posts', []))
            self.log(f"Retrieved {posts_count} posts")
            return True
        else:
            self.log("Failed to get posts", False)
            return False
    
    def test_create_post(self):
        """Test creating a post"""
        print("\n✍️ Testing Create Post...")
        post_data = {
            'title': 'API Test Post',
            'content': 'This is a test post created via the API to verify functionality.'
        }
        response = self.request('POST', '/posts', post_data)
        
        if response and response.status_code == 201:
            data = response.json()
            post_id = data['post']['id']
            self.log(f"Post created successfully - ID: {post_id}")
            return post_id
        else:
            error = response.json().get('error') if response else 'Connection failed'
            self.log(f"Failed to create post: {error}", False)
            return None
    
    def test_get_categories(self):
        """Test getting categories"""
        print("\n📁 Testing Get Categories...")
        response = self.request('GET', '/categories', auth_required=False)
        
        if response and response.status_code == 200:
            data = response.json()
            categories_count = len(data.get('categories', []))
            self.log(f"Retrieved {categories_count} categories")
            return True
        else:
            self.log("Failed to get categories", False)
            return False
    
    def test_create_comment(self, post_id):
        """Test creating a comment"""
        if not post_id:
            self.log("Skipping comment test - no post ID available", False)
            return False
        
        print("\n💬 Testing Create Comment...")
        comment_data = {
            'content': 'This is a test comment created via the API.'
        }
        response = self.request('POST', f'/posts/{post_id}/comments', comment_data)
        
        if response and response.status_code == 201:
            data = response.json()
            comment_id = data['comment']['id']
            self.log(f"Comment created successfully - ID: {comment_id}")
            return True
        else:
            error = response.json().get('error') if response else 'Connection failed'
            self.log(f"Failed to create comment: {error}", False)
            return False
    
    def test_get_profile(self):
        """Test getting user profile"""
        print("\n👨‍💼 Testing Get Profile...")
        response = self.request('GET', '/users/profile')
        
        if response and response.status_code == 200:
            data = response.json()
            username = data['user']['username']
            self.log(f"Profile retrieved - Username: {username}")
            return True
        else:
            self.log("Failed to get profile", False)
            return False
    
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting API Tests...")
        print(f"📍 Base URL: {self.base_url}")
        
        tests_passed = 0
        total_tests = 0
        
        # Test health check
        total_tests += 1
        if self.test_health_check():
            tests_passed += 1
        
        # Test user registration
        total_tests += 1
        if self.test_user_registration():
            tests_passed += 1
        
        # Test user login
        total_tests += 1
        if self.test_user_login():
            tests_passed += 1
        
        # Test token verification (requires login)
        if self.token:
            total_tests += 1
            if self.test_token_verification():
                tests_passed += 1
        
        # Test get profile (requires authentication)
        if self.token:
            total_tests += 1
            if self.test_get_profile():
                tests_passed += 1
        
        # Test getting posts
        total_tests += 1
        if self.test_get_posts():
            tests_passed += 1
        
        # Test getting categories
        total_tests += 1
        if self.test_get_categories():
            tests_passed += 1
        
        # Test creating post (requires authentication)
        post_id = None
        if self.token:
            total_tests += 1
            post_id = self.test_create_post()
            if post_id:
                tests_passed += 1
        
        # Test creating comment (requires authentication and post)
        if self.token and post_id:
            total_tests += 1
            if self.test_create_comment(post_id):
                tests_passed += 1
        
        # Summary
        print("\n" + "="*50)
        print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
        
        if tests_passed == total_tests:
            print("🎉 All tests passed! API is working correctly.")
            return True
        else:
            print(f"⚠️  {total_tests - tests_passed} test(s) failed.")
            return False

def main():
    """Main function to run API tests"""
    print("🧪 Flask Blog API Test Suite")
    print("="*50)
    
    # Check if server is running
    tester = APITester(BASE_URL)
    
    # Run tests
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ API is ready for mobile app integration!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the API implementation.")
        sys.exit(1)

if __name__ == '__main__':
    main()
