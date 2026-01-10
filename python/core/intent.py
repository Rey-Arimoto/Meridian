"""
Core Intent Classification Logic (v0.3)

This module provides the canonical Intent classification logic used by both:
- Layer A (agent): Real-time Intent decision at execution time
- Layer B (reporting): Post-execution Intent derivation from logs

Single Source of Truth:
- All Intent classification must use classify_intent_from_fields()
- Agent and reporting must produce identical Intent for identical inputs
- No randomness, no network, deterministic

Intent Types (6):
- SEEK: Search for opportunities
- HARVEST: Extract value from positions
- DEFEND: Protect capital from adverse moves
- STABILIZE: Reduce exposure during transitions
- PAUSE: Constitutional freeze
- IDLE: No intent, maintain state

Priority Order (fixed):
PAUSE > STABILIZE > DEFEND > HARVEST > SEEK > IDLE > N/A
"""


def classify_intent_from_fields(
    regime: str,
    base_action: str,
    decision_reason: str,
    action_label: str
) -> tuple[str, str]:
    """
    Classify Intent from decision fields (canonical implementation).

    This is the single source of truth for Intent classification.
    Used by both agent (Layer A) and reporting (Layer B).

    Args:
        regime: Regime classification (e.g., "stable_range", "volatile_noise")
        base_action: Base action before overlay (e.g., "act", "pause", "hold")
        decision_reason: Decision explanation string
        action_label: Final action label (e.g., "BUY", "SELL", "HOLD")

    Returns:
        (intent_primary, intent_reason): Tuple of Intent name and explanation

    Intent Priority (evaluated top to bottom, first match wins):
    1. PAUSE: Constitutional freeze/emergency
    2. STABILIZE: Regime transition
    3. DEFEND: High entropy/volatility
    4. HARVEST: Mean reversion/value extraction
    5. SEEK: Actively searching for opportunities
    6. IDLE: Holding current state
    7. N/A: Cannot determine (missing data)

    Notes:
    - Case-insensitive string matching
    - Strips whitespace before comparison
    - Returns "N/A" for missing/invalid data (never crashes)
    - Deterministic (same inputs always produce same output)
    """
    # Normalize inputs (strip + lowercase, handle None)
    def normalize(s):
        if s is None or not isinstance(s, str):
            return ""
        return s.strip().lower()

    regime_norm = normalize(regime)
    base_action_norm = normalize(base_action)
    decision_reason_norm = normalize(decision_reason)
    action_label_norm = normalize(action_label)

    # 1. PAUSE: Constitutional freeze
    if (
        base_action_norm == "pause" or
        "emergency_freeze" in decision_reason_norm or
        "pause" in decision_reason_norm
    ):
        return ("PAUSE", "Constitutional freeze or emergency")

    # 2. STABILIZE: Regime transition
    if (
        regime_norm == "regime_transition" or
        "transition" in regime_norm
    ):
        return ("STABILIZE", "Regime transition detected")

    # 3. DEFEND: High entropy/volatility
    if (
        "volatile" in regime_norm or
        "high" in regime_norm or
        "critical" in regime_norm
    ):
        return ("DEFEND", "High entropy/volatility regime")

    # 4. HARVEST: Mean reversion / value extraction
    if (
        "mean_reversion" in decision_reason_norm or
        "distortion" in decision_reason_norm or
        "harvest" in decision_reason_norm
    ):
        return ("HARVEST", "Value extraction opportunity")

    # 5. SEEK: Actively searching (BUY/SELL actions)
    if (
        base_action_norm in ["buy", "sell", "act"] or
        action_label_norm in ["buy", "sell"]
    ):
        return ("SEEK", "Active opportunity search")

    # 6. IDLE: Holding current state
    if (
        base_action_norm == "hold" or
        action_label_norm == "hold"
    ):
        return ("IDLE", "Holding current state")

    # 7. N/A: Cannot determine
    return ("N/A", "Insufficient data to determine Intent")
