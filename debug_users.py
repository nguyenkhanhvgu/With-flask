#!/usr/bin/env python3
"""Debug script to check users in database"""

from app import app, db, User
from werkzeug.security import check_password_hash

def main():
    with app.app_context():
        print("=== Database Users Debug ===")
        users = User.query.all()
        print(f"Total users found: {len(users)}")
        
        for user in users:
            print(f"\nUser ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Has password hash: {bool(user.password_hash)}")
            print(f"Password hash length: {len(user.password_hash) if user.password_hash else 0}")
            
            # Test password verification
            if user.password_hash:
                test_result = user.check_password('password123')
                print(f"Password 'password123' check: {test_result}")

if __name__ == "__main__":
    main()
