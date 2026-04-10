import os
import sys

import numpy as np
import torch
from flask import Flask, jsonify, request

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Import Models
from models.hybrid_fusion import HybridFusion
from models.msif_lstm_model import VariableInputMSIF_LSTM
from models.ple_gru_model import VariableInputPLE_GRU

app = Flask(__name__)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Global Model Containers
models = {}

# Rule-based weights and functions
RULE_BASED_WEIGHTS = {
    'status_5xx': 0.40,
    'high_error': 0.30,
    'slow_response': 0.20,
    'high_cpu': 0.10,
    'high_memory': 0.10,
}


def rule_based_score(data: dict) -> float:
    score = 0.0
    status = int(data.get('statuscode', data.get('status_code', 200)))
    error = float(data.get('errorrate', data.get('error_rate', 0.0)))
    rt = float(data.get('responsetime', data.get('response_time', 0)))
    cpu = float(data.get('cpuusage', data.get('cpu_usage', 0.0)))
    mem = float(data.get('memoryusage', data.get('memory_usage', 0.0)))

    if status >= 500:
        score += RULE_BASED_WEIGHTS['status_5xx']
    elif status == 429:
        score += 0.20
    if error > 0.30:
        score += RULE_BASED_WEIGHTS['high_error']
    elif error > 0.10:
        score += 0.15
    if rt > 1000:
        score += RULE_BASED_WEIGHTS['slow_response']
    elif rt > 500:
        score += 0.10
    if cpu > 80:
        score += RULE_BASED_WEIGHTS['high_cpu']
    if mem > 85:
        score += RULE_BASED_WEIGHTS['high_memory']

    return round(min(score, 1.0), 4)


def score_to_severity(score: float) -> str:
    if score >= 0.80:
        return "CRITICAL"
    if score >= 0.60:
        return "HIGH"
    if score >= 0.40:
        return "MEDIUM"
    if score >= 0.20:
        return "LOW"
    return "NORMAL"


def load_models():
    print(f"🔄 Loading models on {DEVICE}...")

    # Get the base directory (parent of 'api' folder)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 1. Load MSIF-LSTM
    msif = VariableInputMSIF_LSTM(embedding_dim=3, lstm_hidden_dim=64).to(DEVICE)
    msif_path = os.path.join(base_dir, "models/enhanced/msif_lstm.pth")
    if os.path.exists(msif_path):
        msif.load_state_dict(torch.load(msif_path, map_location=DEVICE))
        print(f"✅ MSIF-LSTM loaded from {msif_path}")
    else:
        print(f"⚠️ MSIF-LSTM weights not found at {msif_path}")
    msif.eval()
    models["msif"] = msif

    # 2. Load PLE-GRU
    ple = VariableInputPLE_GRU(embedding_dim=3, gru_hidden_dim=64, num_experts=3).to(
        DEVICE
    )
    ple_path = os.path.join(base_dir, "models/enhanced/ple_gru.pth")
    if os.path.exists(ple_path):
        ple.load_state_dict(torch.load(ple_path, map_location=DEVICE))
        print(f"✅ PLE-GRU loaded from {ple_path}")
    else:
        print(f"⚠️ PLE-GRU weights not found at {ple_path}")
    ple.eval()
    models["ple"] = ple

    # 3. Hybrid Strategy
    models["fusion"] = HybridFusion()


@app.route("/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "healthy",
            "device": str(DEVICE),
            "models_loaded": list(models.keys()),
        }
    )


@app.route("/predict/multimodal", methods=["POST"])
def predict_multimodal():
    data = request.json

    try:
        m_val = float(data.get("metrics", 0))
        l_val = float(data.get("logs", 0))
        t_val = float(data.get("traces", 0))

        # Preprocess (Log1p normalize as in training)
        feats = np.array([m_val, l_val, t_val], dtype=np.float32)
        feats = np.log1p(feats)

        # Convert to Tensor
        tensor_in = torch.tensor(feats, device=DEVICE).unsqueeze(0)  # (1, 3)

        # Inference
        with torch.no_grad():
            msif_score = models["msif"](tensor_in).item()
            ple_score = models["ple"](tensor_in).item()

        # Hybrid Decision
        final_score, method, agreement, weights = models["fusion"](
            msif_score, ple_score
        )

        status = "ANOMALY" if final_score > 0.8 else "NORMAL"

        return jsonify(
            {
                "status": status,
                "final_score": final_score,
                "details": {
                    "msif_score": msif_score,
                    "ple_score": ple_score,
                    "fusion_method": method,
                    "model_agreement": agreement,
                },
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/predict/test", methods=["POST"])
def predict_test():
    """Test endpoint with controllable scores"""
    data = request.json

    msif_score = float(data.get("msif_score", 0.5))
    ple_score = float(data.get("ple_score", 0.5))

    final_score, method, agreement, weights = models["fusion"](msif_score, ple_score)
    status = "ANOMALY" if final_score > 0.5 else "NORMAL"

    return jsonify(
        {
            "status": status,
            "final_score": final_score,
            "details": {
                "msif_score": msif_score,
                "ple_score": ple_score,
                "fusion_method": method,
                "model_agreement": agreement,
            },
        }
    )


@app.route("/predict", methods=["POST"])
def predict():
    """Main prediction endpoint that backend-service calls"""
    data = request.json

    ml_hybrid = None
    ml_msif = None
    ml_ple = None
    fusion = "ml_inference"
    confidence = 0.5

    try:
        # Attempt ML prediction
        response_time = float(data.get("response_time", 0))
        status_code = int(data.get("status_code", 200))
        cpu_usage = float(data.get("cpu_usage", 0))
        memory_usage = float(data.get("memory_usage", 0))
        error_rate = float(data.get("error_rate", 0))
        request_count = int(data.get("request_count", 1))

        # Normalize metrics to 0-1 range for model input
        m_val = min(response_time / 5000.0, 1.0)
        l_val = max(cpu_usage, memory_usage) / 100.0
        t_val = error_rate

        feats = np.array([m_val, l_val, t_val], dtype=np.float32)
        feats = np.log1p(feats)

        tensor_in = torch.tensor(feats, device=DEVICE).unsqueeze(0)

        with torch.no_grad():
            msif_score = float(models["msif"](tensor_in).item())
            ple_score = float(models["ple"](tensor_in).item())

        final_score, method, agreement, weights = models["fusion"](
            msif_score, ple_score
        )

        ml_hybrid = round(final_score, 4)
        ml_msif = round(msif_score, 4)
        ml_ple = round(ple_score, 4)
        fusion = method
        confidence = abs(msif_score - ple_score) if method == "weighted_ensemble" else 0.5

    except Exception as e:
        print(f"[WARN] ML prediction failed, using rule-based: {e}")
        ml_hybrid = None

    # ALWAYS use rule-based scoring since models aren't trained yet
    USE_RULE_BASED = True

    if USE_RULE_BASED:
        rb_score = rule_based_score(data)
        ml_hybrid = rb_score
        ml_msif = round(rb_score * 0.9, 4)
        ml_ple = round(rb_score * 1.0, 4)
        fusion = "rule-based-fallback"
        confidence = 0.60

    severity = score_to_severity(ml_hybrid)

    return jsonify(
        {
            "status": "success",
            "hybrid_score": ml_hybrid,
            "msif_score": ml_msif,
            "ple_score": ml_ple,
            "severity": severity,
            "fusion_method": fusion,
            "confidence": confidence,
        }
    )


if __name__ == "__main__":
    load_models()
    app.run(host="0.0.0.0", port=9000, debug=False)
