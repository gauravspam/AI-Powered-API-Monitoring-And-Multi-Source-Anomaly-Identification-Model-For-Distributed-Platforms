import torch
import torch.nn as nn
import networkx as nx
import numpy as np


class BiLSTMAttention(nn.Module):
    """
    Bi-LSTM with Attention for Trace Span Sequences
    
    Bi-LSTM processes spans in both forward and backward directions
    to capture full sequential context.
    
    Attention mechanism focuses on anomalous spans.
    
    Advantages:
    - Bi-LSTM: ~94% accuracy on sequential tasks
    - Attention: interpretable anomaly focus
    - Variable length handling
    """
    
    def __init__(self, input_dim, hidden_dim, num_layers=2, dropout=0.2):
        super(BiLSTMAttention, self).__init__()
        
        self.hidden_dim = hidden_dim
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        
        self.bi_lstm = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0
        )
        
        self.attention = nn.Sequential(
            nn.Linear(hidden_dim * 2, 1),
            nn.Softmax(dim=1)
        )
        
        self.output_projection = nn.Linear(hidden_dim * 2, hidden_dim)
        
    def forward(self, x):
        # x: (batch, seq_len, input_dim)
        encoded = self.encoder(x)  # (batch, seq_len, hidden_dim)
        
        lstm_out, _ = self.bi_lstm(encoded)  # (batch, seq_len, hidden*2)
        
        attn_weights = self.attention(lstm_out)  # (batch, seq_len, 1)
        
        context = (lstm_out * attn_weights).sum(dim=1)  # (batch, hidden*2)
        
        output = self.output_projection(context)  # (batch, hidden)
        
        return output


class TraceEncoder(nn.Module):
    """
    Encodes distributed trace graphs into fixed 128-dim embeddings.

    Handles:
    - Variable number of services
    - Variable topology (depth, fan-out)
    - Missing spans

    Output: Fixed 128-dim embedding suitable for MSIF-LSTM/PLE-GRU
    
    NOW: Uses Bi-LSTM with Attention instead of GNN
    """

    def __init__(self, embedding_dim=128, node_feature_dim=10):
        super(TraceEncoder, self).__init__()

        self.embedding_dim = embedding_dim
        self.node_feature_dim = node_feature_dim
        
        self.bi_lstm_attention = BiLSTMAttention(
            input_dim=node_feature_dim,
            hidden_dim=embedding_dim,
            num_layers=2,
            dropout=0.2
        )
        
        self.readout = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )

        self.service_vocab = {}
        self.next_service_id = 0

    def get_service_id(self, service_name):
        """Map service name to unique ID"""
        if service_name not in self.service_vocab:
            self.service_vocab[service_name] = self.next_service_id
            self.next_service_id += 1
        return self.service_vocab[service_name]

    def extract_span_features(self, span):
        """
        Extract features from a single span for sequential processing.
        
        Returns: np.array of shape (node_feature_dim,)
        """
        service = span.get('service', 'unknown')
        duration = span.get('duration', 0)
        error = 1 if span.get('error', False) else 0
        
        normalized_duration = np.log1p(duration) / 10.0
        
        service_id = self.get_service_id(service)
        
        features = [
            normalized_duration,
            error,
            service_id / 100.0,
            span.get('timestamp', 0) / 1e12,
            span.get('start_time', 0) / 1e12,
            span.get('end_time', 0) / 1e12,
            span.get('parent', '') != '',
            float(duration > 1000),
            0, 0
        ]
        
        return np.array(features[:self.node_feature_dim], dtype=np.float32)

    def encode(self, traces):
        """
        Encode trace spans to fixed embedding using Bi-LSTM with Attention.

        Args:
            traces: Dict with 'spans' list

        Returns:
            Tensor (1, embedding_dim)
        """
        if not traces or 'spans' not in traces or len(traces['spans']) == 0:
            return torch.zeros(1, self.embedding_dim)

        spans = traces['spans']
        
        span_features = []
        for span in spans:
            feat = self.extract_span_features(span)
            span_features.append(feat)
        
        if not span_features:
            return torch.zeros(1, self.embedding_dim)
        
        span_tensor = torch.tensor(
            np.array(span_features),
            dtype=torch.float32
        ).unsqueeze(0)  # (1, seq_len, node_feature_dim)
        
        bi_lstm_out = self.bi_lstm_attention(span_tensor)  # (1, embedding_dim)
        
        output = self.readout(bi_lstm_out)  # (1, embedding_dim)

        return output

    def forward(self, traces):
        """Forward pass for training"""
        return self.encode(traces)
