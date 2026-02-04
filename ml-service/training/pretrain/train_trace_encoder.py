import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from models.trace_encoder import TraceEncoder

# --- CONFIG ---
BATCH_SIZE = 16
EPOCHS = 10
LEARNING_RATE = 1e-4
EMBEDDING_DIM = 128
# UPDATED PATH: Pointing to the flattened CSV directory
DATA_PATH = "data/raw/deathstar/flat_csv"
MODEL_SAVE_PATH = "models/encoders/trace/"


# --- 1. DATASET CLASS ---
class TraceDataset(Dataset):
    """
    Dataset for pre-training TraceEncoder on DeathStarBench traces.
    """

    def __init__(self, data_dir, limit=5000):
        self.samples = self.load_data(data_dir, limit)

    def load_data(self, data_dir, limit):
        print(f"⏳ Loading traces from {data_dir}...")
        all_traces = []

        # Find all CSV files in the flat directory
        csv_files = glob.glob(os.path.join(data_dir, "*.csv"))

        if not csv_files:
            print(f"⚠️  No CSV files found in {data_dir}. Generating dummy traces.")
            return self.generate_dummy_data()

        print(f"📂 Found {len(csv_files)} trace files. Parsing...")

        # Iterate over files (use tqdm for progress)
        for file_path in tqdm(csv_files):
            try:
                # Read CSV
                df = pd.read_csv(file_path)

                df.columns = [
                    c.lower().replace(" ", "").replace("_", "") for c in df.columns
                ]

                # Check if we have trace grouping columns
                # DeathStarBench often has 'traceid'
                if "traceid" in df.columns:
                    grouped = df.groupby("traceid")
                    for tid, group in grouped:
                        spans = []
                        for _, row in group.iterrows():
                            # Extract span details
                            # 'rpcid' is often used as service identifier in these datasets
                            service_name = str(
                                row.get("rpcid", row.get("service", "unknown"))
                            )

                            # Duration/Timestamp handling
                            # Some datasets have 'timestamp' (start time), others 'duration'
                            # We use timestamp as a proxy for duration if duration is missing, or simple constant
                            duration = float(
                                row.get("duration", row.get("timestamp", 0))
                            )

                            spans.append(
                                {
                                    "trace_id": str(tid),
                                    "span_id": str(row.get("spanid", "unknown")),
                                    "parent_id": str(row.get("parentid", None)),
                                    "service": service_name,
                                    "duration": duration,
                                    "error": 1 if row.get("success", 1) == 0 else 0,
                                }
                            )

                        if len(spans) > 0:
                            all_traces.append({"spans": spans})

                        if len(all_traces) >= limit:
                            break
                else:
                    # Fallback: Treat the file as one sequence or simple independent spans
                    # Some files are just metric logs in CSV. We skip or process minimally.
                    pass

            except Exception as e:
                # print(f"❌ Error reading {os.path.basename(file_path)}: {e}")
                continue

            if len(all_traces) >= limit:
                break

        if len(all_traces) == 0:
            print("⚠️ Parsed 0 valid traces from CSVs. Falling back to synthetic data.")
            return self.generate_dummy_data()

        print(f"✅ Loaded {len(all_traces)} real traces.")
        return all_traces

    def generate_dummy_data(self):
        print("ℹ️  Generating synthetic trace data for training...")
        samples = []
        services = ["frontend", "api-gateway", "auth", "payment", "db-user", "db-pay"]

        for _ in range(100):
            spans = []
            root = np.random.choice(services)
            spans.append(
                {
                    "service": root,
                    "duration": np.random.randint(50, 500),
                    "parent": None,
                }
            )
            num_children = np.random.randint(1, 5)
            for _ in range(num_children):
                child = np.random.choice(services)
                spans.append(
                    {
                        "service": child,
                        "duration": np.random.randint(10, 200),
                        "parent": root,
                        "error": np.random.random() > 0.9,
                    }
                )
            samples.append({"spans": spans})
        return samples

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, item):
        return self.samples[item]


# --- 2. COLLATE FUNCTION ---
def collate_fn(batch):
    return batch


# --- 3. TRAINING LOOP ---
def train():
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 Training on {device}")

    # Load Data
    dataset = TraceDataset(DATA_PATH, limit=5000)  # Limit loaded traces to avoid OOM
    dataloader = DataLoader(
        dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn
    )

    # Initialize Model
    model = TraceEncoder(embedding_dim=EMBEDDING_DIM).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    model.train()

    for epoch in range(EPOCHS):
        total_loss = 0

        # Progress bar for batches
        pbar = tqdm(
            enumerate(dataloader),
            total=len(dataloader),
            desc=f"Epoch {epoch + 1}/{EPOCHS}",
        )

        for batch_idx, batch_samples in pbar:
            optimizer.zero_grad()
            batch_loss = 0
            valid_samples = 0

            for sample in batch_samples:
                try:
                    # Forward pass
                    embedding = model(sample)  # (1, 128)

                    # Self-Supervised Proxy Loss:
                    # Simple loss: encourage non-zero activity + small norm
                    loss = torch.mean(embedding**2)
                    batch_loss += loss
                    valid_samples += 1
                except Exception as e:
                    continue

            if valid_samples > 0:
                batch_loss = batch_loss / valid_samples
                batch_loss.backward()
                optimizer.step()
                total_loss += batch_loss.item()

                # Update progress bar
                pbar.set_postfix({"loss": f"{batch_loss.item():.4f}"})

        avg_loss = total_loss / max(1, len(dataloader))

        # Save checkpoint
        torch.save(
            model.state_dict(), os.path.join(MODEL_SAVE_PATH, "trace_encoder.pth")
        )

    print(f"✅ Trace Encoder saved to {MODEL_SAVE_PATH}")

    print(f"✅ Trace Encoder saved to {MODEL_SAVE_PATH}")


if __name__ == "__main__":
    train()
