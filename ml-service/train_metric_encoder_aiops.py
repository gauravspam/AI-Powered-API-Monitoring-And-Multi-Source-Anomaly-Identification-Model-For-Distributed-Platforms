"""
Train Metric Encoder using AIOps 2020 data
Pre-trains encoder on platform metrics using reconstruction
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import warnings
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class AIOpsMetricDataset(Dataset):
    def __init__(self, data_dir, window_size=32, stride=10, max_samples=8000):
        self.window_size = window_size
        self.windows = self.load_metrics(data_dir, stride, max_samples)
    
    def load_metrics(self, data_dir, stride, max_samples):
        all_windows = []
        
        date_folders = [
            "2020_04_11", "2020_04_21", "2020_04_22", "2020_04_23",
            "2020_05_22", "2020_05_23", "2020_05_24"
        ]
        
        for df in date_folders:
            path1 = os.path.join(data_dir, df, df, "平台指标/os_linux.csv")
            path2 = os.path.join(data_dir, df, df, "platform_metrics/os_linux.csv")
            path = path1 if os.path.exists(path1) else path2
            
            if not os.path.exists(path):
                continue
            
            try:
                print(f"[INFO] Loading {df}...")
                df_data = pd.read_csv(path)
                
                metric_names = df_data['name'].unique()[:38]
                df_filtered = df_data[df_data['name'].isin(metric_names)]
                df_filtered = df_filtered.sort_values('timestamp')
                
                pivot = df_filtered.pivot_table(
                    index='timestamp', columns='name', values='value', aggfunc='mean'
                ).fillna(0)
                
                data = pivot.values
                data = (data - data.mean(axis=0)) / (data.std(axis=0) + 1e-8)
                
                for i in range(0, len(data) - self.window_size, stride):
                    all_windows.append(data[i:i+self.window_size])
                    
            except Exception as e:
                print(f"[WARN] {df}: {e}")
        
        print(f"[INFO] Total windows: {len(all_windows)}")
        return np.array(all_windows[:max_samples])
    
    def __len__(self):
        return len(self.windows)
    
    def __getitem__(self, idx):
        return torch.tensor(self.windows[idx], dtype=torch.float32)


class SimpleMetricEncoder(nn.Module):
    """Simple autoencoder for metrics - LSTM encoder + FC decoder"""
    def __init__(self, input_dim=38, hidden_dim=64, embedding_dim=128):
        super().__init__()
        
        # Encoder: LSTM processes time series
        self.encoder_lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.2
        )
        
        # Project to embedding
        self.encoder_proj = nn.Sequential(
            nn.Linear(hidden_dim * 2, embedding_dim),
            nn.LayerNorm(embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )
        
        # Decoder: reconstruct input
        self.decoder = nn.Sequential(
            nn.Linear(embedding_dim, hidden_dim * 2),
            nn.ReLU(),
            nn.Linear(hidden_dim * 2, input_dim * 10)  # decode for 10 timesteps
        )
        
    def encode(self, x):
        # x: (batch, seq_len, input_dim)
        lstm_out, _ = self.encoder_lstm(x)
        # Use last timestep
        last_out = lstm_out[:, -1, :]  # (batch, hidden*2)
        embedding = self.encoder_proj(last_out)
        return embedding
    
    def forward(self, x):
        embedding = self.encode(x)
        # Reconstruction
        reconstructed = self.decoder(embedding)
        return reconstructed, embedding


def train_encoder(encoder, train_loader, epochs=10, lr=1e-4, device='cuda'):
    encoder = encoder.to(device)
    optimizer = torch.optim.Adam(encoder.parameters(), lr=lr)
    criterion = nn.MSELoss()
    
    for epoch in range(epochs):
        encoder.train()
        total_loss = 0
        
        for batch in train_loader:
            batch = batch.to(device)
            
            reconstructed, embedding = encoder(batch)
            
            # Reconstruct - try to predict next few timesteps
            target = batch[:, -10:, :].reshape(batch.size(0), -1)  # Last 10 timesteps
            
            loss = criterion(reconstructed, target)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        print(f"  Epoch {epoch+1}/{epochs}: Loss={total_loss/len(train_loader):.4f}")
    
    return encoder


def main():
    parser = argparse.ArgumentParser(description='Train metric encoder on AIOps')
    parser.add_argument('--epochs', type=int, default=10)
    parser.add_argument('--batch_size', type=int, default=64)
    parser.add_argument('--lr', type=float, default=1e-4)
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--window_size', type=int, default=32)
    parser.add_argument('--stride', type=int, default=10)
    args = parser.parse_args()
    
    print("=" * 60)
    print("Training Metric Encoder on AIOps 2020")
    print(f"Device: {args.device}")
    print("=" * 60)
    
    data_dir = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/AIOps_Challenge_Data")
    dataset = AIOpsMetricDataset(data_dir, window_size=args.window_size, stride=args.stride)
    
    train_loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    
    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')
    
    encoder = SimpleMetricEncoder(input_dim=38, hidden_dim=64, embedding_dim=128)
    
    encoder = train_encoder(encoder, train_loader, epochs=args.epochs, lr=args.lr, device=device)
    
    save_dir = os.path.join(BASE_DIR, "models/encoders/metric")
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, "metric_encoder_pretrained.pth")
    torch.save(encoder.state_dict(), save_path)
    
    print(f"\n[OK] Saved encoder to {save_path}")


if __name__ == "__main__":
    main()