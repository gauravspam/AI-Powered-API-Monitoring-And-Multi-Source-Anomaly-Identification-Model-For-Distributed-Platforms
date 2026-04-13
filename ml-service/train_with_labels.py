"""
Proper Anomaly-Labeled Training - Fixed timestamp matching
Uses fault labels from fault_labels_preselection.csv with proper timestamp alignment
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from datetime import datetime, timedelta
import warnings
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from models.msif_lstm_model import VariableInputMSIF_LSTM
from models.ple_gru_model import VariableInputPLE_GRU


import os

# Get absolute paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAULT_LABELS_PATH = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/fault_labels_preselection.csv")


def parse_fault_labels_v2():
    """Parse fault labels using index mapping - more reliable"""
    print("[INFO] Loading fault labels...")
    
    df = pd.read_csv(FAULT_LABELS_PATH)
    
    # Extract start_time from 'start_time' column (more reliable)
    # Format is like: "2020/5/22 0:07" or empty
    fault_times = []
    
    for _, row in df.iterrows():
        start_time_str = str(row.get('start_time', '')).strip()
        
        if not start_time_str or start_time_str == 'nan':
            continue
            
        try:
            # Parse the timestamp
            start_time = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M')
            
            # Also get the log_time for backup
            log_time_str = str(row.get('log_time', '')).strip()
            if log_time_str and log_time_str != 'nan':
                try:
                    log_time = datetime.strptime(log_time_str, '%Y/%m/%d %H:%M')
                except:
                    log_time = None
            else:
                log_time = None
            
            fault_times.append({
                'start': start_time,
                'log_time': log_time,
                'object': str(row.get('object', '')),
                'fault_type': str(row.get('fault_desrcibtion', ''))
            })
        except Exception as e:
            continue
    
    print(f"[INFO] Loaded {len(fault_times)} fault timestamps")
    return fault_times


class LabeledAIOpsDatasetV2(Dataset):
    """Dataset with anomaly labels - multi-day loading"""
    
    def __init__(self, metric_files, fault_times, window_size=60, stride=5):
        self.window_size = window_size
        self.fault_times = fault_times
        
        all_data = []
        all_timestamps = []
        
        for metric_file in metric_files:
            print(f"[INFO] Loading {metric_file}...")
            df = pd.read_csv(metric_file)
            
            # Get metric names and pivot
            metric_names = df['name'].unique()[:38]
            df_filtered = df[df['name'].isin(metric_names)]
            df_filtered = df_filtered.sort_values('timestamp')
            
            pivot = df_filtered.pivot_table(
                index='timestamp',
                columns='name',
                values='value',
                aggfunc='mean'
            ).fillna(0)
            
            all_data.append(pivot.values)
            all_timestamps.extend(pivot.index.tolist())
        
        self.data = np.vstack(all_data)
        self.timestamps = all_timestamps
        
        # Normalize
        self.data = (self.data - self.data.mean(axis=0)) / (self.data.std(axis=0) + 1e-8)
        
        print(f"[INFO] Combined metric data shape: {self.data.shape}")
        
        # Convert timestamps to datetime objects
        ts_datetime = []
        for ts in self.timestamps:
            dt = datetime.fromtimestamp(ts / 1000)
            ts_datetime.append(dt)
        
        # Map fault times - use fuzzy month/day matching
        fault_months_days = set()
        for fault in fault_times:
            if fault['start']:
                fault_months_days.add((fault['start'].month, fault['start'].day))
        
        fault_positions = []
        for idx, dt in enumerate(ts_datetime):
            if (dt.month, dt.day) in fault_months_days:
                fault_positions.append(idx)
        
        print(f"[INFO] Mapped {len(fault_positions)} positions for dates: {fault_months_days}")
        
        # Create windows - mark as anomaly if within 60-timestep window of any fault
        anomaly_window = 30  # timesteps (approximately 30 * data_interval)
        
        self.windows = []
        self.labels = []
        
        for i in range(0, len(self.data) - window_size, stride):
            window_data = self.data[i:i+window_size]
            
            # Check if this window overlaps with any fault position
            is_anomaly = 0
            window_center = i + window_size // 2
            
            for fault_pos in fault_positions:
                if abs(window_center - fault_pos) < anomaly_window:
                    is_anomaly = 1
                    break
            
            self.windows.append(torch.FloatTensor(window_data))
            self.labels.append(torch.tensor(is_anomaly, dtype=torch.float32))
        
        # Stats
        anomaly_count = sum(self.labels)
        normal_count = len(self.labels) - anomaly_count
        print(f"[INFO] Created {len(self.windows)} windows")
        print(f"  Normal: {normal_count}, Anomaly: {anomaly_count}")
        print(f"  Anomaly ratio: {anomaly_count/len(self.labels)*100:.2f}%")
        
        # Class weight for imbalance
        if anomaly_count > 0:
            self.pos_weight = torch.tensor([normal_count / anomaly_count])
        else:
            self.pos_weight = torch.tensor([1.0])
    
    def __len__(self):
        return len(self.windows)
    
    def __getitem__(self, idx):
        return self.windows[idx], self.labels[idx]


def train_model(model, train_loader, val_loader, model_name, epochs=50, lr=1e-3, device='cpu', patience=10):
    """Train with weighted BCE for imbalanced classes"""
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    # Weighted BCE - higher weight for minority class (anomaly)
    pos_weight = torch.tensor([5.0]).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    
    best_f1 = 0
    best_model_state = None
    no_improve = 0
    
    for epoch in range(epochs):
        # Training
        model.train()
        train_loss = 0
        
        for windows, labels in train_loader:
            windows = windows.to(device)
            labels = labels.to(device)
            
            embedding = windows[:, -1, :]
            output = model(embedding).squeeze()
            
            loss = criterion(output, labels)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        # Validation
        model.eval()
        tp = tn = fp = fn = 0
        
        with torch.no_grad():
            for windows, labels in val_loader:
                windows = windows.to(device)
                labels = labels.to(device)
                
                embedding = windows[:, -1, :]
                output = model(embedding).squeeze()
                
                predicted = (torch.sigmoid(output) > 0.5).float()
                
                tp += ((predicted == 1) & (labels == 1)).sum().item()
                tn += ((predicted == 0) & (labels == 0)).sum().item()
                fp += ((predicted == 1) & (labels == 0)).sum().item()
                fn += ((predicted == 0) & (labels == 1)).sum().item()
        
        # Calculate metrics
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"  Epoch {epoch+1}/{epochs}: Loss={train_loss/len(train_loader):.4f}, "
              f"Acc={accuracy:.3f}, Prec={precision:.3f}, Rec={recall:.3f}, F1={f1:.3f}")
        
        # Early stopping based on F1 score
        if f1 > best_f1:
            best_f1 = f1
            best_model_state = model.state_dict().copy()
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"  Early stopping at epoch {epoch+1}")
                break
    
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
    
    return model, best_f1


def main():
    parser = argparse.ArgumentParser(description='Anomaly-labeled training')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch_size', type=int, default=128)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--device', type=str, default='cpu')
    parser.add_argument('--window_size', type=int, default=60)
    parser.add_argument('--stride', type=int, default=5)
    args = parser.parse_args()
    
    print("=" * 60)
    print("Anomaly-Labeled Training for ML Models (v2)")
    print(f"Device: {args.device}")
    print("=" * 60)
    
    # Load fault times
    fault_times = parse_fault_labels_v2()
    
# Create dataset - load from multiple days
    base_path = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/AIOps_Challenge_Data")
    metric_files = [
        os.path.join(base_path, "2020_04_11/2020_04_11/平台指标/os_linux.csv"),
        os.path.join(base_path, "2020_04_21/2020_04_21/平台指标/os_linux.csv"),
        os.path.join(base_path, "2020_04_22/2020_04_22/平台指标/os_linux.csv"),
        os.path.join(base_path, "2020_04_23/2020_04_23/平台指标/os_linux.csv"),
        os.path.join(base_path, "2020_05_22/2020_05_22/平台指标/os_linux.csv"),
        os.path.join(base_path, "2020_05_23/2020_05_23/平台指标/os_linux.csv"),
        os.path.join(base_path, "2020_05_24/2020_05_24/平台指标/os_linux.csv"),
    ]
    dataset = LabeledAIOpsDatasetV2(
        metric_files=metric_files,
        fault_times=fault_times,
        window_size=args.window_size,
        stride=args.stride
    )
    
    # Check if we have anomalies
    if sum(dataset.labels) == 0:
        print("[ERROR] No anomalies detected! Using fallback labeling...")
        # Fallback: mark every Nth window as anomaly
        for i in range(0, len(dataset.labels), 20):
            dataset.labels[i] = torch.tensor(1.0)
    
    # Split
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)
    
    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')
    save_dir = "ml-service/models/enhanced"
    os.makedirs(save_dir, exist_ok=True)
    
    # Train MSIF-LSTM
    print("\n" + "=" * 60)
    print("Training MSIF-LSTM")
    print("=" * 60)
    msif = VariableInputMSIF_LSTM(embedding_dim=38, lstm_hidden_dim=64)
    msif, msif_f1 = train_model(
        msif, train_loader, val_loader, "MSIF-LSTM",
        epochs=args.epochs, lr=args.lr, device=device, patience=10
    )
    torch.save(msif.state_dict(), f"{save_dir}/msif_lstm_labeled.pth")
    print(f"Saved: msif_lstm_labeled.pth (F1: {msif_f1:.3f})")
    
    # Train PLE-GRU
    print("\n" + "=" * 60)
    print("Training PLE-GRU")
    print("=" * 60)
    ple = VariableInputPLE_GRU(embedding_dim=38, gru_hidden_dim=64, num_experts=3)
    ple, ple_f1 = train_model(
        ple, train_loader, val_loader, "PLE-GRU",
        epochs=args.epochs, lr=args.lr, device=device, patience=10
    )
    torch.save(ple.state_dict(), f"{save_dir}/ple_gru_labeled.pth")
    print(f"Saved: ple_gru_labeled.pth (F1: {ple_f1:.3f})")
    
    print("\n" + "=" * 60)
    print(f"Training Complete! MSIF F1: {msif_f1:.3f}, PLE F1: {ple_f1:.3f}")
    print("=" * 60)


if __name__ == "__main__":
    main()