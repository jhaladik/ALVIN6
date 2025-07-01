#!/usr/bin/env python3
# init_database.py - Standalone database initialization script

import os
import sys
from datetime import datetime, timedelta

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def init_database():
    """Initialize database with demo data"""
    print("🔄 Initializing StoryForge AI database...")
    
    # Set environment for development
    os.environ['FLASK_CONFIG'] = 'development'
    
    try:
        from app import create_app, db
        from app.models import User, Project, Scene, StoryObject, BillingPlan, UserSubscription
        # All models should now work with fixed foreign key references
        
        # Create app with development config
        app = create_app('development')
        
        with app.app_context():
            print("📝 Dropping existing tables...")
            db.drop_all()
            
            print("🏗️ Creating new tables...")
            db.create_all()
            
            # Create billing plans
            print("💳 Creating billing plans...")
            create_billing_plans(db)
            
            # Create demo user
            print("👤 Creating demo user...")
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
            print("📚 Creating demo project...")
            demo_project = Project(
                title='Tajemství babičky Anny',
                description='Mladá žena objevuje válečné tajemství své babičky skrze zakódované zprávy.',
                genre='mystery',
                target_word_count=30000,
                current_word_count=2450,
                user_id=demo_user.id
            )
            db.session.add(demo_project)
            db.session.flush()
            
            # Create demo scenes
            print("🎬 Creating demo scenes...")
            demo_scenes = [
                {
                    'title': 'Objev na půdě',
                    'description': 'Anna najde na půdě domu své babičky tajemnou skříňku s kódovanými dopisy.',
                    'scene_type': 'opening',
                    'word_count': 850,
                    'order_index': 1
                },
                {
                    'title': 'První stopa',
                    'description': 'Anna se pokouší rozluštit první dopis a zjišťuje souvislost s válečnými událostmi.',
                    'scene_type': 'development',
                    'word_count': 920,
                    'order_index': 2
                },
                {
                    'title': 'Setkání s historičkou',
                    'description': 'Anna kontaktuje místní historičku, která jí pomáhá pochopit kontext dopisů.',
                    'scene_type': 'development',
                    'word_count': 680,
                    'order_index': 3
                }
            ]
            
            for scene_data in demo_scenes:
                scene = Scene(
                    project_id=demo_project.id,
                    **scene_data
                )
                db.session.add(scene)
            
            # Create demo story objects
            print("🎭 Creating demo story objects...")
            demo_objects = [
                {
                    'name': 'Zakódované dopisy',
                    'object_type': 'object',
                    'description': 'Tajemné dopisy psané šifrou z období druhé světové války.',
                    'importance': 'high'
                },
                {
                    'name': 'Anna Nováková',
                    'object_type': 'character',
                    'description': 'Mladá žena, vnučka válečné hrdinky, která objevuje rodinné tajemství.',
                    'importance': 'high'
                },
                {
                    'name': 'Babička Marie',
                    'object_type': 'character', 
                    'description': 'Zesnulá babička, během války aktivní v odboji.',
                    'importance': 'high'
                },
                {
                    'name': 'Půda domu',
                    'object_type': 'location',
                    'description': 'Staré podkroví rodinného domu, kde jsou ukryty válečné artefakty.',
                    'importance': 'medium'
                }
            ]
            
            for obj_data in demo_objects:
                story_obj = StoryObject(
                    project_id=demo_project.id,
                    **obj_data
                )
                db.session.add(story_obj)
            
            # Commit all changes
            print("💾 Saving to database...")
            db.session.commit()
            
            print("\n✅ Database initialized successfully!")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("🎉 StoryForge AI is ready to use!")
            print("")
            print("📧 Demo login: demo@storyforge.ai")
            print("🔑 Demo password: demo123") 
            print("📊 Demo plan: Pro (10,000 tokens)")
            print("")
            print("🚀 Start the server with: python run.py")
            print("🌐 Then visit: http://localhost:5000")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're in the project root directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def create_billing_plans(db):
    """Create default billing plans"""
    from app.models import BillingPlan
    
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
        try:
            plan = BillingPlan(**plan_data)
            db.session.add(plan)
        except Exception as e:
            print(f"⚠️  Warning: Could not create plan {plan_data['name']}: {e}")
    
    print("📋 Created billing plans: Free, Pro, Enterprise")

if __name__ == '__main__':
    init_database()