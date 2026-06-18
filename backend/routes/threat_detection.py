from flask import Blueprint, request, jsonify
import logging
from services.threat_analyzer import ThreatAnalyzer

logger = logging.getLogger(__name__)
threat_bp = Blueprint('threats', __name__)
analyzer = ThreatAnalyzer()

@threat_bp.route('/analyze/email', methods=['POST'])
def analyze_email():
    """Analyze email for phishing"""
    try:
        data = request.get_json()
        email_content = data.get('content', '')
        sender = data.get('sender', 'unknown')
        
        if not email_content:
            return jsonify({'error': 'Email content required'}), 400
        
        result = analyzer.analyze_email(email_content, sender)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Email analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@threat_bp.route('/analyze/malware', methods=['POST'])
def analyze_malware():
    """Analyze binary/process for malware"""
    try:
        data = request.get_json()
        behavior_log = data.get('behavior_log', '')
        
        if not behavior_log:
            return jsonify({'error': 'Behavior log required'}), 400
        
        result = analyzer.analyze_binary(behavior_log)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Malware analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@threat_bp.route('/analyze/network', methods=['POST'])
def analyze_network():
    """Analyze network packet"""
    try:
        data = request.get_json()
        result = analyzer.analyze_network_packet(data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Network analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@threat_bp.route('/recent', methods=['GET'])
def get_recent_threats():
    """Get recent threats"""
    try:
        limit = request.args.get('limit', 10, type=int)
        threats = analyzer.get_recent_threats(limit)
        return jsonify({
            'threats': threats,
            'count': len(threats)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching threats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@threat_bp.route('/timeline', methods=['GET'])
def get_threat_timeline():
    """Get threat timeline"""
    try:
        hours = request.args.get('hours', 24, type=int)
        timeline = analyzer.get_threat_timeline(hours)
        return jsonify(timeline), 200
    except Exception as e:
        logger.error(f"Error fetching timeline: {str(e)}")
        return jsonify({'error': str(e)}), 500

@threat_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get threat statistics"""
    try:
        stats = analyzer.get_dashboard_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        return jsonify({'error': str(e)}), 500
