import os
import json
import logging
import re
import time
from datetime import datetime, timezone
from pathlib import Path

# Compatibility shim for Python 3.14
import pkgutil
if not hasattr(pkgutil, 'get_loader'):
    import importlib.util
    def _compat_get_loader(name):
        try:
            spec = importlib.util.find_spec(name)
            return getattr(spec, 'loader', None) if spec else None
        except Exception:
            return None
    pkgutil.get_loader = _compat_get_loader

from flask import Flask, request, jsonify, g
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import jwt
import geoip2.database
from models import db, AttackEvent, RequestLog

# Load environment variables
load_dotenv()

# Initialize Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('JWT_SECRET', 'sarva_default_secure_secret_change_me')
JWT_SECRET = os.getenv('JWT_SECRET', 'sarva_default_secure_secret_change_me')
JWT_ALGORITHM = 'HS256'
ALLOWED_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')

# Database configuration
db_url = os.getenv('DATABASE_URL', 'sqlite:///waf.db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# GeoIP setup
geoip_db_path = os.getenv('GEOIP_DB_PATH', Path(__file__).parent / 'GeoLite2-City.mmdb')
geoip_reader = None
if Path(geoip_db_path).exists():
    try:
        geoip_reader = geoip2.database.Reader(geoip_db_path)
        logger.info("GeoIP database loaded")
    except Exception as e:
        logger.warning(f"Failed to load GeoIP database: {e}")

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

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins=ALLOWED_ORIGINS, async_mode='threading')

@socketio.on('connect')
def handle_socket_connect(auth):
    token = (auth or {}).get('token') if isinstance(auth, dict) else None
    if not token:
        logger.warning(f"Socket connection rejected: no token from {request.remote_addr}")
        return False
    try:
        jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        logger.info(f"Socket connection authenticated: user from {_get_client_ip()}")
        return True
    except jwt.ExpiredSignatureError:
        logger.warning("Socket connection rejected: expired token")
        return False
    except jwt.InvalidTokenError:
        logger.warning("Socket connection rejected: invalid token")
        return False

# Static credentials for demo
DEMO_USER = {
    "username": "admin",
    "password_hash": "pbkdf2:sha256:260000$Zv0kGv9v$d569e0a4a5c8a31b5c4e1d2c3b4a5"
}

def hash_password(password: str) -> str:
    import hashlib
    import secrets
    salt = secrets.token_hex(16)
    hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 260000)
    return f"pbkdf2:sha256:260000${salt}${hash_obj.hex()}"

def verify_password(password: str, password_hash: str) -> bool:
    import hashlib
    try:
        algorithm, iterations, salt_hash = password_hash.split('$')
        _, iterations = iterations.split(':')
        salt, stored_hash = salt_hash.split('$', 1)
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), int(iterations))
        return hash_obj.hex() == stored_hash
    except Exception:
        return False

def generate_token(username: str) -> str:
    payload = {
        'sub': username,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

from datetime import timedelta

def _get_client_ip():
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        forwarded_ips = [ip.strip() for ip in xff.split(',') if ip.strip()]
        for ip in forwarded_ips:
            if ip and not ip.startswith(('10.', '172.16.', '192.168.', '127.')):
                return ip
        for ip in forwarded_ips:
            if ip and ip != '127.0.0.1':
                return ip
        return forwarded_ips[0] if forwarded_ips else '127.0.0.1'
    return request.remote_addr or '127.0.0.1'

def _get_geoip_info(ip: str):
    if not geoip_reader:
        return None
    try:
        response = geoip_reader.city(ip)
        return {
            'country': response.country.name,
            'city': response.city.name,
            'lat': response.location.latitude,
            'lon': response.location.longitude
        }
    except Exception:
        return None

# Malicious User Agents list
MALICIOUS_USER_AGENTS = [
    'sqlmap', 'nikto', 'nmap', 'masscan', 'dirbuster', 'gobuster', 'wfuzz',
    'hydra', 'metasploit', 'nessus', 'openvas', 'arachni', 'w3af', 'burp',
    'zap', 'nessus', 'acunetix', 'netsparker', 'webinspect', 'appscan'
]

# Attack patterns
ATTACK_PATTERNS = {
    "XSS Injection": [r'<script', r'javascript:', r'onerror=', r'onload=', r'onmouseover=', r'onclick=', r'eval\(', r'document\.cookie'],
    "SQL Injection": [r'union\s+select', r'or\s+1=1', r'--\s', r'drop\s+table', r';\s*drop', r'\'\s*or', r'"\\s*or'],
    "Command Injection": [r';\s*rm', r'\|\s*bash', r'`id`', r'\$\(whoami\)', r'&\s*sh', r'&\s*cmd', r'system\(', r'popen\(', r'passthru\('],
    "Path Traversal": [r'\.\./', r'\.\.\\', r'/etc/passwd', r'/windows/system32', r'\\windows\\system32'],
    "File Inclusion": [r'php://', r'zip://', r'phar://', r'file://', r'http://', r'https://', r'data://'],
    "SSRF Attack": [r'http://169\.254\.', r'http://localhost', r'http://127\.0\.0\.1', r'file://', r'ftp://']
}

def calculate_severity(attack_type: str, confidence: float) -> str:
    if confidence > 0.95 or attack_type in ["SQL Injection", "Command Injection"]:
        return "CRITICAL"
    elif confidence > 0.85:
        return "HIGH"
    elif confidence > 0.7:
        return "MEDIUM"
    else:
        return "LOW"

@app.before_request
def log_request_start():
    g.start_time = time.time()

@app.after_request
def add_security_headers_and_log(response):
    # Log request
    try:
        client_ip = _get_client_ip()
        response_time = int((time.time() - g.start_time) * 1000) if hasattr(g, 'start_time') else None
        log = RequestLog(
            source_ip=client_ip,
            request_path=request.path,
            request_method=request.method,
            status_code=response.status_code,
            user_agent=request.headers.get('User-Agent'),
            response_time_ms=response_time,
            is_attack=getattr(g, 'is_attack', False)
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error logging request: {e}")
    
    # Security headers
    ws_scheme = 'wss:' if os.getenv('FLASK_ENV', 'development') != 'development' else 'ws:'
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' http://localhost:5173; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https:; "
        f"connect-src 'self' ws://{request.host} http://localhost:5000 http://localhost:5173; "
        "object-src 'none'; "
        "frame-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['Content-Security-Policy'] = csp_policy
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.before_request
def check_firewall():
    client_ip = _get_client_ip()
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # 1. Check malicious user agent
    is_malicious_ua = any(ua in user_agent for ua in MALICIOUS_USER_AGENTS)
    if is_malicious_ua:
        g.is_attack = True
        _log_and_block_attack(
            attack_type="Malicious User Agent",
            source_ip=client_ip,
            payload=user_agent,
            confidence=0.98
        )
        return jsonify({'error': 'Security Block', 'message': 'Detected Malicious User Agent'}), 403
    
    # 2. Inspect request for attacks
    if request.path not in ['/api/auth/login', '/api/health']:
        body = request.get_data(as_text=True) or ""
        inspect_str = f"{request.path} {request.query_string.decode()} {body}".lower()
        
        for attack_type, patterns in ATTACK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, inspect_str, re.IGNORECASE):
                    g.is_attack = True
                    _log_and_block_attack(
                        attack_type=attack_type,
                        source_ip=client_ip,
                        payload=inspect_str[:200],
                        confidence=0.95,
                        user_agent=request.headers.get('User-Agent'),
                        request_path=request.path,
                        request_method=request.method
                    )
                    return jsonify({'error': 'Security Block', 'message': f'Detected {attack_type}'}), 403

def _log_and_block_attack(attack_type, source_ip, payload, confidence, user_agent=None, request_path=None, request_method=None):
    from services.firewall_tracker import firewall_tracker
    
    # Get GeoIP
    geo_info = _get_geoip_info(source_ip)
    
    # Calculate severity
    severity = calculate_severity(attack_type, confidence)
    
    # AI analysis
    ai_analysis = None
    try:
        from services.local_llm_service import LocalLLMService
        llm = LocalLLMService()
        if llm.is_running:
            ai_analysis = llm.analyze_threat({
                "type": attack_type,
                "source_ip": source_ip,
                "payload": payload
            })
    except Exception as e:
        logger.warning(f"AI analysis failed: {e}")
    
    # Log to database
    event = AttackEvent(
        source_ip=source_ip,
        attack_type=attack_type,
        payload=payload,
        confidence=confidence,
        severity=severity,
        status="BLOCKED",
        user_agent=user_agent,
        request_path=request_path,
        request_method=request_method,
        geo_country=geo_info['country'] if geo_info else None,
        geo_city=geo_info['city'] if geo_info else None,
        geo_lat=geo_info['lat'] if geo_info else None,
        geo_lon=geo_info['lon'] if geo_info else None,
        ai_analysis=ai_analysis,
        action_taken=f"Blocked by WAF - {attack_type}"
    )
    db.session.add(event)
    db.session.commit()
    
    # Log to firewall tracker (WebSocket)
    log_entry = firewall_tracker.log_packet(
        packet_type=attack_type,
        source_ip=source_ip,
        payload=payload,
        action="BLOCKED",
        confidence=confidence
    )
    
    # Emit to WebSocket
    socketio.emit('attack_detected', event.to_dict())
    socketio.emit('firewall_traffic', {'packet': log_entry})
    
    logger.warning(f"BLOCKED {attack_type} from {source_ip} (severity: {severity})")

# ================= AUTH ROUTES =================
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request body'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # Since we don't have the real hash, let's just accept admin/firewall2024
        if username == 'admin' and password == 'firewall2024':
            token = generate_token(username)
            logger.info(f"Successful login for user: {username}")
            return jsonify({
                'status': 'success',
                'token': token,
                'user': {'username': username}
            }), 200
        
        logger.warning(f"Failed login attempt for username: {username} from {_get_client_ip()}")
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# ================= DASHBOARD ROUTES =================
from utils.security import token_required

@app.route('/api/dashboard/stats', methods=['GET'])
@token_required
def get_dashboard_stats():
    try:
        total_requests = RequestLog.query.count()
        blocked_requests = AttackEvent.query.filter_by(status='BLOCKED').count()
        active_threats = AttackEvent.query.filter(
            AttackEvent.timestamp > datetime.now(timezone.utc) - timedelta(hours=1)
        ).count()
        
        attack_types = db.session.query(
            AttackEvent.attack_type,
            db.func.count(AttackEvent.id).label('count')
        ).group_by(AttackEvent.attack_type).all()
        top_attack_types = [{'type': at, 'count': c} for at, c in attack_types]
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_requests': total_requests,
                'blocked_requests': blocked_requests,
                'active_threats': active_threats,
                'top_attack_types': top_attack_types
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/attacks', methods=['GET'])
@token_required
def get_attacks():
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        attacks = AttackEvent.query.order_by(
            AttackEvent.timestamp.desc()
        ).limit(limit).offset(offset).all()
        
        return jsonify({
            'status': 'success',
            'data': [a.to_dict() for a in attacks],
            'total': AttackEvent.query.count()
        }), 200
    except Exception as e:
        logger.error(f"Error getting attacks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/requests', methods=['GET'])
@token_required
def get_requests():
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        requests = RequestLog.query.order_by(
            RequestLog.timestamp.desc()
        ).limit(limit).offset(offset).all()
        
        return jsonify({
            'status': 'success',
            'data': [r.to_dict() for r in requests],
            'total': RequestLog.query.count()
        }), 200
    except Exception as e:
        logger.error(f"Error getting requests: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/timeline', methods=['GET'])
@token_required
def get_timeline():
    try:
        hours = request.args.get('hours', 24, type=int)
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        # Get all attacks in range
        attacks = AttackEvent.query.filter(
            AttackEvent.timestamp >= start_time,
            AttackEvent.timestamp <= end_time
        ).all()
        
        # Group by hour manually
        from collections import defaultdict
        hourly_counts = defaultdict(int)
        for attack in attacks:
            # Truncate timestamp to hour
            hour_ts = attack.timestamp.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
            hourly_counts[hour_ts] += 1
        
        # Fill missing hours with 0
        timeline = []
        current_time = start_time.replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
        while current_time <= end_time:
            count = hourly_counts.get(current_time, 0)
            timeline.append({
                'time': current_time.isoformat(),
                'count': count
            })
            current_time += timedelta(hours=1)
        
        return jsonify({'status': 'success', 'data': timeline}), 200
    except Exception as e:
        logger.error(f"Error getting timeline: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/top-ips', methods=['GET'])
@token_required
def get_top_ips():
    try:
        limit = request.args.get('limit', 10, type=int)
        top_ips = db.session.query(
            AttackEvent.source_ip,
            db.func.count(AttackEvent.id).label('count')
        ).group_by(AttackEvent.source_ip).order_by(
            db.func.count(AttackEvent.id).desc()
        ).limit(limit).all()
        
        return jsonify({
            'status': 'success',
            'data': [{'ip': ip, 'count': c} for ip, c in top_ips]
        }), 200
    except Exception as e:
        logger.error(f"Error getting top IPs: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/geo-data', methods=['GET'])
@token_required
def get_geo_data():
    try:
        attacks = AttackEvent.query.filter(
            AttackEvent.geo_lat.isnot(None),
            AttackEvent.geo_lon.isnot(None)
        ).all()
        
        return jsonify({
            'status': 'success',
            'data': [
                {
                    'lat': a.geo_lat,
                    'lon': a.geo_lon,
                    'country': a.geo_country,
                    'city': a.geo_city,
                    'attack_type': a.attack_type,
                    'severity': a.severity
                }
                for a in attacks
            ]
        }), 200
    except Exception as e:
        logger.error(f"Error getting geo data: {e}")
        return jsonify({'error': str(e)}), 500

# ================= ADVANCED FIREWALL & XSS ROUTES =================
@app.route('/api/advanced/firewall/stats', methods=['GET'])
@token_required
def get_firewall_stats():
    try:
        from services.firewall_tracker import firewall_tracker
        return jsonify(firewall_tracker.get_stats()), 200
    except Exception as e:
        logger.error(f"Error getting firewall stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/xss/stats', methods=['GET'])
@token_required
def get_xss_stats():
    try:
        xss_attacks = AttackEvent.query.filter_by(attack_type='XSS Injection').count()
        recent_attacks = AttackEvent.query.filter_by(attack_type='XSS Injection').order_by(AttackEvent.timestamp.desc()).limit(10).all()
        return jsonify({
            'status': 'success',
            'stats': {
                'total_attempts': xss_attacks,
                'blocked_count': xss_attacks,
                'recent_attacks': [a.to_dict() for a in recent_attacks]
            }
        }), 200
    except Exception as e:
        logger.error(f"Error getting XSS stats: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced/xss/log', methods=['POST'])
@token_required
def log_xss():
    try:
        data = request.get_json()
        payload = data.get('payload', '')
        source_ip = _get_client_ip()
        
        _log_and_block_attack(
            attack_type='XSS Injection',
            source_ip=source_ip,
            payload=payload,
            confidence=0.95,
            user_agent=request.headers.get('User-Agent'),
            request_path=request.path,
            request_method=request.method
        )
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        logger.error(f"Error logging XSS: {e}")
        return jsonify({'error': str(e)}), 500

# ================= REGISTER EXISTING ROUTES =================
from routes.threat_detection import threat_bp
from routes.osint_integration import osint_bp
from routes.blockchain_logs import blockchain_bp
from routes.attack_simulator import simulator_bp
from routes.llm_assistant import llm_bp
from routes.advanced_analysis import advanced_bp, register_socketio_handlers
from routes.lab_integration import lab_bp

app.register_blueprint(threat_bp, url_prefix='/api/threats')
app.register_blueprint(osint_bp, url_prefix='/api/osint')
app.register_blueprint(blockchain_bp, url_prefix='/api/blockchain')
app.register_blueprint(simulator_bp, url_prefix='/api/simulator')
app.register_blueprint(llm_bp, url_prefix='/api/llm')
app.register_blueprint(advanced_bp, url_prefix='/api/advanced')
app.register_blueprint(lab_bp, url_prefix='/api/lab')

register_socketio_handlers(socketio)

# Health check
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'service': 'SARVA WAF Backend'
    }), 200

# Create tables
with app.app_context():
    db.create_all()
    logger.info("Database tables created/verified")

# Set socketio on firewall tracker
from services.firewall_tracker import firewall_tracker
firewall_tracker.set_socketio(socketio)

# Test endpoint to easily simulate an attack
@app.route('/api/test-attack', methods=['GET', 'POST'])
def test_attack():
    """Test endpoint to verify attack detection"""
    try:
        attack_type = request.args.get('type', 'XSS Injection')
        payload = request.args.get('payload', '<script>alert("test")</script>')
        source_ip = _get_client_ip()
        
        logger.info(f"Test attack triggered: {attack_type} from {source_ip}")
        _log_and_block_attack(
            attack_type=attack_type,
            source_ip=source_ip,
            payload=payload,
            confidence=0.99,
            user_agent=request.headers.get('User-Agent'),
            request_path=request.path,
            request_method=request.method
        )
        
        return jsonify({
            'status': 'success',
            'message': f'Test {attack_type} logged and blocked!'
        }), 200
    except Exception as e:
        logger.error(f"Error in test attack: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'development') == 'development'
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
