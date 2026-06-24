
from flask import Blueprint, request, jsonify
import logging
from services.traffic_analyzer import traffic_analyzer
from services.iptables_manager import iptables_manager
from services.pfsense_manager import pfsense_manager
from services.scapy_packet_inspector import scapy_inspector
from services.firewall_tracker import firewall_tracker

from utils.security import token_required

logger = logging.getLogger(__name__)
lab_bp = Blueprint('lab', __name__)


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

# ================ Traffic Analysis Routes ================
@lab_bp.route('/traffic/history', methods=['GET'])
@token_required
def get_traffic_history():
    limit = int(request.args.get('limit', 100))
    traffic = traffic_analyzer.get_traffic_summary(limit)
    return jsonify({
        "success": True,
        "data": traffic
    }), 200

@lab_bp.route('/traffic/statistics', methods=['GET'])
@token_required
def get_traffic_stats():
    stats = traffic_analyzer.get_traffic_statistics()
    return jsonify({
        "success": True,
        "data": stats
    }), 200

@lab_bp.route('/attacks/history', methods=['GET'])
@token_required
def get_attack_history():
    limit = int(request.args.get('limit', 100))
    attacks = traffic_analyzer.get_attack_summary(limit)
    return jsonify({
        "success": True,
        "data": attacks
    }), 200

@lab_bp.route('/attacks/statistics', methods=['GET'])
@token_required
def get_attack_stats():
    stats = traffic_analyzer.get_attack_statistics()
    return jsonify({
        "success": True,
        "data": stats
    }), 200

# ================ Iptables Routes (Host Layer) ================
@lab_bp.route('/iptables/rules', methods=['GET'])
@token_required
def get_iptables_rules():
    success, rules = iptables_manager.list_rules()
    return jsonify({
        "success": success,
        "data": rules
    }), 200 if success else 500

@lab_bp.route('/iptables/rules', methods=['POST'])
@token_required
def add_iptables_rule():
    try:
        data = request.get_json()
        chain = data.get("chain", "INPUT")
        protocol = data.get("protocol")
        source_port = data.get("source_port")
        dest_port = data.get("dest_port")
        source_ip = data.get("source_ip")
        dest_ip = data.get("dest_ip")
        action = data.get("action", "ACCEPT")
        comment = data.get("comment", "")
        
        success, rule = iptables_manager.add_rule(
            chain, protocol, source_port, dest_port, 
            source_ip, dest_ip, action, comment
        )
        
        return jsonify({
            "success": success,
            "data": rule
        }), 200 if success else 500
    except Exception as e:
        logger.error(f"Error adding iptables rule: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@lab_bp.route('/iptables/block', methods=['POST'])
@token_required
def block_ip_iptables():
    try:
        data = request.get_json()
        ip = data.get("ip")
        duration = data.get("duration")
        comment = data.get("comment", "IP blocked by SARVA Firewall")
        
        success = iptables_manager.block_ip(ip, duration, comment)
        
        return jsonify({
            "success": success
        }), 200
    except Exception as e:
        logger.error(f"Error blocking IP via iptables: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@lab_bp.route('/iptables/reset', methods=['POST'])
@token_required
def reset_iptables():
    success = iptables_manager.reset_rules()
    return jsonify({
        "success": success
    }), 200

# ================ PfSense Routes (Network Layer) ================
@lab_bp.route('/pfsense/configure', methods=['POST'])
@token_required
def configure_pfsense():
    try:
        data = request.get_json()
        base_url = data.get("base_url")
        api_key = data.get("api_key")
        
        pfsense_manager.configure(base_url, api_key)
        return jsonify({
            "success": True,
            "message": "pfSense manager configured"
        }), 200
    except Exception as e:
        logger.error(f"Error configuring pfSense: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@lab_bp.route('/pfsense/rules', methods=['GET'])
@token_required
def get_pfsense_rules():
    success, rules = pfsense_manager.list_rules()
    return jsonify({
        "success": success,
        "data": rules
    }), 200 if success else 500

@lab_bp.route('/pfsense/rules', methods=['POST'])
@token_required
def add_pfsense_rule():
    try:
        data = request.get_json()
        protocol = data.get("protocol", "tcp")
        source = data.get("source", "any")
        destination = data.get("destination", "any")
        port = data.get("port")
        action = data.get("action", "block")
        description = data.get("description", "")
        
        success, rule_data = pfsense_manager.add_firewall_rule(
            protocol, source, destination, port, action, description
        )
        
        return jsonify({
            "success": success,
            "data": rule_data
        }), 200 if success else 500
    except Exception as e:
        logger.error(f"Error adding pfSense rule: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@lab_bp.route('/pfsense/apply', methods=['POST'])
@token_required
def apply_pfsense_changes():
    success, data = pfsense_manager.apply_changes()
    return jsonify({
        "success": success,
        "data": data
    }), 200 if success else 500

@lab_bp.route('/pfsense/status', methods=['GET'])
@token_required
def get_pfsense_status():
    success, data = pfsense_manager.get_status()
    return jsonify({
        "success": success,
        "data": data
    }), 200 if success else 500

# ================ Scapy Packet Inspection Routes (Packet Layer) ================
@lab_bp.route('/scapy/start', methods=['POST'])
@token_required
def start_scapy_sniffing():
    try:
        data = request.get_json()
        interface = data.get("interface")
        filter_str = data.get("filter")
        
        scapy_inspector.start_sniffing(interface, filter_str)
        
        return jsonify({
            "success": True,
            "message": "Started packet sniffing"
        }), 200
    except Exception as e:
        logger.error(f"Error starting packet sniffing: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@lab_bp.route('/scapy/stop', methods=['POST'])
@token_required
def stop_scapy_sniffing():
    scapy_inspector.stop_sniffing()
    return jsonify({
        "success": True,
        "message": "Stopped packet sniffing"
    }), 200

@lab_bp.route('/scapy/packets', methods=['GET'])
@token_required
def get_scapy_packets():
    limit = int(request.args.get('limit', 100))
    packets = scapy_inspector.get_captured_packets(limit)
    return jsonify({
        "success": True,
        "data": packets
    }), 200

@lab_bp.route('/scapy/test', methods=['POST'])
@token_required
def test_scapy_packet():
    try:
        data = request.get_json() or {}
        src_ip = data.get("source_ip") or _get_client_ip()
        dst_ip = data.get("dest_ip") or request.host or '127.0.0.1'
        src_port = data.get("source_port", 12345)
        dst_port = data.get("dest_port", 80)
        protocol = data.get("protocol", "TCP")
        
        success = scapy_inspector.generate_test_packet(
            src_ip, dst_ip, src_port, dst_port, protocol
        )
        
        return jsonify({
            "success": success
        }), 200
    except Exception as e:
        logger.error(f"Error generating test packet: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ================ Cross-Layer Integration ================
@lab_bp.route('/firewall/log-attack', methods=['POST'])
@token_required
def log_attack_all_layers():
    try:
        data = request.get_json() or {}
        attack_type = data.get("attack_type", "unknown")
        source_ip = data.get("source_ip") or _get_client_ip()
        payload = data.get("payload", "")
        confidence = data.get("confidence", 0.95)
        layer = data.get("layer", "application")
        
        attack_data = {
            "attack_type": attack_type,
            "source_ip": source_ip,
            "target_ip": data.get("target_ip", ""),
            "payload": payload,
            "confidence": confidence,
            "blocked": data.get("blocked", True),
            "action_taken": data.get("action_taken", "Logged"),
            "layer": layer
        }
        
        # Log to traffic analyzer
        traffic_analyzer.log_attack(attack_data, layer)
        
        # Log to firewall tracker
        firewall_tracker.log_packet(
            attack_type, source_ip, payload, "BLOCKED", confidence
        )
        
        return jsonify({
            "success": True,
            "data": attack_data
        }), 200
    except Exception as e:
        logger.error(f"Error logging attack: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
