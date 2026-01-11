#!/usr/bin/env python3
"""
PR121: v1.0 Drift → Execution Policy Binding v1 (READ-ONLY)

Purpose:
    Bind drift classification to execution permission (conservative).
    Drift gates execution based on structural stability.

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - Conservative: High/critical drift → restrictive permissions
    - Drift binding = classification gate only

Binding Philosophy:
    Binding ≠ Action
    Binding ≠ Recommendation
    Binding = Constitutional Gate

    Binding provides:
    - Permission override based on drift level
    - Constraint labels (drift classification only)
    - Conservative degradation under high drift

    Binding does NOT:
    - Execute trades
    - Recommend specific actions
    - Evaluate drift quality
    - Contain numeric patterns

Static Binding Rules (v1 - Conservative):
    - DRIFT_CRITICAL → HOLD + constraint: drift_critical_observed
    - DRIFT_HIGH → DRY_RUN_ONLY + constraint: drift_high_observed
    - DRIFT_MEDIUM → no override + constraint: drift_medium_observed
    - DRIFT_LOW → no override + constraint: drift_low_observed
    - DRIFT_NONE → no override + constraint: drift_none_observed
    - UNCLASSIFIED → no override + constraint: drift_unclassified

Permission Override Logic:
    - HOLD: Hard stop (critical drift)
    - DRY_RUN_ONLY: Simulation only (high drift)
    - No override: Defer to upstream execution engine
"""

from typing import Any, Dict, List, Optional


def bind_drift_to_execution_policy_v1(
    execution_record: Optional[Dict[str, Any]] = None,
    drift_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Bind drift classification to execution permission (conservative).

    Args:
        execution_record: v10 execution record
        drift_record: v10 drift record

    Returns:
        Enhanced execution record with drift-based permission override

    Design:
        - Overrides execution_permission based on drift level
        - Adds drift constraint labels to execution_constraints
        - Conservative rules (critical/high → restrictive)
        - Defensive (None → return original or empty)
        - Warning-only (never raises)
    """
    # Defensive: validate inputs
    if execution_record is None or not isinstance(execution_record, dict):
        # Return minimal valid execution if input invalid
        from execution.v10_execution_schema import V10ExecutionSchema
        return V10ExecutionSchema.create_empty_record()

    if drift_record is None or not isinstance(drift_record, dict):
        # No drift to bind → return original execution
        return execution_record.copy()

    # Copy execution record (defensive)
    enhanced = execution_record.copy()

    # Extract drift information
    drift_mode = drift_record.get("v10_drift_mode", "OFF")
    drift_status = drift_record.get("v10_drift_status", "UNAVAILABLE")
    drift_level = drift_record.get("v10_drift_level", "UNCLASSIFIED")

    # Only bind if drift is AVAILABLE
    if drift_mode == "ON" and drift_status == "AVAILABLE":
        # Add drift artifacts reference
        artifacts = enhanced.get("v10_execution_artifacts", [])
        if not isinstance(artifacts, list):
            artifacts = []

        # Add drift artifact reference (string only, no data)
        if "pr120_drift_record" not in artifacts:
            artifacts.append("pr120_drift_record")

        enhanced["v10_execution_artifacts"] = artifacts

        # Add drift level to execution basis (safe, non-numeric label)
        basis = enhanced.get("v10_execution_basis", [])
        if not isinstance(basis, list):
            basis = []

        # Add drift level to basis if not already present
        if "v10_drift_level" not in basis:
            basis.append("v10_drift_level")

        enhanced["v10_execution_basis"] = basis

        # Apply drift-based permission override (conservative)
        permission_override, constraint_label = _classify_drift_permission_override(drift_level)

        # Override permission if override is more restrictive
        current_permission = enhanced.get("v10_execution_permission", "UNKNOWN")
        enhanced["v10_execution_permission"] = _select_more_restrictive_permission(
            current_permission, permission_override
        )

        # Add drift constraint label
        constraints = enhanced.get("v10_execution_constraints", [])
        if not isinstance(constraints, list):
            constraints = []

        # Add constraint label if not already present
        if constraint_label and constraint_label not in constraints:
            constraints.append(constraint_label)

        enhanced["v10_execution_constraints"] = constraints

        # Update execution summary with drift context (non-prescriptive)
        summary = enhanced.get("v10_execution_summary", "")
        if isinstance(summary, str):
            # Append drift binding context
            drift_context = f" drift-based permission binding applied. {constraint_label}."
            if drift_context not in summary:
                enhanced["v10_execution_summary"] = f"{summary}{drift_context}"

    return enhanced


def _classify_drift_permission_override(drift_level: str) -> tuple[str, str]:
    """
    Classify permission override and constraint label from drift level.

    Args:
        drift_level: Drift classification level

    Returns:
        Tuple of (permission_override, constraint_label)

    Note:
        Conservative rules: critical/high → restrictive permissions
    """
    # Static binding rules (conservative)
    bindings = {
        "DRIFT_CRITICAL": ("HOLD", "drift_critical_observed"),
        "DRIFT_HIGH": ("DRY_RUN_ONLY", "drift_high_observed"),
        "DRIFT_MEDIUM": ("UNKNOWN", "drift_medium_observed"),  # No override
        "DRIFT_LOW": ("UNKNOWN", "drift_low_observed"),  # No override
        "DRIFT_NONE": ("UNKNOWN", "drift_none_observed"),  # No override
        "UNCLASSIFIED": ("UNKNOWN", "drift_unclassified"),  # No override
    }

    return bindings.get(drift_level, ("UNKNOWN", "drift_unknown"))


def _select_more_restrictive_permission(
    current: str,
    override: str,
) -> str:
    """
    Select more restrictive permission between current and override.

    Args:
        current: Current permission level
        override: Override permission level

    Returns:
        More restrictive permission

    Note:
        Restrictiveness order: HOLD > DRY_RUN_ONLY > ALLOW > UNKNOWN
    """
    # Define restrictiveness order (most restrictive first)
    restrictiveness = {
        "HOLD": 4,
        "DRY_RUN_ONLY": 3,
        "ALLOW": 2,
        "UNKNOWN": 1,
    }

    current_level = restrictiveness.get(current, 0)
    override_level = restrictiveness.get(override, 0)

    # Return more restrictive permission
    if override_level > current_level:
        return override
    else:
        return current


def get_drift_execution_binding_v1_info() -> Dict[str, Any]:
    """
    Get drift execution binding v1 information.

    Returns:
        Dict with binding metadata
    """
    return {
        "binding_version": "v1",
        "binding_type": "drift_to_execution_permission",
        "binding_approach": "conservative_permission_override",
        "permission_rules": {
            "DRIFT_CRITICAL": "HOLD",
            "DRIFT_HIGH": "DRY_RUN_ONLY",
            "DRIFT_MEDIUM": "no_override",
            "DRIFT_LOW": "no_override",
            "DRIFT_NONE": "no_override",
            "UNCLASSIFIED": "no_override",
        },
        "defensive": True,
        "warning_only": True,
        "constitutional_validation": True,
        "no_numeric_output": True,
        "no_prescriptive_language": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Drift → Execution Policy Binding v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Valid execution + DRIFT_CRITICAL (should override to HOLD)
    print("Test 1: Valid execution + DRIFT_CRITICAL (override to HOLD)")
    from execution.v10_execution_schema import V10ExecutionSchema

    execution = V10ExecutionSchema.create_empty_record()
    execution["v10_execution_permission"] = "UNKNOWN"
    execution["v10_execution_summary"] = "execution permission classified."

    drift_critical = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "AVAILABLE",
        "v10_drift_level": "DRIFT_CRITICAL",
    }

    enhanced_critical = bind_drift_to_execution_policy_v1(execution, drift_critical)
    print(f"Permission: {enhanced_critical.get('v10_execution_permission')}")
    print(f"Constraints: {enhanced_critical.get('v10_execution_constraints', [])}")
    print(f"Override to HOLD: {enhanced_critical.get('v10_execution_permission') == 'HOLD'}")
    print()

    # Test 2: Valid execution + DRIFT_HIGH (should override to DRY_RUN_ONLY)
    print("Test 2: Valid execution + DRIFT_HIGH (override to DRY_RUN_ONLY)")
    drift_high = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "AVAILABLE",
        "v10_drift_level": "DRIFT_HIGH",
    }

    enhanced_high = bind_drift_to_execution_policy_v1(execution, drift_high)
    print(f"Permission: {enhanced_high.get('v10_execution_permission')}")
    print(f"Constraints: {enhanced_high.get('v10_execution_constraints', [])}")
    print(f"Override to DRY_RUN_ONLY: {enhanced_high.get('v10_execution_permission') == 'DRY_RUN_ONLY'}")
    print()

    # Test 3: Valid execution + DRIFT_LOW (no override)
    print("Test 3: Valid execution + DRIFT_LOW (no override)")
    drift_low = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "AVAILABLE",
        "v10_drift_level": "DRIFT_LOW",
    }

    enhanced_low = bind_drift_to_execution_policy_v1(execution, drift_low)
    print(f"Permission: {enhanced_low.get('v10_execution_permission')}")
    print(f"Constraints: {enhanced_low.get('v10_execution_constraints', [])}")
    print(f"No override (stays UNKNOWN): {enhanced_low.get('v10_execution_permission') == 'UNKNOWN'}")
    print()

    # Test 4: HOLD permission + DRIFT_LOW (should keep HOLD - more restrictive)
    print("Test 4: HOLD permission + DRIFT_LOW (keep HOLD - more restrictive)")
    execution_hold = V10ExecutionSchema.create_empty_record()
    execution_hold["v10_execution_permission"] = "HOLD"

    enhanced_keep_hold = bind_drift_to_execution_policy_v1(execution_hold, drift_low)
    print(f"Permission: {enhanced_keep_hold.get('v10_execution_permission')}")
    print(f"Keeps HOLD: {enhanced_keep_hold.get('v10_execution_permission') == 'HOLD'}")
    print()

    # Test 5: None inputs (defensive)
    print("Test 5: None inputs (defensive)")
    enhanced_none = bind_drift_to_execution_policy_v1(None, None)
    print(f"Returns valid record: {enhanced_none.get('v10_execution_mode') == 'ON'}")
    print(f"Status: {enhanced_none.get('v10_execution_status')}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
