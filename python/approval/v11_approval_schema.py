#!/usr/bin/env python3
"""
PR113: v1.1 Human Approval Gate Schema (READ-ONLY)

Purpose:
    Schema for human approval gate records.
    Approval = State Machine (not action/recommendation).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No should/must vocabulary

Approval Philosophy:
    Approval ≠ Action
    Approval ≠ Recommendation
    Approval = State Label

    Approval describes:
    - Whether approval is structurally required
    - Current approval state (UNREQUESTED/REQUESTED/APPROVED/REJECTED/EXPIRED)
    - Basis for requirement determination

    Approval does NOT:
    - Recommend execution
    - Evaluate profitability
    - Provide trading instructions
    - Interact with wallets

    IMPORTANT: "APPROVED" is a state label only.
    It does NOT mean "execute" or "this is good".

Schema Design:
    - v11_approval_ prefix for approval fields
    - Requirement: NOT_REQUIRED, REQUIRED, REQUIRED_STRICT
    - State: UNREQUESTED, REQUESTED, APPROVED, REJECTED, EXPIRED
    - Status: AVAILABLE, UNAVAILABLE, ERROR
"""

from typing import Any, Dict, List, Optional


class V11ApprovalSchema:
    """
    Schema for v1.1 human approval gate records.

    Approval = State Machine (not action).
    """

    # Required fields for approval record
    REQUIRED_FIELDS = [
        "v11_approval_mode",            # Approval mode (ON/OFF)
        "v11_approval_status",          # Approval status (AVAILABLE/UNAVAILABLE/ERROR)
        "v11_approval_requirement",     # Requirement level
        "v11_approval_state",           # Current state
        "v11_approval_summary",         # Summary description
        "v11_approval_basis",           # Basis (upstream fields used)
        "v11_approval_artifacts",       # Artifacts referenced
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v11_approval_error_info",      # Error information if status is ERROR
        "v11_approval_metadata",        # Additional metadata
    ]

    # Valid approval modes
    VALID_MODES = ["ON", "OFF"]

    # Valid approval statuses
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]

    # Valid approval requirements
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

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate approval record structure.

        Args:
            record: Approval record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V11ApprovalSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v11_approval_mode" in record:
            mode = record["v11_approval_mode"]
            if mode not in V11ApprovalSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v11_approval_mode: {mode}. "
                    f"Must be one of {V11ApprovalSchema.VALID_MODES}"
                )

        # Validate status
        if "v11_approval_status" in record:
            status = record["v11_approval_status"]
            if status not in V11ApprovalSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v11_approval_status: {status}. "
                    f"Must be one of {V11ApprovalSchema.VALID_STATUSES}"
                )

        # Validate requirement
        if "v11_approval_requirement" in record:
            requirement = record["v11_approval_requirement"]
            if requirement not in V11ApprovalSchema.VALID_REQUIREMENTS:
                warnings.append(
                    f"Invalid v11_approval_requirement: {requirement}. "
                    f"Must be one of {V11ApprovalSchema.VALID_REQUIREMENTS}"
                )

        # Validate state
        if "v11_approval_state" in record:
            state = record["v11_approval_state"]
            if state not in V11ApprovalSchema.VALID_STATES:
                warnings.append(
                    f"Invalid v11_approval_state: {state}. "
                    f"Must be one of {V11ApprovalSchema.VALID_STATES}"
                )

        # Validate basis
        if "v11_approval_basis" in record:
            basis = record["v11_approval_basis"]
            if not isinstance(basis, list):
                warnings.append("v11_approval_basis must be a list")

        # Validate artifacts
        if "v11_approval_artifacts" in record:
            artifacts = record["v11_approval_artifacts"]
            if not isinstance(artifacts, list):
                warnings.append("v11_approval_artifacts must be a list")

        # Validate summary
        if "v11_approval_summary" in record:
            summary = record["v11_approval_summary"]
            if not isinstance(summary, str):
                warnings.append("v11_approval_summary must be a string")
            elif len(summary) == 0:
                warnings.append("v11_approval_summary must not be empty")

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty approval record with safe defaults.

        Returns:
            Empty approval record (unavailable state)
        """
        return {
            "v11_approval_mode": "OFF",
            "v11_approval_status": "UNAVAILABLE",
            "v11_approval_requirement": "REQUIRED_STRICT",
            "v11_approval_state": "UNREQUESTED",
            "v11_approval_summary": "approval gate unavailable. defaulting to strict requirement.",
            "v11_approval_basis": [],
            "v11_approval_artifacts": [],
        }

    @staticmethod
    def create_approval_record(
        requirement: str,
        state: str,
        summary: str,
        basis: List[str],
        artifacts: List[str],
    ) -> Dict[str, Any]:
        """
        Create approval record.

        Args:
            requirement: Approval requirement (NOT_REQUIRED/REQUIRED/REQUIRED_STRICT)
            state: Approval state (UNREQUESTED/REQUESTED/APPROVED/REJECTED/EXPIRED)
            summary: Human-readable summary
            basis: List of upstream fields that informed decision
            artifacts: List of artifact references

        Returns:
            Approval record
        """
        return {
            "v11_approval_mode": "ON",
            "v11_approval_status": "AVAILABLE",
            "v11_approval_requirement": requirement,
            "v11_approval_state": state,
            "v11_approval_summary": summary,
            "v11_approval_basis": basis,
            "v11_approval_artifacts": artifacts,
        }

    @staticmethod
    def create_error_record(
        error_info: str,
    ) -> Dict[str, Any]:
        """
        Create error approval record.

        Args:
            error_info: Error information

        Returns:
            Error approval record
        """
        return {
            "v11_approval_mode": "ON",
            "v11_approval_status": "ERROR",
            "v11_approval_requirement": "REQUIRED_STRICT",
            "v11_approval_state": "UNREQUESTED",
            "v11_approval_error_info": error_info,
            "v11_approval_summary": "approval gate error. defaulting to strict requirement.",
            "v11_approval_basis": [],
            "v11_approval_artifacts": [],
        }


def get_approval_schema_info() -> Dict[str, Any]:
    """
    Get approval schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.1",
        "schema_type": "human_approval_gate",
        "required_fields": V11ApprovalSchema.REQUIRED_FIELDS,
        "optional_fields": V11ApprovalSchema.OPTIONAL_FIELDS,
        "valid_modes": V11ApprovalSchema.VALID_MODES,
        "valid_statuses": V11ApprovalSchema.VALID_STATUSES,
        "valid_requirements": V11ApprovalSchema.VALID_REQUIREMENTS,
        "valid_states": V11ApprovalSchema.VALID_STATES,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Human Approval Gate Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Empty record
    print("Test 1: Empty record")
    empty = V11ApprovalSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    warnings = V11ApprovalSchema.validate_structure(empty)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 2: REQUIRED_STRICT approval
    print("Test 2: REQUIRED_STRICT approval (REGIME_CRITICAL)")
    strict_approval = V11ApprovalSchema.create_approval_record(
        requirement="REQUIRED_STRICT",
        state="UNREQUESTED",
        summary="approval required under critical regime conditions. no approval requested.",
        basis=["v11_regime_level", "v11_preview_risk_surface"],
        artifacts=["pr110_regime_record", "pr112_preview_record"],
    )
    print(json.dumps(strict_approval, indent=2))
    warnings = V11ApprovalSchema.validate_structure(strict_approval)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 3: REQUIRED approval
    print("Test 3: REQUIRED approval (REGIME_HIGH)")
    required_approval = V11ApprovalSchema.create_approval_record(
        requirement="REQUIRED",
        state="UNREQUESTED",
        summary="approval required under elevated regime conditions. no approval requested.",
        basis=["v11_regime_level"],
        artifacts=["pr110_regime_record"],
    )
    print(json.dumps(required_approval, indent=2))
    warnings = V11ApprovalSchema.validate_structure(required_approval)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 4: NOT_REQUIRED approval
    print("Test 4: NOT_REQUIRED approval (normal conditions)")
    not_required_approval = V11ApprovalSchema.create_approval_record(
        requirement="NOT_REQUIRED",
        state="UNREQUESTED",
        summary="approval not required under normal regime conditions.",
        basis=["v11_regime_level", "v10_execution_permission"],
        artifacts=["pr110_regime_record", "pr101_execution_record"],
    )
    print(json.dumps(not_required_approval, indent=2))
    warnings = V11ApprovalSchema.validate_structure(not_required_approval)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 5: ERROR record
    print("Test 5: ERROR record")
    error_approval = V11ApprovalSchema.create_error_record(
        error_info="invalid execution record type",
    )
    print(json.dumps(error_approval, indent=2))
    warnings = V11ApprovalSchema.validate_structure(error_approval)
    print(f"Validation warnings: {len(warnings)}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
