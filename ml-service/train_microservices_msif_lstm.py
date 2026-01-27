
#!/usr/bin/env python3

"""

Standalone MSIF-LSTM Training Script for Microservices Dataset

No external project dependencies required

"""



import os

import json

import pickle

import numpy as np

import pandas as pd

from datetime import datetime



import tensorflow as tf

from tensorflow import keras

from tensorflow.keras import layers, models

from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau

from sklearn.preprocessing import StandardScaler

from sklearn.model_selection import train_test_split

from sklearn.metrics import (

    f1_score, precision_score, recall_score, 

    roc_auc_score, confusion_matrix, roc_curve

)



# Configuration

CONFIG = {

    'dataset_name': 'Microservices',

    'data_path': 'data/Microservices_ICSE2023/social_network_processed.parquet',

    'model_save_dir': 'models/microservices',

    'sequence_length': 100,

    'n_features': 21,

    'batch_size': 32,

    'epochs': 100,

    'validation_split': 0.2,

    'early_stopping_patience': 15,

    'learning_rate': 0.001,

    'lstm_units': [64, 32],  # MSIF-LSTM architecture

    'dense_units': [16],

    'dropout_rate': 0.3,

}



def build_msif_lstm_model(input_shape, learning_rate=0.001):

    """Build MSIF-LSTM model architecture"""

    model = models.Sequential([

        layers.Input(shape=input_shape),

        

        # LSTM Layer 1

        layers.LSTM(

            CONFIG['lstm_units'][0],

            return_sequences=True,

            activation='relu',

            recurrent_dropout=0.2

        ),

        layers.BatchNormalization(),

        layers.Dropout(CONFIG['dropout_rate']),

        

        # LSTM Layer 2

        layers.LSTM(

            CONFIG['lstm_units'][1],

            return_sequences=False,

            activation='relu',

            recurrent_dropout=0.2

        ),

        layers.BatchNormalization(),

        layers.Dropout(CONFIG['dropout_rate']),

        

        # Dense layers

        layers.Dense(CONFIG['dense_units'][0], activation='relu'),

        layers.Dropout(CONFIG['dropout_rate']),

        

        # Output

        layers.Dense(1, activation='sigmoid')

    ])

    

    model.compile(

        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),

        loss='binary_crossentropy',

        metrics=['accuracy', 'AUC', 'Precision', 'Recall']

    )

    

    return model



def load_microservices_data():

    """Load and prepare Microservices dataset"""

    print(f"Loading Microservices dataset from {CONFIG['data_path']}")

    

    try:

        df = pd.read_parquet(CONFIG['data_path'])

        print(f"✅ Loaded parquet file successfully")

    except Exception as e:

        print(f"❌ Error loading data: {e}")

        exit(1)

    

    print(f"Dataset shape: {df.shape}")

    print(f"Columns: {list(df.columns)[:10]}... (showing first 10)")

    if 'label' in df.columns:

        print(f"Label distribution:\n{df['label'].value_counts()}")

    

    return df



def create_sequences(data, labels, seq_length):

    """Create sequences for LSTM"""

    X, y = [], []

    

    for i in range(len(data) - seq_length):

        X.append(data[i:i + seq_length])

        y.append(labels[i + seq_length])

    

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.float32)



def prepare_training_data(df):

    """Prepare data for training"""

    print("\n" + "="*70)

    print("DATA PREPARATION")

    print("="*70)

    

    # Separate features and labels

    feature_cols = [col for col in df.columns if col not in ['is_anomaly_max', 'timestamp', 'time', 'fault_type_<lambda>', 'experiment']]

    feature_cols = feature_cols[:CONFIG['n_features']]

    

    print(f"Using {len(feature_cols)} features")

    print(f"Feature columns: {feature_cols[:5]}... (showing first 5)")

    

    X = df[feature_cols].values

    y = df['is_anomaly_max'].values

    

    print(f"Features shape: {X.shape}")

    print(f"Labels shape: {y.shape}")

    print(f"Anomaly rate: {np.mean(y):.2%}")

    

    # Create sequences

    print(f"Creating sequences with length {CONFIG['sequence_length']}...")

    X_seq, y_seq = create_sequences(X, y, CONFIG['sequence_length'])

    print(f"Sequences shape: {X_seq.shape}")

    print(f"Labels shape: {y_seq.shape}")

    

    # Normalize

    print("Normalizing sequences...")

    scaler = StandardScaler()

    

    n_samples, n_timesteps, n_features = X_seq.shape

    X_reshaped = X_seq.reshape(-1, n_features)

    X_scaled_reshaped = scaler.fit_transform(X_reshaped)

    X_scaled = X_scaled_reshaped.reshape(n_samples, n_timesteps, n_features)

    

    # Save scaler

    os.makedirs(CONFIG['model_save_dir'], exist_ok=True)

    scaler_path = os.path.join(CONFIG['model_save_dir'], 'msif_lstm_scaler.pkl')

    with open(scaler_path, 'wb') as f:

        pickle.dump(scaler, f)

    print(f"✅ Scaler saved: {scaler_path}")

    

    return X_scaled, y_seq, scaler



def train_model(X_train, y_train, X_val, y_val):

    """Train MSIF-LSTM model"""

    print("\n" + "="*70)

    print("MODEL TRAINING")

    print("="*70)

    

    # Build model

    print(f"Building MSIF-LSTM model...")

    print(f"Input shape: ({CONFIG['sequence_length']}, {CONFIG['n_features']})")

    

    model = build_msif_lstm_model(

        input_shape=(CONFIG['sequence_length'], CONFIG['n_features']),

        learning_rate=CONFIG['learning_rate']

    )

    

    print("\nModel architecture:")

    model.summary()

    

    # Callbacks

    early_stopping = EarlyStopping(

        monitor='val_loss',

        patience=CONFIG['early_stopping_patience'],

        restore_best_weights=True,

        verbose=1

    )

    

    reduce_lr = ReduceLROnPlateau(

        monitor='val_loss',

        factor=0.5,

        patience=5,

        min_lr=1e-6,

        verbose=1

    )

    

    # Train

    print(f"\nTraining on {len(X_train)} samples, validating on {len(X_val)} samples")

    print(f"Batch size: {CONFIG['batch_size']}, Max epochs: {CONFIG['epochs']}")

    

    history = model.fit(

        X_train, y_train,

        validation_data=(X_val, y_val),

        epochs=CONFIG['epochs'],

        batch_size=CONFIG['batch_size'],

        callbacks=[early_stopping, reduce_lr],

        verbose=1

    )

    

    # Save model

    model_path = os.path.join(CONFIG['model_save_dir'], 'msif_lstm_model.keras')

    model.save(model_path)

    print(f"\n✅ Model saved: {model_path}")

    

    return model, history



def evaluate_model(model, X_test, y_test):

    """Evaluate model on test set"""

    print("\n" + "="*70)

    print("MODEL EVALUATION")

    print("="*70)

    

    # Predictions

    print("Generating predictions...")

    y_pred_proba = model.predict(X_test, verbose=0).flatten()

    

    # Find optimal threshold

    fpr, tpr, thresholds = roc_curve(y_test, y_pred_proba)

    optimal_idx = np.argmax(tpr - fpr)

    optimal_threshold = thresholds[optimal_idx]

    

    y_pred = (y_pred_proba > optimal_threshold).astype(int)

    

    # Metrics

    f1 = f1_score(y_test, y_pred)

    precision = precision_score(y_test, y_pred)

    recall = recall_score(y_test, y_pred)

    auc = roc_auc_score(y_test, y_pred_proba)

    cm = confusion_matrix(y_test, y_pred)

    

    print(f"\n🔵 MSIF-LSTM (Microservices)")

    print(f"  F1:        {f1:.4f}")

    print(f"  Precision: {precision:.4f}")

    print(f"  Recall:    {recall:.4f}")

    print(f"  AUC:       {auc:.4f}")

    print(f"  Threshold: {optimal_threshold:.4f}")

    print(f"\nConfusion Matrix:")

    print(f"  TP: {cm[1,1]:>6}  FP: {cm[0,1]:>6}")

    print(f"  FN: {cm[1,0]:>6}  TN: {cm[0,0]:>6}")

    

    status = 'EXCELLENT' if f1 > 0.95 else 'GOOD' if f1 > 0.90 else 'FAIR' if f1 > 0.80 else 'NEEDS_IMPROVEMENT'

    print(f"\n  Status: ✅ {status}")

    

    metrics = {

        'f1': float(f1),

        'precision': float(precision),

        'recall': float(recall),

        'auc': float(auc),

        'threshold': float(optimal_threshold),

        'confusion_matrix': cm.tolist(),

        'status': status

    }

    

    return metrics



def save_metadata(metrics):

    """Save model metadata"""

    metadata = {

        'model_name': 'MSIF-LSTM',

        'dataset': 'Microservices',

        'training_date': datetime.now().isoformat(),

        'n_features': CONFIG['n_features'],

        'metrics': metrics,

        'hyperparameters': {

            'sequence_length': CONFIG['sequence_length'],

            'batch_size': CONFIG['batch_size'],

            'epochs': CONFIG['epochs'],

            'learning_rate': CONFIG['learning_rate'],

            'early_stopping_patience': CONFIG['early_stopping_patience'],

            'lstm_units': CONFIG['lstm_units'],

            'dense_units': CONFIG['dense_units'],

            'dropout_rate': CONFIG['dropout_rate'],

        }

    }

    

    metadata_path = os.path.join(CONFIG['model_save_dir'], 'metadata.json')

    with open(metadata_path, 'w') as f:

        json.dump(metadata, f, indent=2)

    print(f"✅ Metadata saved: {metadata_path}")

    

    return metadata



def main():

    print("="*70)

    print("MICROSERVICES MSIF-LSTM TRAINING")

    print("="*70)

    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    

    # Load data

    df = load_microservices_data()

    

    # Prepare data

    X, y, scaler = prepare_training_data(df)

    

    # Train-test split

    print("\nSplitting data...")

    X_train, X_test, y_train, y_test = train_test_split(

        X, y, test_size=0.2, random_state=42, stratify=y

    )

    

    X_train, X_val, y_train, y_val = train_test_split(

        X_train, y_train, test_size=CONFIG['validation_split'], random_state=42, stratify=y_train

    )

    

    print(f"Train: {X_train.shape} ({np.mean(y_train):.2%} anomaly)")

    print(f"Val:   {X_val.shape} ({np.mean(y_val):.2%} anomaly)")

    print(f"Test:  {X_test.shape} ({np.mean(y_test):.2%} anomaly)")

    

    # Train model

    model, history = train_model(X_train, y_train, X_val, y_val)

    

    # Evaluate

    metrics = evaluate_model(model, X_test, y_test)

    

    # Save metadata

    metadata = save_metadata(metrics)

    

    print("\n" + "="*70)

    print("✅ TRAINING COMPLETE")

    print("="*70)

    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print(f"\nModel files:")

    print(f"  • Model:    {CONFIG['model_save_dir']}/msif_lstm_model.keras")

    print(f"  • Scaler:   {CONFIG['model_save_dir']}/msif_lstm_scaler.pkl")

    print(f"  • Metadata: {CONFIG['model_save_dir']}/metadata.json")

    print(f"\nPerformance:")

    print(f"  • F1 Score: {metrics['f1']:.4f}")

    print(f"  • AUC:      {metrics['auc']:.4f}")

    print(f"  • Status:   {metrics['status']}")

    print("="*70)



if __name__ == '__main__':

    main()

