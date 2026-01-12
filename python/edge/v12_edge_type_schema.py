#!/usr/bin/env python3
"""
PR135: v1.2 Edge Type Classification Schema (READ-ONLY)

Purpose:
    Define edge type classification schema for regime × role × distortion combinations.
    Edge Type = Structural label (NOT action, NOT recommendation).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: Use observational language
    - No numeric patterns: No digits, %
    - No token literals: No SUI, USDC, BTC, ETH
    - No edge coupling: No "EDGE_AMPLIFY therefore trade"

Edge Type Labels (v1):
    - EDGE_NONE: No edge classification (default/unclassified)
    - EDGE_AMPLIFY: Amplification pattern observed (MEDIUM × VOLATILITY × distortion)
    - EDGE_SHIELD: Shielding pattern observed (CRITICAL/GAS/STABILITY/HEDGE)
    - EDGE_LEAK: Leak pattern observed (HIGH × LIQUIDITY × distortion)
    - EDGE_NEUTRAL: Neutral pattern observed (LOW regime or baseline)

Edge ≠ Action
Edge = Structural label
"""

from typing import Any, Dict, List, Optional


# Edge type constants
EDGE_NONE = "EDGE_NONE"
EDGE_AMPLIFY = "EDGE_AMPLIFY"
EDGE_SHIELD = "EDGE_SHIELD"
EDGE_LEAK = "EDGE_LEAK"
EDGE_NEUTRAL = "EDGE_NEUTRAL"

VALID_EDGE_TYPES = [
    EDGE_NONE,
    EDGE_AMPLIFY,
    EDGE_SHIELD,
    EDGE_LEAK,
    EDGE_NEUTRAL,
]


class V12EdgeTypeSchema:
    """
    v1.2 Edge Type schema class.

    Defines structural edge type classification for regime × role × distortion combinations.
    """

    @staticmethod
    def create_edge_record(
        edge_type: str,
        regime_level: str,
        role_type: str,
        distortion_type: str,
        basis: List[str],
        subtype_label: Optional[str] = None,
        contribution_label: Optional[str] = None,
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an edge type record.

        Args:
            edge_type: Edge type label (EDGE_NONE/AMPLIFY/SHIELD/LEAK/NEUTRAL)
            regime_level: Regime level
            role_type: Role type
            distortion_type: Distortion type
            basis: List of basis field names
            subtype_label: Optional distortion subtype
            contribution_label: Optional contribution label
            artifacts: Optional list of artifact labels
            warnings: Optional list of warnings

        Returns:
            Edge type record
        """
        # Generate non-prescriptive summary
        if edge_type == EDGE_NONE:
            summary = f"Edge type {edge_type} observed for {regime_level} × {role_type} × {distortion_type}."
        else:
            summary = f"Edge type {edge_type} may indicate structural pattern for {regime_level} × {role_type} × {distortion_type}."

        record = {
            "v12_edge_mode": "READ_ONLY",
            "v12_edge_status": "AVAILABLE",
            "v12_edge_type": edge_type,
            "v12_edge_regime": regime_level,
            "v12_edge_role": role_type,
            "v12_edge_distortion": distortion_type,
            "v12_edge_summary": summary,
            "v12_edge_basis": basis,
        }

        # Add optional fields
        if subtype_label and subtype_label != "NONE":
            record["v12_edge_subtype_label"] = subtype_label
        if contribution_label:
            record["v12_edge_contribution_label"] = contribution_label
        if artifacts:
            record["v12_edge_artifacts"] = artifacts
        if warnings:
            record["v12_edge_warnings"] = warnings

        return record

    @staticmethod
    def create_error_record(
        error_message: str,
        regime_level: Optional[str] = None,
        role_type: Optional[str] = None,
        distortion_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an error record.

        Args:
            error_message: Error message
            regime_level: Optional regime level
            role_type: Optional role type
            distortion_type: Optional distortion type

        Returns:
            Error record
        """
        return {
            "v12_edge_mode": "READ_ONLY",
            "v12_edge_status": "ERROR",
            "v12_edge_type": EDGE_NONE,
            "v12_edge_regime": regime_level or "UNCLASSIFIED",
            "v12_edge_role": role_type or "UNCLASSIFIED",
            "v12_edge_distortion": distortion_type or "UNCLASSIFIED",
            "v12_edge_summary": f"Error: {error_message}",
            "v12_edge_basis": [],
            "v12_edge_warnings": [error_message],
        }


def get_edge_type_schema_info() -> Dict[str, Any]:
    """
    Get edge type schema metadata.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "edge_type",
        "prefix": "v12_edge_",
        "edge_types": VALID_EDGE_TYPES,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_edge_coupling",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Edge Type Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create edge record
    print("Test 1: Create edge record")
    record = V12EdgeTypeSchema.create_edge_record(
        edge_type=EDGE_AMPLIFY,
        regime_level="REGIME_MEDIUM",
        role_type="VOLATILITY_ROLE",
        distortion_type="D1_LIQUIDATION",
        basis=["v11_regime_level", "v12_role_carrier_role_type", "v12_distortion_type"],
        subtype_label="D1B_CASCADE_RISK",
    )
    print(json.dumps(record, indent=2))
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    error_record = V12EdgeTypeSchema.create_error_record(
        error_message="invalid inputs: regime_level must be classified.",
    )
    print(json.dumps(error_record, indent=2))
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    schema_info = get_edge_type_schema_info()
    print(json.dumps(schema_info, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
