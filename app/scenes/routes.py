# app/scenes/routes.py - UPDATED scene creation with Claude
from flask import request, jsonify, session, current_app
from app.scenes import scenes_bp
from app.models import Scene, Project, StoryObject, SceneObject
from app.utils.auth import login_required, check_tokens, use_tokens
from app.services.ai_analyzer import AIAnalyzer
from app import db

@scenes_bp.route('', methods=['POST'])
@token_required
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
    
    # AI Analysis with Claude API
    if scene.description:
        try:
            analyzer = AIAnalyzer()
            
            # Get project context for better analysis
            project_context = f"Projekt: {project.title}\nŽánr: {project.genre or 'neurčeno'}\nPopis: {project.description or ''}"
            
            extracted_objects = analyzer.analyze_scene_objects(scene.description, project_context)
            
            # Create/find objects and link to scene
            for obj_type, obj_names in extracted_objects.items():
                for obj_name in obj_names:
                    if not obj_name.strip():
                        continue
                        
                    # Find existing object or create new
                    story_obj = StoryObject.query.filter_by(
                        project_id=project_id,
                        name=obj_name
                    ).first()
                    
                    if not story_obj:
                        story_obj = StoryObject(
                            name=obj_name,
                            object_type=obj_type.rstrip('s'),  # Remove plural
                            project_id=project_id,
                            status='active',
                            description=f"Rozpoznáno AI z scény: {scene.title}"
                        )
                        db.session.add(story_obj)
                        db.session.flush()
                    else:
                        # Update status to active if it was unused
                        if story_obj.status == 'unused':
                            story_obj.status = 'active'
                    
                    # Check if relationship already exists
                    existing_relation = SceneObject.query.filter_by(
                        scene_id=scene.id,
                        object_id=story_obj.id
                    ).first()
                    
                    if not existing_relation:
                        # Link object to scene
                        scene_obj = SceneObject(
                            scene_id=scene.id,
                            object_id=story_obj.id,
                            role='main' if obj_type == 'characters' else 'supporting'
                        )
                        db.session.add(scene_obj)
        
        except Exception as e:
            # Log error but don't fail scene creation
            current_app.logger.error(f"AI analysis failed for scene {scene.id}: {str(e)}")
    
    db.session.commit()
    use_tokens(5)
    
    return jsonify({'success': True, 'scene': scene.to_dict()})