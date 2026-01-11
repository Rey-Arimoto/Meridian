#!/usr/bin/env python3
"""
PR104: v1.0 Execution Simulation Engine v1 (READ-ONLY)

Purpose:
    Simulate plan applicability based on plan constraints.
    Simulation = Plan Applicability Scan (not execution).

Constitutional Constraints:
    - READ-ONLY: No execution logic or trading
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - No amounts: No numeric values, prices, quantities
    - No token literals: No SUI, USDC, BTC, etc.
    - No addresses: No wallet/contract addresses

Engine Philosophy:
    Simulation Engine v1 = Static Plan Applicability Scanner

    Based on plan constraints (v10_plan), enumerate how
    constraints affect plan applicability.

    Engine does NOT:
    - Execute (no trading, no wallet, no transactions)
    - Calculate PnL (no profit/loss)
    - Evaluate (no good/bad judgment)
    - Optimize (no improvement suggestions)
    - Inspect market data (no raw numbers)

Simulation Logic (v1):
    1. Check plan availability
    2. Enumerate constraints as events
    3. Determine applicability based on constraints
    4. Generate trace of constraint applications

Design:
    - Static constraint enumeration (no learning, no inference)
    - Warning-only (never raises, always returns valid record)
    - Transparent logic (no hidden behavior)
"""

from typing import Any, Dict, List, Optional
from .v10_execution_simulation_schema import V10ExecutionSimulationSchema


def simulate_execution_plan_v1(
    plan_record: Optional[Dict[str, Any]] = None,
    window_spec: str = "WINDOW_UNSPECIFIED",
    observation_summaries: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Simulate plan applicability based on constraints.

    Args:
        plan_record: v10 plan record (required)
        window_spec: Time window specification (optional, for tracing only)
        observation_summaries: Optional observation context (for tracing only)

    Returns:
        v10 simulation record with applicability analysis

    Design:
        - Enumerate plan constraints
        - Generate constraint application events
        - Determine applicability
        - No execution, no PnL, no evaluation
    """
    # Initialize simulation record with safe defaults
    simulation_record = V10ExecutionSimulationSchema.create_empty_record()

    # Track basis fields referenced
    basis_fields = []

    # Track trace events
    trace_events = []

    # Handle None or invalid plan_record
    if plan_record is None or not isinstance(plan_record, dict):
        simulation_record["v10_simulation_summary"] = (
            "simulation unavailable. plan record not provided."
        )
        return simulation_record

    # Extract plan fields
    plan_mode = plan_record.get("v10_plan_mode", "OFF")
    plan_status = plan_record.get("v10_plan_status", "UNAVAILABLE")
    plan_type = plan_record.get("v10_plan_type", "NOOP")
    plan_constraints = plan_record.get("v10_plan_constraints", [])

    basis_fields.append("v10_plan_mode")
    basis_fields.append("v10_plan_status")

    # Check if plan is available
    if plan_mode != "ON" or plan_status != "AVAILABLE":
        simulation_record["v10_simulation_summary"] = (
            "simulation unavailable. plan not available."
        )
        simulation_record["v10_simulation_basis"] = basis_fields
        return simulation_record

    # Set simulation mode and status
    simulation_record["v10_simulation_mode"] = "ON"
    simulation_record["v10_simulation_status"] = "AVAILABLE"
    simulation_record["v10_simulation_type"] = "PLAN_APPLICABILITY_SCAN"

    basis_fields.append("v10_plan_type")
    basis_fields.append("v10_plan_constraints")

    # Enumerate constraints and generate events
    constraint_count = 0

    if isinstance(plan_constraints, list):
        for constraint in plan_constraints:
            if not isinstance(constraint, str):
                continue

            constraint_lower = constraint.lower()

            # Generate constraint application events
            if "dry_run_only" in constraint_lower or "dry_run" in constraint_lower:
                event = V10ExecutionSimulationSchema.create_trace_event(
                    "CONSTRAINT_APPLIED",
                    "dry-run-only constraint applied. execution limited to observation mode.",
                    ["v10_plan_constraints"]
                )
                trace_events.append(event)
                constraint_count += 1

            elif "manual_approval" in constraint_lower or "manual" in constraint_lower:
                event = V10ExecutionSimulationSchema.create_trace_event(
                    "CONSTRAINT_APPLIED",
                    "manual approval constraint applied. human review required.",
                    ["v10_plan_constraints"]
                )
                trace_events.append(event)
                constraint_count += 1

            elif "frequency_limit" in constraint_lower or "frequency" in constraint_lower:
                event = V10ExecutionSimulationSchema.create_trace_event(
                    "CONSTRAINT_APPLIED",
                    "frequency limit constraint applied. rate limiting active.",
                    ["v10_plan_constraints"]
                )
                trace_events.append(event)
                constraint_count += 1

            elif "time_window" in constraint_lower or "window" in constraint_lower:
                event = V10ExecutionSimulationSchema.create_trace_event(
                    "CONSTRAINT_APPLIED",
                    "time window constraint applied. execution restricted to specified window.",
                    ["v10_plan_constraints"]
                )
                trace_events.append(event)
                constraint_count += 1

    # Determine applicability
    if constraint_count > 0:
        # Plan has constraints - use descriptive text instead of numbers
        constraint_desc = "multiple constraints" if constraint_count > 1 else "constraint"

        event = V10ExecutionSimulationSchema.create_trace_event(
            "PLAN_APPLICABLE",
            f"plan applicable under {constraint_desc}. constraints enumerated above.",
            ["v10_plan_constraints"]
        )
        trace_events.append(event)

        simulation_record["v10_simulation_summary"] = (
            f"plan applicability scan complete. plan type {plan_type} applicable under {constraint_desc}."
        )
    else:
        # Plan has no constraints (rare in v1)
        event = V10ExecutionSimulationSchema.create_trace_event(
            "PLAN_APPLICABLE",
            "plan applicable with no constraints detected.",
            ["v10_plan_constraints"]
        )
        trace_events.append(event)

        simulation_record["v10_simulation_summary"] = (
            f"plan applicability scan complete. plan type {plan_type} applicable with no constraints."
        )

    # Set basis and trace
    simulation_record["v10_simulation_basis"] = basis_fields
    simulation_record["v10_simulation_trace"] = trace_events

    return simulation_record


def get_simulation_engine_v1_info() -> Dict[str, Any]:
    """
    Get simulation engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "plan_applicability_scan",
        "input_fields": [
            "v10_plan_mode",
            "v10_plan_status",
            "v10_plan_type",
            "v10_plan_constraints",
        ],
        "constraint_types": [
            "dry_run_only",
            "manual_approval",
            "frequency_limit",
            "time_window",
        ],
        "event_types": [
            "CONSTRAINT_APPLIED",
            "PLAN_APPLICABLE",
            "PLAN_NOT_APPLIED",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Execution Simulation Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Plan with constraints
    print("Test 1: Plan with dry_run_only constraint")
    plan1 = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": "MAINTENANCE",
        "v10_plan_constraints": ["dry_run_only", "frequency_limit_once_per_day"],
    }
    sim1 = simulate_execution_plan_v1(plan1)
    print(json.dumps(sim1, indent=2))
    print()

    # Test 2: Plan with manual_approval
    print("Test 2: Plan with manual_approval constraint")
    plan2 = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": "REBALANCE",
        "v10_plan_constraints": ["manual_approval"],
    }
    sim2 = simulate_execution_plan_v1(plan2)
    print(json.dumps(sim2, indent=2))
    print()

    # Test 3: None input (graceful handling)
    print("Test 3: None input → UNAVAILABLE")
    sim3 = simulate_execution_plan_v1(None)
    print(json.dumps(sim3, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
