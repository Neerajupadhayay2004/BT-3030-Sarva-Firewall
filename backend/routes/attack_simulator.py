from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timezone
from services.firewall_tracker import firewall_tracker

from utils.security import token_required

logger = logging.getLogger(__name__)
simulator_bp = Blueprint('simulator', __name__)


def _get_client_ip():
    """Extract client IP from X-Forwarded-For or remote_addr."""
    xff = request.headers.get('X-Forwarded-For', '')
    if xff:
        forwarded_ips = [ip.strip() for ip in xff.split(',') if ip.strip()]
        for ip in forwarded_ips:
            if ip and not ip.startswith(('10.', '172.16.', '192.168.', '127.')):
                return ip
        for ip in forwarded_ips:
            if ip and ip != '127.0.0.1':
                return ip
        return forwarded_ips[0] if forwarded_ips else (request.remote_addr or '127.0.0.1')
    return request.remote_addr or '127.0.0.1'


class AttackSimulator:
    """Simulate various cyberattacks for testing"""
    
    def __init__(self):
        self.active_simulations = {}
    
    def _log_to_firewall(self, attack_type, payload, target):
        """Helper to log simulated attack to firewall tracker using REAL client IP"""
        try:
            attack = firewall_tracker.log_attack(
                attack_type=attack_type,
                source_ip=_get_client_ip(),
                payload=f"Target: {target} | {payload}",
                blocked=True,
                confidence=0.90
            )
            return attack
        except Exception as e:
            logger.error(f"Error logging simulated attack: {str(e)}")
            return None

    def simulate_ddos(self, target_ip, duration=60):
        """Simulate DDoS attack"""
        sim_id = f"ddos_{abs(hash(str(datetime.now(timezone.utc).timestamp()))) % 9000 + 1000}"
        self._log_to_firewall("ddos", "High volume UDP/TCP flood", target_ip)
        
        return {
            'simulation_id': sim_id,
            'type': 'DDoS Attack',
            'target': target_ip,
            'duration': duration,
            'packets_per_second': 5000,
            'attack_vector': 'SYN Flood',
            'status': 'running',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'expected_detection_time': '< 5 seconds'
        }
    
    def simulate_phishing_campaign(self, target_email, email_count=100):
        """Simulate phishing campaign"""
        sim_id = f"phishing_{abs(hash(str(datetime.now(timezone.utc).timestamp()))) % 9000 + 1000}"
        self._log_to_firewall("phishing", f"Campaign with {email_count} emails", target_email)
        
        return {
            'simulation_id': sim_id,
            'type': 'Phishing Campaign',
            'target': target_email,
            'email_count': email_count,
            'templates': ['Credential Harvesting', 'Malware Injection', 'Account Verification'],
            'status': 'running',
            'sent': 0,
            'detected': 0,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'detection_rate': '95%'
        }
    
    def simulate_malware_infection(self, system_id):
        """Simulate malware infection"""
        sim_id = f"malware_{abs(hash(str(datetime.now(timezone.utc).timestamp()))) % 9000 + 1000}"
        self._log_to_firewall("malware", "Remote access trojan attempt", system_id)
        
        return {
            'simulation_id': sim_id,
            'type': 'Malware Infection',
            'system': system_id,
            'malware_samples': 12,
            'behaviors': ['File Modification', 'Registry Access', 'Network Communication', 'Process Injection'],
            'status': 'running',
            'detected': 8,
            'blocked': 6,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'threat_level': 'Critical'
        }
    
    def simulate_port_scan(self, target_range):
        """Simulate port scanning"""
        sim_id = f"portscan_{abs(hash(str(datetime.now(timezone.utc).timestamp()))) % 9000 + 1000}"
        self._log_to_firewall("port-scan", "Full TCP port sweep", target_range)
        
        return {
            'simulation_id': sim_id,
            'type': 'Port Scan',
            'target_range': target_range,
            'ports_scanned': 65535,
            'open_ports_found': 15,
            'vulnerable_services': 4,
            'status': 'running',
            'detection_method': 'Anomaly Detection',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'response_time': '< 1 second'
        }
    
    def simulate_sql_injection(self, target_url, payload_count=50):
        """Simulate SQL injection attacks"""
        sim_id = f"sqli_{abs(hash(str(datetime.now(timezone.utc).timestamp()))) % 9000 + 1000}"
        self._log_to_firewall("sql-injection", f"' OR '1'='1' and {payload_count} other payloads", target_url)
        
        return {
            'simulation_id': sim_id,
            'type': 'SQL Injection',
            'target': target_url,
            'payloads': payload_count,
            'successful_injections': 0,
            'data_exposed': 0,
            'status': 'running',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'waf_detection_rate': '100%'
        }

simulator = AttackSimulator()

@simulator_bp.route('/ddos', methods=['POST'])
@token_required
def start_ddos_simulation():
    """Start DDoS simulation"""
    try:
        data = request.get_json() or {}
        target = data.get('target_ip') or _get_client_ip()
        duration = data.get('duration', 60)
        
        result = simulator.simulate_ddos(target, duration)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"DDoS simulation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@simulator_bp.route('/phishing', methods=['POST'])
@token_required
def start_phishing_simulation():
    """Start phishing campaign simulation"""
    try:
        data = request.get_json() or {}
        email = data.get('target_email') or 'simulated-target@example.com'
        count = data.get('email_count', 100)
        
        result = simulator.simulate_phishing_campaign(email, count)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Phishing simulation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@simulator_bp.route('/malware', methods=['POST'])
@token_required
def start_malware_simulation():
    """Start malware infection simulation"""
    try:
        data = request.get_json() or {}
        system = data.get('system_id') or 'SIM-PC-001'
        
        result = simulator.simulate_malware_infection(system)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Malware simulation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@simulator_bp.route('/portscan', methods=['POST'])
@token_required
def start_portscan_simulation():
    """Start port scan simulation"""
    try:
        data = request.get_json() or {}
        target = data.get('target_range') or '192.168.1.0/24'
        
        result = simulator.simulate_port_scan(target)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Port scan simulation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@simulator_bp.route('/sqli', methods=['POST'])
@token_required
def start_sqli_simulation():
    """Start SQL injection simulation"""
    try:
        data = request.get_json() or {}
        url = data.get('target_url') or 'http://vulnerable-app.local'
        payloads = data.get('payload_count', 50)
        
        result = simulator.simulate_sql_injection(url, payloads)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"SQL injection simulation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@simulator_bp.route('/status/<sim_id>', methods=['GET'])
@token_required
def get_simulation_status(sim_id):
    """Get simulation status"""
    try:
        return jsonify({
            'simulation_id': sim_id,
            'status': 'running',
            'progress': '85%',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({'error': str(e)}), 500
