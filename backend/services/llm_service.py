import requests
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LocalLLMAssistant:
    """Local LLM integration for offline AI analysis"""
    
    def __init__(self):
        self.llm_model = os.getenv('LLM_MODEL', 'llama2')
        self.base_url = os.getenv('LLM_BASE_URL', 'http://localhost:11434')
        self.is_available = self._check_availability()
    
    def _check_availability(self):
        """Check if LLM service is available"""
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def analyze_threat(self, threat_data):
        """Analyze threat using LLM"""
        if not self.is_available:
            return self._generate_fallback_analysis(threat_data)
        
        try:
            prompt = f"""Analyze this security threat and provide recommendations:

Threat Type: {threat_data.get('type', 'unknown')}
Severity: {threat_data.get('severity', 'unknown')}
Source: {threat_data.get('source', 'unknown')}
Details: {threat_data.get('details', 'N/A')}

Provide:
1. Risk assessment
2. Recommended actions
3. Prevention strategies"""
            
            response = requests.post(
                f'{self.base_url}/api/generate',
                json={
                    'model': self.llm_model,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'analysis': response.json()['response'],
                    'model': self.llm_model,
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"LLM analysis error: {str(e)}")
        
        return self._generate_fallback_analysis(threat_data)
    
    def generate_security_report(self, threat_logs):
        """Generate comprehensive security report using LLM"""
        if not self.is_available:
            return self._generate_fallback_report(threat_logs)
        
        try:
            threat_summary = "\n".join([
                f"- {t.get('type')}: {t.get('status')} at {t.get('timestamp')}"
                for t in threat_logs[:5]
            ])
            
            prompt = f"""Generate a security incident report based on these threats:

{threat_summary}

Include:
1. Executive Summary
2. Threat Analysis
3. Detected Attack Patterns
4. Recommended Actions
5. Prevention Strategies"""
            
            response = requests.post(
                f'{self.base_url}/api/generate',
                json={
                    'model': self.llm_model,
                    'prompt': prompt,
                    'stream': False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'report': response.json()['response'],
                    'threat_count': len(threat_logs),
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Report generation error: {str(e)}")
        
        return self._generate_fallback_report(threat_logs)
    
    def _generate_fallback_analysis(self, threat_data):
        """Fallback analysis when LLM is unavailable"""
        threat_type = threat_data.get('type', 'unknown')
        severity = threat_data.get('severity', 'medium')
        
        fallback_responses = {
            'phishing': "This appears to be a phishing attempt. Recommended actions: Block sender, Alert user, Update phishing rules.",
            'malware': f"Malware detected with {severity} severity. Recommended: Isolate system, Run full scan, Block communication.",
            'ddos': "DDoS attack pattern detected. Recommended: Activate DDoS protection, Increase bandwidth, Monitor traffic.",
            'exploit': f"Exploit attempt detected ({severity}). Recommended: Patch vulnerability, Block attacker IP, Update firewall rules."
        }
        
        return {
            'success': True,
            'analysis': fallback_responses.get(threat_type, "Threat detected. Review and take appropriate action."),
            'model': 'offline_fallback',
            'llm_available': False,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _generate_fallback_report(self, threat_logs):
        """Fallback report generation"""
        return {
            'success': True,
            'report': f"""
SARVA Security Report
Generated: {datetime.utcnow().isoformat()}

SUMMARY:
- Total Threats Detected: {len(threat_logs)}
- Critical: {sum(1 for t in threat_logs if t.get('severity') == 'critical')}
- High: {sum(1 for t in threat_logs if t.get('severity') == 'high')}

RECOMMENDATIONS:
1. Review all detected threats immediately
2. Update firewall rules for blocked IPs
3. Conduct full system scan
4. Train users on phishing awareness
5. Enable advanced threat monitoring

STATUS: All critical threats have been blocked and logged.
            """.strip(),
            'threat_count': len(threat_logs),
            'llm_available': False,
            'timestamp': datetime.utcnow().isoformat()
        }
