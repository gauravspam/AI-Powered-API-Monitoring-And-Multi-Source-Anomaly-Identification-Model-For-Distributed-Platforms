import json
import os

import numpy as np
import pandas as pd

# --- CONFIG ---
# Adjusted paths based on your tree output
NAB_ROOT = "data/NAB"
DATA_FILE_REL = "data/realKnownCause/ec2_request_latency_system_failure.csv"
LABELS_FILE_REL = "labels/combined_labels.json"
OUTPUT_FILE = "data/nab_processed_proper.csv"

def load_and_label_nab():
    print("⏳ Starting NAB data preparation...")

    # 1. Load Raw Data
    full_data_path = os.path.join(NAB_ROOT, DATA_FILE_REL)
    print(f"   -> Looking for data at: {full_data_path}")

    if not os.path.exists(full_data_path):
        print(f"❌ Error: Data file not found at {full_data_path}")
        return

    df = pd.read_csv(full_data_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    print(f"✅ Loaded {len(df)} rows.")

    # 2. Load Labels
    full_labels_path = os.path.join(NAB_ROOT, LABELS_FILE_REL)
    print(f"   -> Looking for labels at: {full_labels_path}")

    if not os.path.exists(full_labels_path):
        print(f"❌ Error: Labels file not found at {full_labels_path}")
        return

    with open(full_labels_path, "r") as f:
        labels_json = json.load(f)

    # 3. Match Labels to File
    # The JSON keys in NAB usually look like "realKnownCause/ec2_request_latency_system_failure.csv"
    # We need to match that key style.
    target_key = "realKnownCause/ec2_request_latency_system_failure.csv"

    if target_key not in labels_json:
        print(f"❌ Error: Key '{target_key}' not found in labels JSON.")
        print(f"   Available keys example: {list(labels_json.keys())[:3]}")
        return

    anomaly_timestamps = labels_json[target_key]
    print(f"✅ Found {len(anomaly_timestamps)} anomaly timestamps for this file.")

    # 4. Labeling Logic
    # NAB provides specific timestamps. We will mark a window around them as anomalous.
    df["label"] = 0
    # Window: +/- 5 minutes around the anomaly timestamp is common for point anomalies
    window_minutes = 6

    for ts_str in anomaly_timestamps:
        ts = pd.to_datetime(ts_str)
        # Mark rows within the window
        mask = (df["timestamp"] >= (ts - pd.Timedelta(minutes=window_minutes))) & (
            df["timestamp"] <= (ts + pd.Timedelta(minutes=window_minutes))
        )
        df.loc[mask, "label"] = 1

    print(f"📊 Label Distribution:\n{df['label'].value_counts()}")

    # 5. Feature Engineering
    print("🛠️ Engineering features...")
    # Time features
    df["hour"] = df["timestamp"].dt.hour
    df["day_of_week"] = df["timestamp"].dt.dayofweek

    # Rolling Statistics (Lag features)
    # Important: Shift to avoid data leakage (using current value to predict current label)
    df["rolling_mean_3"] = df["value"].shift(1).rolling(window=3).mean()
    df["rolling_std_3"] = df["value"].shift(1).rolling(window=3).std()
    df["rolling_mean_12"] = df["value"].shift(1).rolling(window=12).mean()  # ~1 hour
    df["rolling_std_12"] = df["value"].shift(1).rolling(window=12).std()

    # Simple differencing
    df["diff"] = df["value"].diff()

    df.bfill(inplace=True)
    df.fillna(0, inplace=True)  # Cleanup any remaining NaNs

    # Save
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✅ Saved processed dataset to {OUTPUT_FILE}")

    print(f"✅ Saved processed dataset to {OUTPUT_FILE}")

if __name__ == "__main__":
    load_and_label_nab()
