#!/usr/bin/env python3
"""
PR114: v1.1 Approval Registry Schema (READ-ONLY)

Purpose:
    Schema for manual approval registry records.
    Registry = State Machine (not action/instruction).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No should/must vocabulary
    - "APPROVED" is a state label only (not instruction)

Registry Philosophy:
    Registry ≠ Action
    Registry ≠ Instruction
    Registry = State Transition Record

    Registry records:
    - Current approval state (UNREQUESTED/REQUESTED/APPROVED/REJECTED/EXPIRED)
    - Last event applied (REQUEST/APPROVE/REJECT/EXPIRE/NONE)
    - Approval requirement level (from PR113)

    Registry does NOT:
    - Execute trades
    - Recommend actions
    - Provide instructions
    - Couple APPROVED state to execution

    IMPORTANT: "APPROVED" is a state label only.
    It does NOT mean "execute" or "proceed".

Schema Design:
    - v11_registry_ prefix for registry fields
    - State: UNREQUESTED, REQUESTED, APPROVED, REJECTED, EXPIRED
    - Event: NONE, REQUEST, APPROVE, REJECT, EXPIRE
    - Requirement: NOT_REQUIRED, REQUIRED, REQUIRED_STRICT (from PR113)
    - No timestamps, no IDs, no user identifiers (avoid PII in v1)
"""

from typing import Any, Dict, List, Optional


class V11ApprovalRegistrySchema:
    """
    Schema for v1.1 manual approval registry records.

    Registry = State Machine (not action/instruction).
    """

    # Required fields for registry record
    REQUIRED_FIELDS = [
        "v11_registry_mode",            # Registry mode (ON/OFF)
        "v11_registry_status",          # Registry status (AVAILABLE/UNAVAILABLE/ERROR)
        "v11_registry_requirement",     # Requirement level (from PR113)
        "v11_registry_state",           # Current state
        "v11_registry_event",           # Last event applied
        "v11_registry_summary",         # Summary description
        "v11_registry_basis",           # Basis (field names used)
        "v11_registry_artifacts",       # Artifacts referenced
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v11_registry_warnings",        # Warnings (if any)
        "v11_registry_error_info",      # Error information if status is ERROR
        "v11_registry_metadata",        # Additional metadata
    ]

    # Valid registry modes
    VALID_MODES = ["ON", "OFF"]

    # Valid registry statuses
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]

    # Valid approval requirements (from PR113)
    VALID_REQUIREMENTS = [
        "NOT_REQUIRED",     # No approval needed
        "REQUIRED",         # Approval recommended
        "REQUIRED_STRICT",  # Approval mandatory (hard gate)
    ]

    # Valid approval states
    VALID_STATES = [
        "UNREQUESTED",  # No approval requested yet
        "REQUESTED",    # Approval requested, pending
        "APPROVED",     # Approved (state label only, not instruction)
        "REJECTED",     # Rejected
        "EXPIRED",      # Approval expired
    ]

    # Valid approval events
    VALID_EVENTS = [
        "NONE",     # No event (read-only)
        "REQUEST",  # Request approval
        "APPROVE",  # Approve request
        "REJECT",   # Reject request
        "EXPIRE",   # Expire approval
    ]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate registry record structure.

        Args:
            record: Registry record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V11ApprovalRegistrySchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v11_registry_mode" in record:
            mode = record["v11_registry_mode"]
            if mode not in V11ApprovalRegistrySchema.VALID_MODES:
                warnings.append(
                    f"Invalid v11_registry_mode: {mode}. "
                    f"Must be one of {V11ApprovalRegistrySchema.VALID_MODES}"
                )

        # Validate status
        if "v11_registry_status" in record:
            status = record["v11_registry_status"]
            if status not in V11ApprovalRegistrySchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v11_registry_status: {status}. "
                    f"Must be one of {V11ApprovalRegistrySchema.VALID_STATUSES}"
                )

        # Validate requirement
        if "v11_registry_requirement" in record:
            requirement = record["v11_registry_requirement"]
            if requirement not in V11ApprovalRegistrySchema.VALID_REQUIREMENTS:
                warnings.append(
                    f"Invalid v11_registry_requirement: {requirement}. "
                    f"Must be one of {V11ApprovalRegistrySchema.VALID_REQUIREMENTS}"
                )

        # Validate state
        if "v11_registry_state" in record:
            state = record["v11_registry_state"]
            if state not in V11ApprovalRegistrySchema.VALID_STATES:
                warnings.append(
                    f"Invalid v11_registry_state: {state}. "
                    f"Must be one of {V11ApprovalRegistrySchema.VALID_STATES}"
                )

        # Validate event
        if "v11_registry_event" in record:
            event = record["v11_registry_event"]
            if event not in V11ApprovalRegistrySchema.VALID_EVENTS:
                warnings.append(
                    f"Invalid v11_registry_event: {event}. "
                    f"Must be one of {V11ApprovalRegistrySchema.VALID_EVENTS}"
                )

        # Validate basis
        if "v11_registry_basis" in record:
            basis = record["v11_registry_basis"]
            if not isinstance(basis, list):
                warnings.append("v11_registry_basis must be a list")

        # Validate artifacts
        if "v11_registry_artifacts" in record:
            artifacts = record["v11_registry_artifacts"]
            if not isinstance(artifacts, list):
                warnings.append("v11_registry_artifacts must be a list")

        # Validate summary
        if "v11_registry_summary" in record:
            summary = record["v11_registry_summary"]
            if not isinstance(summary, str):
                warnings.append("v11_registry_summary must be a string")
            elif len(summary) == 0:
                warnings.append("v11_registry_summary must not be empty")

        # Validate warnings (if present)
        if "v11_registry_warnings" in record:
            warns = record["v11_registry_warnings"]
            if not isinstance(warns, list):
                warnings.append("v11_registry_warnings must be a list")

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty registry record with safe defaults.

        Returns:
            Empty registry record (unavailable state)
        """
        return {
            "v11_registry_mode": "OFF",
            "v11_registry_status": "UNAVAILABLE",
            "v11_registry_requirement": "REQUIRED_STRICT",
            "v11_registry_state": "UNREQUESTED",
            "v11_registry_event": "NONE",
            "v11_registry_summary": "registry unavailable. defaulting to unrequested state.",
            "v11_registry_basis": [],
            "v11_registry_artifacts": [],
            "v11_registry_warnings": [],
        }

    @staticmethod
    def create_registry_record(
        requirement: str,
        state: str,
        event: str,
        summary: str,
        basis: List[str],
        artifacts: List[str],
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create registry record.

        Args:
            requirement: Approval requirement (NOT_REQUIRED/REQUIRED/REQUIRED_STRICT)
            state: Approval state (UNREQUESTED/REQUESTED/APPROVED/REJECTED/EXPIRED)
            event: Event applied (NONE/REQUEST/APPROVE/REJECT/EXPIRE)
            summary: Human-readable summary
            basis: List of field names that informed decision
            artifacts: List of artifact references
            warnings: Optional list of warnings

        Returns:
            Registry record
        """
        record = {
            "v11_registry_mode": "ON",
            "v11_registry_status": "AVAILABLE",
            "v11_registry_requirement": requirement,
            "v11_registry_state": state,
            "v11_registry_event": event,
            "v11_registry_summary": summary,
            "v11_registry_basis": basis,
            "v11_registry_artifacts": artifacts,
        }

        if warnings:
            record["v11_registry_warnings"] = warnings

        return record

    @staticmethod
    def create_error_record(
        error_info: str,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create error registry record.

        Args:
            error_info: Error information
            warnings: Optional list of warnings

        Returns:
            Error registry record
        """
        record = {
            "v11_registry_mode": "ON",
            "v11_registry_status": "ERROR",
            "v11_registry_requirement": "REQUIRED_STRICT",
            "v11_registry_state": "UNREQUESTED",
            "v11_registry_event": "NONE",
            "v11_registry_error_info": error_info,
            "v11_registry_summary": "registry error. defaulting to unrequested state.",
            "v11_registry_basis": [],
            "v11_registry_artifacts": [],
        }

        if warnings:
            record["v11_registry_warnings"] = warnings

        return record


def get_approval_registry_schema_info() -> Dict[str, Any]:
    """
    Get approval registry schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.1",
        "schema_type": "manual_approval_registry",
        "required_fields": V11ApprovalRegistrySchema.REQUIRED_FIELDS,
        "optional_fields": V11ApprovalRegistrySchema.OPTIONAL_FIELDS,
        "valid_modes": V11ApprovalRegistrySchema.VALID_MODES,
        "valid_statuses": V11ApprovalRegistrySchema.VALID_STATUSES,
        "valid_requirements": V11ApprovalRegistrySchema.VALID_REQUIREMENTS,
        "valid_states": V11ApprovalRegistrySchema.VALID_STATES,
        "valid_events": V11ApprovalRegistrySchema.VALID_EVENTS,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Approval Registry Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Empty record
    print("Test 1: Empty record")
    empty = V11ApprovalRegistrySchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    warnings = V11ApprovalRegistrySchema.validate_structure(empty)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 2: REQUESTED state
    print("Test 2: REQUESTED state")
    requested_registry = V11ApprovalRegistrySchema.create_registry_record(
        requirement="REQUIRED",
        state="REQUESTED",
        event="REQUEST",
        summary="approval request recorded. registry state set to requested.",
        basis=["v11_requirement", "event"],
        artifacts=["pr113_approval_record"],
    )
    print(json.dumps(requested_registry, indent=2))
    warnings = V11ApprovalRegistrySchema.validate_structure(requested_registry)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 3: APPROVED state (label only)
    print("Test 3: APPROVED state (label only)")
    approved_registry = V11ApprovalRegistrySchema.create_registry_record(
        requirement="REQUIRED_STRICT",
        state="APPROVED",
        event="APPROVE",
        summary="approval state recorded as approved. this is a state label only.",
        basis=["v11_requirement", "v11_registry_state", "event"],
        artifacts=["pr113_approval_record"],
    )
    print(json.dumps(approved_registry, indent=2))
    warnings = V11ApprovalRegistrySchema.validate_structure(approved_registry)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 4: REJECTED state
    print("Test 4: REJECTED state")
    rejected_registry = V11ApprovalRegistrySchema.create_registry_record(
        requirement="REQUIRED",
        state="REJECTED",
        event="REJECT",
        summary="approval request rejected. registry state set to rejected.",
        basis=["v11_requirement", "v11_registry_state", "event"],
        artifacts=["pr113_approval_record"],
    )
    print(json.dumps(rejected_registry, indent=2))
    warnings = V11ApprovalRegistrySchema.validate_structure(rejected_registry)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 5: ERROR record
    print("Test 5: ERROR record")
    error_registry = V11ApprovalRegistrySchema.create_error_record(
        error_info="invalid approval gate record type",
        warnings=["Invalid input type"],
    )
    print(json.dumps(error_registry, indent=2))
    warnings = V11ApprovalRegistrySchema.validate_structure(error_registry)
    print(f"Validation warnings: {len(warnings)}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
