import os
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'sarva_secret_key')
CORS(app, origins=os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(','))

# Add Security Headers Middleware
@app.after_request
def add_security_headers(response):
    # Content Security Policy (CSP) - Strong XSS Protection
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Needed for React dev mode
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' http://localhost:5000 ws://localhost:5000 wss://localhost:5000; "
        "object-src 'none'; "
        "frame-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['Content-Security-Policy'] = csp_policy
    
    # Additional Security Headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
    
    return response

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Register socketio with firewall tracker
from services.firewall_tracker import firewall_tracker
firewall_tracker.set_socketio(socketio)

# Active Firewall Blocking Middleware
@app.before_request
def check_firewall():
    client_ip = request.remote_addr or '127.0.0.1'
    
    # Skip attack detection for our logging endpoints
    skip_paths = [
        '/api/advanced/xss/log',
        '/api/advanced/firewall/log-attack'
    ]
    if request.path in skip_paths:
        return
    
    # 1. Check if already blacklisted
    if firewall_tracker.is_blocked(client_ip):
        return jsonify({
            'error': 'Access Denied',
            'message': 'Your IP has been blacklisted by SARVA Firewall due to suspicious activity.',
            'timestamp': datetime.utcnow().isoformat()
        }), 403

    # 2. Real-time Attack Detection on the current request
    path = request.path
    args = str(request.args.to_dict())
    body = str(request.get_data())
    full_request = f"{path} {args} {body}"
    headers = str(request.headers)
    
    is_attack = False
    attack_type = ""
    confidence = 0.95

    # XSS Detection - more comprehensive
    xss_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<[^>]+on\w+\s*=',
        r'&#x?\d+;',
        r'%3Cscript',
        r'%3C/img'
    ]
    import re
    for pattern in xss_patterns:
        if re.search(pattern, full_request, re.IGNORECASE):
            is_attack = True
            attack_type = "XSS Injection"
            confidence = 0.98
            break
    
    # SQL Injection Detection - more comprehensive
    sqli_patterns = [
        r'union\s+select',
        r'order\s+by\s+\d+',
        r'or\s+1\s*=\s*1',
        r'and\s+1\s*=\s*1',
        r'--\s*$',
        r';\s*drop',
        r';\s*delete',
        r';\s*insert',
        r';\s*update',
        r'select\s+.*\s+from',
        r'exec\s*\(',
        r'execute\s*\(',
        r'xp_cmdshell'
    ]
    if not is_attack:
        for pattern in sqli_patterns:
            if re.search(pattern, full_request, re.IGNORECASE):
                is_attack = True
                attack_type = "SQL Injection"
                confidence = 0.97
                break
    
    # Path Traversal Detection
    path_traversal_patterns = [
        r'\.\./',
        r'\.\.\\',
        r'%2e%2e%2f',
        r'%2e%2e%5c',
        r'/etc/passwd',
        r'/windows/system32',
        r'/boot.ini',
        r'/proc/self/environ'
    ]
    if not is_attack:
        for pattern in path_traversal_patterns:
            if re.search(pattern, full_request, re.IGNORECASE):
                is_attack = True
                attack_type = "Path Traversal"
                confidence = 0.96
                break
    
    # SSRF Detection
    ssrf_patterns = [
        r'http://127\.0\.0\.1',
        r'http://localhost',
        r'http://0\.0\.0\.0',
        r'http://\[::1\]',
        r'http://169\.254\.',
        r'file://',
        r'gopher://',
        r'tftp://'
    ]
    if not is_attack:
        for pattern in ssrf_patterns:
            if re.search(pattern, full_request, re.IGNORECASE):
                is_attack = True
                attack_type = "SSRF Attack"
                confidence = 0.95
                break
    
    # XXE Detection
    xxe_patterns = [
        r'<!ENTITY',
        r'<!DOCTYPE',
        r'xmlns:',
        r'xlink:',
        r'&[a-z0-9]+;'
    ]
    if not is_attack:
        for pattern in xxe_patterns:
            if re.search(pattern, full_request, re.IGNORECASE):
                is_attack = True
                attack_type = "XXE Injection"
                confidence = 0.94
                break
    
    # Command Injection Detection
    cmd_injection_patterns = [
        r';\s*(rm|cp|mv|cat|nc|bash|sh|cmd|powershell)',
        r'\|\s*(rm|cp|mv|cat|nc|bash|sh|cmd|powershell)',
        r'`.*?`',
        r'\$\(.*?\)',
        r'\$\{.*?\}',
        r'&\s*(rm|cp|mv|cat|nc|bash|sh|cmd|powershell)',
        r'exec\s*\(',
        r'popen\s*\(',
        r'system\s*\('
    ]
    if not is_attack:
        for pattern in cmd_injection_patterns:
            if re.search(pattern, full_request, re.IGNORECASE):
                is_attack = True
                attack_type = "Command Injection"
                confidence = 0.99
                break

    if is_attack:
        # Log the attack and broadcast it
        firewall_tracker.log_packet(
            packet_type=attack_type,
            source_ip=client_ip,
            payload=full_request[:150],
            action="BLOCKED",
            confidence=confidence
        )
        # Log to traffic analyzer (application layer)
        traffic_analyzer.log_attack(
            attack_data={
                "attack_type": attack_type,
                "source_ip": client_ip,
                "target_ip": request.host,
                "payload": full_request[:150],
                "confidence": confidence,
                "blocked": True,
                "action_taken": "Blocked by WAF"
            },
            layer="application"
        )
        # Add automated response actions
        execute_automated_response(client_ip, attack_type)
        
        return jsonify({
            'error': 'Attack Blocked',
            'message': f'SARVA Firewall detected a {attack_type} and blocked your request.',
            'timestamp': datetime.utcnow().isoformat()
        }), 406 # Not Acceptable / Security Block

def execute_automated_response(ip, attack_type):
    """Execute automated response actions for detected attacks"""
    logger.info(f"Executing automated response for IP {ip} with attack type {attack_type}")
    
    # Automated responses based on attack type
    responses = {
        'Critical': [
            'Block IP immediately',
            'Notify security team',
            'Save attack evidence'
        ],
        'High': [
            'Block IP for 1 hour',
            'Log detailed attack information',
            'Monitor further traffic'
        ],
        'Medium': [
            'Rate limit requests',
            'Log attack details',
            'Monitor IP'
        ],
        'Low': [
            'Log attack details',
            'Monitor IP'
        ]
    }
    
    severity = 'High' if attack_type in ['Command Injection', 'SQL Injection', 'XSS Injection'] else 'Medium'
    logger.info(f"Selected severity: {severity}")
    logger.info(f"Response actions: {', '.join(responses[severity])}")

# Start Background Traffic Simulator (DISABLED)
# import threading
# traffic_thread = threading.Thread(target=firewall_tracker.generate_background_traffic, daemon=True)
# traffic_thread.start()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import routes
from routes.threat_detection import threat_bp
from routes.osint_integration import osint_bp
from routes.blockchain_logs import blockchain_bp
from routes.attack_simulator import simulator_bp
from routes.llm_assistant import llm_bp
from routes.advanced_analysis import advanced_bp, register_socketio_handlers
from routes.lab_integration import lab_bp

# Register blueprints
app.register_blueprint(threat_bp, url_prefix='/api/threats')
app.register_blueprint(osint_bp, url_prefix='/api/osint')
app.register_blueprint(blockchain_bp, url_prefix='/api/blockchain')
app.register_blueprint(simulator_bp, url_prefix='/api/simulator')
app.register_blueprint(llm_bp, url_prefix='/api/llm')
app.register_blueprint(advanced_bp, url_prefix='/api/advanced')
app.register_blueprint(lab_bp, url_prefix='/api/lab')

# Integrate traffic analyzer
from services.traffic_analyzer import traffic_analyzer

# Register WebSocket handlers
register_socketio_handlers(socketio)

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'SARVA Firewall Backend'
    }), 200

# Dashboard stats endpoint
@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        from services.threat_analyzer import ThreatAnalyzer
        analyzer = ThreatAnalyzer()
        stats = analyzer.get_dashboard_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Real-time threat feed endpoint
@socketio.on('connect')
def handle_connect():
    logger.info(f'Client connected: {request.sid}')
    emit('connection_response', {'data': 'Connected to SARVA Firewall'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f'Client disconnected: {request.sid}')

@socketio.on('request_live_threats')
def send_live_threats():
    try:
        from services.threat_analyzer import ThreatAnalyzer
        analyzer = ThreatAnalyzer()
        threats = analyzer.get_recent_threats(limit=10)
        emit('live_threats_update', {'threats': threats})
    except Exception as e:
        logger.error(f"Error sending live threats: {str(e)}")
        emit('error', {'message': str(e)})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
