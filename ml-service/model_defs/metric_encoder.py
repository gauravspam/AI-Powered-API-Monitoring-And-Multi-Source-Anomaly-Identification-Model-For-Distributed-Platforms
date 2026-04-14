import torch
import torch.nn as nn
import numpy as np

class MetricEncoder(nn.Module):
    """
    Encodes variable-length metric time-series into fixed 128-dim embeddings.

    Handles:
    - Variable number of metrics (cpu, memory, network, etc.)
    - Variable sequence lengths
    - Missing metrics

    Output: Fixed 128-dim embedding suitable for MSIF-LSTM/PLE-GRU
    """

    def __init__(self, embedding_dim=128, lstm_hidden_dim=64):
        super(MetricEncoder, self).__init__()

        self.embedding_dim = embedding_dim

        # LSTM for processing time-series
        self.lstm = nn.LSTM(
            input_size=1,  # Each metric is univariate
            hidden_size=lstm_hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.3
        )

        # Project LSTM output to embedding space
        self.projection = nn.Sequential(
            nn.Linear(lstm_hidden_dim * 2, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )

        # Feature name embedding (learns what each metric represents)
        self.feature_vocab = {}
        self.next_feature_id = 0
        self.feature_embedding = nn.Embedding(1000, embedding_dim)  # Support 1000 metric types

        # Attention for aggregating multiple metrics
        self.metric_attention = nn.MultiheadAttention(
            embed_dim=embedding_dim,
            num_heads=4,
            batch_first=True
        )

    def get_feature_id(self, metric_name):
        """Map metric name to unique ID"""
        if metric_name not in self.feature_vocab:
            self.feature_vocab[metric_name] = self.next_feature_id
            self.next_feature_id += 1
        return self.feature_vocab[metric_name]

    def encode_single_metric(self, time_series, metric_name):
        """
        Encode a single metric time-series.

        Args:
            time_series: List[float] or np.array - [0.7, 0.75, 0.8, ...]
            metric_name: str - 'cpu_usage', 'memory_usage', etc.

        Returns:
            Tensor (1, embedding_dim)
        """
        # Convert to tensor
        if isinstance(time_series, (list, np.ndarray)):
            ts = torch.tensor(time_series, dtype=torch.float32)
        else:
            ts = time_series

        # Reshape for LSTM: (1, seq_len, 1)
        ts = ts.unsqueeze(0).unsqueeze(-1)

        # Process with LSTM
        _, (h_n, _) = self.lstm(ts)
        # h_n shape: (4, 1, hidden_dim) [2 layers * 2 directions]

        # Concatenate forward and backward final states
        h_forward = h_n[-2]  # (1, hidden_dim)
        h_backward = h_n[-1]  # (1, hidden_dim)
        h_final = torch.cat([h_forward, h_backward], dim=1)  # (1, hidden_dim*2)

        # Project to embedding space
        temporal_embedding = self.projection(h_final)  # (1, embedding_dim)

        # Get semantic embedding for metric name
        metric_id = self.get_feature_id(metric_name)
        semantic_embedding = self.feature_embedding(
            torch.tensor([metric_id], device=temporal_embedding.device)
        )  # (1, embedding_dim)

        # Combine temporal and semantic information
        combined = temporal_embedding + semantic_embedding  # Element-wise addition

        return combined

    def encode(self, metrics):
        """
        Encode multiple metrics to single fixed embedding.

        Args:
            metrics: Dict[str, List[float]] - {
                'cpu_usage': [0.7, 0.75, 0.8, ...],
                'memory_usage': [0.6, 0.65, 0.7, ...],
                'network_rx_bytes': [1000, 1200, 1500, ...]
            }

        Returns:
            Tensor (1, embedding_dim)
        """
        if not metrics or len(metrics) == 0:
            # Return zero embedding if no metrics
            return torch.zeros(1, self.embedding_dim)

        metric_embeddings = []

        for metric_name, time_series in metrics.items():
            if len(time_series) == 0:
                continue

            try:
                emb = self.encode_single_metric(time_series, metric_name)
                metric_embeddings.append(emb)
            except Exception as e:
                print(f"[!] Failed to encode {metric_name}: {e}")
                continue

        if len(metric_embeddings) == 0:
            return torch.zeros(1, self.embedding_dim)

        # Stack all metric embeddings: (num_metrics, embedding_dim)
        metric_stack = torch.cat(metric_embeddings, dim=0).unsqueeze(0)  # (1, num_metrics, embedding_dim)

        # Apply attention to learn which metrics are important
        attended, _ = self.metric_attention(metric_stack, metric_stack, metric_stack)

        # Aggregate to single embedding (mean pooling)
        aggregated = attended.mean(dim=1)  # (1, embedding_dim)

        return aggregated

    def forward(self, metrics):
        """Forward pass for training"""
        return self.encode(metrics)
