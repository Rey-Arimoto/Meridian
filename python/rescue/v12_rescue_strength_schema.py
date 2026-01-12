#!/usr/bin/env python3
"""
PR136: v1.2 Rescue Strength Classification Schema (READ-ONLY)

Purpose:
    Define rescue strength classification schema for rescue relation assessment.
    Rescue Strength = Structural label (NOT action, NOT recommendation).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: Use observational language
    - No numeric patterns: No digits, %
    - No token literals: No SUI, USDC, BTC, ETH
    - No rescue coupling: No "RESCUE_STRONG therefore trade"

Rescue Strength Labels (v1):
    - RESCUE_NONE: No rescue strength (default/blocked)
    - RESCUE_WEAK: Weak rescue strength observed
    - RESCUE_MEDIUM: Medium rescue strength observed
    - RESCUE_STRONG: Strong rescue strength observed (strict conditions)

Rescue Strength ≠ Action
Rescue Strength = Structural label
"""

from typing import Any, Dict, List, Optional


# Rescue strength constants
RESCUE_NONE = "RESCUE_NONE"
RESCUE_WEAK = "RESCUE_WEAK"
RESCUE_MEDIUM = "RESCUE_MEDIUM"
RESCUE_STRONG = "RESCUE_STRONG"

VALID_RESCUE_STRENGTHS = [
    RESCUE_NONE,
    RESCUE_WEAK,
    RESCUE_MEDIUM,
    RESCUE_STRONG,
]


class V12RescueStrengthSchema:
    """
    v1.2 Rescue Strength schema class.

    Defines structural rescue strength classification.
    """

    @staticmethod
    def create_rescue_strength_record(
        rescue_strength: str,
        regime_level: str,
        role_type: str,
        distortion_type: str,
        edge_type: str,
        eligibility_label: str,
        basis: List[str],
        warnings: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a rescue strength record.

        Args:
            rescue_strength: Rescue strength label (RESCUE_NONE/WEAK/MEDIUM/STRONG)
            regime_level: Regime level
            role_type: Role type
            distortion_type: Distortion type
            edge_type: Edge type
            eligibility_label: Eligibility label
            basis: List of basis field names
            warnings: Optional list of warnings
            artifacts: Optional list of artifact labels

        Returns:
            Rescue strength record
        """
        # Generate non-prescriptive summary
        if rescue_strength == RESCUE_NONE:
            summary = f"Rescue strength {rescue_strength} observed for {regime_level} × {role_type} × {distortion_type} × {edge_type}."
        else:
            summary = f"Rescue strength {rescue_strength} may indicate structural pattern for {regime_level} × {role_type} × {distortion_type} × {edge_type}."

        record = {
            "v12_rescue_mode": "READ_ONLY",
            "v12_rescue_status": "AVAILABLE",
            "v12_rescue_strength": rescue_strength,
            "v12_rescue_regime": regime_level,
            "v12_rescue_role": role_type,
            "v12_rescue_distortion": distortion_type,
            "v12_rescue_edge_type": edge_type,
            "v12_rescue_eligibility": eligibility_label,
            "v12_rescue_summary": summary,
            "v12_rescue_basis": basis,
        }

        # Add optional fields
        if warnings:
            record["v12_rescue_warnings"] = warnings
        if artifacts:
            record["v12_rescue_artifacts"] = artifacts

        return record

    @staticmethod
    def create_error_record(
        error_message: str,
        regime_level: Optional[str] = None,
        role_type: Optional[str] = None,
        distortion_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an error record (defensive: returns RESCUE_NONE, not ERROR).

        Args:
            error_message: Error message
            regime_level: Optional regime level
            role_type: Optional role type
            distortion_type: Optional distortion type

        Returns:
            Error record with RESCUE_NONE
        """
        return {
            "v12_rescue_mode": "READ_ONLY",
            "v12_rescue_status": "AVAILABLE",
            "v12_rescue_strength": RESCUE_NONE,
            "v12_rescue_regime": regime_level or "UNCLASSIFIED",
            "v12_rescue_role": role_type or "UNCLASSIFIED",
            "v12_rescue_distortion": distortion_type or "UNCLASSIFIED",
            "v12_rescue_edge_type": "EDGE_NONE",
            "v12_rescue_eligibility": "UNKNOWN",
            "v12_rescue_summary": f"Rescue strength RESCUE_NONE (defensive: {error_message}).",
            "v12_rescue_basis": [],
            "v12_rescue_warnings": [error_message],
        }


def get_rescue_strength_schema_info() -> Dict[str, Any]:
    """
    Get rescue strength schema metadata.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "rescue_strength",
        "prefix": "v12_rescue_",
        "rescue_strengths": VALID_RESCUE_STRENGTHS,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_rescue_coupling",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Rescue Strength Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create rescue strength record
    print("Test 1: Create rescue strength record")
    record = V12RescueStrengthSchema.create_rescue_strength_record(
        rescue_strength=RESCUE_STRONG,
        regime_level="REGIME_MEDIUM",
        role_type="STABILITY_ROLE",
        distortion_type="D1_LIQUIDATION",
        edge_type="EDGE_SHIELD",
        eligibility_label="ELIGIBLE_CONSIDERATION_ONLY",
        basis=["v11_regime_level", "v12_role_carrier_role_type", "v12_distortion_type", "v12_edge_type"],
    )
    print(json.dumps(record, indent=2))
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    error_record = V12RescueStrengthSchema.create_error_record(
        error_message="invalid inputs: regime_level must be classified.",
    )
    print(json.dumps(error_record, indent=2))
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    schema_info = get_rescue_strength_schema_info()
    print(json.dumps(schema_info, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
