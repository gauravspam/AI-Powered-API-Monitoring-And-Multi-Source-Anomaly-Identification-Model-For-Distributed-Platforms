import argparse
import json
import os
import pickle
import time
from pathlib import Path
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, auc, confusion_matrix, f1_score, precision_recall_curve, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
import logging

logger = logging.getLogger('ml-service')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def setup_gpu(mixed_precision=True):
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        logger.info(f"✓ GPU detected: {len(gpus)}")
    if mixed_precision:
        tf.keras.mixed_precision.set_global_policy("mixed_float16")
        logger.info(f"✓ Mixed precision enabled")

def load_and_balance(data_path):
    logger.info(f"📂 Loading {data_path}")
    df = pd.read_csv(data_path)
    
    label_col = 'is_anomaly'
    feature_cols = [c for c in df.columns if c not in [label_col, 'Unnamed: 0']]
    
    X = df[feature_cols].values.astype(np.float32)
    y = df[label_col].values.astype(np.int32)
    
    logger.info(f"   Original - Normal: {(y==0).sum():,} | Anomaly: {(y==1).sum():,}")
    
    # Apply SMOTE to balance classes
    logger.info("\n🔄 Applying SMOTE...")
    smote = SMOTE(random_state=42, k_neighbors=5)
    X_balanced, y_balanced = smote.fit_resample(X, y)
    
    logger.info(f"   After SMOTE - Normal: {(y_balanced==0).sum():,} | Anomaly: {(y_balanced==1).sum():,}")
    
    return X_balanced, y_balanced

def build_improved_lstm(input_shape):
    inputs = tf.keras.Input(shape=input_shape)
    
    # Deeper architecture
    x = tf.keras.layers.LSTM(128, activation="relu", return_sequences=True)(inputs)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    
    x = tf.keras.layers.LSTM(64, activation="relu")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    
    x = tf.keras.layers.Dense(128, activation="relu", kernel_regularizer="l2")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    
    x = tf.keras.layers.Dense(64, activation="relu", kernel_regularizer="l2")(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid", dtype="float32")(x)
    
    return tf.keras.Model(inputs, outputs, name="ImprovedLSTM")

def main():
    logger.info("\n" + "="*70)
    logger.info("🚀 IBM IMPROVED TRAINING")
    logger.info("="*70)
    
    setup_gpu(mixed_precision=True)
    
    # Load and balance data
    X, y = load_and_balance('data/training_data_ibm_improved.csv')
    
    # Split
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.1, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.2, random_state=42, stratify=y_temp)
    
    logger.info(f"\n📊 Split - Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")
    
    # Scale
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train).astype(np.float32)
    X_val = scaler.transform(X_val).astype(np.float32)
    X_test = scaler.transform(X_test).astype(np.float32)
    
    # Reshape for LSTM
    X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
    X_val = X_val.reshape(X_val.shape[0], 1, X_val.shape[1])
    X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])
    
    # Build model
    logger.info("\n🏗️ Building improved model...")
    model = build_improved_lstm(input_shape=(1, X_train.shape[2]))
    
    optimizer = tf.keras.optimizers.Adam(learning_rate=0.001)
    model.compile(optimizer=optimizer, 
                  loss='binary_crossentropy',
                  metrics=['accuracy', tf.keras.metrics.AUC(name='auc'),
                          tf.keras.metrics.Precision(name='precision'),
                          tf.keras.metrics.Recall(name='recall')])
    
    # Train longer without early stopping
    logger.info("\n🎯 Training (50 epochs, no early stopping)...")
    logger.info("="*70)
    
    history = model.fit(X_train, y_train,
                       validation_data=(X_val, y_val),
                       epochs=50,
                       batch_size=128,
                       verbose=1)
    
    # Evaluate with NaN handling
    logger.info("\n📊 Evaluation on Test Set")
    logger.info("="*70)
    
    y_pred_proba = model.predict(X_test, verbose=0).flatten()
    
    # Check for NaN
    if np.isnan(y_pred_proba).any():
        logger.warning(f"⚠️ NaN detected in predictions ({np.isnan(y_pred_proba).sum()} values)")
        # Replace NaN with 0.5 (neutral prediction)
        y_pred_proba = np.nan_to_num(y_pred_proba, nan=0.5)
    
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred)),
        "recall": float(recall_score(y_test, y_pred)),
        "f1": float(f1_score(y_test, y_pred)),
        "roc_auc": float(roc_auc_score(y_test, y_pred_proba))
    }
    
    for k, v in metrics.items():
        logger.info(f"   ✓ {k.upper()}: {v:.4f}")
    
    # Get training metrics
    final_train_auc = history.history['auc'][-1]
    final_val_auc = history.history['val_auc'][-1]
    
    logger.info(f"\n📈 Training Metrics:")
    logger.info(f"   Final Train AUC: {final_train_auc:.4f}")
    logger.info(f"   Final Val AUC: {final_val_auc:.4f}")
    
    # Save
    os.makedirs('trained_models_ibm_improved', exist_ok=True)
    model.save('trained_models_ibm_improved/improved_lstm.h5')
    
    with open('trained_models_ibm_improved/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    with open('trained_models_ibm_improved/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"\n{'='*70}")
    logger.info(f"✅ TRAINING COMPLETE!")
    logger.info(f"{'='*70}")
    logger.info(f"   Test ROC-AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"   Saved to: trained_models_ibm_improved/")
    logger.info("="*70)

if __name__ == "__main__":
    main()
