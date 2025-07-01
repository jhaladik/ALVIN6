# app/models.py - COMPLETE Database Models with Fixed Foreign Key References
from app import db
from datetime import datetime
import uuid
import json
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    """User model for authentication and user management"""
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

class BillingPlan(db.Model):
    """Billing plans for subscription management"""
    __tablename__ = 'billing_plan'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(100), nullable=False)
    monthly_token_limit = db.Column(db.Integer, nullable=False)
    max_projects = db.Column(db.Integer, default=-1)  # -1 = unlimited
    max_collaborators = db.Column(db.Integer, default=0)
    monthly_price_cents = db.Column(db.Integer, nullable=False)
    token_overage_price_per_1k_cents = db.Column(db.Integer, default=0)
    features = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('UserSubscription', backref='plan', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'monthly_token_limit': self.monthly_token_limit,
            'max_projects': self.max_projects,
            'max_collaborators': self.max_collaborators,
            'monthly_price_cents': self.monthly_price_cents,
            'token_overage_price_per_1k_cents': self.token_overage_price_per_1k_cents,
            'features': self.features or [],
            'is_active': self.is_active,
            'is_public': self.is_public
        }

class UserSubscription(db.Model):
    """User subscription to billing plans"""
    __tablename__ = 'user_subscription'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('billing_plan.id'), nullable=False, index=True)
    status = db.Column(db.String(20), default='active', index=True)
    stripe_subscription_id = db.Column(db.String(100), unique=True)
    stripe_customer_id = db.Column(db.String(100))
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    tokens_used_this_period = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='subscription')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan': self.plan.to_dict() if self.plan else None,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'tokens_used_this_period': self.tokens_used_this_period
        }

class Project(db.Model):
    """Main project model for story projects"""
    __tablename__ = 'project'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    genre = db.Column(db.String(50), index=True)
    current_phase = db.Column(db.String(20), default='idea', index=True)
    target_word_count = db.Column(db.Integer, default=50000)
    current_word_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    
    # Additional project metadata
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
    collaborators = db.relationship('ProjectCollaborator', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    token_usage_logs = db.relationship('TokenUsageLog', backref='project', lazy='dynamic')
    
    def to_dict(self):
        """Convert project to dictionary"""
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'genre': self.genre,
            'current_phase': self.current_phase,
            'target_word_count': self.target_word_count,
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
        
        # Add story info if available
        story = Story.query.filter_by(project_id=self.id).first()
        if story:
            result['story_id'] = story.id
            result['story_title'] = story.title
            result['word_count'] = story.word_count
        
        return result

class Scene(db.Model):
    """Scene model for individual story scenes"""
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
    
    # Additional scene metadata
    hook = db.Column(db.Text)  # Scene hook/opening
    character_focus = db.Column(db.String(200))  # Which character is focus
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys - FIXED: Reference correct table name
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    
    # Relationships
    scene_objects = db.relationship('SceneObject', backref='scene', lazy='dynamic', cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='scene', lazy='dynamic', cascade='all, delete-orphan')
    token_usage_logs = db.relationship('TokenUsageLog', backref='scene', lazy='dynamic')
    
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
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StoryObject(db.Model):
    """Story objects (characters, locations, props, conflicts)"""
    __tablename__ = 'story_object'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    object_type = db.Column(db.String(50), index=True)  # character, location, prop, conflict
    description = db.Column(db.Text)
    importance = db.Column(db.String(20), default='medium', index=True)
    status = db.Column(db.String(20), default='active', index=True)
    attributes = db.Column(db.JSON)
    
    # Additional object metadata
    first_appearance = db.Column(db.Integer)  # Scene order where first appears
    symbolic_meaning = db.Column(db.Text)  # Symbolic significance
    character_role = db.Column(db.String(50))  # For characters: protagonist, antagonist, etc.
    
    # Foreign Keys - FIXED: Reference correct table name
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
    
    # Additional relationship metadata
    significance = db.Column(db.String(20), default='supporting')  # main, supporting, background
    interaction_type = db.Column(db.String(50))  # dialogue, action, presence
    
    # Foreign Keys - FIXED: Reference correct table names
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'), nullable=False, index=True)
    object_id = db.Column(db.Integer, db.ForeignKey('story_object.id'), nullable=False, index=True)

class Story(db.Model):
    """Story model - final narrative content generated from scenes"""
    __tablename__ = 'story'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    premise = db.Column(db.Text)
    content = db.Column(db.Text)
    story_metadata = db.Column(db.Text)  # JSON string with genre, theme, etc.
    word_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys - FIXED: Reference correct table name and type
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    
    # Relationships
    chapters = db.relationship('StoryChapter', backref='story', cascade='all, delete-orphan')
    
    # Add relationship back to project
    project = db.relationship('Project', backref=db.backref('story', uselist=False))
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'premise': self.premise,
            'content': self.content,
            'metadata': json.loads(self.story_metadata) if self.story_metadata else {},
            'word_count': self.word_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StoryChapter(db.Model):
    """Chapter model - sections of a story"""
    __tablename__ = 'story_chapter'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    scene_ids = db.Column(db.Text)  # JSON array of scene IDs
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys - FIXED: Reference correct table name
    story_id = db.Column(db.Integer, db.ForeignKey('story.id'), nullable=False, index=True)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'story_id': self.story_id,
            'title': self.title,
            'content': self.content,
            'scenes': json.loads(self.scene_ids) if self.scene_ids else [],
            'order': self.order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProjectCollaborator(db.Model):
    """Collaboration permissions for projects"""
    __tablename__ = 'project_collaborator'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), default='viewer', index=True)
    permissions = db.Column(db.JSON)
    status = db.Column(db.String(20), default='pending', index=True)
    invitation_token = db.Column(db.String(100), unique=True)
    
    # Foreign Keys - FIXED: Reference correct table names
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    invited_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    invited_at = db.Column(db.DateTime, default=datetime.utcnow)
    joined_at = db.Column(db.DateTime)
    last_access = db.Column(db.DateTime)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='collaborations')
    inviter = db.relationship('User', foreign_keys=[invited_by])
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('project_id', 'user_id', name='unique_project_user'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email
            } if self.user else None,
            'role': self.role,
            'permissions': self.permissions or {},
            'status': self.status,
            'invited_at': self.invited_at.isoformat() if self.invited_at else None,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'last_access': self.last_access.isoformat() if self.last_access else None
        }

class Comment(db.Model):
    """Comments on scenes or projects"""
    __tablename__ = 'comment'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    
    # Target (either scene or project level)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), nullable=False)
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'))  # Optional - project level if None
    
    # Author
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Threading
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    thread_depth = db.Column(db.Integer, default=0)
    
    # Status
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    resolved_at = db.Column(db.DateTime)
    
    # Metadata
    comment_type = db.Column(db.String(20), default='general')  # general, suggestion, issue, praise
    position_data = db.Column(db.JSON)  # For highlighting specific text portions
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='comments')
    resolver = db.relationship('User', foreign_keys=[resolved_by])
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]))
    
    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'project_id': self.project_id,
            'scene_id': self.scene_id,
            'user': {
                'id': self.user.id,
                'username': self.user.username
            } if self.user else None,
            'parent_comment_id': self.parent_comment_id,
            'thread_depth': self.thread_depth,
            'is_resolved': self.is_resolved,
            'comment_type': self.comment_type,
            'position_data': self.position_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class TokenUsageLog(db.Model):
    """Log of all token operations for analytics and billing"""
    __tablename__ = 'token_usage_log'
    
    id = db.Column(db.Integer, primary_key=True)
    operation_type = db.Column(db.String(50), nullable=False, index=True)
    
    # Token details
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    total_cost = db.Column(db.Integer, nullable=False)
    multiplier = db.Column(db.Float, default=1.0)
    
    # Context - FIXED: Reference correct table names
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    project_id = db.Column(db.String(36), db.ForeignKey('project.id'), index=True)
    scene_id = db.Column(db.Integer, db.ForeignKey('scene.id'), index=True)
    
    # Metadata
    operation_metadata = db.Column(db.JSON)
    ai_model_used = db.Column(db.String(50))
    response_time_ms = db.Column(db.Integer)
    
    # Billing
    billable = db.Column(db.Boolean, default=True)
    billed_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = db.relationship('User', backref='token_usage_logs')
    
    def to_dict(self):
        return {
            'id': self.id,
            'operation_type': self.operation_type,
            'input_tokens': self.input_tokens,
            'output_tokens': self.output_tokens,
            'total_cost': self.total_cost,
            'project_id': self.project_id,
            'scene_id': self.scene_id,
            'ai_model_used': self.ai_model_used,
            'response_time_ms': self.response_time_ms,
            'operation_metadata': self.operation_metadata,
            'billable': self.billable,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

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