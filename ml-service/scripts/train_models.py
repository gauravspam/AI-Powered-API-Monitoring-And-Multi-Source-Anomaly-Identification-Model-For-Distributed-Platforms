"""
Complete Training Pipeline for AI-Powered Anomaly Detection System

Orchestrates the entire training workflow:
1. Load and preprocess data
2. Train DataPreprocessor (scaler, statistics)
3. Train MSIF-LSTM model
4. Train PLE-GRU model
5. Save all artifacts
6. Evaluate models
7. Generate model registry

Usage:
    python scripts/train_models.py \
        --data-path data/training_data.csv \
        --output-dir trained_models \
        --epochs 50 \
        --batch-size 32 \
        --validation-split 0.2

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
        description='Train AI-Powered Anomaly Detection Models'
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
              batch_size: int) -> dict:
    """
    Train MSIF-LSTM model

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
        Training history dict
    """

    logger.info("=" * 60)
    logger.info("Training MSIF-LSTM Model")
    logger.info("=" * 60)

    # Normalize features
    X_train_norm = np.array([preprocessor.normalize_features(x) for x in X_train])
    X_val_norm = np.array([preprocessor.normalize_features(x) for x in X_val])

    logger.info(f"Normalized data shapes: train={X_train_norm.shape}, val={X_val_norm.shape}")

    # Build and train model
    msif = MSIFLSTM()
    msif.build_model()

    history = msif.train(
        X_train_norm, y_train,
        X_val_norm, y_val,
        epochs=epochs,
        batch_size=batch_size
    )

    # Save model
    msif.save(output_dir)

    logger.info("✅ MSIF-LSTM training complete")
    return history


def train_ple(X_train: np.ndarray,
             y_train: np.ndarray,
             X_val: np.ndarray,
             y_val: np.ndarray,
             output_dir: str,
             preprocessor: DataPreprocessor,
             epochs: int,
             batch_size: int) -> dict:
    """
    Train PLE-GRU model

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
        Training history dict
    """

    logger.info("=" * 60)
    logger.info("Training PLE-GRU Model")
    logger.info("=" * 60)

    # Normalize features
    X_train_norm = np.array([preprocessor.normalize_features(x) for x in X_train])
    X_val_norm = np.array([preprocessor.normalize_features(x) for x in X_val])

    logger.info(f"Normalized data shapes: train={X_train_norm.shape}, val={X_val_norm.shape}")

    # Build and train model
    ple = PLEGRU()
    ple.build_model()

    history = ple.train(
        X_train_norm, y_train,
        X_val_norm, y_val,
        epochs=epochs,
        batch_size=batch_size
    )

    # Save model
    ple.save(output_dir)

    logger.info("✅ PLE-GRU training complete")
    return history


def evaluate_models(X_test: np.ndarray,
                   y_test: np.ndarray,
                   output_dir: str,
                   preprocessor: DataPreprocessor) -> dict:
    """
    Evaluate trained models on test set

    Computes:
    - Accuracy
    - Precision
    - Recall
    - F1 Score
    - AUC-ROC

    Args:
        X_test: Test features (raw)
        y_test: Test labels
        output_dir: Directory with trained models
        preprocessor: DataPreprocessor

    Returns:
        Evaluation metrics dict
    """

    logger.info("=" * 60)
    logger.info("Evaluating Models")
    logger.info("=" * 60)

    try:
        # Load models
        msif = MSIFLSTM()
        msif.load(output_dir)

        ple = PLEGRU()
        ple.load(output_dir)

        # Normalize test data
        X_test_norm = np.array([preprocessor.normalize_features(x) for x in X_test])

        # Get predictions
        msif_scores = msif.predict(X_test_norm)
        ple_scores = ple.predict(X_test_norm)

        # Hybrid predictions
        detector = HybridAnomalyDetector(output_dir)
        hybrid_scores = np.array([
            detector.predict(X_test_norm[i:i+1])['hybrid_score']
            for i in range(len(X_test_norm))
        ])

        # Threshold for binary classification (0.5)
        threshold = 0.5
        msif_pred = (msif_scores > threshold).astype(int)
        ple_pred = (ple_scores > threshold).astype(int)
        hybrid_pred = (hybrid_scores > threshold).astype(int)

        # Compute metrics
        from sklearn.metrics import (
            accuracy_score,
            f1_score,
            precision_score,
            recall_score,
            roc_auc_score,
        )

        metrics = {
            'msif': {
                'accuracy': accuracy_score(y_test, msif_pred),
                'precision': precision_score(y_test, msif_pred, zero_division=0),
                'recall': recall_score(y_test, msif_pred, zero_division=0),
                'f1': f1_score(y_test, msif_pred, zero_division=0),
                'auc': roc_auc_score(y_test, msif_scores)
            },
            'ple': {
                'accuracy': accuracy_score(y_test, ple_pred),
                'precision': precision_score(y_test, ple_pred, zero_division=0),
                'recall': recall_score(y_test, ple_pred, zero_division=0),
                'f1': f1_score(y_test, ple_pred, zero_division=0),
                'auc': roc_auc_score(y_test, ple_scores)
            },
            'hybrid': {
                'accuracy': accuracy_score(y_test, hybrid_pred),
                'precision': precision_score(y_test, hybrid_pred, zero_division=0),
                'recall': recall_score(y_test, hybrid_pred, zero_division=0),
                'f1': f1_score(y_test, hybrid_pred, zero_division=0),
                'auc': roc_auc_score(y_test, hybrid_scores)
            }
        }

        # Log metrics
        for model_name, model_metrics in metrics.items():
            logger.info(f"\n{model_name.upper()} Model Metrics:")
            for metric_name, value in model_metrics.items():
                logger.info(f"  {metric_name}: {value:.4f}")

        return metrics

    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise


def create_registry(output_dir: str,
                   metrics: dict,
                   X_train_shape: tuple,
                   X_test_shape: tuple) -> dict:
    """
    Create and save model registry

    Args:
        output_dir: Directory with trained models
        metrics: Evaluation metrics dict
        X_train_shape: Shape of training set
        X_test_shape: Shape of test set

    Returns:
        Registry dict
    """

    logger.info("=" * 60)
    logger.info("Creating Model Registry")
    logger.info("=" * 60)

    registry_data = {
        'version': config.API_VERSION,
        'timestamp': datetime.utcnow().isoformat(),
        'training_date': datetime.now().isoformat(),
        'models': {
            'msif': {
                'type': 'LSTM',
                'file': 'msif_lstm_model.h5',
                'input_shape': (1, 10),
                'parameters': '~40k'
            },
            'ple': {
                'type': 'GRU',
                'file': 'ple_gru_model.h5',
                'input_shape': (1, 10),
                'parameters': '~35k'
            },
            'hybrid': {
                'type': 'Weighted Ensemble',
                'combination': 'MSIF + PLE'
            }
        },
        'preprocessing': {
            'scaler_file': 'scaler.pkl',
            'stats_file': 'scaler_stats.json',
            'normalization': 'StandardScaler'
        },
        'data': {
            'training_samples': X_train_shape[0],
            'test_samples': X_test_shape[0],
            'features': X_train_shape[1]
        },
        'evaluation': metrics,
        'config': {
            'learning_rate': config.ML_CONFIG.LEARNING_RATE,
            'dropout_rate': config.ML_CONFIG.DROPOUT_RATE,
            'epochs': config.ML_CONFIG.EPOCHS,
            'batch_size': config.ML_CONFIG.BATCH_SIZE
        }
    }

    # Save registry
    registry_path = os.path.join(output_dir, 'registry.json')
    with open(registry_path, 'w') as f:
        json.dump(registry_data, f, indent=2)

    logger.info(f"✅ Registry saved to {registry_path}")
    return registry_data


def main():
    """Main training orchestration"""

    # Parse arguments
    args = parse_arguments()

    logger.info("=" * 60)
    logger.info("AI-Powered Anomaly Detection Training Pipeline")
    logger.info("=" * 60)
    logger.info(f"Data path: {args.data_path}")
    logger.info(f"Output dir: {args.output_dir}")
    logger.info(f"Epochs: {args.epochs}")
    logger.info(f"Batch size: {args.batch_size}")

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

        # ============= STEP 4: Train MSIF-LSTM =============
        msif_history = train_msif(
            X_train, y_train, X_val, y_val,
            args.output_dir, preprocessor,
            args.epochs, args.batch_size
        )

        # ============= STEP 5: Train PLE-GRU =============
        ple_history = train_ple(
            X_train, y_train, X_val, y_val,
            args.output_dir, preprocessor,
            args.epochs, args.batch_size
        )

        # ============= STEP 6: Evaluate =============
        metrics = evaluate_models(X_test, y_test, args.output_dir, preprocessor)

        # ============= STEP 7: Create registry =============
        registry = create_registry(
            args.output_dir, metrics,
            X_train.shape, X_test.shape
        )

        logger.info("=" * 60)
        logger.info("✅ Training Pipeline Complete!")
        logger.info("=" * 60)
        logger.info(f"Models saved to: {args.output_dir}")
        logger.info("\nGenerated files:")
        logger.info("  - msif_lstm_model.h5")
        logger.info("  - ple_gru_model.h5")
        logger.info("  - scaler.pkl")
        logger.info("  - scaler_stats.json")
        logger.info("  - registry.json")

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
