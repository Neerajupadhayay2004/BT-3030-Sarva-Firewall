
import logging
import subprocess
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class IptablesManager:
    def __init__(self):
        self.rules = []
        self.lock = threading.Lock()
        self.sudo_password = None
        logger.info("Iptables Manager initialized")
        
    def _run_iptables_command(self, cmd):
        try:
            if self.sudo_password:
                full_cmd = f"echo {self.sudo_password} | sudo -S iptables {cmd}"
                result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
            else:
                result = subprocess.run(["iptables", *cmd.split()], capture_output=True, text=True)
                
            if result.returncode == 0:
                logger.info(f"Iptables command success: iptables {cmd}")
                return True, result.stdout
            else:
                logger.error(f"Iptables command failed: iptables {cmd}")
                logger.error(f"Error: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            logger.error(f"Iptables command error: {e}")
            return False, str(e)
            
    def add_rule(self, chain, protocol, source_port=None, dest_port=None, 
                 source_ip=None, dest_ip=None, action="ACCEPT", comment=""):
        """Add an iptables rule"""
        with self.lock:
            cmd_parts = [f"-A {chain}"]
            
            if protocol:
                cmd_parts.append(f"-p {protocol}")
            
            if source_ip:
                cmd_parts.append(f"-s {source_ip}")
                
            if dest_ip:
                cmd_parts.append(f"-d {dest_ip}")
                
            if source_port:
                cmd_parts.append(f"--sport {source_port}")
                
            if dest_port:
                cmd_parts.append(f"--dport {dest_port}")
                
            if comment:
                cmd_parts.append(f'-m comment --comment "{comment}"')
                
            cmd_parts.append(f"-j {action}")
            
            cmd = " ".join(cmd_parts)
            success, output = self._run_iptables_command(cmd)
            
            if success:
                rule = {
                    "id": len(self.rules),
                    "chain": chain,
                    "protocol": protocol,
                    "source_port": source_port,
                    "dest_port": dest_port,
                    "source_ip": source_ip,
                    "dest_ip": dest_ip,
                    "action": action,
                    "comment": comment,
                    "timestamp": datetime.utcnow().isoformat()
                }
                self.rules.append(rule)
                logger.info(f"Added iptables rule: {rule}")
                
            return success, rule if success else None
            
    def block_ip(self, ip, duration=None, comment="IP blocked by SARVA Firewall"):
        """Block an IP address"""
        success, _ = self.add_rule(
            chain="INPUT",
            protocol=None,
            source_ip=ip,
            action="DROP",
            comment=comment
        )
        if duration:
            threading.Thread(
                target=self._schedule_unblock, 
                args=(ip, duration), 
                daemon=True
            ).start()
        return success
        
    def _schedule_unblock(self, ip, delay_seconds):
        import time
        time.sleep(delay_seconds)
        self.unblock_ip(ip)
        
    def unblock_ip(self, ip):
        """Unblock an IP address"""
        with self.lock:
            logger.info(f"Unblocking IP: {ip}")
            return self._run_iptables_command(f"-D INPUT -s {ip} -j DROP")
            
    def list_rules(self):
        """List all active iptables rules"""
        success, output = self._run_iptables_command("-L -n -v")
        return success, output
        
    def reset_rules(self):
        """Reset all iptables rules"""
        with self.lock:
            logger.info("Resetting iptables rules")
            self._run_iptables_command("-F")
            self._run_iptables_command("-X")
            self.rules = []
            return True
            
# Global instance
iptables_manager = IptablesManager()
