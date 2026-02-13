import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

import torch
from core.fusion import MultimodalFusionModel
from fastapi import FastAPI, HTTPException

from api.schemas import (
    AnomalyScore,
    PredictionWindow,
    PredictResponse,
)

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ml-service")

# Global Model Registry
models = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Multimodal ML Service...")

    # Initialize Model
    model = MultimodalFusionModel(embed_dim=64)

    # Load trained weights
    weights_path = "models/fusion_v2.pth"
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        logger.info(f"✅ Loaded weights from {weights_path}")
    else:
        logger.warning(f"⚠️ Weights not found at {weights_path}, using random init")

    model.eval()
    models["fusion"] = model
    yield
    models.clear()
    logger.info("Models unloaded.")


app = FastAPI(
    title="Multimodal Anomaly Detection API", version="2.0.0", lifespan=lifespan
)


@app.get("/health")
def health_check():
    if not models:
        raise HTTPException(status_code=503, detail="Models not initialized")
    return {"status": "healthy", "version": "2.0.0", "backend": "pytorch"}


@app.post("/v1/predict", response_model=PredictResponse)
def predict_window(window: PredictionWindow):
    start_time = time.time()
    req_id = str(uuid.uuid4())

    try:
        model = models.get("fusion")
        if not model:
            raise HTTPException(503, "Model not loaded")

        with torch.no_grad():
            # Pass list [window] because model expects batch
            device = torch.device("cpu")
            scores = model([window], device=device)

        fusion_val = scores["fusion"].item()

        is_anomaly = fusion_val > 0.75
        severity = (
            "HIGH" if fusion_val > 0.9 else ("MEDIUM" if fusion_val > 0.75 else "LOW")
        )

        result = AnomalyScore(
            is_anomaly=is_anomaly,
            severity=severity,
            score_msif=0.0,
            score_ple=0.0,
            score_fusion=fusion_val,
            confidence=0.85,
        )

        duration = (time.time() - start_time) * 1000

        return PredictResponse(
            request_id=req_id,
            entity_id=window.entity_id,
            window_end=window.window_end,
            result=result,
            processing_time_ms=duration,
            model_version="v2.0.0",
        )

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
