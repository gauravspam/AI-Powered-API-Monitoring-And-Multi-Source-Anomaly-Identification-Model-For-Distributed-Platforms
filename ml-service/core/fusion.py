import torch
import torch.nn as nn
from api.schemas import PredictionWindow
from core.encoders import LogEncoderV2, MetricEncoderV2, TraceEncoderV2


class MultimodalFusionModel(nn.Module):
    def __init__(self, embed_dim=64):
        super().__init__()
        self.metric_enc = MetricEncoderV2(embed_dim=embed_dim)
        self.log_enc = LogEncoderV2(embed_dim=embed_dim)
        self.trace_enc = TraceEncoderV2(embed_dim=embed_dim)

        # Fusion Layer: Concatenate 3 vectors -> Classifier
        self.fusion_mlp = nn.Sequential(
            nn.Linear(embed_dim * 3, 128),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

        # Independent heads for explainability (MSIF/PLE analogs)
        self.metric_head = nn.Linear(embed_dim, 1)
        self.trace_log_head = nn.Linear(embed_dim * 2, 1)

    def forward(self, window: PredictionWindow, device='cpu'):
        # 1. Encode Modalities independently
        m_vec = self.metric_enc(window.metrics, device)
        l_vec = self.log_enc(window.logs, device)
        t_vec = self.trace_enc(window.traces, device)

        # 2. Fusion Vector
        combined = torch.cat([m_vec, l_vec, t_vec], dim=1) # (1, embed_dim*3)

        # 3. Predictions
        fusion_score = self.fusion_mlp(combined)

        # Auxiliary scores for legacy compatibility
        msif_score = torch.sigmoid(self.metric_head(m_vec))
        ple_score = torch.sigmoid(self.trace_log_head(torch.cat([l_vec, t_vec], dim=1)))

        return {
            "fusion": fusion_score.item(),
            "msif": msif_score.item(),
            "ple": ple_score.item()
        }
