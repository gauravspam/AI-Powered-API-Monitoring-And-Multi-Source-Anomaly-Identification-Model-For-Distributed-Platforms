
#!/usr/bin/env python3

"""

Comprehensive Validation Suite - WITH FOCAL LOSS SUPPORT (FIXED)

"""



import os

import json

import pickle

import numpy as np

import pandas as pd

from datetime import datetime



import tensorflow as tf

from tensorflow import keras

from tensorflow.keras import layers

from sklearn.preprocessing import StandardScaler

from sklearn.model_selection import train_test_split

from sklearn.metrics import (

    f1_score, precision_score, recall_score, 

    roc_auc_score, confusion_matrix, roc_curve

)



# ============================================================================

# DEFINE FOCAL LOSS (Required for NAB/LO2 models)

# ============================================================================



class FocalLoss(keras.losses.Loss):

    """Focal Loss for handling class imbalance"""

    def __init__(self, alpha=0.25, gamma=2.0, name='focal_loss', **kwargs):

        super().__init__(name=name, **kwargs)

        self.alpha = alpha

        self.gamma = gamma

    

    def call(self, y_true, y_pred):

        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)

        cross_entropy = -y_true * tf.math.log(y_pred)

        weight = self.alpha * y_true * tf.pow(1 - y_pred, self.gamma)

        focal_loss = weight * cross_entropy

        return tf.reduce_mean(focal_loss)

    

    def get_config(self):

        config = super().get_config()

        config.update({'alpha': self.alpha, 'gamma': self.gamma})

        return config



print("="*70)

print("COMPREHENSIVE MODEL VALIDATION SUITE")

print("="*70)

print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")



# ============================================================================

# HELPER FUNCTIONS

# ============================================================================



def create_sequences(data, labels, seq_length):

    """Create sequences for LSTM/GRU"""

    X, y = [], []

    for i in range(len(data) - seq_length):

        X.append(data[i:i + seq_length])

        y.append(labels[i + seq_length])

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)



def evaluate_model(model_path, scaler_path, X_test_raw, y_test, model_name, dataset_name, needs_sequence=False):

    """Evaluate a single model with proper normalization"""

    print(f"\n{'='*70}")

    print(f"Testing: {model_name} on {dataset_name}")

    print(f"{'='*70}")

    

    try:

        # Load model with custom objects

        custom_objects = {'FocalLoss': FocalLoss}

        model = keras.models.load_model(model_path, custom_objects=custom_objects, compile=False)

        

        # Recompile to avoid compilation issues

        model.compile(

            optimizer='adam',

            loss='binary_crossentropy',

            metrics=['accuracy', 'AUC', 'Precision', 'Recall']

        )

        

        with open(scaler_path, 'rb') as f:

            scaler = pickle.load(f)

        print(f"✅ Model loaded: {model_path}")

        print(f"✅ Scaler loaded: {scaler_path}")

        print(f"   Scaler expects {scaler.n_features_in_} features")

        

        # Normalize

        if needs_sequence:

            n_samples, n_timesteps, n_features = X_test_raw.shape

            print(f"   Input shape: {X_test_raw.shape}")

            X_reshaped = X_test_raw.reshape(-1, n_features)

            X_scaled_reshaped = scaler.transform(X_reshaped)

            X_test = X_scaled_reshaped.reshape(n_samples, n_timesteps, n_features)

        else:

            print(f"   Input shape: {X_test_raw.shape}")

            X_test = scaler.transform(X_test_raw)

        

        print(f"   Scaled shape: {X_test.shape}")

        

        # Predictions

        y_pred_proba = model.predict(X_test, verbose=0).flatten()

        print(f"   Predictions range: [{y_pred_proba.min():.4f}, {y_pred_proba.max():.4f}]")

        

        # Find optimal threshold

        fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)

        optimal_idx = np.argmax(tpr - fpr)

        optimal_threshold = thresholds[optimal_idx]

        

        y_pred = (y_pred_proba > optimal_threshold).astype(int)

        

        # Metrics

        f1 = f1_score(y_test, y_pred)

        precision = precision_score(y_test, y_pred, zero_division=0)

        recall = recall_score(y_test, y_pred, zero_division=0)

        auc = roc_auc_score(y_test, y_pred_proba)

        cm = confusion_matrix(y_test, y_pred)

        

        # Status

        if f1 > 0.95:

            status, emoji = "EXCELLENT", "🟢"

        elif f1 > 0.90:

            status, emoji = "GOOD", "🔵"

        elif f1 > 0.80:

            status, emoji = "FAIR", "🟡"

        else:

            status, emoji = "NEEDS_IMPROVEMENT", "🔴"

        

        print(f"\n{emoji} {model_name} Results:")

        print(f"  F1:        {f1:.4f}")

        print(f"  Precision: {precision:.4f}")

        print(f"  Recall:    {recall:.4f}")

        print(f"  AUC:       {auc:.4f}")

        print(f"  Threshold: {optimal_threshold:.4f}")

        print(f"\nConfusion Matrix:")

        print(f"  TP: {cm[1,1]:>6}  FP: {cm[0,1]:>6}")

        print(f"  FN: {cm[1,0]:>6}  TN: {cm[0,0]:>6}")

        print(f"\n  Status: {emoji} {status}")

        

        return {

            'model_name': model_name,

            'dataset': dataset_name,

            'f1': float(f1),

            'precision': float(precision),

            'recall': float(recall),

            'auc': float(auc),

            'threshold': float(optimal_threshold),

            'confusion_matrix': {'TP': int(cm[1,1]), 'FP': int(cm[0,1]), 'FN': int(cm[1,0]), 'TN': int(cm[0,0])},

            'status': status,

            'success': True

        }

        

    except Exception as e:

        print(f"❌ Error: {e}")

        import traceback

        traceback.print_exc()

        return {'model_name': model_name, 'dataset': dataset_name, 'error': str(e), 'success': False}



# ============================================================================

# DATASET 1: MICROSERVICES

# ============================================================================



print("\n" + "="*70)

print("DATASET 1: MICROSERVICES")

print("="*70)



results_micro = []

try:

    df_micro = pd.read_parquet('data/Microservices_ICSE2023/social_network_processed.parquet')

    print(f"✅ Loaded: {df_micro.shape}")

    

    feature_cols_micro = [col for col in df_micro.columns if col not in ['is_anomaly_max', 'timestamp', 'time', 'fault_type_<lambda>', 'experiment']][:21]

    X_micro = df_micro[feature_cols_micro].values

    y_micro = df_micro['is_anomaly_max'].values

    

    X_micro_seq, y_micro_seq = create_sequences(X_micro, y_micro, 100)

    _, X_micro_test_raw, _, y_micro_test = train_test_split(X_micro_seq, y_micro_seq, test_size=0.2, random_state=42, stratify=y_micro_seq)

    

    print(f"Test set: {X_micro_test_raw.shape}, Anomaly rate: {np.mean(y_micro_test):.2%}")

    

    results_micro.append(evaluate_model('models/microservices/msif_lstm_model.keras', 'models/microservices/msif_lstm_scaler.pkl', X_micro_test_raw, y_micro_test, 'MSIF-LSTM', 'Microservices', needs_sequence=True))

    results_micro.append(evaluate_model('models/microservices/ple_gru_model.keras', 'models/microservices/ple_gru_scaler.pkl', X_micro_test_raw, y_micro_test, 'PLE-GRU', 'Microservices', needs_sequence=True))

except Exception as e:

    print(f"❌ Failed: {e}")

    import traceback

    traceback.print_exc()



# ============================================================================

# DATASET 2: NAB

# ============================================================================



print("\n" + "="*70)

print("DATASET 2: NAB")

print("="*70)



results_nab = []

try:

    df_nab = pd.read_csv('data/training_data_nab_aws.csv')

    print(f"✅ Loaded: {df_nab.shape}")

    

    feature_cols_nab = ['response_time', 'status_code', 'request_count', 'error_rate', 'cpu_usage', 'memory_usage', 'network_io', 'disk_io', 'hour_of_day', 'day_of_week']

    X_nab = df_nab[feature_cols_nab].values

    y_nab = df_nab['is_anomaly'].values

    

    _, X_nab_test_raw, _, y_nab_test = train_test_split(X_nab, y_nab, test_size=0.2, random_state=42, stratify=y_nab)

    print(f"Test set: {X_nab_test_raw.shape}, Anomaly rate: {np.mean(y_nab_test):.2%}")

    

    results_nab.append(evaluate_model('models/nab/msif_lstm_model.keras', 'models/nab/scaler.pkl', X_nab_test_raw, y_nab_test, 'MSIF-LSTM', 'NAB', needs_sequence=False))

    results_nab.append(evaluate_model('models/nab/ple_gru_model.keras', 'models/nab/scaler.pkl', X_nab_test_raw, y_nab_test, 'PLE-GRU', 'NAB', needs_sequence=False))

except Exception as e:

    print(f"❌ Failed: {e}")

    import traceback

    traceback.print_exc()



# ============================================================================

# DATASET 3: LO2

# ============================================================================



print("\n" + "="*70)

print("DATASET 3: LO2")

print("="*70)



results_lo2 = []

try:

    df_lo2 = pd.read_csv('data/training_data_lo2.csv')

    print(f"✅ Loaded: {df_lo2.shape}")

    

    feature_cols_lo2 = [col for col in df_lo2.columns if col not in ['is_anomaly', 'timestamp']][:100]

    X_lo2 = df_lo2[feature_cols_lo2].values

    y_lo2 = df_lo2['is_anomaly'].values

    

    _, X_lo2_test_raw, _, y_lo2_test = train_test_split(X_lo2, y_lo2, test_size=0.2, random_state=42, stratify=y_lo2)

    print(f"Test set: {X_lo2_test_raw.shape}, Anomaly rate: {np.mean(y_lo2_test):.2%}")

    

    results_lo2.append(evaluate_model('models/lo2/msif_lstm_model.keras', 'models/lo2/scaler.pkl', X_lo2_test_raw, y_lo2_test, 'MSIF-LSTM', 'LO2', needs_sequence=False))

    results_lo2.append(evaluate_model('models/lo2/ple_gru_model.keras', 'models/lo2/scaler.pkl', X_lo2_test_raw, y_lo2_test, 'PLE-GRU', 'LO2', needs_sequence=False))

except Exception as e:

    print(f"❌ Failed: {e}")

    import traceback

    traceback.print_exc()



# ============================================================================

# GENERATE REPORT

# ============================================================================



print("\n" + "="*70)

print("FINAL REPORT")

print("="*70)



all_results = results_micro + results_nab + results_lo2

successful_results = [r for r in all_results if r.get('success', False)]

successful_results.sort(key=lambda x: x['f1'], reverse=True)



print("\n🏆 LEADERBOARD (BY F1 SCORE)")

print("="*70)

for i, result in enumerate(successful_results, 1):

    emoji = {'EXCELLENT': '🟢', 'GOOD': '🔵', 'FAIR': '🟡', 'NEEDS_IMPROVEMENT': '🔴'}.get(result['status'], '⚪')

    medal = '🥇' if i == 1 else '🥈' if i == 2 else '🥉' if i == 3 else f"{i}."

    print(f"{medal:>3} {result['model_name']:10} ({result['dataset']:15}) {emoji} F1={result['f1']:.4f} | AUC={result['auc']:.4f}")



print("\n📊 DATASET-WISE COMPARISON")

print("="*70)

for dataset in ['Microservices', 'NAB', 'LO2']:

    dataset_results = [r for r in successful_results if r['dataset'] == dataset]

    if dataset_results:

        print(f"\n{dataset}:")

        for result in dataset_results:

            emoji = {'EXCELLENT': '🟢', 'GOOD': '🔵', 'FAIR': '🟡', 'NEEDS_IMPROVEMENT': '🔴'}.get(result['status'], '⚪')

            print(f"  {emoji} {result['model_name']:10} F1={result['f1']:.4f} | AUC={result['auc']:.4f}")



print("\n✅ DEPLOYMENT RECOMMENDATIONS")

print("="*70)

for dataset in ['Microservices', 'NAB', 'LO2']:

    dataset_results = [r for r in successful_results if r['dataset'] == dataset]

    if dataset_results:

        best = max(dataset_results, key=lambda x: x['f1'])

        print(f"\n{dataset}: {best['model_name']}")

        print(f"  F1={best['f1']:.4f} | AUC={best['auc']:.4f} | Threshold={best['threshold']:.4f}")



# Save report

with open('validation_report_final.json', 'w') as f:

    json.dump({'validation_date': datetime.now().isoformat(), 'all_results': all_results, 'leaderboard': successful_results}, f, indent=2)



print(f"\n{'='*70}")

print(f"✅ VALIDATION COMPLETE - Tested {len(successful_results)}/6 models")

print(f"📄 Report: validation_report_final.json")

print("="*70)

