
#!/usr/bin/env python3

"""

LO2 Dataset Training Script

Dataset: data/training_data_lo2.csv (6.7M)

Best for: Lightweight deployment with good performance

"""



import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'



import tensorflow as tf

import numpy as np

import pandas as pd

from sklearn.preprocessing import StandardScaler

from sklearn.model_selection import train_test_split

import pickle

import json

from datetime import datetime



DATASET_NAME = "LO2"

DATASET_PATH = 'data/training_data_lo2.csv'

OUTPUT_DIR = 'models/lo2'

EPOCHS = 50

BATCH_SIZE = 32

VALIDATION_SPLIT = 0.2

RANDOM_SEED = 42



FEATURE_COLS = [

    'response_time', 'status_code', 'request_count', 'error_rate',

    'cpu_usage', 'memory_usage', 'network_io', 'disk_io',

    'hour_of_day', 'day_of_week'

]



print("="*70)

print(f"🚀 TRAINING MODELS ON {DATASET_NAME} DATASET")

print("="*70)



np.random.seed(RANDOM_SEED)

tf.random.set_seed(RANDOM_SEED)



gpus = tf.config.list_physical_devices('GPU')

if gpus:

    for gpu in gpus:

        tf.config.experimental.set_memory_growth(gpu, True)

    print(f"✅ GPU: {len(gpus)} device(s)")

else:

    print("⚠️  Training on CPU")



os.makedirs(OUTPUT_DIR, exist_ok=True)



print(f"\n📊 Loading {DATASET_PATH}...")

df = pd.read_csv(DATASET_PATH)

print(f"✓ Shape: {df.shape}")

print(f"  Normal: {(df['label']==0).sum():,}, Anomaly: {(df['label']==1).sum():,}")



X = df[FEATURE_COLS].values.astype(np.float32)

y = df['label'].values.astype(np.float32)



scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)



with open(os.path.join(OUTPUT_DIR, 'scaler.pkl'), 'wb') as f:

    pickle.dump(scaler, f)



scaler_meta = {

    'dataset': DATASET_NAME,

    'mean': scaler.mean_.tolist(),

    'std': scaler.scale_.tolist(),

    'feature_names': FEATURE_COLS

}

with open(os.path.join(OUTPUT_DIR, 'scaler_stats.json'), 'w') as f:

    json.dump(scaler_meta, f, indent=2)



X_train, X_test, y_train, y_test = train_test_split(

    X_scaled, y, test_size=VALIDATION_SPLIT, random_state=RANDOM_SEED, stratify=y

)



print(f"\n🏗️  Building MSIF-LSTM...")

msif_model = tf.keras.Sequential([

    tf.keras.layers.Input(shape=(len(FEATURE_COLS),)),

    tf.keras.layers.Reshape((1, len(FEATURE_COLS))),

    tf.keras.layers.LSTM(128, activation='relu', return_sequences=True),

    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.LSTM(64, activation='relu'),

    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.Dense(32, activation='relu'),

    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dropout(0.2),

    tf.keras.layers.Dense(16, activation='relu'),

    tf.keras.layers.Dense(1, activation='sigmoid')

])



msif_model.compile(

    optimizer=tf.keras.optimizers.Adam(0.001),

    loss='binary_crossentropy',

    metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall(), tf.keras.metrics.AUC()]

)



print("🎯 Training MSIF-LSTM...")

msif_model.fit(

    X_train, y_train,

    validation_data=(X_test, y_test),

    epochs=EPOCHS,

    batch_size=BATCH_SIZE,

    verbose=2,

    callbacks=[

        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),

        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6)

    ]

)



msif_loss, msif_acc, msif_prec, msif_rec, msif_auc = msif_model.evaluate(X_test, y_test, verbose=0)

msif_f1 = 2 * msif_prec * msif_rec / (msif_prec + msif_rec)

print(f"✅ MSIF: Acc={msif_acc:.4f}, Prec={msif_prec:.4f}, Rec={msif_rec:.4f}, F1={msif_f1:.4f}")



print(f"\n🏗️  Building PLE-GRU...")

ple_model = tf.keras.Sequential([

    tf.keras.layers.Input(shape=(len(FEATURE_COLS),)),

    tf.keras.layers.Reshape((1, len(FEATURE_COLS))),

    tf.keras.layers.GRU(128, activation='relu', return_sequences=True),

    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.GRU(64, activation='relu'),

    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.Dense(32, activation='relu'),

    tf.keras.layers.BatchNormalization(),

    tf.keras.layers.Dropout(0.2),

    tf.keras.layers.Dense(16, activation='relu'),

    tf.keras.layers.Dense(1, activation='sigmoid')

])



ple_model.compile(

    optimizer=tf.keras.optimizers.Adam(0.001),

    loss='binary_crossentropy',

    metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall(), tf.keras.metrics.AUC()]

)



print("🎯 Training PLE-GRU...")

ple_model.fit(

    X_train, y_train,

    validation_data=(X_test, y_test),

    epochs=EPOCHS,

    batch_size=BATCH_SIZE,

    verbose=2,

    callbacks=[

        tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),

        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=3, min_lr=1e-6)

    ]

)



ple_loss, ple_acc, ple_prec, ple_rec, ple_auc = ple_model.evaluate(X_test, y_test, verbose=0)

ple_f1 = 2 * ple_prec * ple_rec / (ple_prec + ple_rec)

print(f"✅ PLE: Acc={ple_acc:.4f}, Prec={ple_prec:.4f}, Rec={ple_rec:.4f}, F1={ple_f1:.4f}")



msif_model.save(os.path.join(OUTPUT_DIR, 'msif_lstm_model'), save_format='tf')

ple_model.save(os.path.join(OUTPUT_DIR, 'ple_gru_model'), save_format='tf')



metadata = {

    'dataset': DATASET_NAME,

    'dataset_path': DATASET_PATH,

    'training_date': datetime.now().isoformat(),

    'dataset_size': len(X),

    'msif_lstm': {'accuracy': float(msif_acc), 'precision': float(msif_prec), 'recall': float(msif_rec), 'f1_score': float(msif_f1)},

    'ple_gru': {'accuracy': float(ple_acc), 'precision': float(ple_prec), 'recall': float(ple_rec), 'f1_score': float(ple_f1)}

}



with open(os.path.join(OUTPUT_DIR, 'metadata.json'), 'w') as f:

    json.dump(metadata, f, indent=2)



print(f"\n✅ {DATASET_NAME} TRAINING COMPLETE! Saved to {OUTPUT_DIR}/")

