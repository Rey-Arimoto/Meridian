#!/usr/bin/env python3
"""
PR90: v0.9 Boundary Schema (READ-ONLY)

Purpose:
    Define schema for v0.9 boundary records.
    Boundary = Structural Limit Description (not evaluation).

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Blindspot-bound: Only uses v8 blindspot fields as basis

Boundary Definition:
    Boundary describes where observability stops, not what should be done.

    Boundary classifies blindspots into structural boundary types:
    - SCHEMA_BOUNDARY: Structure cannot be expressed with current schema
    - DATA_BOUNDARY: Required data does not exist or is insufficient
    - ENGINE_BOUNDARY: Interpretation/reflection rules cannot map the structure
    - SAMPLING_BOUNDARY: Structure exists in definition space but not observed
    - TEMPORAL_BOUNDARY: Structure exists but cannot be observed in time window

    Boundary is NOT:
    - Evaluation (good/bad)
    - Recommendation (should/must)
    - Optimization (improve/fix)
    - Root-cause analysis

Schema Fields (v9_ prefix):
    - v9_boundary_mode: ON | OFF
    - v9_boundary_status: AVAILABLE | UNAVAILABLE
    - v9_boundary_type: Structural boundary type (non-evaluative)
    - v9_boundary_description: Non-evaluative structural limit description
    - v9_boundary_basis: Array of field names referenced
    - v9_boundary_artifacts: Array of artifact names referenced
"""

from typing import Any, Dict, List


class V9BoundarySchema:
    """v0.9 Boundary Schema Definition."""

    # Required fields in all boundary records
    REQUIRED_FIELDS = [
        "v9_boundary_mode",
        "v9_boundary_status",
        "v9_boundary_type",
        "v9_boundary_description",
        "v9_boundary_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v9_boundary_artifacts",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE"]

    # Allowed basis fields (blindspot/interpretation/reflection only)
    ALLOWED_BASIS_FIELDS = [
        # v8 blindspot fields (PR80-81)
        "v8_blindspot_tag",
        "v8_blindspot_summary",
        "v8_blindspot_basis",
        "v8_blindspot_artifacts",
        "v8_blindspot_mode",
        "v8_blindspot_status",
        # v7 reflection fields (PR70-71)
        "v7_reflection_tag",
        "v7_reflection_summary",
        "v7_reflection_basis",
        "v7_reflection_artifacts",
        "v7_reflection_mode",
        "v7_reflection_status",
        # v6 interpretation fields (PR60-63)
        "v6_meaning_tag",
        "v6_factors",
        "v6_signals",
        "v6_meaning_summary",
        "v6_interpretation_mode",
        "v6_interpretation_status",
        # PR64 analytics fields
        "pr64_interpretation_analytics",
        "distribution",
        "transitions",
        "meaning_tag_counts",
        "factor_counts",
        "signal_counts",
        "total_records",
    ]

    # Forbidden basis fields (v0.4 boundary)
    FORBIDDEN_BASIS_FIELDS_V04 = [
        "confidence_reason",
        "confidence_reason_version",
        "confidence_detail",
    ]

    # Forbidden basis fields (observation boundary - v5 fields)
    FORBIDDEN_BASIS_FIELDS_V5 = [
        "v5_decision_diff_status",
        "v5_decision_diff_semantics_tag",
        "v5_decision_diff_semantics_detail",
        "v5_shadow_decision_status",
        "v5_primary_decision_status",
    ]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate boundary record structure.

        Args:
            record: Boundary record to validate

        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V9BoundarySchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Check mode enum
        if "v9_boundary_mode" in record:
            if record["v9_boundary_mode"] not in V9BoundarySchema.VALID_MODES:
                warnings.append(
                    f"Invalid v9_boundary_mode: {record['v9_boundary_mode']}"
                )

        # Check status enum
        if "v9_boundary_status" in record:
            if record["v9_boundary_status"] not in V9BoundarySchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v9_boundary_status: {record['v9_boundary_status']}"
                )

        # Check basis is list
        if "v9_boundary_basis" in record:
            if not isinstance(record["v9_boundary_basis"], list):
                warnings.append(
                    f"v9_boundary_basis must be list, got {type(record['v9_boundary_basis'])}"
                )

        # Check artifacts is list (if present)
        if "v9_boundary_artifacts" in record:
            if not isinstance(record["v9_boundary_artifacts"], list):
                warnings.append(
                    f"v9_boundary_artifacts must be list, got {type(record['v9_boundary_artifacts'])}"
                )

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty boundary record with safe defaults.

        Returns:
            Empty boundary record
        """
        return {
            "v9_boundary_mode": "OFF",
            "v9_boundary_status": "UNAVAILABLE",
            "v9_boundary_type": "UNCLASSIFIED",
            "v9_boundary_description": "boundary unavailable.",
            "v9_boundary_basis": [],
            "v9_boundary_artifacts": [],
        }


def validate_basis_fields(basis: List[str]) -> List[str]:
    """
    Validate that basis only references allowed fields.

    Args:
        basis: List of field names

    Returns:
        List of warning messages (empty if valid)
    """
    warnings = []

    for field in basis:
        # Check if field is in allowed list
        if field not in V9BoundarySchema.ALLOWED_BASIS_FIELDS:
            warnings.append(f"Basis field '{field}' not in allowed blindspot/interpretation/reflection fields")

    return warnings


def get_schema_info() -> Dict[str, Any]:
    """
    Get boundary schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v0.9",
        "schema_type": "boundary",
        "required_fields": V9BoundarySchema.REQUIRED_FIELDS,
        "optional_fields": V9BoundarySchema.OPTIONAL_FIELDS,
        "valid_modes": V9BoundarySchema.VALID_MODES,
        "valid_statuses": V9BoundarySchema.VALID_STATUSES,
        "allowed_basis_fields": V9BoundarySchema.ALLOWED_BASIS_FIELDS,
        "forbidden_basis_fields_v04": V9BoundarySchema.FORBIDDEN_BASIS_FIELDS_V04,
        "forbidden_basis_fields_v5": V9BoundarySchema.FORBIDDEN_BASIS_FIELDS_V5,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v0.9 Boundary Schema - Self Test")
    print("=" * 60)
    print()

    # Print schema info
    print("Schema Info:")
    print(json.dumps(get_schema_info(), indent=2))
    print()

    # Test empty record
    print("Empty Record:")
    empty = V9BoundarySchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Validate empty record
    print("Validation:")
    warnings = V9BoundarySchema.validate_structure(empty)
    if warnings:
        print(f"✗ Warnings: {warnings}")
    else:
        print("✓ Empty record is valid")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
