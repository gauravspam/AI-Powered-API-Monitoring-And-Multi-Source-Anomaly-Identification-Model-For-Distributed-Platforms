import os
import sys

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from models.ple_gru_model import VariableInputPLE_GRU

# --- CONFIG ---
BASE_DIR = "data/raw/train_ticket/AIOps挑战赛数据/2020_04_11"
METRICS_DIR = os.path.join(BASE_DIR, "metrics_platform")
LOGS_DIR = os.path.join(BASE_DIR, "metrics_business")
TRACES_DIR = os.path.join(BASE_DIR, "traces")

MODEL_SAVE_PATH = "models/enhanced/"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 32
WINDOW_SIZE = 60 * 1000  # 1 minute
EPOCHS = 20
NUM_EXPERTS = 3  # Experts: 1 for Metric focus, 1 for Log focus, 1 for Trace focus


class MultiModalDataset(Dataset):
    def __init__(self):
        self.windows = self.load_and_align()

    def load_and_align(self):
        print("⏳ Loading and aligning multi-modal data for PLE-GRU...")
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

            # Aggregate
            m_slice = m_df[(m_df["timestamp"] >= t_start) & (m_df["timestamp"] < t_end)]
            m_val = m_slice["value"].mean() if not m_slice.empty else 0.0

            l_slice = l_df[(l_df["startTime"] >= t_start) & (l_df["startTime"] < t_end)]
            l_val = len(l_slice)

            t_slice = t_df[(t_df["startTime"] >= t_start) & (t_df["startTime"] < t_end)]
            t_val = t_slice["elapsedTime"].mean() if not t_slice.empty else 0.0

            # NaNs
            if np.isnan(m_val):
                m_val = 0.0
            if np.isnan(t_val):
                t_val = 0.0

            # Label
            label = 1.0 if t_val > 1000 else 0.0

            # Features
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

    # Model: PLE-GRU
    # Embedding dim 3 (features), Hidden 64, 3 Experts
    model = VariableInputPLE_GRU(
        embedding_dim=3, gru_hidden_dim=64, num_experts=NUM_EXPERTS
    ).to(DEVICE)

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.BCELoss()

    model.train()
    print(f"🚀 Training PLE-GRU on {DEVICE}...")

    for epoch in range(EPOCHS):
        total_loss = 0
        for x, y in loader:
            x, y = x.to(DEVICE), y.to(DEVICE)
            optimizer.zero_grad()

            output = model(x)
            loss = criterion(output, y)

            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        print(f"Epoch {epoch + 1}/{EPOCHS} Loss: {total_loss / len(loader):.4f}")

    torch.save(model.state_dict(), os.path.join(MODEL_SAVE_PATH, "ple_gru.pth"))
    print("✅ PLE-GRU Saved.")


if __name__ == "__main__":
    train()
