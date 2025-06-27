# app/routes/debug.py - Debug endpoint for Claude API
from flask import Blueprint, jsonify
from app.services.claude_api import ClaudeAPIClient

debug_bp = Blueprint('debug', __name__)

@debug_bp.route('/debug/claude', methods=['GET'])
def debug_claude():
    """Debug endpoint for Claude API status"""
    try:
        client = ClaudeAPIClient()
        status = client.test_connection()
        
        return jsonify({
            'claude_api': status,
            'simulation_mode': client.simulation_mode,
            'model': client.model,
            'rate_limit': {
                'max_requests_per_minute': client.max_requests_per_minute,
                'current_requests': len(client.request_times)
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'claude_api': {
                'status': 'error',
                'message': f'Failed to initialize Claude client: {str(e)}'
            }
        }), 500