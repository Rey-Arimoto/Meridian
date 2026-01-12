#!/usr/bin/env python3
"""
PR126: v1.2 Continuous Permission Monitor Engine v1 (READ-ONLY)

Purpose:
    Monitor execution permission state evolution over time.
    Permission = State Trajectory (not flag).

Engine Philosophy:
    - Defensive: invalid input → valid ERROR record
    - Deterministic: same inputs → same outputs
    - Static transition detection (no learning, no optimization)
    - Directional labels only (STABLE/DEGRADING/RECOVERING/SUPPRESSED)

Permission Source Priority (per timestep):
    1. If policy override exists → use it
    2. Else use execution permission

Transition Detection:
    Emit TRANSITION_EVENT when permission label changes:
    - UNKNOWN → HOLD/DRY_RUN_ONLY/ALLOW
    - ALLOW → DRY_RUN_ONLY/HOLD
    - DRY_RUN_ONLY → HOLD
    - HOLD → DRY_RUN_ONLY/UNKNOWN/ALLOW

Suppression State (derived from last two steps):
    - If last permission == HOLD → SUPPRESSED
    - If moved toward more restrictive → DEGRADING
    - If moved toward less restrictive → RECOVERING
    - Else → STABLE

Constitutional Guarantees:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals, addresses, amounts
    - No trajectory coupling
"""

from typing import Any, Dict, List, Optional
from .v12_permission_monitor_schema import V12PermissionMonitorSchema


# Permission restrictiveness order (most restrictive first)
PERMISSION_ORDER = {
    "HOLD": 0,
    "DRY_RUN_ONLY": 1,
    "ALLOW": 2,
    "UNKNOWN": 3,
}


def monitor_permission_v1(
    records_window: Optional[List[Dict[str, Any]]] = None,
    window_label: str = "MEDIUM",
) -> Dict[str, Any]:
    """
    Monitor permission state evolution over time.

    Args:
        records_window: List of timestep records (each contains all artifacts)
        window_label: Window size label (SHORT/MEDIUM/LONG)

    Returns:
        Monitor record (always valid, ERROR on failure)
    """
    # Defensive: validate input
    if not records_window or not isinstance(records_window, list) or len(records_window) == 0:
        return V12PermissionMonitorSchema.create_error_record(
            "monitor generation failed. no records window provided."
        )

    # Validate window_label
    if window_label not in V12PermissionMonitorSchema.VALID_WINDOWS:
        window_label = "MEDIUM"

    # Extract permission trajectory
    trajectory = []
    basis_fields = set()

    for timestep_record in records_window:
        if not isinstance(timestep_record, dict):
            continue

        # Extract permission from timestep record
        permission = _extract_permission_from_timestep(timestep_record, basis_fields)
        trajectory.append(permission)

    # If no trajectory extracted, return error
    if not trajectory:
        return V12PermissionMonitorSchema.create_error_record(
            "monitor generation failed. no permission trajectory extracted."
        )

    # Current permission is last in trajectory
    current_permission = trajectory[-1]

    # Detect transition events
    transition_events = _detect_transitions(trajectory)

    # Determine suppression state
    suppression_state = _determine_suppression_state(trajectory)

    # Create monitor record
    return V12PermissionMonitorSchema.create_monitor_record(
        current_permission=current_permission,
        trajectory=trajectory,
        transition_events=transition_events,
        suppression_state=suppression_state,
        window=window_label,
        basis=list(basis_fields),
    )


def _extract_permission_from_timestep(
    timestep_record: Dict[str, Any],
    basis_fields: set,
) -> str:
    """
    Extract permission from a single timestep record.

    Priority:
    1. Policy override (v11_policy_permission)
    2. Execution permission (v10_execution_permission)

    Args:
        timestep_record: Single timestep record
        basis_fields: Set to accumulate basis field names

    Returns:
        Permission label
    """
    # Check policy override first
    if "v11_policy_permission" in timestep_record:
        basis_fields.add("v11_policy_permission")
        return timestep_record["v11_policy_permission"]

    # Check execution permission
    if "v10_execution_permission" in timestep_record:
        basis_fields.add("v10_execution_permission")
        return timestep_record["v10_execution_permission"]

    # Default to UNKNOWN
    return "UNKNOWN"


def _detect_transitions(trajectory: List[str]) -> List[Dict[str, Any]]:
    """
    Detect permission transition events.

    Args:
        trajectory: List of permission labels

    Returns:
        List of transition events
    """
    events = []

    for i in range(1, len(trajectory)):
        prev_permission = trajectory[i - 1]
        curr_permission = trajectory[i]

        # Check if permission changed
        if prev_permission != curr_permission:
            # Determine event type
            event_type = _classify_transition(prev_permission, curr_permission)

            events.append({
                "event_type": event_type,
                "from_permission": prev_permission,
                "to_permission": curr_permission,
                "position": i,
            })

    return events


def _classify_transition(from_permission: str, to_permission: str) -> str:
    """
    Classify transition event type.

    Args:
        from_permission: Previous permission
        to_permission: Current permission

    Returns:
        Event type label
    """
    from_order = PERMISSION_ORDER.get(from_permission, 3)
    to_order = PERMISSION_ORDER.get(to_permission, 3)

    if to_permission == "HOLD":
        return "SUPPRESSION"
    elif to_order < from_order:
        # Moving toward more restrictive
        return "DEGRADATION"
    elif to_order > from_order:
        # Moving toward less restrictive
        return "RECOVERY"
    else:
        return "PERMISSION_CHANGE"


def _determine_suppression_state(trajectory: List[str]) -> str:
    """
    Determine suppression state from trajectory.

    Logic (based on last two steps):
    - If last permission == HOLD → SUPPRESSED
    - If moved toward more restrictive → DEGRADING
    - If moved toward less restrictive → RECOVERING
    - Else → STABLE

    Args:
        trajectory: List of permission labels

    Returns:
        Suppression state label
    """
    if not trajectory:
        return "STABLE"

    current_permission = trajectory[-1]

    # If currently HOLD, state is SUPPRESSED
    if current_permission == "HOLD":
        return "SUPPRESSED"

    # If only one step, state is STABLE
    if len(trajectory) == 1:
        return "STABLE"

    # Compare last two steps
    prev_permission = trajectory[-2]

    # If no change, state is STABLE
    if prev_permission == current_permission:
        return "STABLE"

    # Check direction of change
    prev_order = PERMISSION_ORDER.get(prev_permission, 3)
    curr_order = PERMISSION_ORDER.get(current_permission, 3)

    if curr_order < prev_order:
        # Moving toward more restrictive
        return "DEGRADING"
    elif curr_order > prev_order:
        # Moving toward less restrictive
        return "RECOVERING"
    else:
        return "STABLE"


def get_monitor_v1_info() -> Dict[str, Any]:
    """
    Get monitor v1 information.

    Returns:
        Dict with monitor metadata
    """
    return {
        "monitor_version": "v1",
        "monitor_type": "continuous_permission_monitor",
        "input_schema": "records_window",
        "output_schema": "v12_permission_monitor",
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
    print("v1.2 Continuous Permission Monitor Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Invalid input → ERROR
    print("Test 1: Invalid input → ERROR")
    result1 = monitor_permission_v1(None)
    print(f"Status: {result1['v12_monitor_status']}")
    print(f"Summary: {result1['v12_monitor_summary']}")
    print()

    # Test 2: Constant permission → STABLE
    print("Test 2: Constant permission → STABLE")
    window2 = [
        {"v10_execution_permission": "ALLOW"},
        {"v10_execution_permission": "ALLOW"},
        {"v10_execution_permission": "ALLOW"},
    ]
    result2 = monitor_permission_v1(window2)
    print(f"Status: {result2['v12_monitor_status']}")
    print(f"Current permission: {result2['v12_monitor_current_permission']}")
    print(f"Suppression state: {result2['v12_monitor_suppression_state']}")
    print(f"Trajectory: {result2['v12_monitor_permission_trajectory']}")
    print(f"Events: {len(result2['v12_monitor_transition_events'])}")
    print()

    # Test 3: ALLOW → DRY_RUN_ONLY → DEGRADING
    print("Test 3: ALLOW → DRY_RUN_ONLY → DEGRADING")
    window3 = [
        {"v10_execution_permission": "ALLOW"},
        {"v10_execution_permission": "DRY_RUN_ONLY"},
    ]
    result3 = monitor_permission_v1(window3)
    print(f"Status: {result3['v12_monitor_status']}")
    print(f"Current permission: {result3['v12_monitor_current_permission']}")
    print(f"Suppression state: {result3['v12_monitor_suppression_state']}")
    print(f"Trajectory: {result3['v12_monitor_permission_trajectory']}")
    print(f"Events: {result3['v12_monitor_transition_events']}")
    print()

    # Test 4: DRY_RUN_ONLY → HOLD → SUPPRESSED
    print("Test 4: DRY_RUN_ONLY → HOLD → SUPPRESSED")
    window4 = [
        {"v10_execution_permission": "DRY_RUN_ONLY"},
        {"v10_execution_permission": "HOLD"},
    ]
    result4 = monitor_permission_v1(window4)
    print(f"Status: {result4['v12_monitor_status']}")
    print(f"Current permission: {result4['v12_monitor_current_permission']}")
    print(f"Suppression state: {result4['v12_monitor_suppression_state']}")
    print(f"Trajectory: {result4['v12_monitor_permission_trajectory']}")
    print(f"Events: {result4['v12_monitor_transition_events']}")
    print()

    # Test 5: HOLD → DRY_RUN_ONLY → RECOVERING
    print("Test 5: HOLD → DRY_RUN_ONLY → RECOVERING")
    window5 = [
        {"v10_execution_permission": "HOLD"},
        {"v10_execution_permission": "DRY_RUN_ONLY"},
    ]
    result5 = monitor_permission_v1(window5)
    print(f"Status: {result5['v12_monitor_status']}")
    print(f"Current permission: {result5['v12_monitor_current_permission']}")
    print(f"Suppression state: {result5['v12_monitor_suppression_state']}")
    print(f"Trajectory: {result5['v12_monitor_permission_trajectory']}")
    print(f"Events: {result5['v12_monitor_transition_events']}")
    print()

    # Test 6: Policy override takes priority
    print("Test 6: Policy override takes priority")
    window6 = [
        {"v10_execution_permission": "ALLOW", "v11_policy_permission": "HOLD"},
    ]
    result6 = monitor_permission_v1(window6)
    print(f"Current permission: {result6['v12_monitor_current_permission']}")
    print(f"Basis: {result6['v12_monitor_basis']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
