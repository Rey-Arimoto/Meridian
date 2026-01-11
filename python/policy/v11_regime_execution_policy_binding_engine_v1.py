#!/usr/bin/env python3
"""
PR111: v1.1 Regime → Execution Policy Binding Engine v1 (READ-ONLY)

Purpose:
    Bind regime classification to execution policy.
    Binding = Constitutional Gate (not action).

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Override labels only
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - No execution vocabulary: No buy, sell, trade, swap
    - Non-evaluative: No good/bad vocabulary
    - Defensive: Never raises, returns valid records

Binding Philosophy:
    Binding ≠ Decision
    Binding ≠ Optimization
    Binding = Constitutional Gate

    Binding establishes:
    - Execution posture (HOLD/DRY_RUN_ONLY/normal)
    - Plan constraints (regime observation labels)
    - Basis (regime fields only)

    Binding does NOT:
    - Recommend actions
    - Optimize outcomes
    - Execute trades
    - Evaluate performance

Binding Rules (v1):
    REGIME_CRITICAL → permission override: HOLD
    REGIME_HIGH → permission override: DRY_RUN_ONLY
    REGIME_MEDIUM → permission override: UNKNOWN (no override)
    REGIME_LOW → permission override: UNKNOWN (no override)
    UNCLASSIFIED → permission override: UNKNOWN

    All regimes append corresponding constraint label.
"""

from typing import Any, Dict, Optional
from .v11_regime_execution_policy_schema import V11RegimeExecutionPolicySchema


def bind_regime_to_execution_policy_v1(
    regime_record: Dict[str, Any],
    execution_record: Optional[Dict[str, Any]] = None,
    plan_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Bind regime classification to execution policy.

    Args:
        regime_record: Regime classification record (from PR110)
        execution_record: Optional execution record to update (from PR101)
        plan_record: Optional plan record to update (from PR103)

    Returns:
        Dict with:
            - policy_record: Policy binding record
            - execution_record: Updated execution record (if provided)
            - plan_record: Updated plan record (if provided)

    Design:
        - Static rule-based mapping (if/elif)
        - Defensive (None/invalid → error record)
        - Warning-only (never raises)
        - Always returns valid records
    """
    # Validate regime record
    if not isinstance(regime_record, dict):
        return {
            "policy_record": V11RegimeExecutionPolicySchema.create_error_record(
                error_info="invalid regime record type",
            ),
            "execution_record": execution_record,
            "plan_record": plan_record,
        }

    # Check regime status
    regime_status = regime_record.get("v11_regime_status", "UNAVAILABLE")
    if regime_status != "AVAILABLE":
        return {
            "policy_record": V11RegimeExecutionPolicySchema.create_error_record(
                error_info="regime classification not available",
            ),
            "execution_record": execution_record,
            "plan_record": plan_record,
        }

    # Extract regime level
    regime_level = regime_record.get("v11_regime_level", "UNCLASSIFIED")

    # Apply binding rules (static if/elif)
    permission_override, plan_constraints = _apply_binding_rules(regime_level)

    # Create policy record
    policy_record = V11RegimeExecutionPolicySchema.create_policy_record(
        regime_level=regime_level,
        permission_override=permission_override,
        plan_constraints_append=plan_constraints,
        basis=["v11_regime_level"],
        artifacts=["pr110_regime_record"],
    )

    # Optionally apply to execution record
    updated_execution_record = execution_record
    if execution_record is not None and isinstance(execution_record, dict):
        updated_execution_record = _apply_permission_override(
            execution_record,
            permission_override,
            regime_level,
        )

    # Optionally apply to plan record
    updated_plan_record = plan_record
    if plan_record is not None and isinstance(plan_record, dict):
        updated_plan_record = _apply_plan_constraints(
            plan_record,
            plan_constraints,
        )

    return {
        "policy_record": policy_record,
        "execution_record": updated_execution_record,
        "plan_record": updated_plan_record,
    }


def _apply_binding_rules(regime_level: str) -> tuple[str, list[str]]:
    """
    Apply static binding rules to regime level.

    Args:
        regime_level: Regime level (REGIME_LOW/MEDIUM/HIGH/CRITICAL/UNCLASSIFIED)

    Returns:
        Tuple of (permission_override, plan_constraints)
    """
    # Static binding rules (v1)
    if regime_level == "REGIME_CRITICAL":
        return ("HOLD", ["regime_critical_observed"])
    elif regime_level == "REGIME_HIGH":
        return ("DRY_RUN_ONLY", ["regime_high_observed"])
    elif regime_level == "REGIME_MEDIUM":
        return ("UNKNOWN", ["regime_medium_observed"])
    elif regime_level == "REGIME_LOW":
        return ("UNKNOWN", ["regime_low_observed"])
    else:  # UNCLASSIFIED
        return ("UNKNOWN", [])


def _apply_permission_override(
    execution_record: Dict[str, Any],
    permission_override: str,
    regime_level: str,
) -> Dict[str, Any]:
    """
    Apply permission override to execution record.

    Args:
        execution_record: Execution record to update
        permission_override: Permission override (HOLD/DRY_RUN_ONLY/UNKNOWN)
        regime_level: Regime level

    Returns:
        Updated execution record
    """
    # Create copy to avoid mutation
    updated = execution_record.copy()

    # Apply override (only if not UNKNOWN)
    if permission_override == "HOLD":
        updated["v10_execution_permission"] = "HOLD"
        # Update basis
        basis = updated.get("v10_execution_basis", [])
        if "v11_regime_level" not in basis:
            updated["v10_execution_basis"] = basis + ["v11_regime_level"]
    elif permission_override == "DRY_RUN_ONLY":
        updated["v10_execution_permission"] = "DRY_RUN_ONLY"
        # Update basis
        basis = updated.get("v10_execution_basis", [])
        if "v11_regime_level" not in basis:
            updated["v10_execution_basis"] = basis + ["v11_regime_level"]

    # If UNKNOWN, leave execution record unchanged
    return updated


def _apply_plan_constraints(
    plan_record: Dict[str, Any],
    plan_constraints: list[str],
) -> Dict[str, Any]:
    """
    Apply plan constraints to plan record.

    Args:
        plan_record: Plan record to update
        plan_constraints: Plan constraints to append

    Returns:
        Updated plan record
    """
    # Create copy to avoid mutation
    updated = plan_record.copy()

    # Append constraints
    if plan_constraints:
        existing_constraints = updated.get("v10_plan_constraints", [])
        # Add new constraints (avoid duplicates)
        for constraint in plan_constraints:
            if constraint not in existing_constraints:
                existing_constraints.append(constraint)
        updated["v10_plan_constraints"] = existing_constraints

    return updated


def get_regime_execution_policy_binding_engine_v1_info() -> Dict[str, Any]:
    """
    Get regime-execution policy binding engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "regime_execution_policy_binding",
        "binding_rules": {
            "REGIME_CRITICAL": {
                "permission_override": "HOLD",
                "plan_constraints": ["regime_critical_observed"],
            },
            "REGIME_HIGH": {
                "permission_override": "DRY_RUN_ONLY",
                "plan_constraints": ["regime_high_observed"],
            },
            "REGIME_MEDIUM": {
                "permission_override": "UNKNOWN",
                "plan_constraints": ["regime_medium_observed"],
            },
            "REGIME_LOW": {
                "permission_override": "UNKNOWN",
                "plan_constraints": ["regime_low_observed"],
            },
            "UNCLASSIFIED": {
                "permission_override": "UNKNOWN",
                "plan_constraints": [],
            },
        },
        "defensive": True,
        "warning_only": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Regime-Execution Policy Binding Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: REGIME_CRITICAL → HOLD
    print("Test 1: REGIME_CRITICAL → HOLD")
    critical_regime = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_CRITICAL",
        "v11_regime_basis": ["observation_count"],
    }
    result = bind_regime_to_execution_policy_v1(critical_regime)
    print(json.dumps(result["policy_record"], indent=2))
    print()

    # Test 2: REGIME_HIGH → DRY_RUN_ONLY
    print("Test 2: REGIME_HIGH → DRY_RUN_ONLY")
    high_regime = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_HIGH",
        "v11_regime_basis": ["market_cost_regime_counts", "liquidity_regime_presence"],
    }
    result = bind_regime_to_execution_policy_v1(high_regime)
    print(json.dumps(result["policy_record"], indent=2))
    print()

    # Test 3: REGIME_LOW → UNKNOWN (no override)
    print("Test 3: REGIME_LOW → UNKNOWN (no override)")
    low_regime = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_LOW",
        "v11_regime_basis": ["market_cost_regime_counts"],
    }
    result = bind_regime_to_execution_policy_v1(low_regime)
    print(json.dumps(result["policy_record"], indent=2))
    print()

    # Test 4: Apply to execution record
    print("Test 4: Apply to execution record (REGIME_HIGH)")
    execution_record = {
        "v10_execution_permission": "ALLOW",
        "v10_execution_basis": ["v9_boundary_type"],
    }
    result = bind_regime_to_execution_policy_v1(high_regime, execution_record=execution_record)
    print("Updated execution record:")
    print(json.dumps(result["execution_record"], indent=2))
    print()

    # Test 5: Apply to plan record
    print("Test 5: Apply to plan record (REGIME_CRITICAL)")
    plan_record = {
        "v10_plan_type": "MAINTENANCE",
        "v10_plan_constraints": ["dry_run_only"],
    }
    result = bind_regime_to_execution_policy_v1(critical_regime, plan_record=plan_record)
    print("Updated plan record:")
    print(json.dumps(result["plan_record"], indent=2))
    print()

    # Test 6: Error case (invalid regime)
    print("Test 6: Error case (invalid regime)")
    result = bind_regime_to_execution_policy_v1("invalid")  # type: ignore
    print(json.dumps(result["policy_record"], indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
