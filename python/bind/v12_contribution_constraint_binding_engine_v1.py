#!/usr/bin/env python3
"""
PR132: v1.2 Contribution → Constraint Binding Engine v1 (READ-ONLY)

Purpose:
    Bind contribution model (PR131) to existing pipeline as non-prescriptive constraint labels.
    Static, deterministic, label-based only (no evaluation, no decision, no instruction).

Rules (first-match-wins):
    0. Invalid inputs → ERROR
    1. REGIME_CRITICAL → BLOCKED
    2. INELIGIBLE → BLOCKED
    3. SUPPRESSED (PR126) → BLOCKED
    4. REGIME_HIGH or REGIME_LOW → SECONDARY
    5. REGIME_MEDIUM × VOLATILITY × D1-D5 → PRIMARY
    6. Default → NONE

Binding ≠ Decision
Binding ≠ Instruction
Binding = Label propagation
"""

from typing import Any, Dict, List, Optional

from .v12_contribution_constraint_schema import (
    V12ContributionConstraintSchema,
    CONTRIB_ZONE_NONE,
    CONTRIB_ZONE_SECONDARY,
    CONTRIB_ZONE_PRIMARY,
    CONTRIB_ZONE_BLOCKED,
    CONSTRAINT_CONTRIB_BLOCKED_REGIME_CRITICAL,
    CONSTRAINT_CONTRIB_BLOCKED_INELIGIBLE,
    CONSTRAINT_CONTRIB_BLOCKED_SUPPRESSED,
    CONSTRAINT_CONTRIB_SECONDARY_REGIME_NON_MEDIUM,
    CONSTRAINT_CONTRIB_PRIMARY_MEDIUM_VOLATILITY_DISTORTION,
    CONSTRAINT_CONTRIB_NONE_DEFAULT,
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


def bind_contribution_constraints_v1(
    contribution_record: Optional[Dict[str, Any]] = None,
    regime_record: Optional[Dict[str, Any]] = None,
    role_record: Optional[Dict[str, Any]] = None,
    distortion_record: Optional[Dict[str, Any]] = None,
    eligibility_record: Optional[Dict[str, Any]] = None,
    permission_monitor_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Bind contribution model to constraint labels.

    Args:
        contribution_record: PR131 contribution record
        regime_record: PR110 regime record
        role_record: PR130 role qualification record
        distortion_record: PR129 distortion record
        eligibility_record: PR128 eligibility record
        permission_monitor_record: PR126 permission monitor record

    Returns:
        Constraint binding record (always valid, ERROR on failure)
    """
    try:
        basis = []

        # Extract contribution label (from PR131)
        contribution_label = _safe_get(contribution_record, "v12_contrib_contribution_label", "UNCLASSIFIED")
        if contribution_record:
            basis.append("v12_contrib_contribution_label")

        # Extract regime level (from PR110)
        regime_level = _safe_get(regime_record, "v11_regime_level", "UNCLASSIFIED")
        if regime_record:
            basis.append("v11_regime_level")

        # Extract role type (from PR130)
        role_type = _safe_get(role_record, "v12_role_carrier_role_type", "UNCLASSIFIED")
        if role_record:
            basis.append("v12_role_carrier_role_type")

        # Extract distortion type (from PR129)
        distortion_type = _safe_get(distortion_record, "v12_distortion_type", "UNCLASSIFIED")
        if distortion_record:
            basis.append("v12_distortion_type")

        # Extract eligibility label (from PR128)
        eligibility_label = _safe_get(eligibility_record, "v12_eligibility_status", "UNKNOWN")
        if eligibility_record:
            basis.append("v12_eligibility_status")

        # Extract suppression state (from PR126)
        suppression_state = _safe_get(permission_monitor_record, "v12_monitor_suppression_state", "UNKNOWN")
        if permission_monitor_record:
            basis.append("v12_monitor_suppression_state")

        # -----------------------------
        # Rule 0: Defensive (invalid inputs)
        # -----------------------------
        if regime_level == "UNCLASSIFIED":
            return V12ContributionConstraintSchema.create_error_record(
                "invalid inputs: regime_level must be classified."
            )

        # -----------------------------
        # Rule 1: REGIME_CRITICAL → BLOCKED
        # -----------------------------
        if regime_level == "REGIME_CRITICAL":
            return V12ContributionConstraintSchema.create_constraint_binding_record(
                zone_label=CONTRIB_ZONE_BLOCKED,
                constraint_labels=[CONSTRAINT_CONTRIB_BLOCKED_REGIME_CRITICAL],
                basis=basis,
                contribution_label=contribution_label if contribution_label != "UNCLASSIFIED" else None,
                regime_level=regime_level,
                role_type=role_type if role_type != "UNCLASSIFIED" else None,
                distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
            )

        # -----------------------------
        # Rule 2: INELIGIBLE → BLOCKED
        # -----------------------------
        if eligibility_label == "INELIGIBLE":
            return V12ContributionConstraintSchema.create_constraint_binding_record(
                zone_label=CONTRIB_ZONE_BLOCKED,
                constraint_labels=[CONSTRAINT_CONTRIB_BLOCKED_INELIGIBLE],
                basis=basis,
                contribution_label=contribution_label if contribution_label != "UNCLASSIFIED" else None,
                regime_level=regime_level,
                role_type=role_type if role_type != "UNCLASSIFIED" else None,
                distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
            )

        # -----------------------------
        # Rule 3: SUPPRESSED → BLOCKED
        # -----------------------------
        if suppression_state == "SUPPRESSED":
            return V12ContributionConstraintSchema.create_constraint_binding_record(
                zone_label=CONTRIB_ZONE_BLOCKED,
                constraint_labels=[CONSTRAINT_CONTRIB_BLOCKED_SUPPRESSED],
                basis=basis,
                contribution_label=contribution_label if contribution_label != "UNCLASSIFIED" else None,
                regime_level=regime_level,
                role_type=role_type if role_type != "UNCLASSIFIED" else None,
                distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
            )

        # -----------------------------
        # Rule 4: REGIME_HIGH or REGIME_LOW → SECONDARY
        # -----------------------------
        if regime_level in ["REGIME_HIGH", "REGIME_LOW"]:
            return V12ContributionConstraintSchema.create_constraint_binding_record(
                zone_label=CONTRIB_ZONE_SECONDARY,
                constraint_labels=[CONSTRAINT_CONTRIB_SECONDARY_REGIME_NON_MEDIUM],
                basis=basis,
                contribution_label=contribution_label if contribution_label != "UNCLASSIFIED" else None,
                regime_level=regime_level,
                role_type=role_type if role_type != "UNCLASSIFIED" else None,
                distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
            )

        # -----------------------------
        # Rule 5: REGIME_MEDIUM × VOLATILITY × D1-D5 → PRIMARY
        # -----------------------------
        if (
            regime_level == "REGIME_MEDIUM"
            and role_type == "VOLATILITY_ROLE"
            and distortion_type in [
                "D1_LIQUIDATION",
                "D2_RANGE_STICKINESS",
                "D3_BOOK_HOLLOWING",
                "D4_EVENT_DISTORTION",
                "D5_CORRELATION_DISTORTION",
            ]
        ):
            return V12ContributionConstraintSchema.create_constraint_binding_record(
                zone_label=CONTRIB_ZONE_PRIMARY,
                constraint_labels=[CONSTRAINT_CONTRIB_PRIMARY_MEDIUM_VOLATILITY_DISTORTION],
                basis=basis,
                contribution_label=contribution_label if contribution_label != "UNCLASSIFIED" else None,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
            )

        # -----------------------------
        # Rule 6: Default → NONE
        # -----------------------------
        return V12ContributionConstraintSchema.create_constraint_binding_record(
            zone_label=CONTRIB_ZONE_NONE,
            constraint_labels=[CONSTRAINT_CONTRIB_NONE_DEFAULT],
            basis=basis,
            contribution_label=contribution_label if contribution_label != "UNCLASSIFIED" else None,
            regime_level=regime_level,
            role_type=role_type if role_type != "UNCLASSIFIED" else None,
            distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
        )

    except Exception as e:
        return V12ContributionConstraintSchema.create_error_record(f"exception: {type(e).__name__}")


def get_contribution_binding_engine_v1_info() -> Dict[str, Any]:
    """
    Get contribution binding engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "contribution_constraint_binding",
        "input_schema": "contribution + regime + role + distortion + eligibility + permission_monitor",
        "output_schema": "v12_contribution_constraint",
        "binding_rules": [
            "invalid_inputs → ERROR",
            "REGIME_CRITICAL → BLOCKED",
            "INELIGIBLE → BLOCKED",
            "SUPPRESSED → BLOCKED",
            "REGIME_HIGH|LOW → SECONDARY",
            "REGIME_MEDIUM × VOLATILITY × D1-D5 → PRIMARY",
            "default → NONE",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_coupling",
            "deterministic",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Contribution Constraint Binding Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Invalid input → ERROR
    print("Test 1: Invalid input → ERROR")
    result1 = bind_contribution_constraints_v1(regime_record={"v11_regime_level": "UNCLASSIFIED"})
    print(f"Status: {result1['v12_contrib_constraint_status']}")
    print(f"Zone: {result1['v12_contrib_constraint_zone_label']}")
    print()

    # Test 2: REGIME_CRITICAL → BLOCKED
    print("Test 2: REGIME_CRITICAL → BLOCKED")
    result2 = bind_contribution_constraints_v1(
        regime_record={"v11_regime_level": "REGIME_CRITICAL"},
    )
    print(f"Zone: {result2['v12_contrib_constraint_zone_label']}")
    print(f"Constraints: {result2['v12_contrib_constraint_labels']}")
    print()

    # Test 3: INELIGIBLE → BLOCKED
    print("Test 3: INELIGIBLE → BLOCKED")
    result3 = bind_contribution_constraints_v1(
        regime_record={"v11_regime_level": "REGIME_MEDIUM"},
        eligibility_record={"v12_eligibility_status": "INELIGIBLE"},
    )
    print(f"Zone: {result3['v12_contrib_constraint_zone_label']}")
    print()

    # Test 4: MEDIUM × VOLATILITY × D1 → PRIMARY
    print("Test 4: MEDIUM × VOLATILITY × D1 → PRIMARY")
    result4 = bind_contribution_constraints_v1(
        regime_record={"v11_regime_level": "REGIME_MEDIUM"},
        role_record={"v12_role_carrier_role_type": "VOLATILITY_ROLE"},
        distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    )
    print(f"Zone: {result4['v12_contrib_constraint_zone_label']}")
    print(f"Constraints: {result4['v12_contrib_constraint_labels']}")
    print()

    # Test 5: REGIME_HIGH → SECONDARY
    print("Test 5: REGIME_HIGH → SECONDARY")
    result5 = bind_contribution_constraints_v1(
        regime_record={"v11_regime_level": "REGIME_HIGH"},
    )
    print(f"Zone: {result5['v12_contrib_constraint_zone_label']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
