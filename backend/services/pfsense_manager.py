
import logging
import requests
import threading
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class PfSenseManager:
    def __init__(self):
        self.base_url = None
        self.api_key = None
        self.rules = []
        self.lock = threading.Lock()
        logger.info("PfSense Manager initialized")
        
    def configure(self, base_url, api_key):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        
    def _make_api_call(self, endpoint, method="GET", data=None):
        if not self.base_url or not self.api_key:
            logger.error("pfSense manager not configured (no base URL or API key)")
            return False, "pfSense manager not configured"
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            url = f"{self.base_url}/api/{endpoint}"
            logger.info(f"Making pfSense API call: {method} {url}")
            
            if method == "GET":
                response = requests.get(url, headers=headers, verify=False)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, verify=False)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, verify=False)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, verify=False)
            
            if response.status_code in [200, 201]:
                return True, response.json()
            else:
                logger.error(f"pfSense API call failed: {response.status_code} {response.text}")
                return False, response.text
        except Exception as e:
            logger.error(f"pfSense API call error: {e}")
            return False, str(e)
            
    def add_firewall_rule(self, protocol, source, destination, port, 
                         action="block", description="Rule added by SARVA Firewall"):
        with self.lock:
            rule = {
                "type": "pass" if action == "allow" else "block",
                "interface": "wan",
                "ipprotocol": "inet4",
                "protocol": protocol,
                "source": source,
                "destination": destination,
                "destination_port": port,
                "descr": description,
                "enabled": True
            }
            
            success, result = self._make_api_call("firewall/rules", method="POST", data=rule)
            if success:
                rule_data = {
                    "id": len(self.rules),
                    "timestamp": datetime.utcnow().isoformat(),
                    "rule": rule
                }
                self.rules.append(rule_data)
                logger.info(f"Added pfSense rule: {rule}")
                
            return success, rule_data if success else None
            
    def block_ip_range(self, ip_range, duration=None):
        rule_data = {
            "type": "block",
            "source": ip_range,
            "descr": f"Blocked by SARVA Firewall - {datetime.utcnow().isoformat()}"
        }
        
        success, result = self._make_api_call("firewall/rules", method="POST", data=rule_data)
        if success and duration:
            threading.Thread(
                target=self._schedule_unblock_range, 
                args=(ip_range, duration), 
                daemon=True
            ).start()
            
        return success
        
    def _schedule_unblock_range(self, ip_range, delay_seconds):
        import time
        time.sleep(delay_seconds)
        self.unblock_ip_range(ip_range)
        
    def unblock_ip_range(self, ip_range):
        logger.info(f"Unblocking IP range: {ip_range}")
        return True
        
    def get_status(self):
        success, data = self._make_api_call("system/status")
        return success, data
        
    def list_rules(self):
        success, data = self._make_api_call("firewall/rules")
        return success, data
        
    def apply_changes(self):
        return self._make_api_call("firewall/apply", method="POST")
        
# Global instance
pfsense_manager = PfSenseManager()
