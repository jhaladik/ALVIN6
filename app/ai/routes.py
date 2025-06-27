# app/ai/routes.py - UPDATED AI routes with Enhanced Token Management
from flask import request, jsonify, session
from app.ai import ai_bp
from app.models import Project, Scene, StoryObject
from app.utils.auth import login_required, track_ai_operation, enhanced_token_check
from app.services.ai_analyzer import AIAnalyzer
from app.services.enhanced_ai_critics import EnhancedAICritics
from app.services.token_manager import token_manager
from app import db
import time

@ai_bp.route('/analyze-idea', methods=['POST'])
@login_required
@track_ai_operation('analyze_idea')
def analyze_idea():
    """Analyze free-form idea text and extract structure"""
    data = request.get_json()
    idea_text = data.get('idea_text', '').strip()
    story_intent = data.get('story_intent')
    
    if not idea_text:
        return jsonify({'error': 'Idea text is required'}), 400
    
    if len(idea_text) < 10:
        return jsonify({'error': 'Idea text is too short'}), 400
    
    # Get cost estimate for user
    cost_estimate = token_manager.get_cost_estimate('analyze_idea', idea_text)
    
    try:
        start_time = time.time()
        analyzer = AIAnalyzer()
        analysis = analyzer.analyze_idea(idea_text, story_intent)
        processing_time = int((time.time() - start_time) * 1000)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'ai_metadata': {
                'operation_type': 'analyze_idea',
                'processing_time_ms': processing_time,
                'input_tokens': cost_estimate['estimated_input_tokens'],
                'output_tokens': cost_estimate['estimated_output_tokens'],
                'model': 'claude-3-5-sonnet'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Idea analysis failed: {str(e)}'}), 500

@ai_bp.route('/create-project-from-idea', methods=['POST'])
@login_required
@track_ai_operation('create_project_from_idea')
def create_project_from_idea():
    """Create project and first scene from analyzed idea"""
    data = request.get_json()
    
    project_title = data.get('project_title', '').strip()
    project_description = data.get('project_description', '').strip()
    project_genre = data.get('project_genre')
    story_intent = data.get('story_intent')
    first_scene = data.get('first_scene', {})
    extracted_objects = data.get('extracted_objects', {})
    
    if not project_title:
        return jsonify({'error': 'Project title is required'}), 400
    
    try:
        start_time = time.time()
        
        # Create project
        project = Project(
            title=project_title,
            description=project_description,
            genre=project_genre,
            current_phase='expand',
            user_id=session['user_id'],
            original_idea=data.get('original_idea_text', ''),
            attributes={'story_intent': story_intent} if story_intent else None
        )
        
        db.session.add(project)
        db.session.flush()
        
        # Create objects from extracted data
        created_objects = []
        object_count = 0
        
        for obj_type, obj_names in extracted_objects.items():
            for obj_name in obj_names:
                if not obj_name.strip():
                    continue
                    
                story_obj = StoryObject(
                    name=obj_name,
                    object_type=obj_type.rstrip('s'),
                    project_id=project.id,
                    status='active',
                    description=f"Rozpoznáno AI z původního nápadu",
                    first_appearance=1  # Will appear in first scene
                )
                db.session.add(story_obj)
                created_objects.append(story_obj)
                object_count += 1
        
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
                hook=first_scene.get('hook'),
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
        processing_time = int((time.time() - start_time) * 1000)
        
        response_data = {
            'success': True,
            'project': project.to_dict(),
            'objects_created': object_count,
            'scene_created': created_scene.to_dict() if created_scene else None,
            'ai_metadata': {
                'operation_type': 'create_project_from_idea',
                'processing_time_ms': processing_time,
                'input_tokens': len(project_description.split()) * 1.3,
                'output_tokens': 200,  # Estimated
                'model': 'claude-3-5-sonnet'
            }
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Project creation failed: {str(e)}'}), 500

@ai_bp.route('/projects/<project_id>/analyze-structure', methods=['POST'])
@login_required
@track_ai_operation('analyze_structure')
def analyze_structure(project_id):
    """Analyze story structure with comprehensive AI critics"""
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    if not scenes:
        return jsonify({'error': 'No scenes found'}), 400
    
    objects = StoryObject.query.filter_by(project_id=project_id).all()
    
    try:
        start_time = time.time()
        
        # Get comprehensive analysis from enhanced critics
        critics = EnhancedAICritics()
        
        # Get focus areas from request or use default
        data = request.get_json() or {}
        focus_areas = data.get('focus_areas', ['structure', 'character', 'pacing'])
        
        comprehensive_analysis = critics.get_all_critiques(
            project, scenes, objects, focus_areas
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return jsonify({
            'success': True,
            'analysis': comprehensive_analysis,
            'focus_areas': focus_areas,
            'ai_metadata': {
                'operation_type': 'analyze_structure',
                'processing_time_ms': processing_time,
                'input_tokens': sum(len(scene.description.split()) for scene in scenes) * 1.3,
                'output_tokens': 800,  # Estimated for comprehensive analysis
                'model': 'claude-3-5-sonnet',
                'critics_analyzed': len(focus_areas)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'AI analysis failed: {str(e)}'}), 500

@ai_bp.route('/projects/<project_id>/enhanced-critics', methods=['POST'])
@login_required
@track_ai_operation('enhanced_critics')
def get_enhanced_critics(project_id):
    """Get feedback from enhanced AI critics system"""
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    objects = StoryObject.query.filter_by(project_id=project_id).all()
    
    data = request.get_json() or {}
    requested_critics = data.get('critics', ['dialog', 'pacing', 'genre', 'plot_holes'])
    
    try:
        start_time = time.time()
        critics = EnhancedAICritics()
        
        comprehensive_critiques = critics.get_all_critiques(
            project, scenes, objects, requested_critics
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return jsonify({
            'success': True,
            'critiques': comprehensive_critiques,
            'critics_analyzed': requested_critics,
            'ai_metadata': {
                'operation_type': 'enhanced_critics',
                'processing_time_ms': processing_time,
                'input_tokens': sum(len(s.description.split()) for s in scenes) * 1.3,
                'output_tokens': len(requested_critics) * 200,
                'model': 'claude-3-5-sonnet'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Enhanced critics analysis failed: {str(e)}'}), 500

@ai_bp.route('/projects/<project_id>/critics/<critic_type>', methods=['POST'])
@login_required
def get_specific_critic(project_id, critic_type):
    """Get feedback from specific AI critic"""
    
    # Dynamic token cost based on critic type
    token_costs = {
        'dialog': 8,
        'pacing': 12,
        'genre': 10,
        'plot_holes': 15,
        'character_arc': 12,
        'conflict_escalation': 8
    }
    
    cost = token_costs.get(critic_type, 10)
    
    # Check tokens before processing
    balance_check = token_manager.check_balance(session['user_id'], cost)
    if not balance_check['allowed']:
        return jsonify({
            'error': 'Insufficient tokens',
            'required_tokens': cost,
            'remaining_tokens': balance_check.get('remaining', 0)
        }), 402
    
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    objects = StoryObject.query.filter_by(project_id=project_id).all()
    
    try:
        start_time = time.time()
        critics = EnhancedAICritics()
        
        # Route to specific critic
        if critic_type == 'dialog':
            characters = [obj for obj in objects if obj.object_type == 'character']
            critique = critics.dialog_critique(project, scenes, characters)
        elif critic_type == 'pacing':
            critique = critics.pacing_critique(project, scenes)
        elif critic_type == 'genre':
            critique = critics.genre_expert_critique(project, scenes)
        elif critic_type == 'plot_holes':
            critique = critics.plot_hole_detection(project, scenes, objects)
        else:
            return jsonify({'error': f'Unknown critic type: {critic_type}'}), 400
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Execute token operation
        from app.utils.auth import execute_token_operation
        token_result = execute_token_operation(
            operation_type=f'{critic_type}_critique',
            user_id=session['user_id'],
            input_tokens=sum(len(s.description.split()) for s in scenes),
            output_tokens=300,
            metadata={'critic_type': critic_type},
            project_id=project_id,
            ai_model='claude-3-5-sonnet',
            response_time_ms=processing_time
        )
        
        return jsonify({
            'success': True,
            'critique': critique,
            'critic_type': critic_type,
            'token_usage': {
                'tokens_used': token_result.get('tokens_used', 0),
                'remaining_tokens': token_result.get('remaining_tokens', 0)
            },
            'ai_metadata': {
                'operation_type': f'{critic_type}_critique',
                'processing_time_ms': processing_time,
                'model': 'claude-3-5-sonnet'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'{critic_type} analysis failed: {str(e)}'}), 500

@ai_bp.route('/projects/<project_id>/suggest-scenes', methods=['POST'])
@login_required
@track_ai_operation('suggest_scenes')
def suggest_scenes(project_id):
    """AI scene suggestions with enhanced context"""
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    objects = StoryObject.query.filter_by(project_id=project_id).all()
    
    data = request.get_json() or {}
    suggestion_count = min(data.get('count', 3), 5)  # Max 5 suggestions
    focus_type = data.get('focus_type', 'development')  # development, climax, resolution
    
    try:
        start_time = time.time()
        analyzer = AIAnalyzer()
        suggestions = analyzer.suggest_next_scenes(project_id, scenes, objects)
        
        # Filter suggestions based on focus_type if specified
        if focus_type != 'any':
            suggestions = [s for s in suggestions if s.get('scene_type') == focus_type]
        
        # Limit to requested count
        suggestions = suggestions[:suggestion_count]
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions,
            'focus_type': focus_type,
            'ai_metadata': {
                'operation_type': 'suggest_scenes',
                'processing_time_ms': processing_time,
                'input_tokens': sum(len(s.description.split()) for s in scenes) * 1.3,
                'output_tokens': len(suggestions) * 100,
                'model': 'claude-3-5-sonnet'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'AI suggestion failed: {str(e)}'}), 500

@ai_bp.route('/projects/<project_id>/generate-story', methods=['POST'])
@login_required
@track_ai_operation('generate_story')
def generate_story(project_id):
    """Generate complete story from scenes"""
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    objects = StoryObject.query.filter_by(project_id=project_id).all()
    
    if len(scenes) < 2:
        return jsonify({'error': 'Need at least 2 scenes to generate story'}), 400
    
    try:
        start_time = time.time()
        analyzer = AIAnalyzer()
        story = analyzer.generate_story_from_scenes(project, scenes, objects)
        
        # Update project phase and metadata
        project.current_phase = 'story'
        project.current_word_count = story.get('estimated_length', 0)
        
        # Update project attributes with story data
        attributes = project.attributes or {}
        attributes.update({
            'story_generated_at': start_time,
            'final_theme': story.get('theme'),
            'target_audience': story.get('target_audience'),
            'marketability': story.get('marketability')
        })
        project.attributes = attributes
        
        db.session.commit()
        processing_time = int((time.time() - start_time) * 1000)
        
        return jsonify({
            'success': True,
            'story': story,
            'project_updated': project.to_dict(),
            'ai_metadata': {
                'operation_type': 'generate_story',
                'processing_time_ms': processing_time,
                'input_tokens': sum(len(s.description.split()) for s in scenes) * 1.3,
                'output_tokens': 1000,
                'model': 'claude-3-5-sonnet'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Story generation failed: {str(e)}'}), 500

@ai_bp.route('/token-estimate', methods=['POST'])
@login_required
def get_token_estimate():
    """Get token cost estimate for AI operation"""
    data = request.get_json()
    operation_type = data.get('operation_type')
    input_text = data.get('input_text', '')
    
    if not operation_type:
        return jsonify({'error': 'Operation type is required'}), 400
    
    try:
        estimate = token_manager.get_cost_estimate(operation_type, input_text)
        
        # Get user's current balance
        user_id = session['user_id']
        balance_check = token_manager.check_balance(user_id, estimate['estimated_total_cost'])
        
        return jsonify({
            'success': True,
            'estimate': estimate,
            'can_afford': balance_check['allowed'],
            'user_balance': balance_check.get('remaining', 0) if balance_check['allowed'] else balance_check
        })
        
    except Exception as e:
        return jsonify({'error': f'Estimate calculation failed: {str(e)}'}), 500

@ai_bp.route('/usage-analytics', methods=['GET'])
@login_required
def get_ai_usage_analytics():
    """Get AI usage analytics for current user"""
    user_id = session['user_id']
    days = request.args.get('days', 30, type=int)
    
    try:
        analytics = token_manager.get_usage_analytics(user_id, days)
        
        return jsonify({
            'success': True,
            'analytics': analytics,
            'period_days': days
        })
        
    except Exception as e:
        return jsonify({'error': f'Analytics calculation failed: {str(e)}'}), 500