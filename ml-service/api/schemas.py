from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class MetricPoint(BaseModel):
    timestamp: int
    value: float


class LogEvent(BaseModel):
    timestamp: int
    level: str
    message: str
    service: Optional[str] = None
    template_id: Optional[str] = None


class TraceSpan(BaseModel):
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    service: str
    operation: str
    duration_ms: float
    status_code: int
    timestamp: int


class PredictionWindow(BaseModel):
    window_start: int
    window_end: int
    entity_id: str
    # Support flexible metric formats
    metrics: Dict[str, List[MetricPoint]]
    logs: List[LogEvent] = []
    traces: List[TraceSpan] = []


class AnomalyScore(BaseModel):
    is_anomaly: bool
    severity: str  # Changed to str (LOW/MEDIUM/HIGH) usually, or float if you prefer
    score_msif: float
    score_ple: float
    score_fusion: float
    confidence: float


class PredictResponse(BaseModel):
    request_id: str
    entity_id: str
    window_end: int
    result: AnomalyScore
    processing_time_ms: float
    model_version: str
