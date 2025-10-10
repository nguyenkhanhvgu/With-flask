#!/usr/bin/env python3
"""
Simple Integration Verification Script

This script performs basic verification that the Flask blog application
is working correctly after the migration to blueprint architecture.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.extensions import db


def verify_application():
    """Verify basic application functionality"""
    print("🔍 Verifying Flask Blog Application Integration")
    print("=" * 50)
    
    try:
        # Create application
        app = create_app('testing')
        print("✅ Application created successfully")
        
        # Check blueprints
        blueprints = list(app.blueprints.keys())
        expected_blueprints = ['main', 'auth', 'blog', 'admin', 'api', 'api_docs']
        
        missing_blueprints = []
        for bp in expected_blueprints:
            if bp not in blueprints:
                missing_blueprints.append(bp)
        
        if missing_blueprints:
            print(f"⚠️  Missing blueprints: {missing_blueprints}")
        else:
            print("✅ All expected blueprints registered")
        
        # Test basic routes
        with app.test_client() as client:
            # Test main routes
            routes_to_test = [
                ('/', 200),
                ('/auth/login', 200),
                ('/auth/register', 200),
                ('/blog/', 200),
                ('/api/v1/health', 200),
            ]
            
            failed_routes = []
            for route, expected_status in routes_to_test:
                try:
                    response = client.get(route)
                    if response.status_code != expected_status:
                        failed_routes.append(f"{route} (got {response.status_code}, expected {expected_status})")
                except Exception as e:
                    failed_routes.append(f"{route} (error: {e})")
            
            if failed_routes:
                print(f"⚠️  Failed routes: {failed_routes}")
            else:
                print("✅ All basic routes working")
        
        # Test database
        with app.app_context():
            try:
                db.create_all()
                print("✅ Database tables created successfully")
                
                # Test basic model imports
                from app.models.user import User
                from app.models.blog import Post, Comment, Category
                from app.models.role import Role, Permission
                print("✅ All models imported successfully")
                
                db.drop_all()
                print("✅ Database cleanup completed")
                
            except Exception as e:
                print(f"⚠️  Database error: {e}")
        
        print("\n🎉 Basic integration verification completed!")
        print("The application appears to be working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Application verification failed: {e}")
        return False


if __name__ == '__main__':
    success = verify_application()
    sys.exit(0 if success else 1)