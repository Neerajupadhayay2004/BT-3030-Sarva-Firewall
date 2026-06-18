"""
Advanced ML Models for Network Traffic Threat Detection
- Random Forest for feature importance
- Gradient Boosting for high accuracy
- Isolation Forest for unknown attacks
- Ensemble for best predictions
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score
import joblib
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class AdvancedMLPipeline:
    """Complete ML pipeline with multiple models"""
    
    def __init__(self, data_path=None):
        self.models = {}
        self.scalers = {}
        self.feature_cols = None
        self.model_dir = Path(__file__).parent / "trained_models"
        self.model_dir.mkdir(exist_ok=True)
        self.data_path = data_path
        
    def load_and_preprocess_data(self, csv_path):
        """Load and preprocess network logs"""
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded {len(df)} records from {csv_path}")
            
            df = self._engineer_features(df)
            df['is_threat'] = self._classify_threats(df)
            
            return df
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def _engineer_features(self, df):
        """Create advanced features from network logs"""
        df_feat = df.copy()
        
        df_feat['src_port_category'] = df_feat['Source Port'].apply(self._categorize_port)
        df_feat['dst_port_category'] = df_feat['Destination Port'].apply(self._categorize_port)
        df_feat['port_diff'] = abs(df_feat['Source Port'] - df_feat['Destination Port'])
        
        df_feat['byte_ratio'] = (df_feat['Bytes Sent'] + 1) / (df_feat['Bytes Received'] + 1)
        df_feat['packet_ratio'] = (df_feat['pkts_sent'] + 1) / (df_feat['pkts_received'] + 1)
        df_feat['bytes_per_packet'] = df_feat['Bytes'] / (df_feat['Packets'] + 1)
        
        df_feat['time_anomaly'] = (df_feat['Elapsed Time (sec)'] > df_feat['Elapsed Time (sec)'].quantile(0.95)).astype(int)
        df_feat['connection_intensity'] = df_feat['Packets'] / (df_feat['Elapsed Time (sec)'] + 1)
        
        df_feat['high_packet_count'] = (df_feat['Packets'] > df_feat['Packets'].quantile(0.9)).astype(int)
        df_feat['high_byte_transfer'] = (df_feat['Bytes'] > df_feat['Bytes'].quantile(0.9)).astype(int)
        df_feat['asymmetric_traffic'] = (abs(df_feat['Bytes Sent'] - df_feat['Bytes Received']) > df_feat['Bytes'] * 0.5).astype(int)
        
        return df_feat
    
    def _categorize_port(self, port):
        """Categorize ports by service type"""
        privileged = port < 1024
        web = port in [80, 443]
        dns = port in [53, 5353]
        rdp = port in [3389, 3390]
        
        if privileged:
            return 1
        elif web:
            return 2
        elif dns:
            return 3
        elif rdp:
            return 4
        else:
            return 0
    
    def _classify_threats(self, df):
        """Intelligent threat classification"""
        threats = np.zeros(len(df))
        threats += (df['Packets'] > df['Packets'].quantile(0.95)).astype(int) * 0.3
        threats += (df['Bytes'] > df['Bytes'].quantile(0.95)).astype(int) * 0.3
        threats += (df['Elapsed Time (sec)'] > 300).astype(int) * 0.2
        threats += (abs(df['Bytes Sent'] - df['Bytes Received']) > df['Bytes'] * 0.7).astype(int) * 0.2
        return (threats >= 0.5).astype(int)
    
    def prepare_data_for_models(self, df):
        """Prepare data for ML models"""
        feature_cols = ['Source Port', 'Destination Port', 'NAT Source Port', 'NAT Destination Port',
                       'Bytes', 'Bytes Sent', 'Bytes Received', 'Packets', 'Elapsed Time (sec)',
                       'pkts_sent', 'pkts_received', 'src_port_category', 'dst_port_category',
                       'port_diff', 'byte_ratio', 'packet_ratio', 'bytes_per_packet',
                       'time_anomaly', 'connection_intensity', 'high_packet_count',
                       'high_byte_transfer', 'asymmetric_traffic']
        
        self.feature_cols = feature_cols
        X = df[feature_cols].fillna(0)
        y = df['is_threat'].values
        return train_test_split(X, y, test_size=0.2, random_state=42)
    
    def build_random_forest_model(self):
        """Build Random Forest model with enhanced parameters"""
        return RandomForestClassifier(
            n_estimators=300,
            max_depth=20,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
    
    def build_gradient_boosting_model(self):
        """Build Gradient Boosting model"""
        return GradientBoostingClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=7,
            min_samples_split=5,
            min_samples_leaf=2,
            subsample=0.8,
            random_state=42
        )
    
    def train_all_models(self, X_train, X_test, y_train, y_test):
        """Train all models"""
        logger.info("Training advanced ML models...")
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        self.scalers['standard'] = scaler
        
        results = {}
        estimators = []
        
        logger.info("Training Random Forest model...")
        rf_model = self.build_random_forest_model()
        rf_model.fit(X_train_scaled, y_train)
        self.models['random_forest'] = rf_model
        estimators.append(('rf', rf_model))
        
        y_pred_rf = rf_model.predict(X_test_scaled)
        results['random_forest'] = {
            'accuracy': float(rf_model.score(X_test_scaled, y_test)),
            'auc': float(roc_auc_score(y_test, rf_model.predict_proba(X_test_scaled)[:, 1])),
            'f1': float(f1_score(y_test, y_pred_rf)),
            'feature_importance': dict(zip(self.feature_cols, rf_model.feature_importances_.tolist()))
        }
        logger.info(f"Random Forest Results: {results['random_forest']}")
        
        logger.info("Training Gradient Boosting model...")
        gb_model = self.build_gradient_boosting_model()
        gb_model.fit(X_train_scaled, y_train)
        self.models['gradient_boosting'] = gb_model
        estimators.append(('gb', gb_model))
        
        y_pred_gb = gb_model.predict(X_test_scaled)
        results['gradient_boosting'] = {
            'accuracy': float(gb_model.score(X_test_scaled, y_test)),
            'auc': float(roc_auc_score(y_test, gb_model.predict_proba(X_test_scaled)[:, 1])),
            'f1': float(f1_score(y_test, y_pred_gb))
        }
        logger.info(f"Gradient Boosting Results: {results['gradient_boosting']}")
        
        logger.info("Training Isolation Forest for unknown attack detection...")
        iso_forest = IsolationForest(
            n_estimators=200,
            contamination=0.05,
            random_state=42,
            n_jobs=-1
        )
        iso_forest.fit(X_train_scaled)
        self.models['isolation_forest'] = iso_forest
        
        y_pred_iso = iso_forest.predict(X_test_scaled)
        y_pred_iso = (y_pred_iso == -1).astype(int)
        results['isolation_forest'] = {
            'anomaly_detection_rate': float(np.mean(y_pred_iso)),
            'description': 'Isolation Forest for unknown threats'
        }
        logger.info(f"Isolation Forest Results: {results['isolation_forest']}")
        
        logger.info("Creating Ensemble model...")
        ensemble = VotingClassifier(estimators=estimators, voting='soft')
        ensemble.fit(X_train_scaled, y_train)
        self.models['ensemble'] = ensemble
        
        y_pred_ensemble = ensemble.predict(X_test_scaled)
        results['ensemble'] = {
            'accuracy': float(ensemble.score(X_test_scaled, y_test)),
            'auc': float(roc_auc_score(y_test, ensemble.predict_proba(X_test_scaled)[:, 1])),
            'f1': float(f1_score(y_test, y_pred_ensemble))
        }
        logger.info(f"Ensemble Results: {results['ensemble']}")
        
        return results, X_test_scaled, y_test
    
    def predict_batch(self, X, model_name='ensemble'):
        """Make predictions on batch data"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")
        
        scaler = self.scalers.get('standard')
        X_scaled = scaler.transform(X) if scaler else X
        
        if model_name == 'isolation_forest':
            model = self.models[model_name]
            preds = model.predict(X_scaled)
            return np.where(preds == -1, 0.95, 0.05)
        
        model = self.models[model_name]
        return model.predict_proba(X_scaled)[:, 1]
    
    def predict_with_all_models(self, X):
        """Predict using all available models for comprehensive analysis"""
        predictions = {}
        scaler = self.scalers.get('standard')
        X_scaled = scaler.transform(X) if scaler else X
        
        for model_name, model in self.models.items():
            try:
                if model_name == 'isolation_forest':
                    preds = model.predict(X_scaled)
                    predictions[model_name] = float(np.where(preds == -1, 0.95, 0.05).mean())
                else:
                    predictions[model_name] = float(model.predict_proba(X_scaled)[:, 1].mean())
            except Exception as e:
                logger.warning(f"Error predicting with {model_name}: {e}")
        
        return predictions
    
    def explain_prediction(self, sample, model_name='random_forest'):
        """Explain individual predictions"""
        if model_name == 'random_forest':
            model = self.models.get(model_name)
            if model and hasattr(model, 'feature_importances_'):
                importance = dict(zip(self.feature_cols, model.feature_importances_))
                return sorted(importance.items(), key=lambda x: x[1], reverse=True)[:10]
        return None
    
    def save_models(self):
        """Save all trained models"""
        for name, model in self.models.items():
            joblib.dump(model, self.model_dir / f"{name}_model.pkl")
        
        joblib.dump(self.scalers.get('standard'), self.model_dir / "scaler.pkl")
        
        with open(self.model_dir / "feature_cols.json", 'w') as f:
            json.dump(self.feature_cols, f)
        
        logger.info(f"Models saved to {self.model_dir}")
    
    def load_models(self):
        """Load pre-trained models"""
        try:
            if (self.model_dir / "best_random_forest_model.joblib").exists():
                self.models['random_forest'] = joblib.load(self.model_dir / "best_random_forest_model.joblib")
                logger.info("Loaded user's best Random Forest model!")
            elif (self.model_dir / "random_forest_model.pkl").exists():
                self.models['random_forest'] = joblib.load(self.model_dir / "random_forest_model.pkl")
            
            if (self.model_dir / "gradient_boosting_model.pkl").exists():
                self.models['gradient_boosting'] = joblib.load(self.model_dir / "gradient_boosting_model.pkl")
            
            if (self.model_dir / "ensemble_model.pkl").exists():
                self.models['ensemble'] = joblib.load(self.model_dir / "ensemble_model.pkl")
            
            if (self.model_dir / "isolation_forest_model.pkl").exists():
                self.models['isolation_forest'] = joblib.load(self.model_dir / "isolation_forest_model.pkl")
            
            if (self.model_dir / "scaler.pkl").exists():
                self.scalers['standard'] = joblib.load(self.model_dir / "scaler.pkl")
            
            if (self.model_dir / "feature_cols.json").exists():
                with open(self.model_dir / "feature_cols.json") as f:
                    self.feature_cols = json.load(f)
            
            logger.info(f"Models loaded from {self.model_dir}")
        except Exception as e:
            logger.warning(f"Could not load pre-trained models: {str(e)}")


if __name__ == "__main__":
    pipeline = AdvancedMLPipeline()
    csv_path = Path(__file__).parent.parent / "log2.csv"
    if csv_path.exists():
        df = pipeline.load_and_preprocess_data(csv_path)
        X_train, X_test, y_train, y_test = pipeline.prepare_data_for_models(df)
        results, X_test_scaled, y_test_scaled = pipeline.train_all_models(X_train, X_test, y_train, y_test)
        pipeline.save_models()
        
        print("\n" + "="*60)
        print("MODEL TRAINING RESULTS")
        print("="*60)
        for model_name, metrics in results.items():
            print(f"\n{model_name.upper()}:")
            for metric, value in metrics.items():
                if metric != 'feature_importance':
                    if isinstance(value, (int, float)):
                        print(f"  {metric}: {value:.4f}")
                    else:
                        print(f"  {metric}: {value}")
