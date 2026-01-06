from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class Regime(Enum):
    """
    Constitutional regime taxonomy (authoritative).
    UNKNOWN is the fail-closed fallback.
    """
    STABLE_RANGE = "stable_range"
    EMERGING_TREND = "emerging_trend"
    VOLATILE_NOISE = "volatile_noise"
    LIQUIDITY_STRESS = "liquidity_stress"
    REGIME_TRANSITION = "regime_transition"
    POST_STRESS_RESET = "post_stress_reset"
    UNKNOWN = "unknown"


class BaseAction(Enum):
    """
    Constitutional action primitives (authoritative).
    """
    ACT = "act"
    GUARD = "guard"
    SHRINK = "shrink"
    PAUSE = "pause"


# Authoritative Regime × Action Matrix (v0.2 Constitution)
REGIME_ACTION_MATRIX: Dict[Regime, BaseAction] = {
    Regime.STABLE_RANGE:      BaseAction.ACT,
    Regime.EMERGING_TREND:    BaseAction.GUARD,
    Regime.VOLATILE_NOISE:    BaseAction.PAUSE,   # Act forbidden
    Regime.LIQUIDITY_STRESS:  BaseAction.SHRINK,
    Regime.REGIME_TRANSITION: BaseAction.PAUSE,   # Act forbidden
    Regime.POST_STRESS_RESET: BaseAction.PAUSE,   # Observe before re-entry
    Regime.UNKNOWN:           BaseAction.PAUSE,   # Fail-closed
}


def validate_matrix() -> None:
    # Ensure every Regime is mapped exactly once
    for r in Regime:
        if r not in REGIME_ACTION_MATRIX:
            raise ValueError(f"REGIME_ACTION_MATRIX missing: {r.value}")


# Validate at import-time (fail fast)
validate_matrix()


def get_base_action(regime: Regime) -> BaseAction:
    """
    The ONLY valid way to derive BaseAction from Regime.
    No caller should bypass this lookup.
    """
    return REGIME_ACTION_MATRIX.get(regime, BaseAction.PAUSE)


@dataclass(frozen=True)
class RegimeClassification:
    regime: Regime
    reason: str
    entropy_bp: int
    confidence: str  # "high" | "medium" | "low"


class RegimeClassifier:
    """
    v0.2 regime classifier (entropy_bp-only, with hysteresis).

    NOTE: This PR introduces the classifier but does NOT wire it into decisions yet.
    """

    def __init__(
        self,
        *,
        critical_entropy_bp: int = 9000,
        volatile_entry: int = 7000,
        volatile_exit: int = 6000,
        emerging_entry: int = 3500,
        emerging_exit: int = 2500,
        stable_max: int = 2000,
    ):
        self.critical_entropy_bp = int(critical_entropy_bp)

        self.volatile_entry = int(volatile_entry)
        self.volatile_exit = int(volatile_exit)

        self.emerging_entry = int(emerging_entry)
        self.emerging_exit = int(emerging_exit)

        self.stable_max = int(stable_max)

        # hysteresis memory
        self._last_regime: Optional[Regime] = None

    def classify(self, entropy_bp: int, **_kwargs) -> RegimeClassification:
        e = int(entropy_bp)

        # 1) Hard stop / transition (entropy-based)
        if e >= self.critical_entropy_bp:
            r = Regime.REGIME_TRANSITION
            self._last_regime = r
            return RegimeClassification(
                regime=r,
                reason=f"entropy_bp {e} >= critical {self.critical_entropy_bp}",
                entropy_bp=e,
                confidence="high",
            )

        last = self._last_regime

        # 2) Volatile/Noise with hysteresis
        # - enter: >= volatile_entry
        # - exit:  <= volatile_exit
        if last == Regime.VOLATILE_NOISE:
            if e > self.volatile_exit:
                return RegimeClassification(
                    regime=Regime.VOLATILE_NOISE,
                    reason=f"hysteresis keep volatile: {e} > volatile_exit {self.volatile_exit}",
                    entropy_bp=e,
                    confidence="medium",
                )
            # exit volatile
            last = None  # fallthrough to re-classify
        if e >= self.volatile_entry:
            self._last_regime = Regime.VOLATILE_NOISE
            return RegimeClassification(
                regime=Regime.VOLATILE_NOISE,
                reason=f"entropy_bp {e} >= volatile_entry {self.volatile_entry}",
                entropy_bp=e,
                confidence="high",
            )

        # 3) Emerging trend with hysteresis
        if last == Regime.EMERGING_TREND:
            if e > self.emerging_exit:
                return RegimeClassification(
                    regime=Regime.EMERGING_TREND,
                    reason=f"hysteresis keep emerging: {e} > emerging_exit {self.emerging_exit}",
                    entropy_bp=e,
                    confidence="medium",
                )
            last = None
        if e >= self.emerging_entry:
            self._last_regime = Regime.EMERGING_TREND
            return RegimeClassification(
                regime=Regime.EMERGING_TREND,
                reason=f"entropy_bp {e} >= emerging_entry {self.emerging_entry}",
                entropy_bp=e,
                confidence="high",
            )

        # 4) Stable/Range
        if e <= self.stable_max:
            self._last_regime = Regime.STABLE_RANGE
            return RegimeClassification(
                regime=Regime.STABLE_RANGE,
                reason=f"entropy_bp {e} <= stable_max {self.stable_max}",
                entropy_bp=e,
                confidence="high",
            )

        # 5) Intermediate zone: Post-stress reset (observe) by default
        # This is intentionally conservative (fail-closed-ish).
        self._last_regime = Regime.POST_STRESS_RESET
        return RegimeClassification(
            regime=Regime.POST_STRESS_RESET,
            reason=f"intermediate zone: stable_max {self.stable_max} < {e} < emerging_entry {self.emerging_entry}",
            entropy_bp=e,
            confidence="low",
        )
