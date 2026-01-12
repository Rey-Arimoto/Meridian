#!/usr/bin/env python3
"""
PR126: v1.2 Continuous Permission Monitor Schema v1 (READ-ONLY)

Purpose:
    Define schema for continuous permission monitoring records.
    Permission = State Trajectory (not flag).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals: No SUI, USDC, BTC, ETH
    - No amounts: No numeric values in output
    - No addresses: No 0x... patterns
    - No trajectory coupling: No "permission improved therefore act"

Monitor Philosophy:
    Permission ≠ Execution
    Permission ≠ Recommendation
    Permission = State Trajectory

    Monitor provides:
    - Permission state over time
    - Transition event detection
    - Suppression state labels (STABLE/DEGRADING/RECOVERING/SUPPRESSED)
    - Non-prescriptive summary

    Monitor does NOT:
    - Recommend actions
    - Execute transactions
    - Evaluate quality (good/bad)
    - Contain token names, amounts, addresses
    - Prescribe responses

v12_monitor_ Prefix:
    All monitor fields use v12_monitor_ prefix for clear separation
    from other v1.x fields.

Schema Fields:
    - v12_monitor_mode: ON | OFF
    - v12_monitor_status: AVAILABLE | UNAVAILABLE | ERROR
    - v12_monitor_window: SHORT | MEDIUM | LONG (label only, no numbers)
    - v12_monitor_current_permission: UNKNOWN | HOLD | DRY_RUN_ONLY | ALLOW
    - v12_monitor_permission_trajectory: List of permission labels (bounded)
    - v12_monitor_transition_events: List of transition event dicts
    - v12_monitor_suppression_state: STABLE | DEGRADING | RECOVERING | SUPPRESSED
    - v12_monitor_summary: Non-prescriptive summary
    - v12_monitor_basis: Array of field names referenced
"""

from typing import Any, Dict, List, Optional


class V12PermissionMonitorSchema:
    """v1.2 Continuous Permission Monitor Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "v12_monitor_mode",
        "v12_monitor_status",
        "v12_monitor_window",
        "v12_monitor_current_permission",
        "v12_monitor_permission_trajectory",
        "v12_monitor_transition_events",
        "v12_monitor_suppression_state",
        "v12_monitor_summary",
        "v12_monitor_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v12_monitor_warnings",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]
    VALID_WINDOWS = ["SHORT", "MEDIUM", "LONG"]
    VALID_PERMISSIONS = ["UNKNOWN", "HOLD", "DRY_RUN_ONLY", "ALLOW"]
    VALID_SUPPRESSION_STATES = ["STABLE", "DEGRADING", "RECOVERING", "SUPPRESSED"]

    # Transition event types
    TRANSITION_EVENT_TYPES = [
        "PERMISSION_CHANGE",
        "DEGRADATION",
        "RECOVERY",
        "SUPPRESSION",
    ]

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty monitor record.

        Returns:
            Empty monitor record
        """
        return {
            "v12_monitor_mode": "ON",
            "v12_monitor_status": "UNAVAILABLE",
            "v12_monitor_window": "MEDIUM",
            "v12_monitor_current_permission": "UNKNOWN",
            "v12_monitor_permission_trajectory": [],
            "v12_monitor_transition_events": [],
            "v12_monitor_suppression_state": "STABLE",
            "v12_monitor_summary": "no monitor data available.",
            "v12_monitor_basis": [],
        }

    @staticmethod
    def create_error_record(error_message: str = "monitor generation failed.") -> Dict[str, Any]:
        """
        Create an ERROR monitor record.

        Args:
            error_message: Error description

        Returns:
            ERROR monitor record
        """
        return {
            "v12_monitor_mode": "ON",
            "v12_monitor_status": "ERROR",
            "v12_monitor_window": "MEDIUM",
            "v12_monitor_current_permission": "UNKNOWN",
            "v12_monitor_permission_trajectory": [],
            "v12_monitor_transition_events": [],
            "v12_monitor_suppression_state": "STABLE",
            "v12_monitor_summary": error_message,
            "v12_monitor_basis": [],
        }

    @staticmethod
    def create_monitor_record(
        current_permission: str,
        trajectory: List[str],
        transition_events: List[Dict[str, Any]],
        suppression_state: str,
        window: str = "MEDIUM",
        basis: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a monitor record.

        Args:
            current_permission: Current permission label
            trajectory: Permission trajectory (list of permission labels)
            transition_events: List of transition events
            suppression_state: Suppression state label
            window: Window size label (SHORT/MEDIUM/LONG)
            basis: Optional array of field names referenced
            warnings: Optional array of warnings

        Returns:
            Monitor record
        """
        # Generate summary
        summary = _generate_summary(current_permission, suppression_state, transition_events)

        record = {
            "v12_monitor_mode": "ON",
            "v12_monitor_status": "AVAILABLE",
            "v12_monitor_window": window,
            "v12_monitor_current_permission": current_permission,
            "v12_monitor_permission_trajectory": trajectory,
            "v12_monitor_transition_events": transition_events,
            "v12_monitor_suppression_state": suppression_state,
            "v12_monitor_summary": summary,
            "v12_monitor_basis": basis or [],
        }

        if warnings:
            record["v12_monitor_warnings"] = warnings

        return record

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate monitor record structure.

        Args:
            record: Monitor record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V12PermissionMonitorSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v12_monitor_mode" in record:
            if record["v12_monitor_mode"] not in V12PermissionMonitorSchema.VALID_MODES:
                warnings.append(f"Invalid monitor mode: {record['v12_monitor_mode']}")

        # Validate status
        if "v12_monitor_status" in record:
            if record["v12_monitor_status"] not in V12PermissionMonitorSchema.VALID_STATUSES:
                warnings.append(f"Invalid monitor status: {record['v12_monitor_status']}")

        # Validate window
        if "v12_monitor_window" in record:
            if record["v12_monitor_window"] not in V12PermissionMonitorSchema.VALID_WINDOWS:
                warnings.append(f"Invalid monitor window: {record['v12_monitor_window']}")

        # Validate current_permission
        if "v12_monitor_current_permission" in record:
            if record["v12_monitor_current_permission"] not in V12PermissionMonitorSchema.VALID_PERMISSIONS:
                warnings.append(f"Invalid current permission: {record['v12_monitor_current_permission']}")

        # Validate suppression_state
        if "v12_monitor_suppression_state" in record:
            if record["v12_monitor_suppression_state"] not in V12PermissionMonitorSchema.VALID_SUPPRESSION_STATES:
                warnings.append(f"Invalid suppression state: {record['v12_monitor_suppression_state']}")

        # Validate trajectory (must be list)
        if "v12_monitor_permission_trajectory" in record:
            if not isinstance(record["v12_monitor_permission_trajectory"], list):
                warnings.append("Permission trajectory must be a list")

        # Validate transition_events (must be list)
        if "v12_monitor_transition_events" in record:
            if not isinstance(record["v12_monitor_transition_events"], list):
                warnings.append("Transition events must be a list")

        # Validate basis (must be list of strings)
        if "v12_monitor_basis" in record:
            if not isinstance(record["v12_monitor_basis"], list):
                warnings.append("Basis must be a list")

        return warnings


def _generate_summary(
    current_permission: str,
    suppression_state: str,
    transition_events: List[Dict[str, Any]],
) -> str:
    """
    Generate non-prescriptive summary.

    Args:
        current_permission: Current permission label
        suppression_state: Suppression state label
        transition_events: Transition events

    Returns:
        Summary text
    """
    fragments = []

    # Current permission
    fragments.append(f"current permission labeled as {current_permission}.")

    # Suppression state
    fragments.append(f"suppression state labeled as {suppression_state}.")

    # Transition events (if any)
    if transition_events:
        fragments.append(f"detected transition events.")

    return " ".join(fragments)


def get_monitor_schema_info() -> Dict[str, Any]:
    """
    Get monitor schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "permission_monitor",
        "valid_modes": V12PermissionMonitorSchema.VALID_MODES,
        "valid_statuses": V12PermissionMonitorSchema.VALID_STATUSES,
        "valid_windows": V12PermissionMonitorSchema.VALID_WINDOWS,
        "valid_permissions": V12PermissionMonitorSchema.VALID_PERMISSIONS,
        "valid_suppression_states": V12PermissionMonitorSchema.VALID_SUPPRESSION_STATES,
        "required_fields": V12PermissionMonitorSchema.REQUIRED_FIELDS,
        "optional_fields": V12PermissionMonitorSchema.OPTIONAL_FIELDS,
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
    print("v1.2 Continuous Permission Monitor Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V12PermissionMonitorSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Validate empty record
    print("Test 2: Validate empty record")
    warnings = V12PermissionMonitorSchema.validate_structure(empty)
    print(f"Warnings: {warnings}")
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V12PermissionMonitorSchema.create_error_record("test error")
    print(json.dumps(error, indent=2))
    print()

    # Test 4: Create full monitor record
    print("Test 4: Create full monitor record")
    monitor = V12PermissionMonitorSchema.create_monitor_record(
        current_permission="DRY_RUN_ONLY",
        trajectory=["ALLOW", "DRY_RUN_ONLY"],
        transition_events=[
            {
                "event_type": "DEGRADATION",
                "from_permission": "ALLOW",
                "to_permission": "DRY_RUN_ONLY",
            }
        ],
        suppression_state="DEGRADING",
        window="MEDIUM",
        basis=["v10_execution_permission", "v11_policy_permission"],
    )
    print(json.dumps(monitor, indent=2))
    print()

    # Test 5: Validate full record
    print("Test 5: Validate full record")
    warnings = V12PermissionMonitorSchema.validate_structure(monitor)
    print(f"Warnings: {warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
