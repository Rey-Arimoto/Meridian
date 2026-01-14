#!/usr/bin/env python3
"""
PR149: v1.4 Shock Phase Detection Engine v1 (READ-ONLY)

Purpose:
    Detect shock phase from observation labels using fixed rules.
    Input: artifact bundle + pair_ref
    Output: label-only shock phase record

Rules (Priority, first-match-wins):
    1. Invalid input → PHASE_ERROR
    2. Observation labels missing → PHASE_UNKNOWN
    3. PRE_SHOCK: liquidity_thinning + (impulse_up or impulse_down) + flow_dominance != unknown
    4. DOWN_SHOCK: impulse_down + (bid_absorption or agg_sell_dominance)
    5. UP_SHOCK: impulse_up + (ask_absorption or agg_buy_dominance)
    6. DOWN_REVERSAL: prev in {DOWN_SHOCK, PRE_SHOCK} + impulse_up + agg_buy_dominance
    7. UP_REVERSAL: prev in {UP_SHOCK, PRE_SHOCK} + impulse_down + agg_sell_dominance
    8. RECOVERY: prev in {UP_REVERSAL, DOWN_REVERSAL, UP_SHOCK, DOWN_SHOCK} + impulse_flat + no_absorption
    9. NORMAL: impulse present but no rule

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Non-prescriptive: No should/must/recommend/advise
    - Label-only output: No numeric values in text
    - Defensive: Invalid input → valid ERROR record
    - Warning-only: Never raises exceptions
"""

from typing import Any, Dict, List, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shock.v14_shock_phase_schema import (
    V14ShockPhaseSchema,
    SHOCK_VERSION_V1,
    SHOCK_STATUS_AVAILABLE,
    SHOCK_STATUS_UNKNOWN,
    SHOCK_STATUS_ERROR,
    SHOCK_SOURCE_AUTO,
    SHOCK_SOURCE_UNKNOWN,
    PHASE_UNKNOWN,
    PHASE_NORMAL,
    PHASE_PRE_SHOCK,
    PHASE_UP_SHOCK,
    PHASE_DOWN_SHOCK,
    PHASE_UP_REVERSAL,
    PHASE_DOWN_REVERSAL,
    PHASE_RECOVERY,
    PHASE_ERROR,
    DIRECTION_UP,
    DIRECTION_DOWN,
    DIRECTION_NONE,
    DIRECTION_UNKNOWN,
    IMPULSE_UP,
    IMPULSE_DOWN,
    IMPULSE_FLAT,
    IMPULSE_UNKNOWN,
    ASK_ABSORPTION,
    BID_ABSORPTION,
    NO_ABSORPTION,
    ABSORPTION_UNKNOWN,
    AGG_BUY_DOMINANCE,
    AGG_SELL_DOMINANCE,
    FLOW_BALANCED,
    FLOW_UNKNOWN,
    LIQUIDITY_THINNING,
    LIQUIDITY_OK,
    LIQUIDITY_UNKNOWN,
)


def _extract_observation_labels_from_bundle(
    artifact_bundle: Dict[str, Any],
    pair_ref: str,
) -> Tuple[Dict[str, str], List[str]]:
    """
    Extract observation labels from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle
        pair_ref: Pair reference

    Returns:
        Tuple of (observation_labels, warnings)
    """
    warnings = []
    observation_labels = {}

    # Try to get observations from bundle
    artifacts = artifact_bundle.get("artifacts", {})
    observations = artifacts.get("observations", {})

    if not observations:
        warnings.append("no observations found in bundle")
        return (observation_labels, warnings)

    # Try to get observations for this pair_ref
    pair_observations = observations.get(pair_ref, {})

    if not pair_observations:
        warnings.append(f"no observations found for pair_ref: {pair_ref}")
        return (observation_labels, warnings)

    # Extract observation labels
    observation_labels["price_impulse_label"] = pair_observations.get("price_impulse_label", IMPULSE_UNKNOWN)
    observation_labels["absorption_label"] = pair_observations.get("absorption_label", ABSORPTION_UNKNOWN)
    observation_labels["flow_dominance_label"] = pair_observations.get("flow_dominance_label", FLOW_UNKNOWN)
    observation_labels["liquidity_thinning_label"] = pair_observations.get("liquidity_thinning_label", LIQUIDITY_UNKNOWN)

    # Extract state memory (optional)
    shock_state_memory = pair_observations.get("shock_state_memory", {})
    observation_labels["prev_phase"] = shock_state_memory.get("prev_phase", None)
    observation_labels["prev_phase_age_label"] = shock_state_memory.get("prev_phase_age_label", None)

    return (observation_labels, warnings)


def _determine_phase_direction(phase_label: str) -> str:
    """
    Determine phase direction from phase label.

    Args:
        phase_label: Phase label

    Returns:
        Phase direction (UP/DOWN/NONE/UNKNOWN)
    """
    if phase_label in [PHASE_UP_SHOCK, PHASE_UP_REVERSAL]:
        return DIRECTION_UP
    elif phase_label in [PHASE_DOWN_SHOCK, PHASE_DOWN_REVERSAL]:
        return DIRECTION_DOWN
    elif phase_label in [PHASE_PRE_SHOCK, PHASE_NORMAL, PHASE_RECOVERY]:
        return DIRECTION_NONE
    else:
        return DIRECTION_UNKNOWN


def _detect_shock_phase_from_labels(
    observation_labels: Dict[str, str],
    prev_phase: Optional[str] = None,
) -> Tuple[str, List[str]]:
    """
    Detect shock phase from observation labels using fixed rules.

    Args:
        observation_labels: Dict of observation labels
        prev_phase: Previous phase (optional)

    Returns:
        Tuple of (phase_label, basis_labels)
    """
    # Extract labels
    price_impulse = observation_labels.get("price_impulse_label", IMPULSE_UNKNOWN)
    absorption = observation_labels.get("absorption_label", ABSORPTION_UNKNOWN)
    flow_dominance = observation_labels.get("flow_dominance_label", FLOW_UNKNOWN)
    liquidity_thinning = observation_labels.get("liquidity_thinning_label", LIQUIDITY_UNKNOWN)

    # Use prev_phase from observation_labels if not provided
    if prev_phase is None:
        prev_phase = observation_labels.get("prev_phase", None)

    # Rule 1: Missing critical observations → UNKNOWN
    if price_impulse == IMPULSE_UNKNOWN:
        return (PHASE_UNKNOWN, ["BASIS_MISSING_IMPULSE"])

    # Rule 2: PRE_SHOCK (liquidity_thinning + impulse + flow_dominance != unknown)
    if liquidity_thinning == LIQUIDITY_THINNING:
        if price_impulse in [IMPULSE_UP, IMPULSE_DOWN] and flow_dominance != FLOW_UNKNOWN:
            return (PHASE_PRE_SHOCK, ["BASIS_LIQUIDITY_THINNING", f"BASIS_IMPULSE_{price_impulse}"])

    # Rule 3: DOWN_REVERSAL (prev in {DOWN_SHOCK, PRE_SHOCK} + impulse_up + agg_buy_dominance)
    # Check REVERSAL before SHOCK (REVERSAL is more specific)
    if prev_phase in [PHASE_DOWN_SHOCK, PHASE_PRE_SHOCK]:
        if price_impulse == IMPULSE_UP and flow_dominance == AGG_BUY_DOMINANCE:
            return (PHASE_DOWN_REVERSAL, ["BASIS_PREV_DOWN_SHOCK", "BASIS_IMPULSE_UP", "BASIS_AGG_BUY_DOMINANCE"])

    # Rule 4: UP_REVERSAL (prev in {UP_SHOCK, PRE_SHOCK} + impulse_down + agg_sell_dominance)
    if prev_phase in [PHASE_UP_SHOCK, PHASE_PRE_SHOCK]:
        if price_impulse == IMPULSE_DOWN and flow_dominance == AGG_SELL_DOMINANCE:
            return (PHASE_UP_REVERSAL, ["BASIS_PREV_UP_SHOCK", "BASIS_IMPULSE_DOWN", "BASIS_AGG_SELL_DOMINANCE"])

    # Rule 5: DOWN_SHOCK (impulse_down + (bid_absorption or agg_sell_dominance))
    if price_impulse == IMPULSE_DOWN:
        if absorption == BID_ABSORPTION or flow_dominance == AGG_SELL_DOMINANCE:
            basis = ["BASIS_IMPULSE_DOWN"]
            if absorption == BID_ABSORPTION:
                basis.append("BASIS_BID_ABSORPTION")
            if flow_dominance == AGG_SELL_DOMINANCE:
                basis.append("BASIS_AGG_SELL_DOMINANCE")
            return (PHASE_DOWN_SHOCK, basis)

    # Rule 6: UP_SHOCK (impulse_up + (ask_absorption or agg_buy_dominance))
    if price_impulse == IMPULSE_UP:
        if absorption == ASK_ABSORPTION or flow_dominance == AGG_BUY_DOMINANCE:
            basis = ["BASIS_IMPULSE_UP"]
            if absorption == ASK_ABSORPTION:
                basis.append("BASIS_ASK_ABSORPTION")
            if flow_dominance == AGG_BUY_DOMINANCE:
                basis.append("BASIS_AGG_BUY_DOMINANCE")
            return (PHASE_UP_SHOCK, basis)

    # Rule 7: RECOVERY (prev in {UP_REVERSAL, DOWN_REVERSAL, UP_SHOCK, DOWN_SHOCK} + impulse_flat + no_absorption)
    if prev_phase in [PHASE_UP_REVERSAL, PHASE_DOWN_REVERSAL, PHASE_UP_SHOCK, PHASE_DOWN_SHOCK]:
        if price_impulse == IMPULSE_FLAT and absorption == NO_ABSORPTION:
            return (PHASE_RECOVERY, ["BASIS_PREV_REVERSAL_OR_SHOCK", "BASIS_IMPULSE_FLAT", "BASIS_NO_ABSORPTION"])

    # Rule 8: NORMAL (impulse present but no rule matches)
    if price_impulse != IMPULSE_UNKNOWN:
        return (PHASE_NORMAL, ["BASIS_IMPULSE_PRESENT", "BASIS_NO_SHOCK_PATTERN"])

    # Fallback: UNKNOWN
    return (PHASE_UNKNOWN, ["BASIS_DEFAULT_UNKNOWN"])


def detect_shock_phase_from_bundle_v1(
    artifact_bundle: Optional[Dict[str, Any]],
    pair_ref: str,
    source: str = SHOCK_SOURCE_AUTO,
    profile_ref: str = "ALERT_ONLY",
) -> Dict[str, Any]:
    """
    Detect shock phase from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle with observations
        pair_ref: Pair reference (e.g., "deep:wBTC/USDC")
        source: Source (AUTO/DEEP/CETUS/MIXED/UNKNOWN)
        profile_ref: Observation profile reference

    Returns:
        Dict with:
        - shock_record: PR149-compliant shock phase record
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid artifact_bundle
    if artifact_bundle is None or not isinstance(artifact_bundle, dict):
        warnings.append("invalid artifact_bundle (expected dict, got None or non-dict)")
        error_record = V14ShockPhaseSchema.create_error_record(
            pair_ref=pair_ref,
            warnings=warnings,
        )
        return {
            "shock_record": error_record,
            "warnings": warnings,
        }

    # Defensive: Handle invalid pair_ref
    if not pair_ref or not isinstance(pair_ref, str):
        warnings.append("invalid pair_ref (expected non-empty string)")
        error_record = V14ShockPhaseSchema.create_error_record(
            pair_ref="",
            warnings=warnings,
        )
        return {
            "shock_record": error_record,
            "warnings": warnings,
        }

    # Extract observation labels
    observation_labels, extraction_warnings = _extract_observation_labels_from_bundle(artifact_bundle, pair_ref)
    warnings.extend(extraction_warnings)

    # Track observation presence
    observation_presence = {
        "price_impulse": observation_labels.get("price_impulse_label", IMPULSE_UNKNOWN) != IMPULSE_UNKNOWN,
        "absorption": observation_labels.get("absorption_label", ABSORPTION_UNKNOWN) != ABSORPTION_UNKNOWN,
        "flow_dominance": observation_labels.get("flow_dominance_label", FLOW_UNKNOWN) != FLOW_UNKNOWN,
        "liquidity_thinning": observation_labels.get("liquidity_thinning_label", LIQUIDITY_UNKNOWN) != LIQUIDITY_UNKNOWN,
        "prev_phase": observation_labels.get("prev_phase") is not None,
    }

    # Check if we have minimum observations
    if not observation_presence["price_impulse"]:
        warnings.append("missing critical observation: price_impulse_label")
        shock_record = V14ShockPhaseSchema.create_shock_record(
            status=SHOCK_STATUS_UNKNOWN,
            pair_ref=pair_ref,
            source=source,
            profile_ref=profile_ref,
            phase_label=PHASE_UNKNOWN,
            phase_direction=DIRECTION_UNKNOWN,
            basis_labels=["BASIS_MISSING_IMPULSE"],
            observation_presence=observation_presence,
            warnings=warnings,
        )
        return {
            "shock_record": shock_record,
            "warnings": warnings,
        }

    # Detect phase
    phase_label, basis_labels = _detect_shock_phase_from_labels(observation_labels)

    # Determine direction
    phase_direction = _determine_phase_direction(phase_label)

    # Create shock record
    shock_record = V14ShockPhaseSchema.create_shock_record(
        version=SHOCK_VERSION_V1,
        status=SHOCK_STATUS_AVAILABLE,
        pair_ref=pair_ref,
        source=source,
        profile_ref=profile_ref,
        phase_label=phase_label,
        phase_direction=phase_direction,
        basis_labels=basis_labels,
        observation_presence=observation_presence,
        warnings=warnings,
    )

    # Validate schema
    schema_errors = V14ShockPhaseSchema.validate_shock_record(shock_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    return {
        "shock_record": shock_record,
        "warnings": warnings,
    }


def get_shock_phase_engine_v1_info() -> Dict[str, Any]:
    """
    Get shock phase engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "shock_phase_detection",
        "philosophy": "Shock Phase = Structural phase label (not instruction, not prediction). Fixed rule detection from observation labels.",
        "input_format": "Artifact bundle + pair_ref",
        "output_format": "shock_phase_record (PR149)",
        "rule_priority": [
            "1. Invalid input → PHASE_ERROR",
            "2. Observation labels missing → PHASE_UNKNOWN",
            "3. PRE_SHOCK: liquidity_thinning + impulse + flow_dominance",
            "4. DOWN_SHOCK: impulse_down + (bid_absorption or agg_sell_dominance)",
            "5. UP_SHOCK: impulse_up + (ask_absorption or agg_buy_dominance)",
            "6. DOWN_REVERSAL: prev down + impulse_up + agg_buy",
            "7. UP_REVERSAL: prev up + impulse_down + agg_sell",
            "8. RECOVERY: prev reversal/shock + impulse_flat + no_absorption",
            "9. NORMAL: impulse present but no rule",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "label_output_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Shock Phase Engine - Self Test")
    print("=" * 60)
    print()

    # Test 1: PRE_SHOCK detection
    print("Test 1: PRE_SHOCK detection")
    bundle1 = {
        "artifacts": {
            "observations": {
                "deep:wBTC/USDC": {
                    "price_impulse_label": IMPULSE_UP,
                    "absorption_label": NO_ABSORPTION,
                    "flow_dominance_label": AGG_BUY_DOMINANCE,
                    "liquidity_thinning_label": LIQUIDITY_THINNING,
                }
            }
        }
    }
    result1 = detect_shock_phase_from_bundle_v1(bundle1, "deep:wBTC/USDC")
    print(f"Phase: {result1['shock_record']['v14_shock_phase_label']}")
    print(f"Direction: {result1['shock_record']['v14_shock_phase_direction']}")
    print()

    # Test 2: DOWN_SHOCK detection
    print("Test 2: DOWN_SHOCK detection")
    bundle2 = {
        "artifacts": {
            "observations": {
                "deep:wBTC/USDC": {
                    "price_impulse_label": IMPULSE_DOWN,
                    "absorption_label": BID_ABSORPTION,
                    "flow_dominance_label": AGG_SELL_DOMINANCE,
                    "liquidity_thinning_label": LIQUIDITY_OK,
                }
            }
        }
    }
    result2 = detect_shock_phase_from_bundle_v1(bundle2, "deep:wBTC/USDC")
    print(f"Phase: {result2['shock_record']['v14_shock_phase_label']}")
    print(f"Direction: {result2['shock_record']['v14_shock_phase_direction']}")
    print()

    # Test 3: NORMAL fallback
    print("Test 3: NORMAL fallback")
    bundle3 = {
        "artifacts": {
            "observations": {
                "deep:wBTC/USDC": {
                    "price_impulse_label": IMPULSE_FLAT,
                    "absorption_label": NO_ABSORPTION,
                    "flow_dominance_label": FLOW_BALANCED,
                    "liquidity_thinning_label": LIQUIDITY_OK,
                }
            }
        }
    }
    result3 = detect_shock_phase_from_bundle_v1(bundle3, "deep:wBTC/USDC")
    print(f"Phase: {result3['shock_record']['v14_shock_phase_label']}")
    print()

    # Test 4: Invalid bundle (defensive)
    print("Test 4: Invalid bundle (defensive)")
    result4 = detect_shock_phase_from_bundle_v1(None, "deep:wBTC/USDC")
    print(f"Status: {result4['shock_record']['v14_shock_status']}")
    print(f"Phase: {result4['shock_record']['v14_shock_phase_label']}")
    print(f"Warnings: {len(result4['warnings'])}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
