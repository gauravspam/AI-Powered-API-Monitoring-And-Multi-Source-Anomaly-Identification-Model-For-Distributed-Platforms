import torch
import torch.nn as nn


class VariableInputMSIF_LSTM(nn.Module):
    def __init__(self, embedding_dim=128, lstm_hidden_dim=64, num_layers=2):
        super(VariableInputMSIF_LSTM, self).__init__()
        self.embedding_dim = embedding_dim

        # LSTM extracts temporal patterns
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=lstm_hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=0.3,
        )

        # Attention Mechanism
        self.attn = nn.MultiheadAttention(
            embed_dim=lstm_hidden_dim * 2, num_heads=4, batch_first=True
        )

        # Classifier
        self.clf = nn.Sequential(
            nn.Linear(lstm_hidden_dim * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        # x shape: (Batch, Features) OR (Batch, Seq, Features)

        # FIX: Ensure 3D input for LSTM
        if x.dim() == 2:
            x = x.unsqueeze(1)  # (Batch, 1, Features)

        out, _ = self.lstm(x)
        attn_out, _ = self.attn(out, out, out)
        return self.clf(attn_out.mean(dim=1))

    def predict(self, x):
        self.eval()
        with torch.no_grad():
            if x.dim() == 2:
                x = x.unsqueeze(1)
            if x.dim() == 2: x = x.unsqueeze(1)
            return float(self.forward(x).item())
