"""
Simple LSTM Training with Synthetic Data
Creates synthetic time-series data with clear anomaly patterns for training
"""

import os
import sys
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import f1_score
from tqdm import tqdm
import warnings

warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from models.msif_lstm_model import VariableInputMSIF_LSTM
from models.ple_gru_model import VariableInputPLE_GRU

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class SimpleDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.LongTensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]


def create_synthetic_data(n_samples=5000, seq_len=12, n_features=26, anomaly_ratio=0.1):
    """Create synthetic time-series data with clear anomaly patterns"""
    np.random.seed(42)
    
    sequences = []
    labels = []
    
    for i in range(n_samples):
        # Create base pattern: simple sine wave
        t = np.linspace(0, 4*np.pi, seq_len)
        base = np.sin(t) * 0.5
        
        seq = np.zeros((seq_len, n_features))
        
        # Fill first few features with clear patterns
        seq[:, 0] = base + np.random.randn(seq_len) * 0.1
        seq[:, 1] = np.cos(t) * 0.5 + np.random.randn(seq_len) * 0.1
        
        # Add anomaly markers in specific features
        if np.random.random() < anomaly_ratio:
            anom_type = np.random.choice(['spike', 'drop'])
            
            if anom_type == 'spike':
                seq[-1, 2] = 5.0  # Clear spike
            else:
                seq[-1, 2] = -5.0  # Clear drop
            
            labels.append(1)
        else:
            # Normal: small random noise
            seq[:, :3] += np.random.randn(seq_len, 3) * 0.2
            labels.append(0)
        
        # Add noise features
        for j in range(3, n_features):
            seq[:, j] = np.random.randn(seq_len) * 0.1
        
        sequences.append(seq)
    
    return np.array(sequences), np.array(labels)


def train_model(model, train_loader, optimizer, device, pos_weight=None):
    model.train()
    total_loss = 0
    num_batches = 0
    
    criterion = nn.BCELoss(reduction='mean')
    
    for seq, label in train_loader:
        seq, label = seq.to(device), label.to(device)
        optimizer.zero_grad()
        output = model(seq).squeeze()
        
        loss = criterion(output, label.float())
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        total_loss += loss.item()
        num_batches += 1
    
    return total_loss / num_batches


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
    
    # Debug: show prediction distribution
    pred_counts = [sum(p == i for p in all_preds) for i in [0, 1]]
    print(f"    [DEBUG] Predictions: Normal={pred_counts[0]}, Anomaly={pred_counts[1]}")
    print(f"    [DEBUG] Actual: Normal={sum(l == 0 for l in all_labels)}, Anomaly={sum(l == 1 for l in all_labels)}")
    
    return f1_score(all_labels, all_preds, average='binary', zero_division=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='msif', choices=['msif', 'ple'])
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--batch', type=int, default=64)
    parser.add_argument('--lr', type=float, default=0.001)
    parser.add_argument('--seq', type=int, default=12)
    parser.add_argument('--hidden', type=int, default=128)
    parser.add_argument('--samples', type=int, default=5000)
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"SIMPLE LSTM TRAINING - {args.model.upper()}")
    print("=" * 60)
    print(f"Device: {device}")
    print(f"Samples: {args.samples}, Seq: {args.seq}, Hidden: {args.hidden}")
    
    # Create synthetic data
    print("\n[INFO] Creating synthetic data...")
    sequences, labels = create_synthetic_data(
        n_samples=args.samples, 
        seq_len=args.seq, 
        n_features=26,
        anomaly_ratio=0.15
    )
    
    # Normalize
    sequences = (sequences - sequences.mean(axis=(0, 1))) / (sequences.std(axis=(0, 1)) + 1e-8)
    
    print(f"Data shape: {sequences.shape}")
    print(f"Labels: Normal={int((labels==0).sum())}, Anomaly={int((labels==1).sum())}")
    
    # Split
    split = int(0.8 * len(sequences))
    X_train, X_test = sequences[:split], sequences[split:]
    y_train, y_test = labels[:split], labels[split:]
    
    train_dataset = SimpleDataset(X_train, y_train)
    test_dataset = SimpleDataset(X_test, y_test)
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=args.batch)
    
    # Class weights
    pos_count = (y_train == 1).sum()
    neg_count = (y_train == 0).sum()
    pos_weight = torch.tensor([neg_count / max(pos_count, 1)])
    print(f"Positive weight: {pos_weight.item():.2f}")
    
    # Model - use simple LSTM classifier
    input_dim = sequences.shape[2]
    
    class SimpleLSTMClassifier(nn.Module):
        def __init__(self, input_dim, hidden_dim=128):
            super().__init__()
            self.lstm = nn.LSTM(input_size=input_dim, hidden_size=hidden_dim, 
                              num_layers=2, batch_first=True, dropout=0.3)
            self.fc = nn.Sequential(
                nn.Linear(hidden_dim, 32),
                nn.ReLU(),
                nn.Dropout(0.3),
                nn.Linear(32, 1),
                nn.Sigmoid()
            )
        
        def forward(self, x):
            if x.dim() == 2:
                x = x.unsqueeze(1)
            lstm_out, _ = self.lstm(x)
            return self.fc(lstm_out[:, -1, :])
    
    model = SimpleLSTMClassifier(input_dim, args.hidden).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    
    print("\n" + "=" * 60)
    print("TRAINING...")
    print("=" * 60)
    
    best_f1 = 0
    best_epoch = 0
    
    for epoch in range(args.epochs):
        loss = train_model(model, train_loader, optimizer, device, pos_weight)
        f1 = evaluate_model(model, test_loader, device)
        
        if f1 > best_f1:
            best_f1 = f1
            best_epoch = epoch + 1
            # Save best model
            model_path = os.path.join(os.path.dirname(__file__), f"models/enhanced/{args.model}_lstm_synthetic.pth")
            os.makedirs(os.path.dirname(model_path), exist_ok=True)
            torch.save(model.state_dict(), model_path)
        
        if epoch == 0 or (epoch + 1) % 5 == 0:
            print(f"Epoch {epoch+1}/{args.epochs} - Loss: {loss:.4f} - F1: {f1:.4f} - Best: {best_f1:.4f}")
    
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    print(f"Best F1: {best_f1:.4f} at epoch {best_epoch}")
    print(f"Model saved to: models/enhanced/{args.model}_lstm_synthetic.pth")


if __name__ == "__main__":
    import sys
    main()
