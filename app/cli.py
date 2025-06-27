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