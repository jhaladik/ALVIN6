# app/cli.py - ENHANCED CLI Commands
import click
from flask.cli import with_appcontext
from app import db
from app.models import User, Project, Scene, StoryObject, BillingPlan, UserSubscription
from app.services.token_manager import token_manager
from datetime import datetime, timedelta
import json

@click.command()
@with_appcontext
def init_db_command():
    """Initialize database with demo data"""
    print("🔄 Initializing database...")
    
    # Drop and create all tables
    db.drop_all()
    db.create_all()
    
    # Create billing plans
    create_billing_plans()
    
    # Create demo user
    demo_user = User(
        username='demo',
        email='demo@storyforge.ai',
        plan='pro',
        tokens_limit=10000,
        tokens_used=150  # Some usage to show in UI
    )
    demo_user.set_password('demo123')
    db.session.add(demo_user)
    db.session.flush()
    
    # Create demo subscription
    pro_plan = BillingPlan.query.filter_by(name='pro').first()
    if pro_plan:
        subscription = UserSubscription(
            user_id=demo_user.id,
            plan_id=pro_plan.id,
            status='active',
            current_period_start=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=30),
            tokens_used_this_period=150
        )
        db.session.add(subscription)
    
    # Create demo project
    demo_project = Project(
        title='Tajemství babičky Anny',
        description='Mladá žena objevuje válečné tajemství své babičky skrze zakódované zprávy.',
        genre='mystery',
        current_phase='expand',
        user_id=demo_user.id,
        original_idea='Při úklidu po babičce najdu v její staré skřínce zakódovaný dopis...',
        tone='mysterious',
        target_audience='adult',
        estimated_scope='novella',
        marketability=4
    )
    db.session.add(demo_project)
    db.session.flush()
    
    # Create demo objects
    objects = [
        StoryObject(name='Sarah', object_type='character', project_id=demo_project.id, 
                   importance='high', character_role='protagonist',
                   description='Mladá žena v třiceti letech, archivářka'),
        StoryObject(name='Zakódovaný dopis', object_type='object', project_id=demo_project.id, 
                   importance='high', symbolic_meaning='Klíč k rodinné historii',
                   description='Starý dopis s šifrou z druhé světové války'),
        StoryObject(name='Stará fotografie', object_type='object', project_id=demo_project.id, 
                   status='unused', description='Černobílá fotografie ženy v uniformě'),
        StoryObject(name='Babičin pokoj', object_type='location', project_id=demo_project.id,
                   description='Podkrovní pokoj plný vzpomínek'),
        StoryObject(name='Pavel Novák', object_type='character', project_id=demo_project.id,
                   character_role='supporting', description='Knihovník specialista na historii'),
    ]
    
    for obj in objects:
        db.session.add(obj)
    
    db.session.flush()
    
    # Create demo scenes
    scenes = [
        Scene(
            title='Objev dopisu',
            description='Sarah při úklidu po babičce objeví v její skříňce zakódovaný dopis a starou fotografii ženy v uniformě. Dopis obsahuje podivné symboly a čísla, která připomínají nějakou šifru.',
            scene_type='inciting',
            order_index=1,
            project_id=demo_project.id,
            location='Babičin podkrovní pokoj',
            emotional_intensity=0.6,
            word_count=450,
            hook='Skříňka vydala zvláštní zvuk, jako by se v ní něco posunulo.',
            conflict='Sarah je zmatená objevem - co babička tajila?'
        ),
        Scene(
            title='Dekódování zprávy',
            description='Sarah se obrací na knihovníka Pavla s prosbou o pomoc s dekódováním. Pavel rozpozná válečnou šifru používanou odbojáři. Společně začnou luštit zprávu, která odhaluje záhadné místo.',
            scene_type='development',
            order_index=2,
            project_id=demo_project.id,
            location='Knihovna',
            emotional_intensity=0.7,
            word_count=520,
            character_focus='Pavel Novák',
            conflict='Šifra je složitější než čekali a čas se krátí'
        ),
        Scene(
            title='Návrat k babiččině minulosti',
            description='Sarah a Pavel navštíví místní archiv, kde hledají informace o babiččině roli během války. Objevují, že Anna nebyla jen obyčejnou ženou, ale hrála důležitou roli v odboji.',
            scene_type='rising_action',
            order_index=3,
            project_id=demo_project.id,
            location='Městský archiv',
            emotional_intensity=0.8,
            word_count=680,
            conflict='Archivní materiály jsou neúplné a někdo se je možná pokusil zničit'
        )
    ]
    
    for scene in scenes:
        db.session.add(scene)
    
    db.session.flush()
    
    # Link objects to scenes
    from app.models import SceneObject
    
    # Scene 1 objects
    scene1_objects = [
        SceneObject(scene_id=scenes[0].id, object_id=objects[0].id, role='main', significance='main'),
        SceneObject(scene_id=scenes[0].id, object_id=objects[1].id, role='main', significance='main'),
        SceneObject(scene_id=scenes[0].id, object_id=objects[2].id, role='supporting', significance='supporting'),
        SceneObject(scene_id=scenes[0].id, object_id=objects[3].id, role='supporting', significance='main'),
    ]
    
    # Scene 2 objects
    scene2_objects = [
        SceneObject(scene_id=scenes[1].id, object_id=objects[0].id, role='main', significance='main'),
        SceneObject(scene_id=scenes[1].id, object_id=objects[4].id, role='main', significance='main'),
        SceneObject(scene_id=scenes[1].id, object_id=objects[1].id, role='supporting', significance='main'),
    ]
    
    # Scene 3 objects
    scene3_objects = [
        SceneObject(scene_id=scenes[2].id, object_id=objects[0].id, role='main', significance='main'),
        SceneObject(scene_id=scenes[2].id, object_id=objects[4].id, role='supporting', significance='supporting'),
    ]
    
    for scene_obj in scene1_objects + scene2_objects + scene3_objects:
        db.session.add(scene_obj)
    
    db.session.commit()
    
    print("✅ Database initialized with demo data!")
    print(f"📧 Demo login: demo@storyforge.ai")
    print(f"🔑 Demo password: demo123")
    print(f"📊 Demo plan: Pro (10,000 tokens)")

def create_billing_plans():
    """Create default billing plans"""
    plans = [
        {
            'name': 'free',
            'display_name': 'Free Plan',
            'monthly_token_limit': 1000,
            'max_projects': 3,
            'max_collaborators': 0,
            'monthly_price_cents': 0,
            'token_overage_price_per_1k_cents': 0,
            'features': ['basic_ai_analysis', 'limited_scenes', 'export_txt'],
            'is_active': True,
            'is_public': True
        },
        {
            'name': 'pro',
            'display_name': 'Pro Plan',
            'monthly_token_limit': 10000,
            'max_projects': -1,  # Unlimited
            'max_collaborators': 5,
            'monthly_price_cents': 1999,  # $19.99
            'token_overage_price_per_1k_cents': 299,  # $2.99 per 1k
            'features': ['full_ai_suite', 'unlimited_scenes', 'basic_collaboration', 
                        'export_pdf', 'export_docx', 'ai_critics', 'structure_analysis'],
            'is_active': True,
            'is_public': True
        },
        {
            'name': 'enterprise',
            'display_name': 'Enterprise Plan',
            'monthly_token_limit': 50000,
            'max_projects': -1,
            'max_collaborators': -1,  # Unlimited
            'monthly_price_cents': 4999,  # $49.99
            'token_overage_price_per_1k_cents': 199,  # $1.99 per 1k
            'features': ['all_features', 'priority_support', 'advanced_collaboration',
                        'custom_export', 'analytics', 'api_access'],
            'is_active': True,
            'is_public': True
        }
    ]
    
    for plan_data in plans:
        plan = BillingPlan(**plan_data)
        db.session.add(plan)
    
    print("📋 Created billing plans: Free, Pro, Enterprise")

@click.command()
@with_appcontext
def create_admin_command():
    """Create admin user"""
    username = click.prompt('Admin username')
    email = click.prompt('Admin email')
    password = click.prompt('Admin password', hide_input=True)
    
    admin_user = User(
        username=username,
        email=email,
        plan='enterprise',
        tokens_limit=100000,
        is_active=True
    )
    admin_user.set_password(password)
    
    db.session.add(admin_user)
    db.session.commit()
    
    print(f"✅ Admin user '{username}' created successfully!")

@click.command()
@with_appcontext
def token_stats_command():
    """Show token usage statistics"""
    from app.models import TokenUsageLog
    
    total_operations = TokenUsageLog.query.count()
    total_tokens = db.session.query(db.func.sum(TokenUsageLog.total_cost)).scalar() or 0
    
    # Top operations
    top_operations = db.session.query(
        TokenUsageLog.operation_type,
        db.func.count(TokenUsageLog.id).label('count'),
        db.func.sum(TokenUsageLog.total_cost).label('total_tokens')
    ).group_by(TokenUsageLog.operation_type).order_by(db.desc('total_tokens')).limit(5).all()
    
    # Top users
    top_users = db.session.query(
        User.username,
        db.func.count(TokenUsageLog.id).label('operations'),
        db.func.sum(TokenUsageLog.total_cost).label('tokens_used')
    ).join(TokenUsageLog).group_by(User.id).order_by(db.desc('tokens_used')).limit(5).all()
    
    print(f"\n📊 Token Usage Statistics")
    print(f"{'=' * 50}")
    print(f"Total Operations: {total_operations:,}")
    print(f"Total Tokens Used: {total_tokens:,}")
    print(f"Average per Operation: {total_tokens/max(total_operations, 1):.1f}")
    
    print(f"\n🔥 Top Operations:")
    for op_type, count, tokens in top_operations:
        print(f"  {op_type}: {count:,} ops, {tokens:,} tokens")
    
    print(f"\n👥 Top Users:")
    for username, ops, tokens in top_users:
        print(f"  {username}: {ops:,} ops, {tokens:,} tokens")

@click.command()
@with_appcontext 
def cleanup_data_command():
    """Clean up old data and optimize database"""
    from app.models import TokenUsageLog
    
    # Delete old token logs (older than 6 months)
    cutoff_date = datetime.utcnow() - timedelta(days=180)
    old_logs = TokenUsageLog.query.filter(TokenUsageLog.created_at < cutoff_date).count()
    
    if old_logs > 0:
        TokenUsageLog.query.filter(TokenUsageLog.created_at < cutoff_date).delete()
        db.session.commit()
        print(f"🗑️ Deleted {old_logs:,} old token usage logs")
    else:
        print("✅ No old data to clean up")

@click.command()
@click.argument('email')
@click.argument('tokens', type=int)
@with_appcontext
def add_tokens_command(email, tokens):
    """Add tokens to user account"""
    user = User.query.filter_by(email=email).first()
    if not user:
        print(f"❌ User with email {email} not found")
        return
    
    result = token_manager.add_tokens(user.id, tokens, "Admin grant")
    
    if result['success']:
        print(f"✅ Added {tokens:,} tokens to {email}")
        print(f"   New balance: {result['remaining']:,} tokens")
    else:
        print(f"❌ Failed to add tokens: {result['error']}")

@click.command()
@with_appcontext
def reset_demo_command():
    """Reset demo user data"""
    demo_user = User.query.filter_by(email='demo@storyforge.ai').first()
    if not demo_user:
        print("❌ Demo user not found")
        return
    
    # Reset token usage
    demo_user.tokens_used = 150
    
    # Reset project word counts
    for project in demo_user.projects:
        project.current_word_count = sum(scene.word_count or 0 for scene in project.scenes)
    
    db.session.commit()
    print("✅ Demo user data reset successfully!")

# Register all commands
def register_commands(app):
    """Register all CLI commands with the app"""
    app.cli.add_command(init_db_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(token_stats_command)
    app.cli.add_command(cleanup_data_command)
    app.cli.add_command(add_tokens_command)
    app.cli.add_command(reset_demo_command)