# app/services/collaboration_manager.py - Collaboration Management
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.models import ProjectCollaborator, Project, User
from app import db
import json

class CollaborationManager:
    """Manages real-time collaboration features"""
    
    def __init__(self):
        # In-memory presence tracking (use Redis in production)
        self.user_presence = {}  # {user_id: {project_id: status}}
        self.active_editors = {}  # {project_id: {scene_id: [user_ids]}}
        self.typing_indicators = {}  # {project_id: {scene_id: {user_id: timestamp}}}
    
    def verify_project_access(self, user_id: int, project_id: str) -> bool:
        """Verify user has access to project"""
        # Check if owner
        project = Project.query.filter_by(id=project_id, user_id=user_id).first()
        if project:
            return True
        
        # Check if collaborator
        collaborator = ProjectCollaborator.query.filter_by(
            project_id=project_id,
            user_id=user_id,
            status='active'
        ).first()
        
        return bool(collaborator)
    
    def verify_scene_edit_access(self, user_id: int, project_id: str, scene_id: int) -> bool:
        """Verify user can edit specific scene"""
        if not self.verify_project_access(user_id, project_id):
            return False
        
        # Check if owner
        project = Project.query.filter_by(id=project_id, user_id=user_id).first()
        if project:
            return True
        
        # Check collaborator permissions
        collaborator = ProjectCollaborator.query.filter_by(
            project_id=project_id,
            user_id=user_id,
            status='active'
        ).first()
        
        if not collaborator:
            return False
        
        # Check edit permissions
        permissions = collaborator.permissions or {}
        return permissions.get('edit_scenes', False) or collaborator.role in ['editor', 'owner']
    
    def update_user_presence(self, user_id: int, project_id: str, status: str):
        """Update user presence status"""
        if user_id not in self.user_presence:
            self.user_presence[user_id] = {}
        
        self.user_presence[user_id][project_id] = {
            'status': status,
            'timestamp': datetime.utcnow(),
            'user_info': self._get_user_info(user_id)
        }
    
    def get_project_presence(self, project_id: str) -> List[Dict]:
        """Get all users present in project"""
        present_users = []
        
        for user_id, projects in self.user_presence.items():
            if project_id in projects:
                presence = projects[project_id]
                # Only include users active in last 5 minutes
                if (datetime.utcnow() - presence['timestamp']).seconds < 300:
                    present_users.append({
                        'user_id': user_id,
                        'status': presence['status'],
                        'last_seen': presence['timestamp'].isoformat(),
                        'user_info': presence['user_info']
                    })
        
        return present_users
    
    def update_user_activity(self, user_id: int, project_id: str):
        """Update user activity timestamp"""
        # Update last access in database
        collaborator = ProjectCollaborator.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()
        
        if collaborator:
            collaborator.last_access = datetime.utcnow()
            db.session.commit()
    
    def cleanup_user_presence(self, user_id: int):
        """Clean up user presence on disconnect"""
        if user_id in self.user_presence:
            for project_id in self.user_presence[user_id]:
                self.update_user_presence(user_id, project_id, 'offline')
    
    def notify_invitation(self, invitee_id: int, project_id: str, inviter_id: int, role: str):
        """Send real-time invitation notification"""
        from app import socketio
        
        # This would typically use a user-specific room
        # For now, we'll emit to a general notification channel
        socketio.emit('collaboration_invitation', {
            'project_id': project_id,
            'inviter': self._get_user_info(inviter_id),
            'role': role,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{invitee_id}')
    
    def notify_collaborator_joined(self, project_id: str, user_id: int):
        """Notify when collaborator joins project"""
        from app import socketio
        
        socketio.emit('collaborator_joined', {
            'user': self._get_user_info(user_id),
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'project_{project_id}')
    
    def notify_new_comment(self, project_id: str, comment_data: Dict):
        """Notify about new comment"""
        from app import socketio
        
        socketio.emit('new_comment', comment_data, room=f'project_{project_id}')
    
    def notify_comment_resolved(self, project_id: str, comment_id: int, resolver_id: int):
        """Notify when comment is resolved"""
        from app import socketio
        
        socketio.emit('comment_resolved', {
            'comment_id': comment_id,
            'resolver': self._get_user_info(resolver_id),
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'project_{project_id}')
    
    def _get_user_info(self, user_id: int) -> Dict:
        """Get basic user info for notifications"""
        user = User.query.get(user_id)
        if user:
            return {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        return {'id': user_id, 'username': 'Unknown', 'email': ''}
    
    def get_collaboration_analytics(self, project_id: str) -> Dict:
        """Get collaboration analytics for project"""
        collaborators = ProjectCollaborator.query.filter_by(
            project_id=project_id
        ).all()
        
        # Calculate activity metrics
        total_collaborators = len(collaborators)
        active_collaborators = len([
            c for c in collaborators 
            if c.last_access and (datetime.utcnow() - c.last_access).days < 7
        ])
        
        # Comment metrics
        from app.models import Comment
        comments = Comment.query.filter_by(project_id=project_id).all()
        total_comments = len(comments)
        resolved_comments = len([c for c in comments if c.is_resolved])
        
        return {
            'total_collaborators': total_collaborators,
            'active_collaborators': active_collaborators,
            'total_comments': total_comments,
            'resolved_comments': resolved_comments,
            'collaboration_score': self._calculate_collaboration_score(
                total_collaborators, active_collaborators, total_comments
            )
        }
    
    def _calculate_collaboration_score(self, total: int, active: int, comments: int) -> float:
        """Calculate collaboration engagement score"""
        if total == 0:
            return 0.0
        
        activity_ratio = active / total
        comment_engagement = min(comments / 10, 1.0)  # Normalize to max 1.0
        
        return round((activity_ratio * 0.7 + comment_engagement * 0.3) * 5, 2)  # Scale to 5