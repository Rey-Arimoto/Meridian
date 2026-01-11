#!/usr/bin/env python3
"""
PR115: v1.0 Pipeline Orchestrator v1 (READ-ONLY)

Purpose:
    Orchestrate the full Meridian pipeline in fixed order.
    Orchestrator = Wiring (not decision/action).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - Defensive: Never raises, returns ERROR records
    - Warning-only: Exit code always 0

Orchestrator Philosophy:
    Orchestrator ≠ Decision
    Orchestrator ≠ Action
    Orchestrator = Fixed-Order Wiring

    Orchestrator connects:
    - Regime Classification (PR110)
    - Policy Binding (PR111)
    - Execution Preview (PR112)
    - Approval Gate (PR113)
    - Manual Approval Registry (PR114)

    Orchestrator does NOT:
    - Make decisions
    - Execute trades
    - Recommend actions
    - Reorder layers

Fixed Pipeline Order (v1):
    1. Onchain Analytics (mock or provided)
    2. Entropy Regime Classification (PR110)
    3. Regime → Execution Policy Binding (PR111)
    4. Execution Plan (mock or provided)
    5. Execution Preview (PR112)
    6. Human Approval Gate (PR113)
    7. Manual Approval Registry (PR114)

Note: PR106-PR109 (Connection/Observation/Bridge/Analytics) are stubbed
with mock inputs in v1. Full integration requires those components.
"""

from typing import Any, Dict, Optional


def run_pipeline_v1(
    onchain_analytics: Optional[Dict[str, Any]] = None,
    execution_plan: Optional[Dict[str, Any]] = None,
    mock_inputs: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the full Meridian pipeline in fixed order.

    Args:
        onchain_analytics: Onchain analytics record (PR109) or None for mock
        execution_plan: Execution plan record (PR103) or None for mock
        mock_inputs: Optional mock inputs for testing

    Returns:
        Dict containing all pipeline artifacts

    Design:
        - Fixed layer order (no reordering)
        - Defensive (invalid inputs → ERROR records)
        - Warning-only (never raises)
        - Always returns valid artifact bundle
    """
    artifacts = {}
    warnings = []

    # Use mock inputs if provided
    if mock_inputs is not None and isinstance(mock_inputs, dict):
        if "onchain_analytics" in mock_inputs:
            onchain_analytics = mock_inputs["onchain_analytics"]
        if "execution_plan" in mock_inputs:
            execution_plan = mock_inputs["execution_plan"]

    # Layer 1: Onchain Analytics (mock or provided)
    if onchain_analytics is None or not isinstance(onchain_analytics, dict):
        # Create mock analytics for testing
        onchain_analytics = _create_mock_analytics()
        warnings.append("Using mock onchain analytics")

    artifacts["onchain_analytics"] = onchain_analytics

    # Layer 2: Entropy Regime Classification (PR110)
    regime_record = _run_regime_classification(onchain_analytics, warnings)
    artifacts["regime_record"] = regime_record

    # Layer 3: Regime → Execution Policy Binding (PR111)
    policy_record = _run_policy_binding(regime_record, execution_plan, warnings)
    artifacts["policy_record"] = policy_record

    # Layer 4: Execution Plan (mock or provided)
    if execution_plan is None or not isinstance(execution_plan, dict):
        # Create mock plan based on policy
        execution_plan = _create_mock_plan(policy_record)
        warnings.append("Using mock execution plan")

    artifacts["execution_plan"] = execution_plan

    # Layer 5: Execution Preview (PR112)
    preview_record = _run_execution_preview(
        execution_plan, regime_record, policy_record, warnings
    )
    artifacts["preview_record"] = preview_record

    # Layer 6: Human Approval Gate (PR113)
    approval_gate_record = _run_approval_gate(
        execution_plan, preview_record, regime_record, policy_record, warnings
    )
    artifacts["approval_gate_record"] = approval_gate_record

    # Layer 7: Manual Approval Registry (PR114) - read-only (event NONE)
    registry_record = _run_approval_registry(approval_gate_record, warnings)
    artifacts["registry_record"] = registry_record

    # Add warnings to bundle
    if warnings:
        artifacts["pipeline_warnings"] = warnings

    # Add pipeline metadata
    artifacts["pipeline_version"] = "v1"
    artifacts["pipeline_status"] = "COMPLETE"
    artifacts["pipeline_order"] = [
        "onchain_analytics",
        "regime_record",
        "policy_record",
        "execution_plan",
        "preview_record",
        "approval_gate_record",
        "registry_record",
    ]

    return artifacts


def _create_mock_analytics() -> Dict[str, Any]:
    """
    Create mock onchain analytics for testing.

    Returns:
        Mock analytics record
    """
    return {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 5, "MEDIUM": 3, "HIGH": 2},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": True, "HIGH": False},
        "event_activity_frequency": {"TRUE": 4, "FALSE": 6},
        "object_dynamics_distribution": {"DECREASE": 1, "STABLE": 7, "INCREASE": 2},
        "observation_count": 10,
    }


def _create_mock_plan(policy_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create mock execution plan based on policy.

    Args:
        policy_record: Policy binding record

    Returns:
        Mock plan record
    """
    permission = policy_record.get("v11_execution_permission_override", "UNKNOWN")

    if permission == "HOLD":
        plan_type = "NOOP"
    elif permission == "DRY_RUN_ONLY":
        plan_type = "MAINTENANCE"
    else:
        plan_type = "MAINTENANCE"

    return {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": plan_type,
        "v10_plan_description": f"mock plan of type {plan_type} based on policy permission {permission}.",
        "v10_plan_constraints": ["dry_run_only"],
        "v10_plan_basis": ["v11_execution_permission_override"],
    }


def _run_regime_classification(
    analytics: Dict[str, Any],
    warnings: list,
) -> Dict[str, Any]:
    """
    Run entropy regime classification (PR110).

    Args:
        analytics: Onchain analytics record
        warnings: Warnings list to append to

    Returns:
        Regime record
    """
    try:
        from regime import classify_entropy_regime_v1

        return classify_entropy_regime_v1(analytics)
    except Exception as e:
        warnings.append(f"Regime classification error: {str(e)}")
        # Return error record (defensive)
        from regime import V11EntropyRegimeSchema
        return V11EntropyRegimeSchema.create_error_record(
            error_info=f"regime classification error: {str(e)}",
        )


def _run_policy_binding(
    regime_record: Dict[str, Any],
    execution_record: Optional[Dict[str, Any]],
    warnings: list,
) -> Dict[str, Any]:
    """
    Run regime → execution policy binding (PR111).

    Args:
        regime_record: Regime classification record
        execution_record: Optional execution record
        warnings: Warnings list to append to

    Returns:
        Policy binding record
    """
    try:
        from policy import bind_regime_to_execution_policy_v1

        result = bind_regime_to_execution_policy_v1(
            regime_record=regime_record,
            execution_record=execution_record,
        )
        return result["policy_record"]
    except Exception as e:
        warnings.append(f"Policy binding error: {str(e)}")
        # Return error record (defensive)
        from policy import V11RegimeExecutionPolicySchema
        return V11RegimeExecutionPolicySchema.create_error_record(
            error_info=f"policy binding error: {str(e)}",
        )


def _run_execution_preview(
    plan_record: Dict[str, Any],
    regime_record: Dict[str, Any],
    policy_record: Dict[str, Any],
    warnings: list,
) -> Dict[str, Any]:
    """
    Run execution preview (PR112).

    Args:
        plan_record: Execution plan record
        regime_record: Regime record
        policy_record: Policy record
        warnings: Warnings list to append to

    Returns:
        Preview record
    """
    try:
        from preview import generate_execution_preview_v1

        return generate_execution_preview_v1(
            plan_record=plan_record,
            regime_record=regime_record,
            policy_record=policy_record,
        )
    except Exception as e:
        warnings.append(f"Execution preview error: {str(e)}")
        # Return error record (defensive)
        from preview import V11ExecutionPreviewSchema
        return V11ExecutionPreviewSchema.create_error_record(
            error_info=f"execution preview error: {str(e)}",
        )


def _run_approval_gate(
    execution_plan: Dict[str, Any],
    preview_record: Dict[str, Any],
    regime_record: Dict[str, Any],
    policy_record: Dict[str, Any],
    warnings: list,
) -> Dict[str, Any]:
    """
    Run human approval gate (PR113).

    Args:
        execution_plan: Execution plan record
        preview_record: Preview record
        regime_record: Regime record
        policy_record: Policy record
        warnings: Warnings list to append to

    Returns:
        Approval gate record
    """
    try:
        from approval import gate_human_approval_v1

        return gate_human_approval_v1(
            plan_record=execution_plan,
            preview_record=preview_record,
            regime_record=regime_record,
            policy_record=policy_record,
        )
    except Exception as e:
        warnings.append(f"Approval gate error: {str(e)}")
        # Return error record (defensive)
        from approval import V11ApprovalSchema
        return V11ApprovalSchema.create_error_record(
            error_info=f"approval gate error: {str(e)}",
        )


def _run_approval_registry(
    approval_gate_record: Dict[str, Any],
    warnings: list,
) -> Dict[str, Any]:
    """
    Run manual approval registry (PR114) - read-only (event NONE).

    Args:
        approval_gate_record: Approval gate record
        warnings: Warnings list to append to

    Returns:
        Registry record
    """
    try:
        from approval import apply_approval_event_v1

        return apply_approval_event_v1(
            approval_gate_record=approval_gate_record,
            registry_record=None,
            event="NONE",  # Read-only in orchestrator v1
        )
    except Exception as e:
        warnings.append(f"Approval registry error: {str(e)}")
        # Return error record (defensive)
        from approval import V11ApprovalRegistrySchema
        return V11ApprovalRegistrySchema.create_error_record(
            error_info=f"approval registry error: {str(e)}",
        )


def get_pipeline_orchestrator_v1_info() -> Dict[str, Any]:
    """
    Get pipeline orchestrator v1 information.

    Returns:
        Dict with orchestrator metadata
    """
    return {
        "orchestrator_version": "v1",
        "orchestrator_type": "fixed_order_pipeline",
        "pipeline_order": [
            "onchain_analytics (mock or provided)",
            "regime_classification (PR110)",
            "policy_binding (PR111)",
            "execution_plan (mock or provided)",
            "execution_preview (PR112)",
            "approval_gate (PR113)",
            "approval_registry (PR114)",
        ],
        "defensive": True,
        "warning_only": True,
        "fixed_order": True,
        "no_reordering": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Pipeline Orchestrator v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: End-to-end run with defaults
    print("Test 1: End-to-end run with defaults")
    artifacts = run_pipeline_v1()
    print(f"Pipeline status: {artifacts['pipeline_status']}")
    print(f"Artifacts generated: {len(artifacts)}")
    print(f"Pipeline order: {artifacts['pipeline_order']}")
    print()

    # Test 2: Run with mock inputs
    print("Test 2: Run with mock inputs")
    mock_analytics = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 8, "MEDIUM": 1, "HIGH": 1},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": False, "HIGH": False},
        "event_activity_frequency": {"TRUE": 2, "FALSE": 8},
        "object_dynamics_distribution": {"DECREASE": 0, "STABLE": 9, "INCREASE": 1},
        "observation_count": 10,
    }
    artifacts = run_pipeline_v1(onchain_analytics=mock_analytics)
    print(f"Regime level: {artifacts['regime_record'].get('v11_regime_level')}")
    print(f"Policy permission: {artifacts['policy_record'].get('v11_execution_permission_override')}")
    print(f"Approval requirement: {artifacts['approval_gate_record'].get('v11_approval_requirement')}")
    print()

    # Test 3: Verify all artifacts present
    print("Test 3: Verify all artifacts present")
    required_artifacts = [
        "onchain_analytics",
        "regime_record",
        "policy_record",
        "execution_plan",
        "preview_record",
        "approval_gate_record",
        "registry_record",
    ]
    all_present = all(art in artifacts for art in required_artifacts)
    print(f"All required artifacts present: {all_present}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
