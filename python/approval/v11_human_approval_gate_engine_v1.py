#!/usr/bin/env python3
"""
PR113: v1.1 Human Approval Gate Engine v1 (READ-ONLY)

Purpose:
    Determine human approval requirement from upstream records.
    Approval Gate = State Machine (not action/recommendation).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No should/must vocabulary
    - Defensive: Never raises, returns valid records

Approval Gate Philosophy:
    Gate ≠ Action
    Gate ≠ Recommendation
    Gate = Requirement Classification

    Gate determines:
    - Whether approval is structurally required
    - Approval requirement level (NOT_REQUIRED/REQUIRED/REQUIRED_STRICT)
    - Current state (UNREQUESTED/REQUESTED/APPROVED/REJECTED/EXPIRED)

    Gate does NOT:
    - Recommend execution
    - Evaluate profitability
    - Provide trading instructions
    - Execute anything

    IMPORTANT: "APPROVED" is a state label only.
    It does NOT mean "execute" or "this is good".

Static Approval Rules (v1):

First match wins (order matters):
    1. If preview_record.v11_preview_status == "BLOCKED"
       → REQUIRED_STRICT
    2. If execution_record.v10_execution_permission == "HOLD"
       → REQUIRED_STRICT
    3. If regime_record.v11_regime_level == "REGIME_CRITICAL"
       → REQUIRED_STRICT
    4. If execution_record.v10_execution_permission == "DRY_RUN_ONLY"
       → REQUIRED
    5. If regime_record.v11_regime_level == "REGIME_HIGH"
       → REQUIRED
    6. Else
       → NOT_REQUIRED (or REQUIRED for conservative v1)

All rules produce state = UNREQUESTED (v1 does not track approval state changes).
"""

from typing import Any, Dict, Optional
from .v11_approval_schema import V11ApprovalSchema


def gate_human_approval_v1(
    execution_record: Optional[Dict[str, Any]] = None,
    plan_record: Optional[Dict[str, Any]] = None,
    simulation_record: Optional[Dict[str, Any]] = None,
    regime_record: Optional[Dict[str, Any]] = None,
    policy_record: Optional[Dict[str, Any]] = None,
    preview_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Gate human approval based on upstream records.

    Args:
        execution_record: Execution record (from PR101)
        plan_record: Plan record (from PR103)
        simulation_record: Simulation record (from PR104)
        regime_record: Regime record (from PR110)
        policy_record: Policy record (from PR111)
        preview_record: Preview record (from PR112)

    Returns:
        Approval record

    Design:
        - Static rule-based classification (if/elif)
        - Defensive (None/invalid → error record)
        - Warning-only (never raises)
        - Always returns valid records
        - First match wins (order matters)
    """
    # Build basis and artifacts lists
    basis = []
    artifacts = []

    # Extract fields for decision (defensive)
    preview_status = None
    execution_permission = None
    regime_level = None

    if preview_record is not None and isinstance(preview_record, dict):
        preview_status = preview_record.get("v11_preview_status")
        basis.append("v11_preview_status")
        artifacts.append("pr112_preview_record")

    if execution_record is not None and isinstance(execution_record, dict):
        execution_permission = execution_record.get("v10_execution_permission")
        basis.append("v10_execution_permission")
        artifacts.append("pr101_execution_record")

    if regime_record is not None and isinstance(regime_record, dict):
        regime_level = regime_record.get("v11_regime_level")
        basis.append("v11_regime_level")
        artifacts.append("pr110_regime_record")

    # Apply static rules (first match wins)
    requirement, summary = _apply_approval_rules(
        preview_status=preview_status,
        execution_permission=execution_permission,
        regime_level=regime_level,
    )

    # v1: Always start in UNREQUESTED state
    state = "UNREQUESTED"

    # Create approval record
    return V11ApprovalSchema.create_approval_record(
        requirement=requirement,
        state=state,
        summary=summary,
        basis=basis,
        artifacts=artifacts,
    )


def _apply_approval_rules(
    preview_status: Optional[str],
    execution_permission: Optional[str],
    regime_level: Optional[str],
) -> tuple[str, str]:
    """
    Apply static approval rules.

    Args:
        preview_status: Preview status
        execution_permission: Execution permission
        regime_level: Regime level

    Returns:
        Tuple of (requirement, summary)
    """
    # Rule 1: Preview BLOCKED → REQUIRED_STRICT
    if preview_status == "BLOCKED":
        return (
            "REQUIRED_STRICT",
            "approval required under blocked preview conditions. no approval requested.",
        )

    # Rule 2: Execution permission HOLD → REQUIRED_STRICT
    if execution_permission == "HOLD":
        return (
            "REQUIRED_STRICT",
            "approval required under hold permission conditions. no approval requested.",
        )

    # Rule 3: Regime CRITICAL → REQUIRED_STRICT
    if regime_level == "REGIME_CRITICAL":
        return (
            "REQUIRED_STRICT",
            "approval required under critical regime conditions. no approval requested.",
        )

    # Rule 4: Execution permission DRY_RUN_ONLY → REQUIRED
    if execution_permission == "DRY_RUN_ONLY":
        return (
            "REQUIRED",
            "approval required under dry-run-only permission conditions. no approval requested.",
        )

    # Rule 5: Regime HIGH → REQUIRED
    if regime_level == "REGIME_HIGH":
        return (
            "REQUIRED",
            "approval required under elevated regime conditions. no approval requested.",
        )

    # Rule 6: Default → NOT_REQUIRED
    # Note: For conservative v1, could return REQUIRED instead
    return (
        "NOT_REQUIRED",
        "approval not required under normal conditions.",
    )


def get_human_approval_gate_v1_info() -> Dict[str, Any]:
    """
    Get human approval gate v1 information.

    Returns:
        Dict with gate metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "human_approval_gate",
        "approval_rules": {
            "rule_1": {
                "condition": "preview_status == BLOCKED",
                "requirement": "REQUIRED_STRICT",
            },
            "rule_2": {
                "condition": "execution_permission == HOLD",
                "requirement": "REQUIRED_STRICT",
            },
            "rule_3": {
                "condition": "regime_level == REGIME_CRITICAL",
                "requirement": "REQUIRED_STRICT",
            },
            "rule_4": {
                "condition": "execution_permission == DRY_RUN_ONLY",
                "requirement": "REQUIRED",
            },
            "rule_5": {
                "condition": "regime_level == REGIME_HIGH",
                "requirement": "REQUIRED",
            },
            "rule_6": {
                "condition": "default",
                "requirement": "NOT_REQUIRED",
            },
        },
        "rule_order": "first match wins",
        "default_state": "UNREQUESTED",
        "defensive": True,
        "warning_only": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Human Approval Gate Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Preview BLOCKED → REQUIRED_STRICT
    print("Test 1: Preview BLOCKED → REQUIRED_STRICT")
    preview_blocked = {
        "v11_preview_mode": "ON",
        "v11_preview_status": "BLOCKED",
        "v11_preview_block_reason": "regime critical observed",
    }
    approval = gate_human_approval_v1(preview_record=preview_blocked)
    print(json.dumps(approval, indent=2))
    print()

    # Test 2: Execution HOLD → REQUIRED_STRICT
    print("Test 2: Execution HOLD → REQUIRED_STRICT")
    execution_hold = {
        "v10_execution_mode": "ON",
        "v10_execution_permission": "HOLD",
    }
    approval = gate_human_approval_v1(execution_record=execution_hold)
    print(json.dumps(approval, indent=2))
    print()

    # Test 3: Regime CRITICAL → REQUIRED_STRICT
    print("Test 3: Regime CRITICAL → REQUIRED_STRICT")
    regime_critical = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_CRITICAL",
    }
    approval = gate_human_approval_v1(regime_record=regime_critical)
    print(json.dumps(approval, indent=2))
    print()

    # Test 4: Execution DRY_RUN_ONLY → REQUIRED
    print("Test 4: Execution DRY_RUN_ONLY → REQUIRED")
    execution_dry_run = {
        "v10_execution_mode": "ON",
        "v10_execution_permission": "DRY_RUN_ONLY",
    }
    approval = gate_human_approval_v1(execution_record=execution_dry_run)
    print(json.dumps(approval, indent=2))
    print()

    # Test 5: Regime HIGH → REQUIRED
    print("Test 5: Regime HIGH → REQUIRED")
    regime_high = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_HIGH",
    }
    approval = gate_human_approval_v1(regime_record=regime_high)
    print(json.dumps(approval, indent=2))
    print()

    # Test 6: Normal conditions → NOT_REQUIRED
    print("Test 6: Normal conditions → NOT_REQUIRED")
    regime_low = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_LOW",
    }
    execution_allow = {
        "v10_execution_mode": "ON",
        "v10_execution_permission": "ALLOW",
    }
    approval = gate_human_approval_v1(
        regime_record=regime_low,
        execution_record=execution_allow,
    )
    print(json.dumps(approval, indent=2))
    print()

    # Test 7: No inputs (defensive)
    print("Test 7: No inputs (defensive)")
    approval = gate_human_approval_v1()
    print(json.dumps(approval, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
