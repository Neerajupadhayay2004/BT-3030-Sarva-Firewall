import random
from datetime import datetime, timedelta
import logging
from services.threat_models import PhishingDetector, MalwareDetector, VulnerabilityScanner
from services.osint_services import OSINTAggregator
from services.blockchain_service import BlockchainLogger

logger = logging.getLogger(__name__)

class ThreatAnalyzer:
    """Central threat analysis engine"""
    
    def __init__(self):
        self.phishing_detector = PhishingDetector()
        self.malware_detector = MalwareDetector()
        self.vuln_scanner = VulnerabilityScanner()
        self.osint = OSINTAggregator()
        self.blockchain = BlockchainLogger()
        self.threats_log = []
    
    def analyze_email(self, email_content, sender):
        """Comprehensive email analysis"""
        phishing_result = self.phishing_detector.predict(email_content)
        
        threat = {
            'id': f"email_{random.randint(1000, 9999)}",
            'type': 'phishing_email',
            'source': sender,
            'content_preview': email_content[:100],
            'analysis': phishing_result,
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'quarantine' if phishing_result['is_phishing'] else 'allow',
            'status': 'detected' if phishing_result['is_phishing'] else 'clean'
        }
        
        # Log to blockchain
        self.blockchain.log_threat_to_blockchain(threat)
        self.threats_log.append(threat)
        
        return threat
    
    def analyze_binary(self, binary_behavior_log):
        """Comprehensive binary analysis"""
        malware_result = self.malware_detector.analyze_behavior(binary_behavior_log)
        
        threat = {
            'id': f"binary_{random.randint(1000, 9999)}",
            'type': 'malware',
            'behavior': binary_behavior_log[:100],
            'analysis': malware_result,
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'block' if malware_result['is_malware'] else 'allow',
            'status': 'detected' if malware_result['is_malware'] else 'clean'
        }
        
        self.blockchain.log_threat_to_blockchain(threat)
        self.threats_log.append(threat)
        
        return threat
    
    def analyze_network_packet(self, packet_data):
        """Analyze network packet for threats"""
        # Simulate network analysis
        threat_types = ['ddos', 'port_scan', 'exploit_attempt', 'data_exfiltration', 'botnet_traffic']
        detected_threat = random.choice([True, False])
        
        threat = {
            'id': f"packet_{random.randint(1000, 9999)}",
            'type': threat_types[random.randint(0, len(threat_types)-1)] if detected_threat else 'benign',
            'source_ip': packet_data.get('source_ip', '192.168.1.100'),
            'dest_ip': packet_data.get('dest_ip', '10.0.0.50'),
            'port': packet_data.get('port', 443),
            'threat_detected': detected_threat,
            'confidence': random.uniform(0.5, 1.0) if detected_threat else random.uniform(0.0, 0.2),
            'timestamp': datetime.utcnow().isoformat(),
            'action': 'block' if detected_threat else 'allow'
        }
        
        self.blockchain.log_threat_to_blockchain(threat)
        self.threats_log.append(threat)
        
        return threat
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        return {
            'total_threats_detected': 156,
            'threats_blocked': 142,
            'threats_in_last_hour': random.randint(3, 15),
            'critical_threats': 5,
            'phishing_emails': 34,
            'malware_detected': 12,
            'network_attacks': 8,
            'system_uptime': '99.8%',
            'last_update': datetime.utcnow().isoformat()
        }
    
    def get_recent_threats(self, limit=10):
        """Get recent threats"""
        return sorted(self.threats_log, 
                     key=lambda x: x['timestamp'], 
                     reverse=True)[:limit]
    
    def get_threat_timeline(self, hours=24):
        """Get threat timeline for graph"""
        timeline = []
        now = datetime.utcnow()
        
        for i in range(hours):
            hour = now - timedelta(hours=i)
            timeline.append({
                'time': hour.strftime('%H:%M'),
                'threats': random.randint(0, 10),
                'blocked': random.randint(0, 8),
                'timestamp': hour.isoformat()
            })
        
        return sorted(timeline, key=lambda x: x['timestamp'])
