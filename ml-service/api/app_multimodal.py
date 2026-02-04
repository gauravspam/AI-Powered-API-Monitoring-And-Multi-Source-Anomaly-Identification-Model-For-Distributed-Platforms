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


if __name__ == "__main__":
    load_models()
    app.run(host="0.0.0.0", port=9000, debug=False)
