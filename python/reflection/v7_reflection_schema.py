#!/usr/bin/env python3
"""
PR70: v0.7 Reflection Schema (READ-ONLY)

Purpose:
    Define schema for reflection records (v7_*).
    Reflection observes interpretation system characteristics.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Interpretation-bound: Only uses interpretation fields as basis

Reflection Definition:
    Reflection = Interpretive System Description

    Reflection observes:
    - What meanings are frequently/rarely observed
    - What combinations have never appeared
    - What the interpretation engine implicitly assumes

    Reflection does NOT:
    - Evaluate (good/bad)
    - Recommend (should/must)
    - Optimize (improve/fix)

v7_ Prefix:
    All reflection fields use v7_ prefix to maintain clear separation
    from v6 interpretation fields.
"""

from typing import Any, Dict, List, Optional


class V7ReflectionSchema:
    """
    v0.7 Reflection Schema definition.

    Reflection records describe interpretation system characteristics
    without evaluation or prescription.
    """

    # Required fields for v7 reflection records
    REQUIRED_FIELDS = [
        "v7_reflection_mode",
        "v7_reflection_status",
        "v7_reflection_tag",
        "v7_reflection_summary",
        "v7_reflection_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v7_reflection_artifacts",
    ]

    # Field types
    FIELD_TYPES = {
        "v7_reflection_mode": str,
        "v7_reflection_status": str,
        "v7_reflection_tag": str,
        "v7_reflection_summary": str,
        "v7_reflection_basis": list,
        "v7_reflection_artifacts": list,
    }

    # Allowed enum values
    ALLOWED_MODES = ["ON", "OFF"]
    ALLOWED_STATUSES = ["AVAILABLE", "UNAVAILABLE"]

    # Allowed basis fields (interpretation-bound)
    ALLOWED_BASIS_FIELDS = [
        "v6_meaning_tag",
        "v6_meaning_status",
        "v6_meaning_factors",
        "v6_meaning_signals",
        "v6_meaning_summary",
        "v6_meaning_basis",
        "pr64_interpretation_analytics",
        "meaning_tag_counts",
        "factor_counts",
        "signal_counts",
        "daily_distributions",
        "transitions",
    ]

    # Forbidden basis fields (v0.4 boundary protection)
    FORBIDDEN_BASIS_FIELDS = [
        "confidence_reason",
        "confidence_reason_version",
        "confidence_reason_generated_at",
        # Direct observation fields (should use interpretation, not raw observation)
        "v5_decision_diff_status",
        "v5_decision_diff_semantics_tag",
        "v5_shadow_decision_action",
    ]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate reflection record structure.

        Warning-only: Returns list of warnings, never raises.

        Args:
            record: Reflection record to validate

        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V7ReflectionSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")
                continue

            # Check field type
            expected_type = V7ReflectionSchema.FIELD_TYPES.get(field)
            if expected_type and not isinstance(record[field], expected_type):
                warnings.append(
                    f"Field '{field}' has wrong type: expected {expected_type.__name__}, "
                    f"got {type(record[field]).__name__}"
                )

        # Check enum values
        if "v7_reflection_mode" in record:
            mode = record["v7_reflection_mode"]
            if mode not in V7ReflectionSchema.ALLOWED_MODES:
                warnings.append(
                    f"Invalid v7_reflection_mode: {mode}. "
                    f"Allowed: {V7ReflectionSchema.ALLOWED_MODES}"
                )

        if "v7_reflection_status" in record:
            status = record["v7_reflection_status"]
            if status not in V7ReflectionSchema.ALLOWED_STATUSES:
                warnings.append(
                    f"Invalid v7_reflection_status: {status}. "
                    f"Allowed: {V7ReflectionSchema.ALLOWED_STATUSES}"
                )

        # Check basis is list of strings
        if "v7_reflection_basis" in record:
            basis = record["v7_reflection_basis"]
            if isinstance(basis, list):
                for item in basis:
                    if not isinstance(item, str):
                        warnings.append(
                            f"v7_reflection_basis contains non-string item: {type(item).__name__}"
                        )
            else:
                warnings.append(
                    f"v7_reflection_basis should be list, got {type(basis).__name__}"
                )

        # Check artifacts is list of strings (if present)
        if "v7_reflection_artifacts" in record:
            artifacts = record["v7_reflection_artifacts"]
            if isinstance(artifacts, list):
                for item in artifacts:
                    if not isinstance(item, str):
                        warnings.append(
                            f"v7_reflection_artifacts contains non-string item: {type(item).__name__}"
                        )
            else:
                warnings.append(
                    f"v7_reflection_artifacts should be list, got {type(artifacts).__name__}"
                )

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty reflection record with safe defaults.

        Returns:
            Empty reflection record dict
        """
        return {
            "v7_reflection_mode": "OFF",
            "v7_reflection_status": "UNAVAILABLE",
            "v7_reflection_tag": "UNCLASSIFIED",
            "v7_reflection_summary": "reflection unavailable.",
            "v7_reflection_basis": [],
            "v7_reflection_artifacts": [],
        }


def validate_basis_fields(basis: List[str]) -> List[str]:
    """
    Validate that basis fields are allowed.

    Warning-only: Returns list of warnings.

    Args:
        basis: List of basis field names

    Returns:
        List of warning messages
    """
    warnings = []

    for field in basis:
        if field in V7ReflectionSchema.FORBIDDEN_BASIS_FIELDS:
            warnings.append(
                f"Forbidden field in basis: {field}. "
                "Reflection must use interpretation fields, not raw observations or v0.4 fields."
            )

    return warnings


def get_schema_info() -> Dict[str, Any]:
    """
    Get schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "version": "v0.7",
        "prefix": "v7_",
        "required_fields": V7ReflectionSchema.REQUIRED_FIELDS,
        "optional_fields": V7ReflectionSchema.OPTIONAL_FIELDS,
        "allowed_modes": V7ReflectionSchema.ALLOWED_MODES,
        "allowed_statuses": V7ReflectionSchema.ALLOWED_STATUSES,
        "allowed_basis_fields": V7ReflectionSchema.ALLOWED_BASIS_FIELDS,
        "forbidden_basis_fields": V7ReflectionSchema.FORBIDDEN_BASIS_FIELDS,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v0.7 Reflection Schema - Self Test")
    print("=" * 60)
    print()

    # Print schema info
    print("Schema Info:")
    print(json.dumps(get_schema_info(), indent=2))
    print()

    # Test empty record creation
    print("Test: Empty record creation")
    empty = V7ReflectionSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test validation
    print("Test: Validation")
    warnings = V7ReflectionSchema.validate_structure(empty)
    if warnings:
        print(f"✗ Empty record has warnings: {warnings}")
    else:
        print("✓ Empty record is valid")
    print()

    # Test invalid record
    print("Test: Invalid record (missing field)")
    invalid = {"v7_reflection_mode": "ON"}
    warnings = V7ReflectionSchema.validate_structure(invalid)
    if warnings:
        print(f"✓ Invalid record detected: {len(warnings)} warnings")
        for w in warnings:
            print(f"  - {w}")
    else:
        print("✗ Invalid record not detected")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
