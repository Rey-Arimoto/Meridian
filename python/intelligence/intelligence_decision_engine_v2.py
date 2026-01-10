#!/usr/bin/env python3
"""
PR42: v0.5 Intelligence Decision Engine v2 (Rule Overlay / Regime-Aware)

Purpose: Overlay-based decision engine with regime-aware rule application.

Evolution from v1:
- v1: Mirrors base_action (simple copy)
- v2: Applies overlay rules based on regime and intent context

Design:
- Base: Starts with base_action
- Overlay: Applies regime-aware and intent-aware rules
- Final: Produces final_action with explanation
- READ-ONLY: Never modifies input or v0.2 execution

Non-Goals:
- No learning, optimization, or model
- No numeric scores or probabilities
- No v0.4 confidence evaluation or featurization

Dependencies:
- PR35: Intelligence Boundary Charter
- PR36: Intelligence Input Contract Charter
- PR38: Intelligence Decision Record Charter
- PR39: Intelligence Decision Record Compliance Guard
- PR40: Intelligence Decision Engine v1 (foundation)
- PR41/PR41A: Decision Record Wiring
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple


# PR36: Allowed input keys (extending from v1)
ALLOWED_INPUT_KEYS = {
    # Category A: Market/State
    "price", "volume", "spread", "volatility",
    "ma_short", "ma_long", "orderbook_depth",
    "position_size", "equity", "balance",
    "timestamp", "tick_count", "entropy_bp",
    "timestamp_utc",

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

# PR42: Ruleset definitions
RULESET_HALTED_REGIMES = [
    "REGIME_TRANSITION",
    "volatile_noise",
]

RULESET_CAUTIOUS_INTENTS = [
    "STABILIZE",
    "DEFEND",
    "PAUSE",
]

# PR42: Action suppression mapping (cautious ruleset)
ACTION_SUPPRESSION = {
    "SHIFT": "HOLD",  # Suppress position changes to hold
    "BUY": "HOLD",    # Suppress buying to hold
    "SELL": "HOLD",   # Suppress selling to hold
}


def _determine_ruleset(
    regime: str,
    intent_primary: str
) -> Tuple[str, str]:
    """
    Determine which overlay ruleset to apply based on regime and intent.

    Returns: (ruleset_name, ruleset_reason)

    Rulesets (priority order):
    1. halted: Critical regimes (REGIME_TRANSITION, volatile_noise)
    2. cautious: Conservative intents (STABILIZE, DEFEND, PAUSE)
    3. default: Normal operation

    Never raises exceptions.
    """
    # Priority 1: Halted (regime-driven safety)
    if regime in RULESET_HALTED_REGIMES:
        return ("halted", f"regime {regime} requires halt")

    # Priority 2: Cautious (intent-driven conservatism)
    if intent_primary in RULESET_CAUTIOUS_INTENTS:
        return ("cautious", f"intent {intent_primary} requires caution")

    # Priority 3: Default (pass-through)
    return ("default", "normal operation")


def _apply_overlay(
    base_action: str,
    ruleset_name: str,
    regime: str,
    intent_primary: str
) -> Tuple[str, str]:
    """
    Apply overlay rules to base_action based on ruleset.

    Returns: (final_action, application_reason)

    Overlay Logic:
    - halted: Force PAUSE (safety override)
    - cautious: Suppress aggressive actions to HOLD
    - default: Pass through base_action

    Never raises exceptions.
    """
    if ruleset_name == "halted":
        # Override to PAUSE (safety-first)
        return ("PAUSE", "safety override applied")

    elif ruleset_name == "cautious":
        # Suppress aggressive actions
        if base_action in ACTION_SUPPRESSION:
            suppressed_action = ACTION_SUPPRESSION[base_action]
            return (suppressed_action, f"suppressed {base_action} to {suppressed_action}")
        else:
            # Base action already conservative, pass through
            return (base_action, "base action maintained")

    else:  # default
        # Pass through base_action unchanged (like v1)
        return (base_action, "base action passed through")


def _build_decision_reason_v2(
    base_action: str,
    final_action: str,
    ruleset_name: str,
    ruleset_reason: str,
    application_reason: str,
    regime: str,
    intent_primary: str,
    has_confidence: bool
) -> str:
    """
    Build decision_reason for v2 (overlay-based).

    Requirements (PR38, PR39):
    - Non-numeric (no digits)
    - Non-evaluative (no good/bad, high/low)
    - No outcome vocabulary (no profit/loss/correct/wrong)
    - Can reference v0.4 READ-ONLY

    Returns human-readable explanation string.
    Never raises exceptions.
    """
    reason_parts = []

    # Base decision context
    if base_action:
        reason_parts.append(f"Base action from deterministic core ({base_action})")

    # Ruleset selection
    reason_parts.append(f"Overlay ruleset selected ({ruleset_name})")

    # Rule application
    if final_action != base_action:
        reason_parts.append(f"Rule applied: {application_reason}")
    else:
        reason_parts.append("Base action maintained by overlay")

    # Context (regime and intent)
    if regime:
        reason_parts.append(f"regime context ({regime})")

    if intent_primary:
        reason_parts.append(f"intent context ({intent_primary})")

    # Acknowledge v0.4 (READ-ONLY reference, no evaluation)
    if has_confidence:
        reason_parts.append("confidence snapshot referenced read-only")

    # Join with periods
    decision_reason = ". ".join(reason_parts) + "."

    return decision_reason


def generate_decision_record_v2(row_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    PR42: Generate v0.5 decision record (overlay-based).

    Algorithm:
    1. Read base_action (v0.2 deterministic)
    2. Determine overlay ruleset (regime-aware, intent-aware)
    3. Apply overlay to compute final_action
    4. Build decision_reason (non-numeric, non-evaluative, no outcome vocab)
    5. Generate decision record (PR38 structure)

    Args:
        row_dict: Input state dictionary (PR36 allowlist compliant)

    Returns:
        Decision record dictionary with PR38 required fields:
        - decision_action (str): Final action after overlay
        - decision_reason (str): Non-numeric, non-evaluative explanation
        - decision_inputs (list[str]): Keys actually used
        - decision_version (str): Fixed "v0.5"
        - decision_generated_at (str): UTC ISO-8601
        - _warnings (list[str], optional): Internal tracking

    Properties:
    - READ-ONLY: Never modifies row_dict
    - Warning-only: Never raises exceptions
    - Returns valid decision record even if input incomplete

    Dependencies:
    - PR38: Decision Record structure
    - PR36: Input allowlist compliance
    - PR39: No post-hoc rationalization vocabulary
    - PR40: Foundation (v1 as baseline)
    """
    warnings = []
    decision_inputs_used = []

    # Step 1: Read base_action
    base_action = row_dict.get("base_action", "")
    if "base_action" in row_dict:
        decision_inputs_used.append("base_action")

    if not base_action or not isinstance(base_action, str):
        # Missing or invalid base_action
        base_action = "UNKNOWN"
        warnings.append(
            "PR42 warning: base_action missing or invalid, "
            "defaulting to 'UNKNOWN'"
        )

    # Read context fields for overlay
    regime = row_dict.get("regime", "")
    if "regime" in row_dict and regime:
        decision_inputs_used.append("regime")

    intent_primary = row_dict.get("intent_primary", "")
    if "intent_primary" in row_dict and intent_primary:
        decision_inputs_used.append("intent_primary")

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

    # Step 2: Determine overlay ruleset (regime-aware, intent-aware)
    ruleset_name, ruleset_reason = _determine_ruleset(regime, intent_primary)

    # Step 3: Apply overlay to compute final_action
    final_action, application_reason = _apply_overlay(
        base_action, ruleset_name, regime, intent_primary
    )

    # Step 4: Build decision_reason (PR38, PR39 compliant)
    decision_reason = _build_decision_reason_v2(
        base_action=base_action,
        final_action=final_action,
        ruleset_name=ruleset_name,
        ruleset_reason=ruleset_reason,
        application_reason=application_reason,
        regime=regime,
        intent_primary=intent_primary,
        has_confidence=has_confidence
    )

    # Generate timestamp (UTC ISO-8601)
    if "timestamp_utc" in row_dict and row_dict["timestamp_utc"]:
        decision_generated_at = row_dict["timestamp_utc"]
        decision_inputs_used.append("timestamp_utc")
    else:
        decision_generated_at = datetime.now(timezone.utc).isoformat()

    # Step 5: Assemble PR38-compliant decision record
    decision_record = {
        "decision_action": final_action,
        "decision_reason": decision_reason,
        "decision_inputs": sorted(set(decision_inputs_used)),  # Unique, sorted
        "decision_version": "v0.5",
        "decision_generated_at": decision_generated_at,
    }

    # Add warnings if any (for internal tracking)
    if warnings:
        decision_record["_warnings"] = warnings

    return decision_record
