"""
Locust Load Testing Configuration

This file defines load testing scenarios for the Flask blog application
using Locust to simulate realistic user behavior and measure performance
under various load conditions.
"""

import random
import json
from locust import HttpUser, task, between, events
from locust.exception import RescheduleTask


class BlogUser(HttpUser):
    """
    Simulates a typical blog user behavior.
    
    This user class represents common user interactions with the blog,
    including browsing posts, reading content, and basic interactions.
    """
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Initialize user session and perform login if needed."""
        self.client.verify = False  # Disable SSL verification for testing
        
        # Try to get the home page to establish session
        response = self.client.get("/")
        if response.status_code != 200:
            print(f"Failed to load home page: {response.status_code}")
    
    @task(3)
    def browse_home_page(self):
        """Browse the home page - most common user action."""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Home page returned {response.status_code}")
    
    @task(2)
    def view_post_list(self):
        """View the list of blog posts."""
        with self.client.get("/posts", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Post list returned {response.status_code}")
    
    @task(2)
    def view_random_post(self):
        """View a random blog post."""
        # Simulate viewing posts with IDs 1-20
        post_id = random.randint(1, 20)
        with self.client.get(f"/posts/{post_id}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # 404 is acceptable for random post IDs
                response.success()
            else:
                response.failure(f"Post view returned {response.status_code}")
    
    @task(1)
    def view_categories(self):
        """Browse post categories."""
        with self.client.get("/categories", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Categories page returned {response.status_code}")
    
    @task(1)
    def search_posts(self):
        """Perform a search query."""
        search_terms = ["python", "flask", "web", "development", "tutorial"]
        query = random.choice(search_terms)
        
        with self.client.get(f"/search?q={query}", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search returned {response.status_code}")


class APIUser(HttpUser):
    """
    Simulates API client behavior.
    
    This user class tests the REST API endpoints under load,
    simulating mobile apps or external integrations.
    """
    
    wait_time = between(0.5, 2)  # API users typically have shorter wait times
    
    def on_start(self):
        """Initialize API client."""
        self.client.verify = False
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    @task(3)
    def api_get_posts(self):
        """Get posts via API."""
        with self.client.get("/api/v1/posts", headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if isinstance(data, (list, dict)):
                        response.success()
                    else:
                        response.failure("Invalid JSON response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"API posts returned {response.status_code}")
    
    @task(2)
    def api_get_post_detail(self):
        """Get post detail via API."""
        post_id = random.randint(1, 20)
        with self.client.get(f"/api/v1/posts/{post_id}", headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 404:
                response.success()  # 404 is acceptable
            else:
                response.failure(f"API post detail returned {response.status_code}")
    
    @task(1)
    def api_get_users(self):
        """Get users via API."""
        with self.client.get("/api/v1/users", headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"API users returned {response.status_code}")
    
    @task(1)
    def api_get_categories(self):
        """Get categories via API."""
        with self.client.get("/api/v1/categories", headers=self.headers, catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"API categories returned {response.status_code}")


class AuthenticatedUser(HttpUser):
    """
    Simulates authenticated user behavior.
    
    This user class tests authenticated features like posting,
    commenting, and user profile management.
    """
    
    wait_time = between(2, 8)  # Authenticated users spend more time
    
    def on_start(self):
        """Login user and establish authenticated session."""
        self.client.verify = False
        
        # Try to login with test credentials
        login_data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        
        with self.client.post("/auth/login", data=login_data, catch_response=True) as response:
            if response.status_code in [200, 302]:  # Success or redirect
                self.authenticated = True
            else:
                self.authenticated = False
                print(f"Login failed: {response.status_code}")
    
    @task(2)
    def view_profile(self):
        """View user profile."""
        if not getattr(self, 'authenticated', False):
            raise RescheduleTask()
        
        with self.client.get("/profile", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Profile view returned {response.status_code}")
    
    @task(1)
    def create_post(self):
        """Create a new blog post."""
        if not getattr(self, 'authenticated', False):
            raise RescheduleTask()
        
        post_data = {
            'title': f'Load Test Post {random.randint(1000, 9999)}',
            'content': 'This is a test post created during load testing.',
            'category_id': random.randint(1, 5)
        }
        
        with self.client.post("/posts/create", data=post_data, catch_response=True) as response:
            if response.status_code in [200, 201, 302]:
                response.success()
            else:
                response.failure(f"Post creation returned {response.status_code}")
    
    @task(1)
    def add_comment(self):
        """Add a comment to a random post."""
        if not getattr(self, 'authenticated', False):
            raise RescheduleTask()
        
        post_id = random.randint(1, 20)
        comment_data = {
            'content': f'Load test comment {random.randint(100, 999)}'
        }
        
        with self.client.post(f"/posts/{post_id}/comment", data=comment_data, catch_response=True) as response:
            if response.status_code in [200, 201, 302, 404]:  # 404 acceptable for random post
                response.success()
            else:
                response.failure(f"Comment creation returned {response.status_code}")


# Event handlers for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    """Custom request handler to log performance metrics."""
    if exception:
        print(f"Request failed: {request_type} {name} - {exception}")
    elif response_time > 2000:  # Log slow requests (>2 seconds)
        print(f"Slow request: {request_type} {name} - {response_time}ms")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Handler for test start event."""
    print("Load test starting...")
    print(f"Target host: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Handler for test stop event."""
    print("Load test completed.")
    
    # Print summary statistics
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Total failures: {stats.total.num_failures}")
    print(f"Average response time: {stats.total.avg_response_time:.2f}ms")
    print(f"Max response time: {stats.total.max_response_time}ms")
    print(f"Requests per second: {stats.total.current_rps:.2f}")
    
    # Log slow endpoints
    print("\nSlowest endpoints:")
    sorted_stats = sorted(stats.entries.items(), key=lambda x: x[1].avg_response_time, reverse=True)
    for (method, endpoint), stat in sorted_stats[:5]:
        print(f"  {method} {endpoint}: {stat.avg_response_time:.2f}ms avg")


# Custom user classes for different load scenarios
class LightLoadUser(BlogUser):
    """Light load scenario - normal browsing behavior."""
    weight = 3
    wait_time = between(3, 10)


class MediumLoadUser(BlogUser):
    """Medium load scenario - more active browsing."""
    weight = 2
    wait_time = between(1, 5)


class HeavyLoadUser(APIUser):
    """Heavy load scenario - API-heavy usage."""
    weight = 1
    wait_time = between(0.1, 1)


# Configuration for different test scenarios
class StressTestUser(HttpUser):
    """Stress test user for maximum load testing."""
    
    wait_time = between(0.1, 0.5)  # Very short wait times
    
    @task
    def rapid_requests(self):
        """Make rapid requests to test system limits."""
        endpoints = ["/", "/posts", "/api/v1/posts", "/categories"]
        endpoint = random.choice(endpoints)
        
        with self.client.get(endpoint, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Stress test request failed: {response.status_code}")