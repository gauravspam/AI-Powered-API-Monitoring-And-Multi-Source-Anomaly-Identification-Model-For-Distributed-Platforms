import os
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import f1_score
import warnings

warnings.filterwarnings('ignore')


class SimpleDataset(Dataset):
    def __init__(self, sequences, labels):
        self.sequences = torch.FloatTensor(sequences)
        self.labels = torch.FloatTensor(labels)
    
    def __len__(self):
        return len(self.labels)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.labels[idx]


def create_synthetic_data(n_samples=5000, seq_len=12, n_features=26, anomaly_ratio=0.1):
    np.random.seed(42)
    sequences = []
    labels = []
    
    for i in range(n_samples):
        seq = np.random.randn(seq_len, n_features) * 0.2
        
        if np.random.random() < anomaly_ratio:
            seq[-1, 0] = 3.0 if np.random.random() > 0.5 else -3.0
            labels.append(1.0)
        else:
            labels.append(0.0)
        
        sequences.append(seq)
    
    return np.array(sequences), np.array(labels)


class LSTMClassifier(nn.Module):
    def __init__(self, input_dim, hidden_dim):
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_dim, hidden_size=hidden_dim, num_layers=2, batch_first=True)
        self.fc = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--batch', type=int, default=64)
    parser.add_argument('--lr', type=float, default=0.001)
    parser.add_argument('--hidden', type=int, default=128)
    args = parser.parse_args()
    
    print("=" * 60)
    print("SIMPLE LSTM TRAINING")
    print("=" * 60)
    
    sequences, labels = create_synthetic_data(n_samples=3000, seq_len=12, n_features=26, anomaly_ratio=0.15)
    print(f"Data: {sequences.shape}, Anomaly={int(labels.sum())}/{len(labels)}")
    
    split = int(0.8 * len(sequences))
    X_train, X_test = sequences[:split], sequences[split:]
    y_train, y_test = labels[:split], labels[split:]
    
    train_loader = DataLoader(SimpleDataset(X_train, y_train), batch_size=args.batch, shuffle=True)
    test_loader = DataLoader(SimpleDataset(X_test, y_test), batch_size=args.batch)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    model = LSTMClassifier(26, args.hidden).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.BCELoss()
    
    print("\nTraining...")
    
    for epoch in range(args.epochs):
        model.train()
        total_loss = 0
        for seq, label in train_loader:
            seq, label = seq.to(device), label.to(device)
            optimizer.zero_grad()
            out = model(seq).squeeze()
            loss = criterion(out, label)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        model.eval()
        preds, true = [], []
        with torch.no_grad():
            for seq, label in test_loader:
                out = model(seq).squeeze()
                pred = (out > 0.5).float()
                preds.extend(pred.cpu().numpy())
                true.extend(label.numpy())
        
        f1 = f1_score(true, preds, zero_division=0)
        
        if epoch % 5 == 0 or epoch == args.epochs - 1:
            print(f"Epoch {epoch+1}: Loss={total_loss:.4f}, F1={f1:.4f}, Preds={sum(preds)}/{len(preds)}")
    
    os.makedirs("models/enhanced", exist_ok=True)
    torch.save(model.state_dict(), "models/enhanced/simple_lstm.pth")
    print("\nDone!")


if __name__ == "__main__":
    main()
