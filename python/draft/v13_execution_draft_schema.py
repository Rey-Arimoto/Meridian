#!/usr/bin/env python3
"""
PR141: v1.3 Execution Draft Schema v1 (READ-ONLY)

Purpose:
    Define strict schema for "execution draft" generated from approval packets.
    This is NOT an instruction, NOT a recommendation, NOT a transaction.
    It is a structured, non-custodial, execution-shaped draft record.

Schema Philosophy:
    Draft ≠ Action ≠ Recommendation
    Execution Draft = Structured shape reference (not instruction)

Record Prefix:
    v13_draft_

Required Fields:
    v13_draft_version: "v1"
    v13_draft_status: AVAILABLE | ERROR
    v13_draft_mode: READ_ONLY
    v13_draft_summary: Non-prescriptive summary
    v13_draft_inputs: References to artifact ids / component presence labels only
    v13_draft_constraints: Labels only (permission/trajectory/eligibility/boundary)
    v13_draft_intended_shape: Labels only (ACTION_CLASS = NONE / DRAFT_ONLY)
    v13_draft_basis: List of strings (no numbers)
    v13_draft_artifacts: List of strings (no ids with numeric patterns)
    v13_draft_warnings: List of strings

Optional Fields:
    v13_draft_components_present: Dict of booleans
    v13_draft_notes: String (guarded)

Constitutional Constraints:
    - READ-ONLY: No signing, no sending, no tx building, no calldata, no addresses
    - No token literals, no amounts, no numeric patterns
    - No trading verbs (swap/buy/sell/execute/sign/transfer/bridge)
    - No prescriptive language (should/must/need to)
    - No causal coupling ("therefore", "so", "hence")
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Draft version
DRAFT_VERSION_V1 = "v1"

# Draft status constants
DRAFT_STATUS_AVAILABLE = "AVAILABLE"
DRAFT_STATUS_ERROR = "ERROR"

# Draft mode constants
DRAFT_MODE_READ_ONLY = "READ_ONLY"

# Action class constants (for intended_shape)
ACTION_CLASS_NONE = "NONE"
ACTION_CLASS_DRAFT_ONLY = "DRAFT_ONLY"
ACTION_CLASS_NO_ACTION = "NO_ACTION"
ACTION_CLASS_HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
ACTION_CLASS_SIMULATION_ONLY = "SIMULATION_ONLY"
ACTION_CLASS_CONSIDERATION_ONLY = "CONSIDERATION_ONLY"


class V13ExecutionDraftSchema:
    """Schema for execution draft records."""

    # Valid statuses
    VALID_STATUSES = [
        DRAFT_STATUS_AVAILABLE,
        DRAFT_STATUS_ERROR,
    ]

    # Valid modes
    VALID_MODES = [
        DRAFT_MODE_READ_ONLY,
    ]

    # Valid action classes
    VALID_ACTION_CLASSES = [
        ACTION_CLASS_NONE,
        ACTION_CLASS_DRAFT_ONLY,
        ACTION_CLASS_NO_ACTION,
        ACTION_CLASS_HUMAN_REVIEW_REQUIRED,
        ACTION_CLASS_SIMULATION_ONLY,
        ACTION_CLASS_CONSIDERATION_ONLY,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "v13_draft_version",
        "v13_draft_status",
        "v13_draft_mode",
        "v13_draft_summary",
        "v13_draft_inputs",
        "v13_draft_constraints",
        "v13_draft_intended_shape",
        "v13_draft_basis",
        "v13_draft_artifacts",
        "v13_draft_warnings",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v13_draft_components_present",
        "v13_draft_notes",
    ]

    @staticmethod
    def create_draft_record(
        version: str = DRAFT_VERSION_V1,
        status: str = DRAFT_STATUS_AVAILABLE,
        mode: str = DRAFT_MODE_READ_ONLY,
        summary: str = "",
        inputs: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None,
        intended_shape: Optional[Dict[str, Any]] = None,
        basis: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        components_present: Optional[Dict[str, bool]] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create execution draft record.

        Args:
            version: Draft version (default "v1")
            status: AVAILABLE | ERROR
            mode: READ_ONLY
            summary: Non-prescriptive summary
            inputs: References to artifact ids / component presence labels only
            constraints: Labels only (permission/trajectory/eligibility/boundary)
            intended_shape: Labels only (ACTION_CLASS = NONE / DRAFT_ONLY)
            basis: List of strings (no numbers)
            artifacts: List of strings (no numeric pattern ids)
            warnings: List of strings
            components_present: Optional dict of booleans
            notes: Optional string (guarded)

        Returns:
            Execution draft record
        """
        record = {
            "v13_draft_version": version,
            "v13_draft_status": status,
            "v13_draft_mode": mode,
            "v13_draft_summary": summary,
            "v13_draft_inputs": inputs if inputs else {},
            "v13_draft_constraints": constraints if constraints else {},
            "v13_draft_intended_shape": intended_shape if intended_shape else {"action_class": ACTION_CLASS_NONE},
            "v13_draft_basis": basis if basis else [],
            "v13_draft_artifacts": artifacts if artifacts else [],
            "v13_draft_warnings": warnings if warnings else [],
        }

        # Add optional fields if provided
        if components_present is not None:
            record["v13_draft_components_present"] = components_present

        if notes is not None:
            record["v13_draft_notes"] = notes

        return record

    @staticmethod
    def create_error_record(
        summary: str = "execution draft generation failed.",
    ) -> Dict[str, Any]:
        """
        Create error record.

        Args:
            summary: Error summary

        Returns:
            Error record
        """
        return V13ExecutionDraftSchema.create_draft_record(
            status=DRAFT_STATUS_ERROR,
            summary=summary,
            inputs={},
            constraints={},
            intended_shape={"action_class": ACTION_CLASS_NONE},
            basis=[],
            artifacts=[],
            warnings=[],
        )

    @staticmethod
    def validate_draft_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate execution draft record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V13ExecutionDraftSchema.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate version
        version = record.get("v13_draft_version")
        if version != DRAFT_VERSION_V1:
            errors.append(f"invalid version: {version} (expected {DRAFT_VERSION_V1})")

        # Validate status
        status = record.get("v13_draft_status")
        if status not in V13ExecutionDraftSchema.VALID_STATUSES:
            errors.append(f"invalid status: {status}")

        # Validate mode
        mode = record.get("v13_draft_mode")
        if mode not in V13ExecutionDraftSchema.VALID_MODES:
            errors.append(f"invalid mode: {mode}")

        # Validate types
        if not isinstance(record.get("v13_draft_summary"), str):
            errors.append("summary must be string")

        if not isinstance(record.get("v13_draft_inputs"), dict):
            errors.append("inputs must be dict")

        if not isinstance(record.get("v13_draft_constraints"), dict):
            errors.append("constraints must be dict")

        if not isinstance(record.get("v13_draft_intended_shape"), dict):
            errors.append("intended_shape must be dict")

        if not isinstance(record.get("v13_draft_basis"), list):
            errors.append("basis must be list")

        if not isinstance(record.get("v13_draft_artifacts"), list):
            errors.append("artifacts must be list")

        if not isinstance(record.get("v13_draft_warnings"), list):
            errors.append("warnings must be list")

        # Validate intended_shape action_class
        intended_shape = record.get("v13_draft_intended_shape", {})
        if isinstance(intended_shape, dict):
            action_class = intended_shape.get("action_class")
            if action_class and action_class not in V13ExecutionDraftSchema.VALID_ACTION_CLASSES:
                errors.append(f"invalid action_class: {action_class}")

        return errors


def get_draft_schema_info() -> Dict[str, Any]:
    """
    Get execution draft schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1",
        "schema_type": "execution_draft",
        "record_prefix": "v13_draft_",
        "valid_statuses": V13ExecutionDraftSchema.VALID_STATUSES,
        "valid_modes": V13ExecutionDraftSchema.VALID_MODES,
        "valid_action_classes": V13ExecutionDraftSchema.VALID_ACTION_CLASSES,
        "philosophy": "Draft ≠ Action ≠ Recommendation",
        "constitutional_guarantees": [
            "READ-ONLY",
            "no_signing",
            "no_sending",
            "no_tx_building",
            "no_calldata",
            "no_addresses",
            "no_token_literals",
            "no_amounts",
            "no_numeric_patterns",
            "no_trading_verbs",
            "no_prescriptive_language",
            "no_causal_coupling",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.3 Execution Draft Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create valid record
    print("Test 1: Create valid record")
    record1 = V13ExecutionDraftSchema.create_draft_record(
        status=DRAFT_STATUS_AVAILABLE,
        summary="execution draft available.",
        inputs={"packet_id": "approval_packet_v1"},
        constraints={"permission": "ALLOWED", "eligibility": "ELIGIBLE"},
        intended_shape={"action_class": ACTION_CLASS_DRAFT_ONLY},
        basis=["v13_approval_packet"],
    )
    errors1 = V13ExecutionDraftSchema.validate_draft_record(record1)
    print(f"Valid record errors: {len(errors1)}")
    if errors1:
        for e in errors1:
            print(f"  - {e}")
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    record2 = V13ExecutionDraftSchema.create_error_record(
        summary="no approval packet provided."
    )
    errors2 = V13ExecutionDraftSchema.validate_draft_record(record2)
    print(f"Error record status: {record2['v13_draft_status']}")
    print(f"Error record errors: {len(errors2)}")
    print()

    # Test 3: Invalid record (missing field)
    print("Test 3: Invalid record (missing field)")
    record3 = {
        "v13_draft_version": "v1",
        "v13_draft_status": DRAFT_STATUS_AVAILABLE,
    }
    errors3 = V13ExecutionDraftSchema.validate_draft_record(record3)
    print(f"Invalid record errors: {len(errors3)}")
    if errors3:
        for e in errors3[:3]:
            print(f"  - {e}")
    print()

    # Test 4: Get schema info
    print("Test 4: Get schema info")
    info = get_draft_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
