import os
import re

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import BertModel, BertTokenizer

# --- CONFIG ---
MAX_LEN = 64
BATCH_SIZE = 32
EPOCHS = 5  # Start small
LEARNING_RATE = 2e-5
EMBEDDING_DIM = 128
DATA_PATH = "data/raw/loghub/HDFS.log"
MODEL_SAVE_PATH = "models/encoders/log/"


# --- 1. DATASET CLASS ---
class LogDataset(Dataset):
    def __init__(self, log_file, tokenizer, max_len):
        self.logs = self.load_logs(log_file)
        self.tokenizer = tokenizer
        self.max_len = max_len

    def load_logs(self, log_file, limit=50000):
        print(f"⏳ Loading logs from {log_file}...")
        logs = []
        try:
            with open(log_file, "r") as f:
                for i, line in enumerate(f):
                    if i >= limit:
                        break
                    # HDFS format: <Date> <Time> <Pid> <Level> <Component>: <Content>
                    # We only want the Content (message)
                    parts = line.strip().split(":", 1)
                    if len(parts) > 1:
                        content = parts[1].strip()
                        # Simple cleanup (remove numbers/IPs to help generalization)
                        content = re.sub(r"\d+", "[NUM]", content)
                        logs.append(content)
        except FileNotFoundError:
            print("❌ Log file not found! Generating dummy data for testing.")
            return [
                "System started",
                "Connection failed to 192.168.1.1",
                "Timeout waiting for service",
            ] * 100

        print(f"✅ Loaded {len(logs)} log lines.")
        return logs

    def __len__(self):
        return len(self.logs)

    def __getitem__(self, item):
        log_text = str(self.logs[item])

        # FIXED: Use tokenizer(...) instead of encode_plus
        encoding = self.tokenizer(
            log_text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            return_tensors="pt",
        )

        return {
            "log_text": log_text,
            "input_ids": encoding["input_ids"].flatten(),
            "attention_mask": encoding["attention_mask"].flatten(),
        }


# --- 2. MODEL ARCHITECTURE ---
class LogEncoder(nn.Module):
    def __init__(self, embedding_dim=128):
        super(LogEncoder, self).__init__()
        self.bert = BertModel.from_pretrained("bert-base-uncased")

        self.projection = nn.Sequential(
            nn.Linear(768, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, embedding_dim),
        )

    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        embedding = self.projection(pooled_output)
        return embedding


# --- 3. TRAINING LOOP ---
def train():
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 Training on {device}")

    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    dataset = LogDataset(DATA_PATH, tokenizer, MAX_LEN)

    # Use num_workers=0 to avoid multiprocessing issues in some envs
    data_loader = DataLoader(
        dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=0
    )

    model = LogEncoder(EMBEDDING_DIM)
    model = model.to(device)

    print("⚠️  Note: Full BERT pre-training takes hours/days.")
    print("⚠️  This script initializes the encoder and verifies the pipeline works.")

    model.train()
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)

    for epoch in range(EPOCHS):
        total_loss = 0
        for batch_idx, batch in enumerate(data_loader):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            optimizer.zero_grad()

            embedding = model(input_ids, attention_mask)

            loss = embedding.norm()

            loss.backward()
            optimizer.step()
            total_loss += loss.item()

            if batch_idx % 10 == 0:
                print(
                    f"Batch {batch_idx}/{len(data_loader)} Loss: {loss.item():.4f}",
                    end="\r",
                )

        print(
            f"\nEpoch {epoch + 1}/{EPOCHS} complete. Avg Loss: {total_loss / len(data_loader)}"
        )

    torch.save(model.state_dict(), os.path.join(MODEL_SAVE_PATH, "log_encoder.pth"))
    print(f"✅ Log Encoder saved to {MODEL_SAVE_PATH}")

    print(f"✅ Log Encoder saved to {MODEL_SAVE_PATH}")


if __name__ == "__main__":
    train()
