from flask import Blueprint, request, jsonify
import logging
from services.llm_service import LocalLLMAssistant

logger = logging.getLogger(__name__)
llm_bp = Blueprint('llm', __name__)
llm = LocalLLMAssistant()

@llm_bp.route('/analyze', methods=['POST'])
def analyze_threat_with_llm():
    """Analyze threat using LLM"""
    try:
        data = request.get_json()
        threat_data = {
            'type': data.get('type', 'unknown'),
            'severity': data.get('severity', 'medium'),
            'source': data.get('source', 'unknown'),
            'details': data.get('details', '')
        }
        
        result = llm.analyze_threat(threat_data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"LLM analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/report', methods=['POST'])
def generate_security_report():
    """Generate security report using LLM"""
    try:
        data = request.get_json()
        threat_logs = data.get('threat_logs', [])
        
        result = llm.generate_security_report(threat_logs)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/chat', methods=['POST'])
def chat_with_ai():
    """Chat with AI security assistant"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': 'Message required'}), 400
        
        # Simulate chat response
        return jsonify({
            'user_message': message,
            'assistant_response': f"I've analyzed your security query: '{message}'. Please provide more details about the specific threat or vulnerability you're concerned about.",
            'llm_available': llm.is_available,
            'timestamp': None
        }), 200
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/status', methods=['GET'])
def get_llm_status():
    """Get LLM service status"""
    try:
        return jsonify({
            'llm_available': llm.is_available,
            'model': llm.llm_model,
            'base_url': llm.base_url,
            'status': 'online' if llm.is_available else 'offline'
        }), 200
    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@llm_bp.route('/recommendations', methods=['POST'])
def get_recommendations():
    """Get AI recommendations for threat mitigation"""
    try:
        data = request.get_json()
        threat_type = data.get('threat_type', 'unknown')
        
        recommendations = {
            'phishing': [
                'Implement multi-factor authentication',
                'Deploy email filtering and DKIM/SPF',
                'Conduct user security awareness training',
                'Enable real-time email link scanning'
            ],
            'malware': [
                'Deploy endpoint detection and response (EDR)',
                'Implement behavioral analysis',
                'Update antivirus signatures regularly',
                'Isolate affected systems immediately'
            ],
            'ddos': [
                'Activate DDoS mitigation services',
                'Implement rate limiting',
                'Use CDN with DDoS protection',
                'Increase bandwidth capacity'
            ],
            'default': [
                'Enable comprehensive logging and monitoring',
                'Implement zero-trust architecture',
                'Regular security audits and penetration testing',
                'Maintain up-to-date patches and configurations'
            ]
        }
        
        recs = recommendations.get(threat_type, recommendations['default'])
        
        return jsonify({
            'threat_type': threat_type,
            'recommendations': recs,
            'timestamp': None
        }), 200
    except Exception as e:
        logger.error(f"Recommendation error: {str(e)}")
        return jsonify({'error': str(e)}), 500
