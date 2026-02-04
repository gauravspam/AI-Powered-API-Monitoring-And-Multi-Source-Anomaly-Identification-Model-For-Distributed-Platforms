import os
import sys

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from models.msif_lstm_model import VariableInputMSIF_LSTM

# --- CONFIG ---
# Use the day you already renamed successfully
BASE_DIR = "data/raw/train_ticket/AIOps挑战赛数据/2020_04_11"
METRICS_DIR = os.path.join(BASE_DIR, "metrics_platform")
LOGS_DIR = os.path.join(BASE_DIR, "metrics_business")
TRACES_DIR = os.path.join(BASE_DIR, "traces")

MODEL_SAVE_PATH = "models/enhanced/"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 32
WINDOW_SIZE = 60 * 1000  # 1 minute
EPOCHS = 20  # <--- Added Missing Variable


class MultiModalDataset(Dataset):
    def __init__(self):
        self.windows = self.load_and_align()

    def load_and_align(self):
        print("⏳ Loading and aligning multi-modal data...")
        if not os.path.exists(METRICS_DIR):
            print(f"❌ Directory not found: {METRICS_DIR}")
            return []

        # Load Data
        m_df = pd.read_csv(os.path.join(METRICS_DIR, "os_linux.csv"))
        m_df = m_df[m_df["cmdb_id"] == "os_001"].sort_values("timestamp")

        l_df = pd.read_csv(os.path.join(LOGS_DIR, "esb.csv"))
        l_df = l_df.sort_values("startTime")

        t_df = pd.read_csv(os.path.join(TRACES_DIR, "trace_csf.csv"))
        t_df = t_df[t_df["cmdb_id"] == "os_001"].sort_values("startTime")

        start_time = m_df["timestamp"].min()
        end_time = m_df["timestamp"].max()
        aligned_data = []

        for t_start in tqdm(range(start_time, end_time, WINDOW_SIZE)):
            t_end = t_start + WINDOW_SIZE

            # Aggregate Features
            m_slice = m_df[(m_df["timestamp"] >= t_start) & (m_df["timestamp"] < t_end)]
            m_val = m_slice["value"].mean() if not m_slice.empty else 0.0

            l_slice = l_df[(l_df["startTime"] >= t_start) & (l_df["startTime"] < t_end)]
            l_val = len(l_slice)

            t_slice = t_df[(t_df["startTime"] >= t_start) & (t_df["startTime"] < t_end)]
            t_val = t_slice["elapsedTime"].mean() if not t_slice.empty else 0.0

            # Handle NaNs
            if np.isnan(m_val):
                m_val = 0.0
            if np.isnan(t_val):
                t_val = 0.0

            # Simple Label Logic (Latency > 1s = Anomaly)
            label = 1.0 if t_val > 1000 else 0.0

            # (3,) Feature Vector
            feats = np.array([m_val, l_val, t_val], dtype=np.float32)
            feats = np.log1p(feats)

            aligned_data.append((feats, np.array([label], dtype=np.float32)))

        print(f"✅ Aligned {len(aligned_data)} time windows.")
        return aligned_data

    def __len__(self):
        return len(self.windows)

    def __getitem__(self, idx):
        return self.windows[idx]


def train():
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    dataset = MultiModalDataset()
    if len(dataset) == 0:
        return

    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    model = VariableInputMSIF_LSTM(embedding_dim=3, lstm_hidden_dim=64).to(DEVICE)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.BCELoss()

    model.train()
    print(f"🚀 Training MSIF-LSTM on {DEVICE}...")

    for epoch in range(EPOCHS):
        total_loss = 0
        for x, y in loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            optimizer.zero_grad()
            output = model(x)  # Input (Batch, 3) -> Model expands to (Batch, 1, 3)
            loss = criterion(output, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch + 1}/{EPOCHS} Loss: {total_loss / len(loader):.4f}")

    torch.save(model.state_dict(), os.path.join(MODEL_SAVE_PATH, "msif_lstm.pth"))
    print("✅ MSIF-LSTM Saved.")


if __name__ == "__main__":
    train()
