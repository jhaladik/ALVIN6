# app/__init__.py - FIXED App Factory with proper static file handling
from datetime import timedelta
from flask import Flask, render_template, send_from_directory, jsonify, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
import os

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO()

def create_app(config_name='development'):
    """Application factory pattern"""
    
    # Get the directory where this file is located (app directory)
    app_dir = os.path.dirname(os.path.abspath(__file__))
    # Get the project root directory (parent of app directory)
    project_root = os.path.dirname(app_dir)
    # Set static folder path
    static_folder = os.path.join(project_root, 'static')
    
    app = Flask(__name__, 
                static_folder=static_folder,
                static_url_path='/static')
    
    print(f"📁 App directory: {app_dir}")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Static folder: {static_folder}")
    print(f"📁 Static folder exists: {os.path.exists(static_folder)}")
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])

    # Add these session configurations
    app.config.update(
        SESSION_COOKIE_SECURE=False,  # Set to True in production with HTTPS
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_DOMAIN=None,  # Allow localhost
        PERMANENT_SESSION_LIFETIME=timedelta(hours=24)
    )
    # Initialize extensions
    db.init_app(app)

    # Replace your current CORS configuration
    CORS(app, supports_credentials=True, 
         origins=['http://localhost:5173', 'http://localhost:3000'])
    socketio.init_app(app, cors_allowed_origins="*")

         
    # Register API blueprints
    from app.auth import auth_bp
    from app.projects import projects_bp
    from app.scenes import scenes_bp
    from app.ai import ai_bp
    from app.collaboration import collaboration_bp
    from app.routes.debug import debug_bp
    
    app.register_blueprint(debug_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(scenes_bp, url_prefix='/api/scenes')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(collaboration_bp, url_prefix='/api/collaboration')
    
    # Main/Frontend routes (přímo v app)
    @app.route('/')
    def index():
        """Serve the main frontend application"""
        try:
            # Try to serve the HTML file directly from frontend folder
            frontend_path = os.path.join(project_root, 'frontend')
            if os.path.exists(os.path.join(frontend_path, 'index.html')):
                return send_from_directory(frontend_path, 'index.html')
        except Exception as e:
            print(f"Error serving frontend: {e}")
        
        # If file doesn't exist, show a simple API info page
        return '''
        <!DOCTYPE html>
        <html lang="cs">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>StoryForge AI - API Server</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen flex items-center justify-center">
            <div class="text-center max-w-2xl">
                <h1 class="text-4xl font-bold text-gray-800 mb-4">🎭 StoryForge AI</h1>
                <p class="text-gray-600 mb-8">Scene-Object-Story Platform API</p>
                
                <div class="bg-white rounded-xl shadow-lg p-8 mb-6">
                    <h2 class="text-2xl font-semibold mb-6 text-green-600">✅ API je funkční!</h2>
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 text-left">
                        <div>
                            <h3 class="font-medium text-gray-800 mb-2">🔗 API Endpointy:</h3>
                            <div class="space-y-1 text-sm text-gray-600">
                                <div><code class="bg-gray-100 px-1 rounded">/api/auth/login</code></div>
                                <div><code class="bg-gray-100 px-1 rounded">/api/projects</code></div>
                                <div><code class="bg-gray-100 px-1 rounded">/api/scenes</code></div>
                                <div><code class="bg-gray-100 px-1 rounded">/api/ai/*</code></div>
                            </div>
                        </div>
                        <div>
                            <h3 class="font-medium text-gray-800 mb-2">🧪 Demo přihlášení:</h3>
                            <div class="space-y-1 text-sm text-gray-600">
                                <div><strong>Email:</strong> demo@storyforge.ai</div>
                                <div><strong>Heslo:</strong> demo123</div>
                                <div><strong>Plán:</strong> Pro (10k tokenů)</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="mt-6 space-x-4">
                        <a href="/api" class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 inline-block">
                            📋 API Info
                        </a>
                        <a href="/health" class="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 inline-block">
                            💚 Health Check
                        </a>
                    </div>
                </div>
                
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <h3 class="font-medium text-yellow-800 mb-2">📁 Frontend Setup</h3>
                    <p class="text-sm text-yellow-700">
                        Frontend: {frontend_path}<br/>
                        Static files: {static_folder}
                    </p>
                </div>
            </div>
        </body>
        </html>
        '''.format(frontend_path=frontend_path, static_folder=static_folder)

    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon"""
        try:
            return send_from_directory(static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')
        except:
            return '', 204

    # Alternative static file route (backup)
    @app.route('/static/<path:filename>')
    def static_files_backup(filename):
        """Backup static file route"""
        try:
            print(f"🔍 Requesting static file: {filename}")
            print(f"🔍 Looking in: {static_folder}")
            print(f"🔍 Full path: {os.path.join(static_folder, filename)}")
            print(f"🔍 File exists: {os.path.exists(os.path.join(static_folder, filename))}")
            
            return send_from_directory(static_folder, filename)
        except Exception as e:
            print(f"❌ Static file error: {e}")
            return f"Static file not found: {filename}", 404

    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'StoryForge AI API',
            'version': '1.0.0',
            'database': 'connected',
            'static_folder': static_folder,
            'static_folder_exists': os.path.exists(static_folder)
        })

    @app.route('/api')
    def api_info():
        """API information endpoint"""
        return jsonify({
            'service': 'StoryForge AI API',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'auth': {
                    'login': 'POST /api/auth/login',
                    'register': 'POST /api/auth/register',
                    'logout': 'POST /api/auth/logout',
                    'me': 'GET /api/auth/me'
                },
                'projects': {
                    'list': 'GET /api/projects',
                    'create': 'POST /api/projects',
                    'detail': 'GET /api/projects/{id}'
                },
                'scenes': {
                    'create': 'POST /api/scenes',
                    'update': 'PUT /api/scenes/{id}',
                    'delete': 'DELETE /api/scenes/{id}'
                },
                'ai': {
                    'analyze': 'POST /api/ai/projects/{id}/analyze-structure',
                    'suggest': 'POST /api/ai/projects/{id}/suggest-scenes'
                }
            },
            'demo_credentials': {
                'email': 'demo@storyforge.ai',
                'password': 'demo123',
                'plan': 'pro',
                'tokens': '10000'
            },
            'static_info': {
                'static_folder': static_folder,
                'static_folder_exists': os.path.exists(static_folder)
            }
        })

    @app.route('/frontend')
    def frontend_explicit():
        """Serve frontend explicitly"""
        frontend_path = os.path.join(project_root, 'frontend')
        try:
            return send_from_directory(frontend_path, 'index.html')
        except:
            return '''
            <h1>Frontend not found</h1>
            <p>Create frontend/index.html to display your frontend application.</p>
            <a href="/">Back to API info</a>
            '''
   
    # Debug route to check static files
    @app.route('/debug/static')
    def debug_static():
        """Debug static files"""
        def list_directory(path, level=0):
            items = []
            if os.path.exists(path):
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    indent = "  " * level
                    if os.path.isdir(item_path):
                        items.append(f"{indent}{item}/")
                        items.extend(list_directory(item_path, level + 1))
                    else:
                        size = os.path.getsize(item_path)
                        items.append(f"{indent}{item} ({size} bytes)")
            return items
        
        static_listing = list_directory(static_folder)
        
        return f"""
        <h1>Static Files Debug</h1>
        <p><strong>Static folder:</strong> {static_folder}</p>
        <p><strong>Exists:</strong> {os.path.exists(static_folder)}</p>
        <h2>Directory listing:</h2>
        <pre>{'<br/>'.join(static_listing) if static_listing else 'Directory empty or not found'}</pre>
        """

    @app.route('/debug/claude')
    def debug_claude():
        """Debug Claude API status"""
        try:
            from app.services.claude_api import ClaudeAPIClient
            client = ClaudeAPIClient()
            status = client.test_connection()
            
            return jsonify({
                'claude_api': status,
                'simulation_mode': client.simulation_mode,
                'model': client.model
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'claude_api': {
                    'status': 'error', 
                    'message': f'Failed to initialize Claude client: {str(e)}'
                }
            }), 500

    # Register CLI commands
    from app.cli import register_commands
    register_commands(app)
    
    # Add this before the "return app" line
    @app.after_request
    def after_request_func(response):
        print(f"🔍 Request: {request.method} {request.path}")
        print(f"🍪 Session: {dict(session)}")
        print(f"🔄 Response status: {response.status_code}")
        print(f"📝 Response headers: {dict(response.headers)}")
        return response
    
    return app