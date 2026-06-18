"""
XSS Attack Tracker - Tracks and logs all XSS attempts
"""

import time
import json
from collections import deque
from datetime import datetime

class XSSTracker:
    def __init__(self, max_logs=100):
        self.attack_log = deque(maxlen=max_logs)
        self.blocked_count = 0
        self.total_attempts = 0
        
    def log_attack(self, payload: str, source: str = "web") -> dict:
        """Log a new XSS attempt"""
        self.total_attempts += 1
        self.blocked_count += 1
        
        attack = {
            "id": self.total_attempts,
            "timestamp": datetime.utcnow().isoformat(),
            "payload": payload,
            "source": source,
            "blocked": True,
            "severity": "HIGH"
        }
        
        self.attack_log.append(attack)
        return attack
        
    def get_stats(self) -> dict:
        """Get XSS statistics"""
        now = datetime.utcnow()
        last_hour = [
            a for a in self.attack_log 
            if (now - datetime.fromisoformat(a["timestamp"])).total_seconds() < 3600
        ]
        
        return {
            "total_attempts": self.total_attempts,
            "blocked_count": self.blocked_count,
            "last_hour_count": len(last_hour),
            "recent_attacks": list(self.attack_log)[-10:][::-1]  # Last 10, newest first
        }
        
    def get_timeline_data(self, points=20) -> list:
        """Get data for timeline graph"""
        timeline = []
        now = time.time()
        
        for i in range(points):
            window_start = now - (points - i) * 60  # 1-minute intervals
            count = len([
                a for a in self.attack_log 
                if datetime.fromisoformat(a["timestamp"]).timestamp() >= window_start
            ])
            timeline.append({
                "time": datetime.fromtimestamp(window_start).strftime("%H:%M:%S"),
                "attacks": count
            })
            
        return timeline
        
# Global tracker instance
xss_tracker = XSSTracker()