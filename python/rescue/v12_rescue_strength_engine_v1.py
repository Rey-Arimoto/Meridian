#!/usr/bin/env python3
"""
PR136: v1.2 Rescue Strength Classification Engine v1 (READ-ONLY)

Purpose:
    Classify rescue strength for rescue relation assessment.
    Static deterministic first-match-wins classification.

Classification Rules (First-match-wins):
    0. Invalid inputs → RESCUE_NONE (defensive)
    1. REGIME_CRITICAL → RESCUE_NONE
    2. INELIGIBLE → RESCUE_NONE
    3. EDGE_LEAK → RESCUE_NONE
    3.5. ELIGIBLE_DRY_RUN_ONLY → cap at WEAK
    4. RESCUE_STRONG (strict):
       - REGIME_MEDIUM + EDGE_SHIELD + STABILITY/HEDGE + D1/D4/D5
       - constraint_binding contains "ALLOW_RESCUE_STRONG"
       - eligibility != INELIGIBLE and != ELIGIBLE_DRY_RUN_ONLY
       - NEVER for VOLATILITY_ROLE or EDGE_AMPLIFY
    5. RESCUE_MEDIUM:
       - REGIME_MEDIUM + SHIELD/NEUTRAL + STABILITY/HEDGE/LIQUIDITY
    6. RESCUE_WEAK:
       - REGIME_HIGH/LOW + EDGE_SHIELD
    7. Default → RESCUE_NONE

Rescue Strength ≠ Action
Rescue Strength = Structural label propagation
"""

from typing import Any, Dict, List, Optional

from .v12_rescue_strength_schema import (
    V12RescueStrengthSchema,
    RESCUE_NONE,
    RESCUE_WEAK,
    RESCUE_MEDIUM,
    RESCUE_STRONG,
)


def _safe_get(d: Optional[Dict[str, Any]], key: str, default: Any = None) -> Any:
    """
    Safely get value from dict.

    Args:
        d: Dictionary (may be None)
        key: Key to get
        default: Default value if not found

    Returns:
        Value or default
    """
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def classify_rescue_strength_v1(
    regime_record: Optional[Dict[str, Any]] = None,
    role_record: Optional[Dict[str, Any]] = None,
    distortion_record: Optional[Dict[str, Any]] = None,
    edge_record: Optional[Dict[str, Any]] = None,
    eligibility_record: Optional[Dict[str, Any]] = None,
    contribution_record: Optional[Dict[str, Any]] = None,
    constraint_binding_record: Optional[Dict[str, Any]] = None,
    trajectory_record: Optional[Dict[str, Any]] = None,
    boundary_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classify rescue strength for rescue relation assessment.

    Args:
        regime_record: PR110 regime record
        role_record: PR130 role qualification record
        distortion_record: PR129 distortion record
        edge_record: PR135 edge type record (optional)
        eligibility_record: PR128 eligibility record (optional)
        contribution_record: PR131 contribution record (optional)
        constraint_binding_record: PR132 constraint binding record (optional)
        trajectory_record: PR127 trajectory record (optional)
        boundary_record: Boundary record (optional)

    Returns:
        Rescue strength record (always AVAILABLE, defensive fallback to RESCUE_NONE)
    """
    try:
        basis = []

        # Extract inputs
        regime_level = _safe_get(regime_record, "v11_regime_level", "UNCLASSIFIED")
        if regime_record:
            basis.append("v11_regime_level")

        role_type = _safe_get(role_record, "v12_role_carrier_role_type", "UNCLASSIFIED")
        if role_record:
            basis.append("v12_role_carrier_role_type")

        distortion_type = _safe_get(distortion_record, "v12_distortion_type", "UNCLASSIFIED")
        if distortion_record:
            basis.append("v12_distortion_type")

        edge_type = _safe_get(edge_record, "v12_edge_type", "EDGE_NONE")
        if edge_record:
            basis.append("v12_edge_type")

        eligibility_label = _safe_get(eligibility_record, "v12_eligibility_status", "UNKNOWN")
        if eligibility_record:
            basis.append("v12_eligibility_status")

        # Extract constraint binding labels
        constraint_labels = _safe_get(constraint_binding_record, "v12_contrib_constraint_labels", [])
        if constraint_binding_record:
            basis.append("v12_contrib_constraint_labels")

        # -----------------------------
        # Rule 0: Defensive (invalid inputs)
        # -----------------------------
        if regime_level == "UNCLASSIFIED" or role_type == "UNCLASSIFIED" or distortion_type == "UNCLASSIFIED":
            return V12RescueStrengthSchema.create_error_record(
                "invalid inputs: missing required fields.",
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
            )

        # -----------------------------
        # Rule 1: REGIME_CRITICAL → RESCUE_NONE
        # -----------------------------
        if regime_level == "REGIME_CRITICAL":
            return V12RescueStrengthSchema.create_rescue_strength_record(
                rescue_strength=RESCUE_NONE,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                edge_type=edge_type,
                eligibility_label=eligibility_label,
                basis=basis,
                warnings=["Rescue blocked: REGIME_CRITICAL."],
            )

        # -----------------------------
        # Rule 2: INELIGIBLE → RESCUE_NONE
        # -----------------------------
        if eligibility_label == "INELIGIBLE":
            return V12RescueStrengthSchema.create_rescue_strength_record(
                rescue_strength=RESCUE_NONE,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                edge_type=edge_type,
                eligibility_label=eligibility_label,
                basis=basis,
                warnings=["Rescue blocked: INELIGIBLE."],
            )

        # -----------------------------
        # Rule 3: EDGE_LEAK → RESCUE_NONE
        # -----------------------------
        if edge_type == "EDGE_LEAK":
            return V12RescueStrengthSchema.create_rescue_strength_record(
                rescue_strength=RESCUE_NONE,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                edge_type=edge_type,
                eligibility_label=eligibility_label,
                basis=basis,
                warnings=["Rescue blocked: EDGE_LEAK."],
            )

        # -----------------------------
        # Rule 3.5: ELIGIBLE_DRY_RUN_ONLY → cap at WEAK
        # -----------------------------
        if eligibility_label == "ELIGIBLE_DRY_RUN_ONLY":
            return V12RescueStrengthSchema.create_rescue_strength_record(
                rescue_strength=RESCUE_WEAK,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                edge_type=edge_type,
                eligibility_label=eligibility_label,
                basis=basis,
                warnings=["Rescue strength capped at WEAK: ELIGIBLE_DRY_RUN_ONLY."],
            )

        # -----------------------------
        # Rule 4: RESCUE_STRONG (strict conditions)
        # -----------------------------
        # STRONG requires:
        # - REGIME_MEDIUM
        # - EDGE_SHIELD
        # - role in {STABILITY_ROLE, HEDGE_ROLE}
        # - distortion in {D1_LIQUIDATION, D4_EVENT_DISTORTION, D5_CORRELATION_DISTORTION}
        # - constraint_binding contains "ALLOW_RESCUE_STRONG"
        # - eligibility != INELIGIBLE and != ELIGIBLE_DRY_RUN_ONLY
        # - NEVER for VOLATILITY_ROLE or EDGE_AMPLIFY

        if (
            regime_level == "REGIME_MEDIUM"
            and edge_type == "EDGE_SHIELD"
            and role_type in ["STABILITY_ROLE", "HEDGE_ROLE"]
            and distortion_type in ["D1_LIQUIDATION", "D4_EVENT_DISTORTION", "D5_CORRELATION_DISTORTION"]
            and "ALLOW_RESCUE_STRONG" in constraint_labels
            and eligibility_label != "INELIGIBLE"
            and eligibility_label != "ELIGIBLE_DRY_RUN_ONLY"
        ):
            return V12RescueStrengthSchema.create_rescue_strength_record(
                rescue_strength=RESCUE_STRONG,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                edge_type=edge_type,
                eligibility_label=eligibility_label,
                basis=basis,
            )

        # -----------------------------
        # Rule 5: RESCUE_MEDIUM
        # -----------------------------
        # MEDIUM: REGIME_MEDIUM + SHIELD/NEUTRAL + STABILITY/HEDGE/LIQUIDITY
        if (
            regime_level == "REGIME_MEDIUM"
            and edge_type in ["EDGE_SHIELD", "EDGE_NEUTRAL"]
            and role_type in ["STABILITY_ROLE", "HEDGE_ROLE", "LIQUIDITY_ROLE"]
        ):
            return V12RescueStrengthSchema.create_rescue_strength_record(
                rescue_strength=RESCUE_MEDIUM,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                edge_type=edge_type,
                eligibility_label=eligibility_label,
                basis=basis,
            )

        # -----------------------------
        # Rule 6: RESCUE_WEAK
        # -----------------------------
        # WEAK: REGIME_HIGH/LOW + EDGE_SHIELD
        if regime_level in ["REGIME_HIGH", "REGIME_LOW"] and edge_type == "EDGE_SHIELD":
            return V12RescueStrengthSchema.create_rescue_strength_record(
                rescue_strength=RESCUE_WEAK,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                edge_type=edge_type,
                eligibility_label=eligibility_label,
                basis=basis,
            )

        # -----------------------------
        # Rule 7: Default → RESCUE_NONE
        # -----------------------------
        return V12RescueStrengthSchema.create_rescue_strength_record(
            rescue_strength=RESCUE_NONE,
            regime_level=regime_level,
            role_type=role_type,
            distortion_type=distortion_type,
            edge_type=edge_type,
            eligibility_label=eligibility_label,
            basis=basis,
        )

    except Exception as e:
        # Defensive: never raise, return RESCUE_NONE with warning
        return V12RescueStrengthSchema.create_error_record(
            f"exception: {type(e).__name__}",
        )


def get_rescue_strength_engine_v1_info() -> Dict[str, Any]:
    """
    Get rescue strength engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "rescue_strength",
        "input_schema": "regime + role + distortion + edge + eligibility + constraint_binding (optional)",
        "output_schema": "v12_rescue",
        "classification_rules": [
            "invalid_inputs → RESCUE_NONE (defensive)",
            "REGIME_CRITICAL → RESCUE_NONE",
            "INELIGIBLE → RESCUE_NONE",
            "EDGE_LEAK → RESCUE_NONE",
            "ELIGIBLE_DRY_RUN_ONLY → cap at WEAK",
            "STRONG (strict): MEDIUM + SHIELD + STABILITY/HEDGE + D1/D4/D5 + ALLOW_RESCUE_STRONG",
            "MEDIUM: MEDIUM + SHIELD/NEUTRAL + STABILITY/HEDGE/LIQUIDITY",
            "WEAK: HIGH/LOW + SHIELD",
            "default → RESCUE_NONE",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_rescue_coupling",
            "deterministic",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Rescue Strength Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Defensive missing inputs → RESCUE_NONE
    print("Test 1: Defensive missing inputs → RESCUE_NONE")
    result1 = classify_rescue_strength_v1(
        regime_record={"v11_regime_level": "UNCLASSIFIED"},
    )
    print(f"Strength: {result1['v12_rescue_strength']}")
    print()

    # Test 2: CRITICAL → RESCUE_NONE
    print("Test 2: CRITICAL → RESCUE_NONE")
    result2 = classify_rescue_strength_v1(
        regime_record={"v11_regime_level": "REGIME_CRITICAL"},
        role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
        distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        edge_record={"v12_edge_type": "EDGE_SHIELD"},
    )
    print(f"Strength: {result2['v12_rescue_strength']}")
    print()

    # Test 3: STRONG (strict)
    print("Test 3: STRONG (strict)")
    result3 = classify_rescue_strength_v1(
        regime_record={"v11_regime_level": "REGIME_MEDIUM"},
        role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
        distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        edge_record={"v12_edge_type": "EDGE_SHIELD"},
        eligibility_record={"v12_eligibility_status": "ELIGIBLE_CONSIDERATION_ONLY"},
        constraint_binding_record={"v12_contrib_constraint_labels": ["ALLOW_RESCUE_STRONG"]},
    )
    print(f"Strength: {result3['v12_rescue_strength']}")
    print()

    # Test 4: MEDIUM
    print("Test 4: MEDIUM")
    result4 = classify_rescue_strength_v1(
        regime_record={"v11_regime_level": "REGIME_MEDIUM"},
        role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
        distortion_record={"v12_distortion_type": "D2_RANGE_STICKINESS"},
        edge_record={"v12_edge_type": "EDGE_SHIELD"},
        eligibility_record={"v12_eligibility_status": "ELIGIBLE_CONSIDERATION_ONLY"},
    )
    print(f"Strength: {result4['v12_rescue_strength']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
