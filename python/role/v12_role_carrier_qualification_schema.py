#!/usr/bin/env python3
"""
PR130: v1.2 Role Carrier Qualification Schema v1 (READ-ONLY)

Purpose:
    Define qualification record schema for asset-to-role fit assessment.
    Qualification = Structural fit between asset profile and role requirements.

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No amounts: No numeric values in output
    - No addresses: No 0x... patterns

Qualification Status:
    - QUALIFIED: All axes meet requirements
    - PARTIALLY_QUALIFIED: Some axes meet requirements
    - DISQUALIFIED: No axes meet requirements or critical failure
    - ERROR: Invalid input or processing failure

v12_role_carrier_ Prefix:
    All qualification fields use v12_role_carrier_ prefix.
"""

from typing import Any, Dict, List, Optional


# Qualification status constants
QUALIFIED = "QUALIFIED"
PARTIALLY_QUALIFIED = "PARTIALLY_QUALIFIED"
DISQUALIFIED = "DISQUALIFIED"

VALID_QUALIFICATION_STATUSES = [
    QUALIFIED,
    PARTIALLY_QUALIFIED,
    DISQUALIFIED,
]

# Mode/Status
VALID_MODES = ["ON", "OFF"]
VALID_STATUSES = ["AVAILABLE", "ERROR"]


class V12RoleCarrierQualificationSchema:
    """v1.2 Role Carrier Qualification Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "v12_role_carrier_mode",
        "v12_role_carrier_status",
        "v12_role_carrier_role_type",
        "v12_role_carrier_qualification_status",
        "v12_role_carrier_failed_axes",
        "v12_role_carrier_summary",
        "v12_role_carrier_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v12_role_carrier_warnings",
        "v12_role_carrier_asset_profile_summary",
    ]

    # Valid enum values
    VALID_MODES = VALID_MODES
    VALID_STATUSES = VALID_STATUSES
    VALID_QUALIFICATION_STATUSES = VALID_QUALIFICATION_STATUSES

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty qualification record.

        Returns:
            Empty qualification record
        """
        return {
            "v12_role_carrier_mode": "ON",
            "v12_role_carrier_status": "AVAILABLE",
            "v12_role_carrier_role_type": "UNCLASSIFIED",
            "v12_role_carrier_qualification_status": DISQUALIFIED,
            "v12_role_carrier_failed_axes": [],
            "v12_role_carrier_summary": "empty qualification record with no assessment.",
            "v12_role_carrier_basis": [],
        }

    @staticmethod
    def create_error_record(
        role_type: str = "UNCLASSIFIED",
        error_message: str = "qualification assessment failed.",
    ) -> Dict[str, Any]:
        """
        Create an ERROR qualification record.

        Args:
            role_type: Role type being assessed
            error_message: Error description

        Returns:
            ERROR qualification record
        """
        return {
            "v12_role_carrier_mode": "ON",
            "v12_role_carrier_status": "ERROR",
            "v12_role_carrier_role_type": role_type,
            "v12_role_carrier_qualification_status": DISQUALIFIED,
            "v12_role_carrier_failed_axes": ["all"],
            "v12_role_carrier_summary": error_message,
            "v12_role_carrier_basis": [],
        }

    @staticmethod
    def create_qualification_record(
        role_type: str,
        qualification_status: str,
        failed_axes: List[str],
        basis: Optional[List[str]] = None,
        asset_profile_summary: Optional[str] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a qualification record.

        Args:
            role_type: Role type being assessed
            qualification_status: Qualification status (QUALIFIED/PARTIALLY_QUALIFIED/DISQUALIFIED)
            failed_axes: List of failed axes (empty if QUALIFIED)
            basis: Optional array of field names referenced
            asset_profile_summary: Optional asset profile summary
            warnings: Optional array of warnings

        Returns:
            Qualification record
        """
        # Generate summary
        summary = _generate_summary(role_type, qualification_status, failed_axes)

        record = {
            "v12_role_carrier_mode": "ON",
            "v12_role_carrier_status": "AVAILABLE",
            "v12_role_carrier_role_type": role_type,
            "v12_role_carrier_qualification_status": qualification_status,
            "v12_role_carrier_failed_axes": failed_axes,
            "v12_role_carrier_summary": summary,
            "v12_role_carrier_basis": basis or [],
        }

        if asset_profile_summary:
            record["v12_role_carrier_asset_profile_summary"] = asset_profile_summary

        if warnings:
            record["v12_role_carrier_warnings"] = warnings

        return record


def _generate_summary(
    role_type: str,
    qualification_status: str,
    failed_axes: List[str],
) -> str:
    """
    Generate non-prescriptive summary.

    Args:
        role_type: Role type
        qualification_status: Qualification status
        failed_axes: Failed axes

    Returns:
        Summary text
    """
    if qualification_status == QUALIFIED:
        return f"asset labeled {qualification_status} for {role_type} (all axes meet requirements)."
    elif qualification_status == PARTIALLY_QUALIFIED:
        failed_str = ", ".join(failed_axes) if failed_axes else "unknown"
        return f"asset labeled {qualification_status} for {role_type} (failed axes: {failed_str})."
    elif qualification_status == DISQUALIFIED:
        failed_str = ", ".join(failed_axes) if failed_axes else "unknown"
        return f"asset labeled {qualification_status} for {role_type} (failed axes: {failed_str})."
    else:
        return f"asset qualification status {qualification_status} for {role_type}."


def get_qualification_schema_info() -> Dict[str, Any]:
    """
    Get qualification schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "role_carrier_qualification",
        "valid_modes": V12RoleCarrierQualificationSchema.VALID_MODES,
        "valid_statuses": V12RoleCarrierQualificationSchema.VALID_STATUSES,
        "valid_qualification_statuses": V12RoleCarrierQualificationSchema.VALID_QUALIFICATION_STATUSES,
        "required_fields": V12RoleCarrierQualificationSchema.REQUIRED_FIELDS,
        "optional_fields": V12RoleCarrierQualificationSchema.OPTIONAL_FIELDS,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "no_token_literals",
            "no_amounts",
            "no_addresses",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Role Carrier Qualification Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V12RoleCarrierQualificationSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Create qualified record
    print("Test 2: Create qualified record")
    qualified = V12RoleCarrierQualificationSchema.create_qualification_record(
        role_type="GAS_ROLE",
        qualification_status=QUALIFIED,
        failed_axes=[],
        basis=["asset_profile_observability", "asset_profile_censorship_resistance"],
    )
    print(json.dumps(qualified, indent=2))
    print()

    # Test 3: Create partially qualified record
    print("Test 3: Create partially qualified record")
    partial = V12RoleCarrierQualificationSchema.create_qualification_record(
        role_type="STABILITY_ROLE",
        qualification_status=PARTIALLY_QUALIFIED,
        failed_axes=["liquidatability"],
        basis=["asset_profile_liquidatability"],
    )
    print(json.dumps(partial, indent=2))
    print()

    # Test 4: Create disqualified record
    print("Test 4: Create disqualified record")
    disqualified = V12RoleCarrierQualificationSchema.create_qualification_record(
        role_type="LIQUIDITY_ROLE",
        qualification_status=DISQUALIFIED,
        failed_axes=["observability", "liquidatability"],
        basis=["asset_profile_observability", "asset_profile_liquidatability"],
    )
    print(json.dumps(disqualified, indent=2))
    print()

    # Test 5: Create error record
    print("Test 5: Create error record")
    error = V12RoleCarrierQualificationSchema.create_error_record(
        role_type="GAS_ROLE",
        error_message="test error",
    )
    print(json.dumps(error, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
