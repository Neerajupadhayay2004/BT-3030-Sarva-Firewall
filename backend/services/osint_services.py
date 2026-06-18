import os
import requests
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ShodanIntegration:
    """Shodan OSINT Integration"""
    
    def __init__(self):
        self.api_key = os.getenv('SHODAN_API_KEY')
        self.base_url = 'https://api.shodan.io'
    
    def search_ip(self, ip_address):
        """Search IP information on Shodan"""
        try:
            response = requests.get(
                f'{self.base_url}/shodan/host/{ip_address}',
                params={'key': self.api_key},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': 'IP not found in Shodan database', 'ip': ip_address}
        except Exception as e:
            logger.error(f"Shodan API error: {str(e)}")
            return {'error': str(e), 'ip': ip_address}
    
    def search_query(self, query):
        """Search Shodan database"""
        try:
            response = requests.get(
                f'{self.base_url}/shodan/host/search',
                params={'q': query, 'key': self.api_key},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {'error': 'Search failed', 'query': query}
        except Exception as e:
            logger.error(f"Shodan search error: {str(e)}")
            return {'error': str(e)}


class AbuseIPDBIntegration:
    """AbuseIPDB OSINT Integration"""
    
    def __init__(self):
        self.api_key = os.getenv('ABUSEIPDB_API_KEY')
        self.base_url = 'https://api.abuseipdb.com/api/v2'
    
    def check_ip_reputation(self, ip_address):
        """Check IP reputation on AbuseIPDB"""
        try:
            headers = {
                'Key': self.api_key,
                'Accept': 'application/json'
            }
            response = requests.get(
                f'{self.base_url}/check',
                params={'ipAddress': ip_address, 'maxAgeInDays': 90},
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {'error': 'IP not found', 'ip': ip_address}
        except Exception as e:
            logger.error(f"AbuseIPDB API error: {str(e)}")
            return {'error': str(e), 'ip': ip_address}


class VirusTotalIntegration:
    """VirusTotal OSINT Integration"""
    
    def __init__(self):
        self.api_key = os.getenv('VIRUSTOTAL_API_KEY')
        self.base_url = 'https://www.virustotal.com/api/v3'
    
    def scan_file(self, file_hash):
        """Scan file hash on VirusTotal"""
        try:
            headers = {
                'x-apikey': self.api_key,
                'Accept': 'application/json'
            }
            response = requests.get(
                f'{self.base_url}/files/{file_hash}',
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {'error': 'File not found', 'hash': file_hash}
        except Exception as e:
            logger.error(f"VirusTotal API error: {str(e)}")
            return {'error': str(e), 'hash': file_hash}
    
    def scan_url(self, url):
        """Scan URL on VirusTotal"""
        try:
            headers = {
                'x-apikey': self.api_key,
                'Accept': 'application/json'
            }
            response = requests.post(
                f'{self.base_url}/urls',
                headers=headers,
                data={'url': url},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return {'error': 'URL scan failed', 'url': url}
        except Exception as e:
            logger.error(f"VirusTotal URL scan error: {str(e)}")
            return {'error': str(e), 'url': url}


class OSINTAggregator:
    """Aggregate OSINT data from multiple sources"""
    
    def __init__(self):
        self.shodan = ShodanIntegration()
        self.abuseipdb = AbuseIPDBIntegration()
        self.virustotal = VirusTotalIntegration()
    
    def investigate_ip(self, ip_address):
        """Comprehensive IP investigation"""
        return {
            'ip': ip_address,
            'shodan': self.shodan.search_ip(ip_address),
            'abuseipdb': self.abuseipdb.check_ip_reputation(ip_address),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def investigate_file(self, file_hash):
        """Comprehensive file investigation"""
        return {
            'hash': file_hash,
            'virustotal': self.virustotal.scan_file(file_hash),
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def investigate_url(self, url):
        """Comprehensive URL investigation"""
        return {
            'url': url,
            'virustotal': self.virustotal.scan_url(url),
            'timestamp': datetime.utcnow().isoformat()
        }
