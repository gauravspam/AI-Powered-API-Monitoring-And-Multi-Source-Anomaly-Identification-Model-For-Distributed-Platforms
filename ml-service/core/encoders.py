from typing import Dict, List

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from api.schemas import LogEvent, MetricPoint, TraceSpan


class BaseEncoder(nn.Module):
    def __init__(self, embed_dim=64):
        super().__init__()
        self.embed_dim = embed_dim

class MetricEncoderV2(BaseEncoder):
    """
    Encodes variable number of metric series into a single fixed vector.
    Architecture: Per-Metric 1D-CNN -> Self-Attention Pooling.
    """
    def __init__(self, input_channels=1, embed_dim=64):
        super().__init__(embed_dim)
        # 1. Feature Extractor per metric series
        self.cnn = nn.Sequential(
            nn.Conv1d(input_channels, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool1d(1) # Flatten time dimension -> (B, 16, 1)
        )
        self.project = nn.Linear(16, embed_dim)

        # 2. Aggregation (Attention over metrics)
        self.attn = nn.MultiheadAttention(embed_dim, num_heads=4, batch_first=True)

    def forward(self, metrics_dict: Dict[str, List[MetricPoint]], device='cpu') -> torch.Tensor:
        """
        Input: Dict of metric_name -> list of points
        Output: (1, embed_dim) vector representing the system state
        """
        if not metrics_dict:
            return torch.zeros(1, self.embed_dim, device=device)

        # Preprocess: Convert dict to batch of tensors
        # Real impl would batch this efficiently. Here we iterate for clarity.
        feats = []
        for name, points in metrics_dict.items():
            if not points: continue
            vals = [p.value for p in points]
            # Normalize simple
            vals = torch.tensor(vals, dtype=torch.float32, device=device)
            if vals.std() > 0:
                vals = (vals - vals.mean()) / vals.std()

            # Shape: (1, 1, SeqLen)
            vals = vals.unsqueeze(0).unsqueeze(0)
            feat = self.cnn(vals).view(-1) # -> (16,)
            feats.append(feat)

        if not feats:
            return torch.zeros(1, self.embed_dim, device=device)

        # Stack: (1, NumMetrics, 16)
        x = torch.stack(feats).unsqueeze(0)
        x = self.project(x) # (1, NumMetrics, embed_dim)

        # Self-Attention to find important metrics
        attn_out, _ = self.attn(x, x, x)

        # Mean Pool over metrics
        embedding = attn_out.mean(dim=1) # (1, embed_dim)
        return embedding

class LogEncoderV2(BaseEncoder):
    """
    Stateless Log Encoder using Hashing Trick + EmbeddingBag.
    No mutable vocabulary!
    """
    def __init__(self, vocab_size=5000, embed_dim=64):
        super().__init__(embed_dim)
        self.vocab_size = vocab_size
        self.embedding = nn.EmbeddingBag(vocab_size, embed_dim, mode='mean')
        self.fc = nn.Linear(embed_dim, embed_dim)

    def _hash_log(self, log: LogEvent) -> int:
        # Simple deterministic hash of level + template/message
        content = f"{log.level}|{log.template_id or log.message[:50]}"
        return hash(content) % self.vocab_size

    def forward(self, logs: List[LogEvent], device='cpu') -> torch.Tensor:
        if not logs:
            return torch.zeros(1, self.embed_dim, device=device)

        indices = torch.tensor([self._hash_log(l) for l in logs], dtype=torch.long, device=device)
        offsets = torch.tensor([0], dtype=torch.long, device=device) # Single bag

        emb = self.embedding(indices, offsets) # (1, embed_dim)
        return F.relu(self.fc(emb))

class TraceEncoderV2(BaseEncoder):
    """
    Graph-free Trace Encoder.
    Encodes "Bag of Spans" focusing on errors and latency.
    """
    def __init__(self, embed_dim=64):
        super().__init__(embed_dim)
        # Input: [Duration, IsError, ServiceHash]
        self.span_mlp = nn.Sequential(
            nn.Linear(3, 32),
            nn.ReLU(),
            nn.Linear(32, embed_dim)
        )
        self.aggregator = nn.GRU(embed_dim, embed_dim, batch_first=True)

    def forward(self, traces: List[TraceSpan], device='cpu') -> torch.Tensor:
        if not traces:
            return torch.zeros(1, self.embed_dim, device=device)

        span_vecs = []
        for t in traces:
            # 1. Normalize Duration (log scale)
            dur = np.log1p(t.duration_ms)
            # 2. Error Flag
            is_err = 1.0 if t.status_code >= 400 else 0.0
            # 3. Service Hash (simple mod)
            svc_hash = (hash(t.service) % 100) / 100.0

            span_vecs.append([dur, is_err, svc_hash])

        x = torch.tensor(span_vecs, dtype=torch.float32, device=device).unsqueeze(0) # (1, Seq, 3)

        # Project each span
        x = self.span_mlp(x) # (1, Seq, embed_dim)

        # Temporal/Structural Aggregation
        _, h_n = self.aggregator(x) # h_n: (1, 1, embed_dim)

        return h_n.squeeze(0)
