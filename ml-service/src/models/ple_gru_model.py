"""
PLE-GRU Model for multimodal anomaly detection.
Now accepts 384-dim concatenated embeddings (128 × 3 modalities).
"""

import torch
import torch.nn as nn


class VariableInputPLEGRU(nn.Module):
    """
    Probabilistic Label Enhancement GRU.

    Input: (batch, seq_len, 384) - concatenated [metric, log, trace] embeddings
    Output: (batch, 1) - anomaly score logits
    """

    def __init__(self, embedding_dim=384, gru_hidden_dim=64, num_classes=1):
        super().__init__()
        self.embedding_dim = embedding_dim  # Changed from 3 to 384
        self.gru_hidden_dim = gru_hidden_dim

        # Multi-layer GRU
        self.gru1 = nn.GRU(
            input_size=embedding_dim,
            hidden_size=gru_hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.3,
            bidirectional=True
        )

        self.gru2 = nn.GRU(
            input_size=gru_hidden_dim * 2,  # Bidirectional
            hidden_size=gru_hidden_dim // 2,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )

        # Self-attention
        self.attention = nn.MultiheadAttention(
            embed_dim=gru_hidden_dim,
            num_heads=4,
            batch_first=True
        )

        # Probabilistic enhancement layer
        self.enhancement = nn.Sequential(
            nn.Linear(gru_hidden_dim, gru_hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(gru_hidden_dim, gru_hidden_dim)
        )

        # Classification head
        self.classifier = nn.Sequential(
            nn.Linear(gru_hidden_dim, gru_hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(gru_hidden_dim // 2, num_classes)
        )

    def forward(self, x):
        """
        Args:
            x: (batch, seq_len, 384) - multimodal embeddings

        Returns:
            logits: (batch, 1) - anomaly score logits (apply sigmoid for probability)
        """
        # First GRU layer
        gru1_out, _ = self.gru1(x)  # (batch, seq_len, gru_hidden_dim*2)

        # Second GRU layer
        gru2_out, _ = self.gru2(gru1_out)  # (batch, seq_len, gru_hidden_dim)

        # Attention pooling
        attn_out, _ = self.attention(gru2_out, gru2_out, gru2_out)

        # Global average pooling
        pooled = attn_out.mean(dim=1)  # (batch, gru_hidden_dim)

        # Probabilistic enhancement
        enhanced = self.enhancement(pooled)

        # Residual connection
        enhanced = enhanced + pooled

        # Classification
        logits = self.classifier(enhanced)  # (batch, 1)

        return logits
