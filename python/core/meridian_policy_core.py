# python/core/meridian_policy_core.py
from dataclasses import dataclass
from config import CRITICAL_ENTROPY_BP, REGIME_THRESHOLDS
from .regime_matrix import (
    Regime,
    BaseAction,
    RegimeClassifier,
    RegimeClassification,
    get_base_action,
)


@dataclass(frozen=True)
class PolicyDecision:
    """v0.2 constitutional decision output"""
    regime: Regime
    base_action: BaseAction
    target_weight: float
    reason: str
    regime_classification: RegimeClassification


class MeridianPolicyCore:
    """
    v0.1 policy core:
    - deliberately simple
    - exposure is reduced as entropy rises
    - if entropy >= CRITICAL, action is frozen elsewhere (and target is forced to 0.0)
    """

    def __init__(self):
        self.target_weight_default = 0.0  # Constitutional default: PAUSE (fail-closed)
        # v0.2: Regime classifier with constitutional thresholds
        self.classifier = RegimeClassifier(**REGIME_THRESHOLDS)

    def decide(self, entropy_bp: int, current_weight: float = 0.0) -> PolicyDecision:
        """
        v0.2 Constitutional decision flow:
        1) Classify regime
        2) Lookup base_action from Regime × Action Matrix
        3) Derive target_weight from base_action
        """
        # Step 1: Classify regime
        regime_classification = self.classifier.classify(entropy_bp)
        regime = regime_classification.regime

        # Step 2: Lookup base_action from constitutional matrix
        base_action = get_base_action(regime)

        # Step 3: Derive target_weight from base_action
        # Mapping preserves PR0 (ACT→0.0 in stable) and reuses existing ladder
        action_to_weight = {
            BaseAction.PAUSE: 0.0,   # All PAUSE regimes
            BaseAction.ACT: 0.0,     # STABLE_RANGE: Preserve PR0 fail-closed
            BaseAction.GUARD: 0.3,   # EMERGING_TREND: Reuse existing medium band
            BaseAction.SHRINK: 0.1,  # LIQUIDITY_STRESS: Reuse existing high band
        }
        target_weight = action_to_weight.get(base_action, 0.0)

        # Step 4: Build reason
        reason = (
            f"Regime={regime.value} ({regime_classification.reason}); "
            f"Matrix→{base_action.value}; target_weight={target_weight}"
        )

        return PolicyDecision(
            regime=regime,
            base_action=base_action,
            target_weight=target_weight,
            reason=reason,
            regime_classification=regime_classification,
        )

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
