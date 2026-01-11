#!/usr/bin/env python3
"""
PR100: v1.0 Execution Schema (READ-ONLY)

Purpose:
    Define schema for v1.0 execution records.
    Execution = Executability Description (not trading).

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Boundary-bound: Only uses v6/v7/v8/v9 fields as basis

Execution Definition:
    Execution Record = Description of executability

    Based on observation/interpretation/reflection/blindspot/boundary,
    generate a record describing execution intent.

    Execution is NOT:
    - Trading (swap, transfer, send, approve, sign)
    - Position changes, fund movement, rebalancing
    - Recommendations (should/must)
    - Profit/loss evaluation
    - Scoring, ranking, optimization

Schema Fields (v10_ prefix):
    - v10_execution_mode: ON | OFF
    - v10_execution_status: AVAILABLE | UNAVAILABLE
    - v10_execution_intent: Structural execution intent type (non-evaluative)
    - v10_execution_permission: Execution permission type
    - v10_execution_summary: Non-evaluative execution description
    - v10_execution_basis: Array of field names referenced
    - v10_execution_artifacts: Array of artifact names referenced (optional)
    - v10_execution_constraints: Execution constraints (optional)
"""

from typing import Any, Dict, List


class V10ExecutionSchema:
    """v1.0 Execution Schema Definition."""

    # Required fields in all execution records
    REQUIRED_FIELDS = [
        "v10_execution_mode",
        "v10_execution_status",
        "v10_execution_intent",
        "v10_execution_permission",
        "v10_execution_summary",
        "v10_execution_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v10_execution_artifacts",
        "v10_execution_constraints",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE"]

    # Valid execution intent types (non-evaluative)
    VALID_INTENTS = [
        "NONE",
        "MAINTENANCE",
        "REBALANCE_INTENT",
        "HEDGE_INTENT",
        "LIQUIDITY_INTENT",
        "UNCLASSIFIED",
    ]

    # Valid execution permission types
    VALID_PERMISSIONS = [
        "UNKNOWN",
        "DRY_RUN_ONLY",
        "HOLD",
        "ALLOW",
    ]

    # Allowed basis fields (v6/v7/v8/v9 only - higher layers)
    ALLOWED_BASIS_FIELDS = [
        # v9 boundary fields (PR90-91)
        "v9_boundary_type",
        "v9_boundary_description",
        "v9_boundary_basis",
        "v9_boundary_artifacts",
        "v9_boundary_mode",
        "v9_boundary_status",
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
        Validate execution record structure.

        Args:
            record: Execution record to validate

        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V10ExecutionSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Check mode enum
        if "v10_execution_mode" in record:
            if record["v10_execution_mode"] not in V10ExecutionSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v10_execution_mode: {record['v10_execution_mode']}"
                )

        # Check status enum
        if "v10_execution_status" in record:
            if record["v10_execution_status"] not in V10ExecutionSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v10_execution_status: {record['v10_execution_status']}"
                )

        # Check intent enum
        if "v10_execution_intent" in record:
            if record["v10_execution_intent"] not in V10ExecutionSchema.VALID_INTENTS:
                warnings.append(
                    f"Invalid v10_execution_intent: {record['v10_execution_intent']}"
                )

        # Check permission enum
        if "v10_execution_permission" in record:
            if record["v10_execution_permission"] not in V10ExecutionSchema.VALID_PERMISSIONS:
                warnings.append(
                    f"Invalid v10_execution_permission: {record['v10_execution_permission']}"
                )

        # Check basis is list
        if "v10_execution_basis" in record:
            if not isinstance(record["v10_execution_basis"], list):
                warnings.append(
                    f"v10_execution_basis must be list, got {type(record['v10_execution_basis'])}"
                )

        # Check artifacts is list (if present)
        if "v10_execution_artifacts" in record:
            if not isinstance(record["v10_execution_artifacts"], list):
                warnings.append(
                    f"v10_execution_artifacts must be list, got {type(record['v10_execution_artifacts'])}"
                )

        # Check constraints is list (if present)
        if "v10_execution_constraints" in record:
            if not isinstance(record["v10_execution_constraints"], list):
                warnings.append(
                    f"v10_execution_constraints must be list, got {type(record['v10_execution_constraints'])}"
                )

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty execution record with safe defaults.

        Returns:
            Empty execution record
        """
        return {
            "v10_execution_mode": "OFF",
            "v10_execution_status": "UNAVAILABLE",
            "v10_execution_intent": "NONE",
            "v10_execution_permission": "UNKNOWN",
            "v10_execution_summary": "execution unavailable.",
            "v10_execution_basis": [],
            "v10_execution_artifacts": [],
            "v10_execution_constraints": [],
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
        if field not in V10ExecutionSchema.ALLOWED_BASIS_FIELDS:
            warnings.append(f"Basis field '{field}' not in allowed v6/v7/v8/v9 fields")

    return warnings


def get_schema_info() -> Dict[str, Any]:
    """
    Get execution schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "execution",
        "required_fields": V10ExecutionSchema.REQUIRED_FIELDS,
        "optional_fields": V10ExecutionSchema.OPTIONAL_FIELDS,
        "valid_modes": V10ExecutionSchema.VALID_MODES,
        "valid_statuses": V10ExecutionSchema.VALID_STATUSES,
        "valid_intents": V10ExecutionSchema.VALID_INTENTS,
        "valid_permissions": V10ExecutionSchema.VALID_PERMISSIONS,
        "allowed_basis_fields": V10ExecutionSchema.ALLOWED_BASIS_FIELDS,
        "forbidden_basis_fields_v04": V10ExecutionSchema.FORBIDDEN_BASIS_FIELDS_V04,
        "forbidden_basis_fields_v5": V10ExecutionSchema.FORBIDDEN_BASIS_FIELDS_V5,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Execution Schema - Self Test")
    print("=" * 60)
    print()

    # Print schema info
    print("Schema Info:")
    print(json.dumps(get_schema_info(), indent=2))
    print()

    # Test empty record
    print("Empty Record:")
    empty = V10ExecutionSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Validate empty record
    print("Validation:")
    warnings = V10ExecutionSchema.validate_structure(empty)
    if warnings:
        print(f"✗ Warnings: {warnings}")
    else:
        print("✓ Empty record is valid")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
