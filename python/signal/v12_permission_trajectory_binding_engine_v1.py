#!/usr/bin/env python3
"""
PR127: v1.2 Permission Trajectory Binding Engine v1 (READ-ONLY)

Purpose:
    Bind PR126 monitor records into human-readable trajectory signals.
    Convert monitor outputs into structural signals for human interface.

Engine Philosophy:
    - Defensive: invalid input → valid ERROR record
    - Deterministic: same inputs → same outputs
    - Static mapping (no learning, no optimization)
    - Label-to-label transformation only

Binding Logic:
    1. Extract current permission from monitor
    2. Extract suppression state from monitor
    3. Determine most recent transition label
    4. Extract window label
    5. Generate non-prescriptive summary

Constitutional Guarantees:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals, addresses, amounts
    - No trajectory coupling
"""

from typing import Any, Dict, List, Optional
from .v12_permission_trajectory_signal_schema import V12PermissionTrajectorySignalSchema


def bind_permission_trajectory_signal_v1(
    monitor_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Bind monitor record to trajectory signal.

    Args:
        monitor_record: PR126 monitor record

    Returns:
        Signal record (always valid, ERROR on failure)
    """
    # Defensive: validate input
    if not monitor_record or not isinstance(monitor_record, dict):
        return V12PermissionTrajectorySignalSchema.create_error_record(
            "signal binding failed. no monitor record provided."
        )

    # Check monitor status
    if monitor_record.get("v12_monitor_status") == "ERROR":
        return V12PermissionTrajectorySignalSchema.create_error_record(
            "signal binding failed. monitor record has ERROR status."
        )

    if monitor_record.get("v12_monitor_status") == "UNAVAILABLE":
        return V12PermissionTrajectorySignalSchema.create_error_record(
            "signal binding failed. monitor record unavailable."
        )

    # Extract permission level
    permission_level = monitor_record.get("v12_monitor_current_permission", "UNKNOWN")

    # Extract suppression state
    suppression_state = monitor_record.get("v12_monitor_suppression_state", "STABLE")

    # Determine transition label (most recent transition)
    transition_label = _determine_transition_label(monitor_record)

    # Extract window label
    window_label = monitor_record.get("v12_monitor_window", "MEDIUM")

    # Build basis array (v12_monitor_* fields only)
    basis = _build_basis(monitor_record)

    # Create signal record
    return V12PermissionTrajectorySignalSchema.create_signal_record(
        permission_level=permission_level,
        suppression_state=suppression_state,
        transition_label=transition_label,
        window_label=window_label,
        basis=basis,
    )


def _determine_transition_label(monitor_record: Dict[str, Any]) -> str:
    """
    Determine transition label from monitor record.

    Logic:
    - If no transitions → NONE
    - If transitions exist → use most recent event_type

    Args:
        monitor_record: Monitor record

    Returns:
        Transition label
    """
    transition_events = monitor_record.get("v12_monitor_transition_events", [])

    if not transition_events or not isinstance(transition_events, list) or len(transition_events) == 0:
        return "NONE"

    # Get most recent transition (last in list)
    most_recent = transition_events[-1]

    if not isinstance(most_recent, dict):
        return "NONE"

    event_type = most_recent.get("event_type", "NONE")

    # Map event_type to transition_label
    # DEGRADATION → DEGRADATION
    # RECOVERY → RECOVERY
    # SUPPRESSION → SUPPRESSION
    # PERMISSION_CHANGE → NONE (non-directional change)
    if event_type == "DEGRADATION":
        return "DEGRADATION"
    elif event_type == "RECOVERY":
        return "RECOVERY"
    elif event_type == "SUPPRESSION":
        return "SUPPRESSION"
    else:
        return "NONE"


def _build_basis(monitor_record: Dict[str, Any]) -> List[str]:
    """
    Build basis array from monitor record.

    Only include v12_monitor_* fields that were used.

    Args:
        monitor_record: Monitor record

    Returns:
        List of field names
    """
    basis = []

    # Core fields used in binding
    if "v12_monitor_current_permission" in monitor_record:
        basis.append("v12_monitor_current_permission")

    if "v12_monitor_suppression_state" in monitor_record:
        basis.append("v12_monitor_suppression_state")

    if "v12_monitor_transition_events" in monitor_record:
        basis.append("v12_monitor_transition_events")

    if "v12_monitor_window" in monitor_record:
        basis.append("v12_monitor_window")

    return basis


def get_binding_v1_info() -> Dict[str, Any]:
    """
    Get binding v1 information.

    Returns:
        Dict with binding metadata
    """
    return {
        "binding_version": "v1",
        "binding_type": "permission_trajectory_signal",
        "input_schema": "v12_permission_monitor",
        "output_schema": "v12_permission_trajectory_signal",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "deterministic",
            "defensive",
            "no_trajectory_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Permission Trajectory Binding Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Invalid input → ERROR
    print("Test 1: Invalid input → ERROR")
    result1 = bind_permission_trajectory_signal_v1(None)
    print(f"Status: {result1['v12_signal_status']}")
    print(f"Summary: {result1['v12_signal_summary']}")
    print()

    # Test 2: Monitor with ERROR → Signal ERROR
    print("Test 2: Monitor with ERROR → Signal ERROR")
    monitor2 = {
        "v12_monitor_status": "ERROR",
        "v12_monitor_summary": "monitor error",
    }
    result2 = bind_permission_trajectory_signal_v1(monitor2)
    print(f"Status: {result2['v12_signal_status']}")
    print(f"Summary: {result2['v12_signal_summary']}")
    print()

    # Test 3: ALLOW + STABLE + no transitions
    print("Test 3: ALLOW + STABLE + no transitions")
    monitor3 = {
        "v12_monitor_status": "AVAILABLE",
        "v12_monitor_current_permission": "ALLOW",
        "v12_monitor_suppression_state": "STABLE",
        "v12_monitor_transition_events": [],
        "v12_monitor_window": "MEDIUM",
    }
    result3 = bind_permission_trajectory_signal_v1(monitor3)
    print(f"Status: {result3['v12_signal_status']}")
    print(f"Permission level: {result3['v12_signal_permission_level']}")
    print(f"Suppression state: {result3['v12_signal_suppression_state']}")
    print(f"Transition label: {result3['v12_signal_transition_label']}")
    print(f"Window label: {result3['v12_signal_window_label']}")
    print(f"Summary: {result3['v12_signal_summary']}")
    print()

    # Test 4: DRY_RUN_ONLY + DEGRADING + DEGRADATION transition
    print("Test 4: DRY_RUN_ONLY + DEGRADING + DEGRADATION transition")
    monitor4 = {
        "v12_monitor_status": "AVAILABLE",
        "v12_monitor_current_permission": "DRY_RUN_ONLY",
        "v12_monitor_suppression_state": "DEGRADING",
        "v12_monitor_transition_events": [
            {
                "event_type": "DEGRADATION",
                "from_permission": "ALLOW",
                "to_permission": "DRY_RUN_ONLY",
            }
        ],
        "v12_monitor_window": "MEDIUM",
    }
    result4 = bind_permission_trajectory_signal_v1(monitor4)
    print(f"Status: {result4['v12_signal_status']}")
    print(f"Permission level: {result4['v12_signal_permission_level']}")
    print(f"Suppression state: {result4['v12_signal_suppression_state']}")
    print(f"Transition label: {result4['v12_signal_transition_label']}")
    print(f"Summary: {result4['v12_signal_summary']}")
    print()

    # Test 5: HOLD + SUPPRESSED + SUPPRESSION transition
    print("Test 5: HOLD + SUPPRESSED + SUPPRESSION transition")
    monitor5 = {
        "v12_monitor_status": "AVAILABLE",
        "v12_monitor_current_permission": "HOLD",
        "v12_monitor_suppression_state": "SUPPRESSED",
        "v12_monitor_transition_events": [
            {
                "event_type": "SUPPRESSION",
                "from_permission": "DRY_RUN_ONLY",
                "to_permission": "HOLD",
            }
        ],
        "v12_monitor_window": "MEDIUM",
    }
    result5 = bind_permission_trajectory_signal_v1(monitor5)
    print(f"Status: {result5['v12_signal_status']}")
    print(f"Permission level: {result5['v12_signal_permission_level']}")
    print(f"Suppression state: {result5['v12_signal_suppression_state']}")
    print(f"Transition label: {result5['v12_signal_transition_label']}")
    print(f"Summary: {result5['v12_signal_summary']}")
    print()

    # Test 6: DRY_RUN_ONLY + RECOVERING + RECOVERY transition
    print("Test 6: DRY_RUN_ONLY + RECOVERING + RECOVERY transition")
    monitor6 = {
        "v12_monitor_status": "AVAILABLE",
        "v12_monitor_current_permission": "DRY_RUN_ONLY",
        "v12_monitor_suppression_state": "RECOVERING",
        "v12_monitor_transition_events": [
            {
                "event_type": "RECOVERY",
                "from_permission": "HOLD",
                "to_permission": "DRY_RUN_ONLY",
            }
        ],
        "v12_monitor_window": "SHORT",
    }
    result6 = bind_permission_trajectory_signal_v1(monitor6)
    print(f"Status: {result6['v12_signal_status']}")
    print(f"Permission level: {result6['v12_signal_permission_level']}")
    print(f"Suppression state: {result6['v12_signal_suppression_state']}")
    print(f"Transition label: {result6['v12_signal_transition_label']}")
    print(f"Window label: {result6['v12_signal_window_label']}")
    print(f"Summary: {result6['v12_signal_summary']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
