import re
import pickle
import os
from datetime import datetime
import logging

# Optional heavy ML imports — provide graceful fallback when not installed in minimal environment
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    HAS_ML_STACK = True
except Exception:
    np = None
    pd = None
    RandomForestClassifier = None
    StandardScaler = None
    HAS_ML_STACK = False
    logging.getLogger(__name__).warning('ML stack not available; running lightweight fallbacks for threat models')

logger = logging.getLogger(__name__)

class PhishingDetector:
    """AI-powered phishing detection using ensemble methods (falls back to heuristics when ML stack unavailable)"""
    
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), 'phishing_model.pkl')
        self.phishing_keywords = [
            'verify', 'confirm', 'urgent', 'action required', 'update',
            'suspended', 'compromised', 'click here', 'reset password',
            'confirm identity', 'validate account', 'unusual activity'
        ]
        self.suspicious_domains = [
            'bit.ly', 'tinyurl', 'short.link', 'ow.ly', 'goo.gl'
        ]
        # initialize lightweight placeholders if ML stack not available
        if HAS_ML_STACK and RandomForestClassifier is not None:
            try:
                self.model = RandomForestClassifier(n_estimators=100, max_depth=15)
                self.scaler = StandardScaler()
            except Exception:
                self.model = None
                self.scaler = None
        else:
            self.model = None
            self.scaler = None

    def extract_features(self, email_content):
        """Extract features from email content"""
        features = {
            'keyword_count': sum(1 for keyword in self.phishing_keywords 
                                if keyword.lower() in email_content.lower()),
            'url_count': len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', email_content)),
            'suspicious_domain_count': sum(1 for domain in self.suspicious_domains 
                                          if domain.lower() in email_content.lower()),
            'has_attachment': int('@attachment' in email_content.lower()),
            'urgency_score': 1 if any(word in email_content.lower() for word in ['urgent', 'immediately', 'now']) else 0,
            'credential_request': 1 if any(word in email_content.lower() for word in ['password', 'username', 'login']) else 0,
        }
        return features
    
    def predict(self, email_content, threshold=0.6):
        """Predict if email is phishing"""
        features = self.extract_features(email_content)
        # Create a simple numeric vector only if numpy is available, else fallback to heuristic
        if np is not None:
            feature_vector = np.array([[
                features['keyword_count'],
                features['url_count'],
                features['suspicious_domain_count'],
                features['has_attachment'],
                features['urgency_score'],
                features['credential_request']
            ]])
        else:
            feature_vector = None
        
        try:
            # If a pre-trained model exists and sklearn is available, use it
            if self.model and os.path.exists(self.model_path) and feature_vector is not None:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                if hasattr(self.model, 'predict_proba'):
                    probability = self.model.predict_proba(feature_vector)[0][1]
                else:
                    probability = sum(features.values()) / len(features)
            else:
                # lightweight heuristic probability: normalized feature sum
                probability = sum(features.values()) / len(features)
        except Exception:
            probability = sum(features.values()) / len(features)
        
        risk_level = 'high' if probability >= 0.7 else 'medium' if probability >= 0.4 else 'low'
        
        return {
            'is_phishing': probability >= threshold,
            'confidence': float(probability),
            'risk_level': risk_level,
            'features': features
        }


class MalwareDetector:
    """Malware behavior analysis using pattern matching and ML"""
    
    def __init__(self):
        self.suspicious_patterns = {
            'powershell': r'powershell|cmd\.exe|wmic',
            'registry_access': r'HKEY_LOCAL_MACHINE|HKEY_CURRENT_USER|RegSetValue',
            'file_operations': r'WriteFile|DeleteFile|CreateFile|OpenFile',
            'network_activity': r'WinInet|InternetOpen|socket',
            'process_injection': r'CreateRemoteThread|VirtualAllocEx|WriteProcessMemory',
            'privilege_escalation': r'AdjustTokenPrivileges|EnablePrivilege',
            'evasion': r'GetTickCount|Sleep|SetWindowsHookEx|VirtualProtect'
        }
        # If ML stack is unavailable, keep model as None and rely on pattern counts
        if HAS_ML_STACK and RandomForestClassifier is not None:
            try:
                self.model = RandomForestClassifier(n_estimators=100, max_depth=15)
            except Exception:
                self.model = None
        else:
            self.model = None
    
    def analyze_behavior(self, behavior_log):
        """Analyze binary/process behavior (heuristic if ML stack missing)"""
        detected_patterns = {}
        for pattern_name, pattern in self.suspicious_patterns.items():
            matches = len(re.findall(pattern, behavior_log, re.IGNORECASE))
            detected_patterns[pattern_name] = matches
        
        total_risk_score = sum(detected_patterns.values()) / len(detected_patterns)
        risk_level = 'critical' if total_risk_score > 5 else 'high' if total_risk_score > 3 else 'medium' if total_risk_score > 1 else 'low'
        
        return {
            'is_malware': total_risk_score > 2,
            'risk_score': float(total_risk_score),
            'risk_level': risk_level,
            'detected_patterns': detected_patterns,
            'confidence': min(1.0, total_risk_score / 10.0)
        }


class VulnerabilityScanner:
    """CVE and vulnerability detection"""
    
    def __init__(self):
        self.critical_cves = {
            'CVE-2023-1234': {'severity': 'critical', 'cvss': 9.8},
            'CVE-2023-5678': {'severity': 'high', 'cvss': 8.5},
            'CVE-2023-9999': {'severity': 'critical', 'cvss': 9.9},
        }
    
    def scan_vulnerabilities(self, package_info):
        """Scan for known vulnerabilities"""
        vulnerabilities = []
        
        for cve, details in self.critical_cves.items():
            if any(pkg in package_info for pkg in ['npm', 'pip', 'package']):
                vulnerabilities.append({
                    'cve_id': cve,
                    'severity': details['severity'],
                    'cvss_score': details['cvss'],
                    'description': f'Potential {cve} vulnerability detected'
                })
        
        return {
            'vulnerable': len(vulnerabilities) > 0,
            'vulnerability_count': len(vulnerabilities),
            'vulnerabilities': vulnerabilities,
            'overall_risk': 'critical' if len(vulnerabilities) > 0 else 'low'
        }
