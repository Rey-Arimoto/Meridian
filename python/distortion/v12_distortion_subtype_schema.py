#!/usr/bin/env python3
"""
PR134: v1.2 Distortion Subtype Taxonomy & Schema (READ-ONLY)

Purpose:
    Define distortion subtype taxonomy (D1A-D5C) for fine-grained classification.
    Subtypes refine parent distortion types (D1-D5) with qualitative labels.

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: Use observational language
    - No numeric patterns: No digits, %
    - No token literals: No SUI, USDC, BTC, ETH
    - No subtype coupling: No "D1B therefore act"

Distortion Subtype Taxonomy (v1):

D1 (Liquidation) Subtypes:
    - D1A_FORCED_FLOW: Forced liquidation flow detected
    - D1B_CASCADE_RISK: Cascade liquidation risk observed
    - D1C_STRESS_UNWIND: Stress position unwinding observed

D2 (Range Stickiness) Subtypes:
    - D2A_MEAN_REVERT_PRESSURE: Mean reversion pressure observed
    - D2B_RANGE_PINNING: Range pinning behavior observed
    - D2C_BREAKOUT_FAKEOUT: Breakout fakeout pattern observed

D3 (Book Hollowing) Subtypes:
    - D3A_TOP_GAP: Top-of-book gap observed
    - D3B_DEPTH_EVAPORATION: Depth evaporation observed
    - D3C_SPREAD_SHOCK: Spread shock observed

D4 (Event Distortion) Subtypes:
    - D4A_EVENT_SPIKE: Event spike observed
    - D4B_EVENT_AFTERSHOCK: Event aftershock observed
    - D4C_EVENT_SILENCE: Event silence observed

D5 (Correlation Distortion) Subtypes:
    - D5A_COUPLING_TIGHTEN: Coupling tightening observed
    - D5B_DECOUPLING: Decoupling observed
    - D5C_ROTATION_PRESSURE: Rotation pressure observed
"""

from typing import Any, Dict, List, Optional


# D1 (Liquidation) subtypes
SUBTYPE_D1A_FORCED_FLOW = "D1A_FORCED_FLOW"
SUBTYPE_D1B_CASCADE_RISK = "D1B_CASCADE_RISK"
SUBTYPE_D1C_STRESS_UNWIND = "D1C_STRESS_UNWIND"

D1_SUBTYPES = [
    SUBTYPE_D1A_FORCED_FLOW,
    SUBTYPE_D1B_CASCADE_RISK,
    SUBTYPE_D1C_STRESS_UNWIND,
]

# D2 (Range Stickiness) subtypes
SUBTYPE_D2A_MEAN_REVERT_PRESSURE = "D2A_MEAN_REVERT_PRESSURE"
SUBTYPE_D2B_RANGE_PINNING = "D2B_RANGE_PINNING"
SUBTYPE_D2C_BREAKOUT_FAKEOUT = "D2C_BREAKOUT_FAKEOUT"

D2_SUBTYPES = [
    SUBTYPE_D2A_MEAN_REVERT_PRESSURE,
    SUBTYPE_D2B_RANGE_PINNING,
    SUBTYPE_D2C_BREAKOUT_FAKEOUT,
]

# D3 (Book Hollowing) subtypes
SUBTYPE_D3A_TOP_GAP = "D3A_TOP_GAP"
SUBTYPE_D3B_DEPTH_EVAPORATION = "D3B_DEPTH_EVAPORATION"
SUBTYPE_D3C_SPREAD_SHOCK = "D3C_SPREAD_SHOCK"

D3_SUBTYPES = [
    SUBTYPE_D3A_TOP_GAP,
    SUBTYPE_D3B_DEPTH_EVAPORATION,
    SUBTYPE_D3C_SPREAD_SHOCK,
]

# D4 (Event Distortion) subtypes
SUBTYPE_D4A_EVENT_SPIKE = "D4A_EVENT_SPIKE"
SUBTYPE_D4B_EVENT_AFTERSHOCK = "D4B_EVENT_AFTERSHOCK"
SUBTYPE_D4C_EVENT_SILENCE = "D4C_EVENT_SILENCE"

D4_SUBTYPES = [
    SUBTYPE_D4A_EVENT_SPIKE,
    SUBTYPE_D4B_EVENT_AFTERSHOCK,
    SUBTYPE_D4C_EVENT_SILENCE,
]

# D5 (Correlation Distortion) subtypes
SUBTYPE_D5A_COUPLING_TIGHTEN = "D5A_COUPLING_TIGHTEN"
SUBTYPE_D5B_DECOUPLING = "D5B_DECOUPLING"
SUBTYPE_D5C_ROTATION_PRESSURE = "D5C_ROTATION_PRESSURE"

D5_SUBTYPES = [
    SUBTYPE_D5A_COUPLING_TIGHTEN,
    SUBTYPE_D5B_DECOUPLING,
    SUBTYPE_D5C_ROTATION_PRESSURE,
]

# All valid subtypes
VALID_SUBTYPES = D1_SUBTYPES + D2_SUBTYPES + D3_SUBTYPES + D4_SUBTYPES + D5_SUBTYPES

# Parent distortion types (from PR129)
PARENT_D1_LIQUIDATION = "D1_LIQUIDATION"
PARENT_D2_RANGE_STICKINESS = "D2_RANGE_STICKINESS"
PARENT_D3_BOOK_HOLLOWING = "D3_BOOK_HOLLOWING"
PARENT_D4_EVENT_DISTORTION = "D4_EVENT_DISTORTION"
PARENT_D5_CORRELATION_DISTORTION = "D5_CORRELATION_DISTORTION"
PARENT_UNCLASSIFIED = "UNCLASSIFIED"

VALID_PARENT_DISTORTIONS = [
    PARENT_D1_LIQUIDATION,
    PARENT_D2_RANGE_STICKINESS,
    PARENT_D3_BOOK_HOLLOWING,
    PARENT_D4_EVENT_DISTORTION,
    PARENT_D5_CORRELATION_DISTORTION,
    PARENT_UNCLASSIFIED,
]


class V12DistortionSubtypeSchema:
    """
    v1.2 Distortion Subtype schema class.

    Defines fine-grained distortion subtype classification (D1A-D5C).
    """

    @staticmethod
    def create_subtype_record(
        parent_distortion: str,
        subtype_label: str,
        basis: List[str],
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a distortion subtype record.

        Args:
            parent_distortion: Parent distortion type (D1-D5)
            subtype_label: Distortion subtype (D1A-D5C)
            basis: List of basis field names
            artifacts: Optional list of artifact labels
            warnings: Optional list of warnings

        Returns:
            Distortion subtype record
        """
        # Generate non-prescriptive summary
        summary = f"Distortion subtype {subtype_label} observed for parent distortion {parent_distortion}."

        record = {
            "v12_subtype_mode": "READ_ONLY",
            "v12_subtype_status": "AVAILABLE",
            "v12_subtype_parent_distortion": parent_distortion,
            "v12_subtype_label": subtype_label,
            "v12_subtype_summary": summary,
            "v12_subtype_basis": basis,
        }

        # Add optional fields
        if artifacts:
            record["v12_subtype_artifacts"] = artifacts
        if warnings:
            record["v12_subtype_warnings"] = warnings

        return record

    @staticmethod
    def create_error_record(
        error_message: str,
        parent_distortion: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an error record.

        Args:
            error_message: Error message
            parent_distortion: Optional parent distortion

        Returns:
            Error record
        """
        return {
            "v12_subtype_mode": "READ_ONLY",
            "v12_subtype_status": "ERROR",
            "v12_subtype_parent_distortion": parent_distortion or PARENT_UNCLASSIFIED,
            "v12_subtype_label": "UNCLASSIFIED",
            "v12_subtype_summary": f"Error: {error_message}",
            "v12_subtype_basis": [],
            "v12_subtype_warnings": [error_message],
        }


def get_distortion_subtype_schema_info() -> Dict[str, Any]:
    """
    Get distortion subtype schema metadata.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "distortion_subtype",
        "prefix": "v12_subtype_",
        "parent_distortions": VALID_PARENT_DISTORTIONS,
        "subtypes": {
            "D1_LIQUIDATION": D1_SUBTYPES,
            "D2_RANGE_STICKINESS": D2_SUBTYPES,
            "D3_BOOK_HOLLOWING": D3_SUBTYPES,
            "D4_EVENT_DISTORTION": D4_SUBTYPES,
            "D5_CORRELATION_DISTORTION": D5_SUBTYPES,
        },
        "total_subtypes": len(VALID_SUBTYPES),
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_subtype_coupling",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Distortion Subtype Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create subtype record
    print("Test 1: Create subtype record")
    record = V12DistortionSubtypeSchema.create_subtype_record(
        parent_distortion=PARENT_D1_LIQUIDATION,
        subtype_label=SUBTYPE_D1A_FORCED_FLOW,
        basis=["market_cost_regime", "liquidity_regime"],
        artifacts=["forced_flow_signal"],
    )
    print(json.dumps(record, indent=2))
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    error_record = V12DistortionSubtypeSchema.create_error_record(
        error_message="invalid inputs: parent_distortion must be classified.",
    )
    print(json.dumps(error_record, indent=2))
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    schema_info = get_distortion_subtype_schema_info()
    print(f"Total subtypes: {schema_info['total_subtypes']}")
    print(f"D1 subtypes: {schema_info['subtypes']['D1_LIQUIDATION']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
