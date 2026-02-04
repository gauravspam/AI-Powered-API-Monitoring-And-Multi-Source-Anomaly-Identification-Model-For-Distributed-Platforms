import torch
import torch.nn as nn
import networkx as nx
import numpy as np

class TraceEncoder(nn.Module):
    """
    Encodes distributed trace graphs into fixed 128-dim embeddings.

    Handles:
    - Variable number of services
    - Variable topology (depth, fan-out)
    - Missing spans

    Output: Fixed 128-dim embedding suitable for MSIF-LSTM/PLE-GRU
    """

    def __init__(self, embedding_dim=128, node_feature_dim=10):
        super(TraceEncoder, self).__init__()

        self.embedding_dim = embedding_dim
        self.node_feature_dim = node_feature_dim

        # Node feature encoder
        self.node_encoder = nn.Sequential(
            nn.Linear(node_feature_dim, 64),
            nn.ReLU(),
            nn.Linear(64, embedding_dim),
            nn.LayerNorm(embedding_dim)
        )

        # Message passing neural network (simplified GNN)
        self.message_nn = nn.Sequential(
            nn.Linear(embedding_dim * 2, embedding_dim),
            nn.ReLU(),
            nn.LayerNorm(embedding_dim)
        )

        # Graph-level readout
        self.readout = nn.Sequential(
            nn.Linear(embedding_dim, embedding_dim),
            nn.ReLU(),
            nn.Dropout(0.2)
        )

        # Service name vocabulary
        self.service_vocab = {}
        self.next_service_id = 0

    def get_service_id(self, service_name):
        """Map service name to unique ID"""
        if service_name not in self.service_vocab:
            self.service_vocab[service_name] = self.next_service_id
            self.next_service_id += 1
        return self.service_vocab[service_name]

    def extract_node_features(self, span, graph):
        """
        Extract features from a single span.

        Returns: np.array of shape (node_feature_dim,)
        """
        service = span.get('service', 'unknown')
        duration = span.get('duration', 0)
        error = 1 if span.get('error', False) else 0

        # Graph topology features
        in_degree = graph.in_degree(service) if graph.has_node(service) else 0
        out_degree = graph.out_degree(service) if graph.has_node(service) else 0

        # Normalize duration (log scale)
        normalized_duration = np.log1p(duration) / 10.0

        # Feature vector: [duration, error, in_deg, out_deg, + padding]
        features = [
            normalized_duration,
            error,
            in_degree / 10.0,  # Normalize degree
            out_degree / 10.0,
            0, 0, 0, 0, 0, 0  # Padding to node_feature_dim
        ]

        return np.array(features[:self.node_feature_dim], dtype=np.float32)

    def build_graph(self, traces):
        """
        Build NetworkX graph from trace data.

        Args:
            traces: Dict - {
                'trace_id': 'abc123',
                'spans': [
                    {'service': 'api-gateway', 'duration': 100, 'parent': None},
                    {'service': 'auth-svc', 'duration': 50, 'parent': 'api-gateway'},
                    ...
                ]
            }

        Returns:
            G: NetworkX DiGraph
            node_features: Dict[service_name -> np.array]
        """
        G = nx.DiGraph()
        node_features = {}

        spans = traces.get('spans', [])
        if not spans:
            return G, node_features

        # Add nodes and edges
        for span in spans:
            service = span.get('service', f"service_{len(G.nodes)}")
            G.add_node(service)

            parent = span.get('parent')
            if parent and parent != service:
                G.add_edge(parent, service)

        # Extract features for each node
        for span in spans:
            service = span.get('service', 'unknown')
            if service in G.nodes:
                node_features[service] = self.extract_node_features(span, G)

        return G, node_features

    def encode(self, traces):
        """
        Encode trace graph to fixed embedding.

        Args:
            traces: Dict with 'spans' list

        Returns:
            Tensor (1, embedding_dim)
        """
        if not traces or 'spans' not in traces or len(traces['spans']) == 0:
            return torch.zeros(1, self.embedding_dim)

        # Build graph
        G, node_features = self.build_graph(traces)

        if len(G.nodes) == 0:
            return torch.zeros(1, self.embedding_dim)

        # Convert to tensors
        node_list = list(G.nodes())
        node_feat_matrix = torch.tensor(
            np.array([node_features.get(n, np.zeros(self.node_feature_dim)) for n in node_list]),
            dtype=torch.float32
        )  # (num_nodes, node_feature_dim)

        # Encode nodes
        node_embeddings = self.node_encoder(node_feat_matrix)  # (num_nodes, embedding_dim)

        # Message passing (1 hop aggregation)
        updated_embeddings = []
        for i, node in enumerate(node_list):
            # Get neighbors
            neighbors = list(G.neighbors(node))

            if len(neighbors) > 0:
                # Aggregate neighbor features
                neighbor_indices = [node_list.index(n) for n in neighbors if n in node_list]
                if len(neighbor_indices) > 0:
                    neighbor_feats = node_embeddings[neighbor_indices]
                    neighbor_mean = neighbor_feats.mean(dim=0, keepdim=True)

                    # Message: concat [node, neighbor_mean]
                    message = torch.cat([node_embeddings[i].unsqueeze(0), neighbor_mean], dim=1)
                    updated = self.message_nn(message)
                else:
                    updated = node_embeddings[i].unsqueeze(0)
            else:
                updated = node_embeddings[i].unsqueeze(0)

            updated_embeddings.append(updated)

        # Stack updated embeddings
        graph_embedding = torch.cat(updated_embeddings, dim=0)  # (num_nodes, embedding_dim)

        # Global pooling (mean)
        pooled = graph_embedding.mean(dim=0, keepdim=True)  # (1, embedding_dim)

        # Final readout
        output = self.readout(pooled)

        return output

    def forward(self, traces):
        """Forward pass for training"""
        return self.encode(traces)
