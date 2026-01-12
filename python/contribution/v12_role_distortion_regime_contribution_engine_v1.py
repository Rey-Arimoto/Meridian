#!/usr/bin/env python3
"""
PR131: v1.2 Role × Distortion × Regime Contribution Engine v1 (READ-ONLY)

Purpose:
    Classify structural return contribution from regime × role × distortion combinations.
    Static, deterministic, label-based only (no numeric returns, no performance claims).

Rules (first-match-wins):
    0. Defensive: Invalid input → ERROR + CONTRIB_UNKNOWN
    1. REGIME_CRITICAL → CONTRIB_STRONGLY_NEGATIVE
    2. INELIGIBLE → CONTRIB_NEUTRAL
    3. REGIME_HIGH → CONTRIB_NEGATIVE (mostly), CONTRIB_NEUTRAL for VOLATILITY × D1/D3/D4
    4. REGIME_LOW → CONTRIB_NEUTRAL
    5. REGIME_MEDIUM → Primary alpha zone (++/+/0 depending on role×distortion)

Contribution ≠ Performance
Contribution ≠ Return guarantee
Contribution = Structural side-effect label
"""

from typing import Any, Dict, List, Optional

from .v12_contribution_schema import (
    V12ContributionSchema,
    CONTRIB_STRONGLY_POSITIVE,
    CONTRIB_POSITIVE,
    CONTRIB_NEUTRAL,
    CONTRIB_NEGATIVE,
    CONTRIB_STRONGLY_NEGATIVE,
    CONTRIB_UNKNOWN,
    RATIONALE_DISTORTION_CAPTURE_ZONE,
    RATIONALE_STRUCTURE_INTELLIGIBLE,
    RATIONALE_FORCED_FLOW_PRESENT,
    RATIONALE_LIQUIDITY_PREMIUM_ZONE,
    RATIONALE_STRUCTURE_BREAKDOWN_RISK,
    RATIONALE_NON_ACTION_PRESERVES_OPTIONALITY,
    RATIONALE_ELEVATED_UNCERTAINTY,
    RATIONALE_CAPITAL_PRESERVATION_PRIORITY,
    RATIONALE_LOW_DISTORTION_DENSITY,
    RATIONALE_OPPORTUNITY_THIN,
    RATIONALE_STABILITY_BUFFER_ROLE,
    RATIONALE_HEDGE_ALIGNMENT_ZONE,
    RATIONALE_OPERATIONAL_ENABLER_ONLY,
    RATIONALE_INELIGIBLE_TOUCHABILITY,
)


def _safe_str(val: Any, default: str = "UNCLASSIFIED") -> str:
    """
    Safely convert value to string.

    Args:
        val: Value to convert
        default: Default value

    Returns:
        String value or default
    """
    if isinstance(val, str):
        return val
    return default


def classify_contribution_v1(
    regime_level: str,
    role_type: str,
    distortion_type: str,
    eligibility_label: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Classify structural return contribution.

    Args:
        regime_level: Regime level (REGIME_LOW/MEDIUM/HIGH/CRITICAL)
        role_type: Role type (GAS_ROLE, STABILITY_ROLE, etc.)
        distortion_type: Distortion type (D1-D5)
        eligibility_label: Optional eligibility label from PR128

    Returns:
        Contribution record (always valid, ERROR on failure)
    """
    try:
        # Defensive validation
        regime_level = _safe_str(regime_level, "UNCLASSIFIED")
        role_type = _safe_str(role_type, "UNCLASSIFIED")
        distortion_type = _safe_str(distortion_type, "UNCLASSIFIED")
        eligibility_label = _safe_str(eligibility_label, "UNKNOWN") if eligibility_label else "UNKNOWN"

        basis = ["regime_level", "role_type", "distortion_type"]
        if eligibility_label != "UNKNOWN":
            basis.append("eligibility_label")

        # -----------------------------
        # Rule 0: Defensive (invalid inputs)
        # -----------------------------
        if regime_level == "UNCLASSIFIED" or role_type == "UNCLASSIFIED" or distortion_type == "UNCLASSIFIED":
            return V12ContributionSchema.create_error_record(
                "invalid inputs: regime/role/distortion must be classified."
            )

        # -----------------------------
        # Rule 1: REGIME_CRITICAL → CONTRIB_STRONGLY_NEGATIVE
        # -----------------------------
        if regime_level == "REGIME_CRITICAL":
            return V12ContributionSchema.create_contribution_record(
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                contribution_label=CONTRIB_STRONGLY_NEGATIVE,
                contribution_rationale=[
                    RATIONALE_STRUCTURE_BREAKDOWN_RISK,
                    RATIONALE_NON_ACTION_PRESERVES_OPTIONALITY,
                ],
                eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
                basis=basis,
            )

        # -----------------------------
        # Rule 2: INELIGIBLE → CONTRIB_NEUTRAL
        # -----------------------------
        if eligibility_label == "INELIGIBLE":
            return V12ContributionSchema.create_contribution_record(
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                contribution_label=CONTRIB_NEUTRAL,
                contribution_rationale=[
                    RATIONALE_INELIGIBLE_TOUCHABILITY,
                    RATIONALE_NON_ACTION_PRESERVES_OPTIONALITY,
                ],
                eligibility_label=eligibility_label,
                basis=basis,
            )

        # -----------------------------
        # Rule 3: REGIME_HIGH → mostly NEGATIVE, some NEUTRAL
        # -----------------------------
        if regime_level == "REGIME_HIGH":
            # VOLATILITY × D1/D3/D4 → NEUTRAL (not positive)
            if role_type == "VOLATILITY_ROLE" and distortion_type in ["D1_LIQUIDATION", "D3_BOOK_HOLLOWING", "D4_EVENT_DISTORTION"]:
                return V12ContributionSchema.create_contribution_record(
                    regime_level=regime_level,
                    role_type=role_type,
                    distortion_type=distortion_type,
                    contribution_label=CONTRIB_NEUTRAL,
                    contribution_rationale=[
                        RATIONALE_ELEVATED_UNCERTAINTY,
                        RATIONALE_CAPITAL_PRESERVATION_PRIORITY,
                    ],
                    eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
                    basis=basis,
                )
            # Others → NEGATIVE
            else:
                return V12ContributionSchema.create_contribution_record(
                    regime_level=regime_level,
                    role_type=role_type,
                    distortion_type=distortion_type,
                    contribution_label=CONTRIB_NEGATIVE,
                    contribution_rationale=[
                        RATIONALE_STRUCTURE_BREAKDOWN_RISK,
                    ],
                    eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
                    basis=basis,
                )

        # -----------------------------
        # Rule 4: REGIME_LOW → CONTRIB_NEUTRAL
        # -----------------------------
        if regime_level == "REGIME_LOW":
            return V12ContributionSchema.create_contribution_record(
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                contribution_label=CONTRIB_NEUTRAL,
                contribution_rationale=[
                    RATIONALE_LOW_DISTORTION_DENSITY,
                    RATIONALE_OPPORTUNITY_THIN,
                ],
                eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
                basis=basis,
            )

        # -----------------------------
        # Rule 5: REGIME_MEDIUM → Primary alpha zone
        # -----------------------------
        if regime_level == "REGIME_MEDIUM":
            # VOLATILITY_ROLE × D1-D5
            if role_type == "VOLATILITY_ROLE" and distortion_type in [
                "D1_LIQUIDATION",
                "D2_RANGE_STICKINESS",
                "D3_BOOK_HOLLOWING",
                "D4_EVENT_DISTORTION",
                "D5_CORRELATION_DISTORTION",
            ]:
                # ELIGIBLE_CONSIDERATION_ONLY → STRONGLY_POSITIVE
                if eligibility_label == "ELIGIBLE_CONSIDERATION_ONLY":
                    return V12ContributionSchema.create_contribution_record(
                        regime_level=regime_level,
                        role_type=role_type,
                        distortion_type=distortion_type,
                        contribution_label=CONTRIB_STRONGLY_POSITIVE,
                        contribution_rationale=[
                            RATIONALE_DISTORTION_CAPTURE_ZONE,
                            RATIONALE_STRUCTURE_INTELLIGIBLE,
                        ],
                        eligibility_label=eligibility_label,
                        basis=basis,
                    )
                # Other eligibility → POSITIVE
                else:
                    return V12ContributionSchema.create_contribution_record(
                        regime_level=regime_level,
                        role_type=role_type,
                        distortion_type=distortion_type,
                        contribution_label=CONTRIB_POSITIVE,
                        contribution_rationale=[
                            RATIONALE_DISTORTION_CAPTURE_ZONE,
                        ],
                        eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
                        basis=basis,
                    )

            # LIQUIDITY_ROLE × D1/D3 → POSITIVE
            if role_type == "LIQUIDITY_ROLE" and distortion_type in ["D1_LIQUIDATION", "D3_BOOK_HOLLOWING"]:
                return V12ContributionSchema.create_contribution_record(
                    regime_level=regime_level,
                    role_type=role_type,
                    distortion_type=distortion_type,
                    contribution_label=CONTRIB_POSITIVE,
                    contribution_rationale=[
                        RATIONALE_LIQUIDITY_PREMIUM_ZONE,
                    ],
                    eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
                    basis=basis,
                )

            # STABILITY_ROLE → NEUTRAL
            if role_type == "STABILITY_ROLE":
                return V12ContributionSchema.create_contribution_record(
                    regime_level=regime_level,
                    role_type=role_type,
                    distortion_type=distortion_type,
                    contribution_label=CONTRIB_NEUTRAL,
                    contribution_rationale=[
                        RATIONALE_STABILITY_BUFFER_ROLE,
                    ],
                    eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
                    basis=basis,
                )

            # HEDGE_ROLE × D5 → POSITIVE
            if role_type == "HEDGE_ROLE" and distortion_type == "D5_CORRELATION_DISTORTION":
                return V12ContributionSchema.create_contribution_record(
                    regime_level=regime_level,
                    role_type=role_type,
                    distortion_type=distortion_type,
                    contribution_label=CONTRIB_POSITIVE,
                    contribution_rationale=[
                        RATIONALE_HEDGE_ALIGNMENT_ZONE,
                    ],
                    eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
                    basis=basis,
                )

            # GAS_ROLE → NEUTRAL
            if role_type == "GAS_ROLE":
                return V12ContributionSchema.create_contribution_record(
                    regime_level=regime_level,
                    role_type=role_type,
                    distortion_type=distortion_type,
                    contribution_label=CONTRIB_NEUTRAL,
                    contribution_rationale=[
                        RATIONALE_OPERATIONAL_ENABLER_ONLY,
                    ],
                    eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
                    basis=basis,
                )

            # Default MEDIUM case → UNKNOWN
            return V12ContributionSchema.create_contribution_record(
                regime_level=regime_level,
                role_type=role_type,
                distortion_type=distortion_type,
                contribution_label=CONTRIB_UNKNOWN,
                contribution_rationale=[],
                eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
                basis=basis,
            )

        # -----------------------------
        # Default → UNKNOWN
        # -----------------------------
        return V12ContributionSchema.create_contribution_record(
            regime_level=regime_level,
            role_type=role_type,
            distortion_type=distortion_type,
            contribution_label=CONTRIB_UNKNOWN,
            contribution_rationale=[],
            eligibility_label=eligibility_label if eligibility_label != "UNKNOWN" else None,
            basis=basis,
        )

    except Exception as e:
        return V12ContributionSchema.create_error_record(f"exception: {type(e).__name__}")


def build_contribution_cube_v1(
    regime_levels: List[str],
    role_types: List[str],
    distortion_types: List[str],
    eligibility_label: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Build contribution cube for all combinations (for documentation/UI).

    Args:
        regime_levels: List of regime levels
        role_types: List of role types
        distortion_types: List of distortion types
        eligibility_label: Optional eligibility label to apply to all

    Returns:
        List of contribution records (deterministic ordering)
    """
    results = []
    for regime in regime_levels:
        for role in role_types:
            for distortion in distortion_types:
                record = classify_contribution_v1(
                    regime_level=regime,
                    role_type=role,
                    distortion_type=distortion,
                    eligibility_label=eligibility_label,
                )
                results.append(record)
    return results


def contribution_to_explain_signals_v1(contrib_record: Dict[str, Any]) -> List[str]:
    """
    Map contribution label to explanation signals for PR122 integration.

    Args:
        contrib_record: Contribution record

    Returns:
        List of signal type labels
    """
    contribution_label = contrib_record.get("v12_contrib_contribution_label", CONTRIB_UNKNOWN)

    signal_map = {
        CONTRIB_STRONGLY_POSITIVE: ["CONTRIB_ZONE_STRONG_POSITIVE"],
        CONTRIB_POSITIVE: ["CONTRIB_ZONE_POSITIVE"],
        CONTRIB_NEUTRAL: ["CONTRIB_ZONE_NEUTRAL"],
        CONTRIB_NEGATIVE: ["CONTRIB_ZONE_NEGATIVE"],
        CONTRIB_STRONGLY_NEGATIVE: ["CONTRIB_ZONE_STRONG_NEGATIVE"],
        CONTRIB_UNKNOWN: ["CONTRIB_ZONE_UNKNOWN"],
    }

    return signal_map.get(contribution_label, ["CONTRIB_ZONE_UNKNOWN"])


def get_contribution_engine_v1_info() -> Dict[str, Any]:
    """
    Get contribution engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "role_distortion_regime_contribution",
        "input_schema": "regime_level + role_type + distortion_type + eligibility_label",
        "output_schema": "v12_contribution",
        "classification_rules": [
            "invalid_inputs → ERROR + CONTRIB_UNKNOWN",
            "REGIME_CRITICAL → CONTRIB_STRONGLY_NEGATIVE",
            "INELIGIBLE → CONTRIB_NEUTRAL",
            "REGIME_HIGH → CONTRIB_NEGATIVE (mostly), CONTRIB_NEUTRAL for VOLATILITY × D1/D3/D4",
            "REGIME_LOW → CONTRIB_NEUTRAL",
            "REGIME_MEDIUM → Primary alpha zone (++/+/0 by role×distortion)",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_return_guarantees",
            "no_backtest_language",
            "deterministic",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Contribution Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Invalid input → ERROR
    print("Test 1: Invalid input → ERROR")
    result1 = classify_contribution_v1("UNCLASSIFIED", "UNCLASSIFIED", "UNCLASSIFIED")
    print(f"Status: {result1['v12_contrib_status']}")
    print(f"Label: {result1['v12_contrib_contribution_label']}")
    print()

    # Test 2: REGIME_CRITICAL → STRONGLY_NEGATIVE
    print("Test 2: REGIME_CRITICAL → STRONGLY_NEGATIVE")
    result2 = classify_contribution_v1("REGIME_CRITICAL", "VOLATILITY_ROLE", "D1_LIQUIDATION")
    print(f"Label: {result2['v12_contrib_contribution_label']}")
    print(f"Rationale: {result2['v12_contrib_contribution_rationale']}")
    print()

    # Test 3: INELIGIBLE → NEUTRAL
    print("Test 3: INELIGIBLE → NEUTRAL")
    result3 = classify_contribution_v1(
        "REGIME_MEDIUM", "VOLATILITY_ROLE", "D1_LIQUIDATION", eligibility_label="INELIGIBLE"
    )
    print(f"Label: {result3['v12_contrib_contribution_label']}")
    print()

    # Test 4: MEDIUM × VOLATILITY × D1 × ELIGIBLE_CONSIDERATION_ONLY → STRONGLY_POSITIVE
    print("Test 4: MEDIUM × VOLATILITY × D1 × ELIGIBLE_CONSIDERATION_ONLY → STRONGLY_POSITIVE")
    result4 = classify_contribution_v1(
        "REGIME_MEDIUM", "VOLATILITY_ROLE", "D1_LIQUIDATION", eligibility_label="ELIGIBLE_CONSIDERATION_ONLY"
    )
    print(f"Label: {result4['v12_contrib_contribution_label']}")
    print(f"Rationale: {result4['v12_contrib_contribution_rationale']}")
    print()

    # Test 5: REGIME_LOW → NEUTRAL
    print("Test 5: REGIME_LOW → NEUTRAL")
    result5 = classify_contribution_v1("REGIME_LOW", "VOLATILITY_ROLE", "D1_LIQUIDATION")
    print(f"Label: {result5['v12_contrib_contribution_label']}")
    print()

    # Test 6: Build contribution cube (sample)
    print("Test 6: Build contribution cube (sample)")
    cube = build_contribution_cube_v1(
        regime_levels=["REGIME_MEDIUM"],
        role_types=["VOLATILITY_ROLE", "GAS_ROLE"],
        distortion_types=["D1_LIQUIDATION"],
    )
    print(f"Generated {len(cube)} contribution records")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
