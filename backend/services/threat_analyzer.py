import random
from datetime import datetime, timedelta, timezone
import logging
import re
from services.threat_models import PhishingDetector, MalwareDetector, VulnerabilityScanner
from services.osint_services import OSINTAggregator
from services.blockchain_service import BlockchainLogger
from services.local_llm_service import LocalLLMService

logger = logging.getLogger(__name__)

# Common regex patterns for simple rule-based detection
_SUSPICIOUS_PATTERNS = [
    re.compile(r"(?i)(union select|select .* from .* where|drop table|--|;\s*--)"),  # SQLi
    re.compile(r"(?i)(<script>|</script>|onerror=|onload=)"),  # XSS
    re.compile(r"(?i)(/etc/passwd|\.{2}/|/proc/)"),  # LFI/path traversal
    re.compile(r"(?i)(nmap|masscan|sqlmap|nikto)")  # scanner user agents/tools
]

class ThreatAnalyzer:
    """Central threat analysis engine"""
    
    def __init__(self):
        self.phishing_detector = PhishingDetector()
        self.malware_detector = MalwareDetector()
        self.vuln_scanner = VulnerabilityScanner()
        self.osint = OSINTAggregator()
        self.blockchain = BlockchainLogger()
        self.threats_log = []
        # Local LLM service — by default will pick local engine if available
        try:
            self.llm = LocalLLMService()
        except Exception:
            self.llm = None

    def analyze_email(self, email_content, sender):
        """Comprehensive email analysis"""
        phishing_result = self.phishing_detector.predict(email_content)
        now = datetime.now(timezone.utc).isoformat()
        threat = {
            'id': f"email_{random.randint(1000, 9999)}",
            'type': 'phishing_email',
            'source': sender,
            'content_preview': email_content[:100],
            'analysis': phishing_result,
            'timestamp': now,
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
        now = datetime.now(timezone.utc).isoformat()
        threat = {
            'id': f"binary_{random.randint(1000, 9999)}",
            'type': 'malware',
            'behavior': binary_behavior_log[:100],
            'analysis': malware_result,
            'timestamp': now,
            'action': 'block' if malware_result['is_malware'] else 'allow',
            'status': 'detected' if malware_result['is_malware'] else 'clean'
        }
        
        self.blockchain.log_threat_to_blockchain(threat)
        self.threats_log.append(threat)
        
        return threat
    
    def analyze_network_packet(self, packet_data):
        """Analyze network packet for threats using regex rules + ML/LLM enrichment."""
        payload = packet_data.get('payload', '') or ''
        source_ip = packet_data.get('source_ip', 'unknown')
        dest_ip = packet_data.get('dest_ip', 'unknown')
        port = packet_data.get('port', 0)

        detected = False
        match_patterns = []

        # Run through suspicious regex patterns
        for patt in _SUSPICIOUS_PATTERNS:
            if patt.search(payload) or patt.search(str(packet_data)):
                detected = True
                match_patterns.append(patt.pattern)

        # simple heuristic: many small packets to many ports -> possible port scan / ddos
        if packet_data.get('packet_count', 1) > 50 or packet_data.get('bytes', 0) > 10_000_000:
            detected = True
            match_patterns.append('volume_or_count_threshold')

        confidence = 0.5
        if detected:
            confidence = 0.7 + random.random() * 0.3
            threat_type = 'exploit_attempt' if any('select' in p.lower() or 'script' in p.lower() for p in match_patterns) else 'ddos' if 'volume_or_count_threshold' in match_patterns else 'suspicious'
            action = 'block'
        else:
            threat_type = 'benign'
            confidence = random.uniform(0.0, 0.2)
            action = 'allow'

        now = datetime.now(timezone.utc).isoformat()
        threat = {
            'id': f"packet_{random.randint(1000, 9999)}",
            'type': threat_type,
            'source_ip': source_ip,
            'dest_ip': dest_ip,
            'port': port,
            'threat_detected': detected,
            'confidence': round(confidence, 3),
            'timestamp': now,
            'action': action,
            'matched_rules': match_patterns
        }

        # Enrich with LLM analysis when available and threat detected
        if detected and self.llm and getattr(self.llm, 'is_running', False):
            try:
                analysis = self.llm.analyze_threat(threat)
                threat['llm_analysis'] = analysis
            except Exception as e:
                logger.warning(f"LLM enrichment failed: {e}")
                threat['llm_analysis'] = 'LLM error'

        # Persist and record
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
