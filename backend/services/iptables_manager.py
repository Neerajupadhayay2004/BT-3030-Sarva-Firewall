
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
        
    def _run_iptables_command(self, cmd_args):
        """Execute iptables using list-based arguments to prevent injection"""
        try:
            # Use sudo if password is provided, but still avoid shell=True if possible
            # If we must use a pipe for sudo -S, we use a more secure method
            if self.sudo_password:
                # Still use list for the command part
                sudo_cmd = ["sudo", "-S", "iptables"] + cmd_args
                process = subprocess.Popen(
                    sudo_cmd, 
                    stdin=subprocess.PIPE, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True
                )
                stdout, stderr = process.communicate(input=f"{self.sudo_password}\n")
                returncode = process.returncode
            else:
                result = subprocess.run(["iptables"] + cmd_args, capture_output=True, text=True)
                stdout, stderr = result.stdout, result.stderr
                returncode = result.returncode
                
            if returncode == 0:
                logger.info(f"Iptables command success: iptables {' '.join(cmd_args)}")
                return True, stdout
            else:
                logger.error(f"Iptables command failed: iptables {' '.join(cmd_args)}")
                logger.error(f"Error: {stderr}")
                return False, stderr
        except Exception as e:
            logger.error(f"Iptables command error: {e}")
            return False, str(e)
            
    def add_rule(self, chain, protocol, source_port=None, dest_port=None, 
                 source_ip=None, dest_ip=None, action="ACCEPT", comment=""):
        """Add an iptables rule with sanitized inputs"""
        with self.lock:
            # Sanitize comment - only allow safe characters
            import re
            safe_comment = re.sub(r'[^a-zA-Z0-9\s\-_]', '', comment)
            
            cmd_args = [f"-A", f"{chain}"]
            
            if protocol:
                cmd_args.extend(["-p", protocol])
            
            if source_ip:
                cmd_args.extend(["-s", source_ip])
                
            if dest_ip:
                cmd_args.extend(["-d", dest_ip])
                
            if source_port:
                cmd_args.extend(["--sport", str(source_port)])
                
            if dest_port:
                cmd_args.extend(["--dport", str(dest_port)])
                
            if safe_comment:
                cmd_args.extend(["-m", "comment", "--comment", safe_comment])
                
            cmd_args.extend(["-j", action])
            
            success, output = self._run_iptables_command(cmd_args)
            
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
            return self._run_iptables_command(["-D", "INPUT", "-s", ip, "-j", "DROP"])
            
    def list_rules(self):
        """List all active iptables rules"""
        success, output = self._run_iptables_command(["-L", "-n", "-v"])
        return success, output
        
    def reset_rules(self):
        """Reset all iptables rules"""
        with self.lock:
            logger.info("Resetting iptables rules")
            self._run_iptables_command(["-F"])
            self._run_iptables_command(["-X"])
            self.rules = []
            return True
            
# Global instance
iptables_manager = IptablesManager()
