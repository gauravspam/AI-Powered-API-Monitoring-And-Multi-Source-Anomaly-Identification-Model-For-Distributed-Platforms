import json
import os
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from imblearn.under_sampling import RandomUnderSampler
import logging

logger = logging.getLogger('ml-service')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def setup_gpu():
    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        for gpu in gpus:
            tf.config.experimental.set_memory_growth(gpu, True)
        tf.keras.mixed_precision.set_global_policy("mixed_float16")
        logger.info(f"✓ GPU: {len(gpus)} | Mixed Precision: ON")

def build_model(input_shape):
    inputs = tf.keras.Input(shape=input_shape)
    x = tf.keras.layers.LSTM(128, activation="relu", return_sequences=True)(inputs)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.3)(x)
    x = tf.keras.layers.LSTM(64, activation="relu")(x)
    x = tf.keras.layers.Dense(128, activation="relu")(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    x = tf.keras.layers.Dense(64, activation="relu")(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid", dtype="float32")(x)
    return tf.keras.Model(inputs, outputs, name="LO2-OAuth2-LSTM")

def main():
    logger.info("\n" + "="*70)
    logger.info("🚀 LO2 OAUTH2 MICROSERVICE TRAINING")
    logger.info("="*70)
    
    setup_gpu()
    
    # Load
    logger.info("\n📂 Loading data...")
    df = pd.read_csv('data/training_data_lo2.csv')
    feature_cols = [c for c in df.columns if c != 'is_anomaly']
    X = df[feature_cols].values.astype(np.float32)
    y = df['is_anomaly'].values.astype(np.int32)
    
    logger.info(f"   ✓ Shape: {X.shape} | Normal: {(y==0).sum():,} | Anomaly: {(y==1).sum():,}")
    logger.info(f"   ⚠️ Inverted imbalance: {(y==1).sum()/(y==0).sum():.1f}x more anomalies")
    
    # Balance by undersampling anomalies
    logger.info("\n⚖️ Balancing via RandomUnderSampler...")
    rus = RandomUnderSampler(random_state=42, sampling_strategy=1.0)
    X_balanced, y_balanced = rus.fit_resample(X, y)
    logger.info(f"   ✓ Balanced: {X_balanced.shape} | Normal: {(y_balanced==0).sum():,} | Anomaly: {(y_balanced==1).sum():,}")
    
    # Split
    X_temp, X_test, y_temp, y_test = train_test_split(X_balanced, y_balanced, test_size=0.1, random_state=42, stratify=y_balanced)
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.2, random_state=42, stratify=y_temp)
    
    # Scale
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train).astype(np.float32).reshape(X_train.shape[0], 1, X_train.shape[1])
    X_val = scaler.transform(X_val).astype(np.float32).reshape(X_val.shape[0], 1, X_val.shape[1])
    X_test = scaler.transform(X_test).astype(np.float32).reshape(X_test.shape[0], 1, X_test.shape[1])
    
    # Build
    model = build_model((1, X_train.shape[2]))
    model.compile(optimizer='adam', loss='binary_crossentropy',
                  metrics=['accuracy', tf.keras.metrics.AUC(name='auc')])
    
    logger.info(f"\n🎯 Training (50 epochs)...")
    
    # Train
    history = model.fit(X_train, y_train,
                       validation_data=(X_val, y_val),
                       epochs=50,
                       batch_size=64,
                       callbacks=[tf.keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)],
                       verbose=1)
    
    # Evaluate
    logger.info("\n📊 Evaluation")
    logger.info("="*70)
    
    y_pred_proba = model.predict(X_test, verbose=0).flatten()
    y_pred = (y_pred_proba > 0.5).astype(int)
    
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_pred_proba))
    }
    
    for k, v in metrics.items():
        logger.info(f"   ✓ {k.upper()}: {v:.4f}")
    
    # Save
    os.makedirs('trained_models_lo2_gpu', exist_ok=True)
    model.save('trained_models_lo2_gpu/lo2_lstm.h5')
    with open('trained_models_lo2_gpu/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    with open('trained_models_lo2_gpu/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    
    logger.info(f"\n✅ COMPLETE! ROC-AUC: {metrics['roc_auc']:.4f}")
    logger.info("="*70)

if __name__ == "__main__":
    main()
