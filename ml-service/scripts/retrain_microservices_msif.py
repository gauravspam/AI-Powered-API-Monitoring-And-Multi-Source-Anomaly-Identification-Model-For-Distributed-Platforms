import json
import os
import pickle

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.layers import LSTM, BatchNormalization, Dense, Dropout, Input
from tensorflow.keras.models import Model

# --- 1. CONFIGURATION ---
DATA_PATH = "data/Microservices_ICSE2023/social_network_processed.parquet"
MODEL_SAVE_PATH = "models/microservices"
SEQ_LENGTH = 100
EPOCHS = 50
BATCH_SIZE = 64
LEARNING_RATE = 1e-4

# Ensure directory exists
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)

# --- 2. CUSTOM LOSS FUNCTION ---
@tf.keras.utils.register_keras_serializable(package="CustomLosses")
class FocalLoss(tf.keras.losses.Loss):
    def __init__(self, alpha=0.25, gamma=2.0, name="focal_loss", **kwargs):
        super().__init__(name=name, **kwargs)
        self.alpha = alpha
        self.gamma = gamma

    def call(self, y_true, y_pred):
        y_pred = tf.clip_by_value(
            y_pred, tf.keras.backend.epsilon(), 1 - tf.keras.backend.epsilon()
        )
        cross_entropy = -y_true * tf.math.log(y_pred)
        weight = self.alpha * y_true * tf.pow((1 - y_pred), self.gamma)
        focal_loss = weight * cross_entropy
        return tf.reduce_mean(tf.reduce_sum(focal_loss, axis=1))

    def get_config(self):
        config = super().get_config()
        config.update({"alpha": self.alpha, "gamma": self.gamma})
        return config


# --- 3. DATA LOADING & PREPROCESSING ---
print(f"⏳ Loading dataset from {DATA_PATH}...")
try:
    if DATA_PATH.endswith(".parquet"):
        df = pd.read_parquet(DATA_PATH)
    else:
        df = pd.read_csv(DATA_PATH)
    print("✅ Dataset loaded successfully")
except FileNotFoundError:
    print(f"❌ Error: Data file not found at {DATA_PATH}")
    exit(1)

# FORCE RENAME 'is_anomaly_max' to 'label'
if "is_anomaly_max" in df.columns:
    print("⚠️ Renaming 'is_anomaly_max' to 'label'")
    df.rename(columns={"is_anomaly_max": "label"}, inplace=True)

if "label" not in df.columns:
    print(f"❌ Error: 'label' column not found. Available columns: {list(df.columns)}")
    exit(1)

# Feature selection
# Removed 'is_anomaly_max' from exclusions since we renamed it
feature_cols = [
    c
    for c in df.columns
    if c
    not in ["timestamp", "label", "experiment", "fault_type_<lambda>", "is_anomaly"]
]
print(f"✅ Features selected ({len(feature_cols)}): {feature_cols[:3]}...")

# Scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[feature_cols].values)
y = df["label"].values


# Create Sequences
def create_sequences(data, labels, seq_length):
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        xs.append(data[i : (i + seq_length)])
        ys.append(labels[i + seq_length])
    return np.array(xs), np.array(ys)


print("⏳ Creating sequences...")
X_seq, y_seq = create_sequences(X_scaled, y, SEQ_LENGTH)
print(f"✅ Data shape: {X_seq.shape}")

# Split
X_train, X_test, y_train, y_test = train_test_split(
    X_seq, y_seq, test_size=0.2, shuffle=False
)

# --- 4. MODEL ARCHITECTURE ---
input_layer = Input(shape=(SEQ_LENGTH, len(feature_cols)))

# Layer 1
x = LSTM(64, return_sequences=True, kernel_regularizer=tf.keras.regularizers.l2(0.001))(
    input_layer
)
x = BatchNormalization()(x)
x = Dropout(0.3)(x)

# Layer 2
x = LSTM(32, return_sequences=False)(x)
x = BatchNormalization()(x)
x = Dropout(0.3)(x)

# Output
output_layer = Dense(1, activation="sigmoid")(x)

model = Model(inputs=input_layer, outputs=output_layer)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
    loss=FocalLoss(alpha=0.25, gamma=2.0),
    metrics=[
        "accuracy",
        tf.keras.metrics.AUC(name="auc"),
        tf.keras.metrics.Precision(name="precision"),
        tf.keras.metrics.Recall(name="recall"),
    ],
)

model.summary()

# --- 5. TRAINING ---
callbacks = [
    EarlyStopping(
        monitor="val_loss", patience=10, restore_best_weights=True, verbose=1
    ),
    ReduceLROnPlateau(
        monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6, verbose=1
    ),
    ModelCheckpoint(
        os.path.join(MODEL_SAVE_PATH, "msif_lstm_model.keras"),
        save_best_only=True,
        monitor="val_auc",
        mode="max",
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

# --- 6. SAVE ---
print("💾 Saving artifacts...")
with open(os.path.join(MODEL_SAVE_PATH, "msif_lstm_scaler.pkl"), "wb") as f:
    pickle.dump(scaler, f)

loss, acc, auc, prec, rec = model.evaluate(X_test, y_test, verbose=0)
f1 = 2 * (prec * rec) / (prec + rec + 1e-7)

metadata = {
    "model_name": "MSIF-LSTM",
    "dataset": "Microservices",
    "training_date": str(pd.Timestamp.now()),
    "n_features": len(feature_cols),
    "f1_score": float(f1),
    "precision": float(prec),
    "recall": float(rec),
    "accuracy": float(acc),
    "auc": float(auc),
}

with open(os.path.join(MODEL_SAVE_PATH, "metadata.json"), "w") as f:
    json.dump(metadata, f, indent=4)

print("\n" + "=" * 50)
print(f"✅ RETRAINING COMPLETE")
print(f"📊 New F1 Score: {f1:.4f}")
print("=" * 50)
print("="*50)
