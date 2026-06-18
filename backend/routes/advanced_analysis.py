"""
Advanced Routes for ML Models, LLM Analysis, and Real-time Threat Detection
"""

from flask import Blueprint, request, jsonify
from flask_socketio import emit
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import json
from collections import deque
import threading

# Import ML and LLM services
from services.local_llm_service import LocalLLMService, ThreatIntelligence
from ml_models.advanced_models import AdvancedMLPipeline
from services.xss_tracker import xss_tracker
from services.firewall_tracker import firewall_tracker

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


# ============= ML MODEL ENDPOINTS =============

@advanced_bp.route('/models/status', methods=['GET'])
def get_models_status():
    """Get status of all ML models"""
    try:
        models_status = {}
        for model_name in ml_pipeline.models.keys():
            models_status[model_name] = 'loaded'
        
        return jsonify({
            'status': 'success',
            'models_loaded': models_status,
            'total_models': len(models_status),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting models status: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/models/train', methods=['POST'])
def train_models():
    """Train all ML models with uploaded data"""
    try:
        data = request.get_json()
        csv_path = data.get('csv_path')
        
        if not csv_path:
            return jsonify({'error': 'csv_path required'}), 400
        
        # Load data
        df = ml_pipeline.load_and_preprocess_data(csv_path)
        
        # Prepare data
        X_train, X_test, y_train, y_test = ml_pipeline.prepare_data_for_models(df)
        
        # Train models
        results, X_test_scaled, y_test = ml_pipeline.train_all_models(
            X_train, X_test, y_train, y_test
        )
        
        # Save models
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
def predict_threat():
    """Get threat predictions from all models AND LLM analysis"""
    try:
        data = request.get_json()
        features = data.get('features')
        model_name = data.get('model', 'ensemble')
        
        if not features:
            return jsonify({'error': 'features required'}), 400
        
        # Convert to DataFrame for proper feature handling
        feature_df = pd.DataFrame([features])
        
        # Make predictions from all available models
        predictions = ml_pipeline.predict_with_all_models(feature_df.values)
        
        # Get explanation from Random Forest
        explanation = ml_pipeline.explain_prediction(features)
        
        # Combine all predictions - if ANY model is >0.7, consider it a threat
        # especially important for Isolation Forest detecting unknown attacks
        threat_confidence = max(predictions.values()) if predictions else 0.5
        
        # Determine threat level
        if threat_confidence > 0.8:
            threat_level = 'CRITICAL'
        elif threat_confidence > 0.6:
            threat_level = 'HIGH'
        elif threat_confidence > 0.4:
            threat_level = 'MEDIUM'
        else:
            threat_level = 'LOW'
        
        # Get LLM analysis if available
        llm_analysis = None
        try:
            if llm_service and llm_service.is_running:
                llm_input = {
                    'threat_data': features,
                    'ml_predictions': predictions,
                    'threat_level': threat_level
                }
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
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Add to threat buffer for graphing
        threat_buffer.append({
            'timestamp': datetime.utcnow().isoformat(),
            'confidence': float(threat_confidence),
            'threat_level': threat_level,
            'predictions': predictions
        })
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error making prediction: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/models/batch-predict', methods=['POST'])
def batch_predict():
    """Predict for multiple records"""
    try:
        data = request.get_json()
        records = data.get('records', [])
        
        if not records:
            return jsonify({'error': 'records required'}), 400
        
        results = []
        feature_df = pd.DataFrame(records)
        
        predictions = ml_pipeline.predict_batch(feature_df.values, 'ensemble')
        
        for i, (record, confidence) in enumerate(zip(records, predictions)):
            threat_level = 'CRITICAL' if confidence > 0.8 else 'HIGH' if confidence > 0.6 else 'MEDIUM' if confidence > 0.4 else 'LOW'
            results.append({
                'record_id': i,
                'confidence': float(confidence),
                'threat_level': threat_level
            })
        
        return jsonify({
            'status': 'success',
            'total_records': len(records),
            'predictions': results
        }), 200
    except Exception as e:
        logger.error(f"Error in batch predict: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============= LLM ANALYSIS ENDPOINTS =============

@advanced_bp.route('/llm/status', methods=['GET'])
def get_llm_status():
    """Get LLM service status"""
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
def start_llm():
    """Start Ollama LLM service"""
    try:
        success = llm_service.start_ollama()
        return jsonify({
            'status': 'success' if success else 'failed',
            'message': 'Ollama started' if success else 'Failed to start Ollama',
            'running': llm_service.is_running
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/llm/switch-model', methods=['POST'])
def switch_llm_model():
    """Switch to different LLM model"""
    try:
        data = request.get_json()
        model_name = data.get('model')
        
        if not model_name:
            return jsonify({'error': 'model name required'}), 400
        
        success = llm_service.switch_model(model_name)
        return jsonify({
            'status': 'success' if success else 'failed',
            'current_model': llm_service.model
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/llm/analyze-threat', methods=['POST'])
def analyze_threat_with_llm():
    """Analyze threat using LLM and ML models"""
    try:
        data = request.get_json()
        threat_data = data.get('threat_data', {})
        ml_prediction = data.get('ml_prediction', {})
        
        # Get combined analysis
        analysis = threat_intelligence.analyze_with_reasoning(ml_prediction, threat_data)
        
        return jsonify({
            'status': 'success',
            'analysis': analysis
        }), 200
    except Exception as e:
        logger.error(f"Error analyzing threat: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/llm/recommendations', methods=['POST'])
def get_threat_recommendations():
    """Get AI-powered threat mitigation recommendations"""
    try:
        data = request.get_json()
        threat_type = data.get('threat_type', 'Unknown')
        severity = data.get('severity', 'MEDIUM')
        
        recommendations = llm_service.get_recommendations(threat_type, severity)
        
        return jsonify({
            'status': 'success',
            'threat_type': threat_type,
            'severity': severity,
            'recommendations': recommendations
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= REAL-TIME GRAPH DATA ENDPOINTS =============

@advanced_bp.route('/graphs/threat-timeline', methods=['GET'])
def get_threat_timeline():
    """Get threat data for timeline graph"""
    try:
        timeline_data = list(threat_buffer)
        
        # Group by threat level
        threat_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
        confidence_values = []
        
        for item in timeline_data:
            threat_counts[item['threat_level']] += 1
            confidence_values.append(item['confidence'])
        
        return jsonify({
            'status': 'success',
            'total_threats': len(timeline_data),
            'threat_breakdown': threat_counts,
            'timeline': timeline_data,
            'average_confidence': float(np.mean(confidence_values)) if confidence_values else 0.0,
            'max_confidence': float(np.max(confidence_values)) if confidence_values else 0.0,
            'min_confidence': float(np.min(confidence_values)) if confidence_values else 0.0
        }), 200
    except Exception as e:
        logger.error(f"Error getting threat timeline: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/graphs/model-comparison', methods=['GET'])
def get_model_comparison():
    """Get model performance comparison data"""
    try:
        # Collect recent predictions for comparison
        model_scores = {model: [] for model in ml_pipeline.models.keys()}
        
        for item in threat_buffer:
            for model, pred in item.get('predictions', {}).items():
                if model in model_scores and pred is not None:
                    model_scores[model].append(pred)
        
        comparison = {}
        for model, scores in model_scores.items():
            if scores:
                comparison[model] = {
                    'average': float(np.mean(scores)),
                    'std': float(np.std(scores)),
                    'count': len(scores)
                }
        
        return jsonify({
            'status': 'success',
            'model_comparison': comparison,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/graphs/threat-distribution', methods=['GET'])
def get_threat_distribution():
    """Get threat level distribution for pie chart"""
    try:
        threat_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
        
        for item in threat_buffer:
            threat_counts[item['threat_level']] += 1
        
        total = sum(threat_counts.values())
        percentages = {k: (v/total*100) if total > 0 else 0 for k, v in threat_counts.items()}
        
        return jsonify({
            'status': 'success',
            'distribution': threat_counts,
            'percentages': percentages,
            'total_records': total
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/graphs/model-metrics', methods=['GET'])
def get_model_metrics():
    """Get detailed model performance metrics"""
    try:
        metrics = {
            'training_history': ml_pipeline.training_history,
            'feature_count': len(ml_pipeline.feature_cols) if ml_pipeline.feature_cols else 0,
            'features': ml_pipeline.feature_cols or []
        }
        
        return jsonify({
            'status': 'success',
            'metrics': metrics
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============= XSS ATTACK TRACKING ENDPOINTS =============

@advanced_bp.route('/xss/log', methods=['POST'])
def log_xss_attack():
    """Log a blocked XSS attack"""
    try:
        data = request.get_json()
        payload = data.get('payload', '')
        source = data.get('source', 'web')
        
        attack = xss_tracker.log_attack(payload, source)
        
        # Also add to threat buffer for graphs
        threat_buffer.append({
            'timestamp': attack['timestamp'],
            'confidence': 0.95,
            'threat_level': 'CRITICAL',
            'attack_type': 'XSS',
            'predictions': {'ensemble': 0.95}
        })
        
        return jsonify({
            'status': 'success',
            'attack': attack
        }), 200
    except Exception as e:
        logger.error(f"Error logging XSS attack: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/xss/stats', methods=['GET'])
def get_xss_stats():
    """Get XSS attack statistics"""
    try:
        stats = xss_tracker.get_stats()
        return jsonify({
            'status': 'success',
            'stats': stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting XSS stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/xss/timeline', methods=['GET'])
def get_xss_timeline():
    """Get XSS attack timeline for graphs"""
    try:
        timeline = xss_tracker.get_timeline_data()
        return jsonify({
            'status': 'success',
            'timeline': timeline
        }), 200
    except Exception as e:
        logger.error(f"Error getting XSS timeline: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ================= FIREWALL ENDPOINTS =================

@advanced_bp.route('/firewall/log-attack', methods=['POST'])
def log_firewall_attack():
    """Log a firewall blocked attack"""
    try:
        data = request.get_json()
        attack_type = data.get('attack_type', 'unknown')
        payload = data.get('payload', '')
        confidence = data.get('confidence', 0.95)
        
        # Get client IP
        source_ip = request.remote_addr or '127.0.0.1'
        
        attack = firewall_tracker.log_packet(
            packet_type=attack_type,
            source_ip=source_ip,
            payload=payload,
            action="BLOCKED",
            confidence=confidence
        )
        
        return jsonify({
            'status': 'success',
            'attack': attack
        }), 200
    except Exception as e:
        logger.error(f"Error logging firewall attack: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/firewall/stats', methods=['GET'])
def get_firewall_stats():
    """Get comprehensive firewall statistics"""
    try:
        stats = firewall_tracker.get_stats()
        return jsonify({
            'status': 'success',
            **stats
        }), 200
    except Exception as e:
        logger.error(f"Error getting firewall stats: {str(e)}")
        return jsonify({'error': str(e)}), 500


@advanced_bp.route('/firewall/recent', methods=['GET'])
def get_recent_attacks():
    """Get recent attacks"""
    try:
        limit = int(request.args.get('limit', 20))
        attacks = firewall_tracker.get_recent_attacks(limit)
        return jsonify({
            'status': 'success',
            'attacks': attacks
        }), 200
    except Exception as e:
        logger.error(f"Error getting recent attacks: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============= REAL-TIME WEBSOCKET UPDATES =============

def register_socketio_handlers(socketio):
    """Register WebSocket handlers for real-time updates"""
    
    @socketio.on('request_live_predictions')
    def send_live_predictions(data):
        """Stream live threat predictions"""
        try:
            # Simulate streaming predictions
            for item in list(threat_buffer)[-10:]:  # Send last 10
                emit('prediction_update', {
                    'timestamp': item['timestamp'],
                    'confidence': item['confidence'],
                    'threat_level': item['threat_level'],
                    'predictions': item['predictions']
                })
        except Exception as e:
            logger.error(f"Error sending live predictions: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('request_graph_update')
    def send_graph_update():
        """Send real-time graph data updates"""
        try:
            timeline_data = list(threat_buffer)[-50:]  # Last 50
            emit('graph_update', {
                'timeline': timeline_data,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending graph update: {str(e)}")
            emit('error', {'message': str(e)})
    
    @socketio.on('request_model_comparison')
    def send_model_comparison():
        """Send model comparison data"""
        try:
            model_scores = {model: [] for model in ml_pipeline.models.keys()}
            
            for item in list(threat_buffer)[-50:]:
                for model, pred in item.get('predictions', {}).items():
                    if model in model_scores and pred is not None:
                        model_scores[model].append(pred)
            
            comparison = {}
            for model, scores in model_scores.items():
                if scores:
                    comparison[model] = {
                        'average': float(np.mean(scores)),
                        'count': len(scores)
                    }
            
            emit('model_comparison', {
                'comparison': comparison,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending model comparison: {str(e)}")
            emit('error', {'message': str(e)})


if __name__ == "__main__":
    logger.info("Advanced routes module loaded")
