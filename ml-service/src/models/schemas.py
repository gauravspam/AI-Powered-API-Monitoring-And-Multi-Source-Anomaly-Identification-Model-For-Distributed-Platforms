"""
Pydantic validation schemas for API requests and responses

Provides:
1. PredictionRequest - Validates incoming prediction requests
2. PredictionResponse - Validates API responses
3. HealthResponse - Validates health check responses

Benefits:
- Automatic type validation
- Boundary checks (min/max values)
- Clear error messages
- OpenAPI/Swagger documentation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
from config.settings import config

class PredictionRequest(BaseModel):
    """
    Validated prediction request schema
    
    All fields are required and must be within bounds.
    Context is optional for advanced use cases.
    
    Example JSON:
    {
        "response_time": 250,
        "status_code": 200,
        "request_count": 100,
        "error_rate": 0.02,
        "cpu_usage": 50,
        "memory_usage": 60,
        "network_io": 300,
        "disk_io": 100,
        "hour_of_day": 14,
        "day_of_week": 1,
        "context": {
            "hour_of_day": 14,
            "endpoint_type": "api",
            "traffic_level": "high"
        },
        "trace_id": "trace-12345"
    }
    """
    
    # Required feature fields with validation
    response_time: float = Field(
        ...,
        ge=0,
        le=10000,
        description="Response time in milliseconds (0-10000)"
    )
    
    status_code: int = Field(
        ...,
        ge=100,
        le=599,
        description="HTTP status code (100-599)"
    )
    
    request_count: float = Field(
        ...,
        ge=0,
        le=100000,
        description="Requests per minute (0-100000)"
    )
    
    error_rate: float = Field(
        ...,
        ge=0,
        le=1,
        description="Error rate as fraction 0-1 (0-100%)"
    )
    
    cpu_usage: float = Field(
        ...,
        ge=0,
        le=100,
        description="CPU usage percentage (0-100%)"
    )
    
    memory_usage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Memory usage percentage (0-100%)"
    )
    
    network_io: float = Field(
        ...,
        ge=0,
        le=10000,
        description="Network I/O in MB/s (0-10000)"
    )
    
    disk_io: float = Field(
        ...,
        ge=0,
        le=10000,
        description="Disk I/O in MB/s (0-10000)"
    )
    
    hour_of_day: int = Field(
        ...,
        ge=0,
        le=23,
        description="Hour of day (0-23)"
    )
    
    day_of_week: int = Field(
        ...,
        ge=0,
        le=6,
        description="Day of week (0=Mon, 6=Sun)"
    )
    
    # Optional context for weighted ensemble
    context: Optional[Dict] = Field(
        default=None,
        description="Optional context dict with hour_of_day, endpoint_type, traffic_level"
    )
    
    # Optional tracing
    trace_id: Optional[str] = Field(
        default=None,
        description="Optional trace ID for request correlation"
    )
    
    class Config:
        # Example for Swagger/OpenAPI docs
        schema_extra = {
            "example": {
                "response_time": 250,
                "status_code": 200,
                "request_count": 100,
                "error_rate": 0.02,
                "cpu_usage": 50,
                "memory_usage": 60,
                "network_io": 300,
                "disk_io": 100,
                "hour_of_day": 14,
                "day_of_week": 1,
                "context": {
                    "hour_of_day": 14,
                    "endpoint_type": "api",
                    "traffic_level": "high"
                },
                "trace_id": "trace-12345"
            }
        }
    
    @validator('error_rate')
    def validate_error_rate(cls, v):
        """Ensure error_rate is between 0 and 1"""
        if not (0 <= v <= 1):
            raise ValueError('error_rate must be between 0 and 1')
        return v


class PredictionResponse(BaseModel):
    """
    Validated prediction response schema
    
    Returned by /predict endpoint with anomaly scores and metadata.
    
    Example response:
    {
        "msif_score": 0.23,
        "ple_score": 0.18,
        "hybrid_score": 0.21,
        "severity": "LOW",
        "confidence": 0.95,
        "weights_used": {"msif": 0.35, "ple": 0.65},
        "fusion_method": "weighted_agreement",
        "models_loaded": true,
        "processing_time_ms": 45.2,
        "trace_id": "trace-12345"
    }
    """
    
    msif_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="MSIF-LSTM anomaly score (0-1)"
    )
    
    ple_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="PLE-GRU anomaly score (0-1)"
    )
    
    hybrid_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="Weighted ensemble anomaly score (0-1)"
    )
    
    severity: str = Field(
        ...,
        description="Severity level: LOW, MEDIUM, HIGH, CRITICAL"
    )
    
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence in prediction based on model agreement (0-1)"
    )
    
    weights_used: Dict = Field(
        ...,
        description="Weights used for fusion: {'msif': 0.35, 'ple': 0.65}"
    )
    
    fusion_method: str = Field(
        ...,
        description="Fusion method: weighted_agreement, conservative_max, conflict_detected"
    )
    
    models_loaded: bool = Field(
        ...,
        description="Whether trained models were successfully loaded"
    )
    
    processing_time_ms: float = Field(
        ...,
        ge=0,
        description="Prediction latency in milliseconds"
    )
    
    trace_id: Optional[str] = Field(
        None,
        description="Trace ID for request correlation (if provided)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "msif_score": 0.23,
                "ple_score": 0.18,
                "hybrid_score": 0.21,
                "severity": "LOW",
                "confidence": 0.95,
                "weights_used": {"msif": 0.35, "ple": 0.65},
                "fusion_method": "weighted_agreement",
                "models_loaded": True,
                "processing_time_ms": 45.2,
                "trace_id": "trace-12345"
            }
        }
    
    @validator('severity')
    def validate_severity(cls, v):
        """Ensure severity is one of allowed values"""
        valid_severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        if v not in valid_severities:
            raise ValueError(f'severity must be one of {valid_severities}')
        return v
    
    @validator('fusion_method')
    def validate_fusion_method(cls, v):
        """Ensure fusion_method is valid"""
        valid_methods = ['weighted_agreement', 'conservative_max', 'conflict_detected']
        if v not in valid_methods:
            raise ValueError(f'fusion_method must be one of {valid_methods}')
        return v


class HealthResponse(BaseModel):
    """
    Validated health check response schema
    
    Returned by /health endpoint to confirm service is running.
    
    Example response:
    {
        "status": "healthy",
        "version": "1.0.0",
        "models_loaded": true,
        "models_info": {
            "msif": {"loaded": true, "type": "LSTM"},
            "ple": {"loaded": true, "type": "GRU"}
        },
        "timestamp": "2026-01-19T12:30:45Z"
    }
    """
    
    status: str = Field(
        ...,
        description="Service status: healthy or unhealthy"
    )
    
    version: str = Field(
        ...,
        description="API version"
    )
    
    models_loaded: bool = Field(
        ...,
        description="Whether trained models are loaded"
    )
    
    models_info: Dict = Field(
        ...,
        description="Detailed model information"
    )
    
    timestamp: str = Field(
        ...,
        description="UTC timestamp of health check"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "models_loaded": True,
                "models_info": {
                    "msif": {"loaded": True, "type": "LSTM"},
                    "ple": {"loaded": True, "type": "GRU"}
                },
                "timestamp": "2026-01-19T12:30:45Z"
            }
        }
    
    @validator('status')
    def validate_status(cls, v):
        """Ensure status is valid"""
        if v not in ['healthy', 'unhealthy']:
            raise ValueError('status must be healthy or unhealthy')
        return v


# ============= ERROR RESPONSE SCHEMAS =============

class ErrorResponse(BaseModel):
    """Generic error response schema"""
    error: str
    message: Optional[str] = None
    trace_id: Optional[str] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response with details"""
    error: str = "Invalid input"
    details: list = Field(..., description="List of validation errors")
    trace_id: Optional[str] = None
