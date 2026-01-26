import pickle

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.models import Sequential

df = pd.read_parquet("data/Microservices_ICSE2023/social_network_processed.parquet")

# Select features (exclude timestamp, labels, experiment)
feature_cols = [
    c
    for c in df.columns
    if c not in ["timestamp", "is_anomaly_max", "fault_type_<lambda>", "experiment"]
]
X = df[feature_cols].values
y = df["is_anomaly_max"].values

print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")
print(f"Anomaly rate: {y.mean() * 100:.1f}%")

# Normalize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)


# Create sequences (100 timesteps)
def create_sequences(X, y, seq_length=100):
    X_seq, y_seq = [], []
    for i in range(len(X) - seq_length):
        X_seq.append(X[i : i + seq_length])
        y_seq.append(y[i + seq_length])
    return np.array(X_seq), np.array(y_seq)


X_seq, y_seq = create_sequences(X_scaled, y)
print(f"Sequence shape: {X_seq.shape}, Labels: {y_seq.shape}")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X_seq, y_seq, test_size=0.2, random_state=42, stratify=y_seq
)
print(f"Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")

# Build LSTM model
model = Sequential(
    [
        LSTM(64, return_sequences=True, input_shape=(100, X_seq.shape[2])),
        Dropout(0.3),
        LSTM(32, return_sequences=True),
        Dropout(0.2),
        LSTM(16),
        Dense(8, activation="relu"),
        Dense(1, activation="sigmoid"),
    ]
)

model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["AUC", "accuracy"])
model.summary()

# Train
print("\nStarting training...")
history = model.fit(
    X_train,
    y_train,
    validation_data=(X_test, y_test),
    epochs=50,
    batch_size=128,
    callbacks=[
        EarlyStopping(patience=5, restore_best_weights=True, verbose=1),
        ModelCheckpoint("models/microservices_lstm.h5", save_best_only=True, verbose=1),
    ],
    verbose=1,
)

# Evaluate
print("\nEvaluating on test set...")
y_pred_prob = model.predict(X_test)
y_pred = (y_pred_prob > 0.5).astype(int)

print("\n" + "=" * 60)
print("Test Performance")
print("=" * 60)
print(f"AUC: {roc_auc_score(y_test, y_pred_prob):.4f}")
print("\n" + classification_report(y_test, y_pred, target_names=["Normal", "Anomaly"]))

# Save scaler
with open("models/microservices_scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

print("Model saved to: models/microservices_lstm.h5")
print("Scaler saved to: models/microservices_scaler.pkl")
