import pandas as pd
import torch
import torch.nn as nn
from models.fusion_model import MultimodalFusionModel
from torch.utils.data import DataLoader, Dataset


class AnomalyDataset(Dataset):
    def __init__(self, csv_path):
        self.data = pd.read_csv(csv_path)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        row = self.data.iloc[idx]

        # Parse logs (stored as JSON string)
        logs = eval(row['logs'])  # ["ERROR: timeout", ...]

        # Parse metrics (stored as JSON string)
        metrics = torch.tensor(eval(row['metrics']), dtype=torch.float32)

        # Parse traces (stored as JSON)
        traces = eval(row['traces'])
        adj = torch.tensor(traces['adj'], dtype=torch.float32)
        features = torch.tensor(traces['features'], dtype=torch.float32)

        label = torch.tensor(row['is_anomaly'], dtype=torch.float32)

        return logs, metrics, adj, features, label

def train():
    # Hyperparameters
    EPOCHS = 50
    BATCH_SIZE = 16
    LR = 0.001

    # Load data
    train_dataset = AnomalyDataset('data/train.csv')
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

    # Initialize model
    model = MultimodalFusionModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    criterion = nn.BCELoss()

    # Training loop
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0
        for logs, metrics, adj, features, labels in train_loader:
            optimizer.zero_grad()

            outputs = model(logs, metrics, adj, features).squeeze()
            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch {epoch+1}/{EPOCHS}, Loss: {total_loss/len(train_loader):.4f}")

    # Save model
    torch.save(model.state_dict(), 'models/multimodal_fusion_v1.pth')
    print("✅ Model saved to models/multimodal_fusion_v1.pth")

if __name__ == "__main__":
    train()
