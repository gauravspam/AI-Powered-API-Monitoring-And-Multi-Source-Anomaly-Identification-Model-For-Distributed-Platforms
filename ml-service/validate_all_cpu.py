#!/usr/bin/env python3
"""
CPU-Optimized Model Validation Script
Validates all 6 models across 3 datasets without GPU
"""

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU-only
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'   # Reduce TensorFlow logs

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    f1_score, precision_score, recall_score, roc_auc_score,
    confusion_matrix, classification_report
)
import pickle
import time
from pathlib import Path

# Configure TensorFlow for CPU optimization
tf.config.threading.set_inter_op_parallelism_threads(4)
tf.config.threading.set_intra_op_parallelism_threads(4)

print(f"TensorFlow version: {tf.__version__}")
print(f"Running on: {'GPU' if tf.config.list_physical_devices('GPU') else 'CPU'}")
print("=" * 80)

# Define FocalLoss for model loading
class FocalLoss(keras.losses.Loss):
    def __init__(self, alpha=0.25, gamma=2.0, **kwargs):
        super().__init__(**kwargs)
        self.alpha = alpha
        self.gamma = gamma

    def call(self, y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        ce = -y_true * tf.math.log(y_pred)
        weight = self.alpha * y_true * tf.pow(1 - y_pred, self.gamma)
        return tf.reduce_mean(weight * ce)

    def get_config(self):
        return {'alpha': self.alpha, 'gamma': self.gamma}


def load_model_safely(model_path):
    """Load model with FocalLoss handling"""
    try:
        custom_objects = {'FocalLoss': FocalLoss}
        model = keras.models.load_model(
            model_path, 
            custom_objects=custom_objects, 
            compile=False
        )
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        return model
    except Exception as e:
        print(f"  ❌ Failed to load {model_path}: {e}")
        return None


def load_scaler_safely(scaler_path):
    """Load StandardScaler pickle"""
    try:
        with open(scaler_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        print(f"  ❌ Failed to load scaler {scaler_path}: {e}")
        return None


def prepare_sequences(df, feature_cols, label_col, sequence_length=100):
    """Create sequences from raw data"""
    X, y = [], []
    features = df[feature_cols].values
    labels = df[label_col].values

    for i in range(len(df) - sequence_length + 1):
        X.append(features[i:i + sequence_length])
        y.append(labels[i + sequence_length - 1])

    return np.array(X), np.array(y)


def find_optimal_threshold(y_true, y_pred_proba):
    """Find threshold that maximizes F1"""
    thresholds = np.arange(0.1, 0.95, 0.05)
    best_f1 = 0
    best_threshold = 0.5

    for thresh in thresholds:
        y_pred = (y_pred_proba >= thresh).astype(int)
        f1 = f1_score(y_true, y_pred)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = thresh

    return best_threshold


def validate_model(model_name, dataset_name, model_path, scaler_path, 
                   data_path, feature_cols, label_col, sequence_length=100):
    """Validate a single model on CPU"""
    print(f"\n{'='*80}")
    print(f"Validating: {model_name} on {dataset_name}")
    print(f"{'='*80}")

    start_time = time.time()

    # Load model and scaler
    print("  📦 Loading model...", end=" ")
    model = load_model_safely(model_path)
    if model is None:
        return None
    print("✅")

    print("  📦 Loading scaler...", end=" ")
    scaler = load_scaler_safely(scaler_path)
    if scaler is None:
        return None
    print("✅")

    # Load data
    print("  📦 Loading data...", end=" ")
    try:
        df = pd.read_csv(data_path)
        print(f"✅ ({len(df)} samples)")
    except Exception as e:
        print(f"❌ {e}")
        return None

    # Prepare sequences
    print("  🔄 Creating sequences...", end=" ")
    X_raw, y_true = prepare_sequences(df, feature_cols, label_col, sequence_length)
    print(f"✅ ({len(X_raw)} sequences)")

    # Scale data (crucial step!)
    print("  🔄 Scaling data...", end=" ")
    n_samples, n_timesteps, n_features = X_raw.shape
    X_reshaped = X_raw.reshape(-1, n_features)
    X_scaled_reshaped = scaler.transform(X_reshaped)
    X_scaled = X_scaled_reshaped.reshape(n_samples, n_timesteps, n_features)
    print("✅")

    # Predict (CPU inference with batching)
    print("  🤖 Running inference...", end=" ")
    batch_size = 32  # Smaller batch for CPU
    y_pred_proba = model.predict(X_scaled, batch_size=batch_size, verbose=0)
    y_pred_proba = y_pred_proba.flatten()
    print("✅")

    # Find optimal threshold
    print("  🎯 Finding optimal threshold...", end=" ")
    threshold = find_optimal_threshold(y_true, y_pred_proba)
    print(f"✅ (threshold={threshold:.4f})")

    # Calculate metrics
    y_pred = (y_pred_proba >= threshold).astype(int)

    f1 = f1_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_pred_proba)

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()

    elapsed = time.time() - start_time

    # Print results
    print(f"\n  📊 Results:")
    print(f"     F1 Score:  {f1*100:6.2f}%")
    print(f"     Precision: {precision*100:6.2f}%")
    print(f"     Recall:    {recall*100:6.2f}%")
    print(f"     AUC:       {auc*100:6.2f}%")
    print(f"\n  📈 Confusion Matrix:")
    print(f"     TP: {tp:5d}  |  FN: {fn:5d}")
    print(f"     FP: {fp:5d}  |  TN: {tn:5d}")
    print(f"\n  ⏱️  Time: {elapsed:.2f}s")

    # Status indicator
    if f1 >= 0.90:
        status = "🟢 EXCELLENT"
    elif f1 >= 0.85:
        status = "🔵 GOOD"
    elif f1 >= 0.70:
        status = "🟡 FAIR"
    else:
        status = "🔴 NEEDS_IMPROVEMENT"

    print(f"\n  Status: {status}")

    return {
        'model': model_name,
        'dataset': dataset_name,
        'f1': f1,
        'precision': precision,
        'recall': recall,
        'auc': auc,
        'threshold': threshold,
        'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn,
        'time_seconds': elapsed,
        'status': status
    }


# Dataset configurations
DATASETS = {
    'microservices': {
        'data_path': 'data/microservices.csv',  # Adjust path
        'feature_cols': [col for col in ['cpu_usage', 'memory_usage', 'network_in', 
                         'network_out', 'disk_io_read', 'disk_io_write'] 
                        if col != 'is_anomaly_max'],  # Exclude label
        'label_col': 'is_anomaly_max',
        'sequence_length': 100
    },
    'nab': {
        'data_path': 'data/training_data_nab_aws.csv',
        'feature_cols': ['value'],  # NAB usually has single metric
        'label_col': 'label',
        'sequence_length': 100
    },
    'lo2': {
        'data_path': 'data/training_data_lo2.csv',
        'feature_cols': ['value'],  # Prometheus metric
        'label_col': 'label',
        'sequence_length': 100
    }
}

# Model configurations
MODELS_TO_VALIDATE = [
    ('MSIF-LSTM', 'microservices', 'models/microservices_msif_lstm.h5', 
     'models/scaler_microservices_msif_lstm.pkl'),
    ('PLE-GRU', 'microservices', 'models/microservices_ple_gru.h5', 
     'models/scaler_microservices_ple_gru.pkl'),

    ('MSIF-LSTM', 'nab', 'models/nab_msif_lstm.h5', 
     'models/scaler_nab_msif_lstm.pkl'),
    ('PLE-GRU', 'nab', 'models/nab_ple_gru.h5', 
     'models/scaler_nab_ple_gru.pkl'),

    ('MSIF-LSTM', 'lo2', 'models/lo2_msif_lstm.h5', 
     'models/scaler_lo2_msif_lstm.pkl'),
    ('PLE-GRU', 'lo2', 'models/lo2_ple_gru.h5', 
     'models/scaler_lo2_ple_gru.pkl'),
]


if __name__ == '__main__':
    print("\n🚀 Starting CPU-Optimized Model Validation")
    print(f"   Models: {len(MODELS_TO_VALIDATE)}")
    print(f"   Datasets: {len(DATASETS)}")

    results = []

    for model_name, dataset_name, model_path, scaler_path in MODELS_TO_VALIDATE:
        # Check if files exist
        if not Path(model_path).exists():
            print(f"\n⚠️  Skipping {model_name} on {dataset_name}: model not found")
            continue
        if not Path(scaler_path).exists():
            print(f"\n⚠️  Skipping {model_name} on {dataset_name}: scaler not found")
            continue

        dataset_config = DATASETS[dataset_name]

        result = validate_model(
            model_name=model_name,
            dataset_name=dataset_name,
            model_path=model_path,
            scaler_path=scaler_path,
            data_path=dataset_config['data_path'],
            feature_cols=dataset_config['feature_cols'],
            label_col=dataset_config['label_col'],
            sequence_length=dataset_config['sequence_length']
        )

        if result:
            results.append(result)

    # Summary table
    if results:
        print(f"\n\n{'='*80}")
        print("📊 VALIDATION SUMMARY")
        print(f"{'='*80}")

        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values('f1', ascending=False).reset_index(drop=True)

        print(f"\n{'Rank':<6}{'Model':<15}{'Dataset':<15}{'F1':<10}{'AUC':<10}{'Time (s)':<10}Status")
        print("-" * 80)

        for idx, row in df_results.iterrows():
            print(f"{idx+1:<6}{row['model']:<15}{row['dataset']:<15}"
                  f"{row['f1']*100:>6.2f}%   {row['auc']*100:>6.2f}%   "
                  f"{row['time_seconds']:>6.2f}s   {row['status']}")

        # Save to CSV
        output_file = 'validation_results_cpu.csv'
        df_results.to_csv(output_file, index=False)
        print(f"\n✅ Results saved to: {output_file}")

    print(f"\n{'='*80}")
    print("✅ Validation complete!")
    print(f"{'='*80}\n")
