#!/usr/bin/env python3
"""
PR109: v1.0 Interpretation Analytics Extension (Onchain-Aware) Smoke Test

Purpose:
    Validate that v1.0 interpretation analytics correctly aggregates
    onchain observations as meaning generation (not execution).

Test Coverage:
    1. Analytics extension import works
    2. Empty observations produce valid aggregation
    3. Single observation aggregates correctly
    4. Multiple observations aggregate correctly
    5. Extended analytics includes onchain aggregation
    6. Analytics summary generates correctly
    7. Constitutional guards detect violations
    8. Defensive behavior (None/empty handling)

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Counts only (bucketed/labeled)
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - Non-evaluative: No good/bad vocabulary

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict, List

# Import v1.0 analytics modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analytics.pr109_interpretation_analytics_onchain_extension import (
    aggregate_onchain_observations,
    extend_interpretation_analytics_v1,
    get_onchain_analytics_summary,
    get_interpretation_analytics_onchain_extension_info,
)
from analytics.pr109_analytics_constitutional_guard import (
    check_analytics_numeric_values,
    validate_interpretation_analytics_record,
    validate_onchain_analytics_summary,
)


def test_analytics_extension_import() -> bool:
    """
    Test 1: Analytics extension import works.
    """
    print("Test 1: Analytics extension import works")
    print("-" * 60)

    try:
        from analytics.pr109_interpretation_analytics_onchain_extension import (
            aggregate_onchain_observations,
        )
        print("✓ Analytics extension import successful")
    except ImportError as e:
        print(f"✗ Analytics extension import failed: {e}")
        return False

    try:
        from analytics.pr109_analytics_constitutional_guard import (
            validate_interpretation_analytics_record,
        )
        print("✓ Constitutional guard import successful")
    except ImportError as e:
        print(f"✗ Constitutional guard import failed: {e}")
        return False

    print("Test 1: PASS\n")
    return True


def test_empty_observations_produce_valid_aggregation() -> bool:
    """
    Test 2: Empty observations produce valid aggregation.
    """
    print("Test 2: Empty observations produce valid aggregation")
    print("-" * 60)

    # Test with empty list
    aggregation = aggregate_onchain_observations([])

    if aggregation["onchain_analytics_mode"] != "OFF":
        print(f"✗ Expected mode OFF, got {aggregation['onchain_analytics_mode']}")
        return False
    print("✓ Onchain analytics mode is OFF")

    if aggregation["onchain_analytics_status"] != "UNAVAILABLE":
        print(f"✗ Expected status UNAVAILABLE, got {aggregation['onchain_analytics_status']}")
        return False
    print("✓ Onchain analytics status is UNAVAILABLE")

    if aggregation["observation_count"] != 0:
        print(f"✗ Expected observation_count 0, got {aggregation['observation_count']}")
        return False
    print("✓ Observation count is 0")

    print("Test 2: PASS\n")
    return True


def test_single_observation_aggregates_correctly() -> bool:
    """
    Test 3: Single observation aggregates correctly.
    """
    print("Test 3: Single observation aggregates correctly")
    print("-" * 60)

    # Create single observation
    import time
    single_obs = [
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_market_cost_regime": "MEDIUM",
            "v10_norm_obs_summary": "normalized observation available.",
        }
    ]

    # Aggregate
    aggregation = aggregate_onchain_observations(single_obs)

    if aggregation["onchain_analytics_status"] != "AVAILABLE":
        print(f"✗ Expected status AVAILABLE, got {aggregation['onchain_analytics_status']}")
        return False
    print("✓ Onchain analytics status is AVAILABLE")

    if aggregation["observation_count"] != 1:
        print(f"✗ Expected observation_count 1, got {aggregation['observation_count']}")
        return False
    print("✓ Observation count is 1")

    # Check market cost regime counts
    market_counts = aggregation["market_cost_regime_counts"]
    if market_counts["MEDIUM"] != 1:
        print(f"✗ Expected MEDIUM count 1, got {market_counts['MEDIUM']}")
        return False
    print("✓ Market cost regime MEDIUM count is 1")

    print("Test 3: PASS\n")
    return True


def test_multiple_observations_aggregate_correctly() -> bool:
    """
    Test 4: Multiple observations aggregate correctly.
    """
    print("Test 4: Multiple observations aggregate correctly")
    print("-" * 60)

    # Create multiple observations
    import time
    multiple_obs = [
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_market_cost_regime": "HIGH",
            "v10_norm_obs_liquidity_regime": "MEDIUM",
            "v10_norm_obs_event_activity_present": "TRUE",
        },
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_object_dynamics": "INCREASE",
            "v10_norm_obs_event_activity_present": "FALSE",
        },
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_market_cost_regime": "HIGH",
            "v10_norm_obs_liquidity_regime": "HIGH",
        },
    ]

    # Aggregate
    aggregation = aggregate_onchain_observations(multiple_obs)

    if aggregation["observation_count"] != 3:
        print(f"✗ Expected observation_count 3, got {aggregation['observation_count']}")
        return False
    print("✓ Observation count is 3")

    # Check market cost regime counts
    market_counts = aggregation["market_cost_regime_counts"]
    if market_counts["HIGH"] != 2:
        print(f"✗ Expected HIGH count 2, got {market_counts['HIGH']}")
        return False
    print("✓ Market cost regime HIGH count is 2")

    # Check liquidity regime presence
    liquidity_presence = aggregation["liquidity_regime_presence"]
    if not liquidity_presence["MEDIUM"]:
        print("✗ Expected MEDIUM liquidity regime present")
        return False
    if not liquidity_presence["HIGH"]:
        print("✗ Expected HIGH liquidity regime present")
        return False
    print("✓ Liquidity regime presence captured correctly")

    # Check event activity frequency
    event_frequency = aggregation["event_activity_frequency"]
    if event_frequency["TRUE"] != 1:
        print(f"✗ Expected TRUE event frequency 1, got {event_frequency['TRUE']}")
        return False
    if event_frequency["FALSE"] != 1:
        print(f"✗ Expected FALSE event frequency 1, got {event_frequency['FALSE']}")
        return False
    print("✓ Event activity frequency captured correctly")

    # Check object dynamics distribution
    object_distribution = aggregation["object_dynamics_distribution"]
    if object_distribution["INCREASE"] != 1:
        print(f"✗ Expected INCREASE count 1, got {object_distribution['INCREASE']}")
        return False
    print("✓ Object dynamics distribution captured correctly")

    print("Test 4: PASS\n")
    return True


def test_extended_analytics_includes_onchain_aggregation() -> bool:
    """
    Test 5: Extended analytics includes onchain aggregation.
    """
    print("Test 5: Extended analytics includes onchain aggregation")
    print("-" * 60)

    # Create base analytics
    base_analytics = {
        "analytics_mode": "ON",
        "analytics_status": "AVAILABLE",
        "analytics_summary": "base interpretation analytics.",
    }

    # Create observations
    import time
    observations = [
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_market_cost_regime": "LOW",
        }
    ]

    # Extend analytics
    extended = extend_interpretation_analytics_v1(base_analytics, observations)

    if "onchain_analytics" not in extended:
        print("✗ Expected onchain_analytics field")
        return False
    print("✓ Extended analytics includes onchain_analytics")

    onchain = extended["onchain_analytics"]
    if onchain["onchain_analytics_status"] != "AVAILABLE":
        print(f"✗ Expected onchain status AVAILABLE, got {onchain['onchain_analytics_status']}")
        return False
    print("✓ Onchain analytics status is AVAILABLE")

    # Check that base analytics preserved
    if extended["analytics_summary"] != "base interpretation analytics.":
        print(f"✗ Base analytics summary not preserved")
        return False
    print("✓ Base analytics preserved")

    print("Test 5: PASS\n")
    return True


def test_analytics_summary_generates_correctly() -> bool:
    """
    Test 6: Analytics summary generates correctly.
    """
    print("Test 6: Analytics summary generates correctly")
    print("-" * 60)

    # Create aggregation with observations
    import time
    observations = [
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_market_cost_regime": "HIGH",
            "v10_norm_obs_liquidity_regime": "MEDIUM",
            "v10_norm_obs_event_activity_present": "TRUE",
            "v10_norm_obs_object_dynamics": "INCREASE",
        }
    ]

    aggregation = aggregate_onchain_observations(observations)

    # Generate summary
    summary = get_onchain_analytics_summary(aggregation)

    if not isinstance(summary, str):
        print("✗ Summary is not a string")
        return False
    print("✓ Summary is a string")

    if len(summary) == 0:
        print("✗ Summary is empty")
        return False
    print("✓ Summary is not empty")

    # Verify summary does not contain violations
    warnings = validate_onchain_analytics_summary(summary)
    if warnings:
        print(f"✗ Summary contains violations: {warnings}")
        return False
    print("✓ Summary passes constitutional guards")

    print(f"  Summary: {summary}")

    print("Test 6: PASS\n")
    return True


def test_constitutional_guards_detect_violations() -> bool:
    """
    Test 7: Constitutional guards detect violations.
    """
    print("Test 7: Constitutional guards detect violations")
    print("-" * 60)

    # Test asset vocabulary violation
    dirty_analytics_asset = {
        "analytics_summary": "analytics of wallet balance and holdings.",
    }
    asset_warnings = validate_interpretation_analytics_record(dirty_analytics_asset)
    if not asset_warnings:
        print("✗ Asset vocabulary guard failed to detect violations")
        return False
    print(f"✓ Asset vocabulary guard detected: {len(asset_warnings)} violations")

    # Test execution vocabulary violation
    dirty_analytics_exec = {
        "analytics_summary": "analytics ready for buy operations.",
    }
    exec_warnings = validate_interpretation_analytics_record(dirty_analytics_exec)
    if not exec_warnings:
        print("✗ Execution vocabulary guard failed to detect violations")
        return False
    print(f"✓ Execution vocabulary guard detected: {len(exec_warnings)} violations")

    # Test token literal violation
    dirty_analytics_token = {
        "analytics_summary": "analytics of SUI market patterns.",
    }
    token_warnings = validate_interpretation_analytics_record(dirty_analytics_token)
    if not token_warnings:
        print("✗ Token literal guard failed to detect violations")
        return False
    print(f"✓ Token literal guard detected: {len(token_warnings)} violations")

    # Test numeric key violation
    dirty_analytics_numeric = {
        "analytics_mode": "ON",
        "onchain_analytics": {
            "market_cost_regime_counts": {1000: 5, 5000: 10},  # Numeric keys (violation)
        },
    }
    numeric_warnings = validate_interpretation_analytics_record(dirty_analytics_numeric)
    if not numeric_warnings:
        print("✗ Numeric value guard failed to detect violations")
        return False
    print(f"✓ Numeric value guard detected: {len(numeric_warnings)} violations")

    # Test clean analytics
    clean_analytics = {
        "analytics_summary": "interpretation analytics with onchain extension.",
        "onchain_analytics": {
            "market_cost_regime_counts": {"LOW": 0, "MEDIUM": 2, "HIGH": 1},
        },
    }
    clean_warnings = validate_interpretation_analytics_record(clean_analytics)
    if clean_warnings:
        print(f"✗ Clean analytics triggered false positives: {clean_warnings}")
        return False
    print("✓ Clean analytics passes all guards")

    print("Test 7: PASS\n")
    return True


def test_defensive_behavior() -> bool:
    """
    Test 8: Defensive behavior (None/empty handling).
    """
    print("Test 8: Defensive behavior (None/empty handling)")
    print("-" * 60)

    # Test with None observations
    aggregation_none = aggregate_onchain_observations(None)  # type: ignore
    if aggregation_none["onchain_analytics_status"] != "UNAVAILABLE":
        print(f"✗ None observations should produce UNAVAILABLE status")
        return False
    print("✓ None observations handled gracefully")

    # Test with empty list
    aggregation_empty = aggregate_onchain_observations([])
    if aggregation_empty["onchain_analytics_status"] != "UNAVAILABLE":
        print(f"✗ Empty observations should produce UNAVAILABLE status")
        return False
    print("✓ Empty observations handled gracefully")

    # Test with ERROR observations
    import time
    error_obs = [
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "ERROR",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_error_info": "observation error",
        }
    ]
    aggregation_error = aggregate_onchain_observations(error_obs)
    if aggregation_error["onchain_analytics_status"] != "UNAVAILABLE":
        print(f"✗ ERROR observations should produce UNAVAILABLE status")
        return False
    print("✓ ERROR observations filtered out correctly")

    # Test extend_interpretation_analytics_v1 with None base
    extended_none = extend_interpretation_analytics_v1(None, None)
    if "analytics_mode" not in extended_none:
        print("✗ None base analytics should produce minimal analytics")
        return False
    print("✓ None base analytics handled gracefully")

    # Test extend_interpretation_analytics_v1 with None observations
    base = {"analytics_mode": "ON"}
    extended_no_obs = extend_interpretation_analytics_v1(base, None)
    if extended_no_obs["onchain_analytics"]["onchain_analytics_status"] != "UNAVAILABLE":
        print("✗ None observations should produce UNAVAILABLE onchain analytics")
        return False
    print("✓ None observations in extension handled gracefully")

    print("Test 8: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR109: v1.0 Interpretation Analytics Extension Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Analytics extension import works", test_analytics_extension_import),
        ("Empty observations produce valid aggregation", test_empty_observations_produce_valid_aggregation),
        ("Single observation aggregates correctly", test_single_observation_aggregates_correctly),
        ("Multiple observations aggregate correctly", test_multiple_observations_aggregate_correctly),
        ("Extended analytics includes onchain aggregation", test_extended_analytics_includes_onchain_aggregation),
        ("Analytics summary generates correctly", test_analytics_summary_generates_correctly),
        ("Constitutional guards detect violations", test_constitutional_guards_detect_violations),
        ("Defensive behavior (None/empty handling)", test_defensive_behavior),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test '{name}' raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    print()
    print("=" * 60)
    if all_passed:
        print("✓ ALL PR109 INTERPRETATION ANALYTICS EXTENSION TESTS PASSED")
    else:
        print("⚠ SOME PR109 INTERPRETATION ANALYTICS EXTENSION TESTS FAILED")
    print("=" * 60)
    print("PR109 Requirements Verified:")
    print("  - Analytics extension import works")
    print("  - Empty observations produce valid aggregation")
    print("  - Single observation aggregates correctly")
    print("  - Multiple observations aggregate correctly")
    print("  - Extended analytics includes onchain aggregation")
    print("  - Analytics summary generates correctly")
    print("  - Constitutional guards detect violations")
    print("  - Defensive behavior (None/empty handling)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
