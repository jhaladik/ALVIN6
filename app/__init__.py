# app/__init__.py - OPRAVENÝ App Factory (bez main blueprint)
from flask import Flask, render_template, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_socketio import SocketIO
import os

# Initialize extensions
db = SQLAlchemy()
socketio = SocketIO()

def create_app(config_name='development'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Register API blueprints
    from app.auth import auth_bp
    from app.projects import projects_bp
    from app.scenes import scenes_bp
    from app.ai import ai_bp
    from app.collaboration import collaboration_bp
    
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
            frontend_path = os.path.join(app.root_path, '..', 'frontend')
            if os.path.exists(os.path.join(frontend_path, 'index.html')):
                return send_from_directory(frontend_path, 'index.html')
        except:
            pass
        
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
                        Pro zobrazení frontendu vytvořte soubor <code class="bg-yellow-100 px-1 rounded">frontend/index.html</code>
                    </p>
                </div>
            </div>
            
            <script>
                // Test API connection
                async function testAPI() {
                    try {
                        const response = await fetch('/api');
                        const data = await response.json();
                        console.log('API Response:', data);
                        alert('API funguje! Zkontrolujte konzoli pro detaily.');
                    } catch (error) {
                        console.error('API Error:', error);
                        alert('Chyba API: ' + error.message);
                    }
                }
                
                // Add click handler to test button
                document.addEventListener('DOMContentLoaded', function() {
                    const testBtn = document.querySelector('a[href="/api"]');
                    if (testBtn) {
                        testBtn.addEventListener('click', function(e) {
                            e.preventDefault();
                            testAPI();
                        });
                    }
                });
            </script>
        </body>
        </html>
        '''

    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon"""
        try:
            return send_from_directory(
                os.path.join(app.root_path, '..', 'static'),
                'favicon.ico',
                mimetype='image/vnd.microsoft.icon'
            )
        except:
            return '', 204

    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files"""
        static_path = os.path.join(app.root_path, '..', 'static')
        return send_from_directory(static_path, filename)

    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': 'StoryForge AI API',
            'version': '1.0.0',
            'database': 'connected'
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
            }
        })

    @app.route('/frontend')
    def frontend_explicit():
        """Serve frontend explicitly"""
        frontend_path = os.path.join(app.root_path, '..', 'frontend')
        try:
            return send_from_directory(frontend_path, 'index.html')
        except:
            return '''
            <h1>Frontend not found</h1>
            <p>Create frontend/index.html to display your frontend application.</p>
            <a href="/">Back to API info</a>
            '''
    
    # Register CLI commands
    from app.cli import init_db_command
    app.cli.add_command(init_db_command)
    
    return app