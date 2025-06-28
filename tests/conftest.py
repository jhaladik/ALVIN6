# tests/conftest.py - Fixed with proper Python path handling
import sys
import os
import pytest
from datetime import datetime, timedelta

# Add the parent directory (project root) to the Python path
# This ensures the 'app' module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import from the app package
from app import create_app, db
from app.models import User, Project, Scene, StoryObject, BillingPlan, UserSubscription

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    # Create temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'AI_SIMULATION_MODE': True,
        'PAYMENT_SIMULATION_MODE': True,
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.app_context():
        db.create_all()
        # Create test billing plans
        create_test_billing_plans()
        yield app
        
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """CLI test runner"""
    return app.test_cli_runner()

@pytest.fixture
def auth_headers():
    """Authentication headers for API tests"""
    return {'Content-Type': 'application/json'}

@pytest.fixture
def test_user(app):
    """Create test user"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            plan='pro',
            tokens_limit=10000,
            tokens_used=100
        )
        user.set_password('testpassword')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def admin_user(app):
    """Create admin user"""
    with app.app_context():
        user = User(
            username='admin',
            email='admin@example.com',
            plan='enterprise',
            tokens_limit=100000,
            tokens_used=0
        )
        user.set_password('adminpassword')
        db.session.add(user)
        db.session.commit()
        return user

@pytest.fixture
def test_project(app, test_user):
    """Create test project"""
    with app.app_context():
        project = Project(
            title='Test Story',
            description='A test story for unit testing',
            genre='mystery',
            current_phase='expand',
            user_id=test_user.id
        )
        db.session.add(project)
        db.session.commit()
        return project

@pytest.fixture
def test_scenes(app, test_project):
    """Create test scenes"""
    with app.app_context():
        scenes = [
            Scene(
                title='Opening Scene',
                description='The story begins...',
                scene_type='opening',
                order_index=1,
                project_id=test_project.id,
                emotional_intensity=0.5,
                word_count=200
            ),
            Scene(
                title='Inciting Incident',
                description='Something happens that changes everything...',
                scene_type='inciting',
                order_index=2,
                project_id=test_project.id,
                emotional_intensity=0.8,
                word_count=350
            )
        ]
        
        for scene in scenes:
            db.session.add(scene)
        
        db.session.commit()
        return scenes

@pytest.fixture
def test_objects(app, test_project):
    """Create test story objects"""
    with app.app_context():
        objects = [
            StoryObject(
                name='Protagonist',
                object_type='character',
                project_id=test_project.id,
                importance='high',
                status='active'
            ),
            StoryObject(
                name='Mysterious Letter',
                object_type='object',
                project_id=test_project.id,
                importance='high',
                status='active'
            ),
            StoryObject(
                name='Old House',
                object_type='location',
                project_id=test_project.id,
                importance='medium',
                status='active'
            )
        ]
        
        for obj in objects:
            db.session.add(obj)
        
        db.session.commit()
        return objects

@pytest.fixture
def authenticated_user(client, test_user):
    """Login user and return session"""
    with client.session_transaction() as sess:
        sess['user_id'] = test_user.id
    return test_user

def create_test_billing_plans():
    """Create test billing plans"""
    plans = [
        BillingPlan(
            name='free',
            display_name='Free Plan',
            monthly_token_limit=1000,
            monthly_price_cents=0,
            is_active=True,
            is_public=True
        ),
        BillingPlan(
            name='pro',
            display_name='Pro Plan',
            monthly_token_limit=10000,
            monthly_price_cents=1999,
            is_active=True,
            is_public=True
        )
    ]
    
    for plan in plans:
        db.session.add(plan)
    
    db.session.commit()