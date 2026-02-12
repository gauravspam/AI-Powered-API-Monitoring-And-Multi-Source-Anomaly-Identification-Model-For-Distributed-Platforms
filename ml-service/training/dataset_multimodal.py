import json
from typing import Dict, List

import torch
from api.schemas import LogEvent, MetricSeries, SpanEvent
from torch.utils.data import Dataset


class MultimodalDataset(Dataset):
    """
    PyTorch Dataset for multimodal windows (JSONL format).

    Each sample is a dict with keys:
    - context: window metadata
    - metrics: List[dict] -> MetricSeries
    - logs: List[dict] -> LogEvent
    - traces: List[dict] -> SpanEvent
    - label: 0 or 1
    """

    def __init__(self, jsonl_path: str, metric_encoder, log_encoder, trace_encoder):
        self.samples = []

        # Load JSONL
        with open(jsonl_path, 'r') as f:
            for line in f:
                self.samples.append(json.loads(line))

        self.metric_encoder = metric_encoder
        self.log_encoder = log_encoder
        self.trace_encoder = trace_encoder

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]

        # Convert dicts to Pydantic models
        metrics = [MetricSeries(**m) for m in sample['metrics']]
        logs = [LogEvent(**l) for l in sample['logs']]
        traces = [SpanEvent(**t) for t in sample['traces']]

        # Encode modalities
        with torch.no_grad():
            metric_emb = self.metric_encoder.encode(metrics)  # (1, 128)
            log_emb = self.log_encoder.encode(logs)           # (1, 128)
            trace_emb = self.trace_encoder.encode(traces)     # (1, 128)

        # Concatenate
        x = torch.cat([metric_emb, log_emb, trace_emb], dim=1).squeeze(0)  # (384,)

        # Label
        y = torch.tensor([sample['label']], dtype=torch.float32)

        return x, y
