# tests/unit/test_models.py - Unit Tests for Models
import pytest
from datetime import datetime
from app.models import User, Project, Scene, StoryObject

class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self, app):
        """Test user creation"""
        with app.app_context():
            user = User(username='newuser', email='new@example.com')
            user.set_password('password123')
            
            assert user.username == 'newuser'
            assert user.email == 'new@example.com'
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')
    
    def test_user_to_dict(self, test_user):
        """Test user serialization"""
        user_dict = test_user.to_dict()
        
        assert user_dict['username'] == 'testuser'
        assert user_dict['email'] == 'test@example.com'
        assert user_dict['plan'] == 'pro'
        assert 'password_hash' not in user_dict

class TestProjectModel:
    """Test Project model"""
    
    def test_project_creation(self, app, test_user):
        """Test project creation"""
        with app.app_context():
            project = Project(
                title='New Story',
                description='A new story',
                user_id=test_user.id
            )
            
            assert project.title == 'New Story'
            assert project.current_phase == 'idea'  # Default
            assert project.user_id == test_user.id
    
    def test_project_to_dict(self, test_project):
        """Test project serialization"""
        project_dict = test_project.to_dict()
        
        assert project_dict['title'] == 'Test Story'
        assert project_dict['genre'] == 'mystery'
        assert 'created_at' in project_dict

class TestSceneModel:
    """Test Scene model"""
    
    def test_scene_creation(self, app, test_project):
        """Test scene creation"""
        with app.app_context():
            scene = Scene(
                title='Test Scene',
                description='A test scene',
                project_id=test_project.id,
                order_index=1
            )
            
            assert scene.title == 'Test Scene'
            assert scene.project_id == test_project.id
            assert scene.order_index == 1