"""
Multi-Modal Anomaly Training - Combines metrics, business data, and traces
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


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAULT_LABELS_PATH = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/fault_labels_preselection.csv")


def parse_fault_labels():
    print("[INFO] Loading fault labels...")
    df = pd.read_csv(FAULT_LABELS_PATH)
    fault_times = []
    
    for _, row in df.iterrows():
        start_time_str = str(row.get('start_time', '')).strip()
        if not start_time_str or start_time_str == 'nan':
            continue
        try:
            start_time = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M')
            fault_times.append({
                'start': start_time,
                'object': str(row.get('object', '')),
                'fault_type': str(row.get('fault_desrcibtion', ''))
            })
        except:
            continue
    
    print(f"[INFO] Loaded {len(fault_times)} fault timestamps")
    return fault_times


def load_platform_metrics(base_path, date_folders):
    """Load platform metrics (CPU, memory, network)"""
    all_data = []
    all_timestamps = []
    
    for df in date_folders:
        path = os.path.join(base_path, df, df, "平台指标/os_linux.csv")
        if not os.path.exists(path):
            path = os.path.join(base_path, df, df, "platform_metrics/os_linux.csv")
        
        if os.path.exists(path):
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
    """Load business metrics (ESB success rate, response time)"""
    all_data = []
    all_timestamps = []
    
    for df in date_folders:
        path = os.path.join(base_path, df, df, "业务指标/esb.csv")
        if not os.path.exists(path):
            path = os.path.join(base_path, df, df, "business_metrics/esb.csv")
        
        if os.path.exists(path):
            try:
                df_data = pd.read_csv(path)
                # Aggregate: avg_time, num, succee_num, succee_rate
                df_agg = df_data.groupby('startTime').agg({
                    'avg_time': 'mean', 'num': 'sum', 'succee_num': 'sum', 'succee_rate': 'mean'
                }).reset_index()
                df_agg = df_agg.sort_values('startTime')
                # Normalize
                values = df_agg[['avg_time', 'num', 'succee_num', 'succee_rate']].values
                values = (values - values.mean(axis=0)) / (values.std(axis=0) + 1e-8)
                all_data.append(values)
                all_timestamps.extend(df_agg['startTime'].tolist())
                print(f"[INFO] Loaded business: {df}")
            except Exception as e:
                print(f"[WARN] {df}: {e}")
    
    return np.vstack(all_data) if all_data else None, all_timestamps


def load_trace_metrics(base_path, date_folders):
    """Load trace metrics (latency, error rate) - with sampling for large files"""
    all_data = []
    all_timestamps = []
    
    for df in date_folders:
        path = os.path.join(base_path, df, df, "调用链指标/trace_local.csv")
        if not os.path.exists(path):
            path = os.path.join(base_path, df, df, "trace_metrics/trace_local.csv")
        
        if os.path.exists(path):
            try:
                print(f"[INFO] Loading trace: {df}...")
                # Read with sampling for large files - load every 100th row
                df_data = pd.read_csv(path)
                print(f"[INFO]   Raw rows: {len(df_data)}")
                
                # Aggregate at source to reduce size
                df_data['success'] = df_data['success'].map({True: 1, False: 0, 'True': 1, 'False': 0}).fillna(0)
                
                # Group by 1-minute intervals at load time
                df_data['time_bucket'] = (df_data['startTime'] // 60000) * 60000
                df_agg = df_data.groupby('time_bucket').agg({
                    'elapsedTime': 'mean', 
                    'success': 'mean'
                }).reset_index()
                
                print(f"[INFO]   Aggregated to {len(df_agg)} buckets")
                
                values = df_agg[['elapsedTime', 'success']].values
                values = (values - values.mean(axis=0)) / (values.std(axis=0) + 1e-8)
                all_data.append(values)
                all_timestamps.extend(df_agg['time_bucket'].tolist())
                print(f"[INFO] Loaded trace: {df}")
            except Exception as e:
                print(f"[WARN] {df}: {e}")
    
    return np.vstack(all_data) if all_data else None, all_timestamps


def align_and_combine_flexible(modality_data_list, modality_timestamps, stride=5):
    """Align multiple modalities but keep original time points from primary (platform)"""
    if not modality_data_list:
        return None, []
    
    # Use platform metrics as primary (most comprehensive)
    platform_data = modality_data_list[0]
    platform_ts = modality_timestamps[0]
    
    if platform_data is None or not platform_ts:
        return None, []
    
    from collections import defaultdict
    
    def bucket_ts(ts_list):
        buckets = defaultdict(list)
        for ts in ts_list:
            bucket = int(ts // 60000) * 60000
            buckets[bucket].append(ts)
        return buckets
    
    # Bucket secondary modalities
    business_ts = modality_timestamps[1] if len(modality_timestamps) > 1 else []
    trace_ts = modality_timestamps[2] if len(modality_timestamps) > 2 else []
    
    business_bucket = bucket_ts(business_ts) if business_ts else {}
    trace_bucket = bucket_ts(trace_ts) if trace_ts else {}
    
    # Expected dimensions
    dim_platform = 20
    dim_business = 4
    dim_trace = 2
    
    print(f"[INFO] Aligning to {len(platform_ts)} platform time points...")
    
    combined_data = []
    combined_timestamps = []
    
    for i, ts in enumerate(platform_ts):
        bucket = int(ts // 60000) * 60000
        
        row = [platform_data[i]]
        
        # Add business data if available
        if bucket in business_bucket and modality_data_list[1] is not None:
            # Find matching index
            b_idxs = [j for j, t in enumerate(business_ts) if int(t // 60000) * 60000 == bucket]
            if b_idxs:
                row.append(modality_data_list[1][b_idxs[0]])
            else:
                row.append(np.zeros(dim_business))
        else:
            row.append(np.zeros(dim_business))
        
        # Add trace data if available
        if bucket in trace_bucket and modality_data_list[2] is not None:
            t_idxs = [j for j, t in enumerate(trace_ts) if int(t // 60000) * 60000 == bucket]
            if t_idxs:
                row.append(modality_data_list[2][t_idxs[0]])
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


class MultimodalDataset(Dataset):
    def __init__(self, combined_data, combined_timestamps, fault_times, window_size=60, stride=5):
        self.window_size = window_size
        self.fault_times = fault_times
        
        self.data = combined_data
        self.timestamps = combined_timestamps
        
        # Convert epoch timestamps to datetime
        ts_datetime = []
        for ts in combined_timestamps:
            try:
                dt = datetime.fromtimestamp(ts / 1000)
                ts_datetime.append(dt)
            except:
                ts_datetime.append(datetime(2020, 5, 22, 16, 0))
        
        # Map fault times - use specific hour matching, not just date
        # Get fault hours for each date
        fault_hours_by_date = {}
        for fault in fault_times:
            if fault['start']:
                key = (fault['start'].month, fault['start'].day)
                if key not in fault_hours_by_date:
                    fault_hours_by_date[key] = set()
                fault_hours_by_date[key].add(fault['start'].hour)
        
        fault_positions = []
        for idx, dt in enumerate(ts_datetime):
            if (dt.month, dt.day) in fault_hours_by_date:
                if dt.hour in fault_hours_by_date[(dt.month, dt.day)]:
                    fault_positions.append(idx)
        
        print(f"[INFO] Combined data shape: {self.data.shape}")
        print(f"[INFO] Mapped {len(fault_positions)} positions with hour-level precision")
        
        # If no hour-level matches, use broader date-based but add some normal periods
        if len(fault_positions) < 10:
            print("[INFO] Using broader date-based labeling")
            for idx, dt in enumerate(ts_datetime):
                if (dt.month, dt.day) in fault_hours_by_date:
                    fault_positions.append(idx)
        
        # Create windows
        self.windows = []
        self.labels = []
        
        for i in range(0, len(self.data) - window_size, stride):
            window_data = self.data[i:i+window_size]
            is_anomaly = 0
            window_center = i + window_size // 2
            
            for fault_pos in fault_positions:
                if abs(window_center - fault_pos) < 30:
                    is_anomaly = 1
                    break
            
            self.windows.append(torch.FloatTensor(window_data))
            self.labels.append(torch.tensor(is_anomaly, dtype=torch.float32))
        
        anomaly_count = sum(self.labels)
        normal_count = len(self.labels) - anomaly_count
        print(f"[INFO] Created {len(self.windows)} windows")
        print(f"  Normal: {normal_count}, Anomaly: {anomaly_count}")
        print(f"  Anomaly ratio: {anomaly_count/len(self.labels)*100:.2f}%")
    
    def __len__(self):
        return len(self.windows)
    
    def __getitem__(self, idx):
        return self.windows[idx], self.labels[idx]


def train_model(model, train_loader, val_loader, model_name, epochs=50, lr=1e-3, device='cpu', patience=10):
    model = model.to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    pos_weight = torch.tensor([5.0]).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    
    best_f1 = 0
    best_model_state = None
    no_improve = 0
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        
        for windows, labels in train_loader:
            windows = windows.to(device)
            labels = labels.to(device)
            
            # Use last timestep embedding
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
        
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
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
    parser = argparse.ArgumentParser(description='Multi-modal anomaly training')
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch_size', type=int, default=128)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--device', type=str, default='cuda')
    parser.add_argument('--window_size', type=int, default=60)
    parser.add_argument('--stride', type=int, default=5)
    args = parser.parse_args()
    
    print("=" * 60)
    print("Multi-Modal Anomaly Training")
    print(f"Device: {args.device}")
    print("=" * 60)
    
    # Load fault times
    fault_times = parse_fault_labels()
    
    # Load all modalities
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
    
    # Combine modalities - use flexible alignment that keeps all platform points
    print("\n[INFO] Combining modalities...")
    combined_data, combined_ts = align_and_combine_flexible(
        [platform_data, business_data, trace_data], 
        [platform_ts, business_ts, trace_ts],
        args.stride
    )
    
    if combined_data is None or len(combined_data) < 100:
        print("[ERROR] Not enough combined data, falling back to platform only")
        combined_data = platform_data[:min(10000, len(platform_data))]
    
    # Create dataset
    dataset = MultimodalDataset(
        combined_data=combined_data,
        combined_timestamps=combined_ts,
        fault_times=fault_times,
        window_size=args.window_size,
        stride=args.stride
    )
    
    if sum(dataset.labels) == 0:
        print("[WARN] No anomalies detected, using synthetic labeling")
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
    
    input_dim = combined_data.shape[1] if combined_data is not None else 38
    
    # Train MSIF-LSTM
    print("\n" + "=" * 60)
    print("Training MSIF-LSTM (Multi-Modal)")
    print("=" * 60)
    msif = VariableInputMSIF_LSTM(embedding_dim=input_dim, lstm_hidden_dim=128).to(device)
    msif, msif_f1 = train_model(
        msif, train_loader, val_loader, "MSIF-LSTM",
        epochs=args.epochs, lr=args.lr, device=device, patience=10
    )
    torch.save(msif.state_dict(), f"{save_dir}/msif_lstm_multimodal.pth")
    print(f"Saved: msif_lstm_multimodal.pth (F1: {msif_f1:.3f})")
    
    # Train PLE-GRU
    print("\n" + "=" * 60)
    print("Training PLE-GRU (Multi-Modal)")
    print("=" * 60)
    ple = VariableInputPLE_GRU(embedding_dim=input_dim, gru_hidden_dim=128, num_experts=4).to(device)
    ple, ple_f1 = train_model(
        ple, train_loader, val_loader, "PLE-GRU",
        epochs=args.epochs, lr=args.lr, device=device, patience=10
    )
    torch.save(ple.state_dict(), f"{save_dir}/ple_gru_multimodal.pth")
    print(f"Saved: ple_gru_multimodal.pth (F1: {ple_f1:.3f})")
    
    print("\n" + "=" * 60)
    print(f"Training Complete! MSIF F1: {msif_f1:.3f}, PLE F1: {ple_f1:.3f}")
    print("=" * 60)


if __name__ == "__main__":
    main()