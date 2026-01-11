#!/usr/bin/env python3
"""
PR105: v1.0 Execution Audit Trail Engine v1 (READ-ONLY)

Purpose:
    Build execution audit trail from artifact chain.
    Audit Trail = Causal Chain Documentation (not execution).

Constitutional Constraints:
    - READ-ONLY: No execution logic or trading
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - No amounts: No numeric values, prices, quantities
    - No token literals: No SUI, USDC, BTC, etc.
    - No addresses: No wallet/contract addresses

Engine Philosophy:
    Audit Trail Engine v1 = Static Chain Aggregation

    Links artifacts in fixed order:
    1. INTERPRETATION_ANALYTICS (PR64)
    2. BLINDSPOT (PR81)
    3. BOUNDARY (PR91)
    4. PERMISSION (PR101)
    5. PLAN (PR103)
    6. SIMULATION (PR104)

    Engine does NOT:
    - Execute (no trading, no wallet, no transactions)
    - Evaluate (no good/bad judgment)
    - Recommend (no should/must)

Design:
    - Fixed layer order (no reordering)
    - Warning-only (never raises, always returns valid record)
    - Defensive (accepts None/invalid, emits UNAVAILABLE)
"""

from typing import Any, Dict, List, Optional
from .v10_execution_audit_trail_schema import V10ExecutionAuditTrailSchema


def build_execution_audit_trail_v1(
    interpretation_analytics: Optional[Dict[str, Any]] = None,
    blindspot_record: Optional[Dict[str, Any]] = None,
    boundary_record: Optional[Dict[str, Any]] = None,
    permission_record: Optional[Dict[str, Any]] = None,
    plan_record: Optional[Dict[str, Any]] = None,
    simulation_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build execution audit trail from artifact chain.

    Args:
        interpretation_analytics: PR64 interpretation analytics (optional)
        blindspot_record: PR81 blindspot record (optional)
        boundary_record: PR91 boundary record (optional)
        permission_record: PR101 permission record (optional)
        plan_record: PR103 plan record (optional)
        simulation_record: PR104 simulation record (optional)

    Returns:
        v10 audit trail record with causal chain

    Design:
        - Fixed layer order (cannot reorder)
        - Defensive (None/invalid → skip layer)
        - Warning-only (never raises)
        - Always returns valid audit trail record
    """
    # Initialize audit trail record with safe defaults
    audit_trail = V10ExecutionAuditTrailSchema.create_empty_record()

    # Track chain events
    chain_events = []
    layer_count = 0

    # Layer 1: INTERPRETATION_ANALYTICS (PR64)
    if interpretation_analytics and isinstance(interpretation_analytics, dict):
        artifact = "pr64_interpretation_analytics"
        basis = []

        # Extract common basis fields if available
        if "meaning_tag_counts" in interpretation_analytics:
            basis.append("meaning_tag_counts")
        if "factor_counts" in interpretation_analytics:
            basis.append("factor_counts")
        if "signal_counts" in interpretation_analytics:
            basis.append("signal_counts")

        event = V10ExecutionAuditTrailSchema.create_chain_event(
            "INTERPRETATION_ANALYTICS",
            artifact,
            basis
        )
        chain_events.append(event)
        layer_count += 1

    # Layer 2: BLINDSPOT (PR81)
    if blindspot_record and isinstance(blindspot_record, dict):
        artifact = "pr81_blindspot_record"
        basis = []

        if "v8_blindspot_tag" in blindspot_record:
            basis.append("v8_blindspot_tag")
        if "v8_blindspot_basis" in blindspot_record:
            basis.append("v8_blindspot_basis")

        event = V10ExecutionAuditTrailSchema.create_chain_event(
            "BLINDSPOT",
            artifact,
            basis
        )
        chain_events.append(event)
        layer_count += 1

    # Layer 3: BOUNDARY (PR91)
    if boundary_record and isinstance(boundary_record, dict):
        artifact = "pr91_boundary_record"
        basis = []

        if "v9_boundary_type" in boundary_record:
            basis.append("v9_boundary_type")
        if "v9_boundary_basis" in boundary_record:
            basis.append("v9_boundary_basis")

        event = V10ExecutionAuditTrailSchema.create_chain_event(
            "BOUNDARY",
            artifact,
            basis
        )
        chain_events.append(event)
        layer_count += 1

    # Layer 4: PERMISSION (PR101)
    if permission_record and isinstance(permission_record, dict):
        artifact = "pr101_execution_record"
        basis = []

        if "v10_execution_permission" in permission_record:
            basis.append("v10_execution_permission")
        if "v10_execution_basis" in permission_record:
            basis.append("v10_execution_basis")

        event = V10ExecutionAuditTrailSchema.create_chain_event(
            "PERMISSION",
            artifact,
            basis
        )
        chain_events.append(event)
        layer_count += 1

    # Layer 5: PLAN (PR103)
    if plan_record and isinstance(plan_record, dict):
        artifact = "pr103_plan_record"
        basis = []

        if "v10_plan_type" in plan_record:
            basis.append("v10_plan_type")
        if "v10_plan_constraints" in plan_record:
            basis.append("v10_plan_constraints")
        if "v10_plan_basis" in plan_record:
            basis.append("v10_plan_basis")

        event = V10ExecutionAuditTrailSchema.create_chain_event(
            "PLAN",
            artifact,
            basis
        )
        chain_events.append(event)
        layer_count += 1

    # Layer 6: SIMULATION (PR104)
    if simulation_record and isinstance(simulation_record, dict):
        artifact = "pr104_simulation_record"
        basis = []

        if "v10_simulation_type" in simulation_record:
            basis.append("v10_simulation_type")
        if "v10_simulation_basis" in simulation_record:
            basis.append("v10_simulation_basis")

        event = V10ExecutionAuditTrailSchema.create_chain_event(
            "SIMULATION",
            artifact,
            basis
        )
        chain_events.append(event)
        layer_count += 1

    # Set audit trail status
    if layer_count > 0:
        audit_trail["v10_audit_mode"] = "ON"
        audit_trail["v10_audit_status"] = "AVAILABLE"
        audit_trail["v10_audit_chain"] = chain_events

        # Generate summary
        layer_desc = "multiple layers" if layer_count > 1 else "layer"
        audit_trail["v10_audit_summary"] = (
            f"audit trail built with {layer_desc} of causal chain. "
            f"chain links interpretation through simulation."
        )
    else:
        # No layers provided
        audit_trail["v10_audit_summary"] = (
            "audit trail unavailable. no artifact records provided."
        )

    return audit_trail


def get_audit_trail_engine_v1_info() -> Dict[str, Any]:
    """
    Get audit trail engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "causal_chain_trace",
        "chain_layers": [
            "INTERPRETATION_ANALYTICS",
            "BLINDSPOT",
            "BOUNDARY",
            "PERMISSION",
            "PLAN",
            "SIMULATION",
        ],
        "chain_order": "fixed",
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Execution Audit Trail Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Full chain
    print("Test 1: Full chain")
    blindspot = {
        "v8_blindspot_tag": "ABSENCE_INSUFFICIENT_EVIDENCE",
        "v8_blindspot_basis": ["meaning_tag_counts"],
    }
    boundary = {
        "v9_boundary_type": "DATA_BOUNDARY",
        "v9_boundary_basis": ["v8_blindspot_tag"],
    }
    permission = {
        "v10_execution_permission": "HOLD",
        "v10_execution_basis": ["v9_boundary_type"],
    }
    plan = {
        "v10_plan_type": "NOOP",
        "v10_plan_constraints": ["manual_approval"],
        "v10_plan_basis": ["v10_execution_permission"],
    }
    simulation = {
        "v10_simulation_type": "PLAN_APPLICABILITY_SCAN",
        "v10_simulation_basis": ["v10_plan_constraints"],
    }

    trail = build_execution_audit_trail_v1(
        blindspot_record=blindspot,
        boundary_record=boundary,
        permission_record=permission,
        plan_record=plan,
        simulation_record=simulation,
    )
    print(json.dumps(trail, indent=2))
    print()

    # Test 2: Empty chain
    print("Test 2: Empty chain (None inputs)")
    trail_empty = build_execution_audit_trail_v1()
    print(json.dumps(trail_empty, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
