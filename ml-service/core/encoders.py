import torch
import torch.nn as nn
import torch.nn.functional as F


class MetricEncoderV2(nn.Module):
    def __init__(self, embed_dim=64):
        super().__init__()
        self.cnn = nn.Conv1d(1, 16, kernel_size=3, padding=1)
        self.lstm = nn.LSTM(16, embed_dim, batch_first=True)  # NOT bidirectional
        self.fc = nn.Linear(embed_dim, embed_dim)

    def forward(self, metrics_dict, device):
        batch_tensors = []
        for batch_item in metrics_dict:
            values = []
            if isinstance(batch_item, dict):
                for points in batch_item.values():
                    values.extend([p.value for p in points])

            if not values:
                values = [0.0] * 10

            tensor = torch.tensor(values, dtype=torch.float32, device=device).unsqueeze(
                1
            )
            batch_tensors.append(tensor)

        padded = torch.nn.utils.rnn.pad_sequence(
            batch_tensors, batch_first=True
        ).permute(0, 2, 1)
        x = F.relu(self.cnn(padded))
        x = x.permute(0, 2, 1)
        _, (h_n, _) = self.lstm(x)
        out = self.fc(h_n.squeeze(0))
        
        return out


class LogEncoderV2(nn.Module):
    def __init__(self, embed_dim=64, vocab_size=1000):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, 32)
        self.lstm = nn.LSTM(32, embed_dim, batch_first=True)  # NOT bidirectional

    def forward(self, logs_batch, device):
        batch_tensors = []
        for logs in logs_batch:
            indices = [hash(l.message) % 1000 for l in logs]
            if not indices:
                indices = [0]
            batch_tensors.append(torch.tensor(indices, dtype=torch.long, device=device))

        padded = torch.nn.utils.rnn.pad_sequence(
            batch_tensors, batch_first=True, padding_value=0
        )
        x = self.embedding(padded)
        _, (h_n, _) = self.lstm(x)
        out = h_n.squeeze(0)

        return out


class TraceEncoderV2(nn.Module):
    def __init__(self, embed_dim=64):
        super().__init__()
        self.fc = nn.Linear(2, embed_dim)

    def forward(self, traces_batch, device):
        batch_tensors = []
        for traces in traces_batch:
            features = [
                [t.duration_ms, 1.0 if t.status_code >= 500 else 0.0] for t in traces
            ]
            if not features:
                features = [[0.0, 0.0]]
            batch_tensors.append(
                torch.tensor(features, dtype=torch.float32, device=device)
            )

        pooled = []
        for t in batch_tensors:
            x = self.fc(t)
            pooled.append(x.mean(dim=0))

        out = torch.stack(pooled)
        
        return out
