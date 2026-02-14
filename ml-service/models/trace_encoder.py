import networkx as nx
import torch
import torch.nn as nn
import torch.nn.functional as F


class TraceEncoder(nn.Module):
    """
    Encodes distributed trace graphs using simplified GNN (Graph Convolutional Network).
    Processes service call relationships and aggregates node features.

    Input: Adjacency matrix [batch, num_nodes, num_nodes] + node features [batch, num_nodes, feature_dim]
    Output: [batch, 128] embeddings
    """
    def __init__(self, node_feature_dim=10, hidden_dim=64, output_dim=128):
        super().__init__()

        # GCN layers
        self.gc1 = nn.Linear(node_feature_dim, hidden_dim)
        self.gc2 = nn.Linear(hidden_dim, output_dim)

        # Batch normalization
        self.bn1 = nn.BatchNorm1d(hidden_dim)
        self.bn2 = nn.BatchNorm1d(output_dim)

        # Dropout
        self.dropout = nn.Dropout(0.3)

    def forward(self, adj, node_features):
        """
        Args:
            adj: torch.Tensor [batch, num_nodes, num_nodes] - Adjacency matrix
            node_features: torch.Tensor [batch, num_nodes, feature_dim] - Node features

        Returns:
            graph_embedding: torch.Tensor [batch, output_dim]
        """
        if adj.size(0) == 0:
            return torch.zeros(1, 128)

        batch_size, num_nodes, _ = adj.shape

        # First GCN layer: A @ X @ W
        x = torch.matmul(adj, node_features)  # [batch, num_nodes, feature_dim]
        x = self.gc1(x)  # [batch, num_nodes, hidden_dim]

        # Batch norm (reshape for BatchNorm1d)
        x = x.transpose(1, 2)  # [batch, hidden_dim, num_nodes]
        x = self.bn1(x)
        x = x.transpose(1, 2)  # [batch, num_nodes, hidden_dim]

        x = F.relu(x)
        x = self.dropout(x)

        # Second GCN layer
        x = torch.matmul(adj, x)  # [batch, num_nodes, hidden_dim]
        x = self.gc2(x)  # [batch, num_nodes, output_dim]

        # Batch norm
        x = x.transpose(1, 2)
        x = self.bn2(x)
        x = x.transpose(1, 2)

        # Global mean pooling (aggregate all nodes)
        graph_embedding = torch.mean(x, dim=1)  # [batch, output_dim]

        return graph_embedding
