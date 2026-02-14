import torch
import torch.nn as nn

from .log_encoder import LogEncoder
from .metric_encoder import MetricEncoder
from .trace_encoder import TraceEncoder


class MultimodalFusionModel(nn.Module):
    """
    Multi-source anomaly detection model that fuses:
    1. Log embeddings (768-dim from DistilBERT)
    2. Metric embeddings (256-dim from LSTM+Attention)
    3. Trace embeddings (128-dim from GNN)

    Final output: Anomaly score [0, 1]
    """
    def __init__(self):
        super().__init__()

        # Modality encoders
        self.log_encoder = LogEncoder(freeze_transformer=True)
        self.metric_encoder = MetricEncoder(input_dim=5, output_dim=256)
        self.trace_encoder = TraceEncoder(node_feature_dim=10, output_dim=128)

        # Fusion layers
        fusion_dim = 768 + 256 + 128  # 1152
        self.fusion_layers = nn.Sequential(
            nn.Linear(fusion_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.3),

            nn.Linear(256, 1),
            nn.Sigmoid()
        )

    def forward(self, logs, metrics, traces_adj, traces_features):
        """
        Args:
            logs: List[str] - Raw log messages
            metrics: torch.Tensor [batch, seq_len, num_features]
            traces_adj: torch.Tensor [batch, num_nodes, num_nodes]
            traces_features: torch.Tensor [batch, num_nodes, feature_dim]

        Returns:
            anomaly_score: torch.Tensor [batch, 1] in range [0, 1]
        """
        # Encode each modality
        log_emb = self.log_encoder(logs)  # [batch, 768]
        metric_emb = self.metric_encoder(metrics)  # [batch, 256]
        trace_emb = self.trace_encoder(traces_adj, traces_features)  # [batch, 128]

        # Concatenate all embeddings
        fused = torch.cat([log_emb, metric_emb, trace_emb], dim=1)  # [batch, 1152]

        # Pass through fusion layers
        anomaly_score = self.fusion_layers(fused)  # [batch, 1]

        return anomaly_score
