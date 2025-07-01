#!/usr/bin/env python3
# force_db_init.py - Force database creation with explicit paths

import os
import sys
from datetime import datetime, timedelta

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def force_init():
    """Force database initialization with explicit config"""
    print("🔄 FORCE initializing database...")
    
    # FORCE development config
    os.environ['FLASK_CONFIG'] = 'development'
    
    try:
        from app import create_app, db
        from app.models import User, Project, Scene, StoryObject, BillingPlan, UserSubscription
        
        # Create app with explicit development config
        app = create_app('development')
        
        with app.app_context():
            # Print database URL to verify
            print(f"📍 Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Delete any existing database files
            db_files = ['storyforge.db', 'storyforge_dev.db']
            for db_file in db_files:
                if os.path.exists(db_file):
                    os.remove(db_file)
                    print(f"🗑️ Deleted: {db_file}")
            
            print("🏗️ Creating fresh database...")
            db.create_all()
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Created tables: {tables}")
            
            if 'user' not in tables:
                print("❌ User table not created! Recreating all tables...")
                # Try creating tables again
                db.create_all()
                tables = inspector.get_table_names()
                print(f"📋 Tables after retry: {tables}")
            
            # Create demo user
            print("👤 Creating demo user...")
            demo_user = User(
                username='demo',
                email='demo@storyforge.ai',
                plan='pro',
                tokens_limit=10000,
                tokens_used=150
            )
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()
            
            # Test user query
            test_user = User.query.filter_by(email='demo@storyforge.ai').first()
            if test_user:
                print(f"✅ User created and found: {test_user.email}")
            else:
                print("❌ User not found after creation!")
            
            print("\n✅ Database FORCE initialized!")
            print("📧 Demo login: demo@storyforge.ai")
            print("🔑 Demo password: demo123")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    force_init()