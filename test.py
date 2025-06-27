# tests.py - Comprehensive Test Suite
import unittest
import json
import tempfile
import os
from app import create_app
from models import db, User, Project, Scene, Character
from werkzeug.security import generate_password_hash

class StoryForgeTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Create test app
        self.app = create_app('testing')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.app.config['TESTING'] = True
        
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
        
        # Create test user
        self.test_user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('testpass'),
            plan='pro',
            tokens_limit=10000
        )
        db.session.add(self.test_user)
        db.session.commit()
        
        # Login test user
        self.login('test@example.com', 'testpass')
    
    def tearDown(self):
        """Clean up after each test method."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def login(self, email, password):
        """Helper method to login user."""
        return self.client.post('/api/auth/login', 
                               data=json.dumps({'email': email, 'password': password}),
                               content_type='application/json')
    
    def logout(self):
        """Helper method to logout user."""
        return self.client.post('/api/auth/logout')

class AuthTestCase(StoryForgeTestCase):
    
    def test_login_success(self):
        """Test successful login."""
        self.logout()  # Logout first
        response = self.login('test@example.com', 'testpass')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['email'], 'test@example.com')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        self.logout()
        response = self.login('test@example.com', 'wrongpass')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 401)
        self.assertIn('error', data)
    
    def test_register_success(self):
        """Test successful registration."""
        response = self.client.post('/api/auth/register',
                                  data=json.dumps({
                                      'username': 'newuser',
                                      'email': 'new@example.com',
                                      'password': 'newpass123'
                                  }),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
    
    def test_register_duplicate_email(self):
        """Test registration with existing email."""
        response = self.client.post('/api/auth/register',
                                  data=json.dumps({
                                      'username': 'duplicate',
                                      'email': 'test@example.com',  # Already exists
                                      'password': 'pass123'
                                  }),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)

class ProjectTestCase(StoryForgeTestCase):
    
    def test_create_project(self):
        """Test project creation."""
        response = self.client.post('/api/projects',
                                  data=json.dumps({
                                      'title': 'Test Project',
                                      'description': 'A test project',
                                      'genre': 'mystery'
                                  }),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('project_id', data)
    
    def test_get_projects(self):
        """Test getting user projects."""
        # Create test project
        project = Project(
            title='Test Project',
            description='Test description',
            genre='mystery',
            user_id=self.test_user.id
        )
        db.session.add(project)
        db.session.commit()
        
        response = self.client.get('/api/projects')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], 'Test Project')
    
    def test_get_project_detail(self):
        """Test getting detailed project data."""
        # Create test project with scene
        project = Project(
            title='Test Project',
            user_id=self.test_user.id
        )
        db.session.add(project)
        db.session.flush()
        
        scene = Scene(
            title='Test Scene',
            description='Test scene description',
            project_id=project.id,
            order_index=1
        )
        db.session.add(scene)
        db.session.commit()
        
        response = self.client.get(f'/api/projects/{project.id}')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('project', data)
        self.assertIn('scenes', data)
        self.assertEqual(len(data['scenes']), 1)
        self.assertEqual(data['scenes'][0]['title'], 'Test Scene')

class SceneTestCase(StoryForgeTestCase):
    
    def setUp(self):
        super().setUp()
        # Create test project
        self.project = Project(
            title='Test Project',
            user_id=self.test_user.id
        )
        db.session.add(self.project)
        db.session.commit()
    
    def test_create_scene(self):
        """Test scene creation with AI analysis."""
        response = self.client.post(f'/api/projects/{self.project.id}/scenes',
                                  data=json.dumps({
                                      'title': 'New Scene',
                                      'description': 'Sarah finds a letter in the library',
                                      'scene_type': 'development',
                                      'location': 'Library'
                                  }),
                                  content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('scene_id', data)
        
        # Check that objects were extracted
        scene = Scene.query.get(data['scene_id'])
        self.assertIsNotNone(scene)
        self.assertEqual(scene.title, 'New Scene')
    
    def test_update_scene(self):
        """Test scene update."""
        # Create test scene
        scene = Scene(
            title='Original Title',
            description='Original description',
            project_id=self.project.id,
            order_index=1
        )
        db.session.add(scene)
        db.session.commit()
        
        response = self.client.put(f'/api/scenes/{scene.id}',
                                 data=json.dumps({
                                     'title': 'Updated Title',
                                     'description': 'Updated description'
                                 }),
                                 content_type='application/json')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        
        # Check that scene was updated
        updated_scene = Scene.query.get(scene.id)
        self.assertEqual(updated_scene.title, 'Updated Title')
    
    def test_delete_scene(self):
        """Test scene deletion."""
        # Create test scene
        scene = Scene(
            title='To Delete',
            project_id=self.project.id,
            order_index=1
        )
        db.session.add(scene)
        db.session.commit()
        scene_id = scene.id
        
        response = self.client.delete(f'/api/scenes/{scene_id}')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        
        # Check that scene was deleted
        deleted_scene = Scene.query.get(scene_id)
        self.assertIsNone(deleted_scene)

class AIAnalysisTestCase(StoryForgeTestCase):
    
    def setUp(self):
        super().setUp()
        # Create test project with scenes
        self.project = Project(
            title='Test Project',
            user_id=self.test_user.id
        )
        db.session.add(self.project)
        db.session.flush()
        
        # Add test scenes
        scenes = [
            Scene(title='Scene 1', scene_type='inciting', project_id=self.project.id, order_index=1),
            Scene(title='Scene 2', scene_type='development', project_id=self.project.id, order_index=2),
            Scene(title='Scene 3', scene_type='climax', project_id=self.project.id, order_index=3)
        ]
        for scene in scenes:
            db.session.add(scene)
        
        db.session.commit()
    
    def test_analyze_structure(self):
        """Test AI structure analysis."""
        response = self.client.post(f'/api/projects/{self.project.id}/ai/analyze-structure')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('analysis', data)
        self.assertIn('feedback_id', data)
        
        analysis = data['analysis']
        self.assertEqual(analysis['total_scenes'], 3)
        self.assertIn('scene_types', analysis)
        self.assertIn('recommendations', analysis)
    
    def test_suggest_scenes(self):
        """Test AI scene suggestions."""
        response = self.client.post(f'/api/projects/{self.project.id}/ai/suggest-scenes')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('suggestions', data)
    
    def test_generate_story(self):
        """Test story generation from scenes."""
        response = self.client.post(f'/api/projects/{self.project.id}/ai/generate-story')
        data = json.loads(response.data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTrue(data['success'])
        self.assertIn('story', data)
        
        story = data['story']
        self.assertIn('title', story)
        self.assertIn('premise', story)
        self.assertIn('structure', story)

class TokenTestCase(StoryForgeTestCase):
    
    def test_token_usage_tracking(self):
        """Test that tokens are properly tracked."""
        initial_tokens = self.test_user.tokens_used
        
        # Create a scene (costs 5 tokens)
        project = Project(title='Test', user_id=self.test_user.id)
        db.session.add(project)
        db.session.commit()
        
        response = self.client.post(f'/api/projects/{project.id}/scenes',
                                  data=json.dumps({
                                      'title': 'Test Scene',
                                      'description': 'Test description'
                                  }),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        # Check token usage
        db.session.refresh(self.test_user)
        self.assertEqual(self.test_user.tokens_used, initial_tokens + 5)
    
    def test_insufficient_tokens(self):
        """Test behavior when user has insufficient tokens."""
        # Set user tokens to limit
        self.test_user.tokens_used = self.test_user.tokens_limit
        db.session.commit()
        
        project = Project(title='Test', user_id=self.test_user.id)
        db.session.add(project)
        db.session.commit()
        
        response = self.client.post(f'/api/projects/{project.id}/ai/analyze-structure')
        
        self.assertEqual(response.status_code, 402)
        data = json.loads(response.data)
        self.assertIn('Insufficient tokens', data['error'])

if __name__ == '__main__':
    # Run all tests
    unittest.main()
