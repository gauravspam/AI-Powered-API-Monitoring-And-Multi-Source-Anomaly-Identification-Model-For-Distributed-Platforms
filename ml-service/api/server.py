import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

import torch
from core.fusion import MultimodalFusionModel
from fastapi import FastAPI, HTTPException, Request

from api.schemas import (
    AnomalyScore,
    BatchPredictionRequest,
    PredictionResponse,
    PredictionWindow,
)

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml-service")

# Global Model Registry
models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Load PyTorch models and Encoders on startup.
    Clean up on shutdown.
    """
    logger.info("Initializing Multimodal ML Service...")

    # TODO: Load actual PyTorch models here
    # from models.fusion import HybridFusionModel
    # models["fusion"] = HybridFusionModel.load(...)

    # Initialize Model (Lazy load weights would happen here)
    model = MultimodalFusionModel(embed_dim=64)

    # Load trained weights
    weights_path = "models/fusion_v2.pth"
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location='cpu'))
        logger.info(f"✅ Loaded weights from {weights_path}")
    else:
        logger.warning(f"⚠️ Weights not found at {weights_path}, using random initialization")

    model.eval() # Inference mode

    # Store in global registry
    models["fusion"] = model
    logger.info("MultimodalFusionModel loaded.")
    yield
    models.clear()

    # Mock loading for now
    models["fusion"] = "LOADED"
    logger.info("Models loaded successfully.")

    yield

    models.clear()
    logger.info("Models unloaded.")

app = FastAPI(
    title="Multimodal Anomaly Detection API",
    version="2.0.0",
    lifespan=lifespan
)

@app.get("/health")
def health_check():
    if not models:
        raise HTTPException(status_code=503, detail="Models not initialized")
    return {"status": "healthy", "version": "2.0.0", "backend": "pytorch"}

@app.post("/v1/predict", response_model=PredictionResponse)
def predict_window(window: PredictionWindow):
    start_time = time.time()
    req_id = str(uuid.uuid4())

    try:
        # 1. TODO: Encoding Step
        # metric_feats = models["metric_encoder"](window.metrics)
        # log_feats = models["log_encoder"](window.logs)

        # 2. TODO: Fusion Step
        # score = models["fusion"](metric_feats, log_feats)

        model = models.get("fusion")
        if not model:
            raise HTTPException(503, "Model not loaded")

        # RUN INFERENCE
        with torch.no_grad():
            scores = model(window) # Returns dict {'fusion': ..., 'msif': ...}

        # LOGIC: Hybrid Decision
        is_anomaly = scores['fusion'] > 0.75

        # MOCK LOGIC for Connectivity Testing
        has_logs = len(window.logs) > 0
        has_metrics = len(window.metrics) > 0

        # Logic: If metrics are high variance or logs contain "ERROR", flag anomaly
        is_error = any("ERROR" in l.level for l in window.logs)
        severity = 0.9 if is_error else 0.1

        result = AnomalyScore(
            is_anomaly=is_anomaly,
            severity=scores['fusion'],
            score_msif=scores['msif'],
            score_ple=scores['ple'],
            score_fusion=scores['fusion'],
            confidence=0.85, # dynamic calc in future
            contributing_factors=[]
        )

        duration = (time.time() - start_time) * 1000

        return PredictionResponse(
            request_id=req_id,
            entity_id=window.entity_id,
            window_end=window.window_end,
            result=result,
            processing_time_ms=duration,
            model_version="v2.0.0-stub"
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/predict:batch")
def predict_batch(batch: BatchPredictionRequest):
    # Wrapper for batch processing
    results = []
    for window in batch.windows:
        results.append(predict_window(window))
    return results
