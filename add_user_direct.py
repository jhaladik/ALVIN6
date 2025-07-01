from app import create_app, db
import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

app = create_app()

with app.app_context():
    # Get database path from Flask-SQLAlchemy
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    print(f"Using database at: {db_path}")
    
    # Connect directly to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if user table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
    if not cursor.fetchone():
        print("Creating user table...")
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128),
            plan VARCHAR(20) DEFAULT 'free',
            tokens_used INTEGER DEFAULT 0,
            tokens_limit INTEGER DEFAULT 1000,
            is_active BOOLEAN DEFAULT 1,
            last_login DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
    
    # Check if demo user exists
    cursor.execute("SELECT id FROM user WHERE email = 'demo@storyforge.ai'")
    if cursor.fetchone():
        print("Demo user already exists")
    else:
        # Create demo user
        now = datetime.utcnow().isoformat()
        password_hash = generate_password_hash('demo123')
        
        cursor.execute('''
        INSERT INTO user (username, email, password_hash, plan, tokens_used, tokens_limit, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('demo', 'demo@storyforge.ai', password_hash, 'pro', 150, 10000, 1, now))
        
        print("Demo user created successfully")
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("✅ Done!")
    print("Email: demo@storyforge.ai")
    print("Password: demo123")