from flask import Blueprint, request, jsonify
import logging
import random
from datetime import datetime
from services.firewall_tracker import firewall_tracker

from utils.security import token_required

logger = logging.getLogger(__name__)
simulator_bp = Blueprint('simulator', __name__)

class AttackSimulator:
    """Simulate various cyberattacks for testing"""
    
    def __init__(self):
        self.active_simulations = {}
    
    def _log_to_firewall(self, attack_type, payload, target):
        """Helper to log simulated attack to firewall tracker"""
        try:
            attack = firewall_tracker.log_attack(
                attack_type=attack_type,
                source_ip=f"192.168.{random.randint(1,255)}.{random.randint(1,255)}",
                payload=f"Target: {target} | {payload}",
                blocked=True,
                confidence=random.uniform(0.85, 0.99)
            )
            return attack
        except Exception as e:
            logger.error(f"Error logging simulated attack: {str(e)}")
            return None

    def simulate_ddos(self, target_ip, duration=60):
        """Simulate DDoS attack"""
        sim_id = f"ddos_{random.randint(1000, 9999)}"
        self._log_to_firewall("ddos", "High volume UDP/TCP flood", target_ip)
        
        return {
            'simulation_id': sim_id,
            'type': 'DDoS Attack',
            'target': target_ip,
            'duration': duration,
            'packets_per_second': random.randint(1000, 10000),
            'attack_vector': random.choice(['UDP Flood', 'SYN Flood', 'HTTP Flood']),
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat(),
            'expected_detection_time': '< 5 seconds'
        }
    
    def simulate_phishing_campaign(self, target_email, email_count=100):
        """Simulate phishing campaign"""
        sim_id = f"phishing_{random.randint(1000, 9999)}"
        self._log_to_firewall("phishing", f"Campaign with {email_count} emails", target_email)
        
        return {
            'simulation_id': sim_id,
            'type': 'Phishing Campaign',
            'target': target_email,
            'email_count': email_count,
            'templates': ['Credential Harvesting', 'Malware Injection', 'Account Verification'],
            'status': 'running',
            'sent': random.randint(0, email_count),
            'detected': random.randint(0, email_count),
            'timestamp': datetime.utcnow().isoformat(),
            'detection_rate': f"{random.randint(80, 100)}%"
        }
    
    def simulate_malware_infection(self, system_id):
        """Simulate malware infection"""
        sim_id = f"malware_{random.randint(1000, 9999)}"
        self._log_to_firewall("malware", "Remote access trojan attempt", system_id)
        
        return {
            'simulation_id': sim_id,
            'type': 'Malware Infection',
            'system': system_id,
            'malware_samples': random.randint(5, 20),
            'behaviors': ['File Modification', 'Registry Access', 'Network Communication', 'Process Injection'],
            'status': 'running',
            'detected': random.randint(3, 20),
            'blocked': random.randint(2, 15),
            'timestamp': datetime.utcnow().isoformat(),
            'threat_level': random.choice(['Critical', 'High', 'Medium'])
        }
    
    def simulate_port_scan(self, target_range):
        """Simulate port scanning"""
        sim_id = f"portscan_{random.randint(1000, 9999)}"
        self._log_to_firewall("port-scan", "Full TCP port sweep", target_range)
        
        return {
            'simulation_id': sim_id,
            'type': 'Port Scan',
            'target_range': target_range,
            'ports_scanned': random.randint(100, 65535),
            'open_ports_found': random.randint(5, 25),
            'vulnerable_services': random.randint(2, 10),
            'status': 'running',
            'detection_method': 'Anomaly Detection',
            'timestamp': datetime.utcnow().isoformat(),
            'response_time': '< 1 second'
        }
    
    def simulate_sql_injection(self, target_url, payload_count=50):
        """Simulate SQL injection attacks"""
        sim_id = f"sqli_{random.randint(1000, 9999)}"
        self._log_to_firewall("sql-injection", f"' OR '1'='1' and {payload_count} other payloads", target_url)
        
        return {
            'simulation_id': sim_id,
            'type': 'SQL Injection',
            'target': target_url,
            'payloads': payload_count,
            'successful_injections': random.randint(0, payload_count),
            'data_exposed': random.randint(0, 10000),
            'status': 'running',
            'timestamp': datetime.utcnow().isoformat(),
            'waf_detection_rate': f"{random.randint(95, 100)}%"
        }

simulator = AttackSimulator()

@simulator_bp.route('/ddos', methods=['POST'])
@token_required
def start_ddos_simulation():
    """Start DDoS simulation"""
    try:
        data = request.get_json()
        target = data.get('target_ip', '192.168.1.1')
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
        data = request.get_json()
        email = data.get('target_email', 'user@example.com')
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
        data = request.get_json()
        system = data.get('system_id', 'PC-001')
        
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
        data = request.get_json()
        target = data.get('target_range', '192.168.1.0/24')
        
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
        data = request.get_json()
        url = data.get('target_url', 'http://vulnerable.app')
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
            'progress': f"{random.randint(20, 95)}%",
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({'error': str(e)}), 500
