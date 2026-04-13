"""
Train Metric Encoder with TCN (Temporal Convolutional Network)
1D dilated convolutions for temporal patterns
~500K params, ~2MB
"""

import os
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np

EPOCHS = 10
BATCH_SIZE = 32
LEARNING_RATE = 1e-3
EMBEDDING_DIM = 128
MODEL_SAVE_PATH = "models/encoders/metric/"


class TemporalConvNet(nn.Module):
    def __init__(self, input_dim=9, embed_dim=128, num_channels=[32, 64, 64], kernel_size=3, dropout=0.2):
        super(TemporalConvNet, self).__init__()
        
        layers = []
        for i in range(len(num_channels)):
            in_ch = input_dim if i == 0 else num_channels[i-1]
            out_ch = num_channels[i]
            dilation = 2 ** i
            
            conv = nn.Conv1d(in_ch, out_ch, kernel_size, padding=(kernel_size-1)*dilation//2, dilation=dilation)
            layers.append(conv)
            layers.append(nn.BatchNorm1d(out_ch))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout))
        
        self.network = nn.Sequential(*layers)
        self.projection = nn.Linear(num_channels[-1], embed_dim)
    
    def forward(self, x):
        x = x.transpose(1, 2)
        x = self.network(x)
        x = x.transpose(1, 2)
        x = x.mean(dim=1)
        return self.projection(x)


class MetricDataset(Dataset):
    def __init__(self, size=5000, seq_len=10):
        self.size = size
        self.seq_len = seq_len
    
    def __len__(self):
        return self.size
    
    def __getitem__(self, idx):
        cpu = np.random.rand(self.seq_len) * 100
        memory = np.random.rand(self.seq_len) * 100
        disk = np.random.rand(self.seq_len) * 1000
        network = np.random.rand(self.seq_len) * 500
        response = np.random.rand(self.seq_len) * 5000
        error = np.random.rand(self.seq_len)
        
        features = np.stack([cpu, memory, disk, network, response, error], axis=1)
        return torch.FloatTensor(features)


def train():
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")
    
    dataset = MetricDataset(size=5000)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    input_dim = 6
    model = TemporalConvNet(input_dim=input_dim, embed_dim=EMBEDDING_DIM).to(device)
    
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
    
    save_path = os.path.join(MODEL_SAVE_PATH, "metric_encoder_tcn.pth")
    torch.save(model.state_dict(), save_path)
    print(f"Saved to {save_path}")
    print(f"Model size: {os.path.getsize(save_path) / 1024:.1f} KB")


if __name__ == "__main__":
    train()