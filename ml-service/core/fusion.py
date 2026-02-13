import torch
import torch.nn as nn

from core.encoders import LogEncoderV2, MetricEncoderV2, TraceEncoderV2


class MultimodalFusionModel(nn.Module):
    def __init__(self, embed_dim=64):
        super().__init__()
        self.metric_enc = MetricEncoderV2(embed_dim)
        self.log_enc = LogEncoderV2(embed_dim)
        self.trace_enc = TraceEncoderV2(embed_dim)

        self.fusion_mlp = nn.Sequential(
            nn.Linear(embed_dim * 3, embed_dim * 2),
            nn.LayerNorm(embed_dim * 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(embed_dim * 2, 1),
            nn.Sigmoid(),
        )

    def forward(self, w_batch, device):
        metrics = [w.metrics for w in w_batch]
        logs = [w.logs for w in w_batch]
        traces = [w.traces for w in w_batch]

        m_emb = self.metric_enc(metrics, device)
        l_emb = self.log_enc(logs, device)
        t_emb = self.trace_enc(traces, device)

        combined = torch.cat([m_emb, l_emb, t_emb], dim=1)
        score = self.fusion_mlp(combined)

        return {"fusion": score}
