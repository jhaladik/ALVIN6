# app/auth/routes.py - COMPLETE Authentication Routes with JWT + Session Support
from flask import request, jsonify, session
from app.auth import auth_bp
from app.models import User
from app import db

# JWT imports with fallback
try:
    from app.utils.jwt_auth import generate_token, verify_token, token_required
    JWT_AVAILABLE = True
    print("✅ JWT authentication available")
except ImportError:
    JWT_AVAILABLE = False
    print("⚠️ JWT not available, using session authentication only")

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint - supports both JWT and session authentication"""
    print("🔍 Login attempt received")
    
    # Validate request data
    data = request.get_json()
    if not data:
        print("❌ No JSON data received")
        return jsonify({'error': 'Invalid request data'}), 400
    
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not email or not password:
        print("❌ Missing email or password")
        return jsonify({'error': 'Email and password are required'}), 400
    
    print(f"📧 Login email: {email}")
    
    # Find user
    user = User.query.filter_by(email=email).first()
    
    if not user:
        print(f"❌ User not found with email: {email}")
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.check_password(password):
        print(f"❌ Invalid password for user: {email}")
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        print(f"❌ User account inactive: {email}")
        return jsonify({'error': 'Account is inactive'}), 401
    
    print(f"✅ Login successful for user ID: {user.id}")
    
    # Update last login
    try:
        user.last_login = db.func.now()
        db.session.commit()
        print("📅 Updated last login timestamp")
    except Exception as e:
        print(f"⚠️ Failed to update last login: {e}")
        db.session.rollback()
    
    # Calculate remaining tokens
    tokens_remaining = max(0, user.tokens_limit - user.tokens_used)
    
    # Prepare user data
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'plan': user.plan,
        'tokensRemaining': tokens_remaining,
        'tokensLimit': user.tokens_limit,
        'tokensUsed': user.tokens_used,
        'createdAt': user.created_at.isoformat() if user.created_at else None,
        'lastLogin': user.last_login.isoformat() if user.last_login else None
    }
    
    # Authentication method selection
    response_data = {
        'success': True,
        'user': user_data
    }
    
    if JWT_AVAILABLE:
        print("🔑 Generating JWT token")
        try:
            token = generate_token(user.id)
            response_data['token'] = token
            response_data['authMethod'] = 'jwt'
            print(f"✅ JWT token generated: {token[:20]}...")
        except Exception as e:
            print(f"❌ JWT token generation failed: {e}")
            # Fallback to session
            session['user_id'] = user.id
            response_data['authMethod'] = 'session'
            print("🍪 Fallback to session authentication")
    else:
        print("🍪 Using session authentication")
        session['user_id'] = user.id
        response_data['authMethod'] = 'session'
    
    print(f"📊 Returning user data: {user_data}")
    return jsonify(response_data)

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current authenticated user - supports both JWT and session"""
    print("🔍 Checking current user authentication")
    print(f"📋 Request headers: {dict(request.headers)}")
    
    # Try JWT authentication first
    if JWT_AVAILABLE:
        auth_header = request.headers.get('Authorization')
        print(f"🔑 Authorization header: {auth_header}")
        
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split(' ')[1]
                print(f"🎫 Extracted token: {token[:20]}...")
                
                user_id = verify_token(token)
                print(f"👤 Verified user_id: {user_id}")
                
                if user_id:
                    user = User.query.get(user_id)
                    if user and user.is_active:
                        tokens_remaining = max(0, user.tokens_limit - user.tokens_used)
                        user_data = {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'plan': user.plan,
                            'tokensRemaining': tokens_remaining,
                            'tokensLimit': user.tokens_limit,
                            'tokensUsed': user.tokens_used,
                            'createdAt': user.created_at.isoformat() if user.created_at else None,
                            'lastLogin': user.last_login.isoformat() if user.last_login else None
                        }
                        print(f"✅ JWT auth successful for user: {user.email}")
                        return jsonify({'user': user_data, 'authMethod': 'jwt'})
                    else:
                        print("❌ User not found or inactive")
                else:
                    print("❌ JWT token verification failed")
            except Exception as e:
                print(f"❌ JWT processing error: {e}")
        else:
            print("❌ No valid Authorization header found")
    else:
        print("⚠️ JWT not available, trying session")
    
    # Fallback to session authentication
    print(f"🍪 Session data: {dict(session)}")
    
    if 'user_id' not in session:
        print("❌ No user_id in session")
        return jsonify({'error': 'Not authenticated', 'authMethod': 'none'}), 401
    
    user = User.query.get(session['user_id'])
    if not user:
        print(f"❌ User not found for session ID: {session['user_id']}")
        session.pop('user_id', None)  # Clean up invalid session
        return jsonify({'error': 'User not found'}), 404
    
    if not user.is_active:
        print(f"❌ User inactive for session ID: {session['user_id']}")
        session.pop('user_id', None)  # Clean up inactive user session
        return jsonify({'error': 'Account is inactive'}), 401
    
    tokens_remaining = max(0, user.tokens_limit - user.tokens_used)
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'plan': user.plan,
        'tokensRemaining': tokens_remaining,
        'tokensLimit': user.tokens_limit,
        'tokensUsed': user.tokens_used,
        'createdAt': user.created_at.isoformat() if user.created_at else None,
        'lastLogin': user.last_login.isoformat() if user.last_login else None
    }
    
    print(f"✅ Session auth successful for user: {user.email}")
    return jsonify({'user': user_data, 'authMethod': 'session'})

@auth_bp.route('/register', methods=['POST'])
def register():
    """User registration endpoint"""
    print("🔍 Registration attempt received")
    
    # Validate request data
    data = request.get_json()
    if not data:
        print("❌ No JSON data received")
        return jsonify({'error': 'Invalid request data'}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    # Validation
    if not username or not email or not password:
        print("❌ Missing required fields")
        return jsonify({'error': 'Username, email, and password are required'}), 400
    
    if len(username) < 3:
        return jsonify({'error': 'Username must be at least 3 characters long'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters long'}), 400
    
    print(f"📧 Registration email: {email}")
    print(f"👤 Registration username: {username}")
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        print(f"❌ Email already exists: {email}")
        return jsonify({'error': 'Email already registered'}), 400
    
    if User.query.filter_by(username=username).first():
        print(f"❌ Username already exists: {username}")
        return jsonify({'error': 'Username already taken'}), 400
    
    # Create new user
    try:
        user = User(
            username=username,
            email=email,
            plan='free',  # Default plan
            tokens_limit=1000,  # Free plan limit
            tokens_used=0,
            is_active=True
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        print(f"✅ User created successfully: {user.id}")
        
    except Exception as e:
        print(f"❌ User creation failed: {e}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed. Please try again.'}), 500
    
    # Prepare user data
    tokens_remaining = user.tokens_limit - user.tokens_used
    user_data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'plan': user.plan,
        'tokensRemaining': tokens_remaining,
        'tokensLimit': user.tokens_limit,
        'tokensUsed': user.tokens_used,
        'createdAt': user.created_at.isoformat() if user.created_at else None
    }
    
    # Authentication setup
    response_data = {
        'success': True,
        'user': user_data,
        'message': 'Registration successful'
    }
    
    if JWT_AVAILABLE:
        print("🔑 Generating JWT token for new user")
        try:
            token = generate_token(user.id)
            response_data['token'] = token
            response_data['authMethod'] = 'jwt'
            print(f"✅ JWT token generated for new user")
        except Exception as e:
            print(f"❌ JWT token generation failed: {e}")
            # Fallback to session
            session['user_id'] = user.id
            response_data['authMethod'] = 'session'
    else:
        print("🍪 Using session for new user")
        session['user_id'] = user.id
        response_data['authMethod'] = 'session'
    
    print(f"📊 Registration complete for: {user.email}")
    return jsonify(response_data), 201

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    print("🔍 Logout attempt received")
    
    # Clear session regardless of auth method
    user_id = session.get('user_id')
    if user_id:
        print(f"🍪 Clearing session for user ID: {user_id}")
        session.pop('user_id', None)
    
    # For JWT, the frontend handles token removal
    # We could implement a token blacklist here if needed
    
    print("✅ Logout successful")
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh JWT token endpoint"""
    if not JWT_AVAILABLE:
        return jsonify({'error': 'JWT not available'}), 400
    
    print("🔍 Token refresh attempt")
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': 'Invalid authorization header'}), 401
    
    try:
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        
        if not user_id:
            return jsonify({'error': 'Invalid token'}), 401
        
        user = User.query.get(user_id)
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Generate new token
        new_token = generate_token(user.id)
        
        print(f"✅ Token refreshed for user: {user.email}")
        return jsonify({
            'success': True,
            'token': new_token,
            'message': 'Token refreshed successfully'
        })
        
    except Exception as e:
        print(f"❌ Token refresh failed: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500

# Health check for auth system
@auth_bp.route('/status', methods=['GET'])
def auth_status():
    """Authentication system status"""
    return jsonify({
        'status': 'healthy',
        'jwt_available': JWT_AVAILABLE,
        'auth_methods': ['jwt', 'session'] if JWT_AVAILABLE else ['session'],
        'endpoints': {
            'login': 'POST /api/auth/login',
            'register': 'POST /api/auth/register',
            'logout': 'POST /api/auth/logout',
            'me': 'GET /api/auth/me',
            'refresh': 'POST /api/auth/refresh' if JWT_AVAILABLE else None,
            'status': 'GET /api/auth/status'
        }
    })