#!/usr/bin/env python3
"""
PR133: v1.2 Role Rescue Relation Schema (READ-ONLY)

Purpose:
    Define ROLE→ROLE structural rescue relation schema.
    Rescue = Structural dependency edge (NOT action, NOT recommendation).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: Use may/can/indicates language
    - No numeric patterns: No digits, %
    - No token literals: No SUI, USDC, BTC, ETH
    - No rescue coupling: No "rescue therefore act"

Edge Types:
    - BUFFER: Role provides stability buffer to target role
    - ANCHOR: Role provides anchoring/reference for target role
    - CONTINUITY: Role provides continuity/operational support
    - ESCAPE: Role provides escape valve for target role
    - DAMPEN: Role dampens volatility for target role
    - UNCLASSIFIED: Relation exists but type unclear

Strength Levels:
    - NONE: No rescue relation present
    - WEAK: Minimal structural support
    - MODERATE: Moderate structural support
    - STRONG: Strong structural support
"""

from typing import Any, Dict, List, Optional


# Edge type constants
RESCUE_EDGE_BUFFER = "BUFFER"
RESCUE_EDGE_ANCHOR = "ANCHOR"
RESCUE_EDGE_CONTINUITY = "CONTINUITY"
RESCUE_EDGE_ESCAPE = "ESCAPE"
RESCUE_EDGE_DAMPEN = "DAMPEN"
RESCUE_EDGE_UNCLASSIFIED = "UNCLASSIFIED"

VALID_EDGE_TYPES = [
    RESCUE_EDGE_BUFFER,
    RESCUE_EDGE_ANCHOR,
    RESCUE_EDGE_CONTINUITY,
    RESCUE_EDGE_ESCAPE,
    RESCUE_EDGE_DAMPEN,
    RESCUE_EDGE_UNCLASSIFIED,
]

# Strength constants
RESCUE_STRENGTH_NONE = "NONE"
RESCUE_STRENGTH_WEAK = "WEAK"
RESCUE_STRENGTH_MODERATE = "MODERATE"
RESCUE_STRENGTH_STRONG = "STRONG"

VALID_STRENGTH_LEVELS = [
    RESCUE_STRENGTH_NONE,
    RESCUE_STRENGTH_WEAK,
    RESCUE_STRENGTH_MODERATE,
    RESCUE_STRENGTH_STRONG,
]

# Role constants (from PR130)
ROLE_GAS = "GAS_ROLE"
ROLE_STABILITY = "STABILITY_ROLE"
ROLE_LIQUIDITY = "LIQUIDITY_ROLE"
ROLE_VOLATILITY = "VOLATILITY_ROLE"
ROLE_HEDGE = "HEDGE_ROLE"
ROLE_UNCLASSIFIED = "UNCLASSIFIED"

VALID_ROLES = [
    ROLE_GAS,
    ROLE_STABILITY,
    ROLE_LIQUIDITY,
    ROLE_VOLATILITY,
    ROLE_HEDGE,
    ROLE_UNCLASSIFIED,
]


class V12RoleRescueRelationSchema:
    """
    v1.2 Role Rescue Relation schema class.

    Defines structural rescue relation from one role to another (ROLE→ROLE edge).
    """

    @staticmethod
    def create_rescue_relation_record(
        role_from: str,
        role_to: str,
        edge_type: str,
        strength: str,
        basis: List[str],
        regime_level: Optional[str] = None,
        distortion_type: Optional[str] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a rescue relation record.

        Args:
            role_from: Source role (rescuer)
            role_to: Target role (rescued)
            edge_type: Edge type (BUFFER/ANCHOR/etc)
            strength: Strength level (NONE/WEAK/MODERATE/STRONG)
            basis: List of basis field names
            regime_level: Optional regime level
            distortion_type: Optional distortion type
            warnings: Optional list of warnings

        Returns:
            Rescue relation record
        """
        # Generate non-prescriptive summary
        if strength == RESCUE_STRENGTH_NONE:
            summary = f"Role rescue relation from {role_from} to {role_to} indicates strength {strength}."
        else:
            summary = f"Role rescue relation from {role_from} to {role_to} may provide edge type {edge_type} with strength {strength}."

        record = {
            "v12_rescue_mode": "READ_ONLY",
            "v12_rescue_status": "AVAILABLE",
            "v12_rescue_relation_type": "ROLE_RESCUE_RELATION",
            "v12_rescue_role_from": role_from,
            "v12_rescue_role_to": role_to,
            "v12_rescue_edge_type": edge_type,
            "v12_rescue_strength": strength,
            "v12_rescue_summary": summary,
            "v12_rescue_basis": basis,
        }

        # Add optional fields
        if regime_level:
            record["v12_rescue_regime_level"] = regime_level
        if distortion_type:
            record["v12_rescue_distortion_type"] = distortion_type
        if warnings:
            record["v12_rescue_warnings"] = warnings

        return record

    @staticmethod
    def create_error_record(
        error_message: str,
        role_from: Optional[str] = None,
        role_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an error record.

        Args:
            error_message: Error message
            role_from: Optional source role
            role_to: Optional target role

        Returns:
            Error record
        """
        return {
            "v12_rescue_mode": "READ_ONLY",
            "v12_rescue_status": "ERROR",
            "v12_rescue_relation_type": "ROLE_RESCUE_RELATION",
            "v12_rescue_role_from": role_from or ROLE_UNCLASSIFIED,
            "v12_rescue_role_to": role_to or ROLE_UNCLASSIFIED,
            "v12_rescue_edge_type": RESCUE_EDGE_UNCLASSIFIED,
            "v12_rescue_strength": RESCUE_STRENGTH_NONE,
            "v12_rescue_summary": f"Error: {error_message}",
            "v12_rescue_basis": [],
            "v12_rescue_warnings": [error_message],
        }


def get_rescue_relation_schema_info() -> Dict[str, Any]:
    """
    Get role rescue relation schema metadata.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "role_rescue_relation",
        "prefix": "v12_rescue_",
        "edge_types": VALID_EDGE_TYPES,
        "strength_levels": VALID_STRENGTH_LEVELS,
        "valid_roles": VALID_ROLES,
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
    print("v1.2 Role Rescue Relation Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create rescue relation record
    print("Test 1: Create rescue relation record")
    record = V12RoleRescueRelationSchema.create_rescue_relation_record(
        role_from=ROLE_STABILITY,
        role_to=ROLE_VOLATILITY,
        edge_type=RESCUE_EDGE_BUFFER,
        strength=RESCUE_STRENGTH_MODERATE,
        basis=["v11_regime_level", "v12_distortion_type"],
        regime_level="REGIME_MEDIUM",
        distortion_type="D1_LIQUIDATION",
    )
    print(json.dumps(record, indent=2))
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    error_record = V12RoleRescueRelationSchema.create_error_record(
        error_message="invalid inputs: role_from must be classified.",
    )
    print(json.dumps(error_record, indent=2))
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    schema_info = get_rescue_relation_schema_info()
    print(json.dumps(schema_info, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
