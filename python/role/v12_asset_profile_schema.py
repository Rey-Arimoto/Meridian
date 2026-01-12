#!/usr/bin/env python3
"""
PR130: v1.2 Asset Profile Schema v1 (READ-ONLY)

Purpose:
    Define abstract asset profile with 4 axes for role carrier qualification.
    No token literals - abstract descriptors only.

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No amounts: No numeric values in output
    - No addresses: No 0x... patterns

Asset Profile Philosophy:
    Profile = Abstract asset descriptor
    Profile ≠ Token identity
    Profile describes observable structural properties only

4 Axes:
    - Observability: Can role-bearing properties be structurally observed?
    - Censorship Resistance: Can asset function persist under constraint?
    - Liquidatability: Can role be rebalanced under stress?
    - Dependency: Does it depend on external systems that can fail?

v12_asset_profile_ Prefix:
    All asset profile fields use v12_asset_profile_ prefix.
"""

from typing import Any, Dict, List, Optional


# Valid enum values

# Asset class (single enum - no token literals)
VALID_ASSET_CLASSES = ["ABSTRACT_ASSET"]

# Observability levels
VALID_OBSERVABILITY = ["OBS_LOW", "OBS_MEDIUM", "OBS_HIGH"]
OBS_LOW = "OBS_LOW"
OBS_MEDIUM = "OBS_MEDIUM"
OBS_HIGH = "OBS_HIGH"

# Censorship resistance levels
VALID_CENSORSHIP_RESISTANCE = ["CENS_LOW", "CENS_MEDIUM", "CENS_HIGH"]
CENS_LOW = "CENS_LOW"
CENS_MEDIUM = "CENS_MEDIUM"
CENS_HIGH = "CENS_HIGH"

# Liquidatability levels
VALID_LIQUIDATABILITY = ["LIQ_LOW", "LIQ_MEDIUM", "LIQ_HIGH"]
LIQ_LOW = "LIQ_LOW"
LIQ_MEDIUM = "LIQ_MEDIUM"
LIQ_HIGH = "LIQ_HIGH"

# Dependency levels
VALID_DEPENDENCY = ["DEP_NONE", "DEP_LOW", "DEP_MEDIUM", "DEP_HIGH"]
DEP_NONE = "DEP_NONE"
DEP_LOW = "DEP_LOW"
DEP_MEDIUM = "DEP_MEDIUM"
DEP_HIGH = "DEP_HIGH"

# Mode/Status
VALID_MODES = ["ON", "OFF"]
VALID_STATUSES = ["AVAILABLE", "ERROR"]


class V12AssetProfileSchema:
    """v1.2 Asset Profile Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "asset_profile_mode",
        "asset_profile_status",
        "asset_profile_asset_class",
        "asset_profile_observability",
        "asset_profile_censorship_resistance",
        "asset_profile_liquidatability",
        "asset_profile_dependency",
        "asset_profile_summary",
        "asset_profile_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "asset_profile_dependency_notes",
        "asset_profile_warnings",
    ]

    # Valid enum values
    VALID_MODES = VALID_MODES
    VALID_STATUSES = VALID_STATUSES
    VALID_ASSET_CLASSES = VALID_ASSET_CLASSES
    VALID_OBSERVABILITY = VALID_OBSERVABILITY
    VALID_CENSORSHIP_RESISTANCE = VALID_CENSORSHIP_RESISTANCE
    VALID_LIQUIDATABILITY = VALID_LIQUIDATABILITY
    VALID_DEPENDENCY = VALID_DEPENDENCY

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty asset profile record.

        Returns:
            Empty asset profile record
        """
        return {
            "asset_profile_mode": "ON",
            "asset_profile_status": "AVAILABLE",
            "asset_profile_asset_class": "ABSTRACT_ASSET",
            "asset_profile_observability": OBS_MEDIUM,
            "asset_profile_censorship_resistance": CENS_MEDIUM,
            "asset_profile_liquidatability": LIQ_MEDIUM,
            "asset_profile_dependency": DEP_MEDIUM,
            "asset_profile_summary": "abstract asset profile with default axes.",
            "asset_profile_basis": [],
        }

    @staticmethod
    def create_error_record(error_message: str = "asset profile generation failed.") -> Dict[str, Any]:
        """
        Create an ERROR asset profile record.

        Args:
            error_message: Error description

        Returns:
            ERROR asset profile record
        """
        return {
            "asset_profile_mode": "ON",
            "asset_profile_status": "ERROR",
            "asset_profile_asset_class": "ABSTRACT_ASSET",
            "asset_profile_observability": OBS_LOW,
            "asset_profile_censorship_resistance": CENS_LOW,
            "asset_profile_liquidatability": LIQ_LOW,
            "asset_profile_dependency": DEP_HIGH,
            "asset_profile_summary": error_message,
            "asset_profile_basis": [],
        }

    @staticmethod
    def create_asset_profile(
        observability: str,
        censorship_resistance: str,
        liquidatability: str,
        dependency: str,
        dependency_notes: Optional[List[str]] = None,
        basis: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an asset profile record.

        Args:
            observability: Observability level
            censorship_resistance: Censorship resistance level
            liquidatability: Liquidatability level
            dependency: Dependency level
            dependency_notes: Optional label-only dependency notes
            basis: Optional array of field names referenced
            warnings: Optional array of warnings

        Returns:
            Asset profile record
        """
        # Generate summary
        summary = _generate_summary(observability, censorship_resistance, liquidatability, dependency)

        record = {
            "asset_profile_mode": "ON",
            "asset_profile_status": "AVAILABLE",
            "asset_profile_asset_class": "ABSTRACT_ASSET",
            "asset_profile_observability": observability,
            "asset_profile_censorship_resistance": censorship_resistance,
            "asset_profile_liquidatability": liquidatability,
            "asset_profile_dependency": dependency,
            "asset_profile_summary": summary,
            "asset_profile_basis": basis or [],
        }

        if dependency_notes:
            record["asset_profile_dependency_notes"] = dependency_notes

        if warnings:
            record["asset_profile_warnings"] = warnings

        return record


def _generate_summary(
    observability: str,
    censorship_resistance: str,
    liquidatability: str,
    dependency: str,
) -> str:
    """
    Generate non-prescriptive summary.

    Args:
        observability: Observability level
        censorship_resistance: Censorship resistance level
        liquidatability: Liquidatability level
        dependency: Dependency level

    Returns:
        Summary text
    """
    return f"asset profile labeled: {observability}, {censorship_resistance}, {liquidatability}, {dependency}."


def get_asset_profile_schema_info() -> Dict[str, Any]:
    """
    Get asset profile schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "asset_profile",
        "valid_modes": V12AssetProfileSchema.VALID_MODES,
        "valid_statuses": V12AssetProfileSchema.VALID_STATUSES,
        "valid_asset_classes": V12AssetProfileSchema.VALID_ASSET_CLASSES,
        "valid_observability": V12AssetProfileSchema.VALID_OBSERVABILITY,
        "valid_censorship_resistance": V12AssetProfileSchema.VALID_CENSORSHIP_RESISTANCE,
        "valid_liquidatability": V12AssetProfileSchema.VALID_LIQUIDATABILITY,
        "valid_dependency": V12AssetProfileSchema.VALID_DEPENDENCY,
        "required_fields": V12AssetProfileSchema.REQUIRED_FIELDS,
        "optional_fields": V12AssetProfileSchema.OPTIONAL_FIELDS,
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
    print("v1.2 Asset Profile Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V12AssetProfileSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Create asset profile
    print("Test 2: Create asset profile")
    profile = V12AssetProfileSchema.create_asset_profile(
        observability=OBS_HIGH,
        censorship_resistance=CENS_HIGH,
        liquidatability=LIQ_MEDIUM,
        dependency=DEP_LOW,
        dependency_notes=["MINIMAL_EXTERNAL_DEP"],
        basis=["onchain_observation", "market_structure"],
    )
    print(json.dumps(profile, indent=2))
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V12AssetProfileSchema.create_error_record("test error")
    print(json.dumps(error, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
