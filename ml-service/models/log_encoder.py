import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer


class LogEncoder(nn.Module):
    """
    Encodes log messages using pre-trained transformer (DistilBERT).
    Handles variable-length text sequences.

    Input: List of log strings (batch_size raw messages)
    Output: [batch_size, 768] embeddings
    """
    def __init__(self, model_name='distilbert-base-uncased', freeze_transformer=True):
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.transformer = AutoModel.from_pretrained(model_name)

        # Freeze transformer weights to speed up training (fine-tuning optional)
        if freeze_transformer:
            for param in self.transformer.parameters():
                param.requires_grad = False

        # Projection layer to match your fusion dimension
        self.projection = nn.Sequential(
            nn.Linear(768, 768),
            nn.LayerNorm(768),
            nn.ReLU(),
            nn.Dropout(0.2)
        )

    def forward(self, log_messages):
        """
        Args:
            log_messages: List[str] - Raw log text (e.g., ["ERROR: timeout", "INFO: ok"])

        Returns:
            embeddings: torch.Tensor [batch_size, 768]
        """
        if not log_messages or len(log_messages) == 0:
            # Return zero embeddings for empty logs
            return torch.zeros(1, 768)

        # Tokenize with padding and truncation
        inputs = self.tokenizer(
            log_messages,
            padding=True,
            truncation=True,
            max_length=128,
            return_tensors='pt'
        )

        # Move to same device as model
        device = next(self.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # Get [CLS] token embeddings (sentence representation)
        with torch.no_grad() if not self.training else torch.enable_grad():
            outputs = self.transformer(**inputs)
            # outputs.last_hidden_state: [batch, seq_len, 768]
            cls_embeddings = outputs.last_hidden_state[:, 0, :]  # [batch, 768]

        # Apply projection
        return self.projection(cls_embeddings)
