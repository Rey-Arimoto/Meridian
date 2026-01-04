# python/core/meridian_policy_core.py
from config import CRITICAL_ENTROPY_BP


class MeridianPolicyCore:
    """
    v0.1 policy core:
    - deliberately simple
    - exposure is reduced as entropy rises
    - if entropy >= CRITICAL, action is frozen elsewhere (and target is forced to 0.0)
    """

    def __init__(self):
        self.target_weight_default = 0.5  # baseline exposure

    @staticmethod
    def classify_volatility_band(entropy_bp: int) -> str:
        # v0.1: entropy_bp is used as proxy for volatility regime
        if entropy_bp < 2000:
            return "V1"
        elif entropy_bp < 8000:
            return "V2"
        else:
            return "V3"

    @staticmethod
    def classify_entropy_state(entropy_bp: int) -> str:
        if entropy_bp >= CRITICAL_ENTROPY_BP:
            return "H_minus"
        elif entropy_bp >= 3000:
            return "H_zero"
        else:
            return "H_plus"

    def decide_target_weight(self, entropy_bp: int) -> float:
        # v0.1: entropy high => reduce exposure
        if entropy_bp >= CRITICAL_ENTROPY_BP:
            return 0.0
        if entropy_bp >= 8000:
            return 0.1
        if entropy_bp >= 3000:
            return 0.3
        return self.target_weight_default
