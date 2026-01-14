#!/usr/bin/env python3
"""
PR150: v1.4 Stress Escalation Binding Schema (READ-ONLY)

Purpose:
    Define schema for stress escalation binding records.
    Escalation = Binding Shock Phase (PR149) to Stress (PR146) with escalate-only logic.

    Escalate-only: max(current_stress, min_required_by_phase)
    No de-escalation: Never lower stress (de-escalation is out of scope for PR150)

Record Prefix:
    v14_escalation_

Required Fields:
    v14_escalation_version: "v1"
    v14_escalation_status: AVAILABLE | UNKNOWN | ERROR
    v14_escalation_mode: READ_ONLY
    v14_escalation_phase_label: Phase label from PR149
    v14_escalation_input_stress_label: Current stress from PR146
    v14_escalation_min_required_stress_label: Minimum stress required by phase
    v14_escalation_output_stress_label: Escalated stress result
    v14_escalation_escalated_flag: ON | OFF | UNKNOWN
    v14_escalation_inputs_present: Dict of input presence flags
    v14_escalation_warnings: List of warnings

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Non-prescriptive: No should/must/recommend/advise
    - Label-only output: No numeric values in text
    - No token literals: No BTC/USDC/SUI/ETH
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/hence
    - Escalate-only: Never lower stress
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Escalation version
ESCALATION_VERSION_V1 = "v1"

# Escalation status constants
ESCALATION_STATUS_AVAILABLE = "AVAILABLE"
ESCALATION_STATUS_UNKNOWN = "UNKNOWN"
ESCALATION_STATUS_ERROR = "ERROR"

# Escalation mode constants
ESCALATION_MODE_READ_ONLY = "READ_ONLY"

# Escalated flag constants
ESCALATED_FLAG_ON = "ON"
ESCALATED_FLAG_OFF = "OFF"
ESCALATED_FLAG_UNKNOWN = "UNKNOWN"


class V14StressEscalationSchema:
    """Schema for stress escalation binding records."""

    # Valid statuses
    VALID_STATUSES = [
        ESCALATION_STATUS_AVAILABLE,
        ESCALATION_STATUS_UNKNOWN,
        ESCALATION_STATUS_ERROR,
    ]

    # Valid modes
    VALID_MODES = [
        ESCALATION_MODE_READ_ONLY,
    ]

    # Valid escalated flags
    VALID_ESCALATED_FLAGS = [
        ESCALATED_FLAG_ON,
        ESCALATED_FLAG_OFF,
        ESCALATED_FLAG_UNKNOWN,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "v14_escalation_version",
        "v14_escalation_status",
        "v14_escalation_mode",
        "v14_escalation_phase_label",
        "v14_escalation_input_stress_label",
        "v14_escalation_min_required_stress_label",
        "v14_escalation_output_stress_label",
        "v14_escalation_escalated_flag",
        "v14_escalation_inputs_present",
        "v14_escalation_warnings",
    ]

    @staticmethod
    def create_escalation_record(
        version: str = ESCALATION_VERSION_V1,
        status: str = ESCALATION_STATUS_AVAILABLE,
        mode: str = ESCALATION_MODE_READ_ONLY,
        phase_label: str = "",
        input_stress_label: str = "",
        min_required_stress_label: str = "",
        output_stress_label: str = "",
        escalated_flag: str = ESCALATED_FLAG_UNKNOWN,
        inputs_present: Optional[Dict[str, bool]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create stress escalation record.

        Args:
            version: Escalation version (default "v1")
            status: AVAILABLE | UNKNOWN | ERROR
            mode: READ_ONLY
            phase_label: Phase label from PR149
            input_stress_label: Current stress from PR146
            min_required_stress_label: Minimum stress required by phase
            output_stress_label: Escalated stress result
            escalated_flag: ON | OFF | UNKNOWN
            inputs_present: Dict of input presence flags
            warnings: List of warnings

        Returns:
            Escalation record
        """
        record = {
            "v14_escalation_version": version,
            "v14_escalation_status": status,
            "v14_escalation_mode": mode,
            "v14_escalation_phase_label": phase_label,
            "v14_escalation_input_stress_label": input_stress_label,
            "v14_escalation_min_required_stress_label": min_required_stress_label,
            "v14_escalation_output_stress_label": output_stress_label,
            "v14_escalation_escalated_flag": escalated_flag,
            "v14_escalation_inputs_present": inputs_present if inputs_present else {},
            "v14_escalation_warnings": warnings if warnings else [],
        }

        return record

    @staticmethod
    def create_error_record(
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create error record.

        Args:
            warnings: List of warnings

        Returns:
            Error record
        """
        return V14StressEscalationSchema.create_escalation_record(
            status=ESCALATION_STATUS_ERROR,
            phase_label="",
            input_stress_label="",
            min_required_stress_label="",
            output_stress_label="",
            escalated_flag=ESCALATED_FLAG_UNKNOWN,
            inputs_present={},
            warnings=warnings if warnings else [],
        )

    @staticmethod
    def validate_escalation_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate escalation record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V14StressEscalationSchema.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate version
        version = record.get("v14_escalation_version")
        if version != ESCALATION_VERSION_V1:
            errors.append(f"invalid version: {version} (expected {ESCALATION_VERSION_V1})")

        # Validate status
        status = record.get("v14_escalation_status")
        if status not in V14StressEscalationSchema.VALID_STATUSES:
            errors.append(f"invalid status: {status}")

        # Validate mode
        mode = record.get("v14_escalation_mode")
        if mode not in V14StressEscalationSchema.VALID_MODES:
            errors.append(f"invalid mode: {mode}")

        # Validate escalated_flag
        escalated_flag = record.get("v14_escalation_escalated_flag")
        if escalated_flag not in V14StressEscalationSchema.VALID_ESCALATED_FLAGS:
            errors.append(f"invalid escalated_flag: {escalated_flag}")

        # Validate types
        if not isinstance(record.get("v14_escalation_phase_label"), str):
            errors.append("phase_label must be string")

        if not isinstance(record.get("v14_escalation_input_stress_label"), str):
            errors.append("input_stress_label must be string")

        if not isinstance(record.get("v14_escalation_min_required_stress_label"), str):
            errors.append("min_required_stress_label must be string")

        if not isinstance(record.get("v14_escalation_output_stress_label"), str):
            errors.append("output_stress_label must be string")

        if not isinstance(record.get("v14_escalation_inputs_present"), dict):
            errors.append("inputs_present must be dict")

        if not isinstance(record.get("v14_escalation_warnings"), list):
            errors.append("warnings must be list")

        return errors


def get_stress_escalation_schema_info() -> Dict[str, Any]:
    """
    Get stress escalation schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1",
        "schema_type": "stress_escalation_binding",
        "record_prefix": "v14_escalation_",
        "valid_statuses": V14StressEscalationSchema.VALID_STATUSES,
        "valid_modes": V14StressEscalationSchema.VALID_MODES,
        "valid_escalated_flags": V14StressEscalationSchema.VALID_ESCALATED_FLAGS,
        "philosophy": "Escalate-only: max(current, min_required_by_phase). No de-escalation in PR150.",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "label_output_only",
            "no_addresses",
            "no_causal_coupling",
            "escalate_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Stress Escalation Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create valid record
    print("Test 1: Create valid record")
    record1 = V14StressEscalationSchema.create_escalation_record(
        status=ESCALATION_STATUS_AVAILABLE,
        phase_label="PHASE_PRE_SHOCK",
        input_stress_label="STRESS_CALM",
        min_required_stress_label="STRESS_TENSE",
        output_stress_label="STRESS_TENSE",
        escalated_flag=ESCALATED_FLAG_ON,
        inputs_present={
            "phase": True,
            "stress": True,
        },
    )
    errors1 = V14StressEscalationSchema.validate_escalation_record(record1)
    print(f"Valid record errors: {len(errors1)}")
    if errors1:
        for e in errors1:
            print(f"  - {e}")
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    record2 = V14StressEscalationSchema.create_error_record(
        warnings=["invalid inputs"],
    )
    errors2 = V14StressEscalationSchema.validate_escalation_record(record2)
    print(f"Error record status: {record2['v14_escalation_status']}")
    print(f"Error record errors: {len(errors2)}")
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    info = get_stress_escalation_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
