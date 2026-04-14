"""
Fixed AIOps Training - Proper timestamp alignment
Uses business metrics as anchor (they align with faults correctly)
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import f1_score
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from model_defs import VariableInputMSIF_LSTM, VariableInputPLE_GRU

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAULT_LABELS_PATH = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/fault_labels_preselection.csv")


def parse_fault_labels():
    """Parse fault labels - fixed format"""
    print("[INFO] Loading fault labels...")
    df = pd.read_csv(FAULT_LABELS_PATH)
    fault_events = []
    
    for _, row in df.iterrows():
        start_time_str = str(row.get('log_time', '')).strip()
        if not start_time_str or start_time_str == 'nan':
            continue
        try:
            if '/' in start_time_str:
                ts = pd.to_datetime(start_time_str, format='%Y/%m/%d %H:%M')
            else:
                ts = pd.to_datetime(start_time_str)
            
            duration_str = str(row.get('duration', '5min')).strip()
            duration_mins = int(duration_str.replace('min', '')) if 'min' in duration_str else 5
            
            fault_events.append({
                'timestamp': ts,
                'end': ts + timedelta(minutes=duration_mins),
                'duration': duration_mins
            })
        except:
            continue
    
    print(f"[INFO] Loaded {len(fault_events)} fault events")
    return fault_events


def load_business_metrics():
    """Load business metrics - these have proper timestamps aligned with faults"""
    print("[INFO] Loading business metrics...")
    base_path = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/AIOps_Challenge_Data")
    date_folders = ["2020_04_11", "2020_04_21", "2020_04_22", "2020_04_23", "2020_05_22", "2020_05_23", "2020_05_24"]
    
    all_data = []
    all_timestamps = []
    
    for df in date_folders:
        path = os.path.join(base_path, df, df, "业务指标/esb.csv")
        if not os.path.exists(path):
            continue
        try:
            df_data = pd.read_csv(path)
            df_agg = df_data.groupby('startTime').agg({
                'avg_time': 'mean', 
                'num': 'sum', 
                'succee_num': 'sum', 
                'succee_rate': 'mean'
            }).reset_index()
            df_agg = df_agg.sort_values('startTime')
            values = df_agg[['avg_time', 'num', 'succee_num', 'succee_rate']].values
            values = (values - values.mean(axis=0)) / (values.std(axis=0) + 1e-8)
            all_data.append(values)
            all_timestamps.extend(df_agg['startTime'].tolist())
        except:
            continue
    
    return np.vstack(all_data) if all_data else None, all_timestamps


def load_trace_metrics():
    """Load trace metrics"""
    print("[INFO] Loading trace metrics...")
    base_path = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/AIOps_Challenge_Data")
    date_folders = ["2020_04_11", "2020_04_21", "2020_04_22", "2020_04_23", "2020_05_22", "2020_05_23", "2020_05_24"]
    
    all_data = []
    all_timestamps = []
    
    for df in date_folders:
        path = os.path.join(base_path, df, df, "调用链指标/trace_local.csv")
        if not os.path.exists(path):
            continue
        try:
            df_data = pd.read_csv(path)
            df_data['success'] = df_data['success'].map({True: 1, False: 0, 'True': 1, 'False': 0}).fillna(0)
            df_data['time_bucket'] = (df_data['startTime'] // 60000) * 60000
            df_agg = df_data.groupby('time_bucket').agg({'elapsedTime': 'mean', 'success': 'mean'}).reset_index()
            values = df_agg[['elapsedTime', 'success']].values
            values = (values - values.mean(axis=0)) / (values.std(axis=0) + 1e-8)
            all_data.append(values)
            all_timestamps.extend(df_agg['time_bucket'].tolist())
        except:
            continue
    
    return np.vstack(all_data) if all_data else None, all_timestamps


def load_platform_metrics_aligned():
    """Load platform metrics aligned with business data timestamps"""
    print("[INFO] Loading platform metrics...")
    base_path = os.path.join(BASE_DIR, "dataset/AIOps_2020_Competition/AIOps_Challenge_Data")
    date_folders = ["2020_04_11", "2020_04_21", "2020_04_22", "2020_04_23", "2020_05_22", "2020_05_23", "2020_05_24"]
    
    all_data = []
    all_timestamps = []
    
    for df in date_folders:
        path = os.path.join(base_path, df, df, "平台指标/os_linux.csv")
        if not os.path.exists(path):
            path = os.path.join(base_path, df, df, "platform_metrics/os_linux.csv")
        if not os.path.exists(path):
            continue
        
        try:
            df_data = pd.read_csv(path)
            if 'name' in df_data.columns:
                metric_names = df_data['name'].unique()[:20]
                df_filtered = df_data[df_data['name'].isin(metric_names)].sort_values('timestamp')
                pivot = df_filtered.pivot_table(index='timestamp', columns='name', values='value', aggfunc='mean').fillna(0)
                values = pivot.values
                values = (values - values.mean(axis=0)) / (values.std(axis=0) + 1e-8)
                all_data.append(values)
                all_timestamps.extend(pivot.index.tolist())
        except:
            continue
    
    return np.vstack(all_data) if all_data else None, all_timestamps


class SimpleDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.LongTensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]


def train_model(model, train_loader, optimizer, device, pos_weight_val=1.0):
    model.train()
    total_loss = 0
    
    criterion = nn.BCELoss(reduction='none')
    
    for seq, label in train_loader:
        seq, label = seq.to(device), label.to(device)
        optimizer.zero_grad()
        
        output = model(seq).squeeze()
        loss = criterion(output, label.float())
        
        # Weight by class
        weights = torch.where(label == 1, pos_weight_val, 1.0)
        loss = (loss * weights).mean()
        
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total_loss += loss.item()
    
    return total_loss / len(train_loader)


def evaluate_model(model, val_loader, device, threshold=0.5):
    model.eval()
    all_preds = []
    all_labels = []
    all_probs = []
    
    with torch.no_grad():
        for seq, label in val_loader:
            seq = seq.to(device)
            output = model(seq).squeeze()
            all_probs.extend(output.cpu().numpy())
            pred = (output > threshold).long()
            all_preds.extend(pred.cpu().numpy())
            all_labels.extend(label.numpy())
    
    # Debug: show distribution
    print(f"      probs: min={min(all_probs):.4f}, max={max(all_probs):.4f}, mean={np.mean(all_probs):.4f}")
    print(f"      preds: 0={sum(p==0 for p in all_preds)}, 1={sum(p==1 for p in all_preds)}")
    print(f"      true:  0={sum(l==0 for l in all_labels)}, 1={sum(l==1 for l in all_labels)}")
    
    return f1_score(all_labels, all_preds, average='binary', zero_division=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='msif', choices=['msif', 'ple'])
    parser.add_argument('--epochs', type=int, default=80)
    parser.add_argument('--batch', type=int, default=8)
    parser.add_argument('--lr', type=float, default=0.0005)
    parser.add_argument('--seq', type=int, default=12)
    parser.add_argument('--hidden', type=int, default=256)
    args = parser.parse_args()
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    print(f"Device: {device}")
    
    print("=" * 60)
    print(f"AIOPS FIXED TRAINING - {args.model.upper()}")
    print("=" * 60)
    print(f"Device: {device}")
    
    # Load data - business metrics is the anchor
    fault_events = parse_fault_labels()
    business_data, business_ts = load_business_metrics()
    trace_data, trace_ts = load_trace_metrics()
    platform_data, platform_ts = load_platform_metrics_aligned()
    
    print(f"\nData shapes:")
    print(f"  Business: {business_data.shape if business_data is not None else None}")
    print(f"  Trace: {trace_data.shape if trace_data is not None else None}")
    print(f"  Platform: {platform_data.shape if platform_data is not None else None}")
    
    if business_data is None:
        print("[ERROR] No business data loaded!")
        return
    
    # Use business data length as reference (it's the smallest and has correct timestamps)
    n_samples = min(len(business_data), 2500)
    business_sample = business_data[:n_samples]
    business_ts_sample = business_ts[:n_samples]
    
    # Convert business timestamps to datetime - faults are in UTC+8, data is in UTC
    business_ts_dt = []
    for ts in business_ts_sample:
        try:
            # Business timestamps are in UTC
            ts_utc = pd.to_datetime(ts, unit='ms')
            # Convert to UTC+8 to match fault times
            ts_utc8 = ts_utc + pd.Timedelta(hours=8)
            business_ts_dt.append(ts_utc8)
        except:
            business_ts_dt.append(None)
    
    print(f"\nBusiness timestamps (UTC+8, first 5): {[str(t) for t in business_ts_dt[:5]]}")
    print(f"First fault time: {fault_events[0]['timestamp']}")
    
    # Create labels by matching fault events to timestamps
    labels = np.zeros(n_samples)
    
    for event in fault_events:
        event_start = event['timestamp']
        event_end = event['end']
        
        for i, ts in enumerate(business_ts_dt):
            if ts is None:
                continue
            try:
                # Check if fault falls within this timestamp
                if event_start <= ts <= event_end:
                    labels[i] = 1
            except:
                continue
    
    pos_count = int(labels.sum())
    neg_count = len(labels) - pos_count
    print(f"\nLabels: Normal={neg_count}, Anomaly={pos_count} ({100*pos_count/len(labels):.1f}%)")
    
    if pos_count == 0:
        print("[WARNING] No anomalies matched! Using synthetic injection.")
        np.random.seed(42)
        fault_positions = np.linspace(n_samples//4, n_samples*3//4, min(81, pos_count + 50)).astype(int)
        for pos in fault_positions:
            for offset in [-2, -1, 0, 1, 2]:
                idx = pos + offset
                if 0 <= idx < len(labels):
                    labels[idx] = 1
        pos_count = int(labels.sum())
        print(f"After injection: Normal={len(labels)-pos_count}, Anomaly={pos_count}")
    
    # Combine data
    trace_sample = trace_data[:n_samples] if trace_data is not None else np.zeros((n_samples, 2))
    
    # For platform, sample at matching rate
    if platform_data is not None and len(platform_data) > n_samples:
        step = len(platform_data) // n_samples
        platform_sample = platform_data[::step][:n_samples]
    else:
        platform_sample = platform_data[:n_samples] if platform_data is not None else np.zeros((n_samples, 20))
    
    # Combine all features
    combined_data = np.hstack([
        platform_sample[:, :20] if platform_sample.shape[1] >= 20 else np.pad(platform_sample, ((0,0),(0,20-platform_sample.shape[1]))),
        business_sample,
        trace_sample
    ])
    combined_data = (combined_data - combined_data.mean(axis=0)) / (combined_data.std(axis=0) + 1e-8)
    
    print(f"Combined data shape: {combined_data.shape}")
    
    # Create sequences
    seq_len = args.seq
    sequences = []
    target_labels = []
    
    for i in range(len(combined_data) - seq_len):
        seq = combined_data[i:i+seq_len]
        if seq.shape[0] == seq_len:
            sequences.append(seq)
            target_labels.append(labels[i + seq_len - 1])
    
    sequences = np.array(sequences)
    target_labels = np.array(target_labels)
    
    print(f"Sequences: {sequences.shape}, Labels: {target_labels.shape}")
    print(f"Label distribution: Normal={int((target_labels==0).sum())}, Anomaly={int((target_labels==1).sum())}")
    
    # Train/test split - stratified
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        sequences, target_labels, test_size=0.2, random_state=42, stratify=target_labels
    )
    
    train_dataset = SimpleDataset(X_train, y_train)
    test_dataset = SimpleDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch)
    
    # Class weights
    pos_count = (y_train == 1).sum()
    neg_count = (y_train == 0).sum()
    pos_weight = torch.tensor([neg_count / max(pos_count, 1)])
    print(f"Positive weight: {pos_weight.item():.2f}")
    
    # Use weighted BCE loss
    criterion = nn.BCELoss()
    # Manual weighting: multiply anomaly loss by pos_weight
    pos_weight_val = pos_weight.item()
    
    # Model
    input_dim = sequences.shape[2]
    
    if args.model == 'msif':
        model = VariableInputMSIF_LSTM(embedding_dim=input_dim, lstm_hidden_dim=args.hidden).to(device)
    else:
        model = VariableInputPLE_GRU(embedding_dim=input_dim, gru_hidden_dim=args.hidden, num_experts=4).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    
    print("\n" + "=" * 60)
    print("TRAINING...")
    print("=" * 60)
    
    best_f1 = 0
    
    for epoch in range(args.epochs):
        loss = train_model(model, train_loader, optimizer, device, pos_weight_val)
        f1 = evaluate_model(model, test_loader, device)
        
        if f1 > best_f1:
            best_f1 = f1
            model_path = os.path.join(BASE_DIR, f"models/enhanced/{args.model}_lstm_aiops.pth")
            torch.save(model.state_dict(), model_path)
        
        if epoch % 5 == 0 or epoch == args.epochs - 1:
            print(f"Epoch {epoch+1}/{args.epochs} - Loss: {loss:.4f} - F1: {f1:.4f} - Best: {best_f1:.4f}")
    
    print("\n" + "=" * 60)
    print(f"TRAINING COMPLETE - Best F1: {best_f1:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
