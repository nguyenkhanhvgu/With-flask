"""
Test data factories for creating consistent test data.

This module provides Factory Boy factories for creating test instances
of database models with realistic and consistent data.
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app.models import User, Post, Comment, Category, Role, Permission, Follow, PostLike, PostView, Notification


class RoleFactory(factory.Factory):
    """Factory for creating Role instances."""
    
    class Meta:
        model = Role
    
    name = factory.Sequence(lambda n: f"role_{n}")
    description = factory.Faker('sentence', nb_words=4)


class PermissionFactory(factory.Factory):
    """Factory for creating Permission instances."""
    
    class Meta:
        model = Permission
    
    name = factory.Sequence(lambda n: f"permission_{n}")
    description = factory.Faker('sentence', nb_words=4)


class UserFactory(factory.Factory):
    """Factory for creating User instances."""
    
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password_hash = factory.LazyFunction(lambda: generate_password_hash("password123"))
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    bio = factory.Faker('text', max_nb_chars=200)
    location = factory.Faker('city')
    website = factory.Faker('url')
    created_at = factory.LazyFunction(datetime.utcnow)
    last_seen = factory.LazyFunction(datetime.utcnow)
    is_active = True
    email_confirmed = True
    role = factory.SubFactory(RoleFactory)
    
    @factory.post_generation
    def set_default_role(obj, create, extracted, **kwargs):
        """Set default user role if none provided."""
        if not obj.role:
            # In a real scenario, you'd query for the default role
            obj.role = RoleFactory(name='user')


class CategoryFactory(factory.Factory):
    """Factory for creating Category instances."""
    
    class Meta:
        model = Category
    
    name = factory.Faker('word')
    description = factory.Faker('sentence', nb_words=8)


class PostFactory(factory.Factory):
    """Factory for creating Post instances."""
    
    class Meta:
        model = Post
    
    title = factory.Faker('sentence', nb_words=6)
    content = factory.Faker('text', max_nb_chars=1000)
    meta_description = factory.Faker('text', max_nb_chars=200)
    view_count = fuzzy.FuzzyInteger(0, 1000)
    like_count = fuzzy.FuzzyInteger(0, 100)
    
    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        """Add tags to the post if provided."""
        if not create:
            return
        
        if extracted:
            for tag in extracted:
                obj.tags.append(tag)


class CommentFactory(factory.Factory):
    """Factory for creating Comment instances."""
    
    class Meta:
        model = Comment
    
    content = factory.Faker('text', max_nb_chars=500)


class FollowFactory(factory.Factory):
    """Factory for creating Follow instances."""
    
    class Meta:
        model = Follow
    
    follower = factory.SubFactory(UserFactory)
    followed = factory.SubFactory(UserFactory)
    created_at = factory.LazyFunction(datetime.utcnow)


class PostLikeFactory(factory.Factory):
    """Factory for creating PostLike instances."""
    
    class Meta:
        model = PostLike
    
    user = factory.SubFactory(UserFactory)
    post = factory.SubFactory(PostFactory)


class PostViewFactory(factory.Factory):
    """Factory for creating PostView instances."""
    
    class Meta:
        model = PostView
    
    post = factory.SubFactory(PostFactory)
    user = factory.SubFactory(UserFactory)
    ip_address = factory.Faker('ipv4')
    user_agent = factory.Faker('user_agent')
    time_spent = fuzzy.FuzzyInteger(10, 600)  # 10 seconds to 10 minutes
    scroll_depth = fuzzy.FuzzyFloat(0.1, 1.0)
    session_id = factory.Faker('uuid4')
    is_unique_view = True
    device_type = fuzzy.FuzzyChoice(['mobile', 'tablet', 'desktop'])
    browser = factory.Faker('user_agent')
    country_code = factory.Faker('country_code')


class NotificationFactory(factory.Factory):
    """Factory for creating Notification instances."""
    
    class Meta:
        model = Notification
    
    user = factory.SubFactory(UserFactory)
    title = factory.Faker('sentence', nb_words=4)
    message = factory.Faker('text', max_nb_chars=200)
    notification_type = fuzzy.FuzzyChoice(['comment', 'like', 'follow', 'system'])
    category = factory.LazyAttribute(lambda obj: obj.notification_type)
    priority = fuzzy.FuzzyChoice(['low', 'normal', 'high'])
    is_read = False


# Specialized factories for specific test scenarios

class AdminUserFactory(UserFactory):
    """Factory for creating admin users."""
    
    username = factory.Sequence(lambda n: f"admin_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@admin.example.com")
    role = factory.SubFactory(RoleFactory, name='admin')


class ModeratorUserFactory(UserFactory):
    """Factory for creating moderator users."""
    
    username = factory.Sequence(lambda n: f"moderator_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@mod.example.com")
    role = factory.SubFactory(RoleFactory, name='moderator')


class InactiveUserFactory(UserFactory):
    """Factory for creating inactive users."""
    
    is_active = False
    email_confirmed = False


class FeaturedPostFactory(PostFactory):
    """Factory for creating featured posts."""
    
    featured = True
    view_count = fuzzy.FuzzyInteger(500, 2000)
    like_count = fuzzy.FuzzyInteger(50, 200)


class DraftPostFactory(PostFactory):
    """Factory for creating draft posts."""
    
    published = False
    created_at = factory.LazyFunction(lambda: datetime.utcnow() - timedelta(days=1))


class OldPostFactory(PostFactory):
    """Factory for creating old posts."""
    
    created_at = factory.LazyFunction(lambda: datetime.utcnow() - timedelta(days=30))
    updated_at = factory.LazyFunction(lambda: datetime.utcnow() - timedelta(days=25))


class PopularPostFactory(PostFactory):
    """Factory for creating popular posts with high engagement."""
    
    view_count = fuzzy.FuzzyInteger(1000, 5000)
    like_count = fuzzy.FuzzyInteger(100, 500)
    
    @factory.post_generation
    def comments(obj, create, extracted, **kwargs):
        """Add multiple comments to make the post popular."""
        if not create:
            return
        
        # Create 5-15 comments for popular posts
        comment_count = fuzzy.FuzzyInteger(5, 15).fuzz()
        CommentFactory.create_batch(comment_count, post=obj)


# Utility functions for creating related test data

def create_user_with_posts(post_count=5, **user_kwargs):
    """Create a user with a specified number of posts."""
    user = UserFactory(**user_kwargs)
    posts = PostFactory.create_batch(post_count, author=user)
    return user, posts


def create_post_with_comments(comment_count=3, **post_kwargs):
    """Create a post with a specified number of comments."""
    post = PostFactory(**post_kwargs)
    comments = CommentFactory.create_batch(comment_count, post=post)
    return post, comments


def create_user_network(user_count=5, follow_ratio=0.3):
    """
    Create a network of users with follow relationships.
    
    Args:
        user_count: Number of users to create
        follow_ratio: Ratio of possible follow relationships to create
    
    Returns:
        List of created users
    """
    users = UserFactory.create_batch(user_count)
    
    # Create follow relationships
    total_possible = user_count * (user_count - 1)
    follow_count = int(total_possible * follow_ratio)
    
    follows = []
    for _ in range(follow_count):
        follower = factory.random.randgen.choice(users)
        followed = factory.random.randgen.choice(users)
        
        # Avoid self-follows and duplicate relationships
        if follower != followed:
            follow = FollowFactory(follower=follower, followed=followed)
            follows.append(follow)
    
    return users, follows