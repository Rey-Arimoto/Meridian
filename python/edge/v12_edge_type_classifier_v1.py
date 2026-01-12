#!/usr/bin/env python3
"""
PR135: v1.2 Edge Type Classification Engine v1 (READ-ONLY)

Purpose:
    Classify edge types for regime × role × distortion combinations.
    Static deterministic first-match-wins classification.

Classification Rules (First-match-wins):
    0. Invalid inputs → ERROR or defensive EDGE_NONE
    1. REGIME_CRITICAL → EDGE_SHIELD (always shield in critical)
    2. GAS_ROLE → EDGE_SHIELD (always shield)
    3. STABILITY_ROLE + distortion in {D1,D3,D4,D5} → EDGE_SHIELD
    4. HEDGE_ROLE + regime in {MEDIUM,HIGH,CRITICAL} → EDGE_SHIELD
    5. LIQUIDITY_ROLE + regime in {HIGH,CRITICAL} → EDGE_LEAK
    6. LIQUIDITY_ROLE + regime MEDIUM → EDGE_NEUTRAL
    7. REGIME_MEDIUM + VOLATILITY_ROLE + distortion D1-D5 → EDGE_AMPLIFY
    8. REGIME_HIGH → EDGE_LEAK (esp LIQUIDITY + D3)
    9. REGIME_LOW → EDGE_NEUTRAL
    10. Default → EDGE_NEUTRAL (defensive)

EdgeType ≠ Action
EdgeType = Structural label propagation
"""

from typing import Any, Dict, List, Optional

from .v12_edge_type_schema import (
    V12EdgeTypeSchema,
    EDGE_NONE,
    EDGE_AMPLIFY,
    EDGE_SHIELD,
    EDGE_LEAK,
    EDGE_NEUTRAL,
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


def classify_edge_type_v1(
    regime_record: Optional[Dict[str, Any]] = None,
    role_record: Optional[Dict[str, Any]] = None,
    distortion_record: Optional[Dict[str, Any]] = None,
    subtype_record: Optional[Dict[str, Any]] = None,
    contribution_record: Optional[Dict[str, Any]] = None,
    constraints_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classify edge type for regime × role × distortion combination.

    Args:
        regime_record: PR110 regime record
        role_record: PR130 role qualification record
        distortion_record: PR129 distortion record
        subtype_record: PR134 distortion subtype record (optional)
        contribution_record: PR131 contribution record (optional)
        constraints_record: PR132 constraint binding record (optional)

    Returns:
        Edge type record (always valid, defensive fallback to EDGE_NEUTRAL)
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

        subtype_label = _safe_get(subtype_record, "v12_subtype_label", "NONE")
        if subtype_record:
            basis.append("v12_subtype_label")

        contribution_label = _safe_get(contribution_record, "v12_contrib_contribution_label", None)

        # -----------------------------
        # Rule 0: Defensive (invalid inputs)
        # -----------------------------
        # Be defensive: if missing critical inputs, return EDGE_NEUTRAL
        if regime_level == "UNCLASSIFIED" or role_type == "UNCLASSIFIED" or distortion_type == "UNCLASSIFIED":
            # Defensive: return EDGE_NEUTRAL instead of ERROR
            return V12EdgeTypeSchema.create_edge_record(
                edge_type=EDGE_NEUTRAL,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                basis=basis,
                warnings=["Defensive: missing inputs, defaulting to EDGE_NEUTRAL."],
            )

        # -----------------------------
        # Rule 1: REGIME_CRITICAL → EDGE_SHIELD
        # -----------------------------
        if regime_level == "REGIME_CRITICAL":
            return V12EdgeTypeSchema.create_edge_record(
                edge_type=EDGE_SHIELD,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                basis=basis,
                subtype_label=subtype_label,
                contribution_label=contribution_label,
            )

        # -----------------------------
        # Rule 2: GAS_ROLE → EDGE_SHIELD
        # -----------------------------
        if role_type == "GAS_ROLE":
            return V12EdgeTypeSchema.create_edge_record(
                edge_type=EDGE_SHIELD,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                basis=basis,
                subtype_label=subtype_label,
                contribution_label=contribution_label,
            )

        # -----------------------------
        # Rule 3: STABILITY_ROLE + distortion in {D1,D3,D4,D5} → EDGE_SHIELD
        # -----------------------------
        if role_type == "STABILITY_ROLE" and distortion_type in [
            "D1_LIQUIDATION",
            "D3_BOOK_HOLLOWING",
            "D4_EVENT_DISTORTION",
            "D5_CORRELATION_DISTORTION",
        ]:
            return V12EdgeTypeSchema.create_edge_record(
                edge_type=EDGE_SHIELD,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                basis=basis,
                subtype_label=subtype_label,
                contribution_label=contribution_label,
            )

        # -----------------------------
        # Rule 4: HEDGE_ROLE + regime in {MEDIUM,HIGH,CRITICAL} → EDGE_SHIELD
        # -----------------------------
        if role_type == "HEDGE_ROLE" and regime_level in ["REGIME_MEDIUM", "REGIME_HIGH", "REGIME_CRITICAL"]:
            return V12EdgeTypeSchema.create_edge_record(
                edge_type=EDGE_SHIELD,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                basis=basis,
                subtype_label=subtype_label,
                contribution_label=contribution_label,
            )

        # -----------------------------
        # Rule 5: LIQUIDITY_ROLE + regime in {HIGH,CRITICAL} → EDGE_LEAK
        # -----------------------------
        if role_type == "LIQUIDITY_ROLE" and regime_level in ["REGIME_HIGH", "REGIME_CRITICAL"]:
            return V12EdgeTypeSchema.create_edge_record(
                edge_type=EDGE_LEAK,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                basis=basis,
                subtype_label=subtype_label,
                contribution_label=contribution_label,
            )

        # -----------------------------
        # Rule 6: LIQUIDITY_ROLE + regime MEDIUM → EDGE_NEUTRAL
        # -----------------------------
        if role_type == "LIQUIDITY_ROLE" and regime_level == "REGIME_MEDIUM":
            return V12EdgeTypeSchema.create_edge_record(
                edge_type=EDGE_NEUTRAL,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                basis=basis,
                subtype_label=subtype_label,
                contribution_label=contribution_label,
            )

        # -----------------------------
        # Rule 7: REGIME_MEDIUM + VOLATILITY_ROLE + distortion D1-D5 → EDGE_AMPLIFY
        # -----------------------------
        if regime_level == "REGIME_MEDIUM" and role_type == "VOLATILITY_ROLE" and distortion_type in [
            "D1_LIQUIDATION",
            "D2_RANGE_STICKINESS",
            "D3_BOOK_HOLLOWING",
            "D4_EVENT_DISTORTION",
            "D5_CORRELATION_DISTORTION",
        ]:
            return V12EdgeTypeSchema.create_edge_record(
                edge_type=EDGE_AMPLIFY,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                basis=basis,
                subtype_label=subtype_label,
                contribution_label=contribution_label,
            )

        # -----------------------------
        # Rule 8: REGIME_HIGH → EDGE_LEAK (esp LIQUIDITY + D3)
        # -----------------------------
        if regime_level == "REGIME_HIGH":
            return V12EdgeTypeSchema.create_edge_record(
                edge_type=EDGE_LEAK,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                basis=basis,
                subtype_label=subtype_label,
                contribution_label=contribution_label,
            )

        # -----------------------------
        # Rule 9: REGIME_LOW → EDGE_NEUTRAL
        # -----------------------------
        if regime_level == "REGIME_LOW":
            return V12EdgeTypeSchema.create_edge_record(
                edge_type=EDGE_NEUTRAL,
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                basis=basis,
                subtype_label=subtype_label,
                contribution_label=contribution_label,
            )

        # -----------------------------
        # Rule 10: Default → EDGE_NEUTRAL (defensive)
        # -----------------------------
        return V12EdgeTypeSchema.create_edge_record(
            edge_type=EDGE_NEUTRAL,
            regime_level=regime_level,
            role_type=role_type,
            distortion_type=distortion_type,
            basis=basis,
            subtype_label=subtype_label,
            contribution_label=contribution_label,
        )

    except Exception as e:
        # Defensive: never raise, return EDGE_NEUTRAL with warning
        return V12EdgeTypeSchema.create_edge_record(
            edge_type=EDGE_NEUTRAL,
            regime_level="UNCLASSIFIED",
            role_type="UNCLASSIFIED",
            distortion_type="UNCLASSIFIED",
            basis=[],
            warnings=[f"Exception: {type(e).__name__}"],
        )


def get_edge_type_classifier_v1_info() -> Dict[str, Any]:
    """
    Get edge type classifier v1 information.

    Returns:
        Dict with classifier metadata
    """
    return {
        "classifier_version": "v1",
        "classifier_type": "edge_type",
        "input_schema": "regime + role + distortion + subtype (optional) + contribution (optional) + constraints (optional)",
        "output_schema": "v12_edge",
        "classification_rules": [
            "invalid_inputs → EDGE_NEUTRAL (defensive)",
            "REGIME_CRITICAL → EDGE_SHIELD",
            "GAS_ROLE → EDGE_SHIELD",
            "STABILITY_ROLE + D1/D3/D4/D5 → EDGE_SHIELD",
            "HEDGE_ROLE + MEDIUM/HIGH/CRITICAL → EDGE_SHIELD",
            "LIQUIDITY_ROLE + HIGH/CRITICAL → EDGE_LEAK",
            "LIQUIDITY_ROLE + MEDIUM → EDGE_NEUTRAL",
            "REGIME_MEDIUM + VOLATILITY_ROLE + D1-D5 → EDGE_AMPLIFY",
            "REGIME_HIGH → EDGE_LEAK",
            "REGIME_LOW → EDGE_NEUTRAL",
            "default → EDGE_NEUTRAL",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_edge_coupling",
            "deterministic",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Edge Type Classifier v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Defensive missing inputs → EDGE_NEUTRAL
    print("Test 1: Defensive missing inputs → EDGE_NEUTRAL")
    result1 = classify_edge_type_v1(
        regime_record={"v11_regime_level": "UNCLASSIFIED"},
    )
    print(f"Edge: {result1['v12_edge_type']}")
    print()

    # Test 2: CRITICAL → SHIELD
    print("Test 2: CRITICAL → SHIELD")
    result2 = classify_edge_type_v1(
        regime_record={"v11_regime_level": "REGIME_CRITICAL"},
        role_record={"v12_role_carrier_role_type": "VOLATILITY_ROLE"},
        distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    )
    print(f"Edge: {result2['v12_edge_type']}")
    print()

    # Test 3: MEDIUM + VOLATILITY + D1 → AMPLIFY
    print("Test 3: MEDIUM + VOLATILITY + D1 → AMPLIFY")
    result3 = classify_edge_type_v1(
        regime_record={"v11_regime_level": "REGIME_MEDIUM"},
        role_record={"v12_role_carrier_role_type": "VOLATILITY_ROLE"},
        distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
    )
    print(f"Edge: {result3['v12_edge_type']}")
    print()

    # Test 4: HIGH + LIQUIDITY → LEAK
    print("Test 4: HIGH + LIQUIDITY → LEAK")
    result4 = classify_edge_type_v1(
        regime_record={"v11_regime_level": "REGIME_HIGH"},
        role_record={"v12_role_carrier_role_type": "LIQUIDITY_ROLE"},
        distortion_record={"v12_distortion_type": "D3_BOOK_HOLLOWING"},
    )
    print(f"Edge: {result4['v12_edge_type']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
