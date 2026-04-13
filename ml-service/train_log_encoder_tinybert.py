"""
Train Log Encoder with TinyBERT-4
Smaller model (14.5M params) vs BERT (109M params)
~55MB vs ~420MB
"""

import os
import sys
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import BertModel, BertTokenizer

MAX_LEN = 64
BATCH_SIZE = 16
EPOCHS = 3
LEARNING_RATE = 2e-5
EMBEDDING_DIM = 128
MODEL_SAVE_PATH = "models/encoders/log/"


class SimpleLogDataset(Dataset):
    def __init__(self, tokenizer, max_len, size=1000):
        self.size = size
        self.tokenizer = tokenizer
        self.max_len = max_len
        self.sample_logs = [
            "INFO Starting service",
            "ERROR Connection failed",
            "WARN Memory usage high",
            "DEBUG Processing request",
            "INFO Request completed",
            "ERROR Timeout occurred",
            "WARN Retry attempt",
            "DEBUG Cache hit",
        ]
    
    def __len__(self):
        return self.size
    
    def __getitem__(self, idx):
        log = self.sample_logs[idx % len(self.sample_logs)]
        encoding = self.tokenizer(
            log,
            max_length=self.max_len,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0)
        }


class LogEncoderTinyBERT(nn.Module):
    def __init__(self, embedding_dim=128):
        super(LogEncoderTinyBERT, self).__init__()
        self.bert = BertModel.from_pretrained("huawei-noah/TinyBERT_General_4L_312D")
        self.hidden_size = 312
        
        self.projection = nn.Sequential(
            nn.Linear(self.hidden_size, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, embedding_dim),
        )
    
    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        return self.projection(pooled_output)


def train():
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")
    
    print("Loading TinyBERT-4 tokenizer...")
    tokenizer = BertTokenizer.from_pretrained("huawei-noah/TinyBERT_General_4L_312D")
    
    print("Creating dataset...")
    dataset = SimpleLogDataset(tokenizer, MAX_LEN, size=500)
    dataloader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    print("Initializing TinyBERT-4 model...")
    model = LogEncoderTinyBERT(EMBEDDING_DIM).to(device)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.MSELoss()
    
    model.train()
    for epoch in range(EPOCHS):
        total_loss = 0
        for batch_idx, batch in enumerate(dataloader):
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            
            optimizer.zero_grad()
            embedding = model(input_ids, attention_mask)
            loss = embedding.norm()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            if batch_idx % 10 == 0:
                print(f"Epoch {epoch+1}/{EPOCHS} Batch {batch_idx} Loss: {loss.item():.4f}")
        
        print(f"Epoch {epoch+1} Avg Loss: {total_loss/len(dataloader):.4f}")
    
    save_path = os.path.join(MODEL_SAVE_PATH, "log_encoder.pth")
    torch.save(model.state_dict(), save_path)
    print(f"Saved to {save_path}")
    print(f"Model size: {os.path.getsize(save_path) / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    train()