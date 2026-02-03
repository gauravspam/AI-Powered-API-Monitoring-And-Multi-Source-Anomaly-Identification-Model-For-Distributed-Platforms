import json
import os
import pickle

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.layers import GRU, BatchNormalization, Dense, Dropout, Input
from tensorflow.keras.models import Model

# --- CONFIGURATION ---
DATA_PATH = "data/nab_processed_proper.csv"
MODEL_SAVE_PATH = "models/nab"
SEQ_LENGTH = 10  # Reduced sequence length for small data
EPOCHS = 50
BATCH_SIZE = 16
LEARNING_RATE = 1e-3

os.makedirs(MODEL_SAVE_PATH, exist_ok=True)

# --- DATA LOADING ---
print(f"⏳ Loading dataset from {DATA_PATH}...")
df = pd.read_csv(DATA_PATH)
feature_cols = [c for c in df.columns if c not in ["timestamp", "label"]]
print(f"✅ Features: {feature_cols}")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[feature_cols].values)
y = df["label"].values


def create_sequences(data, labels, seq_length):
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        xs.append(data[i : (i + seq_length)])
        ys.append(labels[i + seq_length])
    return np.array(xs), np.array(ys)


X_seq, y_seq = create_sequences(X_scaled, y, SEQ_LENGTH)

# Split manually to control oversampling
split_idx = int(len(X_seq) * 0.8)
X_train, X_test = X_seq[:split_idx], X_seq[split_idx:]
y_train, y_test = y_seq[:split_idx], y_seq[split_idx:]

# --- OVERSAMPLING ANOMALIES ---
# Find indices of anomalies in training set
anomaly_indices = np.where(y_train == 1)[0]
if len(anomaly_indices) > 0:
    print(f"Found {len(anomaly_indices)} anomalies in training set. Oversampling...")
    # Repeat anomaly samples 50 times
    X_anom = X_train[anomaly_indices]
    y_anom = y_train[anomaly_indices]

    X_train = np.concatenate([X_train] + [X_anom] * 50, axis=0)
    y_train = np.concatenate([y_train] + [y_anom] * 50, axis=0)

    # Shuffle
    indices = np.arange(len(X_train))
    np.random.shuffle(indices)
    X_train = X_train[indices]
    y_train = y_train[indices]
    print(f"New Training Set Size: {len(X_train)} (Anomalies: {sum(y_train)})")
else:
    print("⚠️ No anomalies found in training split! Validation metrics will be poor.")

# --- MODEL ARCHITECTURE (SIMPLIFIED) ---
input_layer = Input(shape=(SEQ_LENGTH, len(feature_cols)))

# Simple GRU
x = GRU(32, return_sequences=False)(input_layer)
x = BatchNormalization()(x)
x = Dropout(0.2)(x)
output_layer = Dense(1, activation="sigmoid")(x)

model = Model(inputs=input_layer, outputs=output_layer)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
    loss="binary_crossentropy",  # Standard loss is safer for now
    metrics=[
        "accuracy",
        tf.keras.metrics.Precision(name="precision"),
        tf.keras.metrics.Recall(name="recall"),
    ],
)

# --- TRAINING ---
callbacks = [
    EarlyStopping(
        monitor="val_loss", patience=10, restore_best_weights=True, verbose=1
    ),
    ModelCheckpoint(
        os.path.join(MODEL_SAVE_PATH, "ple_gru_model.keras"),
        save_best_only=True,
        monitor="val_loss",
        mode="min",
    ),
]

print("🚀 Starting training...")
history = model.fit(
    X_train,
    y_train,
    validation_data=(X_test, y_test),
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    callbacks=callbacks,
    verbose=1,
)

# --- SAVE ---
with open(os.path.join(MODEL_SAVE_PATH, "ple_gru_scaler.pkl"), "wb") as f:
    pickle.dump(scaler, f)

loss, acc, prec, rec = model.evaluate(X_test, y_test, verbose=0)
f1 = 2 * (prec * rec) / (prec + rec + 1e-7)

metadata = {
    "model_name": "PLE-GRU (Simplified)",
    "dataset": "NAB (EC2 Request Latency)",
    "training_date": str(pd.Timestamp.now()),
    "f1_score": float(f1),
    "precision": float(prec),
    "recall": float(rec),
    "accuracy": float(acc),
}

with open(os.path.join(MODEL_SAVE_PATH, "ple_gru_metadata.json"), "w") as f:
    json.dump(metadata, f, indent=4)

print(f"\n✅ NAB RETRAINING COMPLETE | New F1 Score: {f1:.4f}")
