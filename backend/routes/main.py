from flask import Blueprint, render_template, jsonify

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def serve_app():
    """Serves the main frontend application."""
    return render_template('index.html')

@main_bp.route('/api/status')
def api_status():
    """Provides a simple status check for the API."""
    return jsonify({
        'message': 'Facebook Replica API - Advanced Humanized Edition',
        'version': '2.0',
        'status': 'running'
    })