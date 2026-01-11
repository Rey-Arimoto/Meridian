#!/usr/bin/env python3
"""
PR104: v1.0 Execution Simulation Schema (READ-ONLY)

Purpose:
    Define schema for v1.0 execution simulation records.
    Simulation = Plan Applicability Scan (not execution).

Constitutional Constraints:
    - READ-ONLY: No execution logic or trading
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - No amounts: No numeric values, prices, quantities
    - No token literals: No SUI, USDC, BTC, etc.
    - No addresses: No wallet/contract addresses

Simulation Definition:
    Simulation Record = Plan Applicability Description

    Based on plan (v10_plan), describe how constraints affect
    plan applicability.

    Simulation is NOT:
    - Execution (no trading, no wallet, no transactions)
    - PnL calculation (no profit/loss)
    - Evaluation (no good/bad judgment)
    - Optimization (no improvement suggestions)

Schema Fields (v10_simulation_ prefix):
    - v10_simulation_mode: ON | OFF
    - v10_simulation_status: AVAILABLE | UNAVAILABLE
    - v10_simulation_type: Simulation type (non-evaluative)
    - v10_simulation_summary: Non-evaluative simulation description
    - v10_simulation_basis: Array of field names referenced
    - v10_simulation_artifacts: Array of artifact names (optional)
    - v10_simulation_trace: Array of simulation events (optional)

Trace Event Structure:
    - event_type: Type of event
    - event_summary: Non-evaluative event description
    - event_basis: Array of field names referenced in this event
"""

from typing import Any, Dict, List


class V10ExecutionSimulationSchema:
    """v1.0 Execution Simulation Schema Definition."""

    # Required fields in all simulation records
    REQUIRED_FIELDS = [
        "v10_simulation_mode",
        "v10_simulation_status",
        "v10_simulation_type",
        "v10_simulation_summary",
        "v10_simulation_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v10_simulation_artifacts",
        "v10_simulation_trace",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE"]

    # Valid simulation types (non-evaluative)
    VALID_SIMULATION_TYPES = [
        "PLAN_APPLICABILITY_SCAN",
        "UNCLASSIFIED",
    ]

    # Valid trace event types
    VALID_EVENT_TYPES = [
        "CONSTRAINT_APPLIED",
        "PLAN_APPLICABLE",
        "PLAN_NOT_APPLIED",
        "WINDOW_ADVANCED",
    ]

    # Allowed basis fields (v10 plan fields)
    ALLOWED_BASIS_FIELDS = [
        # v10 plan fields
        "v10_plan_mode",
        "v10_plan_status",
        "v10_plan_type",
        "v10_plan_description",
        "v10_plan_constraints",
        "v10_plan_basis",
        "v10_plan_artifacts",
    ]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate simulation record structure.

        Args:
            record: Simulation record to validate

        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V10ExecutionSimulationSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Check mode enum
        if "v10_simulation_mode" in record:
            if record["v10_simulation_mode"] not in V10ExecutionSimulationSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v10_simulation_mode: {record['v10_simulation_mode']}"
                )

        # Check status enum
        if "v10_simulation_status" in record:
            if record["v10_simulation_status"] not in V10ExecutionSimulationSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v10_simulation_status: {record['v10_simulation_status']}"
                )

        # Check simulation type enum
        if "v10_simulation_type" in record:
            if record["v10_simulation_type"] not in V10ExecutionSimulationSchema.VALID_SIMULATION_TYPES:
                warnings.append(
                    f"Invalid v10_simulation_type: {record['v10_simulation_type']}"
                )

        # Check basis is list
        if "v10_simulation_basis" in record:
            if not isinstance(record["v10_simulation_basis"], list):
                warnings.append(
                    f"v10_simulation_basis must be list, got {type(record['v10_simulation_basis'])}"
                )

        # Check artifacts is list (if present)
        if "v10_simulation_artifacts" in record:
            if not isinstance(record["v10_simulation_artifacts"], list):
                warnings.append(
                    f"v10_simulation_artifacts must be list, got {type(record['v10_simulation_artifacts'])}"
                )

        # Check trace is list (if present)
        if "v10_simulation_trace" in record:
            if not isinstance(record["v10_simulation_trace"], list):
                warnings.append(
                    f"v10_simulation_trace must be list, got {type(record['v10_simulation_trace'])}"
                )

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty simulation record with safe defaults.

        Returns:
            Empty simulation record
        """
        return {
            "v10_simulation_mode": "OFF",
            "v10_simulation_status": "UNAVAILABLE",
            "v10_simulation_type": "UNCLASSIFIED",
            "v10_simulation_summary": "simulation unavailable.",
            "v10_simulation_basis": [],
            "v10_simulation_artifacts": [],
            "v10_simulation_trace": [],
        }

    @staticmethod
    def create_trace_event(
        event_type: str,
        event_summary: str,
        event_basis: List[str],
    ) -> Dict[str, Any]:
        """
        Create trace event.

        Args:
            event_type: Type of event
            event_summary: Non-evaluative event description
            event_basis: Array of field names referenced

        Returns:
            Trace event dict
        """
        return {
            "event_type": event_type,
            "event_summary": event_summary,
            "event_basis": event_basis,
        }


def validate_simulation_basis_fields(basis: List[str]) -> List[str]:
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
        if field not in V10ExecutionSimulationSchema.ALLOWED_BASIS_FIELDS:
            warnings.append(f"Simulation basis field '{field}' not in allowed v10 plan fields")

    return warnings


def get_simulation_schema_info() -> Dict[str, Any]:
    """
    Get simulation schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "execution_simulation",
        "required_fields": V10ExecutionSimulationSchema.REQUIRED_FIELDS,
        "optional_fields": V10ExecutionSimulationSchema.OPTIONAL_FIELDS,
        "valid_modes": V10ExecutionSimulationSchema.VALID_MODES,
        "valid_statuses": V10ExecutionSimulationSchema.VALID_STATUSES,
        "valid_simulation_types": V10ExecutionSimulationSchema.VALID_SIMULATION_TYPES,
        "valid_event_types": V10ExecutionSimulationSchema.VALID_EVENT_TYPES,
        "allowed_basis_fields": V10ExecutionSimulationSchema.ALLOWED_BASIS_FIELDS,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Execution Simulation Schema - Self Test")
    print("=" * 60)
    print()

    # Print schema info
    print("Schema Info:")
    print(json.dumps(get_simulation_schema_info(), indent=2))
    print()

    # Test empty record
    print("Empty Record:")
    empty = V10ExecutionSimulationSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Validate empty record
    print("Validation:")
    warnings = V10ExecutionSimulationSchema.validate_structure(empty)
    if warnings:
        print(f"✗ Warnings: {warnings}")
    else:
        print("✓ Empty record is valid")
    print()

    # Test trace event
    print("Trace Event:")
    event = V10ExecutionSimulationSchema.create_trace_event(
        "CONSTRAINT_APPLIED",
        "dry run constraint applied",
        ["v10_plan_constraints"]
    )
    print(json.dumps(event, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
