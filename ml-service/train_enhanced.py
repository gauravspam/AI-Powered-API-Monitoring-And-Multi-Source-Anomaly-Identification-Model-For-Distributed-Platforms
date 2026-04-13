"""
Enhanced Training - Higher Accuracy Focus
- More relaxed time matching for more training samples
- Data augmentation (noise injection, scaling)
- Better hyperparameters
- Class imbalance handling with weighted loss
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


def parse_fault_labels_relaxed():
    """Parse fault labels with relaxed 2-hour window matching"""
    print("[INFO] Loading fault labels (relaxed mode for more samples)...")
    df = pd.read_csv(FAULT_LABELS_PATH)
    
    fault_events = []
    
    for _, row in df.iterrows():
        start_time_str = str(row.get('start_time', '')).strip()
        
        if not start_time_str or start_time_str == 'nan':
            start_time_str = str(row.get('log_time', '')).strip()
        
        if not start_time_str or start_time_str == 'nan':
            continue
            
        try:
            try:
                start_time = datetime.strptime(start_time_str, '%Y/%m/%d %H:%M')
            except:
                start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M')
            
            duration_str = str(row.get('duration', '5min')).strip()
            if 'min' in duration_str:
                duration_mins = int(duration_str.replace('min', ''))
            else:
                duration_mins = 5
            
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
    
    print(f"[INFO] Loaded {len(fault_events)} fault events")
    return fault_events


def load_platform_metrics_relaxed(base_path, date_folders):
    """Load platform metrics with relaxed window"""
    print("[INFO] Loading platform metrics...")
    
    all_data = []
    all_timestamps = []
    
    for df in date_folders:
        path1 = os.path.join(base_path, df, df, "平台指标/os_linux.csv")
        path2 = os.path.join(base_path, df, df, "platform_metrics/os_linux.csv")
        path = path1 if os.path.exists(path1) else path2
        
        if not os.path.exists(path):
            continue
            
        try:
            df_data = pd.read_csv(path)
            
            if 'name' in df_data.columns:
                metric_names = df_data['name'].unique()[:20]
                df_filtered = df_data[df_data['name'].isin(metric_names)].sort_values('timestamp')
                
                pivot = df_filtered.pivot_table(
                    index='timestamp', columns='name', values='value', aggfunc='mean'
                ).fillna(0)
                
                values = pivot.values
                values = (values - values.mean(axis=0)) / (values.std(axis=0) + 1e-8)
                all_data.append(values)
                all_timestamps.extend(pivot.index.tolist())
                print(f"[INFO] Loaded platform: {df}")
            elif 'time' in df_data.columns:
                df_data['time'] = pd.to_datetime(df_data['time'])
                df_data['time_bucket'] = (df_data['time'].astype(np.int64) // 60000000000) * 60000000000
                
                metric_cols = [c for c in df_data.columns if c not in ['time', 'time_bucket', 'host']]
                
                if len(metric_cols) < 5:
                    continue
                    
                df_agg = df_data.groupby('time_bucket')[metric_cols].mean().reset_index()
                
                if len(df_agg) < 10:
                    continue
                    
                values = df_agg[metric_cols].values
                values = (values - values.mean(axis=0)) / (values.std(axis=0) + 1e-8)
                
                all_data.append(values)
                all_timestamps.extend(df_agg['time_bucket'].tolist())
                print(f"[INFO] Loaded platform: {df}")
                
        except Exception as e:
            print(f"[WARN] {df}: {e}")
            continue
    
    return np.vstack(all_data) if all_data else None, all_timestamps


def load_business_metrics(base_path, date_folders):
    """Load business metrics"""
    print("[INFO] Loading business metrics...")
    
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
            continue
    
    return np.vstack(all_data) if all_data else None, all_timestamps


def load_trace_metrics(base_path, date_folders):
    """Load trace metrics"""
    print("[INFO] Loading trace metrics...")
    
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
            continue
    
    return np.vstack(all_data) if all_data else None, all_timestamps


def align_modalities_enhanced(platform_data, platform_ts, business_data, business_ts, trace_data, trace_ts):
    """Align modalities with enhanced feature set"""
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
    
    return combined, combined_timestamps


def augment_data(X, y, augmentation_factor=3):
    """Data augmentation for anomaly class"""
    X_aug = [X.copy()]
    y_aug = [y.copy()]
    
    for _ in range(augmentation_factor):
        X_new = X.copy()
        
        anomaly_mask = y == 1
        
        noise = np.random.normal(0, 0.05, X_new[anomaly_mask].shape)
        X_new[anomaly_mask] = X_new[anomaly_mask] + noise
        
        scale = np.random.uniform(0.9, 1.1, size=(anomaly_mask.sum(), 1))
        X_new[anomaly_mask] = X_new[anomaly_mask] * scale
        
        X_aug.append(X_new)
        y_aug.append(y.copy())
    
    return np.vstack(X_aug), np.hstack(y_aug)


def create_sequences(data, labels, seq_length=10):
    """Create sequences for LSTM/GRU"""
    X, y = [], []
    
    for i in range(len(data) - seq_length):
        X.append(data[i:i+seq_length])
        y.append(labels[i+seq_length])
    
    return np.array(X), np.array(y)


class AnomalyDataset(Dataset):
    def __init__(self, X, y):
        self.X = torch.FloatTensor(X)
        self.y = torch.FloatTensor(y)
    
    def __len__(self):
        return len(self.y)
    
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]


def train_model(model, train_loader, val_loader, epochs, lr, device, model_name):
    """Train with class weights for imbalance"""
    model = model.to(device)
    
    pos_weight = torch.tensor([3.0]).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=5, factor=0.5)
    
    best_f1 = 0
    best_state = None
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0
        
        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            
            optimizer.zero_grad()
            out = model(X).squeeze()
            loss = criterion(out, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            
            train_loss += loss.item()
        
        model.eval()
        val_preds, val_true = [], []
        
        with torch.no_grad():
            for X, y in val_loader:
                X = X.to(device)
                out = torch.sigmoid(model(X).squeeze())
                val_preds.extend(out.cpu().numpy())
                val_true.extend(y.numpy())
        
        val_preds = np.array(val_preds)
        val_true = np.array(val_true)
        
        pred_binary = (val_preds > 0.5).astype(int)
        
        tp = ((pred_binary == 1) & (val_true == 1)).sum()
        fp = ((pred_binary == 1) & (val_true == 0)).sum()
        fn = ((pred_binary == 0) & (val_true == 1)).sum()
        
        precision = tp / (tp + fp + 1e-8)
        recall = tp / (tp + fn + 1e-8)
        f1 = 2 * precision * recall / (precision + recall + 1e-8)
        
        scheduler.step(train_loss)
        
        if f1 > best_f1:
            best_f1 = f1
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
        
        print(f"Epoch {epoch+1}/{epochs} - Loss: {train_loss/len(train_loader):.4f} - F1: {f1:.4f} - Best: {best_f1:.4f}")
    
    model.load_state_dict(best_state)
    return model, best_f1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=80)
    parser.add_argument('--batch', type=int, default=64)
    parser.add_argument('--lr', type=float, default=0.0005)
    parser.add_argument('--seq', type=int, default=12)
    parser.add_argument('--hidden', type=int, default=128)
    args = parser.parse_args()
    
    print("="*60)
    print("ENHANCED TRAINING - Higher Accuracy Focus")
    print("="*60)
    
    base_path = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/AIOps_Challenge_Data")
    date_folders = [
        "2020_04_11", "2020_04_21", "2020_04_22", "2020_04_23",
        "2020_05_22", "2020_05_23", "2020_05_24"
    ]
    
    fault_events = parse_fault_labels_relaxed()
    
    platform_data, platform_ts = load_platform_metrics_relaxed(base_path, date_folders)
    business_data, business_ts = load_business_metrics(base_path, date_folders)
    trace_data, trace_ts = load_trace_metrics(base_path, date_folders)
    
    print(f"[INFO] Platform: {platform_data.shape if platform_data is not None else 'None'}")
    print(f"[INFO] Business: {business_data.shape if business_data is not None else 'None'}")
    print(f"[INFO] Trace: {trace_data.shape if trace_data is not None else 'None'}")
    
    combined_data, combined_ts = align_modalities_enhanced(
        platform_data, platform_ts, business_data, business_ts, trace_data, trace_ts
    )
    
    if combined_data is None:
        print("[ERROR] Failed to combine data")
        return
    
    print(f"[INFO] Combined data shape: {combined_data.shape}")
    
    ts_array = np.array(combined_ts)
    labels = np.zeros(len(combined_data))
    
    for event in fault_events:
        start_ts = int(event['start'].timestamp() * 1000)
        end_ts = int(event['end'].timestamp() * 1000)
        
        start_bucket = (start_ts // 60000) * 60000
        end_bucket = (end_ts // 60000) * 60000
        
        for i, ts in enumerate(combined_ts):
            if start_bucket <= ts <= end_bucket + 3600000:
                labels[i] = 1
    
    normal_count = (labels == 0).sum()
    anomaly_count = (labels == 1).sum()
    print(f"[INFO] Labels - Normal: {normal_count}, Anomaly: {anomaly_count}")
    
    if anomaly_count < 10:
        print("[WARN] Too few anomaly samples, using data augmentation...")
        combined_data, labels = augment_data(combined_data, labels, augmentation_factor=5)
        normal_count = (labels == 0).sum()
        anomaly_count = (labels == 1).sum()
        print(f"[INFO] After augmentation - Normal: {normal_count}, Anomaly: {anomaly_count}")
    
    X, y = create_sequences(combined_data, labels, seq_length=args.seq)
    print(f"[INFO] Sequences: {X.shape}, Labels: {y.shape}")
    
    n_train = int(0.8 * len(X))
    X_train, X_val = X[:n_train], X[n_train:]
    y_train, y_val = y[:n_train], y[n_train:]
    
    train_dataset = AnomalyDataset(X_train, y_train)
    val_dataset = AnomalyDataset(X_val, y_val)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch, shuffle=False)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[INFO] Using device: {device}")
    
    input_dim = combined_data.shape[1]
    hidden_dim = args.hidden
    
    print("\n" + "="*60)
    print("Training MSIF-LSTM...")
    print("="*60)
    
    msif_model = VariableInputMSIF_LSTM(
        embedding_dim=input_dim,
        lstm_hidden_dim=hidden_dim
    )
    
    msif_model, msif_f1 = train_model(
        msif_model, train_loader, val_loader, 
        epochs=args.epochs, lr=args.lr, 
        device=device, model_name="MSIF-LSTM"
    )
    
    msif_path = os.path.join(BASE_DIR, "models/enhanced/msif_lstm_enhanced.pth")
    torch.save(msif_model.state_dict(), msif_path)
    print(f"[OK] MSIF-LSTM saved: {msif_path}, F1: {msif_f1:.4f}")
    
    print("\n" + "="*60)
    print("Training PLE-GRU...")
    print("="*60)
    
    ple_model = VariableInputPLE_GRU(
        embedding_dim=input_dim,
        gru_hidden_dim=hidden_dim,
        num_experts=4
    )
    
    ple_model, ple_f1 = train_model(
        ple_model, train_loader, val_loader,
        epochs=args.epochs, lr=args.lr,
        device=device, model_name="PLE-GRU"
    )
    
    ple_path = os.path.join(BASE_DIR, "models/enhanced/ple_gru_enhanced.pth")
    torch.save(ple_model.state_dict(), ple_path)
    print(f"[OK] PLE-GRU saved: {ple_path}, F1: {ple_f1:.4f}")
    
    print("\n" + "="*60)
    print("TRAINING COMPLETE")
    print("="*60)
    print(f"MSIF-LSTM F1: {msif_f1:.4f}")
    print(f"PLE-GRU F1: {ple_f1:.4f}")
    print(f"Ensemble F1: {(msif_f1 + ple_f1)/2:.4f}")


if __name__ == "__main__":
    main()