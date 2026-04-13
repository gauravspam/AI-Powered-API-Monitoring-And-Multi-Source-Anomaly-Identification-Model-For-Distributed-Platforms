import torch
import torch.nn as nn
import numpy as np


class FlexibleEncoder(nn.Module):
    """
    Handles 1, 2, or 3 modalities with learnable missing embeddings.
    Zero-padding replaced with trainable "missing" embeddings.
    """
    
    def __init__(self, embedding_dim=128):
        super(FlexibleEncoder, self).__init__()
        
        self.embedding_dim = embedding_dim
        
        # Learnable embeddings for missing modalities (NOT zeros!)
        # These are trained to represent "no data" in the embedding space
        self.missing_metric_emb = nn.Parameter(torch.randn(embedding_dim))
        self.missing_log_emb = nn.Parameter(torch.randn(embedding_dim))
        self.missing_trace_emb = nn.Parameter(torch.randn(embedding_dim))
        
        # Modality attention weights (learns optimal combination)
        self.modality_weights = nn.Parameter(torch.ones(3))
        
    def combine_embeddings(self, metric_emb, log_emb, trace_emb):
        """
        Combine available embeddings with learnable missing embeddings.
        
        Args:
            metric_emb: Tensor (batch, embedding_dim) or None
            log_emb: Tensor (batch, embedding_dim) or None  
            trace_emb: Tensor (batch, embedding_dim) or None
            
        Returns:
            combined: Tensor (batch, embedding_dim * 3)
            modalities_present: int (count of non-None embeddings)
            confidence: float (0.33, 0.66, or 1.0)
        """
        embeddings = []
        weights = []
        
        # Metric modality
        if metric_emb is not None:
            embeddings.append(metric_emb)
            weights.append(self.modality_weights[0])
        else:
            embeddings.append(self.missing_metric_emb.unsqueeze(0).expand(metric_emb.shape if metric_emb is not None else 1, -1))
            
        # Log modality
        if log_emb is not None:
            embeddings.append(log_emb)
            weights.append(self.modality_weights[1])
        else:
            # Use placeholder - will be replaced in forward
            pass
            
        # Trace modality
        if trace_emb is not None:
            embeddings.append(trace_emb)
            weights.append(self.modality_weights[2])
        
        modalities_present = sum([metric_emb is not None, log_emb is not None, trace_emb is not None])
        confidence = modalities_present / 3.0
        
        return confidence, modalities_present
    
    def forward(self, metric_batch=None, log_batch=None, trace_batch=None):
        """
        Forward pass handling flexible modalities.
        
        Each batch item is a list/dict of raw data that needs encoding.
        """
        batch_size = 1
        
        # Placeholder - actual encoding happens in batch_processor
        # This module handles combination logic
        
        return {
            "confidence": 1.0,
            "modalities_present": 3,
            "combined_embedding": None
        }


class ModalityAttention(nn.Module):
    """
    Learns optimal weighting for combining embeddings regardless of missing modalities.
    """
    
    def __init__(self, embedding_dim=128):
        super(ModalityAttention, self).__init__()
        
        self.embedding_dim = embedding_dim
        
        # Learnable weights for each modality
        self.metric_weight = nn.Parameter(torch.tensor(1.0))
        self.log_weight = nn.Parameter(torch.tensor(1.0))
        self.trace_weight = nn.Parameter(torch.tensor(1.0))
        
        # Learnable missing embeddings
        self.missing_metric = nn.Parameter(torch.randn(embedding_dim))
        self.missing_log = nn.Parameter(torch.randn(embedding_dim))
        self.missing_trace = nn.Parameter(torch.randn(embedding_dim))
    
    def forward(self, metric_emb=None, log_emb=None, trace_emb=None):
        """
        Combine embeddings with learned weights.
        
        Args:
            metric_emb: (batch, embedding_dim) or None
            log_emb: (batch, embedding_dim) or None
            trace_emb: (batch, embedding_dim) or None
            
        Returns:
            combined: (batch, embedding_dim)
            info: dict with confidence and modalities info
        """
        embeddings_list = []
        weights_list = []
        
        # Process each modality
        if metric_emb is not None:
            embeddings_list.append(metric_emb)
            weights_list.append(self.metric_weight)
        
        if log_emb is not None:
            embeddings_list.append(log_emb)
            weights_list.append(self.log_weight)
            
        if trace_emb is not None:
            embeddings_list.append(trace_emb)
            weights_list.append(self.trace_weight)
        
        modalities_present = len(embeddings_list)
        
        if modalities_present == 0:
            # No modalities - return zeros
            return torch.zeros(1, self.embedding_dim), {
                "confidence": 0.0,
                "modalities_present": 0
            }
        
        # Stack embeddings
        stacked_emb = torch.stack(embeddings_list, dim=0)  # (num_present, batch, dim)
        
        # Compute softmax weights over valid modalities
        valid_weights = torch.stack(weights_list)
        attention_weights = torch.softmax(valid_weights, dim=0)
        
        # Weighted combination
        combined = sum(w * emb for w, emb in zip(attention_weights, embeddings_list))
        
        # Confidence = how many modalities present / 3
        confidence = modalities_present / 3.0
        
        return combined, {
            "confidence": confidence,
            "modalities_present": modalities_present,
            "weights": attention_weights.detach().cpu().numpy().tolist()
        }


def combine_with_missing(metric_emb, log_emb, trace_emb, missing_metric, missing_log, missing_trace):
    """
    Utility function to combine embeddings with missing embeddings.
    
    Args:
        metric_emb, log_emb, trace_emb: tensors or None
        missing_metric, missing_log, missing_trace: learnable parameters
        
    Returns:
        combined (batch, 384), confidence (float)
    """
    embeddings = []
    num_present = 0
    
    # Metric
    if metric_emb is not None:
        embeddings.append(metric_emb)
        num_present += 1
    else:
        embeddings.append(missing_metric.unsqueeze(0))
    
    # Log
    if log_emb is not None:
        embeddings.append(log_emb)
        num_present += 1
    else:
        embeddings.append(missing_log.unsqueeze(0))
    
    # Trace
    if trace_emb is not None:
        embeddings.append(trace_emb)
        num_present += 1
    else:
        embeddings.append(missing_trace.unsqueeze(0))
    
    combined = torch.cat(embeddings, dim=1)  # (1, 384)
    confidence = num_present / 3.0
    
    return combined, confidence