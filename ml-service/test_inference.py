import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import json
import pickle

import keras  # Import keras directly for decorator
import numpy as np
import tensorflow as tf

# ============================================================================
# REGISTER CUSTOM LOSS (must be done BEFORE loading model)
# ============================================================================


@keras.saving.register_keras_serializable(package="CustomLosses")
class FocalLoss(keras.losses.Loss):
    def __init__(self, alpha=0.25, gamma=2.0, **kwargs):
        super().__init__(**kwargs)
        self.alpha = alpha
        self.gamma = gamma

    def call(self, y_true, y_pred):
        y_pred = tf.clip_by_value(y_pred, 1e-7, 1 - 1e-7)
        pt = tf.where(tf.equal(y_true, 1), y_pred, 1 - y_pred)
        alpha_t = tf.where(tf.equal(y_true, 1), self.alpha, 1 - self.alpha)
        focal_loss = -alpha_t * tf.pow(1 - pt, self.gamma) * tf.math.log(pt)
        return tf.reduce_mean(focal_loss)

    def get_config(self):
        base_config = super().get_config()
        return {**base_config, "alpha": self.alpha, "gamma": self.gamma}


# ============================================================================
# LOAD MODELS
# ============================================================================

print("Loading models...")

msif_model = keras.models.load_model(
    "models/nab/msif_lstm_model.keras", custom_objects={"FocalLoss": FocalLoss}
)

ple_model = keras.models.load_model(
    "models/nab/ple_gru_model.keras", custom_objects={"FocalLoss": FocalLoss}
)

print("✅ Models loaded successfully!")

# Load scaler and metadata
with open("models/nab/scaler.pkl", "rb") as f:
    scaler = pickle.load(f)

with open("models/nab/metadata.json", "r") as f:
    metadata = json.load(f)

print(f"\n📊 Model Information:")
print(f"Dataset: {metadata['dataset']}")
print(f"Optimal Thresholds:")
print(f"  MSIF-LSTM: {metadata['optimal_thresholds']['msif_lstm']:.3f}")
print(f"  PLE-GRU: {metadata['optimal_thresholds']['ple_gru']:.3f}")

print(f"\n📈 Training Results:")
print(
    f"  MSIF-LSTM: Prec={metadata['msif_lstm']['precision']:.3f}, Rec={metadata['msif_lstm']['recall']:.3f}, F1={metadata['msif_lstm']['f1_score']:.3f}"
)
print(
    f"  PLE-GRU: Prec={metadata['ple_gru']['precision']:.3f}, Rec={metadata['ple_gru']['recall']:.3f}, F1={metadata['ple_gru']['f1_score']:.3f}"
)

# ============================================================================
# TEST INFERENCE
# ============================================================================

print(f"\n{'=' * 70}")
print("🎯 TESTING INFERENCE")
print(f"{'=' * 70}")

# Create sample data (10 features matching NAB)
np.random.seed(42)
sample = np.random.randn(1, 10).astype(np.float32)
sample_scaled = scaler.transform(sample)

print(f"\nSample input shape: {sample_scaled.shape}")

# Get predictions
msif_pred = msif_model.predict(sample_scaled, verbose=0)[0][0]
ple_pred = ple_model.predict(sample_scaled, verbose=0)[0][0]

msif_threshold = metadata["optimal_thresholds"]["msif_lstm"]
ple_threshold = metadata["optimal_thresholds"]["ple_gru"]

msif_anomaly = 1 if msif_pred >= msif_threshold else 0
ple_anomaly = 1 if ple_pred >= ple_threshold else 0
ensemble_anomaly = 1 if ((msif_pred + ple_pred) / 2) >= 0.325 else 0

print(f"\n📊 Predictions:")
print(f"  MSIF-LSTM:")
print(f"    Probability: {msif_pred:.4f}")
print(f"    Threshold: {msif_threshold:.3f}")
print(f"    Prediction: {'🚨 ANOMALY' if msif_anomaly else '✅ NORMAL'}")
print(f"\n  PLE-GRU:")
print(f"    Probability: {ple_pred:.4f}")
print(f"    Threshold: {ple_threshold:.3f}")
print(f"    Prediction: {'🚨 ANOMALY' if ple_anomaly else '✅ NORMAL'}")
print(f"\n  Ensemble (Average):")
print(f"    Probability: {(msif_pred + ple_pred) / 2:.4f}")
print(f"    Threshold: 0.325")
print(f"    Prediction: {'🚨 ANOMALY' if ensemble_anomaly else '✅ NORMAL'}")

# ============================================================================
# TEST WITH MULTIPLE SAMPLES
# ============================================================================

print(f"\n{'=' * 70}")
print("🔄 BATCH INFERENCE TEST")
print(f"{'=' * 70}")

batch = np.random.randn(10, 10).astype(np.float32)
batch_scaled = scaler.transform(batch)

msif_batch = msif_model.predict(batch_scaled, verbose=0).flatten()
ple_batch = ple_model.predict(batch_scaled, verbose=0).flatten()

msif_anomalies = (msif_batch >= msif_threshold).sum()
ple_anomalies = (ple_batch >= ple_threshold).sum()
ensemble_anomalies = (((msif_batch + ple_batch) / 2) >= 0.325).sum()

print(f"\nProcessed 10 samples:")
print(f"  MSIF-LSTM anomalies: {msif_anomalies}/10")
print(f"  PLE-GRU anomalies: {ple_anomalies}/10")
print(f"  Ensemble anomalies: {ensemble_anomalies}/10")

print(f"\n{'=' * 70}")
print("✅ INFERENCE TEST COMPLETE!")
print(f"{'=' * 70}")
print(f"{'=' * 70}")
print(f"{'='*70}")
