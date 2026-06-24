"""
Advanced Routes for ML Models, LLM Analysis, and Real-time Threat Detection
Protected with JWT Authentication and Path Validation
"""

from flask import Blueprint, request, jsonify
from flask_socketio import emit
import logging
from datetime import datetime, timedelta, timezone
# Optional heavy libs — use lightweight fallbacks if not installed
try:
    import numpy as np
    import pandas as pd
    HAS_NUMPY = True
except Exception:
    np = None
    pd = None
    HAS_NUMPY = False
import json
from collections import deque
import threading
import os

# Import ML and LLM services
from services.local_llm_service import LocalLLMService, ThreatIntelligence
from ml_models.advanced_models import AdvancedMLPipeline
from services.xss_tracker import xss_tracker
from services.firewall_tracker import firewall_tracker
from utils.security import token_required

logger = logging.getLogger(__name__)

# Create blueprint
advanced_bp = Blueprint('advanced', __name__)

# Global services
llm_service = LocalLLMService()
ml_pipeline = AdvancedMLPipeline()
threat_intelligence = ThreatIntelligence(llm_service)

# Real-time data buffer for graphs
threat_buffer = deque(maxlen=1000)
metrics_buffer = deque(maxlen=100)

ALLOWED_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'traffic_data'))

def is_safe_path(path):
    """Validate path to prevent traversal/LFI"""
    if not path:
        return False
    base_dir = os.path.abspath(ALLOWED_DATA_DIR)
    if not os.path.isabs(path):
        target_path = os.path.abspath(os.path.join(base_dir, path))
    else:
        target_path = os.path.abspath(path)
    return os.path.commonpath([base_dir, target_path]) == base_dir and os.path.exists(target_path)

# ============= ML MODEL ENDPOINTS =============

@advanced_bp.route('/models/status', methods=['GET'])
@token_required
def get_models_status():
    """Get status of all ML models"""
    try:
        models_status = {name: 'loaded' for name in ml_pipeline.models.keys()}
        return jsonify({
            'status': 'success',
            'models_loaded': models_status,
            'total_models': len(models_status),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting models status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/models/train', methods=['POST'])
@token_required
def train_models():
    """Train all ML models with uploaded data (Protected against Path Traversal)"""
    try:
        data = request.get_json()
        csv_path = data.get('csv_path')
        
        if not csv_path:
            return jsonify({'error': 'csv_path required'}), 400
            
        if not is_safe_path(csv_path):
            logger.warning(f"Blocked unauthorized path access attempt: {csv_path}")
            return jsonify({'error': 'Unauthorized path access'}), 403
        
        abs_csv_path = os.path.abspath(os.path.join(ALLOWED_DATA_DIR, os.path.basename(csv_path)))
        df = ml_pipeline.load_and_preprocess_data(abs_csv_path)
        X_train, X_test, y_train, y_test = ml_pipeline.prepare_data_for_models(df)
        results, _, _ = ml_pipeline.train_all_models(X_train, X_test, y_train, y_test)
        ml_pipeline.save_models()
        
        return jsonify({
            'status': 'success',
            'message': 'All models trained successfully',
            'results': results,
            'data_records': len(df),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }), 200
    except Exception as e:
        logger.error(f"Error training models: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/models/predict', methods=['POST'])
@token_required
def predict_threat():
    """Get threat predictions from all models"""
    try:
        data = request.get_json()
        features = data.get('features')
        if not features:
            return jsonify({'error': 'features required'}), 400
        
        feature_df = pd.DataFrame([features])
        predictions = ml_pipeline.predict_with_all_models(feature_df.values)
        explanation = ml_pipeline.explain_prediction(features)
        
        threat_confidence = max(predictions.values()) if predictions else 0.5
        threat_level = 'CRITICAL' if threat_confidence > 0.8 else 'HIGH' if threat_confidence > 0.6 else 'MEDIUM' if threat_confidence > 0.4 else 'LOW'
        
        llm_analysis = None
        try:
            if llm_service and llm_service.is_running:
                llm_analysis = threat_intelligence.analyze_with_reasoning(predictions, features)
        except Exception as llm_err:
            logger.warning(f"LLM analysis skipped: {str(llm_err)}")
        
        result = {
            'status': 'success',
            'predictions': predictions,
            'max_confidence': float(threat_confidence),
            'threat_level': threat_level,
            'explanation': explanation,
            'llm_analysis': llm_analysis,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        threat_buffer.append(result)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/models/batch-predict', methods=['POST'])
@token_required
def batch_predict():
    """Predict for multiple records"""
    try:
        data = request.get_json()
        records = data.get('records', [])
        if not records:
            return jsonify({'error': 'records required'}), 400
        
        feature_df = pd.DataFrame(records)
        predictions = ml_pipeline.predict_batch(feature_df.values, 'ensemble')
        
        results = []
        for i, (record, confidence) in enumerate(zip(records, predictions)):
            threat_level = 'CRITICAL' if confidence > 0.8 else 'HIGH' if confidence > 0.6 else 'MEDIUM' if confidence > 0.4 else 'LOW'
            results.append({'record_id': i, 'confidence': float(confidence), 'threat_level': threat_level})
        
        return jsonify({'status': 'success', 'total_records': len(records), 'predictions': results}), 200
    except Exception as e:
        logger.error(f"Error in batch predict: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============= LLM ANALYSIS ENDPOINTS =============

@advanced_bp.route('/llm/status', methods=['GET'])
@token_required
def get_llm_status():
    try:
        model_info = llm_service.get_model_info()
        return jsonify({
            'status': 'success',
            'llm_running': llm_service.is_running,
            'current_model': llm_service.model,
            'model_info': model_info,
            'available_models': llm_service.list_available_models()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/llm/start', methods=['POST'])
@token_required
def start_llm():
    try:
        data = request.get_json() or {}
        model_path = data.get('model_path')
        # If service is configured to use llama_cpp, load local model path
        if getattr(llm_service, 'engine', None) == 'llama_cpp':
            if not model_path:
                return jsonify({'error': 'model_path required for local llama_cpp engine'}), 400
            success = llm_service.load_local_model(model_path)
        else:
            success = llm_service.start_ollama()
        return jsonify({'status': 'success' if success else 'failed', 'running': llm_service.is_running}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/llm/switch-model', methods=['POST'])
@token_required
def switch_llm_model():
    try:
        data = request.get_json()
        model_name = data.get('model')
        if not model_name:
            return jsonify({'error': 'model name required'}), 400
        success = llm_service.switch_model(model_name)
        return jsonify({'status': 'success' if success else 'failed', 'current_model': llm_service.model}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/llm/analyze-threat', methods=['POST'])
@token_required
def analyze_threat_with_llm():
    try:
        data = request.get_json()
        threat_data = data.get('threat_data', {})
        ml_prediction = data.get('ml_prediction', {})
        analysis = threat_intelligence.analyze_with_reasoning(ml_prediction, threat_data)
        return jsonify({'status': 'success', 'analysis': analysis}), 200
    except Exception as e:
        logger.error(f"Error analyzing threat: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/llm/recommendations', methods=['POST'])
@token_required
def get_threat_recommendations():
    try:
        data = request.get_json()
        threat_type = data.get('threat_type', 'Unknown')
        severity = data.get('severity', 'MEDIUM')
        recommendations = llm_service.get_recommendations(threat_type, severity)
        return jsonify({'status': 'success', 'recommendations': recommendations}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= GRAPH DATA ENDPOINTS =============

@advanced_bp.route('/graphs/threat-timeline', methods=['GET'])
@token_required
def get_threat_timeline():
    try:
        timeline_data = list(threat_buffer)
        threat_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
        confidence_values = [item['max_confidence'] for item in timeline_data if 'max_confidence' in item]
        for item in timeline_data:
            if 'threat_level' in item:
                threat_counts[item['threat_level']] += 1
        # use numpy mean if available, else fallback
        if HAS_NUMPY and confidence_values:
            avg_conf = float(np.mean(confidence_values))
        else:
            avg_conf = float(sum(confidence_values) / len(confidence_values)) if confidence_values else 0.0
        return jsonify({
            'status': 'success',
            'total_threats': len(timeline_data),
            'threat_breakdown': threat_counts,
            'timeline': timeline_data,
            'average_confidence': avg_conf
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/graphs/model-comparison', methods=['GET'])
@token_required
def get_model_comparison():
    try:
        model_scores = {model: [] for model in ml_pipeline.models.keys()}
        for item in threat_buffer:
            for model, pred in item.get('predictions', {}).items():
                if model in model_scores and pred is not None:
                    model_scores[model].append(pred)
        comparison = {model: {'average': float(np.mean(scores)), 'count': len(scores)} for model, scores in model_scores.items() if scores}
        return jsonify({'status': 'success', 'model_comparison': comparison}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= XSS TRACKING =============

@advanced_bp.route('/xss/log', methods=['POST'])
@token_required
def log_xss_attack():
    try:
        data = request.get_json()
        payload = data.get('payload', '')
        source = data.get('source', 'web')
        attack = xss_tracker.log_attack(payload, source)
        return jsonify({'status': 'success', 'attack': attack}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/xss/stats', methods=['GET'])
@token_required
def get_xss_stats():
    try:
        return jsonify({'status': 'success', 'stats': xss_tracker.get_stats()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= FIREWALL STATS =============

@advanced_bp.route('/firewall/stats', methods=['GET'])
@token_required
def get_firewall_stats():
    try:
        return jsonify({'status': 'success', **firewall_tracker.get_stats()}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/firewall/recent', methods=['GET'])
@token_required
def get_recent_attacks():
    try:
        limit = int(request.args.get('limit', 20))
        return jsonify({'status': 'success', 'attacks': firewall_tracker.get_recent_attacks(limit)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/firewall/log-attack', methods=['POST'])
@token_required
def log_attack_manually():
    try:
        data = request.get_json()
        attack_type = data.get('attack_type', 'unknown')
        payload = data.get('payload', '')
        confidence = float(data.get('confidence', 0.9))
        
        # Get real client IP
        from app import _get_client_ip
        source_ip = _get_client_ip()
        
        log_entry = firewall_tracker.log_attack(
            attack_type=attack_type,
            source_ip=source_ip,
            payload=payload,
            blocked=True,
            confidence=confidence
        )
        
        return jsonify({'status': 'success', 'entry': log_entry}), 200
    except Exception as e:
        logger.error(f"Error logging attack: {str(e)}")
        return jsonify({'error': str(e)}), 500

def register_socketio_handlers(socketio):
    @socketio.on('request_live_predictions')
    def send_live_predictions(data):
        try:
            for item in list(threat_buffer)[-10:]:
                emit('prediction_update', item)
        except Exception as e:
            emit('error', {'message': str(e)})

if __name__ == "__main__":
    logger.info("Advanced routes module loaded")
