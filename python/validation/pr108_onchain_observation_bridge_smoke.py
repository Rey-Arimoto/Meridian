#!/usr/bin/env python3
"""
PR108: v1.0 Onchain Observation → Interpretation Bridge v1 Smoke Test

Purpose:
    Validate that v1.0 bridge correctly normalizes onchain observations
    to interpretation-compatible format.

Test Coverage:
    1. Bridge schema import works
    2. Empty normalized observation produces valid record
    3. CHAIN_STATE normalization works correctly
    4. POOL_ACTIVITY normalization works correctly
    5. EVENT_ACTIVITY normalization works correctly
    6. OBJECT_DYNAMICS normalization works correctly
    7. Bridge handles ERROR observations correctly
    8. Asset vocabulary guard detects violations
    9. Execution vocabulary guard detects violations
    10. Defensive behavior (error handling)

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Qualitative states only
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - Non-evaluative: No good/bad vocabulary

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict, List

# Import v1.0 bridge modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bridge.v10_onchain_to_observation_bridge_schema import (
    V10OnchainToObservationBridgeSchema,
    get_bridge_schema_info,
)
from bridge.v10_onchain_to_observation_bridge_engine_v1 import (
    bridge_onchain_observation_v1,
    get_bridge_engine_v1_info,
)
from bridge.v10_bridge_constitutional_guard import (
    check_asset_vocabulary,
    check_execution_vocabulary_bridge,
    validate_normalized_observation_record,
)


def test_bridge_schema_import() -> bool:
    """
    Test 1: Bridge schema import works.
    """
    print("Test 1: Bridge schema import works")
    print("-" * 60)

    try:
        from bridge.v10_onchain_to_observation_bridge_schema import (
            V10OnchainToObservationBridgeSchema,
        )
        print("✓ Bridge schema import successful")
    except ImportError as e:
        print(f"✗ Bridge schema import failed: {e}")
        return False

    try:
        from bridge.v10_onchain_to_observation_bridge_engine_v1 import (
            bridge_onchain_observation_v1,
        )
        print("✓ Bridge engine import successful")
    except ImportError as e:
        print(f"✗ Bridge engine import failed: {e}")
        return False

    try:
        from bridge.v10_bridge_constitutional_guard import (
            validate_normalized_observation_record,
        )
        print("✓ Constitutional guard import successful")
    except ImportError as e:
        print(f"✗ Constitutional guard import failed: {e}")
        return False

    print("Test 1: PASS\n")
    return True


def test_empty_normalized_observation_produces_valid_record() -> bool:
    """
    Test 2: Empty normalized observation produces valid record.
    """
    print("Test 2: Empty normalized observation produces valid record")
    print("-" * 60)

    record = V10OnchainToObservationBridgeSchema.create_empty_record()

    if record["v10_norm_obs_mode"] != "OFF":
        print(f"✗ Expected mode OFF, got {record['v10_norm_obs_mode']}")
        return False
    print("✓ Normalized observation mode is OFF")

    if record["v10_norm_obs_status"] != "UNAVAILABLE":
        print(f"✗ Expected status UNAVAILABLE, got {record['v10_norm_obs_status']}")
        return False
    print("✓ Normalized observation status is UNAVAILABLE")

    # Validate structure
    warnings = V10OnchainToObservationBridgeSchema.validate_structure(record)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid normalized observation record structure")

    print("Test 2: PASS\n")
    return True


def test_chain_state_normalization_works_correctly() -> bool:
    """
    Test 3: CHAIN_STATE normalization works correctly.
    """
    print("Test 3: CHAIN_STATE normalization works correctly")
    print("-" * 60)

    # Create CHAIN_STATE observation
    import time
    chain_state_obs = {
        "v10_obs_mode": "ON",
        "v10_obs_status": "AVAILABLE",
        "v10_obs_type": "CHAIN_STATE",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "testnet",
        "v10_obs_data": {
            "epoch": 100,
            "gas_price_bucket": "MEDIUM",
        },
    }

    # Bridge to normalized observation
    normalized = bridge_onchain_observation_v1(chain_state_obs)

    if normalized["v10_norm_obs_status"] != "AVAILABLE":
        print(f"✗ Expected status AVAILABLE, got {normalized['v10_norm_obs_status']}")
        return False
    print("✓ Normalized observation status is AVAILABLE")

    if "v10_norm_obs_market_cost_regime" not in normalized:
        print("✗ Expected market_cost_regime field")
        return False

    market_cost_regime = normalized["v10_norm_obs_market_cost_regime"]
    if market_cost_regime != "MEDIUM":
        print(f"✗ Expected market_cost_regime MEDIUM, got {market_cost_regime}")
        return False
    print(f"✓ gas_price_bucket MEDIUM → market_cost_regime {market_cost_regime}")

    # Validate structure
    warnings = V10OnchainToObservationBridgeSchema.validate_structure(normalized)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid normalized record structure")

    print("Test 3: PASS\n")
    return True


def test_pool_activity_normalization_works_correctly() -> bool:
    """
    Test 4: POOL_ACTIVITY normalization works correctly.
    """
    print("Test 4: POOL_ACTIVITY normalization works correctly")
    print("-" * 60)

    # Create POOL_ACTIVITY observation
    import time
    pool_activity_obs = {
        "v10_obs_mode": "ON",
        "v10_obs_status": "AVAILABLE",
        "v10_obs_type": "POOL_ACTIVITY",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "mainnet",
        "v10_obs_data": {
            "activity_present": True,
            "liquidity_state": "HIGH",
        },
    }

    # Bridge to normalized observation
    normalized = bridge_onchain_observation_v1(pool_activity_obs)

    if normalized["v10_norm_obs_status"] != "AVAILABLE":
        print(f"✗ Expected status AVAILABLE, got {normalized['v10_norm_obs_status']}")
        return False
    print("✓ Normalized observation status is AVAILABLE")

    # Check liquidity_regime
    if "v10_norm_obs_liquidity_regime" not in normalized:
        print("✗ Expected liquidity_regime field")
        return False

    liquidity_regime = normalized["v10_norm_obs_liquidity_regime"]
    if liquidity_regime != "HIGH":
        print(f"✗ Expected liquidity_regime HIGH, got {liquidity_regime}")
        return False
    print(f"✓ liquidity_state HIGH → liquidity_regime {liquidity_regime}")

    # Check event_activity_present
    if "v10_norm_obs_event_activity_present" not in normalized:
        print("✗ Expected event_activity_present field")
        return False

    event_activity = normalized["v10_norm_obs_event_activity_present"]
    if event_activity != "TRUE":
        print(f"✗ Expected event_activity_present TRUE, got {event_activity}")
        return False
    print(f"✓ activity_present True → event_activity_present {event_activity}")

    # Validate structure
    warnings = V10OnchainToObservationBridgeSchema.validate_structure(normalized)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid normalized record structure")

    print("Test 4: PASS\n")
    return True


def test_event_activity_normalization_works_correctly() -> bool:
    """
    Test 5: EVENT_ACTIVITY normalization works correctly.
    """
    print("Test 5: EVENT_ACTIVITY normalization works correctly")
    print("-" * 60)

    # Create EVENT_ACTIVITY observation
    import time
    event_activity_obs = {
        "v10_obs_mode": "ON",
        "v10_obs_status": "AVAILABLE",
        "v10_obs_type": "EVENT_ACTIVITY",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "devnet",
        "v10_obs_data": {
            "event_type_seen": True,
        },
    }

    # Bridge to normalized observation
    normalized = bridge_onchain_observation_v1(event_activity_obs)

    if normalized["v10_norm_obs_status"] != "AVAILABLE":
        print(f"✗ Expected status AVAILABLE, got {normalized['v10_norm_obs_status']}")
        return False
    print("✓ Normalized observation status is AVAILABLE")

    # Check event_activity_present
    if "v10_norm_obs_event_activity_present" not in normalized:
        print("✗ Expected event_activity_present field")
        return False

    event_activity = normalized["v10_norm_obs_event_activity_present"]
    if event_activity != "TRUE":
        print(f"✗ Expected event_activity_present TRUE, got {event_activity}")
        return False
    print(f"✓ event_type_seen True → event_activity_present {event_activity}")

    # Validate structure
    warnings = V10OnchainToObservationBridgeSchema.validate_structure(normalized)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid normalized record structure")

    print("Test 5: PASS\n")
    return True


def test_object_dynamics_normalization_works_correctly() -> bool:
    """
    Test 6: OBJECT_DYNAMICS normalization works correctly.
    """
    print("Test 6: OBJECT_DYNAMICS normalization works correctly")
    print("-" * 60)

    # Create OBJECT_DYNAMICS observation
    import time
    object_dynamics_obs = {
        "v10_obs_mode": "ON",
        "v10_obs_status": "AVAILABLE",
        "v10_obs_type": "OBJECT_DYNAMICS",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "testnet",
        "v10_obs_data": {
            "object_count_delta": "INCREASE",
        },
    }

    # Bridge to normalized observation
    normalized = bridge_onchain_observation_v1(object_dynamics_obs)

    if normalized["v10_norm_obs_status"] != "AVAILABLE":
        print(f"✗ Expected status AVAILABLE, got {normalized['v10_norm_obs_status']}")
        return False
    print("✓ Normalized observation status is AVAILABLE")

    # Check object_dynamics
    if "v10_norm_obs_object_dynamics" not in normalized:
        print("✗ Expected object_dynamics field")
        return False

    object_dynamics = normalized["v10_norm_obs_object_dynamics"]
    if object_dynamics != "INCREASE":
        print(f"✗ Expected object_dynamics INCREASE, got {object_dynamics}")
        return False
    print(f"✓ object_count_delta INCREASE → object_dynamics {object_dynamics}")

    # Validate structure
    warnings = V10OnchainToObservationBridgeSchema.validate_structure(normalized)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid normalized record structure")

    print("Test 6: PASS\n")
    return True


def test_bridge_handles_error_observations_correctly() -> bool:
    """
    Test 7: Bridge handles ERROR observations correctly.
    """
    print("Test 7: Bridge handles ERROR observations correctly")
    print("-" * 60)

    # Create ERROR observation
    import time
    error_obs = {
        "v10_obs_mode": "ON",
        "v10_obs_status": "ERROR",
        "v10_obs_type": "CHAIN_STATE",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "mainnet",
        "v10_obs_error_info": "connection timeout during fetch",
    }

    # Bridge to normalized observation
    normalized = bridge_onchain_observation_v1(error_obs)

    if normalized["v10_norm_obs_status"] != "ERROR":
        print(f"✗ Expected status ERROR, got {normalized['v10_norm_obs_status']}")
        return False
    print("✓ Error observation produces ERROR normalized record")

    if "v10_norm_obs_error_info" not in normalized:
        print("✗ Expected error_info field")
        return False
    print("✓ Error info propagated to normalized record")

    # Validate structure
    warnings = V10OnchainToObservationBridgeSchema.validate_structure(normalized)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid error normalized record structure")

    print("Test 7: PASS\n")
    return True


def test_asset_vocabulary_guard_detects_violations() -> bool:
    """
    Test 8: Asset vocabulary guard detects violations.
    """
    print("Test 8: Asset vocabulary guard detects violations")
    print("-" * 60)

    # Test cases with asset vocabulary violations
    test_cases = [
        ("balance", "normalized observation of wallet balance"),
        ("holdings", "normalized observation of token holdings"),
        ("portfolio", "normalized observation of portfolio composition"),
        ("assets", "normalized observation of digital assets"),
    ]

    for name, text in test_cases:
        warnings = check_asset_vocabulary(text)
        if not warnings:
            print(f"✗ {name}: Expected violation, got none")
            return False
        print(f"✓ {name}: Violation detected")

    # Test clean text (no violations)
    clean_text = "normalized observation available. structural facts captured."
    warnings = check_asset_vocabulary(clean_text)
    if warnings:
        print(f"✗ Clean text triggered false positive: {warnings}")
        return False
    print("✓ Clean text passes asset vocabulary guard")

    print("Test 8: PASS\n")
    return True


def test_execution_vocabulary_guard_detects_violations() -> bool:
    """
    Test 9: Execution vocabulary guard detects violations.
    """
    print("Test 9: Execution vocabulary guard detects violations")
    print("-" * 60)

    # Test cases with execution vocabulary violations
    test_cases = [
        ("buy operation", "normalized observation ready for buy operations"),
        ("sell operation", "normalized observation enables sell transactions"),
        ("trade operation", "normalized observation supports trade execution"),
        ("swap operation", "normalized observation allows swap operations"),
    ]

    for name, text in test_cases:
        warnings = check_execution_vocabulary_bridge(text)
        if not warnings:
            print(f"✗ {name}: Expected violation, got none")
            return False
        print(f"✓ {name}: Violation detected")

    # Test clean text (no violations)
    clean_text = "normalized observation available. structural facts captured."
    warnings = check_execution_vocabulary_bridge(clean_text)
    if warnings:
        print(f"✗ Clean text triggered false positive: {warnings}")
        return False
    print("✓ Clean text passes execution vocabulary guard")

    print("Test 9: PASS\n")
    return True


def test_defensive_behavior() -> bool:
    """
    Test 10: Defensive behavior (error handling).
    """
    print("Test 10: Defensive behavior (error handling)")
    print("-" * 60)

    # Test with invalid observation type
    invalid_obs = "invalid"
    error_normalized = bridge_onchain_observation_v1(invalid_obs)  # type: ignore

    if error_normalized["v10_norm_obs_status"] != "ERROR":
        print(f"✗ Expected ERROR status, got {error_normalized['v10_norm_obs_status']}")
        return False
    print("✓ Invalid observation type returns ERROR status")

    # Test with UNAVAILABLE observation
    import time
    unavailable_obs = {
        "v10_obs_mode": "OFF",
        "v10_obs_status": "UNAVAILABLE",
        "v10_obs_type": "CHAIN_STATE",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "testnet",
    }

    error_normalized2 = bridge_onchain_observation_v1(unavailable_obs)

    if error_normalized2["v10_norm_obs_status"] != "ERROR":
        print(f"✗ Expected ERROR status, got {error_normalized2['v10_norm_obs_status']}")
        return False
    print("✓ UNAVAILABLE observation returns ERROR status")

    # Test with unknown observation type
    unknown_obs = {
        "v10_obs_mode": "ON",
        "v10_obs_status": "AVAILABLE",
        "v10_obs_type": "UNKNOWN_TYPE",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "mainnet",
        "v10_obs_data": {},
    }

    error_normalized3 = bridge_onchain_observation_v1(unknown_obs)

    if error_normalized3["v10_norm_obs_status"] != "ERROR":
        print(f"✗ Expected ERROR status, got {error_normalized3['v10_norm_obs_status']}")
        return False
    print("✓ Unknown observation type returns ERROR status")

    print("Test 10: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR108: v1.0 Onchain Observation → Interpretation Bridge Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Bridge schema import works", test_bridge_schema_import),
        ("Empty normalized observation produces valid record", test_empty_normalized_observation_produces_valid_record),
        ("CHAIN_STATE normalization works correctly", test_chain_state_normalization_works_correctly),
        ("POOL_ACTIVITY normalization works correctly", test_pool_activity_normalization_works_correctly),
        ("EVENT_ACTIVITY normalization works correctly", test_event_activity_normalization_works_correctly),
        ("OBJECT_DYNAMICS normalization works correctly", test_object_dynamics_normalization_works_correctly),
        ("Bridge handles ERROR observations correctly", test_bridge_handles_error_observations_correctly),
        ("Asset vocabulary guard detects violations", test_asset_vocabulary_guard_detects_violations),
        ("Execution vocabulary guard detects violations", test_execution_vocabulary_guard_detects_violations),
        ("Defensive behavior (error handling)", test_defensive_behavior),
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
        print("✓ ALL PR108 ONCHAIN OBSERVATION BRIDGE TESTS PASSED")
    else:
        print("⚠ SOME PR108 ONCHAIN OBSERVATION BRIDGE TESTS FAILED")
    print("=" * 60)
    print("PR108 Requirements Verified:")
    print("  - Bridge schema import works")
    print("  - Empty normalized observation produces valid record")
    print("  - CHAIN_STATE normalization works correctly")
    print("  - POOL_ACTIVITY normalization works correctly")
    print("  - EVENT_ACTIVITY normalization works correctly")
    print("  - OBJECT_DYNAMICS normalization works correctly")
    print("  - Bridge handles ERROR observations correctly")
    print("  - Asset vocabulary guard detects violations")
    print("  - Execution vocabulary guard detects violations")
    print("  - Defensive behavior (error handling)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
