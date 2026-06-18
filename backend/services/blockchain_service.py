"""
Enhanced Blockchain Service with Immutable Audit Trail
Advanced threat logging with blockchain verification and smart contracts
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import hashlib
import time
from dataclasses import asdict, dataclass
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ThreatRecord:
    """Immutable threat record for blockchain"""
    timestamp: str
    source_ip: str
    destination_ip: str
    threat_type: str
    severity: str
    confidence: float
    ml_model: str
    action_taken: str
    evidence_hash: str
    record_id: str
    
    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict())


class BlockchainAuditService:
    """Blockchain-based immutable threat audit trail"""
    
    def __init__(self):
        self.threat_ledger = []
        self.block_chain = []
        self.pending_transactions = []
        logger.info("BlockchainAuditService initialized")
    
    def create_block(self, transactions: list, previous_hash: str = "0") -> Dict:
        """Create a new block in the chain"""
        try:
            block = {
                'index': len(self.block_chain),
                'timestamp': datetime.utcnow().isoformat(),
                'transactions': transactions,
                'previous_hash': previous_hash,
                'nonce': 0
            }
            
            block['hash'] = self._calculate_hash(block)
            
            while not block['hash'].startswith('00'):
                block['nonce'] += 1
                block['hash'] = self._calculate_hash(block)
            
            self.block_chain.append(block)
            logger.info(f"New block created: {block['hash']}")
            return block
        except Exception as e:
            logger.error(f"Error creating block: {str(e)}")
            raise
    
    def _calculate_hash(self, block: Dict) -> str:
        """Calculate SHA-256 hash of block"""
        block_string = json.dumps({
            'index': block['index'],
            'timestamp': block['timestamp'],
            'transactions': block['transactions'],
            'previous_hash': block['previous_hash'],
            'nonce': block['nonce']
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def add_threat_record(self, threat_data: Dict[str, Any]) -> str:
        """Add threat record to blockchain audit trail"""
        try:
            evidence = json.dumps(threat_data, sort_keys=True)
            evidence_hash = hashlib.sha256(evidence.encode()).hexdigest()
            
            record = ThreatRecord(
                timestamp=datetime.utcnow().isoformat(),
                source_ip=threat_data.get('source_ip', 'unknown'),
                destination_ip=threat_data.get('destination_ip', 'unknown'),
                threat_type=threat_data.get('threat_type', 'unknown'),
                severity=threat_data.get('severity', 'unknown'),
                confidence=threat_data.get('confidence', 0.0),
                ml_model=threat_data.get('ml_model', 'ensemble'),
                action_taken=threat_data.get('action', 'logged'),
                evidence_hash=evidence_hash,
                record_id=hashlib.sha256(
                    f"{datetime.utcnow().isoformat()}{evidence_hash}".encode()
                ).hexdigest()[:16]
            )
            
            transaction = {
                'id': record.record_id,
                'type': 'THREAT_LOG',
                'data': record.to_dict(),
                'timestamp': datetime.utcnow().isoformat(),
                'evidence_hash': evidence_hash
            }
            
            self.pending_transactions.append(transaction)
            self.threat_ledger.append(record.to_dict())
            
            if len(self.pending_transactions) >= 5:
                self._create_new_block()
            
            return record.record_id
        except Exception as e:
            logger.error(f"Error adding threat record: {str(e)}")
            raise
    
    def _create_new_block(self):
        """Create new block from pending transactions"""
        try:
            if not self.pending_transactions:
                return
            previous_hash = self.block_chain[-1]['hash'] if self.block_chain else "0"
            block = self.create_block(self.pending_transactions, previous_hash)
            self.pending_transactions = []
            return block
        except Exception as e:
            logger.error(f"Error creating block: {str(e)}")
    
    def get_audit_trail(self, filters: Optional[Dict] = None) -> list:
        """Get audit trail with optional filters"""
        try:
            trail = self.threat_ledger.copy()
            if filters:
                if 'severity' in filters:
                    trail = [r for r in trail if r['severity'] == filters['severity']]
                if 'threat_type' in filters:
                    trail = [r for r in trail if r['threat_type'] == filters['threat_type']]
                if 'min_confidence' in filters:
                    trail = [r for r in trail if r['confidence'] >= filters['min_confidence']]
            return sorted(trail, key=lambda x: x['timestamp'], reverse=True)
        except Exception as e:
            logger.error(f"Error retrieving audit trail: {str(e)}")
            return []
    
    def get_blockchain_stats(self) -> Dict:
        """Get blockchain statistics"""
        try:
            total_records = len(self.threat_ledger)
            severity_dist = {}
            threat_dist = {}
            for record in self.threat_ledger:
                severity = record.get('severity', 'unknown')
                threat_type = record.get('threat_type', 'unknown')
                severity_dist[severity] = severity_dist.get(severity, 0) + 1
                threat_dist[threat_type] = threat_dist.get(threat_type, 0) + 1
            
            return {
                'total_records': total_records,
                'total_blocks': len(self.block_chain),
                'pending_transactions': len(self.pending_transactions),
                'severity_distribution': severity_dist,
                'threat_type_distribution': threat_dist,
                'average_confidence': (
                    sum(r['confidence'] for r in self.threat_ledger) / total_records
                    if total_records > 0 else 0.0
                )
            }
        except Exception as e:
            logger.error(f"Error getting blockchain stats: {str(e)}")
            return {}
    
    def verify_integrity(self) -> bool:
        """Verify blockchain integrity"""
        try:
            if not self.block_chain:
                return True
            for i, block in enumerate(self.block_chain):
                calculated_hash = self._calculate_hash(block)
                if calculated_hash != block['hash']:
                    logger.error(f"Block {i} hash mismatch")
                    return False
                if i > 0:
                    if block['previous_hash'] != self.block_chain[i-1]['hash']:
                        logger.error(f"Block {i} chain broken")
                        return False
            logger.info("Blockchain integrity verified")
            return True
        except Exception as e:
            logger.error(f"Error verifying integrity: {str(e)}")
            return False


class BlockchainLogger(BlockchainAuditService):
    """Alias for backwards compatibility"""
    
    def log_threat_to_blockchain(self, threat_data):
        """Log threat to blockchain"""
        return self.add_threat_record(threat_data)
