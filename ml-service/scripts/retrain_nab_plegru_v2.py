import json
import os
import pickle

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from tensorflow.keras.layers import (
    GRU,
    BatchNormalization,
    Bidirectional,
    Dense,
    Dropout,
    Input,
)
from tensorflow.keras.models import Model

POSSIBLE_PATHS = [
    "data/training_data_nab_aws.csv",
    "data/NAB/training_data_nab_aws.csv",
    "../data/training_data_nab_aws.csv",
]

DATA_PATH = None
for path in POSSIBLE_PATHS:
    if os.path.exists(path):
        DATA_PATH = path
        break

if DATA_PATH is None:
    print(f"❌ Error: Could not find NAB dataset. Checked: {POSSIBLE_PATHS}")
    exit(1)

MODEL_SAVE_PATH = "models/nab"
SEQ_LENGTH = 10
EPOCHS = 60
BATCH_SIZE = 32
LEARNING_RATE = 1e-3

os.makedirs(MODEL_SAVE_PATH, exist_ok=True)


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


print(f"⏳ Loading dataset from {DATA_PATH}...")
df = pd.read_csv(DATA_PATH)
label_col = "label" if "label" in df.columns else "is_anomaly"
if label_col not in df.columns:
    label_col = df.columns[-1]
print(f"✅ Using label column: {label_col}")

feature_cols = [c for c in df.columns if c not in ["timestamp", label_col]]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[feature_cols].values)
y = df[label_col].values


def create_sequences(data, labels, seq_length):
    xs, ys = [], []
    for i in range(len(data) - seq_length):
        xs.append(data[i : (i + seq_length)])
        ys.append(labels[i + seq_length])
    return np.array(xs), np.array(ys)


X_seq, y_seq = create_sequences(X_scaled, y, SEQ_LENGTH)
X_train, X_test, y_train, y_test = train_test_split(
    X_seq, y_seq, test_size=0.2, shuffle=False
)

input_layer = Input(shape=(SEQ_LENGTH, len(feature_cols)))
x = Bidirectional(GRU(64, return_sequences=True))(input_layer)
x = BatchNormalization()(x)
x = Dropout(0.2)(x)
x = GRU(32, return_sequences=False)(x)
x = BatchNormalization()(x)
x = Dropout(0.2)(x)
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

callbacks = [
    EarlyStopping(
        monitor="val_loss",
        patience=15,
        restore_best_weights=True,
        mode="min",
        verbose=1,
    ),
    ReduceLROnPlateau(
        monitor="val_loss", factor=0.5, patience=5, min_lr=1e-6, verbose=1
    ),
    ModelCheckpoint(
        os.path.join(MODEL_SAVE_PATH, "ple_gru_model.keras"),
        save_best_only=True,
        monitor="val_loss",
        mode="min",
    ),
]

print("🚀 Starting training (Optimized V2)...")
history = model.fit(
    X_train,
    y_train,
    validation_data=(X_test, y_test),
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    callbacks=callbacks,
    verbose=1,
)

with open(os.path.join(MODEL_SAVE_PATH, "ple_gru_scaler.pkl"), "wb") as f:
    pickle.dump(scaler, f)

loss, acc, auc, prec, rec = model.evaluate(X_test, y_test, verbose=0)
f1 = 2 * (prec * rec) / (prec + rec + 1e-7)

metadata_file = os.path.join(MODEL_SAVE_PATH, "ple_gru_metadata.json")
meta = {
    "model_name": "PLE-GRU (BiDirectional)",
    "dataset": "NAB",
    "training_date": str(pd.Timestamp.now()),
    "f1_score": float(f1),
    "precision": float(prec),
    "recall": float(rec),
    "accuracy": float(acc),
    "auc": float(auc),
}

with open(metadata_file, "w") as f:
    json.dump(meta, f, indent=4)

print(f"\n✅ RETRAINING V2 COMPLETE | New F1 Score: {f1:.4f}")
