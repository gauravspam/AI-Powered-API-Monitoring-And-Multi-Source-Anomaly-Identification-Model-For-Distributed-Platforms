import os
import pickle
from datetime import datetime

import numpy as np
import tensorflow as tf
from flask import Flask, jsonify, request

app = Flask(__name__)

# --- CONFIG ---
SEQ_LEN = 100  # Models expect sequence length of 100

# Context-aware fusion thresholds
HIGH_AGREEMENT_THRESHOLD = 0.85
MODERATE_AGREEMENT_THRESHOLD = 0.60

SEVERITY_THRESHOLDS = {
    'CRITICAL': 0.8,
    'HIGH': 0.6,
    'MEDIUM': 0.4,
    'LOW': 0.2
}

WEIGHT_RULES = {
    'peak_hours': {'msif': 0.40, 'ple': 0.60},
    'off_hours': {'msif': 0.55, 'ple': 0.45},
    'cpu_endpoint': {'msif': 0.50, 'ple': 0.50},
    'api_endpoint': {'msif': 0.35, 'ple': 0.65},
    'high_traffic': {'msif': 0.30, 'ple': 0.70},
    'low_traffic': {'msif': 0.50, 'ple': 0.50}
}

# --- STATE ---
MODEL_MSIF = None
MODEL_PLE = None
SCALER_MSIF = None
SCALER_PLE = None
prediction_count = 0
anomaly_count = 0

# --- LOAD MODELS ---
print("⏳ Loading Models...")

try:
    MODEL_MSIF = tf.keras.models.load_model(
        'models/microservices/msif_lstm_model.keras',
        compile=False
    )
    with open('models/microservices/msif_lstm_scaler.pkl', 'rb') as f:
        SCALER_MSIF = pickle.load(f)
    print(f"✅ MSIF-LSTM Model Loaded (input shape: {MODEL_MSIF.input_shape})")
except Exception as e:
    print(f"❌ Failed to load MSIF-LSTM model: {e}")

try:
    MODEL_PLE = tf.keras.models.load_model(
        'models/microservices/ple_gru_model.keras',
        compile=False
    )
    with open('models/microservices/ple_gru_scaler.pkl', 'rb') as f:
        SCALER_PLE = pickle.load(f)
    print(f"✅ PLE-GRU Model Loaded (input shape: {MODEL_PLE.input_shape})")
except Exception as e:
    print(f"❌ Failed to load PLE-GRU model: {e}")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "models_loaded": {
            "msif": MODEL_MSIF is not None,
            "ple": MODEL_PLE is not None
        },
        "total_predictions": prediction_count,
        "anomalies_detected": anomaly_count
    })

def expand_to_21_features(data):
    """
    Expand 10 raw features to 21 aggregated features expected by models.

    Maps incoming features to the 21-feature format the models were trained on:
    - cpu_usage → cpu_usage_{system,total,user}_{mean,std,max} (9 features)
    - memory_usage → memory_{usage,working_set}_{mean,std,max} (6 features)
    - network_io → {rx,tx}_bytes_{sum,mean,std} (6 features)

    Since we only have single-point data, we approximate:
    - mean = value
    - std = small variance (5% of mean)
    - max = value * 1.1 (slightly higher)
    """
    cpu = float(data.get('cpu_usage', 0))
    mem = float(data.get('memory_usage', 0))
    net_io = float(data.get('network_io', 0))

    # Approximate statistics from single values
    cpu_std = cpu * 0.05  # 5% standard deviation
    mem_std = mem * 0.05
    net_std = net_io * 0.05

    # Build 21-feature vector matching training data structure
    features_21 = [
        # CPU system (mean, std, max)
        cpu, cpu_std, cpu * 1.1,
        # CPU total (mean, std, max)
        cpu, cpu_std, cpu * 1.1,
        # CPU user (mean, std, max)
        cpu, cpu_std, cpu * 1.1,
        # Memory usage (mean, std, max)
        mem, mem_std, mem * 1.1,
        # Memory working set (mean, std, max)
        mem, mem_std, mem * 1.1,
        # RX bytes (sum, mean, std)
        net_io, net_io, net_std,
        # TX bytes (sum, mean, std)
        net_io, net_io, net_std
    ]

    return np.array(features_21, dtype=np.float32)

def calculate_dynamic_weights(context):
    """Calculate context-aware weights for ensemble fusion."""
    hour = context.get('hour_of_day', 12)
    endpoint_type = context.get('endpoint_type', 'api')
    traffic_level = context.get('traffic_level', 'medium')

    if 9 <= hour <= 17:
        base_weights = WEIGHT_RULES['peak_hours']
    else:
        base_weights = WEIGHT_RULES['off_hours']

    if endpoint_type == 'cpu_intensive':
        endpoint_adj = WEIGHT_RULES['cpu_endpoint']
    else:
        endpoint_adj = WEIGHT_RULES['api_endpoint']

    if traffic_level == 'high':
        traffic_adj = WEIGHT_RULES['high_traffic']
    else:
        traffic_adj = WEIGHT_RULES['low_traffic']

    final_msif = (0.5 * base_weights['msif'] +
                  0.25 * endpoint_adj['msif'] +
                  0.25 * traffic_adj['msif'])
    final_ple = 1.0 - final_msif

    print(f"🔧 Dynamic weights: MSIF={final_msif:.2f}, PLE={final_ple:.2f}")

    return {'msif': final_msif, 'ple': final_ple}

def fuse_predictions(msif_score, ple_score, weights):
    """Fuse predictions using confidence-based strategy."""
    model_agreement = 1.0 - abs(msif_score - ple_score)

    if model_agreement >= HIGH_AGREEMENT_THRESHOLD:
        hybrid_score = (weights['msif'] * msif_score +
                       weights['ple'] * ple_score)
        fusion_method = "weighted_agreement"
        print(f"✓ High agreement ({model_agreement:.2f}) - weighted average")
    elif model_agreement >= MODERATE_AGREEMENT_THRESHOLD:
        hybrid_score = max(msif_score, ple_score)
        fusion_method = "conservative_max"
        print(f"⚠️  Moderate agreement ({model_agreement:.2f}) - using max")
    else:
        hybrid_score = max(msif_score, ple_score)
        fusion_method = "conflict_detected"
        print(f"🚨 Conflict! MSIF={msif_score:.3f}, PLE={ple_score:.3f}")

    return hybrid_score, fusion_method, model_agreement

def calculate_severity(hybrid_score):
    """Calculate severity level based on hybrid score."""
    if hybrid_score > SEVERITY_THRESHOLDS['CRITICAL']:
        return "CRITICAL", 0.95
    elif hybrid_score > SEVERITY_THRESHOLDS['HIGH']:
        return "HIGH", 0.85
    elif hybrid_score > SEVERITY_THRESHOLDS['MEDIUM']:
        return "MEDIUM", 0.75
    elif hybrid_score > SEVERITY_THRESHOLDS['LOW']:
        return "LOW", 0.65
    else:
        return "NORMAL", 0.90

@app.route('/predict', methods=['POST'])
def predict():
    """Anomaly prediction endpoint."""
    global prediction_count, anomaly_count

    if not MODEL_MSIF and not MODEL_PLE:
        return jsonify({"error": "No models loaded"}), 503

    data = request.json

    try:
        start_time = datetime.now()

        # 1. Expand 10 features to 21 features
        features_21 = expand_to_21_features(data)
        print(f"📊 Expanded to 21 features (first 6): {features_21[:6]}")

        # 2. Create sequence of length 100 by repeating the single point
        sequence = np.tile(features_21, (SEQ_LEN, 1))
        noise = np.random.normal(0, 0.01, sequence.shape)
        sequence = sequence + noise

        # 3. Get individual model predictions
        msif_score = 0.0
        ple_score = 0.0

        if MODEL_MSIF:
            scaled_msif = SCALER_MSIF.transform(sequence)
            input_msif = scaled_msif.reshape(1, SEQ_LEN, 21)
            pred_msif = MODEL_MSIF.predict(input_msif, verbose=0)
            msif_score = float(pred_msif[0][0])
            print(f"🔵 MSIF-LSTM raw output: {msif_score:.4f}")

        if MODEL_PLE:
            scaled_ple = SCALER_PLE.transform(sequence)
            input_ple = scaled_ple.reshape(1, SEQ_LEN, 21)
            pred_ple = MODEL_PLE.predict(input_ple, verbose=0)
            ple_score = float(pred_ple[0][0])
            print(f"🟢 PLE-GRU raw output: {ple_score:.4f}")

        # 4. Calculate context-aware weights
        context = data.get('context', {})
        if 'hour_of_day' not in context and 'hour_of_day' in data:
            context['hour_of_day'] = int(data['hour_of_day'])

        weights = calculate_dynamic_weights(context)

        # 5. Fuse predictions
        if MODEL_MSIF and MODEL_PLE:
            hybrid_score, fusion_method, model_agreement = fuse_predictions(
                msif_score, ple_score, weights
            )
        elif MODEL_MSIF:
            hybrid_score = msif_score
            fusion_method = "msif_only"
            model_agreement = 1.0
        elif MODEL_PLE:
            hybrid_score = ple_score
            fusion_method = "ple_only"
            model_agreement = 1.0
        else:
            return jsonify({"error": "No models available"}), 503

        # 6. Calculate severity and confidence
        severity, base_confidence = calculate_severity(hybrid_score)

        if MODEL_MSIF and MODEL_PLE:
            score_uncertainty = abs(msif_score - ple_score)
            confidence = max(0.5, base_confidence - (score_uncertainty * 0.3))
        else:
            confidence = base_confidence

        # 7. Convert confidence to string for Java backend
        if confidence >= 0.85:
            confidence_str = "HIGH"
        elif confidence >= 0.65:
            confidence_str = "MEDIUM"
        else:
            confidence_str = "LOW"

        # 8. Update statistics
        prediction_count += 1
        if hybrid_score > SEVERITY_THRESHOLDS['MEDIUM']:
            anomaly_count += 1

        # 9. Calculate processing time
        processing_time_ms = (datetime.now() - start_time).total_seconds() * 1000

        # 10. Build response matching Java MLPredictionResponse expectations
        response = {
            "msif_score": round(msif_score, 4),          # snake_case for Java
            "ple_score": round(ple_score, 4),            # snake_case for Java
            "hybrid_score": round(hybrid_score, 4),      # snake_case for Java
            "severity": severity,
            "confidence": confidence_str,                 # String: "HIGH", "MEDIUM", "LOW"
            "fusion_method": fusion_method,              # snake_case for Java
            "weights_used": {                            # snake_case for Java
                "msif": round(weights['msif'], 2),
                "ple": round(weights['ple'], 2)
            },
            "models_loaded": True,                       # snake_case for Java
            "processing_time_ms": round(processing_time_ms, 2),  # snake_case
            "trace_id": data.get('context', {}).get('trace_id', None)
        }

        print(f"✅ Prediction: hybrid={hybrid_score:.4f}, severity={severity}, "
              f"confidence={confidence_str}, method={fusion_method}, "
              f"time={processing_time_ms:.1f}ms")

        return jsonify(response)

    except Exception as e:
        print(f"❌ Prediction Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("🚀 Starting ML Service on port 9000...")
    print(f"   Models: MSIF-LSTM {'✅' if MODEL_MSIF else '❌'}, "
          f"PLE-GRU {'✅' if MODEL_PLE else '❌'}")
    print(f"   Expected input: 10 raw features → expanded to 21 aggregated features")
    print(f"   Sequence length: {SEQ_LEN} timesteps")
    app.run(host='0.0.0.0', port=9000, debug=False)
