# app/utils/auth.py - Authentication Utilities
from functools import wraps
from flask import session, jsonify
from app.models import User
from app import db

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

def check_tokens(tokens_needed):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' in session:
                user = User.query.get(session['user_id'])
                if user and user.tokens_used + tokens_needed > user.tokens_limit:
                    return jsonify({'error': 'Insufficient tokens'}), 402
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def use_tokens(tokens_used):
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            user.tokens_used += tokens_used
            db.session.commit()
