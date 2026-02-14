import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Dict, List, Optional

import torch
from fastapi import FastAPI, HTTPException
from models.fusion_model import MultimodalFusionModel
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml-service")

# Global model registry
models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, unload on shutdown"""
    logger.info("🚀 Initializing Multimodal ML Service...")

    # Initialize model
    model = MultimodalFusionModel()

    # Load trained weights if available
    weights_path = "models/multimodal_fusion_v1.pth"
    try:
        model.load_state_dict(torch.load(weights_path, map_location='cpu'))
        logger.info(f"✅ Loaded weights from {weights_path}")
    except FileNotFoundError:
        logger.warning(f"⚠️ Weights not found at {weights_path}. Using random initialization.")

    model.eval()
    models['fusion'] = model

    yield

    # Cleanup
    models.clear()
    logger.info("🛑 Models unloaded.")

app = FastAPI(
    title="Multimodal Anomaly Detection API",
    version="2.0.0",
    lifespan=lifespan
)

# Request/Response schemas
class MetricPoint(BaseModel):
    name: str
    values: List[float]

class LogEvent(BaseModel):
    timestamp: int
    level: str
    message: str
    service: Optional[str] = None

class SpanEvent(BaseModel):
    trace_id: str
    span_id: str
    service: str
    operation: str
    duration_ms: float
    status_code: int
    is_error: bool

class PredictionWindow(BaseModel):
    context: Dict[str, str]
    metrics: List[MetricPoint]
    logs: List[LogEvent]
    traces: List[SpanEvent]

class PredictResponse(BaseModel):
    request_id: str
    entity_id: str
    window_end: int
    result: Dict
    processing_time_ms: float
    model_version: str

@app.get("/health")
def health_check():
    if not models:
        raise HTTPException(status_code=503, detail="Models not initialized")
    return {"status": "healthy", "version": "2.0.0", "backend": "pytorch"}

@app.post("/v1/predict", response_model=PredictResponse)
def predict(window: PredictionWindow):
    start_time = time.time()
    req_id = str(uuid.uuid4())

    try:
        model = models.get('fusion')
        if not model:
            raise HTTPException(503, "Model not loaded")

        # STEP 1: Extract log messages
        log_messages = [log.message for log in window.logs]
        if not log_messages:
            log_messages = ["INFO: No logs in window"]  # Fallback

        # STEP 2: Convert metrics to tensor
        # Assuming metrics come as time-series: {"cpu": [v1, v2, ...], "memory": [...]}
        # We need shape [batch=1, seq_len, num_features]
        metric_dict = {m.name: m.values for m in window.metrics}
        metric_names = ["cpu", "memory", "latency", "error_rate", "request_rate"]

        # Build time-series matrix
        seq_len = max(len(metric_dict.get(name, [])) for name in metric_names)
        if seq_len == 0:
            seq_len = 60  # Default to 60 timesteps

        metrics_matrix = []
        for i in range(seq_len):
            timestep = []
            for name in metric_names:
                values = metric_dict.get(name, [])
                val = values[i] if i < len(values) else 0.0
                timestep.append(val)
            metrics_matrix.append(timestep)

        metrics_tensor = torch.tensor([metrics_matrix], dtype=torch.float32)  # [1, seq_len, 5]

        # STEP 3: Build trace graph (adjacency + node features)
        # For simplicity, create a dummy graph from spans
        num_services = len(set(span.service for span in window.traces)) if window.traces else 3
        num_services = max(num_services, 3)  # At least 3 nodes

        # Dummy adjacency (fully connected graph)
        adj = torch.ones(1, num_services, num_services)

        # Dummy node features (service-level aggregates)
        node_features = torch.randn(1, num_services, 10)  # [1, num_nodes, 10]

        # STEP 4: Forward pass
        with torch.no_grad():
            score = model(
                logs=log_messages,
                metrics=metrics_tensor,
                traces_adj=adj,
                traces_features=node_features
            ).item()

        # STEP 5: Interpret results
        is_anomaly = score > 0.5
        severity = "HIGH" if score > 0.75 else "MEDIUM" if score > 0.5 else "LOW"
        confidence = abs(score - 0.5) * 2  # Map [0,1] to confidence

        duration = (time.time() - start_time) * 1000

        return PredictResponse(
            request_id=req_id,
            entity_id=window.context.get("service_name", "unknown"),
            window_end=window.context.get("window_end_ms", 0),
            result={
                "is_anomaly": is_anomaly,
                "score_fusion": score,
                "severity": severity,
                "confidence": confidence
            },
            processing_time_ms=duration,
            model_version="v2.0.0"
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
