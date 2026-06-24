import os
import json
import logging
import re
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

from utils.security import generate_token, verify_password, hash_password, token_required

# Initialize Flask app
app = Flask(__name__)

# Security Configuration
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', os.urandom(24).hex())
ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

# Initialize Limiter for Rate Limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["2000 per day", "500 per hour"],
    storage_uri="memory://",
    strategy="fixed-window",
    on_breach=lambda limit: jsonify({'error': 'Rate limit exceeded', 'message': str(limit)}),
)
limiter.request_filter(lambda: request.path == "/api/health")

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        "error": "ratelimit exceeded",
        "message": str(e.description),
        "status": 429
    }), 429


# Configure CORS
CORS(app, origins=ALLOWED_ORIGINS)

# Initialize SocketIO with restricted origins
socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS)

# Static credentials for demo (In production, use a secure database)
DEMO_USER = {
    "username": "admin",
    "password_hash": hash_password("firewall2024")
}

# ================= AUTH ROUTES =================

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Secure login endpoint returning JWT"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request body'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if username == DEMO_USER["username"] and verify_password(password, DEMO_USER["password_hash"]):
            token = generate_token(username)
            logger.info(f"Successful login for user: {username}")
            return jsonify({
                'status': 'success',
                'token': token,
                'user': {'username': username}
            }), 200
            
        logger.warning(f"Failed login attempt for username: {username} from {request.remote_addr}")
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# ================= MIDDLEWARE =================

@app.after_request
def add_security_headers(response):
    """Add production-grade security headers"""
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' http://localhost:5000 ws://localhost:5000 wss://localhost:5000; "
        "object-src 'none'; "
        "frame-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    # Relax CSP only in development mode for Vite/React HMR
    if os.getenv('FLASK_ENV', 'development') == 'development':
        csp_policy = csp_policy.replace("script-src 'self';", "script-src 'self' 'unsafe-inline' 'unsafe-eval';")
        
    response.headers['Content-Security-Policy'] = csp_policy
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

@app.before_request
def check_firewall():
    """Active Firewall/WAF Middleware"""
    client_ip = request.remote_addr or '127.0.0.1'
    
    # 1. Check if blacklisted
    from services.firewall_tracker import firewall_tracker
    if firewall_tracker.is_blocked(client_ip):
        return jsonify({'error': 'Access Denied', 'message': 'IP Blacklisted'}), 403

    # 2. Inspect request for attacks
    if request.path.startswith('/api/') and request.path not in ['/api/auth/login']:
        # Concatenate parts for inspection
        body = request.get_data(as_text=True) or ""
        inspect_str = f"{request.path} {request.query_string.decode()} {body}".lower()
        
        attack_patterns = {
            "XSS Injection": [r'<script', r'javascript:', r'onerror=', r'onload='],
            "SQL Injection": [r'union\s+select', r'or\s+1=1', r'--\s', r'drop\s+table'],
            "Command Injection": [r';\s*rm', r'\|\s*bash', r'`id`', r'\$\(whoami\)'],
            "Path Traversal": [r'\.\./', r'\.\.\\', r'/etc/passwd'],
            "SSRF Attack": [r'http://169\.254\.', r'http://localhost', r'file://']
        }
        
        for attack_type, patterns in attack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, inspect_str):
                    logger.warning(f"WAF: Blocked {attack_type} from {client_ip}")
                    firewall_tracker.log_packet(attack_type, client_ip, inspect_str[:100], "BLOCKED", 0.99)
                    # Log to traffic analyzer (persistent CSV)
                    try:
                        from services.traffic_analyzer import traffic_analyzer
                        traffic_analyzer.log_attack({
                            "attack_type": attack_type,
                            "source_ip": client_ip,
                            "target_ip": request.host or "127.0.0.1",
                            "payload": inspect_str[:100],
                            "confidence": 0.99,
                            "blocked": True,
                            "action_taken": "Blocked by WAF",
                            "layer": "application"
                        }, layer="application")
                        traffic_analyzer.log_packet({
                            "source_ip": client_ip,
                            "dest_ip": request.host or "127.0.0.1",
                            "source_port": request.environ.get('REMOTE_PORT', 0),
                            "dest_port": request.environ.get('SERVER_PORT', 80),
                            "protocol": "HTTP",
                            "packet_size": len(inspect_str),
                            "flags": "SYN/RST",
                            "action": "BLOCKED"
                        }, layer="application")
                    except Exception as e:
                        logger.error(f"Error logging WAF block to traffic analyzer: {e}")
                    return jsonify({'error': 'Security Block', 'message': f'Detected {attack_type}'}), 403

# ================= ROUTE REGISTRATION =================

# Import services
from services.firewall_tracker import firewall_tracker
firewall_tracker.set_socketio(socketio)

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
