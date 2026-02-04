import torch
import torch.nn as nn


class VariableInputPLE_GRU(nn.Module):
    """
    Probability Label Estimation GRU (PLE-GRU).
    Uses multiple 'Expert' GRUs to learn distinct patterns from different modalities.
    """

    def __init__(self, embedding_dim=128, gru_hidden_dim=64, num_experts=3):
        super(VariableInputPLE_GRU, self).__init__()

        # Expert Networks (Separate GRUs)
        self.experts = nn.ModuleList(
            [
                nn.GRU(
                    input_size=embedding_dim,
                    hidden_size=gru_hidden_dim,
                    num_layers=2,
                    batch_first=True,
                    bidirectional=True,
                    dropout=0.3,
                )
                for _ in range(num_experts)
            ]
        )

        # Gating Network / Fusion Attention
        self.fusion = nn.MultiheadAttention(
            embed_dim=gru_hidden_dim * 2, num_heads=4, batch_first=True
        )

        # Classifier
        self.clf = nn.Sequential(
            nn.Linear(gru_hidden_dim * 2, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        # x shape: (Batch, Features) or (Batch, Seq, Features)
        if x.dim() == 2:
            x = x.unsqueeze(1)  # Ensure (Batch, 1, Features)

        expert_outs = []
        for exp in self.experts:
            # exp(x) -> (Batch, Seq, Hidden*2)
            out, _ = exp(x)
            # Take mean over sequence to get (Batch, 1, Hidden*2)
            expert_outs.append(out.mean(dim=1, keepdim=True))

        # Stack experts: (Batch, Num_Experts, Hidden*2)
        stack = torch.cat(expert_outs, dim=1)

        # Attention Fusion: "Which expert should I trust?"
        fused, _ = self.fusion(stack, stack, stack)

        # Average the fused expert opinions
        # (Batch, Hidden*2)
        context_vector = fused.mean(dim=1)

        return self.clf(context_vector)

    def predict(self, x):
        self.eval()
        with torch.no_grad():
            if x.dim() == 2:
                x = x.unsqueeze(1)
            if x.dim() == 2: x = x.unsqueeze(1)
            return float(self.forward(x).item())
