# app/story/routes.py
from flask import Blueprint, request, jsonify, session, send_file
from app.models import Project, Scene, Story, StoryChapter, StoryObject, User
from app.utils.auth import login_required
from app.utils.token_manager import track_ai_operation
from app.services.ai_service import story_generator
from app import db
import json
from datetime import datetime
import io
import os
from werkzeug.utils import secure_filename

story_bp = Blueprint('story', __name__)

@story_bp.route('/projects/<project_id>/story', methods=['GET'])
@login_required
def get_story(project_id):
    """Get story for a project"""
    user_id = session['user_id']
    
    # Check if project exists and user has access
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    # Check if story exists
    story = Story.query.filter_by(project_id=project_id).first()
    if not story:
        return jsonify({'message': 'No story exists for this project yet'}), 404
    
    # Get chapters if they exist
    chapters = StoryChapter.query.filter_by(story_id=story.id).order_by(StoryChapter.order).all()
    
    # Return story data
    return jsonify({
        'success': True,
        'story': {
            'id': story.id,
            'projectId': story.project_id,
            'title': story.title,
            'premise': story.premise,
            'content': story.content,
            'metadata': json.loads(story.metadata) if story.metadata else {
                'genre': project.genre,
                'theme': '',
                'targetAudience': project.target_audience or '',
                'tone': '',
                'uniqueElements': [],
                'keySymbols': []
            },
            'chapters': [
                {
                    'id': chapter.id,
                    'title': chapter.title,
                    'content': chapter.content,
                    'scenes': json.loads(chapter.scene_ids) if chapter.scene_ids else [],
                    'order': chapter.order
                } for chapter in chapters
            ],
            'wordCount': story.word_count,
            'createdAt': story.created_at.isoformat(),
            'updatedAt': story.updated_at.isoformat() if story.updated_at else None
        }
    })

@story_bp.route('/projects/<project_id>/generate-story', methods=['POST'])
@login_required
@track_ai_operation('generate_story')
def generate_story(project_id):
    """Generate story from scenes"""
    user_id = session['user_id']
    data = request.get_json() or {}
    
    # Get narrative options
    narrative_options = data.get('narrativeOptions', {
        'narrativeVoice': 'third_person_limited',
        'proseStyle': 'balanced',
        'dialogStyle': 'direct',
        'tonePreference': 'dramatic'
    })
    
    # Check if project exists and user has access
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    # Get scenes
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    if len(scenes) < 2:
        return jsonify({'error': 'At least 2 scenes are required to generate a story'}), 400
    
    # Get story objects
    characters = StoryObject.query.filter_by(
        project_id=project_id, 
        object_type='character'
    ).all()
    
    locations = StoryObject.query.filter_by(
        project_id=project_id, 
        object_type='location'
    ).all()
    
    props = StoryObject.query.filter_by(
        project_id=project_id, 
        object_type='prop'
    ).all()
    
    try:
        # Generate story using AI service
        story_data = story_generator.generate_full_story(
            project=project,
            scenes=scenes,
            characters=characters,
            locations=locations,
            props=props,
            narrative_options=narrative_options
        )
        
        # Check if story already exists
        existing_story = Story.query.filter_by(project_id=project_id).first()
        
        if existing_story:
            # Update existing story
            existing_story.title = story_data['title']
            existing_story.premise = story_data['premise']
            existing_story.content = story_data['content']
            existing_story.metadata = json.dumps(story_data['metadata'])
            existing_story.word_count = story_data['wordCount']
            existing_story.updated_at = datetime.utcnow()
            
            # Remove existing chapters
            StoryChapter.query.filter_by(story_id=existing_story.id).delete()
            
            story = existing_story
        else:
            # Create new story
            story = Story(
                project_id=project_id,
                title=story_data['title'],
                premise=story_data['premise'],
                content=story_data['content'],
                metadata=json.dumps(story_data['metadata']),
                word_count=story_data['wordCount'],
                created_at=datetime.utcnow()
            )
            db.session.add(story)
            db.session.flush()  # Get the ID for the new story
        
        # Create chapters
        for i, chapter_data in enumerate(story_data['chapters']):
            chapter = StoryChapter(
                story_id=story.id,
                title=chapter_data['title'],
                content=chapter_data['content'],
                scene_ids=json.dumps(chapter_data['scenes']),
                order=i
            )
            db.session.add(chapter)
        
        # Update project phase to 'story' if it's not already
        if project.current_phase != 'story':
            project.current_phase = 'story'
            project.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Update the response with the database IDs
        story_data['id'] = story.id
        story_data['projectId'] = project_id
        story_data['createdAt'] = story.created_at.isoformat()
        story_data['updatedAt'] = story.updated_at.isoformat() if story.updated_at else None
        
        return jsonify({
            'success': True,
            'story': story_data
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to generate story: {str(e)}'}), 500

@story_bp.route('/projects/<project_id>/story', methods=['PUT'])
@login_required
def update_story(project_id):
    """Update existing story"""
    user_id = session['user_id']
    data = request.get_json()
    
    # Check if project exists and user has access
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    # Check if story exists
    story = Story.query.filter_by(project_id=project_id).first()
    if not story:
        return jsonify({'error': 'Story not found'}), 404
    
    try:
        # Update story fields
        if 'title' in data:
            story.title = data['title']
        
        if 'premise' in data:
            story.premise = data['premise']
        
        if 'content' in data:
            story.content = data['content']
            # Update word count
            story.word_count = len(data['content'].split()) if data['content'] else 0
        
        if 'metadata' in data:
            story.metadata = json.dumps(data['metadata'])
        
        story.updated_at = datetime.utcnow()
        
        # Update chapters if provided
        if 'chapters' in data:
            # Remove existing chapters
            StoryChapter.query.filter_by(story_id=story.id).delete()
            
            # Add new chapters
            for i, chapter_data in enumerate(data['chapters']):
                chapter = StoryChapter(
                    story_id=story.id,
                    title=chapter_data['title'],
                    content=chapter_data['content'],
                    scene_ids=json.dumps(chapter_data.get('scenes', [])),
                    order=i
                )
                db.session.add(chapter)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Story updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update story: {str(e)}'}), 500

@story_bp.route('/projects/<project_id>/regenerate-section', methods=['POST'])
@login_required
@track_ai_operation('regenerate_section')
def regenerate_section(project_id):
    """Regenerate a specific section of the story"""
    user_id = session['user_id']
    data = request.get_json() or {}
    
    chapter_index = data.get('chapterIndex')
    if chapter_index is None:
        return jsonify({'error': 'Chapter index is required'}), 400
    
    narrative_options = data.get('narrativeOptions', {
        'narrativeVoice': 'third_person_limited',
        'proseStyle': 'balanced',
        'dialogStyle': 'direct',
        'tonePreference': 'dramatic'
    })
    
    # Check if project exists and user has access
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    # Check if story exists
    story = Story.query.filter_by(project_id=project_id).first()
    if not story:
        return jsonify({'error': 'Story not found'}), 404
    
    # Get chapters
    chapters = StoryChapter.query.filter_by(story_id=story.id).order_by(StoryChapter.order).all()
    if chapter_index >= len(chapters):
        return jsonify({'error': 'Chapter index out of range'}), 400
    
    # Get the chapter to regenerate
    chapter = chapters[chapter_index]
    
    # Get scene IDs for this chapter
    scene_ids = json.loads(chapter.scene_ids) if chapter.scene_ids else []
    
    # Get scenes
    scenes = []
    for scene_id in scene_ids:
        scene = Scene.query.filter_by(id=scene_id).first()
        if scene:
            scenes.append(scene)
    
    if not scenes:
        return jsonify({'error': 'No scenes found for this chapter'}), 400
    
    try:
        # Regenerate chapter using AI service
        regenerated_chapter = story_generator.regenerate_chapter(
            project=project,
            chapter_title=chapter.title,
            scenes=scenes,
            narrative_options=narrative_options
        )
        
        # Update chapter
        chapter.content = regenerated_chapter['content']
        db.session.commit()
        
        # Get all chapters to return updated story
        updated_chapters = StoryChapter.query.filter_by(story_id=story.id).order_by(StoryChapter.order).all()
        
        # Rebuild full story content
        full_content = ""
        for ch in updated_chapters:
            full_content += f"# {ch.title}\n\n{ch.content}\n\n"
        
        story.content = full_content
        story.word_count = len(full_content.split()) if full_content else 0
        story.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Return updated story
        return jsonify({
            'success': True,
            'story': {
                'id': story.id,
                'projectId': story.project_id,
                'title': story.title,
                'premise': story.premise,
                'content': story.content,
                'metadata': json.loads(story.metadata) if story.metadata else {},
                'chapters': [
                    {
                        'id': ch.id,
                        'title': ch.title,
                        'content': ch.content,
                        'scenes': json.loads(ch.scene_ids) if ch.scene_ids else [],
                        'order': ch.order
                    } for ch in updated_chapters
                ],
                'wordCount': story.word_count,
                'createdAt': story.created_at.isoformat(),
                'updatedAt': story.updated_at.isoformat() if story.updated_at else None
            }
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to regenerate section: {str(e)}'}), 500

@story_bp.route('/projects/<project_id>/export-story', methods=['GET'])
@login_required
def export_story(project_id):
    """Export story in various formats"""
    user_id = session['user_id']
    format_type = request.args.get('format', 'pdf')
    
    if format_type not in ['pdf', 'docx', 'epub', 'txt']:
        return jsonify({'error': 'Invalid format type'}), 400
    
    # Check if project exists and user has access
    project = Project.query.filter_by(id=project_id, user_id=user_id).first()
    if not project:
        return jsonify({'error': 'Project not found or access denied'}), 404
    
    # Check if story exists
    story = Story.query.filter_by(project_id=project_id).first()
    if not story:
        return jsonify({'error': 'Story not found'}), 404
    
    try:
        # Generate the appropriate file
        if format_type == 'txt':
            # Simple text export
            content = f"{story.title}\n\n{story.premise}\n\n{story.content}"
            file_stream = io.BytesIO(content.encode('utf-8'))
            filename = f"{secure_filename(story.title)}.txt"
            mimetype = 'text/plain'
        
        elif format_type == 'pdf':
            # PDF export (using a hypothetical PDF generation service)
            from app.services.export_service import generate_pdf
            file_stream = generate_pdf(story)
            filename = f"{secure_filename(story.title)}.pdf"
            mimetype = 'application/pdf'
        
        elif format_type == 'docx':
            # DOCX export (using a hypothetical DOCX generation service)
            from app.services.export_service import generate_docx
            file_stream = generate_docx(story)
            filename = f"{secure_filename(story.title)}.docx"
            mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        
        elif format_type == 'epub':
            # EPUB export (using a hypothetical EPUB generation service)
            from app.services.export_service import generate_epub
            file_stream = generate_epub(story)
            filename = f"{secure_filename(story.title)}.epub"
            mimetype = 'application/epub+zip'
        
        # Track export operation
        user = User.query.get(user_id)
        user.last_activity = datetime.utcnow()
        db.session.commit()
        
        # Return the file
        return send_file(
            file_stream,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({'error': f'Failed to export story: {str(e)}'}), 500

# Register blueprint in app/__init__.py
# app.register_blueprint(story_bp, url_prefix='/api')
