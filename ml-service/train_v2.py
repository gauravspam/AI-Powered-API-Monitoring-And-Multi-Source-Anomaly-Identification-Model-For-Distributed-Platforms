import os

import torch
import torch.nn as nn
import torch.optim as optim
from core.dataset import MultimodalWindowDataset, collate_windows
from core.fusion import MultimodalFusionModel
from torch.utils.data import DataLoader


def train():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")

    dataset = MultimodalWindowDataset("data/processed/train_windows.jsonl")
    if len(dataset) == 0:
        print("❌ No data")
        return

    loader = DataLoader(dataset, batch_size=8, shuffle=True, collate_fn=collate_windows)
    model = MultimodalFusionModel().to(device)
    opt = optim.Adam(model.parameters(), lr=0.001)
    crit = nn.BCELoss()

    model.train()
    for epoch in range(50):
        total_loss = 0
        for windows, labels in loader:
            labels = labels.to(device).squeeze(1)  # (B,)
            out = model(windows, device)["fusion"].squeeze(1)  # (B,)
            loss = crit(out, labels)

            opt.zero_grad()
            loss.backward()
            opt.step()
            total_loss += loss.item()
        print(f"Epoch {epoch + 1}/50: Loss {total_loss:.4f}")

    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), "models/fusion_v2.pth")
    print("✅ Saved models/fusion_v2.pth")


if __name__ == "__main__":
    train()
