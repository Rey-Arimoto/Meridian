#!/usr/bin/env python3
"""
PR143: v1.3 Execution Gate (Always-Blocked) v1 (READ-ONLY)

Purpose:
    Define schema for "execution gate" that enumerates structural block reasons.
    This gate ALWAYS blocks execution. It explains why execution is not reachable.

Gate Philosophy:
    Gate ≠ Allow
    Gate = Explain why execution is not reachable (yet)
    Execution is defined by prohibition first.

Record Prefix:
    v13_gate_

Required Fields:
    v13_gate_version: "v1.3"
    v13_gate_status: AVAILABLE | ERROR
    v13_gate_mode: READ_ONLY
    v13_gate_summary: Non-prescriptive summary
    v13_gate_gate_state: BLOCKED (constant, always)
    v13_gate_block_reasons: List of reason labels
    v13_gate_reason_details: List of dicts (optional; label-only)
    v13_gate_basis: List of strings (no numbers)
    v13_gate_artifacts: List of strings
    v13_gate_warnings: List of strings

Optional Fields:
    v13_gate_inputs_present: Dict of booleans (presence flags only)
    v13_gate_notes: String (guarded)

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - Always BLOCKED: Never produces "ALLOW" or "ready to execute"
    - Label-only: No numeric values, no token literals
    - No prescriptive language: No "should", "must", "need to"
    - No action vocabulary: No execute, sign, transfer, swap, buy, sell
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Gate version
GATE_VERSION_V1_3 = "v1.3"

# Gate status constants
GATE_STATUS_AVAILABLE = "AVAILABLE"
GATE_STATUS_ERROR = "ERROR"

# Gate mode constants
GATE_MODE_READ_ONLY = "READ_ONLY"

# Gate state constants (ALWAYS BLOCKED)
GATE_STATE_BLOCKED = "BLOCKED"

# Block reason constants
REASON_INVALID_DRAFT = "REASON_INVALID_DRAFT"
REASON_NO_ACTION_SHAPE = "REASON_NO_ACTION_SHAPE"
REASON_HUMAN_REVIEW_REQUIRED = "REASON_HUMAN_REVIEW_REQUIRED"
REASON_SIMULATION_ONLY = "REASON_SIMULATION_ONLY"
REASON_CONSIDERATION_ONLY = "REASON_CONSIDERATION_ONLY"
REASON_HARD_CONSTRAINT = "REASON_HARD_CONSTRAINT"
REASON_SUPPRESSED = "REASON_SUPPRESSED"
REASON_MISSING_INPUTS = "REASON_MISSING_INPUTS"
REASON_DRAFT_WARNINGS = "REASON_DRAFT_WARNINGS"
REASON_NO_EXECUTION_LOGIC = "REASON_NO_EXECUTION_LOGIC"


class V13ExecutionGateSchema:
    """Schema for execution gate records."""

    # Valid statuses
    VALID_STATUSES = [
        GATE_STATUS_AVAILABLE,
        GATE_STATUS_ERROR,
    ]

    # Valid modes
    VALID_MODES = [
        GATE_MODE_READ_ONLY,
    ]

    # Valid gate states (only BLOCKED)
    VALID_GATE_STATES = [
        GATE_STATE_BLOCKED,
    ]

    # Valid block reasons
    VALID_BLOCK_REASONS = [
        REASON_INVALID_DRAFT,
        REASON_NO_ACTION_SHAPE,
        REASON_HUMAN_REVIEW_REQUIRED,
        REASON_SIMULATION_ONLY,
        REASON_CONSIDERATION_ONLY,
        REASON_HARD_CONSTRAINT,
        REASON_SUPPRESSED,
        REASON_MISSING_INPUTS,
        REASON_DRAFT_WARNINGS,
        REASON_NO_EXECUTION_LOGIC,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "v13_gate_version",
        "v13_gate_status",
        "v13_gate_mode",
        "v13_gate_summary",
        "v13_gate_gate_state",
        "v13_gate_block_reasons",
        "v13_gate_reason_details",
        "v13_gate_basis",
        "v13_gate_artifacts",
        "v13_gate_warnings",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v13_gate_inputs_present",
        "v13_gate_notes",
    ]

    @staticmethod
    def create_gate_record(
        version: str = GATE_VERSION_V1_3,
        status: str = GATE_STATUS_AVAILABLE,
        mode: str = GATE_MODE_READ_ONLY,
        summary: str = "",
        gate_state: str = GATE_STATE_BLOCKED,
        block_reasons: Optional[List[str]] = None,
        reason_details: Optional[List[Dict[str, Any]]] = None,
        basis: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        inputs_present: Optional[Dict[str, bool]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create execution gate record.

        Args:
            version: Gate version (default "v1.3")
            status: AVAILABLE | ERROR
            mode: READ_ONLY
            summary: Non-prescriptive summary
            gate_state: BLOCKED (constant, always)
            block_reasons: List of reason labels
            reason_details: List of dicts (label-only)
            basis: List of strings (no numbers)
            artifacts: List of strings
            warnings: List of strings
            inputs_present: Optional dict of booleans
            notes: Optional string (guarded)

        Returns:
            Execution gate record
        """
        record = {
            "v13_gate_version": version,
            "v13_gate_status": status,
            "v13_gate_mode": mode,
            "v13_gate_summary": summary,
            "v13_gate_gate_state": gate_state,
            "v13_gate_block_reasons": block_reasons if block_reasons else [],
            "v13_gate_reason_details": reason_details if reason_details else [],
            "v13_gate_basis": basis if basis else [],
            "v13_gate_artifacts": artifacts if artifacts else [],
            "v13_gate_warnings": warnings if warnings else [],
        }

        # Add optional fields if provided
        if inputs_present is not None:
            record["v13_gate_inputs_present"] = inputs_present

        if notes is not None:
            record["v13_gate_notes"] = notes

        return record

    @staticmethod
    def create_error_record(
        summary: str = "execution gate generation failed.",
        block_reasons: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create error record.

        Args:
            summary: Error summary
            block_reasons: Block reasons (includes REASON_INVALID_DRAFT)

        Returns:
            Error record
        """
        if block_reasons is None:
            block_reasons = [REASON_INVALID_DRAFT]
        elif REASON_INVALID_DRAFT not in block_reasons:
            block_reasons = [REASON_INVALID_DRAFT] + block_reasons

        return V13ExecutionGateSchema.create_gate_record(
            status=GATE_STATUS_ERROR,
            summary=summary,
            gate_state=GATE_STATE_BLOCKED,
            block_reasons=block_reasons,
            reason_details=[],
            basis=[],
            artifacts=[],
            warnings=[],
        )

    @staticmethod
    def validate_gate_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate execution gate record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V13ExecutionGateSchema.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate version
        version = record.get("v13_gate_version")
        if version != GATE_VERSION_V1_3:
            errors.append(f"invalid version: {version} (expected {GATE_VERSION_V1_3})")

        # Validate status
        status = record.get("v13_gate_status")
        if status not in V13ExecutionGateSchema.VALID_STATUSES:
            errors.append(f"invalid status: {status}")

        # Validate mode
        mode = record.get("v13_gate_mode")
        if mode not in V13ExecutionGateSchema.VALID_MODES:
            errors.append(f"invalid mode: {mode}")

        # Validate gate_state (MUST be BLOCKED)
        gate_state = record.get("v13_gate_gate_state")
        if gate_state not in V13ExecutionGateSchema.VALID_GATE_STATES:
            errors.append(f"invalid gate_state: {gate_state} (must be BLOCKED)")

        # Validate types
        if not isinstance(record.get("v13_gate_summary"), str):
            errors.append("summary must be string")

        if not isinstance(record.get("v13_gate_block_reasons"), list):
            errors.append("block_reasons must be list")

        if not isinstance(record.get("v13_gate_reason_details"), list):
            errors.append("reason_details must be list")

        if not isinstance(record.get("v13_gate_basis"), list):
            errors.append("basis must be list")

        if not isinstance(record.get("v13_gate_artifacts"), list):
            errors.append("artifacts must be list")

        if not isinstance(record.get("v13_gate_warnings"), list):
            errors.append("warnings must be list")

        # Validate block_reasons (at least one reason required)
        block_reasons = record.get("v13_gate_block_reasons", [])
        if isinstance(block_reasons, list) and len(block_reasons) == 0:
            errors.append("block_reasons must contain at least one reason")

        # Validate block_reasons are valid constants
        for reason in block_reasons:
            if reason not in V13ExecutionGateSchema.VALID_BLOCK_REASONS:
                errors.append(f"invalid block reason: {reason}")

        return errors


def get_gate_schema_info() -> Dict[str, Any]:
    """
    Get execution gate schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.3",
        "schema_type": "execution_gate",
        "record_prefix": "v13_gate_",
        "valid_statuses": V13ExecutionGateSchema.VALID_STATUSES,
        "valid_modes": V13ExecutionGateSchema.VALID_MODES,
        "valid_gate_states": V13ExecutionGateSchema.VALID_GATE_STATES,
        "valid_block_reasons": V13ExecutionGateSchema.VALID_BLOCK_REASONS,
        "philosophy": "Gate ≠ Allow. Gate = Explain why execution is not reachable (yet)",
        "constitutional_guarantees": [
            "READ-ONLY",
            "always_blocked",
            "no_execution",
            "no_signing",
            "no_tx_building",
            "no_allow_state",
            "label_only",
            "no_numeric_values",
            "no_token_literals",
            "no_prescriptive_language",
            "no_action_vocabulary",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.3 Execution Gate Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create valid gate record
    print("Test 1: Create valid gate record")
    record1 = V13ExecutionGateSchema.create_gate_record(
        status=GATE_STATUS_AVAILABLE,
        summary="execution gate produced. state blocked. reasons enumerated.",
        gate_state=GATE_STATE_BLOCKED,
        block_reasons=[REASON_SIMULATION_ONLY, REASON_NO_EXECUTION_LOGIC],
        basis=["v13_execution_draft"],
    )
    errors1 = V13ExecutionGateSchema.validate_gate_record(record1)
    print(f"Valid record errors: {len(errors1)}")
    if errors1:
        for e in errors1:
            print(f"  - {e}")
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    record2 = V13ExecutionGateSchema.create_error_record(
        summary="execution gate generation failed: invalid draft."
    )
    errors2 = V13ExecutionGateSchema.validate_gate_record(record2)
    print(f"Error record status: {record2['v13_gate_status']}")
    print(f"Error record gate_state: {record2['v13_gate_gate_state']}")
    print(f"Error record errors: {len(errors2)}")
    print()

    # Test 3: Invalid record (missing field)
    print("Test 3: Invalid record (missing field)")
    record3 = {
        "v13_gate_version": "v1.3",
        "v13_gate_status": GATE_STATUS_AVAILABLE,
    }
    errors3 = V13ExecutionGateSchema.validate_gate_record(record3)
    print(f"Invalid record errors: {len(errors3)}")
    if errors3:
        for e in errors3[:3]:
            print(f"  - {e}")
    print()

    # Test 4: Get schema info
    print("Test 4: Get schema info")
    info = get_gate_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
