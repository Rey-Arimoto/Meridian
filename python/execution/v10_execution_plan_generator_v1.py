#!/usr/bin/env python3
"""
PR103: v1.0 Execution Plan Generator v1 (READ-ONLY)

Purpose:
    Generate execution plan records based on permission and boundary analysis.
    Plan Generator = Static Plan Synthesis.

Constitutional Constraints:
    - READ-ONLY: No execution logic or trading
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - No amounts: No numeric values, prices, quantities
    - No token literals: No SUI, USDC, BTC, etc.
    - No addresses: No wallet/contract addresses
    - Execution safety: No trading vocabulary

Generator Philosophy:
    Plan Generator v1 = Static Permission-to-Plan Mapping

    Based on execution permission (v10), generate a plan record
    describing the structural plan shape.

    Generator does NOT:
    - Trade (swap, transfer, send, approve, sign)
    - Make recommendations (should/must)
    - Include amounts, prices, or token names
    - Generate addresses or wallet interactions

Plan Generation Rules (v1 - Static):
    HOLD         → NOOP + manual_approval
    UNKNOWN      → UNCLASSIFIED + manual_approval
    DRY_RUN_ONLY → MAINTENANCE + dry_run_only + frequency_limit
    ALLOW        → (intent-based) + manual_approval

Design:
    - Static if/elif rules (no learning, no inference)
    - Warning-only (never raises, always returns valid record)
    - Transparent mapping (no hidden logic)
"""

from typing import Any, Dict, Optional
from .v10_execution_plan_schema import V10ExecutionPlanSchema


def generate_execution_plan_v1(
    execution_record: Optional[Dict[str, Any]] = None,
    boundary_record: Optional[Dict[str, Any]] = None,
    blindspot_record: Optional[Dict[str, Any]] = None,
    reflection_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate execution plan based on permission and boundary analysis.

    Args:
        execution_record: v10 execution record (required for permission)
        boundary_record: v9 boundary record (optional for context)
        blindspot_record: v8 blindspot record (optional for context)
        reflection_record: v7 reflection record (optional for context)

    Returns:
        v10 plan record with plan type and constraints

    Design:
        - Static permission → plan type mapping
        - No learning, no inference
        - Warning-only (never raises)
        - Always returns valid v10 plan record
    """
    # Initialize plan record with safe defaults
    plan_record = V10ExecutionPlanSchema.create_empty_record()

    # Track basis fields referenced
    basis_fields = []

    # Handle None or invalid execution_record
    if execution_record is None or not isinstance(execution_record, dict):
        plan_record["v10_plan_description"] = (
            "plan unavailable. execution record not provided."
        )
        return plan_record

    # Extract execution permission (required)
    permission = execution_record.get("v10_execution_permission", "UNKNOWN")
    basis_fields.append("v10_execution_permission")

    # Check if execution is available
    execution_mode = execution_record.get("v10_execution_mode", "OFF")
    execution_status = execution_record.get("v10_execution_status", "UNAVAILABLE")

    if execution_mode != "ON" or execution_status != "AVAILABLE":
        plan_record["v10_plan_description"] = (
            "plan unavailable. execution not available."
        )
        plan_record["v10_plan_basis"] = basis_fields
        return plan_record

    # Set plan mode and status
    plan_record["v10_plan_mode"] = "ON"
    plan_record["v10_plan_status"] = "AVAILABLE"

    # Static plan generation rules (v1)
    if permission == "HOLD":
        # HOLD: Execution structurally disallowed
        plan_record["v10_plan_type"] = "NOOP"
        plan_record["v10_plan_description"] = (
            "no-op plan emitted because execution is structurally disallowed."
        )
        plan_record["v10_plan_constraints"] = ["manual_approval"]

    elif permission == "UNKNOWN":
        # UNKNOWN: Insufficient clarity
        plan_record["v10_plan_type"] = "UNCLASSIFIED"
        plan_record["v10_plan_description"] = (
            "plan unclassified due to insufficient structural clarity."
        )
        plan_record["v10_plan_constraints"] = ["manual_approval"]

    elif permission == "DRY_RUN_ONLY":
        # DRY_RUN_ONLY: Observation-only execution
        plan_record["v10_plan_type"] = "MAINTENANCE"
        plan_record["v10_plan_description"] = (
            "maintenance plan available in dry-run-only mode due to boundary constraints."
        )
        plan_record["v10_plan_constraints"] = [
            "dry_run_only",
            "frequency_limit_once_per_day",
        ]

        # Add boundary context to basis if available
        if boundary_record and isinstance(boundary_record, dict):
            boundary_type = boundary_record.get("v9_boundary_type")
            if boundary_type:
                basis_fields.append("v9_boundary_type")

    elif permission == "ALLOW":
        # ALLOW: Structurally permitted (rare in v1)
        # Use execution intent to determine plan type
        intent = execution_record.get("v10_execution_intent", "NONE")
        basis_fields.append("v10_execution_intent")

        if intent == "REBALANCE_INTENT":
            plan_record["v10_plan_type"] = "REBALANCE"
            plan_record["v10_plan_description"] = (
                "rebalance plan shape available under allow permission; manual approval required."
            )
        elif intent == "HEDGE_INTENT":
            plan_record["v10_plan_type"] = "HEDGE"
            plan_record["v10_plan_description"] = (
                "hedge plan shape available under allow permission; manual approval required."
            )
        elif intent == "LIQUIDITY_INTENT":
            plan_record["v10_plan_type"] = "LIQUIDITY"
            plan_record["v10_plan_description"] = (
                "liquidity plan shape available under allow permission; manual approval required."
            )
        elif intent == "MAINTENANCE":
            plan_record["v10_plan_type"] = "MAINTENANCE"
            plan_record["v10_plan_description"] = (
                "maintenance plan shape available under allow permission; manual approval required."
            )
        else:
            # NONE or other
            plan_record["v10_plan_type"] = "UNCLASSIFIED"
            plan_record["v10_plan_description"] = (
                "plan shape unclassified under allow permission; manual approval required."
            )

        # Always require manual approval for ALLOW in v1
        plan_record["v10_plan_constraints"] = ["manual_approval"]

    else:
        # Unknown permission value (edge case)
        plan_record["v10_plan_type"] = "UNCLASSIFIED"
        plan_record["v10_plan_description"] = (
            f"plan unclassified due to unrecognized permission: {permission}."
        )
        plan_record["v10_plan_constraints"] = ["manual_approval"]

    # Set basis
    plan_record["v10_plan_basis"] = basis_fields

    return plan_record


def get_generator_v1_info() -> Dict[str, Any]:
    """
    Get plan generator v1 information.

    Returns:
        Dict with generator metadata
    """
    return {
        "generator_version": "v1",
        "generator_type": "static_plan_synthesis",
        "input_fields": [
            "v10_execution_permission",
            "v10_execution_intent",
            "v9_boundary_type",
        ],
        "generation_rules": {
            "HOLD": {
                "plan_type": "NOOP",
                "constraints": ["manual_approval"],
            },
            "UNKNOWN": {
                "plan_type": "UNCLASSIFIED",
                "constraints": ["manual_approval"],
            },
            "DRY_RUN_ONLY": {
                "plan_type": "MAINTENANCE",
                "constraints": ["dry_run_only", "frequency_limit_once_per_day"],
            },
            "ALLOW": {
                "plan_type": "intent_based",
                "constraints": ["manual_approval"],
            },
        },
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Execution Plan Generator v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: HOLD → NOOP
    print("Test 1: HOLD → NOOP")
    execution1 = {
        "v10_execution_mode": "ON",
        "v10_execution_status": "AVAILABLE",
        "v10_execution_permission": "HOLD",
        "v10_execution_intent": "NONE",
    }
    plan1 = generate_execution_plan_v1(execution1)
    print(json.dumps(plan1, indent=2))
    print()

    # Test 2: DRY_RUN_ONLY → MAINTENANCE
    print("Test 2: DRY_RUN_ONLY → MAINTENANCE")
    execution2 = {
        "v10_execution_mode": "ON",
        "v10_execution_status": "AVAILABLE",
        "v10_execution_permission": "DRY_RUN_ONLY",
        "v10_execution_intent": "NONE",
    }
    boundary2 = {
        "v9_boundary_type": "TEMPORAL_BOUNDARY",
    }
    plan2 = generate_execution_plan_v1(execution2, boundary2)
    print(json.dumps(plan2, indent=2))
    print()

    # Test 3: ALLOW + REBALANCE_INTENT → REBALANCE
    print("Test 3: ALLOW + REBALANCE_INTENT → REBALANCE")
    execution3 = {
        "v10_execution_mode": "ON",
        "v10_execution_status": "AVAILABLE",
        "v10_execution_permission": "ALLOW",
        "v10_execution_intent": "REBALANCE_INTENT",
    }
    plan3 = generate_execution_plan_v1(execution3)
    print(json.dumps(plan3, indent=2))
    print()

    # Test 4: None input (graceful handling)
    print("Test 4: None input → UNAVAILABLE")
    plan4 = generate_execution_plan_v1(None)
    print(json.dumps(plan4, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
