# app/projects/routes.py - Project Routes
from flask import request, jsonify, session
from app.projects import projects_bp
from app.models import Project, Scene, StoryObject
from app.utils.auth import login_required
from app import db

@projects_bp.route('', methods=['GET'])
@login_required
def get_projects():
    projects = Project.query.filter_by(user_id=session['user_id']).all()
    return jsonify([p.to_dict() for p in projects])

@projects_bp.route('', methods=['POST'])
@login_required
def create_project():
    data = request.get_json()
    
    project = Project(
        title=data.get('title'),
        description=data.get('description'),
        genre=data.get('genre'),
        user_id=session['user_id']
    )
    
    db.session.add(project)
    db.session.commit()
    
    return jsonify({'success': True, 'project': project.to_dict()})

@projects_bp.route('/<project_id>', methods=['GET'])
@login_required
def get_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=session['user_id']).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    scenes = Scene.query.filter_by(project_id=project_id).order_by(Scene.order_index).all()
    objects = StoryObject.query.filter_by(project_id=project_id).all()
    
    return jsonify({
        'project': project.to_dict(),
        'scenes': [s.to_dict() for s in scenes],
        'objects': [o.to_dict() for o in objects]
    })
