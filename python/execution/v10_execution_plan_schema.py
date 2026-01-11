#!/usr/bin/env python3
"""
PR102: v1.0 Execution Plan Schema v1 (READ-ONLY)

Purpose:
    Define schema for v1.0 execution plan records.
    Plan = Structural Plan Shape (not trading).

Constitutional Constraints:
    - READ-ONLY: No execution logic or trading
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - No amounts: No numeric values, prices, quantities
    - No token literals: No SUI, USDC, BTC, etc.
    - No addresses: No wallet/contract addresses

Plan Definition:
    Execution Plan = Structural Plan Shape Description

    Based on execution permission (v10), describe the structural
    shape of a plan that could exist.

    Plan is NOT:
    - Trading (swap, transfer, send, approve, sign)
    - Position changes, fund movement
    - Recommendations (should/must)
    - Specific amounts or prices
    - Token names or addresses

Schema Fields (v10_plan_ prefix):
    - v10_plan_mode: ON | OFF
    - v10_plan_status: AVAILABLE | UNAVAILABLE
    - v10_plan_type: Structural plan type (non-evaluative)
    - v10_plan_description: Non-evaluative plan shape description
    - v10_plan_constraints: Structural constraints (time/frequency only)
    - v10_plan_basis: Array of execution field names referenced
    - v10_plan_artifacts: Array of artifact names referenced (optional)
"""

from typing import Any, Dict, List


class V10ExecutionPlanSchema:
    """v1.0 Execution Plan Schema Definition."""

    # Required fields in all plan records
    REQUIRED_FIELDS = [
        "v10_plan_mode",
        "v10_plan_status",
        "v10_plan_type",
        "v10_plan_description",
        "v10_plan_constraints",
        "v10_plan_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v10_plan_artifacts",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE"]

    # Valid plan types (non-evaluative)
    VALID_PLAN_TYPES = [
        "NOOP",
        "MAINTENANCE",
        "REBALANCE",
        "HEDGE",
        "LIQUIDITY",
        "UNCLASSIFIED",
    ]

    # Valid constraint types (structural only, no amounts)
    VALID_CONSTRAINT_TYPES = [
        "time_window",      # e.g., "business_hours_only"
        "frequency_limit",  # e.g., "once_per_day"
        "dry_run_only",     # e.g., "no_live_execution"
        "manual_approval",  # e.g., "requires_manual_approval"
    ]

    # Allowed basis fields (v10 execution fields)
    ALLOWED_BASIS_FIELDS = [
        # v10 execution fields
        "v10_execution_mode",
        "v10_execution_status",
        "v10_execution_intent",
        "v10_execution_permission",
        "v10_execution_summary",
        "v10_execution_basis",
        "v10_execution_artifacts",
        "v10_execution_constraints",
    ]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate plan record structure.

        Args:
            record: Plan record to validate

        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V10ExecutionPlanSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Check mode enum
        if "v10_plan_mode" in record:
            if record["v10_plan_mode"] not in V10ExecutionPlanSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v10_plan_mode: {record['v10_plan_mode']}"
                )

        # Check status enum
        if "v10_plan_status" in record:
            if record["v10_plan_status"] not in V10ExecutionPlanSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v10_plan_status: {record['v10_plan_status']}"
                )

        # Check plan type enum
        if "v10_plan_type" in record:
            if record["v10_plan_type"] not in V10ExecutionPlanSchema.VALID_PLAN_TYPES:
                warnings.append(
                    f"Invalid v10_plan_type: {record['v10_plan_type']}"
                )

        # Check constraints is list
        if "v10_plan_constraints" in record:
            if not isinstance(record["v10_plan_constraints"], list):
                warnings.append(
                    f"v10_plan_constraints must be list, got {type(record['v10_plan_constraints'])}"
                )

        # Check basis is list
        if "v10_plan_basis" in record:
            if not isinstance(record["v10_plan_basis"], list):
                warnings.append(
                    f"v10_plan_basis must be list, got {type(record['v10_plan_basis'])}"
                )

        # Check artifacts is list (if present)
        if "v10_plan_artifacts" in record:
            if not isinstance(record["v10_plan_artifacts"], list):
                warnings.append(
                    f"v10_plan_artifacts must be list, got {type(record['v10_plan_artifacts'])}"
                )

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty plan record with safe defaults.

        Returns:
            Empty plan record
        """
        return {
            "v10_plan_mode": "OFF",
            "v10_plan_status": "UNAVAILABLE",
            "v10_plan_type": "NOOP",
            "v10_plan_description": "plan unavailable.",
            "v10_plan_constraints": [],
            "v10_plan_basis": [],
            "v10_plan_artifacts": [],
        }


def validate_plan_basis_fields(basis: List[str]) -> List[str]:
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
        if field not in V10ExecutionPlanSchema.ALLOWED_BASIS_FIELDS:
            warnings.append(f"Plan basis field '{field}' not in allowed v10 execution fields")

    return warnings


def get_plan_schema_info() -> Dict[str, Any]:
    """
    Get plan schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "execution_plan",
        "required_fields": V10ExecutionPlanSchema.REQUIRED_FIELDS,
        "optional_fields": V10ExecutionPlanSchema.OPTIONAL_FIELDS,
        "valid_modes": V10ExecutionPlanSchema.VALID_MODES,
        "valid_statuses": V10ExecutionPlanSchema.VALID_STATUSES,
        "valid_plan_types": V10ExecutionPlanSchema.VALID_PLAN_TYPES,
        "valid_constraint_types": V10ExecutionPlanSchema.VALID_CONSTRAINT_TYPES,
        "allowed_basis_fields": V10ExecutionPlanSchema.ALLOWED_BASIS_FIELDS,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Execution Plan Schema - Self Test")
    print("=" * 60)
    print()

    # Print schema info
    print("Schema Info:")
    print(json.dumps(get_plan_schema_info(), indent=2))
    print()

    # Test empty record
    print("Empty Record:")
    empty = V10ExecutionPlanSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Validate empty record
    print("Validation:")
    warnings = V10ExecutionPlanSchema.validate_structure(empty)
    if warnings:
        print(f"✗ Warnings: {warnings}")
    else:
        print("✓ Empty record is valid")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
