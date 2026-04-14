import torch
import torch.nn as nn
from transformers import BertTokenizer, BertModel

class LogEncoder(nn.Module):
    """
    Encodes variable-length log strings into fixed 128-dim embeddings.

    Uses pre-trained BERT from training/pretrain/train_log_encoder.py

    Handles:
    - Variable number of logs
    - Variable log lengths
    - Missing logs

    Output: Fixed 128-dim embedding suitable for MSIF-LSTM/PLE-GRU
    """

    def __init__(self, embedding_dim=128, pretrained_path=None):
        super(LogEncoder, self).__init__()

        self.embedding_dim = embedding_dim

        # Load tokenizer
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')

        # Load BERT model
        self.bert = BertModel.from_pretrained('bert-base-uncased')

        # Freeze BERT (use as feature extractor)
        for param in self.bert.parameters():
            param.requires_grad = False

        # Project BERT output (768-dim) to embedding space (128-dim)
        self.projection = nn.Sequential(
            nn.Linear(768, 256),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(256, embedding_dim),
            nn.LayerNorm(embedding_dim)
        )

        # Attention for aggregating multiple logs
        self.log_attention = nn.MultiheadAttention(
            embed_dim=embedding_dim,
            num_heads=4,
            batch_first=True
        )

        # Load pre-trained weights if available
        if pretrained_path:
            try:
                state_dict = torch.load(pretrained_path, map_location='cpu')
                # Load only projection layer (BERT is frozen)
                projection_state = {k.replace('projection.', ''): v 
                                   for k, v in state_dict.items() 
                                   if k.startswith('projection')}
                self.projection.load_state_dict(projection_state, strict=False)
                print(f"[OK] Loaded pre-trained LogEncoder from {pretrained_path}")
            except Exception as e:
                print(f"[!] Could not load pre-trained weights: {e}")

    def encode_single_log(self, log_text):
        """
        Encode a single log string.

        Args:
            log_text: str - "ERROR: Connection timeout to database"

        Returns:
            Tensor (1, embedding_dim)
        """
        # Tokenize
        encoded = self.tokenizer(
            log_text,
            padding='max_length',
            truncation=True,
            max_length=128,
            return_tensors='pt'
        )

        # Pass through BERT
        with torch.no_grad():
            outputs = self.bert(**encoded)
            # Use CLS token embedding
            cls_embedding = outputs.pooler_output  # (1, 768)

        # Project to target embedding space
        log_embedding = self.projection(cls_embedding)  # (1, embedding_dim)

        return log_embedding

    def encode(self, logs):
        """
        Encode multiple log strings to single fixed embedding.

        Args:
            logs: List[str] - [
                "ERROR: Connection timeout",
                "WARN: High latency detected",
                "INFO: Request completed"
            ]

        Returns:
            Tensor (1, embedding_dim)
        """
        if not logs or len(logs) == 0:
            # Return zero embedding if no logs
            return torch.zeros(1, self.embedding_dim)

        # Encode all logs
        log_embeddings = []
        for log_text in logs:
            if not log_text or len(log_text.strip()) == 0:
                continue

            try:
                emb = self.encode_single_log(log_text)
                log_embeddings.append(emb)
            except Exception as e:
                print(f"[!] Failed to encode log: {e}")
                continue

        if len(log_embeddings) == 0:
            return torch.zeros(1, self.embedding_dim)

        # Stack all log embeddings: (num_logs, embedding_dim)
        log_stack = torch.cat(log_embeddings, dim=0).unsqueeze(0)  # (1, num_logs, embedding_dim)

        # Apply attention to learn which logs are important
        attended, _ = self.log_attention(log_stack, log_stack, log_stack)

        # Aggregate to single embedding (mean pooling)
        aggregated = attended.mean(dim=1)  # (1, embedding_dim)

        return aggregated

    def forward(self, logs):
        """Forward pass for training"""
        return self.encode(logs)
