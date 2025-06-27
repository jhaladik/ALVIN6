# app/ai/routes.py - UPDATED AI routes with Claude
from flask import request, jsonify, session
from app.ai import ai_bp
from app.models import Project, Scene, StoryObject
from app.utils.auth import login_required, check_tokens, use_tokens
from app.services.ai_analyzer import AIAnalyzer
from app.services.ai_critics import AICritics
from app import db

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
