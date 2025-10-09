#!/usr/bin/env python3
"""
Fix database schema by manually adding missing columns
"""

from app import create_app, db
import sqlite3

def fix_database():
    """Add missing columns to the database"""
    app = create_app()
    
    with app.app_context():
        # Get the database path
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        print(f"Fixing database at: {db_path}")
        
        # Connect directly to SQLite
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if columns exist
            cursor.execute("PRAGMA table_info(post)")
            columns = [row[1] for row in cursor.fetchall()]
            print(f"Current post columns: {columns}")
            
            # Add missing columns to post table
            if 'like_count' not in columns:
                print("Adding like_count column...")
                cursor.execute("ALTER TABLE post ADD COLUMN like_count INTEGER DEFAULT 0")
            
            if 'view_count' not in columns:
                print("Adding view_count column...")
                cursor.execute("ALTER TABLE post ADD COLUMN view_count INTEGER DEFAULT 0")
            
            if 'slug' not in columns:
                print("Adding slug column...")
                cursor.execute("ALTER TABLE post ADD COLUMN slug VARCHAR(255)")
            
            if 'meta_description' not in columns:
                print("Adding meta_description column...")
                cursor.execute("ALTER TABLE post ADD COLUMN meta_description TEXT")
            
            # Check if post_like table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='post_like'")
            if not cursor.fetchone():
                print("Creating post_like table...")
                cursor.execute("""
                    CREATE TABLE post_like (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER NOT NULL,
                        post_id INTEGER NOT NULL,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES user(id),
                        FOREIGN KEY(post_id) REFERENCES post(id),
                        UNIQUE(user_id, post_id)
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX idx_post_like_user_id ON post_like(user_id)")
                cursor.execute("CREATE INDEX idx_post_like_post_id ON post_like(post_id)")
                cursor.execute("CREATE INDEX idx_like_user_created ON post_like(user_id, created_at)")
                cursor.execute("CREATE INDEX idx_like_post_created ON post_like(post_id, created_at)")
            
            conn.commit()
            print("Database fixed successfully!")
            
        except Exception as e:
            print(f"Error fixing database: {e}")
            conn.rollback()
        finally:
            conn.close()

if __name__ == '__main__':
    fix_database()