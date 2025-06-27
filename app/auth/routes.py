# app/auth/routes.py - Authentication Routes
from flask import request, jsonify, session
from app.auth import auth_bp
from app.models import User
from app import db

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    
    if user and user.check_password(data.get('password')):
        session['user_id'] = user.id
        user.last_login = db.func.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    user = User(
        username=data.get('username'),
        email=data.get('email'),
        plan='free',
        tokens_limit=1000
    )
    user.set_password(data.get('password'))
    
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    return jsonify({'success': True, 'user': user.to_dict()})

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'success': True})

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()})