# app/main/routes.py - Frontend & Static Routes
import os
from flask import render_template, send_from_directory, jsonify, current_app
from app.main import main_bp

@main_bp.route('/')
def index():
    """Serve the main frontend application"""
    try:
        # Try to serve the HTML file directly
        frontend_path = os.path.join(current_app.root_path, '..', 'frontend')
        return send_from_directory(frontend_path, 'index.html')
    except:
        # If file doesn't exist, show a simple landing page
        return '''
        <!DOCTYPE html>
        <html lang="cs">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>StoryForge AI - Scene-Object-Story Platform</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gradient-to-br from-slate-50 to-blue-50 min-h-screen flex items-center justify-center">
            <div class="text-center">
                <h1 class="text-4xl font-bold text-gray-800 mb-4">🎭 StoryForge AI</h1>
                <p class="text-gray-600 mb-8">Scene-Object-Story Platform</p>
                <div class="bg-white rounded-lg shadow-lg p-6 max-w-md">
                    <h2 class="text-xl font-semibold mb-4">API je funkční!</h2>
                    <div class="space-y-2 text-sm text-left">
                        <div><strong>API Base:</strong> /api</div>
                        <div><strong>Auth:</strong> /api/auth/login</div>
                        <div><strong>Projects:</strong> /api/projects</div>
                        <div><strong>Demo User:</strong> demo@storyforge.ai</div>
                        <div><strong>Demo Pass:</strong> demo123</div>
                    </div>
                    <div class="mt-4">
                        <a href="/api/auth/me" class="text-blue-600 hover:underline">Test API</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        '''

@main_bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    try:
        return send_from_directory(
            os.path.join(current_app.root_path, '..', 'static'),
            'favicon.ico',
            mimetype='image/vnd.microsoft.icon'
        )
    except:
        # Return empty response if favicon doesn't exist
        return '', 204

@main_bp.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    static_path = os.path.join(current_app.root_path, '..', 'static')
    return send_from_directory(static_path, filename)

@main_bp.route('/frontend')
def frontend():
    """Alternative route to serve frontend explicitly"""
    frontend_path = os.path.join(current_app.root_path, '..', 'frontend')
    return send_from_directory(frontend_path, 'index.html')

@main_bp.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'StoryForge AI API',
        'version': '1.0.0'
    })

@main_bp.route('/api')
def api_info():
    """API information endpoint"""
    return jsonify({
        'service': 'StoryForge AI API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/api/auth/*',
            'projects': '/api/projects',
            'scenes': '/api/scenes',
            'ai': '/api/ai/*',
            'collaboration': '/api/collaboration/*'
        },
        'demo_credentials': {
            'email': 'demo@storyforge.ai',
            'password': 'demo123'
        }
    })