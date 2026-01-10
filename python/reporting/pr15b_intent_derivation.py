"""
PR15B: Intent Derivation (Layer B - Reporting)

This module derives primary Intent from v0.2 execution logs.

Key Properties:
- READ-ONLY: Does not modify agent, log schema, or trading logic
- Deterministic: Same inputs always produce same Intent
- Fail-safe: Returns "N/A" on missing data, never crashes
- Layer B: Intent computed in reporting layer (not at decision time)

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

import pandas as pd


def derive_intent_primary(df: pd.DataFrame) -> pd.Series:
    """
    Derive primary Intent from v0.2 execution log.

    Args:
        df: DataFrame with v0.2 log columns (regime, base_action, decision_reason, action_label)

    Returns:
        pd.Series with dtype=str, values are canonical Intent names or "N/A"

    Intent Priority (evaluated top to bottom, first match wins):
    1. PAUSE: Constitutional freeze/emergency
    2. STABILIZE: Regime transition
    3. DEFEND: High entropy/volatility
    4. HARVEST: Mean reversion/value extraction
    5. SEEK: Actively searching for opportunities
    6. IDLE: Holding current state
    7. N/A: Cannot determine (missing data)

    Notes:
    - Does NOT modify df in-place
    - Case-insensitive string matching
    - Strips whitespace before comparison
    - Returns "N/A" for missing/invalid data (never crashes)
    """
    # Check required columns
    required_cols = ["regime", "base_action", "decision_reason", "action_label"]

    # Initialize result series with N/A
    result = pd.Series(["N/A"] * len(df), index=df.index, dtype=str)

    # Helper: safe string normalization
    def normalize(series: pd.Series) -> pd.Series:
        """Normalize string series: strip + lowercase, fillna("")."""
        return series.fillna("").astype(str).str.strip().str.lower()

    # Extract and normalize columns (safe even if missing)
    regime = normalize(df.get("regime", pd.Series([""] * len(df))))
    base_action = normalize(df.get("base_action", pd.Series([""] * len(df))))
    decision_reason = normalize(df.get("decision_reason", pd.Series([""] * len(df))))
    action_label = normalize(df.get("action_label", pd.Series([""] * len(df))))

    # Apply priority rules (top to bottom, first match wins)

    # 1. PAUSE: Constitutional freeze
    pause_mask = (
        (base_action == "pause") |
        decision_reason.str.contains("emergency_freeze", na=False, case=False) |
        decision_reason.str.contains("pause", na=False, case=False)
    )
    result[pause_mask] = "PAUSE"

    # 2. STABILIZE: Regime transition
    stabilize_mask = (
        ~pause_mask &
        (
            (regime == "regime_transition") |
            regime.str.contains("transition", na=False, case=False)
        )
    )
    result[stabilize_mask] = "STABILIZE"

    # 3. DEFEND: High entropy/volatility
    defend_mask = (
        ~pause_mask &
        ~stabilize_mask &
        (
            regime.str.contains("volatile", na=False, case=False) |
            regime.str.contains("high", na=False, case=False) |
            regime.str.contains("critical", na=False, case=False)
        )
    )
    result[defend_mask] = "DEFEND"

    # 4. HARVEST: Mean reversion / value extraction
    harvest_mask = (
        ~pause_mask &
        ~stabilize_mask &
        ~defend_mask &
        (
            decision_reason.str.contains("mean_reversion", na=False, case=False) |
            decision_reason.str.contains("distortion", na=False, case=False) |
            decision_reason.str.contains("harvest", na=False, case=False)
        )
    )
    result[harvest_mask] = "HARVEST"

    # 5. SEEK: Actively searching (BUY/SELL actions)
    seek_mask = (
        ~pause_mask &
        ~stabilize_mask &
        ~defend_mask &
        ~harvest_mask &
        (
            (base_action == "buy") |
            (base_action == "sell") |
            (base_action == "act") |  # v0.2 uses "act" for active mode
            (action_label == "buy") |
            (action_label == "sell")
        )
    )
    result[seek_mask] = "SEEK"

    # 6. IDLE: Holding current state
    idle_mask = (
        ~pause_mask &
        ~stabilize_mask &
        ~defend_mask &
        ~harvest_mask &
        ~seek_mask &
        (
            (base_action == "hold") |
            (action_label == "hold")
        )
    )
    result[idle_mask] = "IDLE"

    # 7. N/A: Already initialized, no change needed
    # Rows that didn't match any rule remain "N/A"

    return result


def derive_intent_with_reason(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive Intent with reasoning explanation.

    Args:
        df: DataFrame with v0.2 log columns

    Returns:
        DataFrame with two columns:
        - intent_primary: Canonical Intent name
        - intent_reason: Brief explanation of why this Intent was selected

    Notes:
    - Does NOT modify input df
    - Useful for debugging and reporting
    """
    intent = derive_intent_primary(df)

    # Generate reason based on Intent
    reason = pd.Series([""] * len(df), index=df.index, dtype=str)

    reason[intent == "PAUSE"] = "Constitutional freeze or emergency"
    reason[intent == "STABILIZE"] = "Regime transition detected"
    reason[intent == "DEFEND"] = "High entropy/volatility regime"
    reason[intent == "HARVEST"] = "Value extraction opportunity"
    reason[intent == "SEEK"] = "Active opportunity search"
    reason[intent == "IDLE"] = "Holding current state"
    reason[intent == "N/A"] = "Insufficient data to determine Intent"

    return pd.DataFrame({
        "intent_primary": intent,
        "intent_reason": reason
    }, index=df.index)
