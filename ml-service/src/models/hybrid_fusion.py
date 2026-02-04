import torch
import torch.nn as nn

class HybridFusion(nn.Module):
    """
    YOUR ORIGINAL FUSION LOGIC - Weighted average of MSIF-LSTM and PLE-GRU.

    This preserves your thesis contribution:
    - Compare MSIF-LSTM vs PLE-GRU architectures
    - Intelligent weighted fusion
    - Context-aware weight adjustment

    Now works with multi-source unified embeddings!
    """

    def __init__(self):
        super(HybridFusion, self).__init__()

        # Default weights (can be adjusted dynamically)
        self.default_weights = {
            'msif': 0.5,
            'ple': 0.5
        }

        # Context-aware weight rules (your existing logic)
        self.weight_rules = {
            'peak_hours': {'msif': 0.40, 'ple': 0.60},
            'off_hours': {'msif': 0.55, 'ple': 0.45},
            'high_traffic': {'msif': 0.30, 'ple': 0.70},
            'low_traffic': {'msif': 0.50, 'ple': 0.50}
        }

        # Agreement thresholds (your existing logic)
        self.HIGH_AGREEMENT_THRESHOLD = 0.85
        self.MODERATE_AGREEMENT_THRESHOLD = 0.60

    def calculate_dynamic_weights(self, context):
        """
        Calculate context-aware weights (your existing logic).

        Args:
            context: Dict - {
                'hour_of_day': 14,
                'traffic_level': 'high',
                'endpoint_type': 'api'
            }

        Returns:
            Dict - {'msif': 0.4, 'ple': 0.6}
        """
        hour = context.get('hour_of_day', 12)
        traffic_level = context.get('traffic_level', 'medium')

        # Base weights from time of day
        if 9 <= hour <= 17:
            base_weights = self.weight_rules['peak_hours']
        else:
            base_weights = self.weight_rules['off_hours']

        # Adjust for traffic
        if traffic_level == 'high':
            traffic_adj = self.weight_rules['high_traffic']
        else:
            traffic_adj = self.weight_rules['low_traffic']

        # Combine adjustments
        final_msif = 0.5 * base_weights['msif'] + 0.5 * traffic_adj['msif']
        final_ple = 1.0 - final_msif

        return {'msif': final_msif, 'ple': final_ple}

    def fuse_predictions(self, msif_score, ple_score, weights, context=None):
        """
        Fuse MSIF and PLE scores using confidence-based strategy (your existing logic).

        Args:
            msif_score: float - Score from MSIF-LSTM (0-1)
            ple_score: float - Score from PLE-GRU (0-1)
            weights: Dict - {'msif': 0.5, 'ple': 0.5}
            context: Dict - Optional context for logging

        Returns:
            hybrid_score: float
            fusion_method: str
            model_agreement: float
        """
        # Calculate model agreement
        model_agreement = 1.0 - abs(msif_score - ple_score)

        # Fusion strategy based on agreement
        if model_agreement >= self.HIGH_AGREEMENT_THRESHOLD:
            # High agreement: weighted average
            hybrid_score = (weights['msif'] * msif_score + 
                           weights['ple'] * ple_score)
            fusion_method = "weighted_agreement"

        elif model_agreement >= self.MODERATE_AGREEMENT_THRESHOLD:
            # Moderate agreement: conservative max
            hybrid_score = max(msif_score, ple_score)
            fusion_method = "conservative_max"

        else:
            # Conflict: take max (conservative approach)
            hybrid_score = max(msif_score, ple_score)
            fusion_method = "conflict_detected"

        return hybrid_score, fusion_method, model_agreement

    def forward(self, msif_score, ple_score, context=None):
        """
        Forward pass for training.

        Args:
            msif_score: Tensor or float
            ple_score: Tensor or float
            context: Dict - Optional context

        Returns:
            hybrid_score: Tensor or float
        """
        # Convert to float if tensors
        if isinstance(msif_score, torch.Tensor):
            msif_score = float(msif_score.item())
        if isinstance(ple_score, torch.Tensor):
            ple_score = float(ple_score.item())

        # Calculate weights
        if context:
            weights = self.calculate_dynamic_weights(context)
        else:
            weights = self.default_weights

        # Fuse
        hybrid_score, fusion_method, model_agreement = self.fuse_predictions(
            msif_score, ple_score, weights, context
        )

        return hybrid_score, fusion_method, model_agreement, weights
