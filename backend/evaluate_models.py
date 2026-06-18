#!/usr/bin/env python3
"""
Model Testing and Evaluation Script
Tests trained models against the dataset and generates detailed metrics
"""

import sys
import os
from pathlib import Path
import logging
import json
import numpy as np
from datetime import datetime
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_curve, auc,
    precision_recall_curve, accuracy_score, f1_score, roc_auc_score
)
import matplotlib.pyplot as plt
import seaborn as sns

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from ml_models.advanced_models import AdvancedMLPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Comprehensive model evaluation and testing"""
    
    def __init__(self):
        self.pipeline = AdvancedMLPipeline()
        self.results = {}
        self.output_dir = Path(__file__).parent / "evaluation_results"
        self.output_dir.mkdir(exist_ok=True)
    
    def evaluate_all_models(self, X_test, y_test):
        """Evaluate all models"""
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE MODEL EVALUATION")
        print("="*70)
        
        for model_name, model in self.pipeline.models.items():
            print(f"\n{'='*70}")
            print(f"Evaluating: {model_name.upper()}")
            print('='*70)
            
            self.evaluate_model(model_name, model, X_test, y_test)
    
    def evaluate_model(self, model_name, model, X_test, y_test):
        """Evaluate single model"""
        try:
            # Get predictions
            if model_name in ['cnn', 'lstm']:
                y_pred_prob = model.predict(X_test)
                y_pred = (y_pred_prob > 0.5).flatten()
            else:
                y_pred = model.predict(X_test)
                y_pred_prob = model.predict_proba(X_test)[:, 1]
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            precision = np.mean(y_pred[y_test == 1] == y_test[y_test == 1]) if np.sum(y_test == 1) > 0 else 0
            recall = np.sum((y_pred == 1) & (y_test == 1)) / np.sum(y_test == 1) if np.sum(y_test == 1) > 0 else 0
            
            if len(np.unique(y_test)) > 1:
                auc_score = roc_auc_score(y_test, y_pred_prob)
            else:
                auc_score = 0.0
            
            # Print metrics
            print(f"  Accuracy:  {accuracy:.4f} ({accuracy*100:.2f}%)")
            print(f"  F1-Score:  {f1:.4f}")
            print(f"  AUC-ROC:   {auc_score:.4f}")
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall:    {recall:.4f}")
            
            # Confusion matrix
            cm = confusion_matrix(y_test, y_pred)
            print(f"\n  Confusion Matrix:")
            print(f"    True Negatives:  {cm[0][0]}")
            print(f"    False Positives: {cm[0][1]}")
            print(f"    False Negatives: {cm[1][0]}")
            print(f"    True Positives:  {cm[1][1]}")
            
            # Classification report
            print(f"\n  Classification Report:")
            report_dict = classification_report(y_test, y_pred, output_dict=True)
            print(f"    Class 0 (Normal):")
            print(f"      Precision: {report_dict['0']['precision']:.4f}")
            print(f"      Recall:    {report_dict['0']['recall']:.4f}")
            print(f"      F1-Score:  {report_dict['0']['f1-score']:.4f}")
            print(f"    Class 1 (Threat):")
            print(f"      Precision: {report_dict['1']['precision']:.4f}")
            print(f"      Recall:    {report_dict['1']['recall']:.4f}")
            print(f"      F1-Score:  {report_dict['1']['f1-score']:.4f}")
            
            # Store results
            self.results[model_name] = {
                'accuracy': float(accuracy),
                'f1_score': float(f1),
                'auc': float(auc_score),
                'precision': float(precision),
                'recall': float(recall),
                'confusion_matrix': cm.tolist(),
                'classification_report': report_dict
            }
            
            # Generate plots if not neural network
            if model_name not in ['cnn', 'lstm']:
                self.plot_model_evaluation(model_name, y_test, y_pred, y_pred_prob, cm)
        
        except Exception as e:
            logger.error(f"Error evaluating {model_name}: {str(e)}")
    
    def plot_model_evaluation(self, model_name, y_test, y_pred, y_pred_prob, cm):
        """Generate evaluation plots"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(12, 10))
            fig.suptitle(f'{model_name.upper()} - Model Evaluation', fontsize=16, fontweight='bold')
            
            # Confusion Matrix
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0, 0])
            axes[0, 0].set_title('Confusion Matrix')
            axes[0, 0].set_ylabel('True Label')
            axes[0, 0].set_xlabel('Predicted Label')
            
            # ROC Curve
            fpr, tpr, _ = roc_curve(y_test, y_pred_prob)
            roc_auc = auc(fpr, tpr)
            axes[0, 1].plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {roc_auc:.3f})')
            axes[0, 1].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
            axes[0, 1].set_xlabel('False Positive Rate')
            axes[0, 1].set_ylabel('True Positive Rate')
            axes[0, 1].set_title('ROC Curve')
            axes[0, 1].legend(loc='lower right')
            
            # Precision-Recall Curve
            precision, recall, _ = precision_recall_curve(y_test, y_pred_prob)
            axes[1, 0].plot(recall, precision, marker='o', label='PR Curve')
            axes[1, 0].set_xlabel('Recall')
            axes[1, 0].set_ylabel('Precision')
            axes[1, 0].set_title('Precision-Recall Curve')
            axes[1, 0].legend()
            axes[1, 0].grid(True)
            
            # Prediction Distribution
            axes[1, 1].hist(y_pred_prob[y_test == 0], bins=50, alpha=0.7, label='Normal', color='blue')
            axes[1, 1].hist(y_pred_prob[y_test == 1], bins=50, alpha=0.7, label='Threat', color='red')
            axes[1, 1].set_xlabel('Prediction Probability')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].set_title('Prediction Distribution')
            axes[1, 1].legend()
            
            plt.tight_layout()
            
            # Save figure
            output_file = self.output_dir / f"{model_name}_evaluation.png"
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            logger.info(f"Saved evaluation plot: {output_file}")
            plt.close()
        
        except Exception as e:
            logger.warning(f"Could not generate plots: {str(e)}")
    
    def generate_summary_report(self):
        """Generate comprehensive summary report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'evaluation_summary': {},
            'model_comparison': {}
        }
        
        # Calculate rankings
        print("\n" + "="*70)
        print("📋 MODEL COMPARISON & RANKINGS")
        print("="*70 + "\n")
        
        # Create comparison table
        metrics = {}
        for model_name, results in self.results.items():
            metrics[model_name] = {
                'accuracy': results['accuracy'],
                'f1_score': results['f1_score'],
                'auc': results['auc'],
                'precision': results['precision'],
                'recall': results['recall']
            }
        
        # Print table
        print(f"{'Model':<20} {'Accuracy':<12} {'F1-Score':<12} {'AUC':<12} {'Precision':<12} {'Recall':<12}")
        print("-" * 80)
        
        for model_name, m in sorted(metrics.items(), key=lambda x: x[1]['accuracy'], reverse=True):
            print(f"{model_name:<20} {m['accuracy']:<12.4f} {m['f1_score']:<12.4f} {m['auc']:<12.4f} {m['precision']:<12.4f} {m['recall']:<12.4f}")
        
        print("-" * 80)
        
        # Find best model
        best_model = max(metrics.items(), key=lambda x: x[1]['accuracy'])
        print(f"\n🏆 Best Model: {best_model[0].upper()} (Accuracy: {best_model[1]['accuracy']:.4f})")
        
        # Save report
        report['model_comparison'] = self.results
        
        output_file = self.output_dir / f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Evaluation report saved: {output_file}")
        
        return report


def main():
    """Main evaluation function"""
    print("\n" + "="*70)
    print("🧪 MODEL TESTING AND EVALUATION")
    print("="*70)
    
    evaluator = ModelEvaluator()
    
    # Load dataset
    csv_path = "/home/neeraj/Downloads/archive/log2.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"Dataset not found at {csv_path}")
        return False
    
    # Load and prepare data
    logger.info("Loading dataset...")
    df = evaluator.pipeline.load_and_preprocess_data(csv_path)
    
    logger.info("Preparing data...")
    X_train, X_test, y_train, y_test = evaluator.pipeline.prepare_data_for_models(df)
    
    # Try to load trained models
    logger.info("Loading trained models...")
    evaluator.pipeline.load_models()
    
    if not evaluator.pipeline.models:
        logger.error("No trained models found. Please run train_models.py first.")
        return False
    
    # Evaluate all models
    evaluator.evaluate_all_models(X_test, y_test)
    
    # Generate summary report
    evaluator.generate_summary_report()
    
    print("\n" + "="*70)
    print("✅ EVALUATION COMPLETE")
    print("="*70)
    print(f"\nResults saved to: {evaluator.output_dir}")
    print("\n")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
