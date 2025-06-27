# app/models.py - EXTENDED Database Models with Project Attributes
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
    
    # NEW: Additional project metadata
    attributes = db.Column(db.JSON)  # For story_intent, themes, etc.
    tone = db.Column(db.String(50))  # dark, light, mysterious, comedic
    target_audience = db.Column(db.String(50))  # children, YA, adult
    estimated_scope = db.Column(db.String(50))  # short-story, novella, novel
    marketability = db.Column(db.Integer, default=3)  # 1-5 scale
    original_idea = db.Column(db.Text)  # Store original idea text
    
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
            'tone': self.tone,
            'target_audience': self.target_audience,
            'estimated_scope': self.estimated_scope,
            'marketability': self.marketability,
            'attributes': self.attributes or {},
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
    
    # NEW: Additional scene metadata
    hook = db.Column(db.Text)  # Scene hook/opening
    character_focus = db.Column(db.String(200))  # Which character is focus
    
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
            'hook': self.hook,
            'character_focus': self.character_focus,
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
    
    # NEW: Additional object metadata
    first_appearance = db.Column(db.Integer)  # Scene order where first appears
    symbolic_meaning = db.Column(db.Text)  # Symbolic significance
    character_role = db.Column(db.String(50))  # For characters: protagonist, antagonist, etc.
    
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
            'scene_count': self.scene_objects.count(),
            'first_appearance': self.first_appearance,
            'symbolic_meaning': self.symbolic_meaning,
            'character_role': self.character_role,
            'attributes': self.attributes or {}
        }

class SceneObject(db.Model):
    """Many-to-many relationship between scenes and objects"""
    __tablename__ = 'scene_object'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50))
    transformation = db.Column(db.Text)
    
    # NEW: Additional relationship metadata
    significance = db.Column(db.String(20), default='supporting')  # main, supporting, background
    interaction_type = db.Column(db.String(50))  # dialogue, action, presence
    
    # Foreign Keys
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'), nullable=False, index=True)
    object_id = db.Column(db.Integer, db.ForeignKey('story_object.id'), nullable=False, index=True)

# NEW: Template system for idea generation
class IdeaTemplate(db.Model):
    """Predefined templates for idea generation"""
    __tablename__ = 'idea_template'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), index=True)
    prompt_template = db.Column(db.Text, nullable=False)
    example_variables = db.Column(db.JSON)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'genre': self.genre,
            'prompt_template': self.prompt_template,
            'example_variables': self.example_variables or {},
            'description': self.description,
            'usage_count': self.usage_count
        }