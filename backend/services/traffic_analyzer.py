
import json
import logging
import csv
from datetime import datetime, timezone
from pathlib import Path
from collections import deque
import threading

logger = logging.getLogger(__name__)

class TrafficAnalyzer:
    def __init__(self, data_dir="traffic_data"):
        self.data_dir = Path(__file__).parent.parent / data_dir
        self.data_dir.mkdir(exist_ok=True)
        
        self.attack_log_file = self.data_dir / "attacks.csv"
        self.traffic_log_file = self.data_dir / "traffic.csv"
        
        # Initialize CSV headers if files don't exist
        self._initialize_csv_files()
        
        self.recent_traffic = deque(maxlen=1000)
        self.recent_attacks = deque(maxlen=500)
        
        self.lock = threading.Lock()
        logger.info("Traffic Analyzer initialized")
        
    def _initialize_csv_files(self):
        if not self.attack_log_file.exists():
            with open(self.attack_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "attack_type", "source_ip", "target_ip", 
                    "payload", "confidence", "blocked", "action_taken", "layer"
                ])
        
        if not self.traffic_log_file.exists():
            with open(self.traffic_log_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "source_ip", "dest_ip", "source_port", 
                    "dest_port", "protocol", "packet_size", "flags", 
                    "action", "layer"
                ])
                
    def log_packet(self, packet_data, layer="application"):
        with self.lock:
            timestamp = datetime.now(timezone.utc).isoformat()
            row = [
                timestamp,
                packet_data.get("source_ip", ""),
                packet_data.get("dest_ip", ""),
                packet_data.get("source_port", ""),
                packet_data.get("dest_port", ""),
                packet_data.get("protocol", ""),
                packet_data.get("packet_size", 0),
                packet_data.get("flags", ""),
                packet_data.get("action", ""),
                layer
            ]
            self.recent_traffic.append(row)
            
            with open(self.traffic_log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            logger.info(f"Logged packet at {layer} layer: {packet_data}")
            
    def log_attack(self, attack_data, layer="application"):
        with self.lock:
            timestamp = datetime.now(timezone.utc).isoformat()
            row = [
                timestamp,
                attack_data.get("attack_type", ""),
                attack_data.get("source_ip", ""),
                attack_data.get("target_ip", ""),
                attack_data.get("payload", ""),
                attack_data.get("confidence", 0.0),
                attack_data.get("blocked", False),
                attack_data.get("action_taken", ""),
                layer
            ]
            self.recent_attacks.append(row)
            
            with open(self.attack_log_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            logger.info(f"Logged attack at {layer} layer: {attack_data}")
            
    def get_traffic_summary(self, limit=100):
        return list(self.recent_traffic)[-limit:]
        
    def get_attack_summary(self, limit=100):
        return list(self.recent_attacks)[-limit:]
        
    def get_attack_statistics(self):
        stats = {
            "total_attacks": 0,
            "attacks_by_type": {},
            "attacks_by_layer": {},
            "blocked_count": 0,
            "allowed_count": 0
        }
        
        try:
            with open(self.attack_log_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats["total_attacks"] += 1
                    attack_type = row["attack_type"]
                    layer = row["layer"]
                    
                    if attack_type not in stats["attacks_by_type"]:
                        stats["attacks_by_type"][attack_type] = 0
                    stats["attacks_by_type"][attack_type] += 1
                    
                    if layer not in stats["attacks_by_layer"]:
                        stats["attacks_by_layer"][layer] = 0
                    stats["attacks_by_layer"][layer] += 1
                    
                    if row.get("blocked", "False") == "True":
                        stats["blocked_count"] += 1
                    else:
                        stats["allowed_count"] += 1
        except Exception as e:
            logger.error(f"Error calculating attack stats: {e}")
            
        return stats
        
    def get_traffic_statistics(self):
        stats = {
            "total_packets": 0,
            "packets_by_protocol": {},
            "packets_by_layer": {},
            "total_bytes": 0
        }
        
        try:
            with open(self.traffic_log_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    stats["total_packets"] += 1
                    protocol = row.get("protocol", "")
                    layer = row.get("layer", "application")
                    
                    if protocol not in stats["packets_by_protocol"]:
                        stats["packets_by_protocol"][protocol] = 0
                    stats["packets_by_protocol"][protocol] += 1
                    
                    if layer not in stats["packets_by_layer"]:
                        stats["packets_by_layer"][layer] = 0
                    stats["packets_by_layer"][layer] += 1
                    
                    try:
                        stats["total_bytes"] += int(row.get("packet_size", 0))
                    except ValueError:
                        pass
        except Exception as e:
            logger.error(f"Error calculating traffic stats: {e}")
            
        return stats
        
# Global instance
traffic_analyzer = TrafficAnalyzer()
