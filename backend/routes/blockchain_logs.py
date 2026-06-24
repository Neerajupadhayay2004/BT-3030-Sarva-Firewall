from flask import Blueprint, request, jsonify
import logging
from services.blockchain_service import BlockchainLogger
from utils.security import token_required

logger = logging.getLogger(__name__)
blockchain_bp = Blueprint('blockchain', __name__)
blockchain = BlockchainLogger()

@blockchain_bp.route('/log/threat', methods=['POST'])
@token_required
def log_threat():
    """Log threat to blockchain"""
    try:
        data = request.get_json()
        
        if not data.get('id'):
            return jsonify({'error': 'Threat ID required'}), 400
        
        result = blockchain.log_threat_to_blockchain(data)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Blockchain logging error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/verify/<threat_id>', methods=['GET'])
@token_required
def verify_threat(threat_id):
    """Verify threat log on blockchain"""
    try:
        result = blockchain.verify_threat_log(threat_id)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Blockchain verification error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/history', methods=['GET'])
@token_required
def get_threat_history():
    """Get threat history from blockchain"""
    try:
        limit = request.args.get('limit', 100, type=int)
        result = blockchain.get_threat_history(limit)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error fetching threat history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/network/status', methods=['GET'])
@token_required
def network_status():
    """Get blockchain network status"""
    try:
        return jsonify({
            'network': 'Polygon Amoy Testnet',
            'connected': blockchain.w3.is_connected(),
            'contract_address': blockchain.contract_address,
            'provider': blockchain.provider_url,
            'latest_block': 'N/A'
        }), 200
    except Exception as e:
        logger.error(f"Network status error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@blockchain_bp.route('/transaction/<tx_hash>', methods=['GET'])
@token_required
def get_transaction(tx_hash):
    """Get transaction details"""
    try:
        # Simulate transaction lookup
        return jsonify({
            'transaction_hash': tx_hash,
            'status': 'confirmed',
            'block_number': 12345,
            'from_address': '0x...',
            'to_address': blockchain.contract_address,
            'timestamp': 'N/A'
        }), 200
    except Exception as e:
        logger.error(f"Transaction lookup error: {str(e)}")
        return jsonify({'error': str(e)}), 500
