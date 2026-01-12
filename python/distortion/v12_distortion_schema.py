#!/usr/bin/env python3
"""
PR129: v1.2 Distortion Schema v1 (READ-ONLY)

Purpose:
    Define schema for market structure distortion classification.
    Distortion = Structural label (not signal, not recommendation).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals: No SUI, USDC, BTC, ETH
    - No amounts: No numeric values in output
    - No addresses: No 0x... patterns
    - No distortion coupling: No "D1 therefore act"

Distortion Philosophy:
    Distortion ≠ Signal ≠ Recommendation
    Distortion = Structural label

    This is not instruction. It is failure-mode classification.

v12_distortion_ Prefix:
    All distortion fields use v12_distortion_ prefix for clear separation.

Schema Fields:
    - v12_distortion_mode: ON | OFF
    - v12_distortion_status: AVAILABLE | ERROR | DISABLED
    - v12_distortion_type: D0_NONE | D1_LIQUIDATION | D2_RANGE_STICKINESS |
                          D3_BOOK_HOLLOWING | D4_EVENT_DISTORTION |
                          D5_CORRELATION_DISTORTION | UNCLASSIFIED
    - v12_distortion_summary: Non-prescriptive summary
    - v12_distortion_basis: Array of field names referenced
    - v12_distortion_artifacts: Upstream artifact names (optional)
    - v12_distortion_warnings: Optional array of warnings
"""

from typing import Any, Dict, List, Optional


# Valid enum values
VALID_MODES = ["ON", "OFF"]
VALID_STATUSES = ["AVAILABLE", "ERROR", "DISABLED"]
VALID_DISTORTION_TYPES = [
    "D0_NONE",
    "D1_LIQUIDATION",
    "D2_RANGE_STICKINESS",
    "D3_BOOK_HOLLOWING",
    "D4_EVENT_DISTORTION",
    "D5_CORRELATION_DISTORTION",
    "UNCLASSIFIED",
]

# Distortion type constants
D0_NONE = "D0_NONE"
D1_LIQUIDATION = "D1_LIQUIDATION"
D2_RANGE_STICKINESS = "D2_RANGE_STICKINESS"
D3_BOOK_HOLLOWING = "D3_BOOK_HOLLOWING"
D4_EVENT_DISTORTION = "D4_EVENT_DISTORTION"
D5_CORRELATION_DISTORTION = "D5_CORRELATION_DISTORTION"
DISTORTION_UNCLASSIFIED = "UNCLASSIFIED"


class V12DistortionSchema:
    """v1.2 Distortion Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "v12_distortion_mode",
        "v12_distortion_status",
        "v12_distortion_type",
        "v12_distortion_summary",
        "v12_distortion_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v12_distortion_artifacts",
        "v12_distortion_warnings",
    ]

    # Valid enum values
    VALID_MODES = VALID_MODES
    VALID_STATUSES = VALID_STATUSES
    VALID_DISTORTION_TYPES = VALID_DISTORTION_TYPES

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty distortion record.

        Returns:
            Empty distortion record
        """
        return {
            "v12_distortion_mode": "ON",
            "v12_distortion_status": "AVAILABLE",
            "v12_distortion_type": DISTORTION_UNCLASSIFIED,
            "v12_distortion_summary": "no distortion detection available.",
            "v12_distortion_basis": [],
        }

    @staticmethod
    def create_error_record(error_message: str = "distortion detection failed.") -> Dict[str, Any]:
        """
        Create an ERROR distortion record.

        Args:
            error_message: Error description

        Returns:
            ERROR distortion record
        """
        return {
            "v12_distortion_mode": "ON",
            "v12_distortion_status": "ERROR",
            "v12_distortion_type": DISTORTION_UNCLASSIFIED,
            "v12_distortion_summary": error_message,
            "v12_distortion_basis": [],
        }

    @staticmethod
    def create_distortion_record(
        distortion_type: str,
        basis: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a distortion record.

        Args:
            distortion_type: Distortion type label
            basis: Optional array of field names referenced
            artifacts: Optional array of upstream artifact names
            warnings: Optional array of warnings

        Returns:
            Distortion record
        """
        # Generate summary
        summary = _generate_summary(distortion_type)

        record = {
            "v12_distortion_mode": "ON",
            "v12_distortion_status": "AVAILABLE",
            "v12_distortion_type": distortion_type,
            "v12_distortion_summary": summary,
            "v12_distortion_basis": basis or [],
        }

        if artifacts:
            record["v12_distortion_artifacts"] = artifacts

        if warnings:
            record["v12_distortion_warnings"] = warnings

        return record

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate distortion record structure.

        Args:
            record: Distortion record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V12DistortionSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v12_distortion_mode" in record:
            if record["v12_distortion_mode"] not in V12DistortionSchema.VALID_MODES:
                warnings.append(f"Invalid distortion mode: {record['v12_distortion_mode']}")

        # Validate status
        if "v12_distortion_status" in record:
            if record["v12_distortion_status"] not in V12DistortionSchema.VALID_STATUSES:
                warnings.append(f"Invalid distortion status: {record['v12_distortion_status']}")

        # Validate distortion_type
        if "v12_distortion_type" in record:
            if record["v12_distortion_type"] not in V12DistortionSchema.VALID_DISTORTION_TYPES:
                warnings.append(f"Invalid distortion type: {record['v12_distortion_type']}")

        # Validate basis (must be list)
        if "v12_distortion_basis" in record:
            if not isinstance(record["v12_distortion_basis"], list):
                warnings.append("Basis must be a list")

        return warnings


def _generate_summary(distortion_type: str) -> str:
    """
    Generate non-prescriptive summary.

    Args:
        distortion_type: Distortion type label

    Returns:
        Summary text
    """
    return f"distortion label classified as {distortion_type} based on labeled activity patterns."


def get_distortion_schema_info() -> Dict[str, Any]:
    """
    Get distortion schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "distortion_classification",
        "valid_modes": V12DistortionSchema.VALID_MODES,
        "valid_statuses": V12DistortionSchema.VALID_STATUSES,
        "valid_distortion_types": V12DistortionSchema.VALID_DISTORTION_TYPES,
        "required_fields": V12DistortionSchema.REQUIRED_FIELDS,
        "optional_fields": V12DistortionSchema.OPTIONAL_FIELDS,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "no_token_literals",
            "no_amounts",
            "no_addresses",
            "no_distortion_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Distortion Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V12DistortionSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Validate empty record
    print("Test 2: Validate empty record")
    warnings = V12DistortionSchema.validate_structure(empty)
    print(f"Warnings: {warnings}")
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V12DistortionSchema.create_error_record("test error")
    print(json.dumps(error, indent=2))
    print()

    # Test 4: Create full distortion record
    print("Test 4: Create full distortion record")
    distortion = V12DistortionSchema.create_distortion_record(
        distortion_type=D4_EVENT_DISTORTION,
        basis=["event_activity_present", "v11_regime_level"],
        artifacts=["v109_analytics", "v110_regime"],
    )
    print(json.dumps(distortion, indent=2))
    print()

    # Test 5: Validate full record
    print("Test 5: Validate full record")
    warnings = V12DistortionSchema.validate_structure(distortion)
    print(f"Warnings: {warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
