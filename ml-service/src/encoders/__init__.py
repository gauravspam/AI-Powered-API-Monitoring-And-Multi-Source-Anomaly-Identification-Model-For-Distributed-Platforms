"""
Metric Encoder for Multi-Modal Anomaly Detection

Transforms numerical metrics into fixed-size embedding vectors
for processing through ML models.

Input: CPU, Memory, Response Time, Error Rate, Request Count, etc.
Output: Normalized embedding vector
"""

import numpy as np
import torch
import torch.nn as nn
from typing import Dict, List, Any


class TemporalConvNet(nn.Module):
    """
    TCN (Temporal Convolutional Network) for Metric Time Series
    
    Uses 1D dilated convolutions to capture temporal patterns
    in multi-metric time series data.
    
    Advantages over LSTM:
    - Faster inference (parallel convs vs sequential)
    - Better local pattern capture
    - Fewer parameters (~500K vs 1M+)
    """
    
    def __init__(self, input_dim=9, embed_dim=128, num_channels=[64, 64, 128], kernel_size=3, dropout=0.2):
        super(TemporalConvNet, self).__init__()
        
        layers = []
        num_levels = len(num_channels)
        
        for i in range(num_levels):
            in_ch = input_dim if i == 0 else num_channels[i-1]
            out_ch = num_channels[i]
            dilation = 2 ** i
            
            conv = nn.Conv1d(
                in_ch, out_ch, kernel_size,
                padding=(kernel_size - 1) * dilation // 2,
                dilation=dilation
            )
            layers.append(conv)
            layers.append(nn.BatchNorm1d(out_ch))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
        
        self.network = nn.Sequential(*layers)
        self.projection = nn.Linear(num_channels[-1], embed_dim)
        
    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        x = x.transpose(1, 2)  # (batch, input_dim, seq_len)
        x = self.network(x)
        x = x.transpose(1, 2)  # (batch, seq_len, channels)
        x = x.mean(dim=1)  # Global average pooling
        return self.projection(x)


class MetricEncoderTCN(nn.Module):
    """
    Neural Network-based Metric Encoder using TCN
    
    Processes sequential metric data for better temporal pattern capture.
    """
    
    def __init__(self, input_dim=9, embed_dim=128, hidden_dim=64):
        super(MetricEncoderTCN, self).__init__()
        
        self.tcn = TemporalConvNet(
            input_dim=input_dim,
            embed_dim=embed_dim,
            num_channels=[32, 64, 64],
            kernel_size=3,
            dropout=0.2
        )
        
    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        return self.tcn(x)


class MetricEncoder:
    """Encoder for system metrics"""
    
    def __init__(self, embedding_dim: int = 128):
        self.embedding_dim = embedding_dim
        self.feature_names = [
            'cpu_usage', 'memory_usage', 'disk_io', 
            'network_io', 'response_time', 'request_count', 'error_rate'
        ]
        
    def normalize(self, value: float, min_val: float, max_val: float) -> float:
        """Min-max normalization"""
        if max_val == min_val:
            return 0.0
        return (value - min_val) / (max_val - min_val)
    
    def log_normalize(self, value: float) -> float:
        """Log transform for positive values"""
        return np.log1p(value) / 10.0  # Normalize to 0-1 range
    
    def encode(self, metrics: Dict[str, Any]) -> np.ndarray:
        """
        Encode metrics to embedding vector
        
        Args:
            metrics: Dict with keys like 'cpu_usage', 'memory_usage', etc.
            
        Returns:
            Embedding vector of shape (embedding_dim,)
        """
        embedding = np.zeros(self.embedding_dim)
        
        # Encode CPU usage (0-100 -> 0-1)
        cpu = metrics.get('cpu_usage', 0.0)
        embedding[0] = self.normalize(cpu, 0, 100)
        
        # Encode memory usage (0-100 -> 0-1)
        memory = metrics.get('memory_usage', 0.0)
        embedding[1] = self.normalize(memory, 0, 100)
        
        # Encode disk I/O (log scale)
        disk = metrics.get('disk_io_bytes', 0)
        embedding[2] = min(self.log_normalize(disk), 1.0)
        
        # Encode network I/O (log scale)
        network = metrics.get('network_io_bytes', 0)
        embedding[3] = min(self.log_normalize(network), 1.0)
        
        # Encode response time (log scale)
        response_time = metrics.get('response_time_ms', 0)
        embedding[4] = min(self.log_normalize(response_time), 1.0)
        
        # Encode request count (log scale)
        requests = metrics.get('request_count', 0)
        embedding[5] = min(self.log_normalize(requests), 1.0)
        
        # Encode error rate (already 0-1)
        error = metrics.get('error_rate', 0.0)
        embedding[6] = min(max(error, 0.0), 1.0)
        
        # Add derived features
        # Throughput = requests / response_time
        if response_time > 0:
            throughput = requests / (response_time / 1000.0)
            embedding[7] = min(self.log_normalize(throughput), 1.0)
        
        # Efficiency score
        efficiency = (100 - cpu) * (100 - memory) / 10000.0
        embedding[8] = efficiency
        
        return embedding


def encode_metrics_batch(metrics_list: List[Dict[str, Any]], 
                       embedding_dim: int = 128) -> np.ndarray:
    """Encode a batch of metrics"""
    encoder = MetricEncoder(embedding_dim)
    embeddings = []
    
    for metrics in metrics_list:
        emb = encoder.encode(metrics)
        embeddings.append(emb)
    
    return np.array(embeddings)