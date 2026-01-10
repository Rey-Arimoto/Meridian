#!/usr/bin/env python3
"""
PR40: v0.5 Intelligence Decision Engine v1 (Mirror Base-Action)

Purpose: Minimal decision engine that mirrors v0.2 base_action as v0.5 decision.

Design:
- Mirrors base_action → decision_action (exact copy)
- Generates PR38-compliant decision record
- READ-ONLY: Never modifies input
- Warning-only: Never raises exceptions

Non-Goals:
- No learning, optimization, or model
- No behavior modification (READ-ONLY)
- No v0.4 confidence evaluation or regeneration
- No v0.4 confidence featurization

Dependencies:
- PR35: Intelligence Boundary Charter (v0.4 immutability)
- PR36: Intelligence Input Contract Charter (allowlist)
- PR37: Intelligence Input Contract Compliance Guard
- PR38: Intelligence Decision Record Charter (structure)
- PR39: Intelligence Decision Record Compliance Guard
"""

from datetime import datetime, timezone
from typing import Dict, Any, List


# PR36: Allowed input keys (subset relevant for v1)
ALLOWED_INPUT_KEYS = {
    # Category A: Market/State
    "price", "volume", "spread", "volatility",
    "ma_short", "ma_long", "orderbook_depth",
    "position_size", "equity", "balance",
    "timestamp", "tick_count", "entropy_bp",
    "timestamp_utc",  # For decision_generated_at

    # Category B: Intent/Regime
    "intent_primary", "intent_reason",
    "regime", "base_action", "overlay_rule",
    "decision_reason",

    # Category C: v0.4 Confidence Snapshot (READ-ONLY)
    "confidence_reason",
    "confidence_reason_version",
    "confidence_reason_generated_at",
    "confidence_value",
}

# PR39: Prohibited outcome vocabulary (avoid in decision_reason)
PROHIBITED_OUTCOME_VOCABULARY = {
    "outcome", "result", "profit", "loss", "pnl",
    "success", "failure", "win", "lose",
    "correct", "incorrect", "right", "wrong",
}


def _validate_allowlist_compliance(row_dict: Dict[str, Any]) -> List[str]:
    """
    Validate that row_dict keys are in PR36 allowlist.

    Returns list of warnings (empty if compliant).
    Never raises exceptions.
    """
    warnings = []

    for key in row_dict.keys():
        if key not in ALLOWED_INPUT_KEYS:
            warnings.append(
                f"PR36 Input Contract violation: undeclared input key '{key}' "
                f"(not in allowlist)"
            )

    return warnings


def _build_decision_reason_v1(
    base_action: str,
    intent_primary: str,
    regime: str,
    has_confidence: bool
) -> str:
    """
    Build decision_reason for v1 (mirror-base-action).

    Requirements (PR38, PR39):
    - Non-numeric (no digits)
    - Non-evaluative (no good/bad, high/low)
    - No outcome vocabulary (no profit/loss/correct/wrong)
    - Can reference v0.4 READ-ONLY

    Returns human-readable explanation string.
    Never raises exceptions.
    """
    # Base template (non-numeric, non-evaluative)
    reason_parts = []

    # Acknowledge mirroring
    reason_parts.append("Mirrored base action from deterministic core")

    # Add context (if available)
    if intent_primary:
        reason_parts.append(f"intent context captured ({intent_primary})")

    if regime:
        reason_parts.append(f"regime context captured ({regime})")

    # Acknowledge confidence (READ-ONLY reference, no version number to avoid digits)
    if has_confidence:
        reason_parts.append("confidence snapshot referenced read-only")

    # Join with periods
    decision_reason = ". ".join(reason_parts) + "."

    return decision_reason


def generate_decision_record_v1(row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    PR40: Generate v0.5 decision record (mirror-base-action).

    Algorithm:
    1. Read base_action from row_dict (v0.2 deterministic action)
    2. Mirror it to decision_action (exact copy)
    3. Build decision_reason (non-numeric, non-evaluative, no outcome vocab)
    4. Collect decision_inputs (keys actually read from allowlist)
    5. Generate decision record (PR38 structure)

    Args:
        row_dict: Input state dictionary (PR36 allowlist compliant)

    Returns:
        Decision record dictionary with PR38 required fields:
        - decision_action (str)
        - decision_reason (str)
        - decision_inputs (list[str])
        - decision_version (str, fixed "v0.5")
        - decision_generated_at (str, UTC ISO-8601)
        - _warnings (list[str], optional, for internal tracking)

    Properties:
    - READ-ONLY: Never modifies row_dict
    - Warning-only: Never raises exceptions
    - Returns valid decision record even if input is incomplete

    Dependencies:
    - PR38: Decision Record structure
    - PR36: Input allowlist compliance
    - PR39: No post-hoc rationalization vocabulary
    """
    warnings = []
    decision_inputs_used = []

    # Validate allowlist compliance (PR36, PR37)
    allowlist_warnings = _validate_allowlist_compliance(row_dict)
    warnings.extend(allowlist_warnings)

    # Read base_action (required for mirroring)
    base_action = row_dict.get("base_action", "")
    if "base_action" in row_dict:
        decision_inputs_used.append("base_action")

    # Mirror base_action to decision_action
    if not base_action or not isinstance(base_action, str):
        # Missing or invalid base_action
        decision_action = "UNKNOWN"
        warnings.append(
            "PR40 mirror warning: base_action missing or invalid, "
            "defaulting decision_action to 'UNKNOWN'"
        )
    else:
        # Exact mirror (no transformation)
        decision_action = base_action

    # Read optional context fields (for decision_reason)
    intent_primary = row_dict.get("intent_primary", "")
    if "intent_primary" in row_dict and intent_primary:
        decision_inputs_used.append("intent_primary")

    regime = row_dict.get("regime", "")
    if "regime" in row_dict and regime:
        decision_inputs_used.append("regime")

    # Read v0.4 confidence snapshot (READ-ONLY reference)
    confidence_reason = row_dict.get("confidence_reason", "")
    confidence_version = row_dict.get("confidence_reason_version", "")
    has_confidence = bool(confidence_reason or confidence_version)

    if "confidence_reason" in row_dict:
        decision_inputs_used.append("confidence_reason")
    if "confidence_reason_version" in row_dict:
        decision_inputs_used.append("confidence_reason_version")
    if "confidence_reason_generated_at" in row_dict:
        decision_inputs_used.append("confidence_reason_generated_at")

    # Build decision_reason (PR38, PR39 compliant)
    decision_reason = _build_decision_reason_v1(
        base_action=decision_action,
        intent_primary=intent_primary,
        regime=regime,
        has_confidence=has_confidence
    )

    # Generate timestamp (UTC ISO-8601)
    # Prefer row_dict timestamp_utc if available, else now
    if "timestamp_utc" in row_dict and row_dict["timestamp_utc"]:
        decision_generated_at = row_dict["timestamp_utc"]
        decision_inputs_used.append("timestamp_utc")
    else:
        decision_generated_at = datetime.now(timezone.utc).isoformat()

    # Assemble PR38-compliant decision record
    decision_record = {
        "decision_action": decision_action,
        "decision_reason": decision_reason,
        "decision_inputs": sorted(set(decision_inputs_used)),  # Unique, sorted
        "decision_version": "v0.5",
        "decision_generated_at": decision_generated_at,
    }

    # Add warnings if any (for internal tracking, not part of PR38 spec)
    if warnings:
        decision_record["_warnings"] = warnings

    return decision_record
