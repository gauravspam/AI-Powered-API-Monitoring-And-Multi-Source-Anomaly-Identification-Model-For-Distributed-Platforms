import torch
import torch.nn as nn
import torch.optim as optim
from core.dataset import MultimodalWindowDataset, collate_windows
from core.fusion import MultimodalFusionModel
from torch.utils.data import DataLoader

# CONFIG
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 0.001
DATA_PATH = "data/train_windows.jsonl" # You need to generate this

def train():
    # 1. Setup Device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")

    # 2. Load Data
    # For testing, create a dummy file if it doesn't exist
    try:
        dataset = MultimodalWindowDataset(DATA_PATH)
    except FileNotFoundError:
        print(f"❌ Data file {DATA_PATH} not found. Please run 'scripts/build_dataset.py' first.")
        return

    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_windows)

    # 3. Initialize Model
    model = MultimodalFusionModel(embed_dim=64).to(device)
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.BCELoss() # Binary Cross Entropy

    # 4. Training Loop
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0
        for batch_idx, (windows, labels) in enumerate(dataloader):
            labels = labels.to(device)

            # Forward Pass
            # Note: We must iterate windows in the model forward or batch them inside.
            # Our current model forward() takes a single window.
            # For efficiency, we should vectorise the encoders.
            # For this MVP refactor, we loop (slower but correct).

            outputs = []
            for w in windows:
                scores = model(w, device=device)
                outputs.append(scores['fusion'])

            # Stack outputs: (BatchSize, 1)
            preds = torch.tensor(outputs, dtype=torch.float32, device=device).unsqueeze(1)
            preds.requires_grad = True # Hack for loop-based forward, ideally model handles batch

            # IMPORTANT: The loop above breaks autograd if not careful.
            # CORRECT WAY: The model encoders should accept lists.
            # Let's assume for this step we run one-by-one or refactor model later.
            # For now, let's fix the Model to accept batches?
            # No, keep it simple. We will just execute the model call cleanly.

            # Re-running forward properly to keep graph connected:
            batch_preds = []
            for w in windows:
                # This keeps the graph connected to model params
                out = model.fusion_mlp(
                    torch.cat([
                        model.metric_enc(w.metrics, device),
                        model.log_enc(w.logs, device),
                        model.trace_enc(w.traces, device)
                    ], dim=1)
                )
                batch_preds.append(out)

            preds = torch.stack(batch_preds).squeeze(1) # (Batch, 1)

            loss = criterion(preds, labels)

            # Backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

        print(f"Epoch {epoch+1}/{EPOCHS} | Loss: {total_loss/len(dataloader):.4f}")

    # 5. Save Model
    torch.save(model.state_dict(), "models/fusion_v2.pth")
    print("✅ Model saved to models/fusion_v2.pth")

if __name__ == "__main__":
    train()
