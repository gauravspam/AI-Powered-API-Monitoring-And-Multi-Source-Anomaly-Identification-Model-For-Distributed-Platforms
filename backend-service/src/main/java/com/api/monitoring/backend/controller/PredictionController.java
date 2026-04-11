"""
Backend API for Smart Polling

Provides endpoints for frontend to check for new predictions
without full data refresh
"""

from datetime import datetime
from typing import Optional


class PredictionMetadata:
    """Lightweight prediction metadata for smart polling"""
    
    def __init__(self):
        self.prediction_id: Optional[str] = None
        self.prediction_time: Optional[str] = None
        self.severity: Optional[str] = None
        self.alert_count: int = 0
        
    def update(self, prediction_id: str, severity: str, alert_count: int):
        """Update prediction metadata"""
        self.prediction_id = prediction_id
        self.prediction_time = datetime.utcnow().isoformat() + "Z"
        self.severity = severity
        self.alert_count = alert_count
        
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "prediction_id": self.prediction_id,
            "prediction_time": self.prediction_time,
            "severity": self.severity,
            "alert_count": self.alert_count
        }


# Global metadata instance
_latest_prediction = PredictionMetadata()


def update_prediction(prediction_id: str, severity: str, alert_count: int):
    """Update the latest prediction metadata"""
    _latest_prediction.update(prediction_id, severity, alert_count)


def get_latest_prediction():
    """Get the latest prediction metadata"""
    return _latest_prediction.to_dict()