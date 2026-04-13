"""
Quick Training Script for Multi-Modal Models
Trains MSIF-LSTM and PLE-GRU directly on AIOps metric data with synthetic anomaly labels
"""

import os
import sys
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from models.msif_lstm_model import VariableInputMSIF_LSTM
from models.ple_gru_model import VariableInputPLE_GRU
from models.hybrid_fusion import HybridFusion


class AIOpsDataset(Dataset):
    """Simple dataset from AIOps metrics"""
    
    def __init__(self, csv_path, window_size=60):
        import pandas as pd
        
        print("[INFO] Loading metric data...")
        df = pd.read_csv(csv_path)
        
        # Pivot to get feature matrix
        metric_names = df['name'].unique()[:38]
        df_filtered = df[df['name'].isin(metric_names)]
        pivot = df_filtered.pivot_table(
            index='timestamp',
            columns='name',
            values='value',
            aggfunc='mean'
        ).fillna(0).values
        
        # Normalize
        self.data = (pivot - pivot.mean(axis=0)) / (pivot.std(axis=0) + 1e-8)
        self.window_size = window_size
        
        # Create windows
        self.windows = []
        for i in range(0, len(self.data) - window_size, 10):
            window = self.data[i:i+window_size]
            self.windows.append(torch.FloatTensor(window))
        
        print(f"Created {len(self.windows)} windows, each {window_size}x{self.data.shape[1]}")
    
    def __len__(self):
        return len(self.windows)
    
    def __getitem__(self, idx):
        window = self.windows[idx]
        
        # Create synthetic labels based on anomaly detection heuristics
        # High CPU, memory, or unusual patterns = anomaly
        last_values = window[-1]  # Last timestep
        
        # Simple rule: if any metric > 2 std above mean, it's an anomaly
        label = 1.0 if (last_values > 2.0).any() else 0.0
        
        # Add some noise to labels
        if np.random.random() < 0.1:
            label = 1.0 - label
        
        return window, torch.tensor(label, dtype=torch.float32)


def train_model(model, train_loader, epochs=10, lr=1e-4, device='cpu'):
    """Train a single model"""
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()
    
    model.train()
    for epoch in range(epochs):
        total_loss = 0
        for windows, labels in train_loader:
            windows = windows.to(device)  # (batch, window, features)
            labels = labels.to(device)
            
            # Use last timestep as embedding (38-dim)
            embedding = windows[:, -1, :]  # (batch, 38)
            
            # Forward
            output = model(embedding).squeeze()
            
            # Loss
            loss = criterion(output, labels)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        print(f"  Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.4f}")
    
    return model


def main():
    parser = argparse.ArgumentParser(description='Quick train models')
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--device', type=str, default='cpu')
    args = parser.parse_args()
    
    print("=== Quick Model Training ===")
    
    # Data path
    csv_path = "C:/stack/project/AI-Powered-API-Monitoring-And-Multi-Source-Anomaly-Identification-Model-For-Distributed-Platforms/ml-service/dataset/AIOps挑战赛2020预赛数据/AIOps挑战赛数据/2020_05_31/2020_05_31/平台指标/os_linux.csv"
    
    # Create dataset
    dataset = AIOpsDataset(csv_path, window_size=60)
    train_loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    
    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')
    save_dir = "ml-service/models/enhanced"
    os.makedirs(save_dir, exist_ok=True)
    
    # Train MSIF-LSTM
    print("\n=== Training MSIF-LSTM ===")
    msif = VariableInputMSIF_LSTM(embedding_dim=38, lstm_hidden_dim=64)
    msif = train_model(msif, train_loader, epochs=args.epochs, device=device)
    torch.save(msif.state_dict(), f"{save_dir}/msif_lstm_aiops.pth")
    print(f"Saved: {save_dir}/msif_lstm_aiops.pth")
    
    # Train PLE-GRU
    print("\n=== Training PLE-GRU ===")
    ple = VariableInputPLE_GRU(embedding_dim=38, gru_hidden_dim=64, num_experts=3)
    ple = train_model(ple, train_loader, epochs=args.epochs, device=device)
    torch.save(ple.state_dict(), f"{save_dir}/ple_gru_aiops.pth")
    print(f"Saved: {save_dir}/ple_gru_aiops.pth")
    
    print("\n=== Training Complete ===")
    print("Models saved to:", save_dir)


if __name__ == "__main__":
    main()