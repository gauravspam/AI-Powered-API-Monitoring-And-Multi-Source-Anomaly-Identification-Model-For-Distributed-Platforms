"""
Train Trace Encoder with Bi-LSTM + Attention
Bi-directional processing with attention for anomaly focus
~1-2M params, ~8MB
"""

import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np

EPOCHS = 10
BATCH_SIZE = 16
LEARNING_RATE = 1e-3
EMBEDDING_DIM = 128
MODEL_SAVE_PATH = "models/encoders/trace/"


class BiLSTMAttention(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers=2, dropout=0.2):
        super(BiLSTMAttention, self).__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        self.bi_lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, 1),
            nn.Softmax(dim=1)
        )
        
        self.output_projection = nn.Linear(hidden_dim * 2, hidden_dim)
    
    def forward(self, x):
        encoded = self.encoder(x)
        lstm_out, _ = self.bi_lstm(encoded)
        attn_weights = self.attention(lstm_out)
        context = (lstm_out * attn_weights).sum(dim=1)
        output = self.output_projection(context)
        return output


class TraceDataset(Dataset):
    def __init__(self, size=5000, max_spans=20):
        self.size = size
        self.max_spans = max_spans
        self.node_feature_dim = 10
    
    def __len__(self):
        return self.size
    
    def __getitem__(self, idx):
        num_spans = np.random.randint(3, self.max_spans)
        
        spans = []
        for i in range(num_spans):
            duration = np.random.rand() * 2000
            error = np.random.rand() > 0.9
            timestamp = np.random.rand() * 1e12
            
            features = [
                np.log1p(duration) / 10.0,
                float(error),
                i / 100.0,
                timestamp / 1e12,
                timestamp / 1e12,
                timestamp / 1e12,
                float(i > 0),
                float(duration > 1000),
                np.random.rand(),
                np.random.rand()
            ]
            spans.append(features)
        
        while len(spans) < 5:
            spans.append([0] * 10)
        
        return torch.FloatTensor(spans[:5])


def train():
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")
    
    dataset = TraceDataset(size=5000)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    input_dim = 10
    model = BiLSTMAttention(
        input_dim=input_dim,
        hidden_dim=EMBEDDING_DIM,
        num_layers=2,
        dropout=0.2
    ).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0
        for batch in dataloader:
            batch = batch.to(device)
            
            optimizer.zero_grad()
            output = model(batch)
            loss = output.mean()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        print(f"Epoch {epoch+1}/{EPOCHS} Loss: {total_loss/len(dataloader):.4f}")
    
    save_path = os.path.join(MODEL_SAVE_PATH, "trace_encoder.pth")
    torch.save(model.state_dict(), save_path)
    print(f"Saved to {save_path}")
    print(f"Model size: {os.path.getsize(save_path) / 1024:.1f} KB")


if __name__ == "__main__":
    train()