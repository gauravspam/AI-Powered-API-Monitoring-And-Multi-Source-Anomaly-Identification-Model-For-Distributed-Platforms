
#!/usr/bin/env python3

"""NAB Anomaly Detection Training"""

import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import tensorflow as tf

import numpy as np

import pandas as pd

from sklearn.preprocessing import StandardScaler

from sklearn.model_selection import train_test_split

from imblearn.over_sampling import SMOTE

from sklearn.metrics import precision_recall_curve, precision_score, recall_score, f1_score

import pickle

import json

from datetime import datetime



class FocalLoss(tf.keras.losses.Loss):

    def __init__(self, alpha=0.25, gamma=2.0):

        super().__init__()

        self.alpha = alpha

        self.gamma = gamma

    

    def call(self, y_true, y_pred):

        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)

        pt = tf.where(tf.equal(y_true, 1), y_pred, 1 - y_pred)

        alpha_t = tf.where(tf.equal(y_true, 1), self.alpha, 1 - self.alpha)

        focal_loss = -alpha_t * tf.pow(1 - pt, self.gamma) * tf.math.log(pt)

        return tf.reduce_mean(focal_loss)



DATASET_NAME = "NAB"

DATASET_PATH = 'data/training_data_nab_aws.csv'

OUTPUT_DIR = 'models/nab'

EPOCHS = 50

BATCH_SIZE = 16

RANDOM_SEED = 42



print("="*70)

print(f"🚀 NAB ANOMALY DETECTION TRAINING")

print("="*70)



np.random.seed(RANDOM_SEED)

tf.random.set_seed(RANDOM_SEED)



gpus = tf.config.list_physical_devices('GPU')

if gpus:

    for gpu in gpus:

        tf.config.experimental.set_memory_growth(gpu, True)

    print(f"\n✅ GPU: {gpus[0].name}")



os.makedirs(OUTPUT_DIR, exist_ok=True)



# Load data

print(f"\n{'='*70}")

print("📊 LOADING NAB DATASET")

print("="*70)



df = pd.read_csv(DATASET_PATH)

print(f"✓ Shape: {df.shape}")

print(f"✓ Columns: {list(df.columns)}")



# NAB uses 'is_anomaly' not 'label'

label_col = 'is_anomaly'

feature_cols = [col for col in df.columns if col not in [label_col, 'timestamp']]



print(f"\n  Features: {len(feature_cols)}")

print(f"  Label: {label_col}")



X = df[feature_cols].values.astype(np.float32)

y = df[label_col].values.astype(np.float32)



normal_count = (y == 0).sum()

anomaly_count = (y == 1).sum()

print(f"\n  Normal: {normal_count:,} ({normal_count/len(y)*100:.1f}%)")

print(f"  Anomaly: {anomaly_count:,} ({anomaly_count/len(y)*100:.1f}%)")



# Preprocessing

print(f"\n{'='*70}")

print("🔧 PREPROCESSING")

print("="*70)



scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)



with open(os.path.join(OUTPUT_DIR, 'scaler.pkl'), 'wb') as f:

    pickle.dump(scaler, f)

print("✓ Scaler saved")



X_train, X_test, y_train, y_test = train_test_split(

    X_scaled, y, test_size=0.2, random_state=RANDOM_SEED, stratify=y

)



# Apply SMOTE if imbalanced

if anomaly_count / len(y) < 0.3:

    print(f"\n🔧 Applying SMOTE...")

    smote = SMOTE(sampling_strategy=0.4, random_state=RANDOM_SEED)

    X_train, y_train = smote.fit_resample(X_train, y_train)

    print(f"✓ After SMOTE: {len(X_train):,} samples")

    print(f"  Normal: {(y_train==0).sum():,}, Anomaly: {(y_train==1).sum():,}")



# Build MSIF-LSTM

print(f"\n{'='*70}")

print("🏗️  MSIF-LSTM")

print("="*70)



msif_model = tf.keras.Sequential([

    tf.keras.layers.Input(shape=(len(feature_cols),)),

    tf.keras.layers.Reshape((1, len(feature_cols))),

    tf.keras.layers.LSTM(64, activation='relu', return_sequences=True),

    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.LSTM(32, activation='relu'),

    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.Dense(16, activation='relu'),

    tf.keras.layers.Dense(1, activation='sigmoid')

])



msif_model.compile(

    optimizer=tf.keras.optimizers.Adam(0.001),

    loss=FocalLoss(alpha=0.25, gamma=2.0),

    metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall(), tf.keras.metrics.AUC()]

)



print("🎯 Training...")

msif_model.fit(

    X_train, y_train,

    validation_data=(X_test, y_test),

    epochs=EPOCHS,

    batch_size=BATCH_SIZE,

    verbose=2,

    callbacks=[

        tf.keras.callbacks.EarlyStopping(monitor='val_auc', patience=10, mode='max', restore_best_weights=True),

        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_auc', factor=0.5, patience=5, mode='max', min_lr=1e-6)

    ]

)



# Evaluate with optimal threshold

y_pred_proba = msif_model.predict(X_test, verbose=0).flatten()

precisions, recalls, thresholds = precision_recall_curve(y_test, y_pred_proba)

f1_scores = 2 * (precisions[:-1] * recalls[:-1]) / (precisions[:-1] + recalls[:-1] + 1e-7)

optimal_threshold = thresholds[np.argmax(f1_scores)]



y_pred_optimal = (y_pred_proba >= optimal_threshold).astype(int)



msif_loss, msif_acc, msif_prec, msif_rec, msif_auc = msif_model.evaluate(X_test, y_test, verbose=0)

msif_prec_opt = precision_score(y_test, y_pred_optimal)

msif_rec_opt = recall_score(y_test, y_pred_optimal)

msif_f1_opt = f1_score(y_test, y_pred_optimal)



print(f"\n✅ MSIF-LSTM (threshold={optimal_threshold:.3f}):")

print(f"   Precision: {msif_prec_opt:.4f}")

print(f"   Recall:    {msif_rec_opt:.4f}")

print(f"   F1-Score:  {msif_f1_opt:.4f}")

print(f"   AUC:       {msif_auc:.4f}")



# Build PLE-GRU

print(f"\n{'='*70}")

print("🏗️  PLE-GRU")

print("="*70)



ple_model = tf.keras.Sequential([

    tf.keras.layers.Input(shape=(len(feature_cols),)),

    tf.keras.layers.Reshape((1, len(feature_cols))),

    tf.keras.layers.GRU(64, activation='relu', return_sequences=True),

    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.GRU(32, activation='relu'),

    tf.keras.layers.Dropout(0.3),

    tf.keras.layers.Dense(16, activation='relu'),

    tf.keras.layers.Dense(1, activation='sigmoid')

])



ple_model.compile(

    optimizer=tf.keras.optimizers.Adam(0.001),

    loss=FocalLoss(alpha=0.25, gamma=2.0),

    metrics=['accuracy', tf.keras.metrics.Precision(), tf.keras.metrics.Recall(), tf.keras.metrics.AUC()]

)



print("🎯 Training...")

ple_model.fit(

    X_train, y_train,

    validation_data=(X_test, y_test),

    epochs=EPOCHS,

    batch_size=BATCH_SIZE,

    verbose=2,

    callbacks=[

        tf.keras.callbacks.EarlyStopping(monitor='val_auc', patience=10, mode='max', restore_best_weights=True),

        tf.keras.callbacks.ReduceLROnPlateau(monitor='val_auc', factor=0.5, patience=5, mode='max', min_lr=1e-6)

    ]

)



y_pred_proba_ple = ple_model.predict(X_test, verbose=0).flatten()

precisions_ple, recalls_ple, thresholds_ple = precision_recall_curve(y_test, y_pred_proba_ple)

f1_scores_ple = 2 * (precisions_ple[:-1] * recalls_ple[:-1]) / (precisions_ple[:-1] + recalls_ple[:-1] + 1e-7)

optimal_threshold_ple = thresholds_ple[np.argmax(f1_scores_ple)]



y_pred_optimal_ple = (y_pred_proba_ple >= optimal_threshold_ple).astype(int)



ple_loss, ple_acc, ple_prec, ple_rec, ple_auc = ple_model.evaluate(X_test, y_test, verbose=0)

ple_prec_opt = precision_score(y_test, y_pred_optimal_ple)

ple_rec_opt = recall_score(y_test, y_pred_optimal_ple)

ple_f1_opt = f1_score(y_test, y_pred_optimal_ple)



print(f"\n✅ PLE-GRU (threshold={optimal_threshold_ple:.3f}):")

print(f"   Precision: {ple_prec_opt:.4f}")

print(f"   Recall:    {ple_rec_opt:.4f}")

print(f"   F1-Score:  {ple_f1_opt:.4f}")

print(f"   AUC:       {ple_auc:.4f}")



# Save models

print(f"\n{'='*70}")

print("💾 SAVING MODELS")

print("="*70)



msif_model.save(os.path.join(OUTPUT_DIR, 'msif_lstm_model.keras'))

ple_model.save(os.path.join(OUTPUT_DIR, 'ple_gru_model.keras'))



metadata = {

    'dataset': DATASET_NAME,

    'training_date': datetime.now().isoformat(),

    'dataset_size': len(X),

    'n_features': len(feature_cols),

    'feature_names': feature_cols,

    'optimal_thresholds': {

        'msif_lstm': float(optimal_threshold),

        'ple_gru': float(optimal_threshold_ple)

    },

    'msif_lstm': {

        'precision': float(msif_prec_opt),

        'recall': float(msif_rec_opt),

        'f1_score': float(msif_f1_opt),

        'auc': float(msif_auc)

    },

    'ple_gru': {

        'precision': float(ple_prec_opt),

        'recall': float(ple_rec_opt),

        'f1_score': float(ple_f1_opt),

        'auc': float(ple_auc)

    }

}



with open(os.path.join(OUTPUT_DIR, 'metadata.json'), 'w') as f:

    json.dump(metadata, f, indent=2)



print(f"\n{'='*70}")

print("✅ TRAINING COMPLETE!")

print(f"{'='*70}")

print(f"\n📊 Final Performance:")

print(f"   MSIF: Prec={msif_prec_opt:.3f}, Rec={msif_rec_opt:.3f}, F1={msif_f1_opt:.3f}")

print(f"   PLE:  Prec={ple_prec_opt:.3f}, Rec={ple_rec_opt:.3f}, F1={ple_f1_opt:.3f}")

print(f"\n📁 Saved: {OUTPUT_DIR}/")

print("="*70)

