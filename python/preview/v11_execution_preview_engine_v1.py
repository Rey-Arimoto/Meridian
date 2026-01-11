#!/usr/bin/env python3
"""
PR112: v1.1 Execution Preview Engine v1 (READ-ONLY)

Purpose:
    Generate execution preview from plan, simulation, regime, and policy.
    Preview = Impact Shape Description (not simulation/execution).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No amounts: Impact types only (INCREASE/DECREASE/NONE)
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad, profitable/unprofitable vocabulary
    - Defensive: Never raises, returns valid records

Preview Philosophy:
    Preview ≠ Simulation ≠ Execution

    Simulation (PR104): "Is this plan applicable under constraints?"
    Preview (PR112): "What kind of impact would this plan have, structurally?"
    Execution: Not allowed here

    Preview provides:
    - Impact shape awareness
    - Human review enablement
    - Structural understanding
    - Pre-execution visibility

    Preview does NOT provide:
    - Action recommendations
    - Optimization suggestions
    - Numeric outcomes
    - Profitability analysis

Preview Rules (v1):

Exposure Change:
    NOOP / MAINTENANCE → NONE
    REBALANCE → INCREASE or DECREASE (plan-dependent)
    HEDGE → DECREASE
    LIQUIDITY → INCREASE
    UNCLASSIFIED → NONE

Interaction Type:
    MAINTENANCE → NONE
    REBALANCE → POOL_TOUCH
    HEDGE → POOL_TOUCH
    LIQUIDITY → POOL_TOUCH
    NOOP → NONE

Risk Surface (Regime-Aware):
    REGIME_LOW → LOW
    REGIME_MEDIUM → MEDIUM
    REGIME_HIGH → HIGH
    REGIME_CRITICAL → BLOCKED (not preview)

Special Cases:
    - If REGIME_CRITICAL: Preview BLOCKED
    - If policy permission = HOLD: Preview BLOCKED
    - If simulation not applicable: Preview ERROR
    - If plan not available: Preview ERROR
"""

from typing import Any, Dict, Optional
from .v11_execution_preview_schema import V11ExecutionPreviewSchema


def generate_execution_preview_v1(
    plan_record: Optional[Dict[str, Any]] = None,
    simulation_record: Optional[Dict[str, Any]] = None,
    regime_record: Optional[Dict[str, Any]] = None,
    policy_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate execution preview from upstream records.

    Args:
        plan_record: Execution plan record (from PR103)
        simulation_record: Simulation record (from PR104)
        regime_record: Regime classification record (from PR110)
        policy_record: Policy binding record (from PR111)

    Returns:
        Execution preview record

    Design:
        - Static rule-based mapping (if/elif)
        - Defensive (None/invalid → error record)
        - Warning-only (never raises)
        - Always returns valid records
    """
    # Validate plan record
    if not isinstance(plan_record, dict):
        return V11ExecutionPreviewSchema.create_error_record(
            error_info="invalid plan record type",
        )

    # Check plan status
    plan_status = plan_record.get("v10_plan_status", "UNAVAILABLE")
    if plan_status != "AVAILABLE":
        return V11ExecutionPreviewSchema.create_error_record(
            error_info="execution plan not available",
        )

    # Check simulation status (if provided)
    if simulation_record is not None and isinstance(simulation_record, dict):
        sim_applicable = simulation_record.get("v10_simulation_plan_applicable", False)
        if not sim_applicable:
            return V11ExecutionPreviewSchema.create_error_record(
                error_info="simulation indicates plan not applicable",
            )

    # Extract plan type
    plan_type = plan_record.get("v10_plan_type", "UNCLASSIFIED")

    # Extract regime level (if provided)
    regime_level = "REGIME_LOW"  # Default safe assumption
    if regime_record is not None and isinstance(regime_record, dict):
        regime_level = regime_record.get("v11_regime_level", "REGIME_LOW")

    # Extract policy permission (if provided)
    policy_permission = "UNKNOWN"
    if policy_record is not None and isinstance(policy_record, dict):
        policy_permission = policy_record.get("v11_execution_permission_override", "UNKNOWN")

    # Build basis list
    basis = ["v10_plan_type"]
    if regime_record is not None:
        basis.append("v11_regime_level")
    if policy_record is not None:
        basis.append("v11_policy_permission")

    # Check for BLOCKED conditions
    # 1. REGIME_CRITICAL
    if regime_level == "REGIME_CRITICAL":
        return V11ExecutionPreviewSchema.create_blocked_record(
            block_reason="regime critical observed. execution halted.",
            basis=basis,
        )

    # 2. Policy permission = HOLD
    if policy_permission == "HOLD":
        return V11ExecutionPreviewSchema.create_blocked_record(
            block_reason="policy permission hold. execution halted.",
            basis=basis,
        )

    # Apply preview rules
    exposure_change = _determine_exposure_change(plan_type)
    interaction_type = _determine_interaction_type(plan_type)
    risk_surface = _determine_risk_surface(regime_level)

    # Generate summary
    summary = _generate_summary(plan_type, exposure_change, interaction_type, risk_surface, regime_level)

    # Create preview record
    return V11ExecutionPreviewSchema.create_preview_record(
        exposure_change=exposure_change,
        interaction_type=interaction_type,
        risk_surface=risk_surface,
        summary=summary,
        basis=basis,
    )


def _determine_exposure_change(plan_type: str) -> str:
    """
    Determine exposure change from plan type.

    Args:
        plan_type: Plan type

    Returns:
        Exposure change type (NONE/INCREASE/DECREASE)
    """
    # Static rules (v1)
    if plan_type in ["NOOP", "MAINTENANCE"]:
        return "NONE"
    elif plan_type == "HEDGE":
        return "DECREASE"
    elif plan_type == "LIQUIDITY":
        return "INCREASE"
    elif plan_type == "REBALANCE":
        # REBALANCE can be either INCREASE or DECREASE
        # For v1, default to DECREASE (conservative)
        return "DECREASE"
    else:  # UNCLASSIFIED
        return "NONE"


def _determine_interaction_type(plan_type: str) -> str:
    """
    Determine interaction type from plan type.

    Args:
        plan_type: Plan type

    Returns:
        Interaction type (NONE/POOL_TOUCH/EVENT_INTERACTION)
    """
    # Static rules (v1)
    if plan_type == "MAINTENANCE":
        return "NONE"
    elif plan_type in ["REBALANCE", "HEDGE", "LIQUIDITY"]:
        return "POOL_TOUCH"
    elif plan_type == "NOOP":
        return "NONE"
    else:  # UNCLASSIFIED
        return "NONE"


def _determine_risk_surface(regime_level: str) -> str:
    """
    Determine risk surface from regime level.

    Args:
        regime_level: Regime level

    Returns:
        Risk surface level (LOW/MEDIUM/HIGH)
    """
    # Static rules (v1)
    if regime_level == "REGIME_LOW":
        return "LOW"
    elif regime_level == "REGIME_MEDIUM":
        return "MEDIUM"
    elif regime_level in ["REGIME_HIGH", "REGIME_CRITICAL"]:
        return "HIGH"
    else:  # UNCLASSIFIED
        return "LOW"


def _generate_summary(
    plan_type: str,
    exposure_change: str,
    interaction_type: str,
    risk_surface: str,
    regime_level: str,
) -> str:
    """
    Generate human-readable summary.

    Args:
        plan_type: Plan type
        exposure_change: Exposure change type
        interaction_type: Interaction type
        risk_surface: Risk surface level
        regime_level: Regime level

    Returns:
        Human-readable summary
    """
    # Map plan type to description
    plan_desc = {
        "NOOP": "no-operation plan",
        "MAINTENANCE": "maintenance plan",
        "REBALANCE": "rebalance-type plan",
        "HEDGE": "hedge-type plan",
        "LIQUIDITY": "liquidity-type plan",
        "UNCLASSIFIED": "unclassified plan",
    }.get(plan_type, "plan")

    # Map exposure change to description
    exposure_desc = {
        "NONE": "no exposure change",
        "INCREASE": "increase exposure",
        "DECREASE": "reduce exposure",
    }.get(exposure_change, "exposure change")

    # Map interaction type to description
    interaction_desc = {
        "NONE": "no interaction",
        "POOL_TOUCH": "pool interaction",
        "EVENT_INTERACTION": "event interaction",
    }.get(interaction_type, "interaction")

    # Map regime to description
    regime_desc = {
        "REGIME_LOW": "stable market regime",
        "REGIME_MEDIUM": "moderate market regime",
        "REGIME_HIGH": "elevated market regime",
        "REGIME_CRITICAL": "critical market regime",
    }.get(regime_level, "market regime")

    # Build summary
    if exposure_change == "NONE" and interaction_type == "NONE":
        # NOOP or MAINTENANCE
        summary = f"{plan_desc} with {exposure_desc} and {interaction_desc}."
    else:
        # Active plan
        summary = f"{plan_desc} would {exposure_desc} with {interaction_desc} under {regime_desc}."

    return summary


def get_execution_preview_engine_v1_info() -> Dict[str, Any]:
    """
    Get execution preview engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "execution_preview",
        "preview_rules": {
            "exposure_change": {
                "NOOP": "NONE",
                "MAINTENANCE": "NONE",
                "REBALANCE": "DECREASE",
                "HEDGE": "DECREASE",
                "LIQUIDITY": "INCREASE",
                "UNCLASSIFIED": "NONE",
            },
            "interaction_type": {
                "MAINTENANCE": "NONE",
                "REBALANCE": "POOL_TOUCH",
                "HEDGE": "POOL_TOUCH",
                "LIQUIDITY": "POOL_TOUCH",
                "NOOP": "NONE",
                "UNCLASSIFIED": "NONE",
            },
            "risk_surface": {
                "REGIME_LOW": "LOW",
                "REGIME_MEDIUM": "MEDIUM",
                "REGIME_HIGH": "HIGH",
                "REGIME_CRITICAL": "BLOCKED",
            },
        },
        "defensive": True,
        "warning_only": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Execution Preview Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: NOOP plan (NONE exposure, NONE interaction)
    print("Test 1: NOOP plan (NONE exposure, NONE interaction)")
    noop_plan = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": "NOOP",
    }
    preview_noop = generate_execution_preview_v1(plan_record=noop_plan)
    print(json.dumps(preview_noop, indent=2))
    print()

    # Test 2: HEDGE plan under REGIME_HIGH
    print("Test 2: HEDGE plan under REGIME_HIGH")
    hedge_plan = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": "HEDGE",
    }
    regime_high = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_HIGH",
    }
    preview_hedge = generate_execution_preview_v1(
        plan_record=hedge_plan,
        regime_record=regime_high,
    )
    print(json.dumps(preview_hedge, indent=2))
    print()

    # Test 3: REGIME_CRITICAL → BLOCKED
    print("Test 3: REGIME_CRITICAL → BLOCKED")
    regime_critical = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_CRITICAL",
    }
    preview_blocked = generate_execution_preview_v1(
        plan_record=hedge_plan,
        regime_record=regime_critical,
    )
    print(json.dumps(preview_blocked, indent=2))
    print()

    # Test 4: Policy HOLD → BLOCKED
    print("Test 4: Policy HOLD → BLOCKED")
    policy_hold = {
        "v11_policy_mode": "ON",
        "v11_policy_status": "AVAILABLE",
        "v11_execution_permission_override": "HOLD",
    }
    preview_policy_blocked = generate_execution_preview_v1(
        plan_record=hedge_plan,
        policy_record=policy_hold,
    )
    print(json.dumps(preview_policy_blocked, indent=2))
    print()

    # Test 5: LIQUIDITY plan under REGIME_LOW
    print("Test 5: LIQUIDITY plan under REGIME_LOW")
    liquidity_plan = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": "LIQUIDITY",
    }
    regime_low = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_LOW",
    }
    preview_liquidity = generate_execution_preview_v1(
        plan_record=liquidity_plan,
        regime_record=regime_low,
    )
    print(json.dumps(preview_liquidity, indent=2))
    print()

    # Test 6: Error case (invalid plan)
    print("Test 6: Error case (invalid plan)")
    preview_error = generate_execution_preview_v1(plan_record="invalid")  # type: ignore
    print(json.dumps(preview_error, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
