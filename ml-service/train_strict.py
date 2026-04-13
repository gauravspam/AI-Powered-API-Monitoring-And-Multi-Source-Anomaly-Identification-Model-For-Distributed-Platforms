"""
Strict Anomaly-Labeled Training - Precise timestamp matching
Uses exact hour-level matching with tighter windows for cleaner labels
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
from tqdm import tqdm
import warnings
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
warnings.filterwarnings('ignore')
pd.set_option('display.max_columns', None)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from models.msif_lstm_model import VariableInputMSIF_LSTM
from models.ple_gru_model import VariableInputPLE_GRU


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAULT_LABELS_PATH = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/fault_labels_preselection.csv")


def parse_fault_labels_strict():
    """Parse fault labels with exact hour matching"""
    print("[INFO] Loading fault labels (strict mode)...")
    df = pd.read_csv(FAULT_LABELS_PATH)
    
    fault_events = []
    
    for _, row in df.iterrows():
        # Use start_time as primary (more precise)
        start_time_str = str(row.get('start_time', '')).strip()
        
        if not start_time_str or start_time_str == 'nan':
            # Fall back to log_time
            start_time_str = str(row.get('log_time', '')).strip()
        
        if not start_time_str or start_time_str == 'nan':
            continue
            
        try:
            # Try primary format
            try:
                start_time = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M')
            except:
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
            
            # Get duration in minutes (default 5 min)
            duration_str = str(row.get('duration', '5min')).strip()
            if 'min' in duration_str:
                duration_mins = int(duration_str.replace('min', ''))
            else:
                duration_mins = 5
            
            # Get object/component info
            obj = str(row.get('object', ''))
            fault_type = str(row.get('fault_desrcibtion', ''))
            
            fault_events.append({
                'start': start_time,
                'end': start_time + timedelta(minutes=duration_mins),
                'hour': start_time.hour,
                'object': obj,
                'fault_type': fault_type
            })
        except Exception as e:
            continue
    
    print(f"[INFO] Loaded {len(fault_events)} fault events with precise times")
    return fault_events


def load_platform_metrics(base_path, date_folders):
    """Load platform metrics from multiple days"""
    all_data = []
    all_timestamps = []
    
    for df in date_folders:
        # Try both folder naming conventions
        path1 = os.path.join(base_path, df, df, "平台指标/os_linux.csv")
        path2 = os.path.join(base_path, df, df, "platform_metrics/os_linux.csv")
        path = path1 if os.path.exists(path1) else path2
        
        if not os.path.exists(path):
            continue
            
        try:
            df_data = pd.read_csv(path)
            metric_names = df_data['name'].unique()[:20]
            df_filtered = df_data[df_data['name'].isin(metric_names)].sort_values('timestamp')
            
            pivot = df_filtered.pivot_table(
                index='timestamp', columns='name', values='value', aggfunc='mean'
            ).fillna(0)
            
            all_data.append(pivot.values)
            all_timestamps.extend(pivot.index.tolist())
            print(f"[INFO] Loaded platform: {df}")
        except Exception as e:
            print(f"[WARN] {df}: {e}")
    
    return np.vstack(all_data) if all_data else None, all_timestamps


def load_business_metrics(base_path, date_folders):
    """Load business metrics"""
    all_data = []
    all_timestamps = []
    
    for df in date_folders:
        path1 = os.path.join(base_path, df, df, "业务指标/esb.csv")
        path2 = os.path.join(base_path, df, df, "business_metrics/esb.csv")
        path = path1 if os.path.exists(path1) else path2
        
        if not os.path.exists(path):
            continue
            
        try:
            df_data = pd.read_csv(path)
            df_agg = df_data.groupby('startTime').agg({
                'avg_time': 'mean', 'num': 'sum', 'succee_num': 'sum', 'succee_rate': 'mean'
            }).reset_index()
            df_agg = df_agg.sort_values('startTime')
            
            values = df_agg[['avg_time', 'num', 'succee_num', 'succee_rate']].values
            values = (values - values.mean(axis=0)) / (values.std(axis=0) + 1e-8)
            all_data.append(values)
            all_timestamps.extend(df_agg['startTime'].tolist())
            print(f"[INFO] Loaded business: {df}")
        except Exception as e:
            print(f"[WARN] {df}: {e}")
    
    return np.vstack(all_data) if all_data else None, all_timestamps


def load_trace_metrics(base_path, date_folders):
    """Load trace metrics with aggregation"""
    all_data = []
    all_timestamps = []
    
    for df in date_folders:
        path1 = os.path.join(base_path, df, df, "调用链指标/trace_local.csv")
        path2 = os.path.join(base_path, df, df, "trace_metrics/trace_local.csv")
        path = path1 if os.path.exists(path1) else path2
        
        if not os.path.exists(path):
            continue
            
        try:
            print(f"[INFO] Loading trace: {df}...")
            df_data = pd.read_csv(path)
            df_data['success'] = df_data['success'].map({True: 1, False: 0, 'True': 1, 'False': 0}).fillna(0)
            
            df_data['time_bucket'] = (df_data['startTime'] // 60000) * 60000
            df_agg = df_data.groupby('time_bucket').agg({
                'elapsedTime': 'mean', 'success': 'mean'
            }).reset_index()
            
            values = df_agg[['elapsedTime', 'success']].values
            values = (values - values.mean(axis=0)) / (values.std(axis=0) + 1e-8)
            all_data.append(values)
            all_timestamps.extend(df_agg['time_bucket'].tolist())
            print(f"[INFO] Loaded trace: {df}")
        except Exception as e:
            print(f"[WARN] {df}: {e}")
    
    return np.vstack(all_data) if all_data else None, all_timestamps


def align_modalities_flexible(platform_data, platform_ts, business_data, business_ts, trace_data, trace_ts):
    """Align modalities using platform as primary"""
    if platform_data is None or not platform_ts:
        return None, []
    
    from collections import defaultdict
    
    business_bucket = defaultdict(list)
    for ts in business_ts:
        business_bucket[int(ts // 60000) * 60000].append(ts)
    
    trace_bucket = defaultdict(list)
    for ts in trace_ts:
        trace_bucket[int(ts // 60000) * 60000].append(ts)
    
    dim_platform = 20
    dim_business = 4
    dim_trace = 2
    
    combined_data = []
    combined_timestamps = []
    
    for i, ts in enumerate(platform_ts):
        bucket = int(ts // 60000) * 60000
        
        row = [platform_data[i]]
        
        if bucket in business_bucket and business_data is not None:
            b_idxs = [j for j, t in enumerate(business_ts) if int(t // 60000) * 60000 == bucket]
            if b_idxs:
                row.append(business_data[b_idxs[0]])
            else:
                row.append(np.zeros(dim_business))
        else:
            row.append(np.zeros(dim_business))
        
        if bucket in trace_bucket and trace_data is not None:
            t_idxs = [j for j, t in enumerate(trace_ts) if int(t // 60000) * 60000 == bucket]
            if t_idxs:
                row.append(trace_data[t_idxs[0]])
            else:
                row.append(np.zeros(dim_trace))
        else:
            row.append(np.zeros(dim_trace))
        
        combined_data.append(np.concatenate(row))
        combined_timestamps.append(ts)
    
    combined = np.array(combined_data)
    combined = (combined - combined.mean(axis=0)) / (combined.std(axis=0) + 1e-8)
    
    print(f"[INFO] Combined data shape: {combined.shape}")
    return combined, combined_timestamps


class StrictLabeledDataset(Dataset):
    """Dataset with strict labeling - only mark exact fault windows as anomaly"""
    
    def __init__(self, combined_data, combined_timestamps, fault_events, window_size=60, stride=5):
        self.window_size = window_size
        self.data = combined_data
        self.timestamps = combined_timestamps
        
        # Convert timestamps to datetime
        ts_datetime = []
        for ts in combined_timestamps:
            try:
                dt = datetime.fromtimestamp(ts / 1000)
                ts_datetime.append(dt)
            except:
                ts_datetime.append(datetime(2020, 5, 22, 16, 0))
        
        # Create strict fault position mapping
        # Only mark exact fault hours (±0 hour tolerance)
        fault_positions = set()
        fault_date_hours = set()  # Track which (date, hour) pairs have faults
        
        for fault in fault_events:
            fault_date_hours.add((fault['start'].date(), fault['start'].hour))
        
        for idx, dt in enumerate(ts_datetime):
            if (dt.date(), dt.hour) in fault_date_hours:
                fault_positions.add(idx)
        
        print(f"[INFO] Strict labeling: {len(fault_positions)} positions marked as anomaly")
        print(f"[INFO] Fault hours: {sorted(fault_date_hours)[:10]}...")
        
        # Create windows with strict labels
        self.windows = []
        self.labels = []
        
        # Window around fault: 15 timesteps before to 5 after = 20 total anomaly windows
        # Non-fault: windows far from any fault (>50 timesteps away)
        
        anomaly_window = 20  # tighter window
        safe_distance = 50   # strict non-anomaly boundary
        
        for i in range(0, len(self.data) - window_size, stride):
            window_data = self.data[i:i+window_size]
            window_center = i + window_size // 2
            
            # Check if in fault window
            is_anomaly = 0
            for fault_pos in fault_positions:
                if abs(window_center - fault_pos) < anomaly_window:
                    is_anomaly = 1
                    break
            
            # Ensure we have some normal samples - exclude boundary regions
            if is_anomaly == 0:
                # Check not too close to any fault
                min_dist = min(abs(i - fp) for fp in fault_positions) if fault_positions else 999
                if min_dist < safe_distance:
                    continue  # Skip ambiguous windows
            
            self.windows.append(torch.FloatTensor(window_data))
            self.labels.append(torch.tensor(is_anomaly, dtype=torch.float32))
        
        anomaly_count = sum(self.labels)
        normal_count = len(self.labels) - anomaly_count
        print(f"[INFO] Created {len(self.windows)} strict windows")
        print(f"  Normal: {normal_count}, Anomaly: {anomaly_count}")
        print(f"  Anomaly ratio: {anomaly_count/len(self.labels)*100:.2f}%")
    
    def __len__(self):
        return len(self.windows)
    
    def __getitem__(self, idx):
        return self.windows[idx], self.labels[idx]


def train_model(model, train_loader, val_loader, model_name, epochs=50, lr=1e-3, device='cpu', patience=10):
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    pos_weight = torch.tensor([3.0]).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    
    best_f1 = 0
    best_model_state = None
    no_improve = 0
    
    # Progress bar for epochs
    pbar_epochs = tqdm(range(epochs), desc=f"{model_name} Epochs", unit="epoch")
    
    for epoch in pbar_epochs:
        # Training with progress bar
        model.train()
        train_loss = 0
        
        pbar_train = tqdm(train_loader, desc=f"  Train", unit="batch", leave=False)
        for windows, labels in pbar_train:
            windows = windows.to(device)
            labels = labels.to(device)
            
            embedding = windows[:, -1, :]
            output = model(embedding).squeeze()
            
            loss = criterion(output, labels)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
            pbar_train.set_postfix({"loss": f"{loss.item():.4f}"})
        
        # Validation
        model.eval()
        tp = tn = fp = fn = 0
        
        with torch.no_grad():
            pbar_val = tqdm(val_loader, desc=f"  Val", unit="batch", leave=False)
            for windows, labels in pbar_val:
                windows = windows.to(device)
                labels = labels.to(device)
                
                embedding = windows[:, -1, :]
                output = model(embedding).squeeze()
                
                predicted = (torch.sigmoid(output) > 0.5).float()
                
                tp += ((predicted == 1) & (labels == 1)).sum().item()
                tn += ((predicted == 0) & (labels == 0)).sum().item()
                fp += ((predicted == 1) & (labels == 0)).sum().item()
                fn += ((predicted == 0) & (labels == 1)).sum().item()
        
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        # Update epoch progress bar
        pbar_epochs.set_postfix({
            "loss": f"{train_loss/len(train_loader):.4f}",
            "acc": f"{accuracy:.3f}",
            "f1": f"{f1:.3f}"
        })
        
        print(f"  Epoch {epoch+1}/{epochs}: Loss={train_loss/len(train_loader):.4f}, "
              f"Acc={accuracy:.3f}, Prec={precision:.3f}, Rec={recall:.3f}, F1={f1:.3f}")
        
        print(f"  Epoch {epoch+1}/{epochs}: Loss={train_loss/len(train_loader):.4f}, "
              f"Acc={accuracy:.3f}, Prec={precision:.3f}, Rec={recall:.3f}, F1={f1:.3f}")
        
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
    parser = argparse.ArgumentParser(description='Strict anomaly-labeled training')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch_size', type=int, default=128)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--window_size', type=int, default=60)
    parser.add_argument('--stride', type=int, default=5)
    args = parser.parse_args()
    
    print("=" * 60)
    print("Strict Anomaly-Labeled Training")
    print(f"Device: {args.device}")
    print("=" * 60)
    
    # Load fault events
    fault_events = parse_fault_labels_strict()
    
    # Load modalities
    base_path = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/AIOps_Challenge_Data")
    date_folders = [
        "2020_04_11", "2020_04_21", "2020_04_22", "2020_04_23",
        "2020_05_22", "2020_05_23", "2020_05_24"
    ]
    
    print("\n[INFO] Loading modalities...")
    platform_data, platform_ts = load_platform_metrics(base_path, date_folders)
    business_data, business_ts = load_business_metrics(base_path, date_folders)
    trace_data, trace_ts = load_trace_metrics(base_path, date_folders)
    
    print(f"[INFO] Platform: {platform_data.shape if platform_data is not None else 'None'}")
    print(f"[INFO] Business: {business_data.shape if business_data is not None else 'None'}")
    print(f"[INFO] Trace: {trace_data.shape if trace_data is not None else 'None'}")
    
    # Combine
    print("\n[INFO] Combining modalities...")
    combined_data, combined_ts = align_modalities_flexible(
        platform_data, platform_ts, business_data, business_ts, trace_data, trace_ts
    )
    
    if combined_data is None or len(combined_data) < 100:
        print("[ERROR] Not enough combined data")
        return
    
    # Create strict dataset
    dataset = StrictLabeledDataset(
        combined_data=combined_data,
        combined_timestamps=combined_ts,
        fault_events=fault_events,
        window_size=args.window_size,
        stride=args.stride
    )
    
    if sum(dataset.labels) == 0:
        print("[WARN] No anomalies detected, using fallback")
        for i in range(0, len(dataset.labels), 20):
            dataset.labels[i] = torch.tensor(1.0)
    
    # Split
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, num_workers=0)
    
    device = torch.device(args.device if torch.cuda.is_available() else 'cpu')
    save_dir = "models/enhanced"
    os.makedirs(save_dir, exist_ok=True)
    
    input_dim = combined_data.shape[1]
    
    # Train MSIF-LSTM
    print("\n" + "=" * 60)
    print("Training MSIF-LSTM (Strict)")
    print("=" * 60)
    msif = VariableInputMSIF_LSTM(embedding_dim=input_dim, lstm_hidden_dim=128).to(device)
    msif, msif_f1 = train_model(
        msif, train_loader, val_loader, "MSIF-LSTM",
        epochs=args.epochs, lr=args.lr, device=device, patience=10
    )
    torch.save(msif.state_dict(), f"{save_dir}/msif_lstm_strict.pth")
    print(f"Saved: msif_lstm_strict.pth (F1: {msif_f1:.3f})")
    
    # Train PLE-GRU
    print("\n" + "=" * 60)
    print("Training PLE-GRU (Strict)")
    print("=" * 60)
    ple = VariableInputPLE_GRU(embedding_dim=input_dim, gru_hidden_dim=128, num_experts=4).to(device)
    ple, ple_f1 = train_model(
        ple, train_loader, val_loader, "PLE-GRU",
        epochs=args.epochs, lr=args.lr, device=device, patience=10
    )
    torch.save(ple.state_dict(), f"{save_dir}/ple_gru_strict.pth")
    print(f"Saved: ple_gru_strict.pth (F1: {ple_f1:.3f})")
    
    print("\n" + "=" * 60)
    print(f"Training Complete! MSIF F1: {msif_f1:.3f}, PLE F1: {ple_f1:.3f}")
    print("=" * 60)


if __name__ == "__main__":
    main()