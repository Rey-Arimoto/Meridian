#!/usr/bin/env python3
"""
PR109: v1.0 Analytics Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on interpretation analytics.
    Guards against asset vocabulary, execution operations, and evaluation.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric values: Counts only (bucketed/labeled)
    - No asset vocabulary: No balance, holdings, portfolio
    - No execution vocabulary: No buy, sell, trade, swap
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No should/must recommendations

Guards:
    1. Token literal guard (token names)
    2. Asset vocabulary guard (balance, holdings, portfolio)
    3. Execution vocabulary guard (buy, sell, trade, swap)
    4. Evaluative vocabulary guard (good/bad, correct/wrong)
    5. Numeric value guard (raw amounts/prices)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def check_analytics_numeric_values(analytics: Dict[str, Any]) -> List[str]:
    """
    Check for raw numeric values in analytics (not counts).

    Args:
        analytics: Analytics record to check

    Returns:
        List of warnings (empty if no violations)
    """
    warnings = []

    # Check onchain analytics aggregation
    if "onchain_analytics" in analytics:
        onchain = analytics["onchain_analytics"]
        if isinstance(onchain, dict):
            # Check counts - these are allowed, but verify they're bucketed/labeled
            market_counts = onchain.get("market_cost_regime_counts", {})
            if isinstance(market_counts, dict):
                # Verify keys are labels (LOW/MEDIUM/HIGH), not numeric
                for key in market_counts.keys():
                    if isinstance(key, (int, float)):
                        warnings.append(f"Numeric key in market_cost_regime_counts: {key}")

            liquidity_presence = onchain.get("liquidity_regime_presence", {})
            if isinstance(liquidity_presence, dict):
                # Verify keys are labels (LOW/MEDIUM/HIGH), not numeric
                for key in liquidity_presence.keys():
                    if isinstance(key, (int, float)):
                        warnings.append(f"Numeric key in liquidity_regime_presence: {key}")

            event_frequency = onchain.get("event_activity_frequency", {})
            if isinstance(event_frequency, dict):
                # Verify keys are labels (TRUE/FALSE), not numeric
                for key in event_frequency.keys():
                    if isinstance(key, (int, float)):
                        warnings.append(f"Numeric key in event_activity_frequency: {key}")

            object_distribution = onchain.get("object_dynamics_distribution", {})
            if isinstance(object_distribution, dict):
                # Verify keys are labels (DECREASE/STABLE/INCREASE), not numeric
                for key in object_distribution.keys():
                    if isinstance(key, (int, float)):
                        warnings.append(f"Numeric key in object_dynamics_distribution: {key}")

    return warnings


def validate_interpretation_analytics_record(analytics: Dict[str, Any]) -> List[str]:
    """
    Validate interpretation analytics record against all constitutional guards.

    Args:
        analytics: Analytics record to validate

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
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )

    warnings = []

    # Check analytics summary
    if "analytics_summary" in analytics:
        summary = analytics["analytics_summary"]

        # Token literals guard
        token_warnings = check_observation_token_literals(summary)
        warnings.extend(token_warnings)

        # Asset vocabulary guard
        asset_warnings = check_asset_vocabulary(summary)
        warnings.extend(asset_warnings)

        # Execution vocabulary guard
        exec_warnings = check_execution_vocabulary_bridge(summary)
        warnings.extend(exec_warnings)

        # Forbidden vocabulary guard
        vocab_warnings = check_forbidden_vocabulary(summary)
        warnings.extend(vocab_warnings)

    # Check onchain analytics
    if "onchain_analytics" in analytics:
        # Numeric values guard (analytics-specific)
        numeric_warnings = check_analytics_numeric_values(analytics)
        warnings.extend(numeric_warnings)

    return warnings


def validate_onchain_analytics_summary(summary: str) -> List[str]:
    """
    Validate onchain analytics summary text.

    Args:
        summary: Summary text to validate

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
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )

    warnings = []

    # Token literals guard
    token_warnings = check_observation_token_literals(summary)
    warnings.extend(token_warnings)

    # Asset vocabulary guard
    asset_warnings = check_asset_vocabulary(summary)
    warnings.extend(asset_warnings)

    # Execution vocabulary guard
    exec_warnings = check_execution_vocabulary_bridge(summary)
    warnings.extend(exec_warnings)

    # Forbidden vocabulary guard
    vocab_warnings = check_forbidden_vocabulary(summary)
    warnings.extend(vocab_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Analytics Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean analytics record
    print("Test 1: Clean analytics record")
    clean_analytics = {
        "analytics_mode": "ON",
        "analytics_status": "AVAILABLE",
        "analytics_summary": "interpretation analytics with onchain extension.",
        "onchain_analytics": {
            "onchain_analytics_mode": "ON",
            "onchain_analytics_status": "AVAILABLE",
            "market_cost_regime_counts": {"LOW": 0, "MEDIUM": 2, "HIGH": 1},
            "liquidity_regime_presence": {"LOW": False, "MEDIUM": True, "HIGH": True},
            "event_activity_frequency": {"TRUE": 2, "FALSE": 1},
            "object_dynamics_distribution": {"DECREASE": 0, "STABLE": 1, "INCREASE": 1},
            "observation_count": 3,
        },
    }
    clean_warnings = validate_interpretation_analytics_record(clean_analytics)
    print(f"Clean analytics warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty analytics (asset vocabulary)
    print("Test 2: Dirty analytics (asset vocabulary)")
    dirty_analytics_asset = {
        "analytics_summary": "analytics of wallet balance and holdings distribution.",
    }
    dirty_warnings = validate_interpretation_analytics_record(dirty_analytics_asset)
    print(f"Dirty analytics warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty analytics (execution vocabulary)
    print("Test 3: Dirty analytics (execution vocabulary)")
    dirty_analytics_exec = {
        "analytics_summary": "analytics ready for buy and sell operations.",
    }
    dirty_warnings_exec = validate_interpretation_analytics_record(dirty_analytics_exec)
    print(f"Dirty analytics warnings: {len(dirty_warnings_exec)}")
    if dirty_warnings_exec:
        print("  Warnings:")
        for w in dirty_warnings_exec:
            print(f"    - {w}")
    print()

    # Test 4: Dirty analytics (token literals)
    print("Test 4: Dirty analytics (token literals)")
    dirty_analytics_token = {
        "analytics_summary": "analytics of SUI and USDC market patterns.",
    }
    dirty_warnings_token = validate_interpretation_analytics_record(dirty_analytics_token)
    print(f"Dirty analytics warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 5: Dirty analytics (numeric keys)
    print("Test 5: Dirty analytics (numeric keys)")
    dirty_analytics_numeric = {
        "analytics_mode": "ON",
        "onchain_analytics": {
            "market_cost_regime_counts": {1000: 5, 5000: 10},  # Numeric keys (violation)
        },
    }
    dirty_warnings_numeric = validate_interpretation_analytics_record(dirty_analytics_numeric)
    print(f"Dirty analytics warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 6: Clean summary
    print("Test 6: Clean summary")
    clean_summary = "onchain analytics aggregated from multiple observations. market cost regime observed as HIGH."
    clean_summary_warnings = validate_onchain_analytics_summary(clean_summary)
    print(f"Clean summary warnings: {len(clean_summary_warnings)}")
    if clean_summary_warnings:
        print(f"  Warnings: {clean_summary_warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
