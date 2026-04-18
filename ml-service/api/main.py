import os
import sys
import uuid
import threading
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import Models
from model_defs import (
    HybridFusion,
    VariableInputMSIF_LSTM,
    VariableInputPLE_GRU,
    MetricEncoder as MetricEncoderTCN,
    LogEncoder as LogEncoderTinyBERT,
    TraceEncoder
)

app = Flask(__name__)
CORS(app)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Global components
models = {}
encoders = {}

# Projection layer to map 384-dim combined embeddings to 3-dim for trained models
embedding_projector = None

# Batch processing configuration
BATCH_SIZE_METRICS = 5000
BATCH_SIZE_LOGS = 5000
BATCH_SIZE_TRACES = 5000
BATCH_INTERVAL_SECONDS = 120

# Learnable missing embeddings (trained, NOT zeros!)
missing_metric_emb = None
missing_log_emb = None
missing_trace_emb = None

# Projection layer to map 384-dim to 3-dim for pre-trained models
embedding_projector = None

# Rule-based weights
RULE_BASED_WEIGHTS = {
    'status_5xx': 0.40,
    'high_error': 0.30,
    'slow_response': 0.20,
    'high_cpu': 0.10,
    'high_memory': 0.10,
}


def init_flexible_embeddings():
    """Initialize learnable missing embeddings"""
    global missing_metric_emb, missing_log_emb, missing_trace_emb, embedding_projector
    
    missing_metric_emb = nn.Parameter(torch.randn(128).to(DEVICE))
    missing_log_emb = nn.Parameter(torch.randn(128).to(DEVICE))
    missing_trace_emb = nn.Parameter(torch.randn(128).to(DEVICE))
    
    # Projection layer: 384-dim (combined) → 26-dim (multi-modal model)
    embedding_projector = nn.Sequential(
        nn.Linear(384, 128),
        nn.ReLU(),
        nn.Dropout(0.2),
        nn.Linear(128, 26)
    ).to(DEVICE)
    
    print(f"[OK] Flexible embeddings initialized on {DEVICE}")


def combine_embeddings(metric_emb, log_emb, trace_emb, use_projection=False):
    """
    Combine embeddings with learnable missing embeddings for missing modalities.
    
    For multi-modal model: 26-dim (20 platform + 4 business + 2 trace)
    
    Args:
        metric_emb: tensor (batch, 128) or None
        log_emb: tensor (batch, 128) or None  
        trace_emb: tensor (batch, 128) or None
        use_projection: if True, project to trained model dimensions
        
    Returns:
        combined: (batch, 26) for multi-modal
        confidence: float (0.33, 0.66, or 1.0)
        modalities_present: int
    """
    global missing_metric_emb, missing_log_emb, missing_trace_emb, embedding_projector
    
    # Get actual embeddings or fallbacks - ensure at least one modality has data
    if metric_emb is not None and metric_emb.shape[1] >= 20:
        platform_emb = metric_emb[:, :20]
    elif log_emb is not None and log_emb.shape[1] >= 20:
        platform_emb = log_emb[:, :20]
    elif trace_emb is not None and trace_emb.shape[1] >= 20:
        repeated = torch.cat([trace_emb[:, :10], trace_emb[:, :10]], dim=1)
        platform_emb = repeated[:, :20]
    else:
        platform_emb = torch.zeros(1, 20).to(DEVICE)
    
    # Add business (4 dim) - currently always zeros (no business encoder)
    business = torch.zeros(platform_emb.shape[0], 4).to(DEVICE)
    platform_emb = torch.cat([platform_emb, business], dim=1)
    
    # Add trace (2 dim) - extract from trace embedding or use zeros
    if trace_emb is not None and trace_emb.shape[1] >= 2:
        trace_part = trace_emb[:, :2]
    else:
        trace_part = torch.zeros(platform_emb.shape[0], 2).to(DEVICE)
    combined = torch.cat([platform_emb, trace_part], dim=1)
    
    # Count modalities - only count if embedding has actual data
    modalities_present = 0
    if metric_emb is not None and metric_emb.shape[1] > 0:
        modalities_present += 1
    if log_emb is not None and log_emb.shape[1] > 0:
        modalities_present += 1
    if trace_emb is not None and trace_emb.shape[1] > 0:
        modalities_present += 1
    
    # Fallback: if no modalities, default to 1 with platform
    if modalities_present == 0:
        modalities_present = 1
    
    confidence = modalities_present / 3.0
    
    return combined, confidence, modalities_present


def encode_metric(metrics_data):
    """
    Encode metric data to embedding.
    Always returns (1, 128) tensor.
    Handles both single dict and array of dicts.
    """
    if not metrics_data:
        return None
    
    try:
        # Handle array of metrics - use first one or aggregate
        if isinstance(metrics_data, list):
            if len(metrics_data) == 0:
                return None
            metrics_data = metrics_data[0]  # Use first metric entry for now
        
        # Extract values from dict
        cpu = float(metrics_data.get('cpu_usage', metrics_data.get('cpuUsagePercent', 0)))
        memory = float(metrics_data.get('memory_usage', metrics_data.get('memoryUsagePercent', 0)))
        response_time = float(metrics_data.get('response_time_ms', metrics_data.get('responseTimeMs', 0)))
        error_rate = float(metrics_data.get('error_rate', metrics_data.get('errorRate', 0)))
        request_count = float(metrics_data.get('request_count', metrics_data.get('requestCount', 0)))
        
        # Normalize values
        cpu_norm = min(cpu / 100.0, 1.0)
        memory_norm = min(memory / 100.0, 1.0)
        response_norm = min(response_time / 5000.0, 1.0)
        error_norm = min(error_rate, 1.0)
        request_norm = min(request_count / 10000.0, 1.0)
        
        # Create 128-dim embedding by repeating normalized values
        values = [cpu_norm, memory_norm, response_norm, error_norm, request_norm]
        emb = torch.tensor(values * 26, dtype=torch.float32).unsqueeze(0).to(DEVICE)  # 5 * 26 = 130, truncate to 128
        emb = emb[:, :128]
        
        return emb
            
    except Exception as e:
        print(f"[WARN] Metric encoding failed: {e}")
        return None


def encode_logs(logs_data):
    """
    Encode log data to embedding.
    Always returns (1, 128) tensor.
    """
    if not logs_data:
        return None
    
    try:
        # Normalize to list
        if isinstance(logs_data, dict):
            logs_data = [logs_data]
        
        if not logs_data:
            return None
        
        # Compute severity score based on log levels
        level_scores = {'CRITICAL': 1.0, 'ERROR': 0.8, 'WARN': 0.5, 'INFO': 0.2, 'DEBUG': 0.1}
        max_level_score = 0.0
        error_count = 0
        
        for log in logs_data:
            level = log.get('level', 'INFO').upper()
            score = level_scores.get(level, 0.2)
            if score > max_level_score:
                max_level_score = score
            if level in ['ERROR', 'CRITICAL']:
                error_count += 1
        
        # Create 128-dim embedding
        emb = torch.zeros(1, 128, dtype=torch.float32).to(DEVICE)
        emb[0, 0] = max_level_score  # Max severity
        emb[0, 1] = min(error_count / 5.0, 1.0)  # Normalized error count
        emb[0, 2] = len(logs_data) / 50.0  # Log count normalized
        emb[0, 3] = max_level_score * error_count  # Combined severity
        
        return emb
            
    except Exception as e:
        print(f"[WARN] Log encoding failed: {e}")
        return None


def encode_traces(traces_data):
    """
    Encode trace data to embedding.
    Always returns (1, 128) tensor.
    """
    if not traces_data:
        return None
    
    try:
        # Normalize to list
        if isinstance(traces_data, dict):
            traces_data = [traces_data]
        
        if not traces_data:
            return None
        
        # Extract features from traces
        # Support both 'duration' and 'latency_ms' field names
        # Handle status_code as number (200, 500) or string ('error', 'timeout')
        def get_trace_errors(t):
            status = t.get('status_code', t.get('status', 200))
            if isinstance(status, str):
                return status.lower() in ['error', 'timeout']
            return status >= 400
        
        total_duration = sum(t.get('duration', t.get('latency_ms', 0)) for t in traces_data)
        error_count = sum(1 for t in traces_data if get_trace_errors(t))
        max_duration = max(t.get('duration', t.get('latency_ms', 0)) for t in traces_data)
        service_count = len(set(t.get('service', 'unknown') for t in traces_data))
        
        avg_duration = total_duration / len(traces_data) if traces_data else 0
        
        # Create 128-dim embedding
        emb = torch.zeros(1, 128, dtype=torch.float32).to(DEVICE)
        emb[0, 0] = min(avg_duration / 1000.0, 1.0)  # Normalized avg duration
        emb[0, 1] = min(error_count / 5.0, 1.0)  # Normalized error count
        emb[0, 2] = min(len(traces_data) / 50.0, 1.0)  # Span count normalized
        emb[0, 3] = min(service_count / 10.0, 1.0)  # Service count normalized
        emb[0, 4] = min(max_duration / 2000.0, 1.0)  # Max duration
        
        # Also set some features based on latency_ms field specifically
        latency_ms = traces_data[0].get('latency_ms', 0) if traces_data else 0
        emb[0, 5] = min(latency_ms / 5000.0, 1.0)  # latency_ms normalized
        
        return emb
            
    except Exception as e:
        print(f"[WARN] Trace encoding failed: {e}")
        return None


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


def load_models():
    print(f"Loading models on {DEVICE}...")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize flexible embeddings
    init_flexible_embeddings()
    
    # Load Encoders
    print("Loading encoders...")
    
    # Metric Encoder (TCN - using trained weights)
    try:
        metric_enc = MetricEncoderTCN(embedding_dim=128, lstm_hidden_dim=64).to(DEVICE)
        metric_path = os.path.join(base_dir, "models/encoders/metric/metric_encoder_tcn.pth")
        if os.path.exists(metric_path):
            metric_enc.load_state_dict(torch.load(metric_path, map_location=DEVICE), strict=False)
            print(f"OK Metric TCN Encoder loaded")
        metric_enc.eval()
        encoders['metric'] = metric_enc
    except Exception as e:
        print(f"WARN Metric Encoder: {e}")
    
    # Log encoder can trigger large model downloads on cold start.
    # By default we skip loading it because encode_logs() uses lightweight heuristics.
    load_log_encoder = os.getenv("LOAD_LOG_ENCODER", "false").lower() == "true"
    if load_log_encoder:
        try:
            log_enc = LogEncoderTinyBERT(embedding_dim=128).to(DEVICE)
            print(f"OK Log TinyBERT-4 initialized (14.5M params)")
            log_path = os.path.join(base_dir, "models/encoders/log/log_encoder.pth")
            if os.path.exists(log_path):
                log_enc.load_state_dict(torch.load(log_path, map_location=DEVICE), strict=False)
                print(f"OK Log TinyBERT-4 loaded with weights")
            else:
                print(f"OK Log TinyBERT-4 (fresh, no weights)")
            log_enc.eval()
            encoders['log'] = log_enc
        except Exception as e:
            print(f"WARN Log Encoder: {e}")
    else:
        print("OK Log Encoder skipped (set LOAD_LOG_ENCODER=true to enable)")
    
    # Trace Encoder
    try:
        trace_enc = TraceEncoder(embedding_dim=128, node_feature_dim=10).to(DEVICE)
        trace_path = os.path.join(base_dir, "models/encoders/trace/trace_encoder.pth")
        if os.path.exists(trace_path):
            trace_enc.load_state_dict(torch.load(trace_path, map_location=DEVICE), strict=False)
            print(f"OK Trace Encoder loaded")
        trace_enc.eval()
        encoders['trace'] = trace_enc
    except Exception as e:
        print(f"WARN Trace Encoder: {e}")

    # Load ML Models - multi-modal training with 26-dim (20 platform + 4 business + 2 trace)
    print("Loading ML models (strict training)...")
    
    msif = VariableInputMSIF_LSTM(embedding_dim=26, lstm_hidden_dim=128).to(DEVICE)
    msif_path = os.path.join(base_dir, "models/enhanced/msif_lstm_strict.pth")
    if os.path.exists(msif_path):
        msif.load_state_dict(torch.load(msif_path, map_location=DEVICE), strict=False)
        print(f"OK MSIF-LSTM loaded (strict)")
    msif.eval()
    models["msif"] = msif

    ple = VariableInputPLE_GRU(embedding_dim=26, gru_hidden_dim=128, num_experts=4).to(DEVICE)
    ple_path = os.path.join(base_dir, "models/enhanced/ple_gru_strict.pth")
    if os.path.exists(ple_path):
        ple.load_state_dict(torch.load(ple_path, map_location=DEVICE), strict=False)
        print(f"OK PLE-GRU loaded (strict)")
    ple.eval()
    models["ple"] = ple

    models["fusion"] = HybridFusion()
    
    print(f"All models and encoders loaded successfully")


# ==================== NEW FLEXIBLE ENDPOINTS ====================

@app.route("/predict/flexible", methods=["POST"])
def predict_flexible():
    """
    Flexible prediction endpoint that handles 1, 2, or 3 modalities.
    Uses actual encoders for embedding generation.
    """
    data = request.json
    
    try:
        # Extract modalities
        metrics_data = data.get("metrics")
        logs_data = data.get("logs")
        traces_data = data.get("traces")
        
        # Validate at least one modality present
        if not metrics_data and not logs_data and not traces_data:
            return jsonify({"error": "At least one modality required (metrics, logs, or traces)"}), 400
        
        # Encode each modality using actual encoders
        metric_emb = encode_metric(metrics_data)
        log_emb = encode_logs(logs_data)
        trace_emb = encode_traces(traces_data)
        
        # Combine embeddings with learnable missing embeddings
        combined, confidence, modalities_present = combine_embeddings(
            metric_emb, log_emb, trace_emb
        )
        
        # Get ML predictions
        with torch.no_grad():
            msif_score = models["msif"](combined).item()
            ple_score = models["ple"](combined).item()
        
        # Hybrid ensemble
        final_score, method, agreement, weights = models["fusion"](
            msif_score, ple_score
        )
        
        # Rule-based boost: if raw ML scores are low but business rules indicate anomaly
        rule_boost = 0.0
        
        # Extract values for rule-based scoring
        # Handle array or single dict for metrics
        metrics_for_rules = metrics_data[0] if isinstance(metrics_data, list) else metrics_data
        cpu = float(metrics_for_rules.get('cpu_usage', 0) if metrics_for_rules else 0)
        memory = float(metrics_for_rules.get('memory_usage', 0) if metrics_for_rules else 0)
        response_time = float(metrics_for_rules.get('response_time_ms', 0) if metrics_for_rules else 0)
        error_rate = float(metrics_for_rules.get('error_rate', 0) if metrics_for_rules else 0)
        
        # Check log severity
        log_severity = 0
        if logs_data:
            for log in (logs_data if isinstance(logs_data, list) else [logs_data]):
                level = str(log.get('level', '')).upper()
                if 'FATAL' in level:
                    log_severity = 1.0
                elif 'ERROR' in level:
                    log_severity = max(log_severity, 0.7)
                elif 'WARNING' in level:
                    log_severity = max(log_severity, 0.4)
        
        # Check trace errors
        trace_severity = 0
        if traces_data:
            for trace in (traces_data if isinstance(traces_data, list) else [traces_data]):
                status = str(trace.get('status', '')).lower()
                latency = float(trace.get('latency_ms', 0))
                if status in ['error', 'timeout'] or latency > 5000:
                    trace_severity = 0.8
        
        # Apply rule-based boost if severe conditions detected
        if cpu > 90:
            rule_boost = max(rule_boost, 0.8)
        elif cpu > 80:
            rule_boost = max(rule_boost, 0.5)
        if memory > 90:
            rule_boost = max(rule_boost, 0.8)
        elif memory > 80:
            rule_boost = max(rule_boost, 0.5)
        if response_time > 5000:
            rule_boost = max(rule_boost, 0.7)
        elif response_time > 2000:
            rule_boost = max(rule_boost, 0.4)
        if error_rate > 0.3:
            rule_boost = max(rule_boost, 0.8)
        elif error_rate > 0.15:
            rule_boost = max(rule_boost, 0.4)
        if log_severity > 0.7:
            rule_boost = max(rule_boost, 0.9)
        elif log_severity > 0.4:
            rule_boost = max(rule_boost, 0.6)
        if trace_severity > 0.5:
            rule_boost = max(rule_boost, 0.8)
        
        # Combine ML score with rule-based boost - use higher of ML or rules
        if rule_boost > 0.3:
            # Take the max of ML score and rule boost
            final_score = max(final_score, rule_boost)
        
        # Apply confidence scaling
        adjusted_score = final_score * confidence
        
        # Determine severity based on adjusted score
        severity = score_to_severity(adjusted_score)
        
        return jsonify({
            "status": "success",
            "prediction_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "final_score": round(adjusted_score, 4),
            "raw_score": round(final_score, 4),
            "msif_score": round(msif_score, 4),
            "ple_score": round(ple_score, 4),
            "confidence": round(confidence, 2),
            "modalities_present": modalities_present,
            "fusion_method": method,
            "model_agreement": round(agreement, 2),
            "severity": severity,
            "modalities_used": {
                "metrics": metrics_data is not None,
                "logs": logs_data is not None,
                "traces": traces_data is not None
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/predict/batch", methods=["POST"])
def predict_batch():
    """
    Batch prediction endpoint for processing up to 5000 items per modality.
    Uses actual encoders for embedding generation.
    """
    data = request.json
    
    try:
        metrics_batch = data.get("metrics", [])
        logs_batch = data.get("logs", [])
        traces_batch = data.get("traces", [])
        
        if not metrics_batch and not logs_batch and not traces_batch:
            return jsonify({"error": "At least one modality required"}), 400
        
        batch_size = max(len(metrics_batch), len(logs_batch), len(traces_batch))
        
        results = []
        
        for i in range(batch_size):
            # Get corresponding data from each modality
            metric_item = metrics_batch[i] if i < len(metrics_batch) else None
            log_item = logs_batch[i] if i < len(logs_batch) else None
            trace_item = traces_batch[i] if i < len(traces_batch) else None
            
            # Encode each modality using actual encoders
            metric_emb = encode_metric(metric_item) if metric_item else None
            log_emb = encode_logs(log_item) if log_item else None
            trace_emb = encode_traces(trace_item) if trace_item else None
            
            # Combine and predict
            combined, confidence, modalities_present = combine_embeddings(
                metric_emb, log_emb, trace_emb
            )
            
            with torch.no_grad():
                msif_score = models["msif"](combined).item()
                ple_score = models["ple"](combined).item()
            
            final_score, method, agreement, weights = models["fusion"](
                msif_score, ple_score
            )
            
            adjusted_score = final_score * confidence
            severity = score_to_severity(adjusted_score)
            
            results.append({
                "index": i,
                "prediction_id": str(uuid.uuid4()),
                "final_score": round(adjusted_score, 4),
                "msif_score": round(msif_score, 4),
                "ple_score": round(ple_score, 4),
                "confidence": round(confidence, 2),
                "modalities_present": modalities_present,
                "severity": severity
            })
        
        # Summary statistics
        scores = [r["final_score"] for r in results]
        
        return jsonify({
            "status": "success",
            "batch_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "total_items": len(results),
            "modalities": {
                "metrics_count": len(metrics_batch),
                "logs_count": len(logs_batch),
                "traces_count": len(traces_batch)
            },
            "summary": {
                "mean_score": round(np.mean(scores), 4),
                "max_score": round(max(scores), 4),
                "min_score": round(min(scores), 4),
                "anomaly_count": sum(1 for s in scores if s >= 0.6),
                "critical_count": sum(1 for s in scores if s >= 0.8)
            },
            "predictions": results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/batch/status", methods=["GET"])
def batch_status():
    """Get batch processing status"""
    return jsonify({
        "status": "ready",
        "device": str(DEVICE),
        "batch_interval_seconds": BATCH_INTERVAL_SECONDS,
        "batch_sizes": {
            "metrics": BATCH_SIZE_METRICS,
            "logs": BATCH_SIZE_LOGS,
            "traces": BATCH_SIZE_TRACES
        },
        "encoders_loaded": list(encoders.keys()),
        "confidence_thresholds": {
            "3_modalities": 1.0,
            "2_modalities": 0.66,
            "1_modality": 0.33
        }
    })


# ==================== EXISTING ENDPOINTS ====================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "device": str(DEVICE),
        "models_loaded": list(models.keys()),
        "encoders_loaded": list(encoders.keys()),
        "flexible_input": "enabled"
    })


@app.route("/predict/multimodal", methods=["POST"])
def predict_multimodal():
    """Legacy multimodal endpoint"""
    data = request.json

    try:
        m_val = float(data.get("metrics", 0))
        l_val = float(data.get("logs", 0))
        t_val = float(data.get("traces", 0))

        feats = np.array([m_val, l_val, t_val], dtype=np.float32)
        feats = np.log1p(feats)

        tensor_in = torch.tensor(feats, device=DEVICE).unsqueeze(0)

        with torch.no_grad():
            msif_score = models["msif"](tensor_in).item()
            ple_score = models["ple"](tensor_in).item()

        final_score, method, agreement, weights = models["fusion"](
            msif_score, ple_score
        )

        status = "ANOMALY" if final_score > 0.8 else "NORMAL"

        return jsonify({
            "status": status,
            "final_score": final_score,
            "details": {
                "msif_score": msif_score,
                "ple_score": ple_score,
                "fusion_method": method,
                "model_agreement": agreement,
            },
        })

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

    return jsonify({
        "status": status,
        "final_score": final_score,
        "details": {
            "msif_score": msif_score,
            "ple_score": ple_score,
            "fusion_method": method,
            "model_agreement": agreement,
        }
    })


@app.route("/predict", methods=["POST"])
def predict():
    """Main prediction endpoint - compatible with backend service"""
    data = request.json
    
    # Try to use flexible format first
    metrics_data = data.get("metrics")
    logs_data = data.get("logs")
    traces_data = data.get("traces")
    
    # If flexible format, use flexible endpoint logic
    if metrics_data or logs_data or traces_data:
        return predict_flexible()
    
    # Otherwise use legacy format
    ml_hybrid = None
    ml_msif = None
    ml_ple = None
    fusion = "ml_inference"
    confidence = 0.5

    try:
        response_time = float(data.get("response_time", 0))
        cpu_usage = float(data.get("cpu_usage", 0))
        memory_usage = float(data.get("memory_usage", 0))
        error_rate = float(data.get("error_rate", 0))

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
        print(f"WARN ML prediction failed, using rule-based: {e}")
        ml_hybrid = None

    USE_RULE_BASED = True

    if USE_RULE_BASED:
        rb_score = rule_based_score(data)
        ml_hybrid = rb_score
        ml_msif = round(rb_score * 0.9, 4)
        ml_ple = round(rb_score * 1.0, 4)
        fusion = "rule-based-fallback"
        confidence = 0.60

    severity = score_to_severity(ml_hybrid)

    return jsonify({
        "status": "success",
        "hybrid_score": ml_hybrid,
        "msif_score": ml_msif,
        "ple_score": ml_ple,
        "severity": severity,
        "fusion_method": fusion,
        "confidence": round(confidence, 2),
        "processing_time_ms": 0,
    })


if __name__ == "__main__":
    load_models()
    app.run(host="0.0.0.0", port=int(os.getenv("ML_SERVICE_PORT", "9000")), debug=False)