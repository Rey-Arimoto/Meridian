# python/core/safety_overlay.py
"""
Safety Overlay v1: Deterministic safety rules that suppress excessive trading.

Purpose:
- Receives PolicyDecision from MeridianPolicyCore
- Applies safety rules to calculate final_target_weight
- Rules are SUPPRESSION-ONLY (never increase exposure)
- All error paths fail-closed to 0.0

Rules:
1. Cooldown: No weight changes for COOLDOWN_SECONDS after last change
2. Max Delta: Limit per-step weight change to MAX_DW_PER_STEP
3. Min Threshold: Ignore changes below MIN_DW_IGNORE
4. Fail-Closed: Unknown/error → 0.0
5. Emergency Freeze: Respect existing FREEZE (0.0)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .meridian_policy_core import PolicyDecision
from .regime_matrix import Regime


@dataclass
class SafetyOverlayResult:
    """Result of applying safety overlay to a policy decision"""
    final_target_weight: float
    overlay_rule: str  # Which rule was applied (for logging)
    suppressed: bool   # True if overlay modified the target_weight


class SafetyOverlay:
    """
    Safety Overlay v1: Deterministic suppression-only rules.

    Applies safety constraints on top of PolicyDecision to prevent:
    - Excessive trading (cooldown)
    - Rapid weight changes (max delta)
    - Noisy micro-adjustments (min threshold)
    - Unstable states (fail-closed)
    """

    def __init__(
        self,
        *,
        enabled: bool = True,
        cooldown_seconds: int = 600,
        max_dw_per_step: float = 0.05,
        min_dw_ignore: float = 0.02,
    ):
        """
        Initialize Safety Overlay.

        Args:
            enabled: If False, overlay passes through without modification
            cooldown_seconds: Minimum time between weight changes
            max_dw_per_step: Maximum absolute weight change per step
            min_dw_ignore: Minimum weight change to act on (below this = HOLD)
        """
        self.enabled = enabled
        self.cooldown_seconds = int(cooldown_seconds)
        self.max_dw_per_step = float(max_dw_per_step)
        self.min_dw_ignore = float(min_dw_ignore)

        # State tracking (for cooldown)
        self._last_change_time: Optional[datetime] = None
        self._last_weight: float = 0.0

    def apply(
        self,
        decision: Optional[PolicyDecision],
        current_weight: float,
        now_utc: datetime,
        emergency_freeze: bool = False,
    ) -> SafetyOverlayResult:
        """
        Apply safety overlay to a policy decision.

        Args:
            decision: PolicyDecision from MeridianPolicyCore (or None if unavailable)
            current_weight: Current portfolio weight
            now_utc: Current UTC timestamp
            emergency_freeze: True if emergency freeze is active

        Returns:
            SafetyOverlayResult with final_target_weight and rule applied
        """
        # If overlay disabled, pass through
        if not self.enabled:
            if decision is None:
                return SafetyOverlayResult(
                    final_target_weight=0.0,
                    overlay_rule="DISABLED_FAIL_CLOSED",
                    suppressed=True,
                )
            return SafetyOverlayResult(
                final_target_weight=decision.target_weight,
                overlay_rule="DISABLED_PASSTHROUGH",
                suppressed=False,
            )

        # Rule 5: Emergency Freeze - respect existing FREEZE
        if emergency_freeze:
            return SafetyOverlayResult(
                final_target_weight=0.0,
                overlay_rule="EMERGENCY_FREEZE",
                suppressed=True,
            )

        # Rule 4: Fail-Closed - missing decision or UNKNOWN regime
        if decision is None:
            return SafetyOverlayResult(
                final_target_weight=0.0,
                overlay_rule="FAIL_CLOSED_NO_DECISION",
                suppressed=True,
            )

        if decision.regime == Regime.UNKNOWN:
            return SafetyOverlayResult(
                final_target_weight=0.0,
                overlay_rule="FAIL_CLOSED_UNKNOWN_REGIME",
                suppressed=True,
            )

        # Get target from decision
        target_weight = decision.target_weight

        # Calculate delta
        delta = target_weight - current_weight

        # Rule 3: Min Threshold - ignore small changes
        if abs(delta) < self.min_dw_ignore:
            return SafetyOverlayResult(
                final_target_weight=current_weight,
                overlay_rule="MIN_THRESHOLD_HOLD",
                suppressed=(abs(delta) > 0),
            )

        # Rule 1: Cooldown - prevent changes during cooldown period
        if self._last_change_time is not None:
            elapsed = (now_utc - self._last_change_time).total_seconds()
            if elapsed < self.cooldown_seconds:
                # Still in cooldown, maintain current weight
                return SafetyOverlayResult(
                    final_target_weight=current_weight,
                    overlay_rule=f"COOLDOWN_HOLD_{int(self.cooldown_seconds - elapsed)}s",
                    suppressed=True,
                )

        # Rule 2: Max Delta - limit per-step change
        if abs(delta) > self.max_dw_per_step:
            # Clamp delta to max allowed
            clamped_delta = self.max_dw_per_step if delta > 0 else -self.max_dw_per_step
            final_weight = current_weight + clamped_delta

            # Update state (change is happening, but clamped)
            self._last_change_time = now_utc
            self._last_weight = final_weight

            return SafetyOverlayResult(
                final_target_weight=final_weight,
                overlay_rule=f"MAX_DELTA_CLAMP_{abs(delta):.3f}→{abs(clamped_delta):.3f}",
                suppressed=True,
            )

        # No overlay rule triggered, allow change
        # Update state
        self._last_change_time = now_utc
        self._last_weight = target_weight

        return SafetyOverlayResult(
            final_target_weight=target_weight,
            overlay_rule="ALLOW",
            suppressed=False,
        )

    def reset(self):
        """Reset overlay state (for testing or manual intervention)"""
        self._last_change_time = None
        self._last_weight = 0.0
