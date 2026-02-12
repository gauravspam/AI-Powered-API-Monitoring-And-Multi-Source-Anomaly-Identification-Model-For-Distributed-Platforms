"""
MSIF-LSTM Model for multimodal anomaly detection.
Now accepts 384-dim concatenated embeddings (128 × 3 modalities).
"""

import torch
import torch.nn as nn


class VariableInputMSIFLSTM(nn.Module):
    """
    Multi-Scale Isolation Forest LSTM.

    Input: (batch, seq_len, 384) - concatenated [metric, log, trace] embeddings
    Output: (batch, 1) - anomaly score logits
    """

    def __init__(self, embedding_dim=384, lstm_hidden_dim=64, num_classes=1):
        super().__init__()
        self.embedding_dim = embedding_dim  # Changed from 3 to 384
        self.lstm_hidden_dim = lstm_hidden_dim

        # Multi-scale LSTM layers
        self.lstm1 = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=lstm_hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.3,
            bidirectional=True
        )

        self.lstm2 = nn.LSTM(
            input_size=lstm_hidden_dim * 2,  # Bidirectional
            hidden_size=lstm_hidden_dim // 2,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=lstm_hidden_dim,
            num_heads=4,
            batch_first=True
        )

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(lstm_hidden_dim, lstm_hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(lstm_hidden_dim // 2, num_classes)
        )

    def forward(self, x):
        """
        Args:
            x: (batch, seq_len, 384) - multimodal embeddings

        Returns:
            logits: (batch, 1) - anomaly score logits (apply sigmoid for probability)
        """
        # First LSTM layer
        lstm1_out, _ = self.lstm1(x)  # (batch, seq_len, lstm_hidden_dim*2)

        # Second LSTM layer
        lstm2_out, _ = self.lstm2(lstm1_out)  # (batch, seq_len, lstm_hidden_dim)

        # Attention pooling
        attn_out, _ = self.attention(lstm2_out, lstm2_out, lstm2_out)

        # Global average pooling
        pooled = attn_out.mean(dim=1)  # (batch, lstm_hidden_dim)

        # Classification
        logits = self.classifier(pooled)  # (batch, 1)

        return logits
