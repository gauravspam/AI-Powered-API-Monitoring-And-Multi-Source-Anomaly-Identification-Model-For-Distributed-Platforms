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
import logging

logger = logging.getLogger('ml-service')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def setup_gpu(mixed_precision=True, memory_limit=None):
    gpus = tf.config.list_physical_devices("GPU")
    if not gpus:
        logger.warning("⚠️ No GPU detected - using CPU")
        return False, 0, None
    logger.info("\n" + "="*70)
    logger.info("🚀 GPU INITIALIZATION")
    logger.info("="*70)
    logger.info(f"GPUs Detected: {len(gpus)}")
    for gpu in gpus:
        if memory_limit:
            tf.config.set_logical_device_configuration(gpu, [tf.config.LogicalDeviceConfiguration(memory_limit=memory_limit)])
        else:
            tf.config.experimental.set_memory_growth(gpu, True)
        logger.info(f"   ✓ Dynamic memory growth enabled")
    policy = None
    if mixed_precision:
        try:
            policy = tf.keras.mixed_precision.Policy("mixed_float16")
            tf.keras.mixed_precision.set_global_policy(policy)
            logger.info(f"   ✓ Mixed precision enabled")
        except:
            logger.warning(f"   ⚠️ Mixed precision unavailable")
    logger.info("="*70)
    return True, len(gpus), policy

class GPUMonitorCallback(tf.keras.callbacks.Callback):
    def __init__(self, batch_size, total_epochs):
        super().__init__()
        self.batch_size = batch_size
        self.total_epochs = total_epochs
        self.start_time = time.time()
    def on_epoch_end(self, epoch, logs=None):
        if logs is None: logs = {}
        elapsed = time.time() - self.start_time
        time_per_epoch = elapsed / (epoch + 1) if epoch > 0 else 0
        eta_seconds = time_per_epoch * (self.total_epochs - epoch - 1)
        gpu_mem_info = "N/A"
        try:
            import subprocess
            result = subprocess.run(["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,nounits,noheader"], capture_output=True, text=True, timeout=2)
            if result.stdout:
                used, total = result.stdout.strip().split(",")
                gpu_mem_info = f"{int(used):,}/{int(total):,}MB"
        except: pass
        loss = logs.get("loss", 0)
        val_loss = logs.get("val_loss", 0)
        acc = logs.get("accuracy", 0)
        logger.info(f"   Epoch {epoch + 1:2d} | Loss: {loss:.4f} | Val Loss: {val_loss:.4f} | Acc: {acc:.4f} | GPU: {gpu_mem_info} | ETA: {eta_seconds / 60:.1f}m")

def load_data(data_path):
    logger.info(f"📂 Loading data from {data_path}")
    df = pd.read_csv(data_path)
    logger.info(f"   ✓ Loaded {len(df):,} samples")
    logger.info(f"   ✓ Columns: {list(df.columns[:5])}... ({len(df.columns)} total)")
    
    # Find label column (is_anomaly or similar)
    label_col = None
    for col in ['is_anomaly', 'label', 'anomaly', 'target', 'y']:
        if col in df.columns:
            label_col = col
            break
    
    if label_col is None:
        raise ValueError("Could not find label column (is_anomaly, label, anomaly, target)")
    
    # All other columns are features
    feature_cols = [c for c in df.columns if c != label_col and c != 'Unnamed: 0' and 'timestamp' not in c.lower() and 'date' not in c.lower()]
    
    logger.info(f"   ✓ Using {len(feature_cols)} features")
    logger.info(f"   ✓ Label column: {label_col}")
    
    X = df[feature_cols].values.astype(np.float32)
    y = df[label_col].values.astype(np.int32)
    
    if np.isnan(X).any():
        mask = ~np.isnan(X).any(axis=1)
        X = X[mask]
        y = y[mask]
    
    logger.info(f"   ✓ Features: {X.shape} | Labels: {np.bincount(y)}")
    return X, y

def split_and_preprocess(X, y, val_split=0.2, test_split=0.1, seed=42):
    logger.info("\n📊 Data Splitting & Preprocessing")
    logger.info("-" * 70)
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=test_split, random_state=seed, stratify=y)
    val_size = val_split / (1 - test_split)
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=val_size, random_state=seed, stratify=y_temp)
    logger.info(f"   ✓ Train: {len(X_train):,} | Val: {len(X_val):,} | Test: {len(X_test):,}")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train).astype(np.float32)
    X_val_scaled = scaler.transform(X_val).astype(np.float32)
    X_test_scaled = scaler.transform(X_test).astype(np.float32)
    logger.info(f"   ✓ Normalized")
    return X_train_scaled, X_val_scaled, X_test_scaled, y_train, y_val, y_test, scaler

def create_tf_dataset(X, y, batch_size, shuffle=True):
    X_reshaped = X.reshape(X.shape[0], 1, X.shape[1])
    dataset = tf.data.Dataset.from_tensor_slices((X_reshaped, y))
    if shuffle: dataset = dataset.shuffle(buffer_size=len(X), reshuffle_each_iteration=True)
    return dataset.batch(batch_size).prefetch(tf.data.AUTOTUNE)

def build_msif_lstm(input_shape):
    inputs = tf.keras.Input(shape=input_shape)
    branch1 = tf.keras.layers.LSTM(64, activation="relu")(inputs)
    branch2 = tf.keras.layers.LSTM(32, activation="relu")(inputs)
    merged = tf.keras.layers.Concatenate()([branch1, branch2])
    x = tf.keras.layers.BatchNormalization()(merged)
    x = tf.keras.layers.Dense(64, activation="relu", kernel_regularizer="l2")(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid", dtype="float32")(x)
    return tf.keras.Model(inputs, outputs, name="MSIF-LSTM")

def build_ple_gru(input_shape):
    inputs = tf.keras.Input(shape=input_shape)
    x = tf.keras.layers.GRU(64, activation="relu", return_sequences=True)(inputs)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    x = tf.keras.layers.GRU(32, activation="relu")(x)
    x = tf.keras.layers.Dense(64, activation="relu", kernel_regularizer="l2")(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid", dtype="float32")(x)
    return tf.keras.Model(inputs, outputs, name="PLE-GRU")

def compile_model(model, learning_rate=0.001):
    lr_schedule = tf.keras.optimizers.schedules.PolynomialDecay(initial_learning_rate=learning_rate, decay_steps=1000, end_learning_rate=0.00001, power=1.0)
    optimizer = tf.keras.optimizers.Adam(learning_rate=lr_schedule)
    model.compile(optimizer=optimizer, loss=tf.keras.losses.BinaryCrossentropy(from_logits=False), metrics=["accuracy", tf.keras.metrics.AUC(name="auc")])
    return model

def calculate_class_weights(y):
    n_normal = (y == 0).sum()
    n_anomaly = (y == 1).sum()
    class_weight = {0: 1.0 / n_normal, 1: 1.0 / n_anomaly}
    logger.info(f"\n⚖️ Class Weights | Normal: {class_weight[0]:.4f} | Anomaly: {class_weight[1]:.4f} | Ratio: {class_weight[1]/class_weight[0]:.1f}x")
    return class_weight

def train_model(model, train_dataset, val_dataset, y_train, epochs, model_name):
    class_weights = calculate_class_weights(y_train)
    logger.info(f"\n{'='*70}\n🚀 Training {model_name}\n{'='*70}")
    callbacks = [GPUMonitorCallback(batch_size=32, total_epochs=epochs), tf.keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, restore_best_weights=True, verbose=0)]
    start_time = time.time()
    history = model.fit(train_dataset, validation_data=val_dataset, epochs=epochs, class_weight=class_weights, callbacks=callbacks, verbose=0)
    elapsed = time.time() - start_time
    logger.info(f"   ✓ Complete in {elapsed/60:.1f}m ({elapsed/epochs:.1f}s/epoch)")
    return history

def evaluate_model(model, X_test, y_test, model_name):
    logger.info(f"\n📊 Evaluating {model_name}\n" + "-" * 70)
    X_test_reshaped = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])
    y_pred_proba = model.predict(X_test_reshaped, verbose=0)
    y_pred = (y_pred_proba > 0.5).astype(int).flatten()
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    try: roc_auc = roc_auc_score(y_test, y_pred_proba)
    except: roc_auc = 0.0
    try:
        precision_curve, recall_curve, _ = precision_recall_curve(y_test, y_pred_proba)
        pr_auc = auc(recall_curve, precision_curve)
    except: pr_auc = 0.0
    results = {"accuracy": float(accuracy), "precision": float(precision), "recall": float(recall), "f1": float(f1), "roc_auc": float(roc_auc), "pr_auc": float(pr_auc)}
    for key, val in results.items(): logger.info(f"   ✓ {key.upper()}: {val:.4f}")
    return results

def main():
    parser = argparse.ArgumentParser(description="GPU-Optimized Training (Flexible)")
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--output-dir", type=str, default="./trained_models_gpu")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--mixed-precision", action="store_true", default=True)
    parser.add_argument("--memory-limit", type=int, default=None)
    args = parser.parse_args()
    gpu_available, num_gpus, policy = setup_gpu(mixed_precision=args.mixed_precision, memory_limit=args.memory_limit)
    logger.info("\n" + "="*70 + "\nAI-Powered Anomaly Detection (GPU v2.0 Flexible)\n" + "="*70 + f"\nData: {args.data_path}\nOutput: {args.output_dir}\nEpochs: {args.epochs} | Batch: {args.batch_size}\nGPU: {'Yes' if gpu_available else 'No'}\n" + "="*70)
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    try:
        X, y = load_data(args.data_path)
        X_train, X_val, X_test, y_train, y_val, y_test, scaler = split_and_preprocess(X, y)
        with open(os.path.join(args.output_dir, "scaler.pkl"), "wb") as f: pickle.dump(scaler, f)
        logger.info(f"\n✅ Scaler saved")
        logger.info("\n🔗 Creating TensorFlow datasets")
        train_dataset = create_tf_dataset(X_train, y_train, args.batch_size, shuffle=True)
        val_dataset = create_tf_dataset(X_val, y_val, args.batch_size, shuffle=False)
        input_shape = (1, X_train.shape[1])
        msif_model = build_msif_lstm(input_shape)
        msif_model = compile_model(msif_model)
        train_model(msif_model, train_dataset, val_dataset, y_train, args.epochs, "MSIF-LSTM")
        msif_model.save(os.path.join(args.output_dir, "msif_lstm_gpu.h5"))
        ple_model = build_ple_gru(input_shape)
        ple_model = compile_model(ple_model)
        train_model(ple_model, train_dataset, val_dataset, y_train, args.epochs, "PLE-GRU")
        ple_model.save(os.path.join(args.output_dir, "ple_gru_gpu.h5"))
        logger.info("\n" + "="*70 + "\nEVALUATION\n" + "="*70)
        msif_metrics = evaluate_model(msif_model, X_test, y_test, "MSIF-LSTM")
        ple_metrics = evaluate_model(ple_model, X_test, y_test, "PLE-GRU")
        metrics = {"msif": msif_metrics, "ple": ple_metrics}
        with open(os.path.join(args.output_dir, "metrics_gpu.json"), "w") as f: json.dump(metrics, f, indent=2)
        logger.info("\n" + "="*70 + "\n✅ GPU TRAINING COMPLETE!\n" + "="*70 + f"\nOutput: {args.output_dir}\nFiles: msif_lstm_gpu.h5, ple_gru_gpu.h5, scaler.pkl, metrics_gpu.json\n" + "="*70)
    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
