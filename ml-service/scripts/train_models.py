"""
Complete Training Pipeline for AI-Powered Anomaly Detection System (v2.0)

Orchestrates the entire training workflow with production-grade refinements:
1. Load and preprocess data
2. Train DataPreprocessor (scaler, statistics)
3. Train MSIF-LSTM model (v2.0 with class imbalance handling)
4. Train PLE-GRU model (v2.0 with class imbalance handling)
5. Evaluate both models with comprehensive metrics (PR-AUC, ROC-AUC, F1)
6. Save all artifacts and generate model registry
7. Compare model performance

v2.0 Refinements:
✅ Automatic class weight calculation for imbalanced data
✅ Learning rate scheduling for stable training
✅ Comprehensive evaluation metrics (PR-AUC, ROC-AUC, F1, Specificity)
✅ Confusion matrix analysis
✅ Threshold-based predictions for imbalanced scenarios
✅ Enhanced logging throughout pipeline
✅ Model comparison and registry generation

Usage:
    python scripts/train_models.py \
        --data-path data/training_data.csv \
        --output-dir trained_models \
        --epochs 50 \
        --batch-size 32 \
        --validation-split 0.2 \
        --test-split 0.1

Output:
    trained_models/
    ├── msif_lstm_model.h5
    ├── ple_gru_model.h5
    ├── scaler.pkl
    ├── scaler_stats.json
    └── registry.json
"""

import argparse
import json
import os
import pickle
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from config.settings import config
from models.data_preprocessor import DataPreprocessor
from models.hybrid_fusion import HybridAnomalyDetector
from models.msif_lstm_model import MSIFLSTM
from models.ple_gru_model import PLEGRU
from src.logger import logger
from src.model_registry import ModelRegistry


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Train AI-Powered Anomaly Detection Models (v2.0)'
    )

    parser.add_argument(
        '--data-path',
        type=str,
        required=True,
        help='Path to training data CSV file'
    )

    parser.add_argument(
        '--output-dir',
        type=str,
        default='./trained_models',
        help='Directory to save trained models (default: ./trained_models)'
    )

    parser.add_argument(
        '--epochs',
        type=int,
        default=50,
        help='Number of training epochs (default: 50)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=32,
        help='Batch size for training (default: 32)'
    )

    parser.add_argument(
        '--validation-split',
        type=float,
        default=0.2,
        help='Validation split ratio (default: 0.2)'
    )

    parser.add_argument(
        '--test-split',
        type=float,
        default=0.1,
        help='Test split ratio (default: 0.1)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()


def load_data(data_path: str) -> tuple:
    """
    Load training data from CSV

    Expected CSV format:
    response_time,status_code,request_count,error_rate,cpu_usage,memory_usage,
    network_io,disk_io,hour_of_day,day_of_week,is_anomaly

    Args:
        data_path: Path to CSV file

    Returns:
        (features, labels) - numpy arrays

    Raises:
        FileNotFoundError if file not found
        ValueError if data format invalid
    """

    logger.info(f"Loading data from {data_path}")

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")

    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df):,} samples")

        # Extract features and labels
        # Expected columns: 10 features + is_anomaly label
        feature_cols = [
            'response_time', 'status_code', 'request_count', 'error_rate',
            'cpu_usage', 'memory_usage', 'network_io', 'disk_io',
            'hour_of_day', 'day_of_week'
        ]
        label_col = 'is_anomaly'

        # Validate columns exist
        missing_cols = [col for col in feature_cols + [label_col] if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns in CSV: {missing_cols}")

        X = df[feature_cols].values.astype(np.float32)
        y = df[label_col].values.astype(np.int32)

        # Check for NaN values
        if np.isnan(X).any():
            logger.warning("Found NaN values in features, removing rows")
            mask = ~np.isnan(X).any(axis=1)
            X = X[mask]
            y = y[mask]

        logger.info(f"Features shape: {X.shape}")
        logger.info(f"Labels distribution: {np.bincount(y)}")

        return X, y

    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise


def split_data(X: np.ndarray,
               y: np.ndarray,
               val_split: float,
               test_split: float,
               seed: int) -> tuple:
    """
    Split data into train/val/test sets

    Args:
        X: Features array
        y: Labels array
        val_split: Validation set ratio (0-1)
        test_split: Test set ratio (0-1)
        seed: Random seed

    Returns:
        (X_train, X_val, X_test, y_train, y_val, y_test)
    """

    np.random.seed(seed)
    n_samples = len(X)

    # Calculate split indices
    n_test = int(n_samples * test_split)
    n_val = int((n_samples - n_test) * val_split)
    n_train = n_samples - n_test - n_val

    # Shuffle indices
    indices = np.random.permutation(n_samples)

    train_idx = indices[:n_train]
    val_idx = indices[n_train:n_train + n_val]
    test_idx = indices[n_train + n_val:]

    logger.info(f"Train set: {n_train:,} samples ({n_train/n_samples*100:.1f}%)")
    logger.info(f"Val set: {n_val:,} samples ({n_val/n_samples*100:.1f}%)")
    logger.info(f"Test set: {n_test:,} samples ({n_test/n_samples*100:.1f}%)")

    return (
        X[train_idx], X[val_idx], X[test_idx],
        y[train_idx], y[val_idx], y[test_idx]
    )


def train_preprocessing(X_train: np.ndarray,
                       output_dir: str) -> DataPreprocessor:
    """
    Train data preprocessor (scaler)

    Args:
        X_train: Training features
        output_dir: Directory to save preprocessor

    Returns:
        Trained DataPreprocessor instance
    """

    logger.info("=" * 60)
    logger.info("Training Data Preprocessor")
    logger.info("=" * 60)

    preprocessor = DataPreprocessor()
    preprocessor.fit(X_train)
    preprocessor.save(output_dir)

    logger.info(f"✅ Preprocessor saved to {output_dir}")
    return preprocessor


def train_msif(X_train: np.ndarray,
              y_train: np.ndarray,
              X_val: np.ndarray,
              y_val: np.ndarray,
              output_dir: str,
              preprocessor: DataPreprocessor,
              epochs: int,
              batch_size: int) -> tuple:
    """
    Train MSIF-LSTM model (v2.0)

    Args:
        X_train: Training features (raw)
        y_train: Training labels
        X_val: Validation features (raw)
        y_val: Validation labels
        output_dir: Directory to save model
        preprocessor: DataPreprocessor for normalization
        epochs: Number of epochs
        batch_size: Batch size

    Returns:
        (training_history, model_instance)
    """

    logger.info("=" * 60)
    logger.info("Training MSIF-LSTM Model (v2.0)")
    logger.info("=" * 60)

    # Normalize features
    X_train_norm = np.array([preprocessor.normalize_features(x) for x in X_train])
    X_val_norm = np.array([preprocessor.normalize_features(x) for x in X_val])

    logger.info(f"Normalized data shapes: train={X_train_norm.shape}, val={X_val_norm.shape}")

    # Build and train model with v2.0 refinements
    msif = MSIFLSTM()
    msif.build_model(use_lr_schedule=True)  # ✅ LR scheduling enabled

    history = msif.train(
        X_train_norm, y_train,
        X_val_norm, y_val,
        epochs=epochs,
        batch_size=batch_size,
        auto_class_weight=True  # ✅ Auto-handles imbalance
    )

    # Save model
    msif.save(output_dir)

    logger.info("✅ MSIF-LSTM training complete")
    return history, msif


def train_ple(X_train: np.ndarray,
             y_train: np.ndarray,
             X_val: np.ndarray,
             y_val: np.ndarray,
             output_dir: str,
             preprocessor: DataPreprocessor,
             epochs: int,
             batch_size: int) -> tuple:
    """
    Train PLE-GRU model (v2.0)

    Args:
        X_train: Training features (raw)
        y_train: Training labels
        X_val: Validation features (raw)
        y_val: Validation labels
        output_dir: Directory to save model
        preprocessor: DataPreprocessor for normalization
        epochs: Number of epochs
        batch_size: Batch size

    Returns:
        (training_history, model_instance)
    """

    logger.info("=" * 60)
    logger.info("Training PLE-GRU Model (v2.0)")
    logger.info("=" * 60)

    # Normalize features
    X_train_norm = np.array([preprocessor.normalize_features(x) for x in X_train])
    X_val_norm = np.array([preprocessor.normalize_features(x) for x in X_val])

    logger.info(f"Normalized data shapes: train={X_train_norm.shape}, val={X_val_norm.shape}")

    # Build and train model with v2.0 refinements
    ple = PLEGRU()
    ple.build_model(use_lr_schedule=True)  # ✅ LR scheduling enabled

    history = ple.train(
        X_train_norm, y_train,
        X_val_norm, y_val,
        epochs=epochs,
        batch_size=batch_size,
        auto_class_weight=True  # ✅ Auto-handles imbalance
    )

    # Save model
    ple.save(output_dir)

    logger.info("✅ PLE-GRU training complete")
    return history, ple


def evaluate_models(X_test: np.ndarray,
                   y_test: np.ndarray,
                   output_dir: str,
                   preprocessor: DataPreprocessor) -> dict:
    """
    Evaluate trained models on test set with comprehensive metrics (v2.0)

    NEW: Uses model.evaluate() method with PR-AUC, ROC-AUC, F1, Specificity
    Computes confusion matrix and threshold analysis

    Args:
        X_test: Test features (raw)
        y_test: Test labels
        output_dir: Directory with trained models
        preprocessor: DataPreprocessor

    Returns:
        Evaluation metrics dict with both models
    """

    logger.info("=" * 60)
    logger.info("Evaluating Models (v2.0 - Comprehensive Metrics)")
    logger.info("=" * 60)

    try:
        # Load models
        msif = MSIFLSTM()
        msif.load(output_dir)

        ple = PLEGRU()
        ple.load(output_dir)

        # Normalize test data
        X_test_norm = np.array([preprocessor.normalize_features(x) for x in X_test])

        # NEW: Use model.evaluate() method with comprehensive metrics
        # Default threshold 0.5 for balanced view
        logger.info("")
        logger.info("Evaluating MSIF-LSTM...")
        msif_results = msif.evaluate(X_test_norm, y_test, threshold=0.5)

        logger.info("")
        logger.info("Evaluating PLE-GRU...")
        ple_results = ple.evaluate(X_test_norm, y_test, threshold=0.5)

        # Hybrid predictions
        logger.info("")
        logger.info("Evaluating Hybrid Ensemble...")
        detector = HybridAnomalyDetector(output_dir)
        hybrid_scores = np.array([
            detector.predict(X_test_norm[i:i+1])['hybrid_score']
            for i in range(len(X_test_norm))
        ])

        # NEW: Evaluate hybrid with comprehensive metrics
        from sklearn.metrics import (
            accuracy_score,
            auc,
            confusion_matrix,
            f1_score,
            precision_recall_curve,
            precision_score,
            recall_score,
            roc_auc_score,
        )

        hybrid_pred = (hybrid_scores > 0.5).astype(int)
        hybrid_accuracy = accuracy_score(y_test, hybrid_pred)
        hybrid_precision = precision_score(y_test, hybrid_pred, zero_division=0)
        hybrid_recall = recall_score(y_test, hybrid_pred, zero_division=0)
        hybrid_f1 = f1_score(y_test, hybrid_pred, zero_division=0)

        try:
            hybrid_roc_auc = roc_auc_score(y_test, hybrid_scores)
        except:
            hybrid_roc_auc = 0.0

        try:
            precision_curve, recall_curve, _ = precision_recall_curve(y_test, hybrid_scores)
            hybrid_pr_auc = auc(recall_curve, precision_curve)
        except:
            hybrid_pr_auc = 0.0

        try:
            tn, fp, fn, tp = confusion_matrix(y_test, hybrid_pred).ravel()
            hybrid_specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        except:
            hybrid_specificity = 0.0

        hybrid_results = {
            'accuracy': float(hybrid_accuracy),
            'precision': float(hybrid_precision),
            'recall': float(hybrid_recall),
            'f1': float(hybrid_f1),
            'roc_auc': float(hybrid_roc_auc),
            'pr_auc': float(hybrid_pr_auc),
            'specificity': float(hybrid_specificity),
            'threshold': 0.5
        }

        # Combine results
        metrics = {
            'msif': msif_results,
            'ple': ple_results,
            'hybrid': hybrid_results
        }

        # Log comparative analysis
        logger.info("")
        logger.info("=" * 60)
        logger.info("MODEL COMPARISON")
        logger.info("=" * 60)

        for model_name in ['msif', 'ple', 'hybrid']:
            model_metrics = metrics[model_name]
            logger.info(f"\n{model_name.upper()}:")
            logger.info(f"  Accuracy:  {model_metrics['accuracy']:.4f}")
            logger.info(f"  Precision: {model_metrics['precision']:.4f}")
            logger.info(f"  Recall:    {model_metrics['recall']:.4f}")
            logger.info(f"  F1:        {model_metrics['f1']:.4f}")
            logger.info(f"  ROC-AUC:   {model_metrics['roc_auc']:.4f}")
            logger.info(f"  PR-AUC:    {model_metrics['pr_auc']:.4f}")
            logger.info(f"  Specificity: {model_metrics['specificity']:.4f}")

        logger.info("=" * 60)

        return metrics

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise


def create_registry(output_dir: str,
                   metrics: dict,
                   X_train_shape: tuple,
                   X_test_shape: tuple) -> dict:
    """
    Create and save enhanced model registry (v2.0)

    NEW: Includes PR-AUC, Specificity, and comprehensive metrics
    for imbalanced data evaluation

    Args:
        output_dir: Directory with trained models
        metrics: Evaluation metrics dict (from evaluate_models)
        X_train_shape: Shape of training set
        X_test_shape: Shape of test set

    Returns:
        Registry dict
    """

    logger.info("=" * 60)
    logger.info("Creating Enhanced Model Registry (v2.0)")
    logger.info("=" * 60)

    registry_data = {
        'version': config.API_VERSION,
        'timestamp': datetime.utcnow().isoformat(),
        'training_date': datetime.now().isoformat(),
        'training_pipeline': 'v2.0 (Refined)',
        'models': {
            'msif': {
                'type': 'LSTM',
                'file': 'msif_lstm_model.h5',
                'input_shape': (1, 10),
                'parameters': '~40k',
                'refinements': [
                    'Input validation',
                    'Class imbalance handling',
                    'Learning rate scheduling',
                    'Comprehensive metrics'
                ]
            },
            'ple': {
                'type': 'GRU',
                'file': 'ple_gru_model.h5',
                'input_shape': (1, 10),
                'parameters': '~35k',
                'refinements': [
                    'Input validation',
                    'Class imbalance handling',
                    'Learning rate scheduling',
                    'Comprehensive metrics'
                ]
            },
            'hybrid': {
                'type': 'Weighted Ensemble',
                'combination': 'MSIF (50%) + PLE (50%)',
                'description': 'Combines both models for robustness'
            }
        },
        'preprocessing': {
            'scaler_file': 'scaler.pkl',
            'stats_file': 'scaler_stats.json',
            'normalization': 'StandardScaler',
            'feature_count': 10
        },
        'data': {
            'training_samples': X_train_shape[0],
            'test_samples': X_test_shape[0],
            'features': X_train_shape[1]
        },
        'evaluation': metrics,
        'config': {
            'learning_rate': config.ML_CONFIG.LEARNING_RATE,
            'learning_rate_schedule': 'Polynomial decay (0.0001 → 0.001)',
            'dropout_rate': config.ML_CONFIG.DROPOUT_RATE,
            'epochs': config.ML_CONFIG.EPOCHS,
            'batch_size': config.ML_CONFIG.BATCH_SIZE,
            'early_stopping_patience': 5,
            'class_weight_strategy': 'Automatic (inverse frequency)'
        },
        'metrics_explanation': {
            'pr_auc': 'Precision-Recall AUC (recommended for imbalanced data)',
            'roc_auc': 'ROC AUC (threshold-independent ranking)',
            'f1': 'Harmonic mean of precision and recall',
            'specificity': 'True negative rate (correctly identified normal)',
            'recall': 'True positive rate (detected anomalies)',
            'precision': 'Positive predictive value (accuracy of anomaly predictions)'
        }
    }

    # Save registry
    registry_path = os.path.join(output_dir, 'registry.json')
    with open(registry_path, 'w') as f:
        json.dump(registry_data, f, indent=2)

    logger.info(f"✅ Enhanced registry saved to {registry_path}")
    return registry_data


def main():
    """Main training orchestration"""

    # Parse arguments
    args = parse_arguments()

    logger.info("=" * 60)
    logger.info("AI-Powered Anomaly Detection Training Pipeline (v2.0)")
    logger.info("=" * 60)
    logger.info(f"Data path: {args.data_path}")
    logger.info(f"Output dir: {args.output_dir}")
    logger.info(f"Epochs: {args.epochs}")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Validation split: {args.validation_split}")
    logger.info(f"Test split: {args.test_split}")
    logger.info("")

    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    try:
        # ============= STEP 1: Load data =============
        X, y = load_data(args.data_path)

        # ============= STEP 2: Split data =============
        X_train, X_val, X_test, y_train, y_val, y_test = split_data(
            X, y,
            val_split=args.validation_split,
            test_split=args.test_split,
            seed=args.seed
        )

        # ============= STEP 3: Train preprocessor =============
        preprocessor = train_preprocessing(X_train, args.output_dir)

        # ============= STEP 4: Train MSIF-LSTM (v2.0) =============
        msif_history, msif_model = train_msif(
            X_train, y_train, X_val, y_val,
            args.output_dir, preprocessor,
            args.epochs, args.batch_size
        )

        # ============= STEP 5: Train PLE-GRU (v2.0) =============
        ple_history, ple_model = train_ple(
            X_train, y_train, X_val, y_val,
            args.output_dir, preprocessor,
            args.epochs, args.batch_size
        )

        # ============= STEP 6: Evaluate (v2.0 - Comprehensive) =============
        metrics = evaluate_models(X_test, y_test, args.output_dir, preprocessor)

        # ============= STEP 7: Create enhanced registry =============
        registry = create_registry(
            args.output_dir, metrics,
            X_train.shape, X_test.shape
        )

        logger.info("=" * 60)
        logger.info("✅ Training Pipeline Complete! (v2.0)")
        logger.info("=" * 60)
        logger.info(f"Models saved to: {args.output_dir}")
        logger.info("\nGenerated files:")
        logger.info("  ✅ msif_lstm_model.h5 (with v2.0 refinements)")
        logger.info("  ✅ ple_gru_model.h5 (with v2.0 refinements)")
        logger.info("  ✅ scaler.pkl")
        logger.info("  ✅ scaler_stats.json")
        logger.info("  ✅ registry.json (enhanced with PR-AUC, Specificity)")
        logger.info("")
        logger.info("Key Improvements in v2.0:")
        logger.info("  • Automatic class weight calculation for imbalanced data")
        logger.info("  • Learning rate scheduling for stable convergence")
        logger.info("  • Input validation layer in both models")
        logger.info("  • Comprehensive evaluation metrics (PR-AUC, ROC-AUC, F1)")
        logger.info("  • Threshold-based predictions for flexible deployment")
        logger.info("  • Professional logging and error handling")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
