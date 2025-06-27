# app/ai/routes.py - EXTENDED AI routes with Idea Analysis
from flask import request, jsonify, session
from app.ai import ai_bp
from app.models import Project, Scene, StoryObject
from app.utils.auth import login_required, check_tokens, use_tokens
from app.services.ai_analyzer import AIAnalyzer
from app.services.ai_critics import AICritics
from app import db

@ai_bp.route('/analyze-idea', methods=['POST'])
@login_required
@check_tokens(8)
def analyze_idea():
    """Analyze free-form idea text and extract structure"""
    data = request.get_json()
    idea_text = data.get('idea_text', '').strip()
    story_intent = data.get('story_intent')  # Optional hint: short-story, screenplay, etc.
    
    if not idea_text:
        return jsonify({'error': 'Idea text is required'}), 400
    
    if len(idea_text) < 10:
        return jsonify({'error': 'Idea text is too short'}), 400
    
    try:
        analyzer = AIAnalyzer()
        analysis = analyzer.analyze_idea(idea_text, story_intent)
        
        use_tokens(8)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
        
    except Exception as e:
        return jsonify({'error': f'Idea analysis failed: {str(e)}'}), 500

@ai_bp.route('/create-project-from-idea', methods=['POST'])
@login_required
@check_tokens(12)
def create_project_from_idea():
    """Create project and first scene from analyzed idea"""
    data = request.get_json()
    
    # Project data
    project_title = data.get('project_title', '').strip()
    project_description = data.get('project_description', '').strip()
    project_genre = data.get('project_genre')
    story_intent = data.get('story_intent')
    
    # First scene data
    first_scene = data.get('first_scene', {})
    extracted_objects = data.get('extracted_objects', {})
    
    if not project_title:
        return jsonify({'error': 'Project title is required'}), 400
    
    try:
        # Create project
        project = Project(
            title=project_title,
            description=project_description,
            genre=project_genre,
            current_phase='expand',  # Move directly to expand phase
            user_id=session['user_id']
        )
        
        # Add story intent to project attributes if provided
        if story_intent:
            project.attributes = {'story_intent': story_intent}
        
        db.session.add(project)
        db.session.flush()
        
        # Create objects from extracted data
        created_objects = []
        for obj_type, obj_names in extracted_objects.items():
            for obj_name in obj_names:
                if not obj_name.strip():
                    continue
                    
                story_obj = StoryObject(
                    name=obj_name,
                    object_type=obj_type.rstrip('s'),  # Remove plural
                    project_id=project.id,
                    status='active',
                    description=f"Rozpoznáno AI z původního nápadu"
                )
                db.session.add(story_obj)
                created_objects.append(story_obj)
        
        db.session.flush()
        
        # Create first scene if provided
        created_scene = None
        if first_scene.get('title') and first_scene.get('description'):
            scene = Scene(
                title=first_scene['title'],
                description=first_scene['description'],
                scene_type=first_scene.get('scene_type', 'inciting'),
                order_index=1,
                location=first_scene.get('location'),
                project_id=project.id
            )
            db.session.add(scene)
            db.session.flush()
            created_scene = scene
            
            # Link relevant objects to scene
            scene_objects = first_scene.get('objects', [])
            for obj_name in scene_objects:
                story_obj = next((obj for obj in created_objects if obj.name == obj_name), None)
                if story_obj:
                    from app.models import SceneObject
                    scene_obj = SceneObject(
                        scene_id=scene.id,
                        object_id=story_obj.id,
                        role='main'
                    )
                    db.session.add(scene_obj)
        
        db.session.commit()
        use_tokens(12)
        
        response_data = {
            'success': True,
            'project': project.to_dict(),
            'objects_created': len(created_objects),
            'scene_created': created_scene.to_dict() if created_scene else None
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Project creation failed: {str(e)}'}), 500

@ai_bp.route('/projects/<project_id>/analyze-structure', methods=['POST'])
@login_required
@check_tokens(15)
def analyze_structure(project_id):
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    if not scenes:
        return jsonify({'error': 'No scenes found'}), 400
    
    try:
        analyzer = AIAnalyzer()
        analysis = analyzer.analyze_story_structure(scenes, project)
        
        # Also get critics feedback
        critics = AICritics()
        structure_critique = critics.structure_critique(project, scenes)
        
        use_tokens(15)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'critique': structure_critique
        })
        
    except Exception as e:
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500

@ai_bp.route('/projects/<project_id>/suggest-scenes', methods=['POST'])
@login_required
@check_tokens(10)
def suggest_scenes(project_id):
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    objects = StoryObject.query.filter_by(project_id=project_id).all()
    
    try:
        analyzer = AIAnalyzer()
        suggestions = analyzer.suggest_next_scenes(project_id, scenes, objects)
        
        use_tokens(10)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return jsonify({'error': f'AI suggestion failed: {str(e)}'}), 500

@ai_bp.route('/projects/<project_id>/generate-story', methods=['POST'])
@login_required
@check_tokens(25)
def generate_story(project_id):
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    objects = StoryObject.query.filter_by(project_id=project_id).all()
    
    if len(scenes) < 2:
        return jsonify({'error': 'Need at least 2 scenes to generate story'}), 400
    
    try:
        analyzer = AIAnalyzer()
        story = analyzer.generate_story_from_scenes(project, scenes, objects)
        
        # Update project phase
        project.current_phase = 'story'
        db.session.commit()
        
        use_tokens(25)
        
        return jsonify({
            'success': True,
            'story': story
        })
        
    except Exception as e:
        return jsonify({'error': f'Story generation failed: {str(e)}'}), 500

@ai_bp.route('/projects/<project_id>/critics', methods=['POST'])
@login_required
@check_tokens(20)
def get_ai_critics(project_id):
    """Get feedback from all AI critics"""
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    objects = StoryObject.query.filter_by(project_id=project_id).all()
    characters = [obj for obj in objects if obj.object_type == 'character']
    
    try:
        critics = AICritics()
        
        critiques = {
            'structure': critics.structure_critique(project, scenes),
            'character': critics.character_critique(project, scenes, characters),
            'object_flow': critics.object_flow_critique(project, scenes, objects)
        }
        
        use_tokens(20)
        
        return jsonify({
            'success': True,
            'critiques': critiques
        })
        
    except Exception as e:
        return jsonify({'error': f'Critics analysis failed: {str(e)}'}), 500