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

PR15A Update:
- Uses shared classify_intent_from_fields() from core.intent
- Ensures agent (Layer A) and reporting (Layer B) produce identical results
"""

import pandas as pd
from core.intent import classify_intent_from_fields


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
    - Uses shared classify_intent_from_fields() from core.intent
    - Returns "N/A" for missing/invalid data (never crashes)
    """
    # Extract columns (safe even if missing)
    regime_col = df.get("regime", pd.Series([None] * len(df), index=df.index))
    base_action_col = df.get("base_action", pd.Series([None] * len(df), index=df.index))
    decision_reason_col = df.get("decision_reason", pd.Series([None] * len(df), index=df.index))
    action_label_col = df.get("action_label", pd.Series([None] * len(df), index=df.index))

    # Apply shared classification logic row by row
    intents = []
    for i in range(len(df)):
        regime = regime_col.iloc[i] if i < len(regime_col) else None
        base_action = base_action_col.iloc[i] if i < len(base_action_col) else None
        decision_reason = decision_reason_col.iloc[i] if i < len(decision_reason_col) else None
        action_label = action_label_col.iloc[i] if i < len(action_label_col) else None

        intent_primary, _ = classify_intent_from_fields(
            regime=regime,
            base_action=base_action,
            decision_reason=decision_reason,
            action_label=action_label
        )
        intents.append(intent_primary)

    return pd.Series(intents, index=df.index, dtype=str)


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
    - Uses shared classify_intent_from_fields() from core.intent
    - Useful for debugging and reporting
    """
    # Extract columns (safe even if missing)
    regime_col = df.get("regime", pd.Series([None] * len(df), index=df.index))
    base_action_col = df.get("base_action", pd.Series([None] * len(df), index=df.index))
    decision_reason_col = df.get("decision_reason", pd.Series([None] * len(df), index=df.index))
    action_label_col = df.get("action_label", pd.Series([None] * len(df), index=df.index))

    # Apply shared classification logic row by row
    intents = []
    reasons = []
    for i in range(len(df)):
        regime = regime_col.iloc[i] if i < len(regime_col) else None
        base_action = base_action_col.iloc[i] if i < len(base_action_col) else None
        decision_reason = decision_reason_col.iloc[i] if i < len(decision_reason_col) else None
        action_label = action_label_col.iloc[i] if i < len(action_label_col) else None

        intent_primary, intent_reason = classify_intent_from_fields(
            regime=regime,
            base_action=base_action,
            decision_reason=decision_reason,
            action_label=action_label
        )
        intents.append(intent_primary)
        reasons.append(intent_reason)

    return pd.DataFrame({
        "intent_primary": pd.Series(intents, index=df.index, dtype=str),
        "intent_reason": pd.Series(reasons, index=df.index, dtype=str)
    }, index=df.index)
