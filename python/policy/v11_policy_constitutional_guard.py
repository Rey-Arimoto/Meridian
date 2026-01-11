#!/usr/bin/env python3
"""
PR111: v1.1 Policy Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on policy binding records.
    Guards against action vocabulary, execution operations, and evaluation.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No asset vocabulary: No balance, holdings, portfolio
    - No execution vocabulary: No buy, sell, trade, swap
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-prescriptive: No should/must recommendations

Guards:
    1. Token literal guard (token names)
    2. Asset vocabulary guard (balance, holdings, portfolio)
    3. Execution vocabulary guard (buy, sell, trade, swap)
    4. Action vocabulary guard (recommend, suggest, optimize)
    5. Forbidden vocabulary guard (evaluative/prescriptive)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def validate_policy_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate policy record against all constitutional guards.

    Args:
        record: Policy record to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import existing guards
    from observation.v10_observation_constitutional_guard import (
        check_observation_token_literals,
    )
    from bridge.v10_bridge_constitutional_guard import (
        check_asset_vocabulary,
        check_execution_vocabulary_bridge,
    )
    from regime.v11_regime_constitutional_guard import (
        check_action_vocabulary,
    )
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )

    warnings = []

    # Check policy summary
    if "v11_policy_summary" in record:
        summary = record["v11_policy_summary"]

        # Token literals guard
        token_warnings = check_observation_token_literals(summary)
        warnings.extend(token_warnings)

        # Asset vocabulary guard
        asset_warnings = check_asset_vocabulary(summary)
        warnings.extend(asset_warnings)

        # Execution vocabulary guard
        exec_warnings = check_execution_vocabulary_bridge(summary)
        warnings.extend(exec_warnings)

        # Action vocabulary guard
        action_warnings = check_action_vocabulary(summary)
        warnings.extend(action_warnings)

        # Forbidden vocabulary guard
        vocab_warnings = check_forbidden_vocabulary(summary)
        warnings.extend(vocab_warnings)

    # Check error info
    if "v11_policy_error_info" in record:
        error_info = record["v11_policy_error_info"]
        if isinstance(error_info, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(error_info)
            warnings.extend(token_warnings)

            # Asset vocabulary guard
            asset_warnings = check_asset_vocabulary(error_info)
            warnings.extend(asset_warnings)

    # Check plan constraints (should be labels only, no numeric patterns)
    if "v11_plan_constraints_append" in record:
        constraints = record["v11_plan_constraints_append"]
        if isinstance(constraints, list):
            for constraint in constraints:
                if isinstance(constraint, str):
                    # Check for numeric patterns in constraint labels
                    import re
                    if re.search(r'\d+', constraint):
                        warnings.append(f"Numeric pattern in constraint label: {constraint}")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.1 Policy Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean policy record
    print("Test 1: Clean policy record")
    clean_policy = {
        "v11_policy_summary": "regime binding applied. execution limited to simulation under elevated regime conditions.",
        "v11_plan_constraints_append": ["regime_high_observed"],
    }
    clean_warnings = validate_policy_record(clean_policy)
    print(f"Clean policy warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty policy (action vocabulary)
    print("Test 2: Dirty policy (action vocabulary)")
    dirty_policy_action = {
        "v11_policy_summary": "regime high. recommend reducing positions immediately.",
    }
    dirty_warnings = validate_policy_record(dirty_policy_action)
    print(f"Dirty policy warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty policy (asset vocabulary)
    print("Test 3: Dirty policy (asset vocabulary)")
    dirty_policy_asset = {
        "v11_policy_summary": "policy applied based on portfolio balance patterns.",
    }
    dirty_warnings_asset = validate_policy_record(dirty_policy_asset)
    print(f"Dirty policy warnings: {len(dirty_warnings_asset)}")
    if dirty_warnings_asset:
        print("  Warnings:")
        for w in dirty_warnings_asset:
            print(f"    - {w}")
    print()

    # Test 4: Dirty policy (execution vocabulary)
    print("Test 4: Dirty policy (execution vocabulary)")
    dirty_policy_exec = {
        "v11_policy_summary": "policy ready to execute buy and sell operations.",
    }
    dirty_warnings_exec = validate_policy_record(dirty_policy_exec)
    print(f"Dirty policy warnings: {len(dirty_warnings_exec)}")
    if dirty_warnings_exec:
        print("  Warnings:")
        for w in dirty_warnings_exec:
            print(f"    - {w}")
    print()

    # Test 5: Dirty policy (numeric constraint)
    print("Test 5: Dirty policy (numeric constraint)")
    dirty_policy_numeric = {
        "v11_plan_constraints_append": ["frequency_limit_5_times", "regime_high_observed"],
    }
    dirty_warnings_numeric = validate_policy_record(dirty_policy_numeric)
    print(f"Dirty policy warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 6: Dirty policy (token literals)
    print("Test 6: Dirty policy (token literals)")
    dirty_policy_token = {
        "v11_policy_summary": "policy binding for SUI and USDC trading.",
    }
    dirty_warnings_token = validate_policy_record(dirty_policy_token)
    print(f"Dirty policy warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
