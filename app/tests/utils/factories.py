# tests/utils/factories.py - Test Data Factories
import factory
from datetime import datetime
from app.models import User, Project, Scene, StoryObject
from app import db

class UserFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating test users"""
    
    class Meta:
        model = User
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    plan = 'pro'
    tokens_limit = 10000
    tokens_used = 0
    
    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        if not create:
            return
        obj.set_password('testpassword')

class ProjectFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating test projects"""
    
    class Meta:
        model = Project
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    title = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text', max_nb_chars=200)
    genre = factory.Faker('random_element', elements=('mystery', 'romance', 'sci-fi', 'fantasy'))
    current_phase = 'expand'
    user = factory.SubFactory(UserFactory)

class SceneFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Factory for creating test scenes"""
    
    class Meta:
        model = Scene
        sqlalchemy_session = db.session
        sqlalchemy_session_persistence = 'commit'
    
    title = factory.Faker('sentence', nb_words=4)
    description = factory.Faker('text', max_nb_chars=500)
    scene_type = factory.Faker('random_element', 
                              elements=('opening', 'inciting', 'development', 'climax', 'resolution'))
    order_index = factory.Sequence(lambda n: n + 1)
    emotional_intensity = factory.Faker('pyfloat', left_digits=0, right_digits=1, 
                                       positive=True, min_value=0, max_value=1)
    word_count = factory.Faker('pyint', min_value=100, max_value=1000)
    project = factory.SubFactory(ProjectFactory)