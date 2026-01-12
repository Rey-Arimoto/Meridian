#!/usr/bin/env python3
"""
PR127: v1.2 Explanation Context Permission Trajectory Extension (READ-ONLY)

Purpose:
    Extend PR122 explanation context with permission trajectory signals.
    Append-only extension (does not modify PR122 core).

Extension Philosophy:
    - PR122 remains unchanged (backward compatible)
    - New signal family: TRAJECTORY_*
    - Maps v12_signal_* to human interface signals
    - Non-prescriptive, label-only signals

New Signal Types:
    - TRAJECTORY_DEGRADING: Permission trajectory moving toward more restrictive
    - TRAJECTORY_RECOVERING: Permission trajectory moving toward less restrictive
    - TRAJECTORY_SUPPRESSED: Permission trajectory currently suppressed
    - TRAJECTORY_STABLE: Permission trajectory stable (no change)

Constitutional Guarantees:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No trajectory coupling: No "degrading therefore stop"
"""

from typing import Any, Dict, List, Optional


def extend_explanation_context_with_trajectory_signals(
    context_record: Dict[str, Any],
    trajectory_signal: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Extend explanation context with trajectory signals.

    Args:
        context_record: PR122 explanation context record
        trajectory_signal: PR127 trajectory signal record

    Returns:
        Extended context record (backward compatible)
    """
    # Defensive: if no trajectory signal, return context unchanged
    if not trajectory_signal or not isinstance(trajectory_signal, dict):
        return context_record

    # Check trajectory signal status
    if trajectory_signal.get("v12_signal_status") != "AVAILABLE":
        # Signal unavailable or error - return context unchanged
        return context_record

    # Create extended context (copy original)
    extended_context = context_record.copy()

    # Extract trajectory signal components
    suppression_state = trajectory_signal.get("v12_signal_suppression_state", "STABLE")
    transition_label = trajectory_signal.get("v12_signal_transition_label", "NONE")

    # Generate trajectory signal labels for human interface
    trajectory_signals = _generate_trajectory_signals(suppression_state, transition_label)

    # Append trajectory signals to context signals
    if "v12_context_signals" in extended_context:
        # Append to existing signals
        existing_signals = extended_context["v12_context_signals"]
        if isinstance(existing_signals, list):
            extended_context["v12_context_signals"] = existing_signals + trajectory_signals
    else:
        # Create new signals array
        extended_context["v12_context_signals"] = trajectory_signals

    # Add trajectory signal basis to context basis
    if "v12_context_basis" in extended_context and "v12_signal_basis" in trajectory_signal:
        existing_basis = extended_context["v12_context_basis"]
        signal_basis = trajectory_signal["v12_signal_basis"]
        if isinstance(existing_basis, list) and isinstance(signal_basis, list):
            extended_context["v12_context_basis"] = existing_basis + signal_basis

    return extended_context


def _generate_trajectory_signals(suppression_state: str, transition_label: str) -> List[str]:
    """
    Generate trajectory signal labels.

    Args:
        suppression_state: Suppression state label
        transition_label: Transition label

    Returns:
        List of trajectory signal labels
    """
    signals = []

    # Map suppression state to trajectory signal
    if suppression_state == "DEGRADING":
        signals.append("TRAJECTORY_DEGRADING")
    elif suppression_state == "RECOVERING":
        signals.append("TRAJECTORY_RECOVERING")
    elif suppression_state == "SUPPRESSED":
        signals.append("TRAJECTORY_SUPPRESSED")
    elif suppression_state == "STABLE":
        signals.append("TRAJECTORY_STABLE")

    # Optionally add transition-specific signal
    if transition_label == "DEGRADATION":
        # Already covered by TRAJECTORY_DEGRADING
        pass
    elif transition_label == "RECOVERY":
        # Already covered by TRAJECTORY_RECOVERING
        pass
    elif transition_label == "SUPPRESSION":
        # Already covered by TRAJECTORY_SUPPRESSED
        pass

    return signals


def get_trajectory_signal_types() -> List[str]:
    """
    Get all trajectory signal types.

    Returns:
        List of trajectory signal type names
    """
    return [
        "TRAJECTORY_DEGRADING",
        "TRAJECTORY_RECOVERING",
        "TRAJECTORY_SUPPRESSED",
        "TRAJECTORY_STABLE",
    ]


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Explain Context Permission Trajectory Extension - Self Test")
    print("=" * 60)
    print()

    # Test 1: Extend context with DEGRADING trajectory
    print("Test 1: Extend context with DEGRADING trajectory")
    context1 = {
        "v12_context_signals": ["REGIME_CALM", "DRIFT_STABLE"],
        "v12_context_basis": ["v10_regime_label", "v10_drift_label"],
    }
    signal1 = {
        "v12_signal_status": "AVAILABLE",
        "v12_signal_suppression_state": "DEGRADING",
        "v12_signal_transition_label": "DEGRADATION",
        "v12_signal_basis": ["v12_monitor_suppression_state"],
    }
    extended1 = extend_explanation_context_with_trajectory_signals(context1, signal1)
    print(f"Original signals: {context1['v12_context_signals']}")
    print(f"Extended signals: {extended1['v12_context_signals']}")
    print(f"Extended basis: {extended1['v12_context_basis']}")
    print()

    # Test 2: Extend context with SUPPRESSED trajectory
    print("Test 2: Extend context with SUPPRESSED trajectory")
    context2 = {
        "v12_context_signals": ["REGIME_VOLATILE"],
        "v12_context_basis": ["v10_regime_label"],
    }
    signal2 = {
        "v12_signal_status": "AVAILABLE",
        "v12_signal_suppression_state": "SUPPRESSED",
        "v12_signal_transition_label": "SUPPRESSION",
        "v12_signal_basis": ["v12_monitor_suppression_state"],
    }
    extended2 = extend_explanation_context_with_trajectory_signals(context2, signal2)
    print(f"Original signals: {context2['v12_context_signals']}")
    print(f"Extended signals: {extended2['v12_context_signals']}")
    print()

    # Test 3: Extend context with RECOVERING trajectory
    print("Test 3: Extend context with RECOVERING trajectory")
    context3 = {
        "v12_context_signals": [],
        "v12_context_basis": [],
    }
    signal3 = {
        "v12_signal_status": "AVAILABLE",
        "v12_signal_suppression_state": "RECOVERING",
        "v12_signal_transition_label": "RECOVERY",
        "v12_signal_basis": ["v12_monitor_suppression_state"],
    }
    extended3 = extend_explanation_context_with_trajectory_signals(context3, signal3)
    print(f"Extended signals: {extended3['v12_context_signals']}")
    print()

    # Test 4: Signal unavailable - context unchanged
    print("Test 4: Signal unavailable - context unchanged")
    context4 = {
        "v12_context_signals": ["REGIME_CALM"],
        "v12_context_basis": ["v10_regime_label"],
    }
    signal4 = {
        "v12_signal_status": "ERROR",
    }
    extended4 = extend_explanation_context_with_trajectory_signals(context4, signal4)
    print(f"Original signals: {context4['v12_context_signals']}")
    print(f"Extended signals: {extended4['v12_context_signals']}")
    print(f"Context unchanged: {context4['v12_context_signals'] == extended4['v12_context_signals']}")
    print()

    # Test 5: Get all trajectory signal types
    print("Test 5: Get all trajectory signal types")
    signal_types = get_trajectory_signal_types()
    print(f"Trajectory signal types: {signal_types}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
