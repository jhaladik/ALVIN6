from app import db, create_app
from app.models import User
from werkzeug.security import generate_password_hash
from datetime import datetime

# Create the app
app = create_app()

# Use the app context
with app.app_context():
    # Check if demo user already exists
    existing_user = User.query.filter_by(email='demo@storyforge.ai').first()
    
    if existing_user:
        print("✅ Demo user already exists!")
        print("Email: demo@storyforge.ai")
        print("Password: demo123")
    else:
        # Create demo user
        demo_user = User(
            username='demo',
            email='demo@storyforge.ai',
            plan='pro',
            tokens_limit=10000,
            tokens_used=150,
            is_active=True,
            created_at=datetime.utcnow()
        )
        demo_user.password_hash = generate_password_hash('demo123')
        
        try:
            # Add to database
            db.session.add(demo_user)
            db.session.commit()
            print("✅ Demo user created successfully!")
            print("Email: demo@storyforge.ai")
            print("Password: demo123")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating demo user: {e}")