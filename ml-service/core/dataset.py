import json
from typing import List

import torch
from api.schemas import LogEvent, MetricPoint, PredictionWindow, TraceSpan
from torch.utils.data import Dataset


class MultimodalWindowDataset(Dataset):
    """
    Loads PredictionWindows from a JSONL file.
    Each line in the file must be a valid PredictionWindow JSON.
    """
    def __init__(self, jsonl_path: str):
        self.windows = []
        self.labels = []

        print(f"Loading dataset from {jsonl_path}...")
        with open(jsonl_path, 'r') as f:
            for line in f:
                data = json.loads(line)

                # Parse JSON into Pydantic Model (Validation)
                window = PredictionWindow(**data)

                # Extract Label (assuming 'label' field exists in training data,
                # even though it's not in the inference schema)
                is_anomaly = data.get("label", 0)

                self.windows.append(window)
                self.labels.append(float(is_anomaly))

        print(f"Loaded {len(self.windows)} windows.")

    def __len__(self):
        return len(self.windows)

    def __getitem__(self, idx):
        window = self.windows[idx]
        label = torch.tensor([self.labels[idx]], dtype=torch.float32)
        return window, label

def collate_windows(batch):
    """
    Custom collate function because 'window' is an object, not a tensor.
    Returns: (List[PredictionWindow], Tensor[BatchSize, 1])
    """
    windows = [item[0] for item in batch]
    labels = torch.stack([item[1] for item in batch])
    return windows, labels
