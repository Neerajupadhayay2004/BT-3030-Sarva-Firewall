from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class AttackEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_ip = db.Column(db.String(50), nullable=False)
    attack_type = db.Column(db.String(50), nullable=False)
    payload = db.Column(db.Text, nullable=True)
    confidence = db.Column(db.Float, default=0.9)
    severity = db.Column(db.String(20), default='MEDIUM')  # LOW, MEDIUM, HIGH, CRITICAL
    status = db.Column(db.String(20), default='BLOCKED')  # BLOCKED, ALLOWED, MONITORED
    user_agent = db.Column(db.String(500), nullable=True)
    request_path = db.Column(db.String(500), nullable=True)
    request_method = db.Column(db.String(10), nullable=True)
    geo_country = db.Column(db.String(100), nullable=True)
    geo_city = db.Column(db.String(100), nullable=True)
    geo_lat = db.Column(db.Float, nullable=True)
    geo_lon = db.Column(db.Float, nullable=True)
    ai_analysis = db.Column(db.Text, nullable=True)
    action_taken = db.Column(db.String(200), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'source_ip': self.source_ip,
            'attack_type': self.attack_type,
            'payload': self.payload,
            'confidence': self.confidence,
            'severity': self.severity,
            'status': self.status,
            'user_agent': self.user_agent,
            'request_path': self.request_path,
            'request_method': self.request_method,
            'geo_country': self.geo_country,
            'geo_city': self.geo_city,
            'geo_lat': self.geo_lat,
            'geo_lon': self.geo_lon,
            'ai_analysis': self.ai_analysis,
            'action_taken': self.action_taken
        }

class RequestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    source_ip = db.Column(db.String(50), nullable=False)
    request_path = db.Column(db.String(500), nullable=False)
    request_method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    user_agent = db.Column(db.String(500), nullable=True)
    response_time_ms = db.Column(db.Integer, nullable=True)
    is_attack = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'source_ip': self.source_ip,
            'request_path': self.request_path,
            'request_method': self.request_method,
            'status_code': self.status_code,
            'user_agent': self.user_agent,
            'response_time_ms': self.response_time_ms,
            'is_attack': self.is_attack
        }
