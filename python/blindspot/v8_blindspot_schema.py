#!/usr/bin/env python3
"""
PR80: v0.8 Blindspot Schema (READ-ONLY)

Purpose:
    Define schema for v0.8 blindspot records.
    Blindspot = Structural Absence Description (not evaluation).

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Interpretation/Reflection-bound: Only uses v6/v7 fields as basis

Blindspot Definition:
    Blindspot observes what the interpretation/reflection systems cannot see:
    - Unseen signal types
    - Unseen factor types
    - Unobserved meaning types
    - Transitions never observed
    - Structures the schema cannot express

    Blindspot is NOT:
    - Evaluation (good/bad)
    - Recommendation (should/must)
    - Optimization (improve/fix)

Schema Fields (v8_ prefix):
    - v8_blindspot_mode: ON | OFF
    - v8_blindspot_status: AVAILABLE | UNAVAILABLE
    - v8_blindspot_tag: Structural absence type (non-evaluative)
    - v8_blindspot_summary: Non-evaluative structural absence description
    - v8_blindspot_basis: Array of field names referenced
    - v8_blindspot_artifacts: Array of artifact names referenced
"""

from typing import Any, Dict, List


class V8BlindspotSchema:
    """v0.8 Blindspot Schema Definition."""

    # Required fields in all blindspot records
    REQUIRED_FIELDS = [
        "v8_blindspot_mode",
        "v8_blindspot_status",
        "v8_blindspot_tag",
        "v8_blindspot_summary",
        "v8_blindspot_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v8_blindspot_artifacts",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE"]

    # Allowed basis fields (interpretation/reflection only)
    ALLOWED_BASIS_FIELDS = [
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
        # v7 reflection fields (PR70-71)
        "v7_reflection_tag",
        "v7_reflection_summary",
        "v7_reflection_basis",
        "v7_reflection_artifacts",
        "v7_reflection_mode",
        "v7_reflection_status",
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
        Validate blindspot record structure.

        Args:
            record: Blindspot record to validate

        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V8BlindspotSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Check mode enum
        if "v8_blindspot_mode" in record:
            if record["v8_blindspot_mode"] not in V8BlindspotSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v8_blindspot_mode: {record['v8_blindspot_mode']}"
                )

        # Check status enum
        if "v8_blindspot_status" in record:
            if record["v8_blindspot_status"] not in V8BlindspotSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v8_blindspot_status: {record['v8_blindspot_status']}"
                )

        # Check basis is list
        if "v8_blindspot_basis" in record:
            if not isinstance(record["v8_blindspot_basis"], list):
                warnings.append(
                    f"v8_blindspot_basis must be list, got {type(record['v8_blindspot_basis'])}"
                )

        # Check artifacts is list (if present)
        if "v8_blindspot_artifacts" in record:
            if not isinstance(record["v8_blindspot_artifacts"], list):
                warnings.append(
                    f"v8_blindspot_artifacts must be list, got {type(record['v8_blindspot_artifacts'])}"
                )

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty blindspot record with safe defaults.

        Returns:
            Empty blindspot record
        """
        return {
            "v8_blindspot_mode": "OFF",
            "v8_blindspot_status": "UNAVAILABLE",
            "v8_blindspot_tag": "UNCLASSIFIED",
            "v8_blindspot_summary": "blindspot unavailable.",
            "v8_blindspot_basis": [],
            "v8_blindspot_artifacts": [],
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
        if field not in V8BlindspotSchema.ALLOWED_BASIS_FIELDS:
            warnings.append(f"Basis field '{field}' not in allowed interpretation/reflection fields")

    return warnings


def get_schema_info() -> Dict[str, Any]:
    """
    Get blindspot schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v0.8",
        "schema_type": "blindspot",
        "required_fields": V8BlindspotSchema.REQUIRED_FIELDS,
        "optional_fields": V8BlindspotSchema.OPTIONAL_FIELDS,
        "valid_modes": V8BlindspotSchema.VALID_MODES,
        "valid_statuses": V8BlindspotSchema.VALID_STATUSES,
        "allowed_basis_fields": V8BlindspotSchema.ALLOWED_BASIS_FIELDS,
        "forbidden_basis_fields_v04": V8BlindspotSchema.FORBIDDEN_BASIS_FIELDS_V04,
        "forbidden_basis_fields_v5": V8BlindspotSchema.FORBIDDEN_BASIS_FIELDS_V5,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v0.8 Blindspot Schema - Self Test")
    print("=" * 60)
    print()

    # Print schema info
    print("Schema Info:")
    print(json.dumps(get_schema_info(), indent=2))
    print()

    # Test empty record
    print("Empty Record:")
    empty = V8BlindspotSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Validate empty record
    print("Validation:")
    warnings = V8BlindspotSchema.validate_structure(empty)
    if warnings:
        print(f"✗ Warnings: {warnings}")
    else:
        print("✓ Empty record is valid")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
