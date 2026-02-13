import json

import torch
from api.schemas import PredictionWindow
from torch.utils.data import Dataset

class MultimodalWindowDataset(Dataset):
    def __init__(self, jsonl_path: str):
        self.windows = []
        self.labels = []

        print(f"Loading {jsonl_path}...")
        try:
            with open(jsonl_path, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        # Fix metric format if needed
                        metrics = data.get("metrics", [])
                        if isinstance(metrics, list):
                            new_m = {}
                            for m in metrics:
                                new_m[m["name"]] = [
                                    {"timestamp": t, "value": v}
                                    for t, v in zip(m["timestamps"], m["values"])
                                ]
                            data["metrics"] = new_m

                        self.windows.append(PredictionWindow(**data))
                        self.labels.append(float(data.get("label", 0)))
                    except Exception as e:
                        continue
        except FileNotFoundError:
            print("File not found")

        print(f"✅ Loaded {len(self.windows)} windows")

    def __len__(self):
        return len(self.windows)

    def __getitem__(self, idx):
        return self.windows[idx], torch.tensor([self.labels[idx]], dtype=torch.float32)

    def __getitem__(self, idx):
        return self.windows[idx], torch.tensor([self.labels[idx]], dtype=torch.float32)

def collate_windows(batch):
    windows = [b[0] for b in batch]
    labels = torch.stack([b[1] for b in batch])
    return windows, labels
