# app/collaboration/routes.py - ENHANCED Collaboration Routes
from flask import request, jsonify, session
from flask_socketio import emit, join_room, leave_room, rooms
from app.collaboration import collaboration_bp
from app.models import Project, ProjectCollaborator, Comment, User, Scene
from app.utils.auth import login_required, collaboration_permission_required
from app.services.collaboration_manager import CollaborationManager
from app import db, socketio
from datetime import datetime
import secrets
import json

collaboration_manager = CollaborationManager()

@collaboration_bp.route('/projects/<project_id>/invite', methods=['POST'])
@token_required
@collaboration_permission_required('invite_collaborators')
def invite_collaborator(project_id):
    """Invite user to collaborate on project"""
    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'viewer')
    permissions = data.get('permissions', {})
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Find user by email
    invitee = User.query.filter_by(email=email).first()
    if not invitee:
        return jsonify({'error': 'User not found'}), 404
    
    # Check if already collaborator
    existing = ProjectCollaborator.query.filter_by(
        project_id=project_id, 
        user_id=invitee.id
    ).first()
    
    if existing:
        return jsonify({'error': 'User is already a collaborator'}), 400
    
    try:
        # Create invitation
        invitation_token = secrets.token_urlsafe(32)
        collaborator = ProjectCollaborator(
            project_id=project_id,
            user_id=invitee.id,
            role=role,
            permissions=permissions,
            status='pending',
            invitation_token=invitation_token,
            invited_by=session['user_id']
        )
        
        db.session.add(collaborator)
        db.session.commit()
        
        # Send real-time notification
        collaboration_manager.notify_invitation(
            invitee.id, project_id, session['user_id'], role
        )
        
        return jsonify({
            'success': True,
            'collaborator': collaborator.to_dict(),
            'invitation_token': invitation_token
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Invitation failed: {str(e)}'}), 500

@collaboration_bp.route('/projects/<project_id>/collaborators', methods=['GET'])
@token_required
@collaboration_permission_required('view_collaborators')
def get_collaborators(project_id):
    """Get all collaborators for project"""
    collaborators = ProjectCollaborator.query.filter_by(
        project_id=project_id
    ).all()
    
    return jsonify({
        'success': True,
        'collaborators': [c.to_dict() for c in collaborators],
        'total': len(collaborators)
    })

@collaboration_bp.route('/invitations/<invitation_token>/accept', methods=['POST'])
@token_required
def accept_invitation(invitation_token):
    """Accept collaboration invitation"""
    user_id = session['user_id']
    
    collaborator = ProjectCollaborator.query.filter_by(
        invitation_token=invitation_token,
        user_id=user_id,
        status='pending'
    ).first()
    
    if not collaborator:
        return jsonify({'error': 'Invalid or expired invitation'}), 404
    
    try:
        collaborator.status = 'active'
        collaborator.joined_at = datetime.utcnow()
        collaborator.invitation_token = None  # Clear token after use
        
        db.session.commit()
        
        # Notify other collaborators
        collaboration_manager.notify_collaborator_joined(
            collaborator.project_id, user_id
        )
        
        return jsonify({
            'success': True,
            'project': collaborator.project.to_dict(),
            'role': collaborator.role,
            'permissions': collaborator.permissions
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to accept invitation: {str(e)}'}), 500

@collaboration_bp.route('/projects/<project_id>/comments', methods=['GET'])
@token_required
@collaboration_permission_required('view_comments')
def get_comments(project_id):
    """Get comments for project or scene"""
    scene_id = request.args.get('scene_id', type=int)
    
    query = Comment.query.filter_by(project_id=project_id)
    if scene_id:
        query = query.filter_by(scene_id=scene_id)
    
    comments = query.order_by(Comment.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'comments': [c.to_dict() for c in comments],
        'total': len(comments)
    })

@collaboration_bp.route('/projects/<project_id>/comments', methods=['POST'])
@token_required
@collaboration_permission_required('add_comments')
def add_comment(project_id):
    """Add comment to project or scene"""
    data = request.get_json()
    content = data.get('content')
    scene_id = data.get('scene_id')
    parent_comment_id = data.get('parent_comment_id')
    comment_type = data.get('comment_type', 'general')
    position_data = data.get('position_data')
    
    if not content:
        return jsonify({'error': 'Comment content is required'}), 400
    
    try:
        # Calculate thread depth
        thread_depth = 0
        if parent_comment_id:
            parent = Comment.query.get(parent_comment_id)
            if parent:
                thread_depth = parent.thread_depth + 1
        
        comment = Comment(
            content=content,
            project_id=project_id,
            scene_id=scene_id,
            user_id=session['user_id'],
            parent_comment_id=parent_comment_id,
            thread_depth=thread_depth,
            comment_type=comment_type,
            position_data=position_data
        )
        
        db.session.add(comment)
        db.session.commit()
        
        # Notify collaborators in real-time
        collaboration_manager.notify_new_comment(
            project_id, comment.to_dict()
        )
        
        return jsonify({
            'success': True,
            'comment': comment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to add comment: {str(e)}'}), 500

@collaboration_bp.route('/comments/<comment_id>/resolve', methods=['POST'])
@token_required
def resolve_comment(comment_id):
    """Resolve a comment"""
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'Comment not found'}), 404
    
    # Check permission
    collaborator = ProjectCollaborator.query.filter_by(
        project_id=comment.project_id,
        user_id=session['user_id'],
        status='active'
    ).first()
    
    if not collaborator and comment.project.user_id != session['user_id']:
        return jsonify({'error': 'Permission denied'}), 403
    
    try:
        comment.is_resolved = True
        comment.resolved_by = session['user_id']
        comment.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        # Notify collaborators
        collaboration_manager.notify_comment_resolved(
            comment.project_id, comment_id, session['user_id']
        )
        
        return jsonify({
            'success': True,
            'comment': comment.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to resolve comment: {str(e)}'}), 500

@collaboration_bp.route('/projects/<project_id>/presence', methods=['GET'])
@token_required
@collaboration_permission_required('view_presence')
def get_presence(project_id):
    """Get current user presence in project"""
    presence = collaboration_manager.get_project_presence(project_id)
    return jsonify({
        'success': True,
        'presence': presence
    })

# WebSocket Events for Real-time Collaboration
@socketio.on('join_project')
def handle_join_project(data):
    """User joins project for real-time updates"""
    if 'user_id' not in session:
        emit('error', {'message': 'Authentication required'})
        return
    
    project_id = data.get('project_id')
    if not project_id:
        emit('error', {'message': 'Project ID required'})
        return
    
    # Verify user has access to project
    user_id = session['user_id']
    has_access = collaboration_manager.verify_project_access(user_id, project_id)
    
    if not has_access:
        emit('error', {'message': 'Access denied'})
        return
    
    # Join project room
    room = f'project_{project_id}'
    join_room(room)
    
    # Update presence
    collaboration_manager.update_user_presence(user_id, project_id, 'online')
    
    # Notify others
    emit('user_joined', {
        'user_id': user_id,
        'project_id': project_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room, include_self=False)
    
    emit('joined_project', {
        'project_id': project_id,
        'presence': collaboration_manager.get_project_presence(project_id)
    })

@socketio.on('leave_project')
def handle_leave_project(data):
    """User leaves project"""
    if 'user_id' not in session:
        return
    
    project_id = data.get('project_id')
    user_id = session['user_id']
    room = f'project_{project_id}'
    
    leave_room(room)
    
    # Update presence
    collaboration_manager.update_user_presence(user_id, project_id, 'offline')
    
    # Notify others
    emit('user_left', {
        'user_id': user_id,
        'project_id': project_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room)

@socketio.on('scene_editing')
def handle_scene_editing(data):
    """User is editing a scene"""
    if 'user_id' not in session:
        return
    
    project_id = data.get('project_id')
    scene_id = data.get('scene_id')
    user_id = session['user_id']
    
    # Verify access
    if not collaboration_manager.verify_scene_edit_access(user_id, project_id, scene_id):
        emit('error', {'message': 'Edit access denied'})
        return
    
    room = f'project_{project_id}'
    
    # Notify others that user is editing
    emit('scene_being_edited', {
        'scene_id': scene_id,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room, include_self=False)

@socketio.on('scene_changes')
def handle_scene_changes(data):
    """Broadcast scene changes to collaborators"""
    if 'user_id' not in session:
        return
    
    project_id = data.get('project_id')
    scene_id = data.get('scene_id')
    changes = data.get('changes', {})
    user_id = session['user_id']
    
    # Verify edit permission
    if not collaboration_manager.verify_scene_edit_access(user_id, project_id, scene_id):
        emit('error', {'message': 'Edit access denied'})
        return
    
    room = f'project_{project_id}'
    
    # Broadcast changes
    emit('scene_updated', {
        'scene_id': scene_id,
        'changes': changes,
        'user_id': user_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room, include_self=False)
    
    # Update last activity
    collaboration_manager.update_user_activity(user_id, project_id)

@socketio.on('typing_indicator')
def handle_typing_indicator(data):
    """Handle typing indicators for real-time feedback"""
    if 'user_id' not in session:
        return
    
    project_id = data.get('project_id')
    scene_id = data.get('scene_id')
    is_typing = data.get('is_typing', False)
    user_id = session['user_id']
    
    room = f'project_{project_id}'
    
    emit('user_typing', {
        'scene_id': scene_id,
        'user_id': user_id,
        'is_typing': is_typing,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room, include_self=False)

@socketio.on('cursor_position')
def handle_cursor_position(data):
    """Handle cursor position sharing for collaborative editing"""
    if 'user_id' not in session:
        return
    
    project_id = data.get('project_id')
    scene_id = data.get('scene_id')
    position = data.get('position', {})
    user_id = session['user_id']
    
    room = f'project_{project_id}'
    
    emit('cursor_moved', {
        'scene_id': scene_id,
        'user_id': user_id,
        'position': position,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room, include_self=False)

@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnection"""
    if 'user_id' in session:
        user_id = session['user_id']
        
        # Update presence for all projects
        collaboration_manager.cleanup_user_presence(user_id)
        
        # Notify all rooms the user was in
        user_rooms = [room for room in rooms() if room.startswith('project_')]
        for room in user_rooms:
            emit('user_disconnected', {
                'user_id': user_id,
                'timestamp': datetime.utcnow().isoformat()
            }, room=room)