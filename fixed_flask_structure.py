# app/__init__.py - App Factory
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO()

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register blueprints
    from app.auth import auth_bp
    from app.projects import projects_bp
    from app.scenes import scenes_bp
    from app.ai import ai_bp
    from app.collaboration import collaboration_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(scenes_bp, url_prefix='/api/scenes')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(collaboration_bp, url_prefix='/api/collaboration')
    
    # Register CLI commands
    from app.cli import init_db_command
    app.cli.add_command(init_db_command)
    
    return app

# app/models.py - Database Models
from app import db
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    plan = db.Column(db.String(20), default='free', index=True)
    tokens_used = db.Column(db.Integer, default=0)
    tokens_limit = db.Column(db.Integer, default=1000)
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    projects = db.relationship('Project', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'plan': self.plan,
            'tokens_used': self.tokens_used,
            'tokens_limit': self.tokens_limit,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Project(db.Model):
    __tablename__ = 'project'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    genre = db.Column(db.String(50), index=True)
    current_phase = db.Column(db.String(20), default='idea', index=True)
    target_word_count = db.Column(db.Integer, default=50000)
    current_word_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # Relationships
    scenes = db.relationship('Scene', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    story_objects = db.relationship('StoryObject', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'genre': self.genre,
            'current_phase': self.current_phase,
            'current_word_count': self.current_word_count,
            'scene_count': self.scenes.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Scene(db.Model):
    __tablename__ = 'scene'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    scene_type = db.Column(db.String(50), index=True)
    order_index = db.Column(db.Integer, index=True)
    location = db.Column(db.String(200))
    conflict = db.Column(db.Text)
    emotional_intensity = db.Column(db.Float, default=0.5)
    word_count = db.Column(db.Integer, default=0)
    dialog_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    
    # Relationships
    scene_objects = db.relationship('SceneObject', backref='scene', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'scene_type': self.scene_type,
            'order_index': self.order_index,
            'location': self.location,
            'conflict': self.conflict,
            'emotional_intensity': self.emotional_intensity,
            'word_count': self.word_count,
            'dialog_count': self.dialog_count,
            'objects': [so.story_object.to_dict() for so in self.scene_objects.all()],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class StoryObject(db.Model):
    __tablename__ = 'story_object'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    object_type = db.Column(db.String(50), index=True)  # character, location, prop, conflict
    description = db.Column(db.Text)
    importance = db.Column(db.String(20), default='medium', index=True)
    status = db.Column(db.String(20), default='active', index=True)
    attributes = db.Column(db.JSON)
    
    # Foreign Keys
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    
    # Relationships
    scene_objects = db.relationship('SceneObject', backref='story_object', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'object_type': self.object_type,
            'description': self.description,
            'importance': self.importance,
            'status': self.status,
            'scene_count': self.scene_objects.count()
        }

class SceneObject(db.Model):
    """Many-to-many relationship between scenes and objects"""
    __tablename__ = 'scene_object'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50))
    transformation = db.Column(db.Text)
    
    # Foreign Keys
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'), nullable=False, index=True)
    object_id = db.Column(db.Integer, db.ForeignKey('story_object.id'), nullable=False, index=True)

# app/auth/__init__.py
from flask import Blueprint

auth_bp = Blueprint('auth', __name__)

from app.auth import routes

# app/auth/routes.py - Authentication Routes
from flask import request, jsonify, session
from app.auth import auth_bp
from app.models import User
from app import db

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    if user and user.check_password(data.get('password')):
        session['user_id'] = user.id
        user.last_login = db.func.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data.get('username'),
        email=data.get('email'),
        plan='free',
        tokens_limit=1000
    )
    user.set_password(data.get('password'))
    
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    return jsonify({'success': True, 'user': user.to_dict()})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True})

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()})

# app/projects/__init__.py
from flask import Blueprint

projects_bp = Blueprint('projects', __name__)

from app.projects import routes

# app/projects/routes.py - Project Routes
from flask import request, jsonify, session
from app.projects import projects_bp
from app.models import Project, Scene, StoryObject
from app.utils.auth import login_required
from app import db

@projects_bp.route('', methods=['GET'])
@login_required
def get_projects():
    projects = Project.query.filter_by(user_id=session['user_id']).all()
    return jsonify([p.to_dict() for p in projects])

@projects_bp.route('', methods=['POST'])
@login_required
def create_project():
    data = request.get_json()
    
    project = Project(
        title=data.get('title'),
        description=data.get('description'),
        genre=data.get('genre'),
        user_id=session['user_id']
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify({'success': True, 'project': project.to_dict()})

@projects_bp.route('/<project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    objects = StoryObject.query.filter_by(project_id=project_id).all()
    
    return jsonify({
        'project': project.to_dict(),
        'scenes': [s.to_dict() for s in scenes],
        'objects': [o.to_dict() for o in objects]
    })

# app/scenes/__init__.py
from flask import Blueprint

scenes_bp = Blueprint('scenes', __name__)

from app.scenes import routes

# app/scenes/routes.py - Scene Routes
from flask import request, jsonify, session
from app.scenes import scenes_bp
from app.models import Scene, Project, StoryObject, SceneObject
from app.utils.auth import login_required, check_tokens, use_tokens
from app.services.ai_analyzer import AIAnalyzer
from app import db

@scenes_bp.route('', methods=['POST'])
@login_required
@check_tokens(5)
def create_scene():
    data = request.get_json()
    project_id = data.get('project_id')
    
    # Verify project ownership
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    # Get next order index
    last_scene = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index.desc()).first()
    order_index = (last_scene.order_index + 1) if last_scene else 1
    
    # Create scene
    scene = Scene(
        title=data.get('title'),
        description=data.get('description'),
        scene_type=data.get('scene_type', 'development'),
        order_index=order_index,
        location=data.get('location'),
        conflict=data.get('conflict'),
        project_id=project_id
    )
    
    db.session.add(scene)
    db.session.flush()
    
    # AI Analysis of scene description
    if scene.description:
        extracted_objects = AIAnalyzer.analyze_scene_objects(scene.description)
        
        # Create/find objects and link to scene
        for obj_type, obj_names in extracted_objects.items():
            for obj_name in obj_names:
                story_obj = StoryObject.query.filter_by(
                    project_id=project_id,
                    name=obj_name
                ).first()
                
                if not story_obj:
                    story_obj = StoryObject(
                        name=obj_name,
                        object_type=obj_type.rstrip('s'),
                        project_id=project_id,
                        status='active'
                    )
                    db.session.add(story_obj)
                    db.session.flush()
                
                scene_obj = SceneObject(
                    scene_id=scene.id,
                    object_id=story_obj.id,
                    role='main' if obj_type == 'characters' else 'supporting'
                )
                db.session.add(scene_obj)
    
    db.session.commit()
    use_tokens(5)
    
    return jsonify({'success': True, 'scene': scene.to_dict()})

@scenes_bp.route('/<int:scene_id>', methods=['PUT'])
@login_required
def update_scene(scene_id):
    scene = Scene.query.get_or_404(scene_id)
    
    # Verify ownership
    if scene.project.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    data = request.get_json()
    scene.title = data.get('title', scene.title)
    scene.description = data.get('description', scene.description)
    scene.scene_type = data.get('scene_type', scene.scene_type)
    scene.location = data.get('location', scene.location)
    scene.conflict = data.get('conflict', scene.conflict)
    
    db.session.commit()
    return jsonify({'success': True, 'scene': scene.to_dict()})

@scenes_bp.route('/<int:scene_id>', methods=['DELETE'])
@login_required
def delete_scene(scene_id):
    scene = Scene.query.get_or_404(scene_id)
    
    # Verify ownership
    if scene.project.user_id != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(scene)
    db.session.commit()
    
    return jsonify({'success': True})

# app/ai/__init__.py
from flask import Blueprint

ai_bp = Blueprint('ai', __name__)

from app.ai import routes

# app/ai/routes.py - AI Analysis Routes
from flask import request, jsonify, session
from app.ai import ai_bp
from app.models import Project, Scene
from app.utils.auth import login_required, check_tokens, use_tokens
from app.services.ai_analyzer import AIAnalyzer
from app import db

@ai_bp.route('/projects/<project_id>/analyze-structure', methods=['POST'])
@login_required
@check_tokens(15)
def analyze_structure(project_id):
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).all()
    analysis = AIAnalyzer.analyze_story_structure(scenes)
    
    use_tokens(15)
    
    return jsonify({
        'success': True,
        'analysis': analysis
    })

@ai_bp.route('/projects/<project_id>/suggest-scenes', methods=['POST'])
@login_required
@check_tokens(10)
def suggest_scenes(project_id):
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    suggestions = AIAnalyzer.suggest_next_scenes(project_id)
    use_tokens(10)
    
    return jsonify({
        'success': True,
        'suggestions': suggestions
    })

# app/collaboration/__init__.py
from flask import Blueprint

collaboration_bp = Blueprint('collaboration', __name__)

from app.collaboration import routes

# app/collaboration/routes.py - Collaboration Routes
from flask import request, jsonify, session
from app.collaboration import collaboration_bp
from app.models import Project
from app.utils.auth import login_required
from app import db

@collaboration_bp.route('/projects/<project_id>/invite', methods=['POST'])
@login_required
def invite_collaborator(project_id):
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    data = request.get_json()
    # Placeholder for collaboration logic
    
    return jsonify({'success': True, 'message': 'Invitation sent'})

# app/utils/auth.py - Authentication Utilities
from functools import wraps
from flask import session, jsonify
from app.models import User
from app import db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def check_tokens(tokens_needed):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' in session:
                user = User.query.get(session['user_id'])
                if user and user.tokens_used + tokens_needed > user.tokens_limit:
                    return jsonify({'error': 'Insufficient tokens'}), 402
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def use_tokens(tokens_used):
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user.tokens_used += tokens_used
            db.session.commit()

# app/services/ai_analyzer.py - AI Services
import time
import random
from app.models import StoryObject

class AIAnalyzer:
    @staticmethod
    def analyze_scene_objects(scene_description):
        """Extract objects from scene description"""
        time.sleep(0.5)  # Simulate processing
        
        keywords = {
            'characters': [],
            'locations': [],
            'objects': [],
            'conflicts': []
        }
        
        description_lower = scene_description.lower()
        
        # Character detection
        if 'sarah' in description_lower:
            keywords['characters'].append('Sarah')
        if 'pavel' in description_lower:
            keywords['characters'].append('Pavel')
        if 'matka' in description_lower or 'máma' in description_lower:
            keywords['characters'].append('Matka')
        
        # Location detection  
        if 'knihovna' in description_lower:
            keywords['locations'].append('Knihovna')
        if 'pokoj' in description_lower:
            keywords['locations'].append('Babičcin pokoj')
        if 'kavárna' in description_lower:
            keywords['locations'].append('Kavárna')
        
        # Object detection
        if 'dopis' in description_lower:
            keywords['objects'].append('Zakódovaný dopis')
        if 'fotografie' in description_lower:
            keywords['objects'].append('Stará fotografie')
        if 'kniha' in description_lower:
            keywords['objects'].append('Tajemná kniha')
        
        return keywords
    
    @staticmethod
    def analyze_story_structure(scenes):
        """Analyze overall story structure"""
        analysis = {
            'total_scenes': len(scenes),
            'scene_types': {},
            'continuity_score': round(random.uniform(0.7, 0.9), 2),
            'pacing_score': round(random.uniform(0.6, 0.8), 2),
            'missing_elements': [],
            'recommendations': []
        }
        
        # Count scene types
        for scene in scenes:
            scene_type = scene.scene_type or 'development'
            analysis['scene_types'][scene_type] = analysis['scene_types'].get(scene_type, 0) + 1
        
        # Check for missing elements
        if 'inciting' not in analysis['scene_types']:
            analysis['missing_elements'].append('inciting_incident')
        if 'climax' not in analysis['scene_types']:
            analysis['missing_elements'].append('climax')
        if 'resolution' not in analysis['scene_types']:
            analysis['missing_elements'].append('resolution')
        
        # Generate recommendations
        if len(scenes) < 5:
            analysis['recommendations'].append('Consider adding more scenes for fuller story development')
        if analysis['scene_types'].get('development', 0) < 2:
            analysis['recommendations'].append('Add more development scenes to build tension')
        
        return analysis
    
    @staticmethod
    def suggest_next_scenes(project_id):
        """Suggest next scenes based on unused objects"""
        unused_objects = StoryObject.query.filter_by(
            project_id=project_id,
            status='unused'
        ).all()
        
        suggestions = []
        for obj in unused_objects[:3]:
            suggestion = {
                'title': f'Scene exploring {obj.name}',
                'description': f'A scene that develops the role of {obj.name} in the story.',
                'suggested_objects': [obj.name],
                'scene_type': 'development',
                'confidence': round(random.uniform(0.7, 0.95), 2)
            }
            suggestions.append(suggestion)
        
        # Add generic suggestions if no unused objects
        if not suggestions:
            suggestions = [
                {
                    'title': 'Character development scene',
                    'description': 'A scene focusing on character backstory and motivation.',
                    'scene_type': 'development',
                    'confidence': 0.75
                },
                {
                    'title': 'Conflict escalation',
                    'description': 'A scene that raises the stakes and increases tension.',
                    'scene_type': 'rising_action',
                    'confidence': 0.80
                }
            ]
        
        return suggestions

# app/cli.py - CLI Commands for Database
import click
from flask.cli import with_appcontext
from app import db
from app.models import User, Project, Scene, StoryObject

@click.command()
@with_appcontext
def init_db_command():
    """Initialize database with demo data"""
    # Drop and create all tables
    db.drop_all()
    db.create_all()
    
    # Create demo user
    demo_user = User(
        username='demo',
        email='demo@storyforge.ai',
        plan='pro',
        tokens_limit=10000
    )
    demo_user.set_password('demo123')
    db.session.add(demo_user)
    db.session.flush()
    
    # Create demo project
    demo_project = Project(
        title='Tajemství babičky Anny',
        description='Mladá žena objevuje válečné tajemství své babičky skrze zakódované zprávy.',
        genre='mystery',
        current_phase='expand',
        user_id=demo_user.id
    )
    db.session.add(demo_project)
    db.session.flush()
    
    # Create demo objects
    objects = [
        StoryObject(name='Sarah', object_type='character', project_id=demo_project.id, importance='high'),
        StoryObject(name='Zakódovaný dopis', object_type='object', project_id=demo_project.id, importance='high'),
        StoryObject(name='Stará fotografie', object_type='object', project_id=demo_project.id, status='unused'),
        StoryObject(name='Babičcin pokoj', object_type='location', project_id=demo_project.id),
    ]
    
    for obj in objects:
        db.session.add(obj)
    
    # Create demo scenes
    scenes = [
        Scene(
            title='Objev dopisu',
            description='Sarah při úklidu po babičce objeví v její skříňce zakódovaný dopis a starou fotografii ženy v uniformě.',
            scene_type='inciting',
            order_index=1,
            project_id=demo_project.id,
            location='Babičcin podkrovní pokoj'
        ),
        Scene(
            title='Dekódování zprávy',
            description='Sarah se obrací na knihovníka Pavla s prosbou o pomoc s dekódováním. Objevují válečnou šifru.',
            scene_type='development',
            order_index=2,
            project_id=demo_project.id,
            location='Knihovna'
        )
    ]
    
    for scene in scenes:
        db.session.add(scene)
    
    db.session.commit()
    click.echo('Database initialized with demo data!')

# config.py - Updated Configuration
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///storyforge.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Token limits by plan
    TOKEN_LIMITS = {
        'free': 1000,
        'pro': 10000,
        'enterprise': 50000
    }

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///storyforge_dev.db'

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# run.py - Application Runner
import os
from app import create_app, socketio

config_name = os.getenv('FLASK_CONFIG', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    socketio.run(
        app,
        debug=app.config.get('DEBUG', False),
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )

# requirements.txt - Updated Dependencies
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-CORS==4.0.0
Flask-SocketIO==5.3.6
python-socketio==5.8.0
Werkzeug==2.3.7
python-dotenv==1.0.0
click==8.1.7