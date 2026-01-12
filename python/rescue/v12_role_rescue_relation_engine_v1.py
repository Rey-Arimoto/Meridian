#!/usr/bin/env python3
"""
PR133: v1.2 Role Rescue Relation Engine v1 (READ-ONLY)

Purpose:
    Classify ROLE→ROLE structural rescue relations based on regime/distortion/boundary conditions.
    Rescue = Structural dependency edge (NOT action, NOT recommendation).

Rules (first-match-wins):
    0. Invalid inputs → ERROR
    1. Hard stops (NONE):
       - REGIME_CRITICAL
       - SCHEMA_BOUNDARY, DATA_BOUNDARY, ENGINE_BOUNDARY
       - SUPPRESSED (PR126)
       - INELIGIBLE (PR128)
    2. REGIME_HIGH → max strength WEAK
    3. REGIME_LOW → max strength WEAK
    4. REGIME_MEDIUM → Use DistortionType × role mapping:
       - STABILITY → VOLATILITY (D1/D5) => BUFFER/ANCHOR, MODERATE
       - LIQUIDITY → VOLATILITY (D2/D3) => DAMPEN, MODERATE
       - HEDGE → VOLATILITY (D4/D5) => BUFFER, WEAK (prefer WEAK)
       - GAS → VOLATILITY (any) => CONTINUITY, WEAK
       - LIQUIDITY → STABILITY (D2/D3) => DAMPEN, WEAK
       - STABILITY → LIQUIDITY (D2/D3) => ANCHOR, WEAK
    5. Default → UNCLASSIFIED, WEAK (respects HIGH/LOW caps)

Rescue ≠ Action
Rescue = Label propagation
"""

from typing import Any, Dict, List, Optional

from .v12_role_rescue_relation_schema import (
    V12RoleRescueRelationSchema,
    RESCUE_EDGE_BUFFER,
    RESCUE_EDGE_ANCHOR,
    RESCUE_EDGE_CONTINUITY,
    RESCUE_EDGE_DAMPEN,
    RESCUE_EDGE_UNCLASSIFIED,
    RESCUE_STRENGTH_NONE,
    RESCUE_STRENGTH_WEAK,
    RESCUE_STRENGTH_MODERATE,
    RESCUE_STRENGTH_STRONG,
    ROLE_GAS,
    ROLE_STABILITY,
    ROLE_LIQUIDITY,
    ROLE_VOLATILITY,
    ROLE_HEDGE,
    ROLE_UNCLASSIFIED,
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


def classify_role_rescue_relation_v1(
    regime_record: Optional[Dict[str, Any]] = None,
    distortion_record: Optional[Dict[str, Any]] = None,
    role_from: Optional[str] = None,
    role_to: Optional[str] = None,
    boundary_record: Optional[Dict[str, Any]] = None,
    permission_monitor_record: Optional[Dict[str, Any]] = None,
    eligibility_record: Optional[Dict[str, Any]] = None,
    policy_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classify role rescue relation (ROLE→ROLE structural dependency edge).

    Args:
        regime_record: PR110 regime record
        distortion_record: PR129 distortion record
        role_from: Source role (rescuer)
        role_to: Target role (rescued)
        boundary_record: Optional boundary record
        permission_monitor_record: PR126 permission monitor record
        eligibility_record: PR128 eligibility record
        policy_record: Optional policy record

    Returns:
        Rescue relation record (always valid, ERROR on failure)
    """
    try:
        basis = []

        # Extract inputs
        regime_level = _safe_get(regime_record, "v11_regime_level", "UNCLASSIFIED")
        if regime_record:
            basis.append("v11_regime_level")

        distortion_type = _safe_get(distortion_record, "v12_distortion_type", "UNCLASSIFIED")
        if distortion_record:
            basis.append("v12_distortion_type")

        boundary_type = _safe_get(boundary_record, "v11_boundary_type", "NONE")
        if boundary_record:
            basis.append("v11_boundary_type")

        suppression_state = _safe_get(permission_monitor_record, "v12_monitor_suppression_state", "UNKNOWN")
        if permission_monitor_record:
            basis.append("v12_monitor_suppression_state")

        eligibility_label = _safe_get(eligibility_record, "v12_eligibility_status", "UNKNOWN")
        if eligibility_record:
            basis.append("v12_eligibility_status")

        # -----------------------------
        # Rule 0: Defensive (invalid inputs)
        # -----------------------------
        if not role_from or role_from == ROLE_UNCLASSIFIED:
            return V12RoleRescueRelationSchema.create_error_record(
                "invalid inputs: role_from must be classified.",
                role_from=role_from,
                role_to=role_to,
            )

        if not role_to or role_to == ROLE_UNCLASSIFIED:
            return V12RoleRescueRelationSchema.create_error_record(
                "invalid inputs: role_to must be classified.",
                role_from=role_from,
                role_to=role_to,
            )

        if regime_level == "UNCLASSIFIED":
            return V12RoleRescueRelationSchema.create_error_record(
                "invalid inputs: regime_level must be classified.",
                role_from=role_from,
                role_to=role_to,
            )

        # -----------------------------
        # Rule 1: Hard stops → NONE
        # -----------------------------

        # 1a) REGIME_CRITICAL
        if regime_level == "REGIME_CRITICAL":
            return V12RoleRescueRelationSchema.create_rescue_relation_record(
                role_from=role_from,
                role_to=role_to,
                edge_type=RESCUE_EDGE_UNCLASSIFIED,
                strength=RESCUE_STRENGTH_NONE,
                basis=basis,
                regime_level=regime_level,
                distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
                warnings=["Rescue blocked: REGIME_CRITICAL."],
            )

        # 1b) Hard boundaries
        if boundary_type in ["SCHEMA_BOUNDARY", "DATA_BOUNDARY", "ENGINE_BOUNDARY"]:
            return V12RoleRescueRelationSchema.create_rescue_relation_record(
                role_from=role_from,
                role_to=role_to,
                edge_type=RESCUE_EDGE_UNCLASSIFIED,
                strength=RESCUE_STRENGTH_NONE,
                basis=basis,
                regime_level=regime_level,
                distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
                warnings=[f"Rescue blocked: hard boundary {boundary_type}."],
            )

        # 1c) SUPPRESSED
        if suppression_state == "SUPPRESSED":
            return V12RoleRescueRelationSchema.create_rescue_relation_record(
                role_from=role_from,
                role_to=role_to,
                edge_type=RESCUE_EDGE_UNCLASSIFIED,
                strength=RESCUE_STRENGTH_NONE,
                basis=basis,
                regime_level=regime_level,
                distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
                warnings=["Rescue blocked: SUPPRESSED."],
            )

        # 1d) INELIGIBLE
        if eligibility_label == "INELIGIBLE":
            return V12RoleRescueRelationSchema.create_rescue_relation_record(
                role_from=role_from,
                role_to=role_to,
                edge_type=RESCUE_EDGE_UNCLASSIFIED,
                strength=RESCUE_STRENGTH_NONE,
                basis=basis,
                regime_level=regime_level,
                distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
                warnings=["Rescue blocked: INELIGIBLE."],
            )

        # -----------------------------
        # Rule 2/3: HIGH/LOW regime → max WEAK
        # -----------------------------
        if regime_level in ["REGIME_HIGH", "REGIME_LOW"]:
            # Still try to classify edge type, but cap strength at WEAK
            edge_type = _classify_edge_type(role_from, role_to, distortion_type)
            return V12RoleRescueRelationSchema.create_rescue_relation_record(
                role_from=role_from,
                role_to=role_to,
                edge_type=edge_type,
                strength=RESCUE_STRENGTH_WEAK,
                basis=basis,
                regime_level=regime_level,
                distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
            )

        # -----------------------------
        # Rule 4: REGIME_MEDIUM → Use distortion × role mapping
        # -----------------------------
        if regime_level == "REGIME_MEDIUM":
            edge_type, strength = _classify_medium_regime_rescue(role_from, role_to, distortion_type)
            return V12RoleRescueRelationSchema.create_rescue_relation_record(
                role_from=role_from,
                role_to=role_to,
                edge_type=edge_type,
                strength=strength,
                basis=basis,
                regime_level=regime_level,
                distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
            )

        # -----------------------------
        # Rule 5: Default → UNCLASSIFIED, WEAK
        # -----------------------------
        return V12RoleRescueRelationSchema.create_rescue_relation_record(
            role_from=role_from,
            role_to=role_to,
            edge_type=RESCUE_EDGE_UNCLASSIFIED,
            strength=RESCUE_STRENGTH_WEAK,
            basis=basis,
            regime_level=regime_level,
            distortion_type=distortion_type if distortion_type != "UNCLASSIFIED" else None,
        )

    except Exception as e:
        return V12RoleRescueRelationSchema.create_error_record(
            f"exception: {type(e).__name__}",
            role_from=role_from,
            role_to=role_to,
        )


def _classify_edge_type(role_from: str, role_to: str, distortion_type: str) -> str:
    """
    Classify edge type based on role pair (simplified, no strength).

    Args:
        role_from: Source role
        role_to: Target role
        distortion_type: Distortion type

    Returns:
        Edge type
    """
    # STABILITY → VOLATILITY
    if role_from == ROLE_STABILITY and role_to == ROLE_VOLATILITY:
        if distortion_type in ["D1_LIQUIDATION", "D5_CORRELATION_DISTORTION"]:
            return RESCUE_EDGE_BUFFER
        return RESCUE_EDGE_ANCHOR

    # LIQUIDITY → VOLATILITY
    if role_from == ROLE_LIQUIDITY and role_to == ROLE_VOLATILITY:
        if distortion_type in ["D2_RANGE_STICKINESS", "D3_BOOK_HOLLOWING"]:
            return RESCUE_EDGE_DAMPEN
        return RESCUE_EDGE_UNCLASSIFIED

    # HEDGE → VOLATILITY
    if role_from == ROLE_HEDGE and role_to == ROLE_VOLATILITY:
        return RESCUE_EDGE_BUFFER

    # GAS → VOLATILITY
    if role_from == ROLE_GAS and role_to == ROLE_VOLATILITY:
        return RESCUE_EDGE_CONTINUITY

    # LIQUIDITY → STABILITY
    if role_from == ROLE_LIQUIDITY and role_to == ROLE_STABILITY:
        if distortion_type in ["D2_RANGE_STICKINESS", "D3_BOOK_HOLLOWING"]:
            return RESCUE_EDGE_DAMPEN
        return RESCUE_EDGE_UNCLASSIFIED

    # STABILITY → LIQUIDITY
    if role_from == ROLE_STABILITY and role_to == ROLE_LIQUIDITY:
        if distortion_type in ["D2_RANGE_STICKINESS", "D3_BOOK_HOLLOWING"]:
            return RESCUE_EDGE_ANCHOR
        return RESCUE_EDGE_UNCLASSIFIED

    return RESCUE_EDGE_UNCLASSIFIED


def _classify_medium_regime_rescue(role_from: str, role_to: str, distortion_type: str) -> tuple[str, str]:
    """
    Classify rescue relation for REGIME_MEDIUM.

    Args:
        role_from: Source role
        role_to: Target role
        distortion_type: Distortion type

    Returns:
        Tuple of (edge_type, strength)
    """
    # STABILITY → VOLATILITY
    if role_from == ROLE_STABILITY and role_to == ROLE_VOLATILITY:
        if distortion_type in ["D1_LIQUIDATION", "D5_CORRELATION_DISTORTION"]:
            # D1 => BUFFER, D5 => ANCHOR (both MODERATE)
            edge_type = RESCUE_EDGE_BUFFER if distortion_type == "D1_LIQUIDATION" else RESCUE_EDGE_ANCHOR
            return (edge_type, RESCUE_STRENGTH_MODERATE)
        return (RESCUE_EDGE_ANCHOR, RESCUE_STRENGTH_WEAK)

    # LIQUIDITY → VOLATILITY
    if role_from == ROLE_LIQUIDITY and role_to == ROLE_VOLATILITY:
        if distortion_type in ["D2_RANGE_STICKINESS", "D3_BOOK_HOLLOWING"]:
            return (RESCUE_EDGE_DAMPEN, RESCUE_STRENGTH_MODERATE)
        return (RESCUE_EDGE_UNCLASSIFIED, RESCUE_STRENGTH_WEAK)

    # HEDGE → VOLATILITY
    if role_from == ROLE_HEDGE and role_to == ROLE_VOLATILITY:
        if distortion_type in ["D4_EVENT_DISTORTION", "D5_CORRELATION_DISTORTION"]:
            # Prefer WEAK for HEDGE
            return (RESCUE_EDGE_BUFFER, RESCUE_STRENGTH_WEAK)
        return (RESCUE_EDGE_BUFFER, RESCUE_STRENGTH_WEAK)

    # GAS → VOLATILITY
    if role_from == ROLE_GAS and role_to == ROLE_VOLATILITY:
        return (RESCUE_EDGE_CONTINUITY, RESCUE_STRENGTH_WEAK)

    # LIQUIDITY → STABILITY
    if role_from == ROLE_LIQUIDITY and role_to == ROLE_STABILITY:
        if distortion_type in ["D2_RANGE_STICKINESS", "D3_BOOK_HOLLOWING"]:
            return (RESCUE_EDGE_DAMPEN, RESCUE_STRENGTH_WEAK)
        return (RESCUE_EDGE_UNCLASSIFIED, RESCUE_STRENGTH_WEAK)

    # STABILITY → LIQUIDITY
    if role_from == ROLE_STABILITY and role_to == ROLE_LIQUIDITY:
        if distortion_type in ["D2_RANGE_STICKINESS", "D3_BOOK_HOLLOWING"]:
            return (RESCUE_EDGE_ANCHOR, RESCUE_STRENGTH_WEAK)
        return (RESCUE_EDGE_UNCLASSIFIED, RESCUE_STRENGTH_WEAK)

    # Default
    return (RESCUE_EDGE_UNCLASSIFIED, RESCUE_STRENGTH_WEAK)


def get_role_rescue_relation_engine_v1_info() -> Dict[str, Any]:
    """
    Get role rescue relation engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "role_rescue_relation",
        "input_schema": "regime + distortion + role_from + role_to + boundary + permission_monitor + eligibility + policy",
        "output_schema": "v12_rescue",
        "classification_rules": [
            "invalid_inputs → ERROR",
            "REGIME_CRITICAL → NONE",
            "hard_boundaries → NONE",
            "SUPPRESSED → NONE",
            "INELIGIBLE → NONE",
            "REGIME_HIGH|LOW → max WEAK",
            "REGIME_MEDIUM × distortion × role → edge type + strength",
            "default → UNCLASSIFIED WEAK",
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
    print("v1.2 Role Rescue Relation Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Invalid input → ERROR
    print("Test 1: Invalid input → ERROR")
    result1 = classify_role_rescue_relation_v1(
        regime_record={"v11_regime_level": "UNCLASSIFIED"},
        role_from=ROLE_STABILITY,
        role_to=ROLE_VOLATILITY,
    )
    print(f"Status: {result1['v12_rescue_status']}")
    print()

    # Test 2: REGIME_CRITICAL → NONE
    print("Test 2: REGIME_CRITICAL → NONE")
    result2 = classify_role_rescue_relation_v1(
        regime_record={"v11_regime_level": "REGIME_CRITICAL"},
        role_from=ROLE_STABILITY,
        role_to=ROLE_VOLATILITY,
    )
    print(f"Strength: {result2['v12_rescue_strength']}")
    print(f"Warnings: {result2.get('v12_rescue_warnings', [])}")
    print()

    # Test 3: MEDIUM + STABILITY→VOLATILITY + D1 → BUFFER MODERATE
    print("Test 3: MEDIUM + STABILITY→VOLATILITY + D1 → BUFFER MODERATE")
    result3 = classify_role_rescue_relation_v1(
        regime_record={"v11_regime_level": "REGIME_MEDIUM"},
        distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        role_from=ROLE_STABILITY,
        role_to=ROLE_VOLATILITY,
    )
    print(f"Edge: {result3['v12_rescue_edge_type']}")
    print(f"Strength: {result3['v12_rescue_strength']}")
    print()

    # Test 4: HIGH → max WEAK
    print("Test 4: HIGH → max WEAK")
    result4 = classify_role_rescue_relation_v1(
        regime_record={"v11_regime_level": "REGIME_HIGH"},
        distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        role_from=ROLE_STABILITY,
        role_to=ROLE_VOLATILITY,
    )
    print(f"Strength: {result4['v12_rescue_strength']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
