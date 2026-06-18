from flask import Blueprint, request, jsonify
import logging
from services.osint_services import OSINTAggregator

logger = logging.getLogger(__name__)
osint_bp = Blueprint('osint', __name__)
osint = OSINTAggregator()

@osint_bp.route('/investigate/ip', methods=['POST'])
def investigate_ip():
    """Investigate IP address"""
    try:
        data = request.get_json()
        ip_address = data.get('ip')
        
        if not ip_address:
            return jsonify({'error': 'IP address required'}), 400
        
        result = osint.investigate_ip(ip_address)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"IP investigation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@osint_bp.route('/investigate/file', methods=['POST'])
def investigate_file():
    """Investigate file hash"""
    try:
        data = request.get_json()
        file_hash = data.get('hash')
        
        if not file_hash:
            return jsonify({'error': 'File hash required'}), 400
        
        result = osint.investigate_file(file_hash)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"File investigation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@osint_bp.route('/investigate/url', methods=['POST'])
def investigate_url():
    """Investigate URL"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL required'}), 400
        
        result = osint.investigate_url(url)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"URL investigation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@osint_bp.route('/shodan/search', methods=['POST'])
def shodan_search():
    """Search Shodan database"""
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'Query required'}), 400
        
        result = osint.shodan.search_query(query)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Shodan search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@osint_bp.route('/abuseipdb/check', methods=['POST'])
def abuseipdb_check():
    """Check AbuseIPDB reputation"""
    try:
        data = request.get_json()
        ip = data.get('ip')
        
        if not ip:
            return jsonify({'error': 'IP required'}), 400
        
        result = osint.abuseipdb.check_ip_reputation(ip)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"AbuseIPDB check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@osint_bp.route('/virustotal/scan', methods=['POST'])
def virustotal_scan():
    """Scan with VirusTotal"""
    try:
        data = request.get_json()
        file_hash = data.get('hash')
        url = data.get('url')
        
        if file_hash:
            result = osint.virustotal.scan_file(file_hash)
        elif url:
            result = osint.virustotal.scan_url(url)
        else:
            return jsonify({'error': 'Hash or URL required'}), 400
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"VirusTotal scan error: {str(e)}")
        return jsonify({'error': str(e)}), 500
