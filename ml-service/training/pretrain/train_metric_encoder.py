import os
import sys

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset, random_split
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from models.metric_encoder import MetricEncoder

# --- CONFIG ---
BATCH_SIZE = 64
EPOCHS = 10
LEARNING_RATE = 1e-4
EMBEDDING_DIM = 128
WINDOW_SIZE = 64  # How many timestamps to feed into the LSTM
DATA_PATH = "data/raw/smd/train"
MODEL_SAVE_PATH = "models/encoders/metric/"


# --- 1. DATASET CLASS ---
class SMDDataset(Dataset):
    "Dataset for pre-training MetricEncoder on Server Machine Dataset (SMD)."

    def __init__(self, data_dir, window_size=64, stride=10, limit_files=None):
        self.window_size = window_size
        self.samples = self.load_data(data_dir, stride, limit_files)

    def load_data(self, data_dir, stride, limit_files):
        print(f"⏳ Loading metrics from {data_dir}...")
        all_windows = []

        if not os.path.exists(data_dir):
            print(f"⚠️  Data directory {data_dir} not found. Generating dummy metrics.")
            return self.generate_dummy_data()

        files = sorted([f for f in os.listdir(data_dir) if f.endswith(".txt")])
        if limit_files:
            files = files[:limit_files]

        if not files:
            return self.generate_dummy_data()

        print(f"📂 Found {len(files)} machine files. Processing...")

        for file_name in tqdm(files):
            try:
                # SMD format: CSV-like with 38 columns, no header
                file_path = os.path.join(data_dir, file_name)
                # Read strictly as float32 to save memory
                data = np.genfromtxt(file_path, delimiter=",", dtype=np.float32)

                # Check for NaN and replace
                if np.isnan(data).any():
                    data = np.nan_to_num(data)

                # Normalize (Z-score) per machine
                mean = data.mean(axis=0)
                std = data.std(axis=0) + 1e-6
                data = (data - mean) / std

                # Sliding window
                num_timestamps = data.shape[0]
                # We need data of shape (window_size, 38)

                for i in range(0, num_timestamps - self.window_size, stride):
                    window = data[i : i + self.window_size]
                    all_windows.append(window)

            except Exception as e:
                print(f"❌ Error loading {file_name}: {e}")
                continue

        if len(all_windows) == 0:
            return self.generate_dummy_data()

        print(f"✅ Created {len(all_windows)} metric windows.")
        return np.array(all_windows)  # (N, window, 38)

    def generate_dummy_data(self):
        print("ℹ️  Generating synthetic metric data...")
        # (N, window, features)
        return np.random.randn(1000, self.window_size, 38).astype(np.float32)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, item):
        # Return (window_size, 38)
        return torch.tensor(self.samples[item], dtype=torch.float32)


# --- 2. MODIFIED ENCODER FOR PRE-TRAINING ---
# The original encoder expects a dict input. For efficient pre-training on SMD,
# we need a wrapper or slightly modified forward pass to accept tensors directly.


class MetricPretrainer(nn.Module):
    def __init__(self, original_model):
        super().__init__()
        self.model = original_model
        # Strategy: Project 38 features -> embedding_dim directly using LSTM
        # We will override the core logic for this pre-training script only

        self.lstm = nn.LSTM(
            input_size=38,
            hidden_size=64,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
        )
        self.readout = nn.Sequential(
            nn.Linear(128, EMBEDDING_DIM),  # 64*2 directions
            nn.LayerNorm(EMBEDDING_DIM),
        )
        self.decoder = nn.Sequential(
            nn.Linear(EMBEDDING_DIM, 128),
            nn.ReLU(),
            nn.Linear(128, 38 * WINDOW_SIZE),  # Reconstruct input
        )

    def forward(self, x):
        # x: (batch, window, 38)
        out, (h_n, _) = self.lstm(x)
        # Take last hidden state
        h_last = torch.cat([h_n[-2], h_n[-1]], dim=1)  # (batch, 128)
        embedding = self.readout(h_last)

        # Reconstruction for self-supervised loss
        reconstruction = self.decoder(embedding)
        return embedding, reconstruction.view(x.shape)


# --- 3. TRAINING LOOP ---
def train():
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 Training on {device}")

    # Load Data
    dataset = SMDDataset(
        DATA_PATH, window_size=WINDOW_SIZE, stride=50
    )  # Stride 50 to reduce overlap/size

    # Split
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_set, val_set = random_split(dataset, [train_size, val_size])

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE, shuffle=False)

    # Initialize Model
    # We use a specialized pre-trainer wrapper
    base_encoder = MetricEncoder(embedding_dim=EMBEDDING_DIM)
    model = MetricPretrainer(base_encoder).to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()  # Reconstruction loss

    model.train()

    for epoch in range(EPOCHS):
        total_loss = 0
        pbar = tqdm(
            enumerate(train_loader),
            total=len(train_loader),
            desc=f"Epoch {epoch + 1}/{EPOCHS}",
        )

        for batch_idx, windows in pbar:
            windows = windows.to(device)  # (batch, window, 38)

            optimizer.zero_grad()

            embedding, reconstructed = model(windows)

            loss = criterion(reconstructed, windows)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        # Validation
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for windows in val_loader:
                windows = windows.to(device)
                _, recon = model(windows)
                val_loss += criterion(recon, windows).item()

        avg_val = val_loss / len(val_loader)
        # print(f"Val Loss: {avg_val:.4f}")
        model.train()

        # Save checkpoint
        torch.save(
            model.state_dict(),
            os.path.join(MODEL_SAVE_PATH, "metric_encoder_pretrained.pth"),
        )

    print(f"✅ Metric Encoder saved to {MODEL_SAVE_PATH}")

    print(f"✅ Metric Encoder saved to {MODEL_SAVE_PATH}")


if __name__ == "__main__":
    train()
