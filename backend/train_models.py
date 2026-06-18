#!/usr/bin/env python3
"""
Complete ML Model Training Script
Trains CNN, LSTM, Random Forest, Gradient Boosting, and Ensemble models
"""

import sys
import os
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from ml_models.advanced_models import AdvancedMLPipeline
import pandas as pd
import numpy as np
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main training function"""
    
    print("\n" + "="*70)
    print("🚀 ADVANCED ML MODEL TRAINING PIPELINE")
    print("="*70)
    
    # Initialize pipeline
    logger.info("Initializing Advanced ML Pipeline...")
    pipeline = AdvancedMLPipeline()
    
    # Path to dataset
    csv_path = "/home/neeraj/Downloads/archive/log2.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"Dataset not found at {csv_path}")
        return False
    
    try:
        # Load and preprocess data
        logger.info(f"Loading data from {csv_path}...")
        df = pipeline.load_and_preprocess_data(csv_path)
        print(f"✓ Loaded {len(df)} network traffic records")
        
        # Show data statistics
        print(f"\nDataset Statistics:")
        print(f"  - Total Records: {len(df)}")
        print(f"  - Threat Distribution:")
        print(f"    - Normal: {(df['is_threat'] == 0).sum()}")
        print(f"    - Threat: {(df['is_threat'] == 1).sum()}")
        
        # Prepare data
        logger.info("Preparing data for training...")
        X_train, X_test, y_train, y_test = pipeline.prepare_data_for_models(df)
        print(f"\n✓ Data prepared:")
        print(f"  - Training set: {len(X_train)} samples")
        print(f"  - Test set: {len(X_test)} samples")
        print(f"  - Features: {len(X_train.columns)}")
        
        # Display features
        print(f"\nFeatures used:")
        for i, feat in enumerate(pipeline.feature_cols, 1):
            print(f"  {i:2d}. {feat}")
        
        # Train all models
        print("\n" + "="*70)
        print("TRAINING ALL MODELS")
        print("="*70 + "\n")
        
        results, X_test_scaled, y_test_scaled = pipeline.train_all_models(
            X_train, X_test, y_train, y_test
        )
        
        # Display results
        print("\n" + "="*70)
        print("📊 MODEL PERFORMANCE COMPARISON")
        print("="*70)
        
        # Create summary table
        print(f"\n{'Model':<20} {'Accuracy':<12} {'AUC':<12} {'F1-Score':<12}")
        print("-" * 56)
        
        best_model = None
        best_accuracy = 0
        
        for model_name, metrics in results.items():
            accuracy = metrics.get('accuracy', 0)
            auc = metrics.get('auc', 0)
            f1 = metrics.get('f1', 0)
            
            print(f"{model_name:<20} {accuracy:<12.4f} {auc:<12.4f} {f1:<12.4f}")
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model = model_name
        
        print("-" * 56)
        print(f"\n🏆 Best Model: {best_model.upper()} (Accuracy: {best_accuracy:.4f})")
        
        # Display feature importance (Random Forest)
        if 'feature_importance' in results.get('random_forest', {}):
            print("\n" + "="*70)
            print("🔍 FEATURE IMPORTANCE (Random Forest)")
            print("="*70 + "\n")
            
            importance_dict = results['random_forest']['feature_importance']
            sorted_features = sorted(importance_dict.items(), key=lambda x: x[1], reverse=True)
            
            print(f"{'Feature':<30} {'Importance':<15}")
            print("-" * 45)
            
            for feature, importance in sorted_features[:15]:
                bar = "█" * int(importance * 100)
                print(f"{feature:<30} {importance:<8.4f} {bar}")
        
        # Save models
        logger.info("Saving trained models...")
        pipeline.save_models()
        print(f"\n✓ Models saved to: {pipeline.model_dir}")
        
        # Training summary
        print("\n" + "="*70)
        print("✅ TRAINING COMPLETE")
        print("="*70)
        print(f"\nTraining Summary:")
        print(f"  - Timestamp: {datetime.now().isoformat()}")
        print(f"  - Models Trained: {len(results)}")
        print(f"  - Best Model: {best_model}")
        print(f"  - Total Parameters: {sum(m.count_params() if hasattr(m, 'count_params') else 0 for m in pipeline.models.values())}")
        
        print(f"\n📁 Model Files:")
        for model_file in pipeline.model_dir.glob("*"):
            size_mb = model_file.stat().st_size / (1024*1024)
            print(f"  - {model_file.name} ({size_mb:.2f} MB)")
        
        print("\n" + "="*70)
        print("Models are ready for predictions!")
        print("Start the Flask backend with: python app.py")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"Training failed: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
