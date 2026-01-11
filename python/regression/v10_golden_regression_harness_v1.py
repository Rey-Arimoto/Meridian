#!/usr/bin/env python3
"""
PR117: v1.0 Golden Regression Harness v1 (READ-ONLY)

Purpose:
    Test structural determinism using golden fixtures.
    Harness = Determinism Proof (not optimization/profit test).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - Regression = determinism proof (not optimization)
    - Diff is structural (not evaluative)
    - Warning-only: Exit code always 0

Harness Philosophy:
    Harness ≠ Optimization
    Harness ≠ Profit Test
    Harness = Determinism Proof

    Harness validates:
    - Same input → same structural output
    - Schema stability across PRs
    - No vocabulary leakage

    Harness does NOT:
    - Evaluate quality
    - Test profitability
    - Recommend actions
    - Measure performance

Golden Test Cases:
    - case_A: stable_low_activity (LOW regime expected)
    - case_B: high_variation (MEDIUM/HIGH regime expected)
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def run_golden_regression_v1(case_name: str) -> Dict[str, Any]:
    """
    Run golden regression test for a named case.

    Args:
        case_name: Test case name (e.g., "case_A", "case_B")

    Returns:
        Dict with regression results

    Design:
        - Loads fixture inputs for case
        - Runs orchestrator with those inputs
        - Builds bundle from output
        - Compares with expected bundle (if present)
        - Returns match status + diff summary
        - Defensive (missing files → warnings)
        - Warning-only (never raises)
    """
    warnings: List[str] = []

    # Get fixture directory
    fixture_dir = Path(__file__).parent.parent / "fixtures" / "golden" / "v1.0"

    # Load mock observations for this case
    observations_file = fixture_dir / f"mock_observations_{case_name}.json"
    if not observations_file.exists():
        return {
            "case_name": case_name,
            "match": False,
            "status": "ERROR",
            "error_info": f"observations fixture not found: {observations_file}",
            "warnings": warnings,
        }

    try:
        with open(observations_file, "r") as f:
            mock_observations = json.load(f)
    except Exception as e:
        return {
            "case_name": case_name,
            "match": False,
            "status": "ERROR",
            "error_info": f"failed to load observations: {str(e)}",
            "warnings": warnings,
        }

    # Run orchestrator with mock observations
    try:
        from orchestrator import run_pipeline_v1

        orchestrator_output = run_pipeline_v1(onchain_analytics=mock_observations)
    except Exception as e:
        warnings.append(f"Orchestrator error: {str(e)}")
        return {
            "case_name": case_name,
            "match": False,
            "status": "ERROR",
            "error_info": f"orchestrator failed: {str(e)}",
            "warnings": warnings,
        }

    # Build bundle from orchestrator output
    try:
        from bundle import build_artifact_bundle_v1

        actual_bundle = build_artifact_bundle_v1(orchestrator_output)
    except Exception as e:
        warnings.append(f"Bundle builder error: {str(e)}")
        return {
            "case_name": case_name,
            "match": False,
            "status": "ERROR",
            "error_info": f"bundle builder failed: {str(e)}",
            "warnings": warnings,
        }

    # Check if expected bundle exists
    expected_file = fixture_dir / f"expected_bundle_{case_name}.json"
    if not expected_file.exists():
        # No expected bundle - return actual bundle for review
        return {
            "case_name": case_name,
            "match": None,
            "status": "NO_EXPECTED",
            "actual_bundle": actual_bundle,
            "message": "no expected bundle found. actual bundle returned for review.",
            "warnings": warnings,
        }

    # Load expected bundle
    try:
        with open(expected_file, "r") as f:
            expected_bundle = json.load(f)
    except Exception as e:
        warnings.append(f"Failed to load expected bundle: {str(e)}")
        return {
            "case_name": case_name,
            "match": False,
            "status": "ERROR",
            "error_info": f"failed to load expected bundle: {str(e)}",
            "warnings": warnings,
        }

    # Compare bundles
    match, diff_summary = _compare_bundles(expected_bundle, actual_bundle)

    return {
        "case_name": case_name,
        "match": match,
        "status": "COMPLETE" if match else "MISMATCH",
        "diff_summary": diff_summary if not match else "bundles match. no differences detected.",
        "actual_bundle": actual_bundle if not match else None,
        "warnings": warnings if warnings else None,
    }


def _compare_bundles(
    expected: Dict[str, Any], actual: Dict[str, Any]
) -> tuple[bool, str]:
    """
    Compare two bundles structurally.

    Args:
        expected: Expected bundle
        actual: Actual bundle

    Returns:
        Tuple of (match, diff_summary)
    """
    differences = []

    # Compare bundle status
    if expected.get("v10_bundle_status") != actual.get("v10_bundle_status"):
        differences.append(
            f"bundle status differs: expected {expected.get('v10_bundle_status')}, "
            f"got {actual.get('v10_bundle_status')}"
        )

    # Compare layers
    expected_layers = expected.get("v10_bundle_layers", [])
    actual_layers = actual.get("v10_bundle_layers", [])

    if set(expected_layers) != set(actual_layers):
        differences.append(
            f"layer set differs: expected {sorted(expected_layers)}, "
            f"got {sorted(actual_layers)}"
        )

    # Compare layer order
    if expected_layers != actual_layers:
        differences.append("layer ordering differs")

    # Compare artifacts (lightweight check on key fields)
    expected_artifacts = expected.get("v10_bundle_artifacts", {})
    actual_artifacts = actual.get("v10_bundle_artifacts", {})

    for layer_name in expected_layers:
        if layer_name not in actual_artifacts:
            differences.append(f"layer {layer_name} missing in actual artifacts")
            continue

        expected_artifact = expected_artifacts.get(layer_name, {})
        actual_artifact = actual_artifacts.get(layer_name, {})

        # Check key fields based on layer type
        artifact_diffs = _compare_artifact(layer_name, expected_artifact, actual_artifact)
        differences.extend(artifact_diffs)

    # Build diff summary
    if len(differences) == 0:
        return True, ""

    diff_summary = f"{len(differences)} differences detected. " + "; ".join(
        differences[:5]
    )  # Limit to first 5
    if len(differences) > 5:
        diff_summary += f"; and {len(differences) - 5} more"

    return False, diff_summary


def _compare_artifact(
    layer_name: str, expected: Dict[str, Any], actual: Dict[str, Any]
) -> List[str]:
    """
    Compare artifacts for a specific layer.

    Args:
        layer_name: Layer name
        expected: Expected artifact
        actual: Actual artifact

    Returns:
        List of difference descriptions
    """
    differences = []

    # Check key fields based on layer type
    if layer_name == "REGIME":
        if expected.get("v11_regime_level") != actual.get("v11_regime_level"):
            differences.append(
                f"regime level differs: expected {expected.get('v11_regime_level')}, "
                f"got {actual.get('v11_regime_level')}"
            )

    elif layer_name == "POLICY_BINDING":
        if expected.get("v11_execution_permission_override") != actual.get(
            "v11_execution_permission_override"
        ):
            differences.append(
                f"policy permission differs: expected {expected.get('v11_execution_permission_override')}, "
                f"got {actual.get('v11_execution_permission_override')}"
            )

    elif layer_name == "PLAN":
        if expected.get("v10_plan_type") != actual.get("v10_plan_type"):
            differences.append(
                f"plan type differs: expected {expected.get('v10_plan_type')}, "
                f"got {actual.get('v10_plan_type')}"
            )

    elif layer_name == "PREVIEW":
        if expected.get("v11_preview_mode") != actual.get("v11_preview_mode"):
            differences.append(
                f"preview mode differs: expected {expected.get('v11_preview_mode')}, "
                f"got {actual.get('v11_preview_mode')}"
            )

    elif layer_name == "APPROVAL_GATE":
        if expected.get("v11_approval_requirement") != actual.get(
            "v11_approval_requirement"
        ):
            differences.append(
                f"approval requirement differs: expected {expected.get('v11_approval_requirement')}, "
                f"got {actual.get('v11_approval_requirement')}"
            )

    elif layer_name == "APPROVAL_REGISTRY":
        if expected.get("v11_registry_state") != actual.get("v11_registry_state"):
            differences.append(
                f"registry state differs: expected {expected.get('v11_registry_state')}, "
                f"got {actual.get('v11_registry_state')}"
            )

    return differences


def get_golden_regression_harness_v1_info() -> Dict[str, Any]:
    """
    Get golden regression harness v1 information.

    Returns:
        Dict with harness metadata
    """
    return {
        "harness_version": "v1",
        "harness_type": "golden_regression",
        "test_cases": ["case_A", "case_B"],
        "case_A_description": "stable_low_activity (LOW regime expected)",
        "case_B_description": "high_variation (MEDIUM/HIGH regime expected)",
        "defensive": True,
        "warning_only": True,
        "determinism_test": True,
        "not_profit_test": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Golden Regression Harness v1 - Self Test")
    print("=" * 60)
    print()

    # Test case A
    print("Test: Run golden regression for case_A")
    result_a = run_golden_regression_v1("case_A")
    print(f"Case A status: {result_a.get('status')}")
    print(f"Case A match: {result_a.get('match')}")
    if result_a.get("diff_summary"):
        print(f"Case A diff: {result_a.get('diff_summary')}")
    print()

    # Test case B
    print("Test: Run golden regression for case_B")
    result_b = run_golden_regression_v1("case_B")
    print(f"Case B status: {result_b.get('status')}")
    print(f"Case B match: {result_b.get('match')}")
    if result_b.get("diff_summary"):
        print(f"Case B diff: {result_b.get('diff_summary')}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
