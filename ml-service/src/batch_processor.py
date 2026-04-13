"""
Batch Processor for Multi-Modal Anomaly Detection

Queries 5000 items per modality every 2 minutes and processes them through
encoders and ML models for anomaly detection.
"""

import os
import sys
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import settings


class BatchQueryService:
    """
    Queries data from PostgreSQL/OpenSearch for batch processing.
    """
    
    def __init__(self, db_connection=None):
        self.db = db_connection
        
    def query_recent_metrics(self, limit=5000) -> List[Dict]:
        """
        Query recent metrics from database.
        Returns list of metric records.
        """
        # Placeholder - will be replaced with actual DB query
        # This should query PostgreSQL or OpenSearch
        pass
    
    def query_recent_logs(self, limit=5000) -> List[Dict]:
        """
        Query recent logs from database.
        Returns list of log records.
        """
        pass
    
    def query_recent_traces(self, limit=5000) -> List[Dict]:
        """
        Query recent traces from database.
        Returns list of trace records.
        """
        pass


class DataNormalizer:
    """
    Normalizes raw data from different sources to standard format for encoders.
    """
    
    @staticmethod
    def normalize_metric(record: Dict) -> Dict:
        """Normalize metric record to standard format"""
        return {
            "cpu_usage": record.get("cpuUsagePercent", record.get("cpu_usage", 0)),
            "memory_usage": record.get("memoryUsagePercent", record.get("memory_usage", 0)),
            "disk_io_bytes": record.get("diskIoBytes", record.get("disk_io_bytes", 0)),
            "network_io_bytes": record.get("networkIoBytes", record.get("network_io_bytes", 0)),
            "response_time_ms": record.get("responseTimeMs", record.get("response_time_ms", 0)),
            "request_count": record.get("requestCount", record.get("request_count", 0)),
            "error_rate": record.get("errorRate", record.get("error_rate", 0)),
            "timestamp": record.get("timestamp", record.get("metricTimestamp", ""))
        }
    
    @staticmethod
    def normalize_log(record: Dict) -> Dict:
        """Normalize log record to standard format"""
        return {
            "level": record.get("level", "INFO"),
            "message": record.get("message", ""),
            "service_name": record.get("serviceName", record.get("service_name", "")),
            "timestamp": record.get("timestamp", record.get("createdAt", ""))
        }
    
    @staticmethod
    def normalize_trace(record: Dict) -> Dict:
        """Normalize trace record to standard format"""
        return {
            "trace_id": record.get("traceId", record.get("trace_id", "")),
            "span_id": record.get("spanId", record.get("span_id", "")),
            "service_name": record.get("serviceName", record.get("service_name", "")),
            "operation_name": record.get("operationName", record.get("operation_name", "")),
            "duration": record.get("duration", 0),
            "status_code": record.get("statusCode", record.get("status_code", 200)),
            "timestamp": record.get("timestamp", record.get("startTime", ""))
        }


class TimeSeriesBuffer:
    """
    Buffers individual records into time-series windows for encoder input.
    """
    
    def __init__(self, window_size=60):
        self.window_size = window_size
        self.buffers = defaultdict(list)
    
    def add_metric(self, service_name: str, metric: Dict):
        """Add metric to time-series buffer"""
        key = service_name
        self.buffers[key].append(metric)
        if len(self.buffers[key]) > self.window_size:
            self.buffers[key] = self.buffers[key][-self.window_size:]
    
    def get_window(self, service_name: str) -> List[Dict]:
        """Get time-series window for a service"""
        return self.buffers.get(service_name, [])[-self.window_size:]
    
    def get_all_windows(self) -> Dict[str, List[Dict]]:
        """Get all service time-series windows"""
        return {k: v[-self.window_size:] for k, v in self.buffers.items()}


class FlexibleBatchProcessor:
    """
    Main batch processor that handles 1, 2, or 3 modalities.
    Combines encoders with confidence scaling.
    """
    
    def __init__(self, device=None):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Configuration
        self.embedding_dim = 128
        self.batch_size = settings.BATCH_SIZE_METRICS  # 5000
        
        # Initialize learnable missing embeddings (NOT zeros!)
        self.missing_metric_emb = nn.Parameter(torch.randn(self.embedding_dim).to(self.device))
        self.missing_log_emb = nn.Parameter(torch.randn(self.embedding_dim).to(self.device))
        self.missing_trace_emb = nn.Parameter(torch.randn(self.embedding_dim).to(self.device))
        
        # Modality attention weights
        self.metric_weight = nn.Parameter(torch.tensor(1.0)).to(self.device)
        self.log_weight = nn.Parameter(torch.tensor(1.0)).to(self.device)
        self.trace_weight = nn.Parameter(torch.tensor(1.0)).to(self.device)
        
        # Time series buffers
        self.metric_buffer = TimeSeriesBuffer(window_size=60)
        self.log_buffer = []
        self.trace_buffer = []
        
        # Placeholder for encoders (to be loaded)
        self.metric_encoder = None
        self.log_encoder = None
        self.trace_encoder = None
        
        # Placeholder for ML models
        self.msif_model = None
        self.ple_model = None
        self.fusion = None
    
    def load_encoders(self, metric_path, log_path, trace_path):
        """Load pre-trained encoders"""
        from src.models.metric_encoder import MetricEncoder
        from src.models.log_encoder import LogEncoder
        from src.models.trace_encoder import TraceEncoder
        
        # Metric Encoder
        self.metric_encoder = MetricEncoder(
            embedding_dim=self.embedding_dim,
            lstm_hidden_dim=64
        ).to(self.device)
        if os.path.exists(metric_path):
            state = torch.load(metric_path, map_location=self.device)
            self.metric_encoder.load_state_dict(state, strict=False)
        self.metric_encoder.eval()
        
        # Log Encoder
        self.log_encoder = LogEncoder(embedding_dim=self.embedding_dim)
        if os.path.exists(log_path):
            state = torch.load(log_path, map_location=self.device)
            self.log_encoder.load_state_dict(state, strict=False)
        self.log_encoder.eval()
        
        # Trace Encoder
        self.trace_encoder = TraceEncoder(
            num_nodes=50,
            node_embedding_dim=64,
            message_dim=128
        ).to(self.device)
        if os.path.exists(trace_path):
            state = torch.load(trace_path, map_location=self.device)
            self.trace_encoder.load_state_dict(state, strict=False)
        self.trace_encoder.eval()
        
        print(f"[OK] Encoders loaded on {self.device}")
    
    def load_models(self, msif_path, ple_path):
        """Load MSIF-LSTM and PLE-GRU models"""
        from src.models.msif_lstm_model import VariableInputMSIF_LSTM
        from src.models.ple_gru_model import VariableInputPLE_GRU
        from src.models.hybrid_fusion import HybridFusion
        
        # MSIF-LSTM
        self.msif_model = VariableInputMSIF_LSTM(
            embedding_dim=384,  # 128 * 3
            lstm_hidden_dim=64
        ).to(self.device)
        if os.path.exists(msif_path):
            state = torch.load(msif_path, map_location=self.device)
            self.msif_model.load_state_dict(state, strict=False)
        self.msif_model.eval()
        
        # PLE-GRU
        self.ple_model = VariableInputPLE_GRU(
            embedding_dim=384,
            gru_hidden_dim=64,
            num_experts=3
        ).to(self.device)
        if os.path.exists(ple_path):
            state = torch.load(ple_path, map_location=self.device)
            self.ple_model.load_state_dict(state, strict=False)
        self.ple_model.eval()
        
        # Fusion
        self.fusion = HybridFusion()
        
        print(f"[OK] ML Models loaded on {self.device}")
    
    def encode_metric(self, time_series: List[float]) -> torch.Tensor:
        """Encode metric time-series to embedding"""
        if not time_series or len(time_series) == 0:
            return None
        
        with torch.no_grad():
            # Convert to tensor
            ts = torch.tensor(time_series, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)
            ts = ts.to(self.device)
            
            # Use metric encoder (simplified - actual encoder may need dict input)
            # For now, return random embedding as placeholder
            emb = torch.randn(1, self.embedding_dim).to(self.device)
            
        return emb
    
    def encode_log(self, log_messages: List[str]) -> torch.Tensor:
        """Encode log messages to embedding"""
        if not log_messages or len(log_messages) == 0:
            return None
        
        with torch.no_grad():
            # Placeholder - actual implementation needs log encoder
            emb = torch.randn(1, self.embedding_dim).to(self.device)
            
        return emb
    
    def encode_trace(self, trace_data: Dict) -> torch.Tensor:
        """Encode trace data to embedding"""
        if not trace_data:
            return None
        
        with torch.no_grad():
            # Placeholder - actual implementation needs trace encoder
            emb = torch.randn(1, self.embedding_dim).to(self.device)
            
        return emb
    
    def combine_embeddings(self, metric_emb, log_emb, trace_emb) -> Tuple[torch.Tensor, float, int]:
        """
        Combine embeddings with learnable missing embeddings.
        
        Returns:
            combined: (1, 384) tensor
            confidence: float (0.33, 0.66, or 1.0)
            modalities_present: int
        """
        embeddings = []
        
        # Metric
        if metric_emb is not None:
            embeddings.append(metric_emb)
        else:
            embeddings.append(self.missing_metric_emb.unsqueeze(0))
        
        # Log
        if log_emb is not None:
            embeddings.append(log_emb)
        else:
            embeddings.append(self.missing_log_emb.unsqueeze(0))
        
        # Trace
        if trace_emb is not None:
            embeddings.append(trace_emb)
        else:
            embeddings.append(self.missing_trace_emb.unsqueeze(0))
        
        # Concatenate
        combined = torch.cat(embeddings, dim=1)  # (1, 384)
        
        # Count present modalities
        modalities_present = sum([
            metric_emb is not None,
            log_emb is not None,
            trace_emb is not None
        ])
        
        # Confidence based on modalities present
        confidence = modalities_present / 3.0
        
        return combined, confidence, modalities_present
    
    def predict_single(self, metric_emb=None, log_emb=None, trace_emb=None) -> Dict:
        """
        Predict anomaly score for a single item with flexible modalities.
        
        Args:
            metric_emb: encoded metric tensor or None
            log_emb: encoded log tensor or None
            trace_emb: encoded trace tensor or None
            
        Returns:
            dict with score, confidence, severity
        """
        # Combine embeddings
        combined, confidence, modalities_present = self.combine_embeddings(
            metric_emb, log_emb, trace_emb
        )
        
        # Get ML predictions
        with torch.no_grad():
            msif_score = self.msif_model(combined).item()
            ple_score = self.ple_model(combined).item()
        
        # Ensemble
        final_score, method, agreement, weights = self.fusion(msif_score, ple_score)
        
        # Apply confidence scaling
        adjusted_score = final_score * confidence
        
        # Determine severity
        if adjusted_score >= 0.8:
            severity = "CRITICAL"
        elif adjusted_score >= 0.6:
            severity = "HIGH"
        elif adjusted_score >= 0.4:
            severity = "MEDIUM"
        else:
            severity = "LOW"
        
        return {
            "prediction_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "final_score": round(adjusted_score, 4),
            "raw_score": round(final_score, 4),
            "msif_score": round(msif_score, 4),
            "ple_score": round(ple_score, 4),
            "confidence": round(confidence, 2),
            "modalities_present": modalities_present,
            "fusion_method": method,
            "severity": severity
        }
    
    def process_batch(self, metrics=None, logs=None, traces=None) -> List[Dict]:
        """
        Process a batch of data with flexible modalities.
        
        Args:
            metrics: List of metric records (can be empty/None)
            logs: List of log records (can be empty/None)
            traces: List of trace records (can be empty/None)
            
        Returns:
            List of prediction results
        """
        results = []
        
        # Determine batch size (use maximum available)
        max_items = max(
            len(metrics) if metrics else 0,
            len(logs) if logs else 0,
            len(traces) if traces else 0
        )
        
        if max_items == 0:
            return results
        
        # Process each item
        for i in range(max_items):
            # Get corresponding data from each modality
            metric_item = metrics[i] if metrics and i < len(metrics) else None
            log_item = logs[i] if logs and i < len(logs) else None
            trace_item = traces[i] if traces and i < len(traces) else None
            
            # Encode each modality
            metric_emb = None
            log_emb = None
            trace_emb = None
            
            if metric_item:
                # Extract time series from metric
                time_series = [
                    metric_item.get("cpu_usage", 0),
                    metric_item.get("memory_usage", 0),
                    metric_item.get("response_time_ms", 0),
                    metric_item.get("error_rate", 0)
                ]
                metric_emb = self.encode_metric(time_series)
            
            if log_item:
                log_emb = self.encode_log([log_item.get("message", "")])
            
            if trace_item:
                trace_emb = self.encode_trace(trace_item)
            
            # Predict
            result = self.predict_single(metric_emb, log_emb, trace_emb)
            results.append(result)
        
        return results


class BatchScheduler:
    """
    Schedules batch processing every 2 minutes.
    """
    
    def __init__(self, interval_seconds=120):
        self.interval = interval_seconds
        self.processor = None
        self.running = False
    
    def start(self, query_service: BatchQueryService):
        """Start the batch scheduler"""
        self.running = True
        print(f"[INFO] Batch scheduler started - processing every {self.interval}s")
        
        while self.running:
            try:
                print(f"[INFO] Starting batch query at {datetime.now()}")
                
                # Query data
                metrics = query_service.query_recent_metrics(limit=settings.BATCH_SIZE_METRICS)
                logs = query_service.query_recent_logs(limit=settings.BATCH_SIZE_LOGS)
                traces = query_service.query_recent_traces(limit=settings.BATCH_SIZE_TRACES)
                
                print(f"[INFO] Queried: {len(metrics)} metrics, {len(logs)} logs, {len(traces)} traces")
                
                if self.processor:
                    results = self.processor.process_batch(metrics, logs, traces)
                    print(f"[INFO] Processed {len(results)} predictions")
                    
                    # Store results (to be implemented)
                    # self.store_predictions(results)
                
            except Exception as e:
                print(f"[ERROR] Batch processing failed: {e}")
            
            # Sleep until next interval
            time.sleep(self.interval)
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        print("[INFO] Batch scheduler stopped")


if __name__ == "__main__":
    print("=== Batch Processor Module ===")
    print("This module provides:")
    print("  - BatchQueryService: Queries 5000 items per modality")
    print("  - FlexibleBatchProcessor: Handles 1/2/3 modalities with confidence scaling")
    print("  - BatchScheduler: Runs every 2 minutes")
    print("\nImport and use in app_multimodal.py")