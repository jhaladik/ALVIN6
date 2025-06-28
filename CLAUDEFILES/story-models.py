# Add to app/models.py

class Story(db.Model):
    """Story model - final narrative content generated from scenes"""
    __tablename__ = 'stories'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    premise = db.Column(db.Text)
    content = db.Column(db.Text)
    metadata = db.Column(db.Text)  # JSON string with genre, theme, etc.
    word_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)
    
    # Relationships
    project = db.relationship('Project', backref=db.backref('story', uselist=False))
    chapters = db.relationship('StoryChapter', backref='story', cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'title': self.title,
            'premise': self.premise,
            'content': self.content,
            'metadata': json.loads(self.metadata) if self.metadata else {},
            'word_count': self.word_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class StoryChapter(db.Model):
    """Chapter model - sections of a story"""
    __tablename__ = 'story_chapters'
    
    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    scene_ids = db.Column(db.Text)  # JSON array of scene IDs
    order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)
    
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

# Add to Project model
# Update the Project.to_dict() method to include story phase info
def to_dict(self):
    """Convert project to dictionary"""
    result = {
        'id': self.id,
        'title': self.title,
        'description': self.description,
        'genre': self.genre,
        'currentPhase': self.current_phase,
        'sceneCount': Scene.query.filter_by(project_id=self.id).count(),
        'createdAt': self.created_at.isoformat() if self.created_at else None,
        'updatedAt': self.updated_at.isoformat() if self.updated_at else None,
    }
    
    # Add story info if available
    story = Story.query.filter_by(project_id=self.id).first()
    if story:
        result['storyId'] = story.id
        result['storyTitle'] = story.title
        result['wordCount'] = story.word_count
    
    return result

# Database migration
"""
Add the following to a new migration file:

# Create stories table
op.create_table(
    'stories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('project_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('premise', sa.Text(), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('metadata', sa.Text(), nullable=True),
    sa.Column('word_count', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
    sa.PrimaryKeyConstraint('id')
)
op.create_index(op.f('ix_stories_project_id'), 'stories', ['project_id'], unique=False)

# Create story_chapters table
op.create_table(
    'story_chapters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('story_id', sa.Integer(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('scene_ids', sa.Text(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
    sa.PrimaryKeyConstraint('id')
)
op.create_index(op.f('ix_story_chapters_story_id'), 'story_chapters', ['story_id'], unique=False)
"""
