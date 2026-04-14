import torch
import torch.nn as nn

class HybridFusion(nn.Module):
    """
    Weighted average of MSIF-LSTM and PLE-GRU.
    Intelligent weighted fusion with context-aware weight adjustment.
    """

    def __init__(self):
        super(HybridFusion, self).__init__()

        self.default_weights = {
            'msif': 0.5,
            'ple': 0.5
        }

        self.weight_rules = {
            'peak_hours': {'msif': 0.40, 'ple': 0.60},
            'off_hours': {'msif': 0.55, 'ple': 0.45},
            'high_traffic': {'msif': 0.30, 'ple': 0.70},
            'low_traffic': {'msif': 0.50, 'ple': 0.50}
        }

        self.HIGH_AGREEMENT_THRESHOLD = 0.85
        self.MODERATE_AGREEMENT_THRESHOLD = 0.60

    def calculate_dynamic_weights(self, context):
        hour = context.get('hour_of_day', 12)
        traffic_level = context.get('traffic_level', 'medium')

        if 9 <= hour <= 17:
            base_weights = self.weight_rules['peak_hours']
        else:
            base_weights = self.weight_rules['off_hours']

        if traffic_level == 'high':
            traffic_adj = self.weight_rules['high_traffic']
        else:
            traffic_adj = self.weight_rules['low_traffic']

        final_msif = 0.5 * base_weights['msif'] + 0.5 * traffic_adj['msif']
        final_ple = 1.0 - final_msif

        return {'msif': final_msif, 'ple': final_ple}

    def fuse_predictions(self, msif_score, ple_score, weights, context=None):
        model_agreement = 1.0 - abs(msif_score - ple_score)

        if model_agreement >= self.HIGH_AGREEMENT_THRESHOLD:
            hybrid_score = (weights['msif'] * msif_score + 
                           weights['ple'] * ple_score)
            fusion_method = "weighted_agreement"

        elif model_agreement >= self.MODERATE_AGREEMENT_THRESHOLD:
            hybrid_score = max(msif_score, ple_score)
            fusion_method = "conservative_max"

        else:
            hybrid_score = max(msif_score, ple_score)
            fusion_method = "conflict_detected"

        return hybrid_score, fusion_method, model_agreement

    def forward(self, msif_score, ple_score, context=None):
        if isinstance(msif_score, torch.Tensor):
            msif_score = float(msif_score.item())
        if isinstance(ple_score, torch.Tensor):
            ple_score = float(ple_score.item())

        if context:
            weights = self.calculate_dynamic_weights(context)
        else:
            weights = self.default_weights

        hybrid_score, fusion_method, model_agreement = self.fuse_predictions(
            msif_score, ple_score, weights, context
        )

        return hybrid_score, fusion_method, model_agreement, weights
