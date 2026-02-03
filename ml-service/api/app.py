import os
import time
import pickle
import numpy as np
import pandas as pd
import tensorflow as tf
from flask import Flask, request, jsonify
from collections import deque

app = Flask(__name__)

# --- CONFIG ---
SEQ_LEN_MICRO = 100
SEQ_LEN_NAB = 10  # If we use NAB later
FEATURE_COLS = [
    'cpu_usage_system_mean', 'cpu_usage_system_std', 'cpu_usage_system_max',
    'cpu_usage_total_mean', 'cpu_usage_total_std', 'cpu_usage_total_max',
    'cpu_usage_user_mean', 'cpu_usage_user_std', 'cpu_usage_user_max',
    'memory_usage_mean', 'memory_usage_std', 'memory_usage_max',
    'memory_working_set_mean', 'memory_working_set_std', 'memory_working_set_max',
    'rx_bytes_sum', 'rx_bytes_mean', 'rx_bytes_std',
    'tx_bytes_sum', 'tx_bytes_mean', 'tx_bytes_std'
]

# --- STATE ---
# Buffer to hold recent metrics: { "endpoint_name": deque(maxlen=100) }
METRIC_BUFFERS = {}

# --- LOAD ARTIFACTS ---
print("⏳ Loading Models...")
try:
    MODEL_MICRO = tf.keras.models.load_model('models/microservices/msif_lstm_model.keras', compile=False)
    with open('models/microservices/msif_lstm_scaler.pkl', 'rb') as f:
        SCALER_MICRO = pickle.load(f)
    print("✅ Microservices Model Loaded")
except Exception as e:
    print(f"❌ Failed to load Microservices model: {e}")
    MODEL_MICRO = None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "models_loaded": MODEL_MICRO is not None})

@app.route('/predict', methods=['POST'])
def predict():
    """
    Receives a single log record from Java Backend.
    Buffers it.
    Returns anomaly prediction if buffer is full.
    """
    if not MODEL_MICRO:
        return jsonify({"error": "Model not loaded"}), 503

    data = request.json
    endpoint = data.get('endpoint', 'default')

    # 1. Extract relevant features from the single log
    # We need to map the incoming simple metrics to the 21 complex features the model expects.
    # For this demo, we will duplicate/approximate the missing stats.

    try:
        # Incoming: cpu_usage, memory_usage, network_io, disk_io
        cpu = float(data.get('cpu_usage', 0))
        mem = float(data.get('memory_usage', 0))
        net_in = float(data.get('network_io', 0))
        net_out = float(data.get('network_io', 0)) # approx

        # Construct a 21-feature vector (Approximation for demo)
        # Real world: You'd calculate rolling stats here or in Java
        features = [
            cpu, 0, cpu, # cpu_system (mean, std, max)
            cpu, 0, cpu, # cpu_total
            cpu, 0, cpu, # cpu_user
            mem, 0, mem, # mem_usage
            mem, 0, mem, # mem_working_set
            net_in, net_in, 0, # rx
            net_out, net_out, 0 # tx
        ]

        # 2. Add to Buffer
        if endpoint not in METRIC_BUFFERS:
            METRIC_BUFFERS[endpoint] = deque(maxlen=SEQ_LEN_MICRO)

        METRIC_BUFFERS[endpoint].append(features)

        # 3. Predict if enough data
        msif_score = 0.0
        severity = "LOW"

        if len(METRIC_BUFFERS[endpoint]) == SEQ_LEN_MICRO:
            # Convert to numpy
            raw_seq = np.array(METRIC_BUFFERS[endpoint]) # shape (100, 21)

            # Scale
            scaled_seq = SCALER_MICRO.transform(raw_seq)

            # Reshape (1, 100, 21)
            input_seq = scaled_seq.reshape(1, SEQ_LEN_MICRO, 21)

            # Predict
            pred = MODEL_MICRO.predict(input_seq, verbose=0)
            msif_score = float(pred[0][0])

            # Determine Severity
            if msif_score > 0.8: severity = "CRITICAL"
            elif msif_score > 0.6: severity = "HIGH"
            elif msif_score > 0.4: severity = "MEDIUM"

        return jsonify({
            "msifScore": msif_score,
            "pleScore": 0.0, # Placeholder
            "hybridScore": msif_score,
            "severity": severity,
            "confidence": 0.95 if len(METRIC_BUFFERS[endpoint]) == SEQ_LEN_MICRO else 0.0,
            "fusionMethod": "MSIF_ONLY"
        })

    except Exception as e:
        print(f"Prediction Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000) # Port matches Java config
