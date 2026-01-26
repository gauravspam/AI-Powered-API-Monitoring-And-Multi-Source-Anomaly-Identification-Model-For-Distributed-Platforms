
import pickle

import numpy as np

import pandas as pd

from sklearn.model_selection import train_test_split

from sklearn.preprocessing import StandardScaler

from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint

from tensorflow.keras.layers import GRU, Dense, Dropout, Permute, Reshape

from tensorflow.keras.models import Sequential

from sklearn.metrics import classification_report, roc_auc_score



# Load processed data

df = pd.read_parquet('data/Microservices_ICSE2023/social_network_processed.parquet')



# Select features

feature_cols = [c for c in df.columns if c not in ['timestamp', 'is_anomaly_max', 'fault_type_<lambda>', 'experiment']]

X = df[feature_cols].values

y = df['is_anomaly_max'].values



print(f"Dataset: {X.shape[0]} samples, {X.shape[1]} features")

print(f"Anomaly rate: {y.mean()*100:.1f}%")



# Normalize features

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)



# Create sequences

def create_sequences(X, y, seq_length=100):

    X_seq, y_seq = [], []

    for i in range(len(X) - seq_length):

        X_seq.append(X[i:i+seq_length])

        y_seq.append(y[i+seq_length])

    return np.array(X_seq), np.array(y_seq)



X_seq, y_seq = create_sequences(X_scaled, y)

print(f"Sequence shape: {X_seq.shape}, Labels: {y_seq.shape}")



# Train/test split

X_train, X_test, y_train, y_test = train_test_split(X_seq, y_seq, test_size=0.2, random_state=42, stratify=y_seq)

print(f"Train: {X_train.shape[0]}, Test: {X_test.shape[0]}")



# Build PLE-GRU model

model = Sequential([

    # Input: (batch, 100 timesteps, 21 features)

    Dense(64, activation='relu', input_shape=(100, 21)),

    

    # Permutation Layer Expansion (PLE)

    # Permute dimensions to capture cross-feature relationships

    Permute((2, 1)),  # (batch, 21, 100) - features as time dimension

    

    # GRU processes permuted features

    GRU(32, return_sequences=True),

    Dropout(0.3),

    

    # Permute back

    Permute((2, 1)),  # (batch, 100, 32)

    

    # Standard GRU processing

    GRU(16),

    Dropout(0.2),

    

    Dense(8, activation='relu'),

    Dense(1, activation='sigmoid')

])



model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['AUC', 'accuracy'])

model.summary()



# Train

print("\nStarting PLE-GRU training...")

history = model.fit(

    X_train, y_train,

    validation_data=(X_test, y_test),

    epochs=50,

    batch_size=128,

    callbacks=[

        EarlyStopping(patience=5, restore_best_weights=True, verbose=1),

        ModelCheckpoint('models/microservices_plegru.h5', save_best_only=True, verbose=1)

    ],

    verbose=1

)



# Evaluate

print("\nEvaluating on test set...")

y_pred_prob = model.predict(X_test)

y_pred = (y_pred_prob > 0.5).astype(int)



print("\n" + "="*60)

print("PLE-GRU Test Performance")

print("="*60)

print(f"AUC: {roc_auc_score(y_test, y_pred_prob):.4f}")

print("\n" + classification_report(y_test, y_pred, target_names=['Normal', 'Anomaly']))



# Compare with LSTM

print("\n" + "="*60)

print("Model Comparison")

print("="*60)

print("LSTM AUC:    98.44%")

print(f"PLE-GRU AUC: {roc_auc_score(y_test, y_pred_prob)*100:.2f}%")



# Save scaler (reuse same one)

with open('models/microservices_plegru_scaler.pkl', 'wb') as f:

    pickle.dump(scaler, f)



print("\nPLE-GRU model saved to: models/microservices_plegru.h5")

