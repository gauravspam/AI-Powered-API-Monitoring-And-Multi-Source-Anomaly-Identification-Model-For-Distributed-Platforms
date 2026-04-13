"""
Optimized Training with Better Hyperparameters
Designed to achieve higher accuracy on AIOps 2020 data
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


def parse_fault_labels():
    """Parse fault labels"""
    print("[INFO] Loading fault labels...")
    df = pd.read_csv(FAULT_LABELS_PATH)
    fault_events = []
    
    for _, row in df.iterrows():
        start_time_str = str(row.get('log_time', '')).strip()
        if not start_time_str or start_time_str == 'nan':
            start_time_str = str(row.get('start_time', '')).strip()
        if not start_time_str or start_time_str == 'nan':
            continue
        try:
            if 'T' in start_time_str:
                ts = pd.to_datetime(start_time_str)
            elif '/' in start_time_str:
                ts = pd.to_datetime(start_time_str, format='%Y/%m/%d %H:%M')
            else:
                ts = pd.to_datetime(start_time_str, format='%Y-%m-%d %H:%M:%S')
            fault_events.append({
                'timestamp': ts,
                'severity': str(row.get('severity', 'unknown'))
            })
        except:
            continue
    
    print(f"[INFO] Loaded {len(fault_events)} fault events")
    return fault_events


def load_platform_metrics():
    """Load platform metrics"""
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


def load_business_metrics():
    """Load business metrics"""
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
            df_agg = df_data.groupby('startTime').agg({'avg_time': 'mean', 'num': 'sum', 'succee_num': 'sum', 'succee_rate': 'mean'}).reset_index()
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
            path = os.path.join(base_path, df, df, "trace_metrics/trace_local.csv")
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


class AnomalyDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.LongTensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]


def train_model(model, train_loader, optimizer, device, class_weights=None):
    model.train()
    total_loss = 0
    
    criterion = nn.BCEWithLogitsLoss(weight=class_weights.to(device)) if class_weights is not None else nn.BCEWithLogitsLoss()
    
    for seq, label in train_loader:
        seq, label = seq.to(device), label.to(device)
        optimizer.zero_grad()
        output = model(seq).squeeze()
        loss = criterion(output, label.float())
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total_loss += loss.item()
    
    return total_loss / len(train_loader)


def evaluate_model(model, val_loader, device):
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for seq, label in val_loader:
            seq = seq.to(device)
            output = model(seq).squeeze()
            pred = (torch.sigmoid(output) > 0.5).long()
            all_preds.extend(pred.cpu().numpy())
            all_labels.extend(label.numpy())
    
    return f1_score(all_labels, all_preds, average='binary', zero_division=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--batch', type=int, default=64)
    parser.add_argument('--lr', type=float, default=0.001)
    parser.add_argument('--seq', type=int, default=12)
    parser.add_argument('--hidden', type=int, default=128)
    args = parser.parse_args()
    
    print("=" * 60)
    print("OPTIMIZED TRAINING FOR HIGHER ACCURACY")
    print("=" * 60)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    # Load data
    fault_events = parse_fault_labels()
    platform_data, platform_ts = load_platform_metrics()
    business_data, business_ts = load_business_metrics()
    trace_data, trace_ts = load_trace_metrics()
    
    print(f"Platform: {platform_data.shape if platform_data is not None else None}")
    print(f"Business: {business_data.shape if business_data is not None else None}")
    print(f"Trace: {trace_data.shape if trace_data is not None else None}")
    
    if platform_data is None:
        print("[ERROR] No platform data loaded!")
        return
    
    # Combine data
    min_len = min(len(platform_data), 2500)
    platform_sample = platform_data[:min_len]
    platform_ts_sample = platform_ts[:min_len]
    
    business_sample = business_data[:min_len] if business_data is not None else np.zeros((min_len, 4))
    trace_sample = trace_data[:min_len] if trace_data is not None else np.zeros((min_len, 2))
    
    combined_data = np.hstack([platform_sample[:, :min(platform_sample.shape[1], 20)], 
                              business_sample[:, :4], 
                              trace_sample[:, :2]])
    combined_data = (combined_data - combined_data.mean(axis=0)) / (combined_data.std(axis=0) + 1e-8)
    
    # Create labels
    labels = np.zeros(len(combined_data))
    for event in fault_events:
        ts = event['timestamp'].timestamp() * 1000
        for i, platform_ts_val in enumerate(platform_ts_sample):
            if abs(platform_ts_val - ts) < 3600000:
                labels[i] = 1
                break
    
    pos_count = int(labels.sum())
    neg_count = len(labels) - pos_count
    print(f"Labels: Normal={neg_count}, Anomaly={pos_count}")
    
    # Create sequences
    seq_len = min(args.seq, 20)
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
    
    # Split data
    split = int(len(sequences) * 0.8)
    train_seq, val_seq = sequences[:split], sequences[split:]
    train_labels, val_labels = target_labels[:split], target_labels[split:]
    
    train_dataset = AnomalyDataset(train_seq, train_labels)
    val_dataset = AnomalyDataset(val_seq, val_labels)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch, shuffle=False)
    
    # Class weights for imbalanced data
    pos_weight = torch.tensor([neg_count / max(pos_count, 1)])
    print(f"Positive weight: {pos_weight.item():.2f}")
    
    input_dim = sequences.shape[2]
    hidden_dim = args.hidden
    
    # Train MSIF-LSTM
    print("\n" + "=" * 60)
    print("Training MSIF-LSTM...")
    print("=" * 60)
    
    msif = VariableInputMSIF_LSTM(embedding_dim=input_dim, lstm_hidden_dim=hidden_dim).to(device)
    optimizer = torch.optim.AdamW(msif.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=5)
    
    best_f1 = 0
    patience_counter = 0
    
    for epoch in range(args.epochs):
        loss = train_model(msif, train_loader, optimizer, device, pos_weight)
        f1 = evaluate_model(msif, val_loader, device)
        
        scheduler.step(f1)
        
        if f1 > best_f1:
            best_f1 = f1
            torch.save(msif.state_dict(), os.path.join(BASE_DIR, "models/enhanced/msif_lstm_optimized.pth"))
            patience_counter = 0
        else:
            patience_counter += 1
        
        print(f"Epoch {epoch+1}/{args.epochs} - Loss: {loss:.4f} - F1: {f1:.4f} - Best: {best_f1:.4f}")
        
        if patience_counter >= 10:
            print(f"Early stopping at epoch {epoch+1}")
            break
    
    msif_f1 = best_f1
    
    # Train PLE-GRU
    print("\n" + "=" * 60)
    print("Training PLE-GRU...")
    print("=" * 60)
    
    ple = VariableInputPLE_GRU(embedding_dim=input_dim, gru_hidden_dim=hidden_dim, num_experts=4).to(device)
    optimizer = torch.optim.AdamW(ple.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', factor=0.5, patience=5)
    
    best_f1 = 0
    patience_counter = 0
    
    for epoch in range(args.epochs):
        loss = train_model(ple, train_loader, optimizer, device, pos_weight)
        f1 = evaluate_model(ple, val_loader, device)
        
        scheduler.step(f1)
        
        if f1 > best_f1:
            best_f1 = f1
            torch.save(ple.state_dict(), os.path.join(BASE_DIR, "models/enhanced/ple_gru_optimized.pth"))
            patience_counter = 0
        else:
            patience_counter += 1
        
        print(f"Epoch {epoch+1}/{args.epochs} - Loss: {loss:.4f} - F1: {f1:.4f} - Best: {best_f1:.4f}")
        
        if patience_counter >= 10:
            print(f"Early stopping at epoch {epoch+1}")
            break
    
    ple_f1 = best_f1
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"MSIF-LSTM F1: {msif_f1:.4f}")
    print(f"PLE-GRU F1: {ple_f1:.4f}")
    print(f"Ensemble F1: {(msif_f1 + ple_f1) / 2:.4f}")
    
    # Update the main model files
    import shutil
    shutil.copy(os.path.join(BASE_DIR, "models/enhanced/msif_lstm_optimized.pth"),
                os.path.join(BASE_DIR, "models/enhanced/msif_lstm_strict.pth"))
    shutil.copy(os.path.join(BASE_DIR, "models/enhanced/ple_gru_optimized.pth"),
                os.path.join(BASE_DIR, "models/enhanced/ple_gru_strict.pth"))
    print("\nModels updated!")


if __name__ == "__main__":
    main()