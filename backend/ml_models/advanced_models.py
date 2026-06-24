"""
Lightweight Advanced ML Pipeline fallback for environments without numpy/scikit-learn.
This implementation provides the same public interface but uses simple heuristics
so the rest of the application can run without the heavy ML stack installed.
"""

import csv
import random
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class AdvancedMLPipeline:
    """Lightweight fallback pipeline implementing required methods."""
    def __init__(self, data_path=None):
        self.models = {}
        self.scalers = {}
        self.feature_cols = []
        self.model_dir = Path(__file__).parent / "trained_models"
        self.model_dir.mkdir(exist_ok=True)
        self.data_path = data_path

    def load_and_preprocess_data(self, csv_path):
        """Load CSV into list of dicts and do minimal feature engineering."""
        records = []
        try:
            with open(csv_path, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    records.append(row)
            logger.info(f"Loaded {len(records)} records from {csv_path} (fallback)")
        except Exception as e:
            logger.warning(f"Could not load CSV (fallback): {e}")
            raise
        return records

    def prepare_data_for_models(self, df):
        """Prepare simple train/test split of list data."""
        if not df:
            return [], [], [], []
        split = int(len(df) * 0.8)
        X_train = df[:split]
        X_test = df[split:]
        y_train = [0 for _ in X_train]
        y_test = [0 for _ in X_test]
        return X_train, X_test, y_train, y_test

    def train_all_models(self, X_train, X_test, y_train, y_test):
        """Return placeholder training results and register a dummy ensemble."""
        logger.info("Fallback train_all_models called — creating dummy ensemble")
        self.models['ensemble'] = {'type': 'heuristic', 'created_at': datetime.utcnow().isoformat()}
        results = {
            'ensemble': {'accuracy': 0.5, 'auc': 0.5, 'f1': 0.5}
        }
        return results, X_test, y_test

    def save_models(self):
        logger.info("Fallback save_models called — skipping")

    def load_models(self):
        logger.info("Fallback load_models called — skipping")

    def predict_batch(self, X, model_name='ensemble'):
        """Return 0.5 confidence for each input record as fallback."""
        return [0.5 for _ in X]

    def predict_with_all_models(self, X):
        """Return a minimal predictions dict."""
        return { 'ensemble': 0.5 }

    def explain_prediction(self, sample, model_name='random_forest'):
        return None


if __name__ == '__main__':
    pipeline = AdvancedMLPipeline()
    print('Fallback AdvancedMLPipeline ready')
