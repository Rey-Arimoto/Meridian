#!/usr/bin/env python3
"""
PR127: v1.2 Permission Trajectory Signal Schema v1 (READ-ONLY)

Purpose:
    Define schema for permission trajectory signals bound for human interface.
    Convert PR126 monitor records into human-readable structural signals.

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals: No SUI, USDC, BTC, ETH
    - No amounts: No numeric values in output
    - No addresses: No 0x... patterns
    - No trajectory coupling: No "permission improved therefore act"

Signal Philosophy:
    Binding ≠ Conclusion
    Trajectory ≠ Permission to act
    Signal = Human-readable structural label

    Signal provides:
    - Permission level label (current state)
    - Suppression state label (trajectory direction)
    - Transition label (most recent event type)
    - Window label (timeframe context)
    - Non-prescriptive summary

    Signal does NOT:
    - Recommend actions
    - Evaluate quality (good/bad)
    - Execute or trigger execution
    - Contain token names, amounts, addresses
    - Couple trajectory to action

v12_signal_ Prefix:
    All signal fields use v12_signal_ prefix for clear separation
    from monitor fields (v12_monitor_).

Schema Fields:
    - v12_signal_mode: ON | OFF
    - v12_signal_status: AVAILABLE | UNAVAILABLE | ERROR
    - v12_signal_permission_level: UNKNOWN | HOLD | DRY_RUN_ONLY | ALLOW
    - v12_signal_suppression_state: STABLE | DEGRADING | RECOVERING | SUPPRESSED
    - v12_signal_transition_label: NONE | DEGRADATION | RECOVERY | SUPPRESSION
    - v12_signal_window_label: SHORT | MEDIUM | LONG (no numbers)
    - v12_signal_summary: Non-prescriptive summary
    - v12_signal_basis: Array of field names referenced (v12_monitor_* only)
"""

from typing import Any, Dict, List, Optional


class V12PermissionTrajectorySignalSchema:
    """v1.2 Permission Trajectory Signal Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "v12_signal_mode",
        "v12_signal_status",
        "v12_signal_permission_level",
        "v12_signal_suppression_state",
        "v12_signal_transition_label",
        "v12_signal_window_label",
        "v12_signal_summary",
        "v12_signal_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v12_signal_warnings",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]
    VALID_PERMISSION_LEVELS = ["UNKNOWN", "HOLD", "DRY_RUN_ONLY", "ALLOW"]
    VALID_SUPPRESSION_STATES = ["STABLE", "DEGRADING", "RECOVERING", "SUPPRESSED"]
    VALID_TRANSITION_LABELS = ["NONE", "DEGRADATION", "RECOVERY", "SUPPRESSION"]
    VALID_WINDOW_LABELS = ["SHORT", "MEDIUM", "LONG"]

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty signal record.

        Returns:
            Empty signal record
        """
        return {
            "v12_signal_mode": "ON",
            "v12_signal_status": "UNAVAILABLE",
            "v12_signal_permission_level": "UNKNOWN",
            "v12_signal_suppression_state": "STABLE",
            "v12_signal_transition_label": "NONE",
            "v12_signal_window_label": "MEDIUM",
            "v12_signal_summary": "no trajectory signal available.",
            "v12_signal_basis": [],
        }

    @staticmethod
    def create_error_record(error_message: str = "signal generation failed.") -> Dict[str, Any]:
        """
        Create an ERROR signal record.

        Args:
            error_message: Error description

        Returns:
            ERROR signal record
        """
        return {
            "v12_signal_mode": "ON",
            "v12_signal_status": "ERROR",
            "v12_signal_permission_level": "UNKNOWN",
            "v12_signal_suppression_state": "STABLE",
            "v12_signal_transition_label": "NONE",
            "v12_signal_window_label": "MEDIUM",
            "v12_signal_summary": error_message,
            "v12_signal_basis": [],
        }

    @staticmethod
    def create_signal_record(
        permission_level: str,
        suppression_state: str,
        transition_label: str,
        window_label: str = "MEDIUM",
        basis: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a trajectory signal record.

        Args:
            permission_level: Permission level label
            suppression_state: Suppression state label
            transition_label: Transition label
            window_label: Window label (SHORT/MEDIUM/LONG)
            basis: Optional array of field names referenced
            warnings: Optional array of warnings

        Returns:
            Signal record
        """
        # Generate summary
        summary = _generate_summary(permission_level, suppression_state, transition_label, window_label)

        record = {
            "v12_signal_mode": "ON",
            "v12_signal_status": "AVAILABLE",
            "v12_signal_permission_level": permission_level,
            "v12_signal_suppression_state": suppression_state,
            "v12_signal_transition_label": transition_label,
            "v12_signal_window_label": window_label,
            "v12_signal_summary": summary,
            "v12_signal_basis": basis or [],
        }

        if warnings:
            record["v12_signal_warnings"] = warnings

        return record

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate signal record structure.

        Args:
            record: Signal record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V12PermissionTrajectorySignalSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v12_signal_mode" in record:
            if record["v12_signal_mode"] not in V12PermissionTrajectorySignalSchema.VALID_MODES:
                warnings.append(f"Invalid signal mode: {record['v12_signal_mode']}")

        # Validate status
        if "v12_signal_status" in record:
            if record["v12_signal_status"] not in V12PermissionTrajectorySignalSchema.VALID_STATUSES:
                warnings.append(f"Invalid signal status: {record['v12_signal_status']}")

        # Validate permission_level
        if "v12_signal_permission_level" in record:
            if record["v12_signal_permission_level"] not in V12PermissionTrajectorySignalSchema.VALID_PERMISSION_LEVELS:
                warnings.append(f"Invalid permission level: {record['v12_signal_permission_level']}")

        # Validate suppression_state
        if "v12_signal_suppression_state" in record:
            if record["v12_signal_suppression_state"] not in V12PermissionTrajectorySignalSchema.VALID_SUPPRESSION_STATES:
                warnings.append(f"Invalid suppression state: {record['v12_signal_suppression_state']}")

        # Validate transition_label
        if "v12_signal_transition_label" in record:
            if record["v12_signal_transition_label"] not in V12PermissionTrajectorySignalSchema.VALID_TRANSITION_LABELS:
                warnings.append(f"Invalid transition label: {record['v12_signal_transition_label']}")

        # Validate window_label
        if "v12_signal_window_label" in record:
            if record["v12_signal_window_label"] not in V12PermissionTrajectorySignalSchema.VALID_WINDOW_LABELS:
                warnings.append(f"Invalid window label: {record['v12_signal_window_label']}")

        # Validate basis (must be list of strings)
        if "v12_signal_basis" in record:
            if not isinstance(record["v12_signal_basis"], list):
                warnings.append("Basis must be a list")

        return warnings


def _generate_summary(
    permission_level: str,
    suppression_state: str,
    transition_label: str,
    window_label: str,
) -> str:
    """
    Generate non-prescriptive summary.

    Args:
        permission_level: Permission level label
        suppression_state: Suppression state label
        transition_label: Transition label
        window_label: Window label

    Returns:
        Summary text
    """
    fragments = []

    # Permission level
    fragments.append(f"permission level labeled as {permission_level}.")

    # Suppression state
    fragments.append(f"suppression state labeled as {suppression_state}.")

    # Transition (if not NONE)
    if transition_label != "NONE":
        fragments.append(f"transition labeled as {transition_label}.")

    # Window
    fragments.append(f"window labeled as {window_label}.")

    return " ".join(fragments)


def get_signal_schema_info() -> Dict[str, Any]:
    """
    Get signal schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "permission_trajectory_signal",
        "valid_modes": V12PermissionTrajectorySignalSchema.VALID_MODES,
        "valid_statuses": V12PermissionTrajectorySignalSchema.VALID_STATUSES,
        "valid_permission_levels": V12PermissionTrajectorySignalSchema.VALID_PERMISSION_LEVELS,
        "valid_suppression_states": V12PermissionTrajectorySignalSchema.VALID_SUPPRESSION_STATES,
        "valid_transition_labels": V12PermissionTrajectorySignalSchema.VALID_TRANSITION_LABELS,
        "valid_window_labels": V12PermissionTrajectorySignalSchema.VALID_WINDOW_LABELS,
        "required_fields": V12PermissionTrajectorySignalSchema.REQUIRED_FIELDS,
        "optional_fields": V12PermissionTrajectorySignalSchema.OPTIONAL_FIELDS,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "no_token_literals",
            "no_amounts",
            "no_addresses",
            "no_trajectory_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Permission Trajectory Signal Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V12PermissionTrajectorySignalSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Validate empty record
    print("Test 2: Validate empty record")
    warnings = V12PermissionTrajectorySignalSchema.validate_structure(empty)
    print(f"Warnings: {warnings}")
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V12PermissionTrajectorySignalSchema.create_error_record("test error")
    print(json.dumps(error, indent=2))
    print()

    # Test 4: Create full signal record
    print("Test 4: Create full signal record")
    signal = V12PermissionTrajectorySignalSchema.create_signal_record(
        permission_level="DRY_RUN_ONLY",
        suppression_state="DEGRADING",
        transition_label="DEGRADATION",
        window_label="MEDIUM",
        basis=["v12_monitor_current_permission", "v12_monitor_suppression_state"],
    )
    print(json.dumps(signal, indent=2))
    print()

    # Test 5: Validate full record
    print("Test 5: Validate full record")
    warnings = V12PermissionTrajectorySignalSchema.validate_structure(signal)
    print(f"Warnings: {warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
