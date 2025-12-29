from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import logging
from model_inference import AnomalyDetectionEngine
from datetime import datetime

app = FastAPI(title="AI Anomaly Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = AnomalyDetectionEngine()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogEntry(BaseModel):
    api_name: str
    response_time: float
    status_code: int
    request_count: int
    error_rate: float
    cpu_usage: float
    memory_usage: float
    network_io: float
    disk_io: float
    hour_of_day: int = None
    day_of_week: int = None
    timestamp: str = None

class BatchLogEntry(BaseModel):
    logs: List[LogEntry]

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "models_loaded": True,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/detect-anomaly")
def detect_single(log_entry: LogEntry):
    try:
        log_dict = log_entry.dict()
        result = engine.detect_anomaly(log_dict)
        
        result['api_name'] = log_entry.api_name
        result['timestamp'] = log_entry.timestamp or datetime.now().isoformat()
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/detect-batch")
def detect_batch(batch: BatchLogEntry):
    try:
        results = []
        
        for log_entry in batch.logs:
            log_dict = log_entry.dict()
            result = engine.detect_anomaly(log_dict)
            result['api_name'] = log_entry.api_name
            result['timestamp'] = log_entry.timestamp or datetime.now().isoformat()
            results.append(result)
        
        return {
            "success": True,
            "total_processed": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Batch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/model-info")
def model_info():
    return {
        "stage1_model": "MSIF-LSTM",
        "stage2_model": "PLE-GRU",
        "confidence_threshold_stage1": 0.3,
        "confidence_threshold_stage2": 0.7,
        "features": 10,
        "description": "Two-stage anomaly detection system"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
