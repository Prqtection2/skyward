from flask import Flask, render_template, request, jsonify, Response, send_file
from utils.skyward import SkywardGPA
import os
import json
import glob

app = Flask(__name__)
app.config['ENV'] = os.environ.get('FLASK_ENV', 'production')

# Global variable to store progress updates
progress_updates = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        # Get session ID from request headers or create one
        session_id = request.headers.get('X-Session-ID', f"{username}_{id(username)}")
        progress_updates[session_id] = []
        
        # Create calculator with progress callback
        def progress_callback(message, progress):
            if session_id in progress_updates:
                progress_updates[session_id].append({
                    'message': message,
                    'progress': progress
                })
        
        calculator = SkywardGPA(username, password, progress_callback)
        result = calculator.calculate()
        
        # Clean up progress updates
        if session_id in progress_updates:
            del progress_updates[session_id]
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/progress/<session_id>')
def get_progress(session_id):
    """Get progress updates for a session"""
    if session_id in progress_updates:
        updates = progress_updates[session_id]
        return jsonify(updates)
    return jsonify([])

@app.route('/debug/screenshots')
def list_screenshots():
    """List available debug screenshots"""
    try:
        screenshot_files = glob.glob('/tmp/debug_*.png')
        screenshots = []
        for file_path in screenshot_files:
            filename = os.path.basename(file_path)
            screenshots.append({
                'filename': filename,
                'url': f'/debug/screenshot/{filename}'
            })
        return jsonify(screenshots)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/debug/screenshot/<filename>')
def get_screenshot(filename):
    """Serve a debug screenshot"""
    try:
        file_path = f'/tmp/{filename}'
        if os.path.exists(file_path):
            return send_file(file_path, mimetype='image/png')
        else:
            return jsonify({'error': 'Screenshot not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)