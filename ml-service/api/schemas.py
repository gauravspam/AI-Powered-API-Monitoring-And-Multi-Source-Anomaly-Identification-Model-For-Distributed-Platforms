from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# --- INPUT: Multimodal Entities ---

class MetricPoint(BaseModel):
    timestamp: int
    value: float

class LogEvent(BaseModel):
    timestamp: int
    message: str
    level: str = "INFO"
    template_id: Optional[str] = None
    attributes: Dict[str, str] = Field(default_factory=dict)

class TraceSpan(BaseModel):
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    service: str
    operation: str
    duration_ms: float
    status_code: int = 0
    timestamp: int

class PredictionWindow(BaseModel):
    """
    Represents a time window (e.g. 60s) of raw multimodal data.
    This replaces the legacy 3-scalar input.
    """
    window_start: int
    window_end: int
    entity_id: str  # e.g., service name

    # Structured data (Raw sources, not pre-reduced)
    metrics: Dict[str, List[MetricPoint]] = Field(default_factory=dict)
    logs: List[LogEvent] = Field(default_factory=list)
    traces: List[TraceSpan] = Field(default_factory=list)

class BatchPredictionRequest(BaseModel):
    windows: List[PredictionWindow]

# --- OUTPUT: Anomaly Scores ---

class AnomalyScore(BaseModel):
    is_anomaly: bool
    severity: float  # 0.0 to 1.0

    # Sub-model scores for explainability
    score_msif: float  # Metrics View
    score_ple: float   # Logs/Sequences View
    score_fusion: float # Final Weighted Fusion

    # Diagnostics
    confidence: float
    contributing_factors: List[str] = []

class PredictionResponse(BaseModel):
    request_id: str
    entity_id: str
    window_end: int
    result: AnomalyScore
    processing_time_ms: float
    model_version: str
