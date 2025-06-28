# tests/unit/test_database.py - Modified version that works without TestingConfig
import pytest
import os
from datetime import datetime, timedelta
from app import create_app, db
from app.models import (
    User, Project, Scene, StoryObject, SceneObject, 
    TokenUsageLog, BillingPlan, UserSubscription, 
    ProjectCollaborator, Comment
)

class TestDatabase:
    """Comprehensive database tests for all models and relationships"""
    
    @pytest.fixture
    def app(self):
        """Create test application with in-memory SQLite database"""
        # Use 'development' since we know it exists, and override configs
        app = create_app('development')
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'WTF_CSRF_ENABLED': False,
            'AI_SIMULATION_MODE': True
        })
        
        with app.app_context():
            db.create_all()
            yield app
            db.session.remove()
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Test client"""
        return app.test_client()
    
    def test_user_creation(self, app):
        """Test creating a user"""
        with app.app_context():
            # Create a user
            user = User(
                username='testuser',
                email='test@example.com',
                plan='free',
                tokens_limit=1000
            )
            user.set_password('password123')
            
            db.session.add(user)
            db.session.commit()
            
            # Query the user
            saved_user = User.query.filter_by(email='test@example.com').first()
            
            # Assertions
            assert saved_user is not None
            assert saved_user.username == 'testuser'
            assert saved_user.check_password('password123')
            assert saved_user.plan == 'free'
            assert saved_user.tokens_limit == 1000
            assert saved_user.tokens_used == 0
            assert saved_user.is_active == True
    
    def test_user_password_hashing(self, app):
        """Test password hashing"""
        with app.app_context():
            user = User(username='passwordtest', email='password@test.com')
            user.set_password('mypassword')
            
            db.session.add(user)
            db.session.commit()
            
            # Check hashing
            assert user.password_hash is not None
            assert user.password_hash != 'mypassword'
            assert user.check_password('mypassword')
            assert not user.check_password('wrongpassword')
    
    def test_project_creation(self, app):
        """Test creating a project and its relationships"""
        with app.app_context():
            # Create a user first
            user = User(username='projectuser', email='project@test.com')
            db.session.add(user)
            db.session.flush()
            
            # Create a project
            project = Project(
                title='Test Project',
                description='A test project description',
                genre='mystery',
                current_phase='idea',
                user_id=user.id
            )
            db.session.add(project)
            db.session.commit()
            
            # Query the project
            saved_project = Project.query.filter_by(title='Test Project').first()
            
            # Assertions
            assert saved_project is not None
            assert saved_project.title == 'Test Project'
            assert saved_project.genre == 'mystery'
            assert saved_project.current_phase == 'idea'
            assert saved_project.user_id == user.id
            
            # Test user-project relationship
            assert saved_project in user.projects.all()
    
    def test_scene_creation_and_ordering(self, app):
        """Test creating scenes with proper ordering"""
        with app.app_context():
            # Create user and project
            user = User(username='sceneuser', email='scene@test.com')
            db.session.add(user)
            db.session.flush()
            
            project = Project(title='Scene Project', user_id=user.id)
            db.session.add(project)
            db.session.flush()
            
            # Create scenes with specific order
            scenes = [
                Scene(title='Scene 1', order_index=1, project_id=project.id, scene_type='opening'),
                Scene(title='Scene 2', order_index=2, project_id=project.id, scene_type='inciting'),
                Scene(title='Scene 3', order_index=3, project_id=project.id, scene_type='development')
            ]
            
            for scene in scenes:
                db.session.add(scene)
            
            db.session.commit()
            
            # Query scenes in order
            saved_scenes = Scene.query.filter_by(project_id=project.id).order_by(Scene.order_index).all()
            
            # Assertions
            assert len(saved_scenes) == 3
            assert saved_scenes[0].title == 'Scene 1'
            assert saved_scenes[1].title == 'Scene 2'
            assert saved_scenes[2].title == 'Scene 3'
            
            # Test project-scene relationship
            assert len(project.scenes.all()) == 3
    
    def test_story_objects_and_scene_relationships(self, app):
        """Test story objects and their relationships with scenes"""
        with app.app_context():
            # Create user and project
            user = User(username='objectuser', email='object@test.com')
            db.session.add(user)
            db.session.flush()
            
            project = Project(title='Object Project', user_id=user.id)
            db.session.add(project)
            db.session.flush()
            
            # Create a scene
            scene = Scene(title='Object Scene', project_id=project.id, order_index=1)
            db.session.add(scene)
            db.session.flush()
            
            # Create story objects
            objects = [
                StoryObject(name='Character 1', object_type='character', project_id=project.id),
                StoryObject(name='Location 1', object_type='location', project_id=project.id),
                StoryObject(name='Item 1', object_type='object', project_id=project.id)
            ]
            
            for obj in objects:
                db.session.add(obj)
            
            db.session.flush()
            
            # Link objects to scene
            scene_objects = [
                SceneObject(scene_id=scene.id, object_id=objects[0].id, role='main'),
                SceneObject(scene_id=scene.id, object_id=objects[1].id, role='supporting'),
                SceneObject(scene_id=scene.id, object_id=objects[2].id, role='supporting')
            ]
            
            for scene_obj in scene_objects:
                db.session.add(scene_obj)
            
            db.session.commit()
            
            # Verify relationships
            saved_scene = Scene.query.get(scene.id)
            assert len(saved_scene.scene_objects.all()) == 3
            
            # Test object retrieval through relationship
            scene_character = saved_scene.scene_objects.filter_by(role='main').first().story_object
            assert scene_character.name == 'Character 1'
            assert scene_character.object_type == 'character'
    
    def test_token_usage_logging(self, app):
        """Test token usage logging functionality"""
        with app.app_context():
            # Create user and project
            user = User(username='tokenuser', email='token@test.com')
            db.session.add(user)
            db.session.flush()
            
            project = Project(title='Token Project', user_id=user.id)
            db.session.add(project)
            db.session.flush()
            
            # Create token usage log
            token_log = TokenUsageLog(
                user_id=user.id,
                operation_type='analyze_idea',
                input_tokens=100,
                output_tokens=50,
                total_cost=15,
                project_id=project.id,
                ai_model_used='claude-3-5-sonnet',
                response_time_ms=1500,
                billable=True
            )
            
            db.session.add(token_log)
            db.session.commit()
            
            # Query token logs
            saved_log = TokenUsageLog.query.filter_by(user_id=user.id).first()
            
            # Assertions
            assert saved_log is not None
            assert saved_log.operation_type == 'analyze_idea'
            assert saved_log.total_cost == 15
            assert saved_log.ai_model_used == 'claude-3-5-sonnet'
            
            # Test relationships
            assert saved_log.user == user
            assert saved_log.project == project
    
    def test_billing_plans_and_subscriptions(self, app):
        """Test billing plans and user subscriptions"""
        with app.app_context():
            # Create user
            user = User(username='subuser', email='sub@test.com')
            db.session.add(user)
            db.session.flush()
            
            # Create billing plan
            plan = BillingPlan(
                name='pro',
                display_name='Pro Plan',
                monthly_token_limit=10000,
                monthly_price_cents=1999,
                features=['full_ai_suite', 'unlimited_scenes'],
                is_active=True
            )
            db.session.add(plan)
            db.session.flush()
            
            # Create subscription
            now = datetime.utcnow()
            subscription = UserSubscription(
                user_id=user.id,
                plan_id=plan.id,
                status='active',
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
                tokens_used_this_period=150,
                stripe_subscription_id='sub_123456'
            )
            db.session.add(subscription)
            db.session.commit()
            
            # Query subscription
            saved_sub = UserSubscription.query.filter_by(user_id=user.id).first()
            
            # Assertions
            assert saved_sub is not None
            assert saved_sub.status == 'active'
            assert saved_sub.tokens_used_this_period == 150
            
            # Test relationships
            assert saved_sub.user == user
            assert saved_sub.plan == plan
            assert saved_sub.plan.monthly_token_limit == 10000
    
    def test_collaboration_functionality(self, app):
        """Test collaboration functionality between users"""
        with app.app_context():
            # Create users
            owner = User(username='owner', email='owner@test.com')
            collaborator = User(username='collaborator', email='collab@test.com')
            db.session.add_all([owner, collaborator])
            db.session.flush()
            
            # Create project
            project = Project(title='Collab Project', user_id=owner.id)
            db.session.add(project)
            db.session.flush()
            
            # Set up collaboration
            collab = ProjectCollaborator(
                project_id=project.id,
                user_id=collaborator.id,
                role='editor',
                permissions={'edit_scenes': True, 'add_comments': True},
                status='active',
                invited_by=owner.id
            )
            db.session.add(collab)
            db.session.commit()
            
            # Query collaboration
            saved_collab = ProjectCollaborator.query.filter_by(
                project_id=project.id, 
                user_id=collaborator.id
            ).first()
            
            # Assertions
            assert saved_collab is not None
            assert saved_collab.role == 'editor'
            assert saved_collab.permissions.get('edit_scenes') == True
            
            # Test relationships
            assert saved_collab.user == collaborator
            assert saved_collab.project == project
            assert saved_collab.inviter == owner
    
    def test_comments_and_threading(self, app):
        """Test comment functionality with threading"""
        with app.app_context():
            # Create users
            user1 = User(username='user1', email='user1@test.com')
            user2 = User(username='user2', email='user2@test.com')
            db.session.add_all([user1, user2])
            db.session.flush()
            
            # Create project and scene
            project = Project(title='Comment Project', user_id=user1.id)
            db.session.add(project)
            db.session.flush()
            
            scene = Scene(title='Comment Scene', project_id=project.id, order_index=1)
            db.session.add(scene)
            db.session.flush()
            
            # Create parent comment
            parent_comment = Comment(
                content='This is a parent comment',
                project_id=project.id,
                scene_id=scene.id,
                user_id=user1.id,
                thread_depth=0,
                comment_type='general'
            )
            db.session.add(parent_comment)
            db.session.flush()
            
            # Create reply comment
            reply_comment = Comment(
                content='This is a reply',
                project_id=project.id,
                scene_id=scene.id,
                user_id=user2.id,
                parent_comment_id=parent_comment.id,
                thread_depth=1,
                comment_type='general'
            )
            db.session.add(reply_comment)
            db.session.commit()
            
            # Query comments
            parent = Comment.query.filter_by(thread_depth=0).first()
            reply = Comment.query.filter_by(thread_depth=1).first()
            
            # Assertions
            assert parent is not None
            assert reply is not None
            assert reply.parent_comment_id == parent.id
            
            # Test relationships
            assert reply.parent == parent
            assert reply in parent.replies
            assert reply.user == user2
    
    def test_cascade_delete(self, app):
        """Test cascade delete functionality"""
        with app.app_context():
            # Create user and project
            user = User(username='cascadeuser', email='cascade@test.com')
            db.session.add(user)
            db.session.flush()
            
            project = Project(title='Cascade Project', user_id=user.id)
            db.session.add(project)
            db.session.flush()
            
            # Create scenes
            scene = Scene(title='Cascade Scene', project_id=project.id, order_index=1)
            db.session.add(scene)
            db.session.flush()
            
            # Create story object
            obj = StoryObject(name='Cascade Object', object_type='object', project_id=project.id)
            db.session.add(obj)
            db.session.flush()
            
            # Link object to scene
            scene_obj = SceneObject(scene_id=scene.id, object_id=obj.id)
            db.session.add(scene_obj)
            
            db.session.commit()
            
            # Verify initial state
            assert Scene.query.count() == 1
            assert StoryObject.query.count() == 1
            assert SceneObject.query.count() == 1
            
            # Delete project (should cascade)
            db.session.delete(project)
            db.session.commit()
            
            # Verify cascade deletion
            assert Scene.query.count() == 0
            assert StoryObject.query.count() == 0
            assert SceneObject.query.count() == 0
    
    def test_custom_model_methods(self, app):
        """Test custom methods on models"""
        with app.app_context():
            # Create user
            user = User(username='methoduser', email='method@test.com')
            db.session.add(user)
            db.session.flush()
            
            # Test to_dict method
            user_dict = user.to_dict()
            assert 'username' in user_dict
            assert 'email' in user_dict
            assert 'password_hash' not in user_dict  # Sensitive data excluded
            
            # Create project
            project = Project(title='Method Project', user_id=user.id)
            db.session.add(project)
            db.session.commit()
            
            # Test project to_dict
            project_dict = project.to_dict()
            assert 'id' in project_dict
            assert 'title' in project_dict
            assert project_dict['title'] == 'Method Project'
    
    def test_json_fields(self, app):
        """Test JSON fields in models"""
        with app.app_context():
            # Create project with JSON attributes
            user = User(username='jsonuser', email='json@test.com')
            db.session.add(user)
            db.session.flush()
            
            project = Project(
                title='JSON Project', 
                user_id=user.id,
                attributes={'theme': 'mystery', 'keywords': ['detective', 'crime']}
            )
            db.session.add(project)
            db.session.commit()
            
            # Query project
            saved_project = Project.query.filter_by(title='JSON Project').first()
            
            # Test JSON field
            assert saved_project.attributes is not None
            assert 'theme' in saved_project.attributes
            assert saved_project.attributes['theme'] == 'mystery'
            assert 'keywords' in saved_project.attributes
            assert 'detective' in saved_project.attributes['keywords']
    
    def test_token_limits_and_usage(self, app):
        """Test token limits and usage tracking"""
        with app.app_context():
            # Create user with token limit
            user = User(
                username='tokentracker',
                email='tracker@test.com',
                plan='pro',
                tokens_limit=10000,
                tokens_used=500
            )
            db.session.add(user)
            db.session.commit()
            
            # Update token usage
            user.tokens_used += 100
            db.session.commit()
            
            # Query user
            updated_user = User.query.filter_by(email='tracker@test.com').first()
            
            # Assertions
            assert updated_user.tokens_used == 600
            assert updated_user.tokens_limit == 10000
            
            # Test remaining tokens
            remaining = updated_user.tokens_limit - updated_user.tokens_used
            assert remaining == 9400