import torch
import torch.nn as nn


class MetricEncoder(nn.Module):
    """
    Encodes time-series metrics using Bidirectional LSTM + Attention.
    Handles variable-length sequences.

    Input: [batch, seq_len, num_features] (e.g., [32, 60, 5] for 60 timestamps, 5 metrics)
    Output: [batch, 256] embeddings
    """
    def __init__(self, input_dim=5, hidden_dim=128, output_dim=256, num_layers=2):
        super().__init__()

        # Bidirectional LSTM
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.3 if num_layers > 1 else 0
        )

        # Attention mechanism
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, 128),
            nn.Tanh(),
            nn.Linear(128, 1)
        )

        # Final projection
        self.projection = nn.Sequential(
            nn.Linear(hidden_dim * 2, output_dim),
            nn.LayerNorm(output_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )

    def forward(self, x):
        """
        Args:
            x: torch.Tensor [batch, seq_len, input_dim]
               Example: [32, 60, 5] for 60 timesteps of 5 metrics

        Returns:
            embeddings: torch.Tensor [batch, output_dim]
        """
        if x.size(0) == 0:
            return torch.zeros(1, self.projection[-3].out_features)

        # LSTM forward pass
        lstm_out, _ = self.lstm(x)  # [batch, seq_len, hidden_dim*2]

        # Attention weights
        attn_scores = self.attention(lstm_out)  # [batch, seq_len, 1]
        attn_weights = torch.softmax(attn_scores, dim=1)  # Normalize across time

        # Weighted sum (context vector)
        context = torch.sum(attn_weights * lstm_out, dim=1)  # [batch, hidden_dim*2]

        # Project to output dimension
        return self.projection(context)  # [batch, output_dim]
