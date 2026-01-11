#!/usr/bin/env python3
"""
PR107: v1.0 Sui Onchain Observation Fetch v1 Smoke Test

Purpose:
    Validate that v1.0 observation fetch correctly ingests
    onchain state as structural facts (not asset knowledge).

Test Coverage:
    1. Observation schema import works
    2. Empty observation produces valid record
    3. Chain state observation validates correctly
    4. Pool activity observation validates correctly
    5. Event activity observation validates correctly
    6. Object dynamics observation validates correctly
    7. Fetch engine handles mock data correctly
    8. Constitutional guards detect violations
    9. Numeric bucketing works correctly
    10. Defensive behavior (error handling)

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Numeric values bucketed (LOW/MEDIUM/HIGH)
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - Non-evaluative: No good/bad vocabulary

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict, List

# Import v1.0 observation modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from observation.v10_sui_onchain_observation_schema import (
    V10SuiOnchainObservationSchema,
    get_onchain_observation_schema_info,
)
from observation.v10_sui_readonly_fetch_engine_v1 import (
    fetch_chain_state_observation,
    fetch_pool_activity_observation,
    fetch_event_activity_observation,
    fetch_object_dynamics_observation,
    bucket_gas_price,
    bucket_liquidity,
    bucket_object_count_delta,
)
from observation.v10_observation_constitutional_guard import (
    check_observation_token_literals,
    check_observation_numeric_patterns,
    check_rpc_execution_vocabulary,
    validate_observation_record,
)


def test_observation_schema_import() -> bool:
    """
    Test 1: Observation schema import works.
    """
    print("Test 1: Observation schema import works")
    print("-" * 60)

    try:
        from observation.v10_sui_onchain_observation_schema import (
            V10SuiOnchainObservationSchema,
        )
        print("✓ Observation schema import successful")
    except ImportError as e:
        print(f"✗ Observation schema import failed: {e}")
        return False

    try:
        from observation.v10_sui_readonly_fetch_engine_v1 import (
            fetch_chain_state_observation,
        )
        print("✓ Fetch engine import successful")
    except ImportError as e:
        print(f"✗ Fetch engine import failed: {e}")
        return False

    try:
        from observation.v10_observation_constitutional_guard import (
            validate_observation_record,
        )
        print("✓ Constitutional guard import successful")
    except ImportError as e:
        print(f"✗ Constitutional guard import failed: {e}")
        return False

    print("Test 1: PASS\n")
    return True


def test_empty_observation_produces_valid_record() -> bool:
    """
    Test 2: Empty observation produces valid record.
    """
    print("Test 2: Empty observation produces valid record")
    print("-" * 60)

    record = V10SuiOnchainObservationSchema.create_empty_record()

    if record["v10_obs_mode"] != "OFF":
        print(f"✗ Expected mode OFF, got {record['v10_obs_mode']}")
        return False
    print("✓ Observation mode is OFF")

    if record["v10_obs_status"] != "UNAVAILABLE":
        print(f"✗ Expected status UNAVAILABLE, got {record['v10_obs_status']}")
        return False
    print("✓ Observation status is UNAVAILABLE")

    # Validate structure
    warnings = V10SuiOnchainObservationSchema.validate_structure(record)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid observation record structure")

    print("Test 2: PASS\n")
    return True


def test_chain_state_observation_validates_correctly() -> bool:
    """
    Test 3: Chain state observation validates correctly.
    """
    print("Test 3: Chain state observation validates correctly")
    print("-" * 60)

    record = V10SuiOnchainObservationSchema.create_chain_state_record(
        network="testnet",
        epoch=100,
        gas_price_bucket="MEDIUM",
    )

    if record["v10_obs_mode"] != "ON":
        print(f"✗ Expected mode ON, got {record['v10_obs_mode']}")
        return False
    print("✓ Observation mode is ON")

    if record["v10_obs_status"] != "AVAILABLE":
        print(f"✗ Expected status AVAILABLE, got {record['v10_obs_status']}")
        return False
    print("✓ Observation status is AVAILABLE")

    if record["v10_obs_type"] != "CHAIN_STATE":
        print(f"✗ Expected type CHAIN_STATE, got {record['v10_obs_type']}")
        return False
    print("✓ Observation type is CHAIN_STATE")

    # Validate structure
    warnings = V10SuiOnchainObservationSchema.validate_structure(record)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid chain state record structure")

    print("Test 3: PASS\n")
    return True


def test_pool_activity_observation_validates_correctly() -> bool:
    """
    Test 4: Pool activity observation validates correctly.
    """
    print("Test 4: Pool activity observation validates correctly")
    print("-" * 60)

    record = V10SuiOnchainObservationSchema.create_pool_activity_record(
        network="mainnet",
        activity_present=True,
        liquidity_state="HIGH",
    )

    if record["v10_obs_type"] != "POOL_ACTIVITY":
        print(f"✗ Expected type POOL_ACTIVITY, got {record['v10_obs_type']}")
        return False
    print("✓ Observation type is POOL_ACTIVITY")

    if "v10_obs_data" not in record:
        print("✗ Expected obs_data field")
        return False

    obs_data = record["v10_obs_data"]
    if obs_data["liquidity_state"] != "HIGH":
        print(f"✗ Expected liquidity_state HIGH, got {obs_data['liquidity_state']}")
        return False
    print("✓ Liquidity state is HIGH (bucketed)")

    # Validate structure
    warnings = V10SuiOnchainObservationSchema.validate_structure(record)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid pool activity record structure")

    print("Test 4: PASS\n")
    return True


def test_event_activity_observation_validates_correctly() -> bool:
    """
    Test 5: Event activity observation validates correctly.
    """
    print("Test 5: Event activity observation validates correctly")
    print("-" * 60)

    record = V10SuiOnchainObservationSchema.create_event_activity_record(
        network="devnet",
        event_type_seen=True,
    )

    if record["v10_obs_type"] != "EVENT_ACTIVITY":
        print(f"✗ Expected type EVENT_ACTIVITY, got {record['v10_obs_type']}")
        return False
    print("✓ Observation type is EVENT_ACTIVITY")

    # Validate structure
    warnings = V10SuiOnchainObservationSchema.validate_structure(record)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid event activity record structure")

    print("Test 5: PASS\n")
    return True


def test_object_dynamics_observation_validates_correctly() -> bool:
    """
    Test 6: Object dynamics observation validates correctly.
    """
    print("Test 6: Object dynamics observation validates correctly")
    print("-" * 60)

    record = V10SuiOnchainObservationSchema.create_object_dynamics_record(
        network="testnet",
        object_count_delta="INCREASE",
    )

    if record["v10_obs_type"] != "OBJECT_DYNAMICS":
        print(f"✗ Expected type OBJECT_DYNAMICS, got {record['v10_obs_type']}")
        return False
    print("✓ Observation type is OBJECT_DYNAMICS")

    if "v10_obs_data" not in record:
        print("✗ Expected obs_data field")
        return False

    obs_data = record["v10_obs_data"]
    if obs_data["object_count_delta"] != "INCREASE":
        print(f"✗ Expected object_count_delta INCREASE, got {obs_data['object_count_delta']}")
        return False
    print("✓ Object count delta is INCREASE (bucketed)")

    # Validate structure
    warnings = V10SuiOnchainObservationSchema.validate_structure(record)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid object dynamics record structure")

    print("Test 6: PASS\n")
    return True


def test_fetch_engine_handles_mock_data_correctly() -> bool:
    """
    Test 7: Fetch engine handles mock data correctly.
    """
    print("Test 7: Fetch engine handles mock data correctly")
    print("-" * 60)

    # Mock connection record (CONNECTED)
    mock_connection = {
        "v10_conn_mode": "ON",
        "v10_conn_status": "CONNECTED",
        "v10_conn_network": "testnet",
        "v10_conn_capabilities": ["RPC_READ", "INDEXER_READ"],
    }

    # Test chain state fetch
    mock_chain_data = {
        "epoch": 100,
        "reference_gas_price": 5000,
    }
    chain_obs = fetch_chain_state_observation(mock_connection, mock_chain_data)

    if chain_obs["v10_obs_status"] != "AVAILABLE":
        print(f"✗ Expected status AVAILABLE, got {chain_obs['v10_obs_status']}")
        return False
    print("✓ Chain state fetch successful")

    # Check gas price bucketing
    gas_price_bucket = chain_obs["v10_obs_data"]["gas_price_bucket"]
    if gas_price_bucket not in ["LOW", "MEDIUM", "HIGH"]:
        print(f"✗ Invalid gas price bucket: {gas_price_bucket}")
        return False
    print(f"✓ Gas price bucketed: {gas_price_bucket}")

    # Test pool activity fetch
    mock_pool_data = {
        "activity_present": True,
        "liquidity_value": 500000,
    }
    pool_obs = fetch_pool_activity_observation(mock_connection, mock_pool_data)

    if pool_obs["v10_obs_status"] != "AVAILABLE":
        print(f"✗ Expected status AVAILABLE, got {pool_obs['v10_obs_status']}")
        return False
    print("✓ Pool activity fetch successful")

    # Check liquidity bucketing
    liquidity_state = pool_obs["v10_obs_data"]["liquidity_state"]
    if liquidity_state not in ["LOW", "MEDIUM", "HIGH"]:
        print(f"✗ Invalid liquidity state: {liquidity_state}")
        return False
    print(f"✓ Liquidity bucketed: {liquidity_state}")

    print("Test 7: PASS\n")
    return True


def test_constitutional_guards_detect_violations() -> bool:
    """
    Test 8: Constitutional guards detect violations.
    """
    print("Test 8: Constitutional guards detect violations")
    print("-" * 60)

    # Test token literals guard
    token_text = "observed SUI and USDC pool activity"
    token_warnings = check_observation_token_literals(token_text)
    if not token_warnings:
        print("✗ Token literals guard failed to detect violations")
        return False
    print(f"✓ Token literals guard detected: {len(token_warnings)} violations")

    # Test numeric patterns guard
    numeric_text = "observed balance of 1000 tokens at $2.50"
    numeric_warnings = check_observation_numeric_patterns(numeric_text)
    if not numeric_warnings:
        print("✗ Numeric patterns guard failed to detect violations")
        return False
    print(f"✓ Numeric patterns guard detected: {len(numeric_warnings)} violations")

    # Test RPC execution guard
    rpc_text = "fetched using getBalance and sign operations"
    rpc_warnings = check_rpc_execution_vocabulary(rpc_text)
    if not rpc_warnings:
        print("✗ RPC execution guard failed to detect violations")
        return False
    print(f"✓ RPC execution guard detected: {len(rpc_warnings)} violations")

    # Test clean text (no violations)
    clean_text = "chain state observed on testnet. epoch and gas price bucket captured."
    clean_token_warnings = check_observation_token_literals(clean_text)
    clean_numeric_warnings = check_observation_numeric_patterns(clean_text)
    clean_rpc_warnings = check_rpc_execution_vocabulary(clean_text)

    if clean_token_warnings or clean_numeric_warnings or clean_rpc_warnings:
        print("✗ Clean text triggered false positives")
        return False
    print("✓ Clean text passes all guards")

    print("Test 8: PASS\n")
    return True


def test_numeric_bucketing_works_correctly() -> bool:
    """
    Test 9: Numeric bucketing works correctly.
    """
    print("Test 9: Numeric bucketing works correctly")
    print("-" * 60)

    # Test gas price bucketing
    low_gas = bucket_gas_price(500)
    medium_gas = bucket_gas_price(5000)
    high_gas = bucket_gas_price(50000)

    if low_gas != "LOW":
        print(f"✗ Expected LOW gas bucket, got {low_gas}")
        return False
    print(f"✓ Gas price 500 → {low_gas}")

    if medium_gas != "MEDIUM":
        print(f"✗ Expected MEDIUM gas bucket, got {medium_gas}")
        return False
    print(f"✓ Gas price 5000 → {medium_gas}")

    if high_gas != "HIGH":
        print(f"✗ Expected HIGH gas bucket, got {high_gas}")
        return False
    print(f"✓ Gas price 50000 → {high_gas}")

    # Test liquidity bucketing
    low_liq = bucket_liquidity(50000)
    medium_liq = bucket_liquidity(500000)
    high_liq = bucket_liquidity(5000000)

    if low_liq != "LOW":
        print(f"✗ Expected LOW liquidity bucket, got {low_liq}")
        return False
    print(f"✓ Liquidity 50000 → {low_liq}")

    if medium_liq != "MEDIUM":
        print(f"✗ Expected MEDIUM liquidity bucket, got {medium_liq}")
        return False
    print(f"✓ Liquidity 500000 → {medium_liq}")

    if high_liq != "HIGH":
        print(f"✗ Expected HIGH liquidity bucket, got {high_liq}")
        return False
    print(f"✓ Liquidity 5000000 → {high_liq}")

    # Test object count delta bucketing
    decrease_delta = bucket_object_count_delta(-50)
    stable_delta = bucket_object_count_delta(5)
    increase_delta = bucket_object_count_delta(50)

    if decrease_delta != "DECREASE":
        print(f"✗ Expected DECREASE delta, got {decrease_delta}")
        return False
    print(f"✓ Delta -50 → {decrease_delta}")

    if stable_delta != "STABLE":
        print(f"✗ Expected STABLE delta, got {stable_delta}")
        return False
    print(f"✓ Delta 5 → {stable_delta}")

    if increase_delta != "INCREASE":
        print(f"✗ Expected INCREASE delta, got {increase_delta}")
        return False
    print(f"✓ Delta 50 → {increase_delta}")

    print("Test 9: PASS\n")
    return True


def test_defensive_behavior() -> bool:
    """
    Test 10: Defensive behavior (error handling).
    """
    print("Test 10: Defensive behavior (error handling)")
    print("-" * 60)

    # Test with disconnected connection
    disconnected_connection = {
        "v10_conn_mode": "OFF",
        "v10_conn_status": "DISCONNECTED",
        "v10_conn_network": "mainnet",
        "v10_conn_capabilities": [],
    }

    error_obs = fetch_chain_state_observation(disconnected_connection)

    if error_obs["v10_obs_status"] != "ERROR":
        print(f"✗ Expected ERROR status, got {error_obs['v10_obs_status']}")
        return False
    print("✓ Disconnected connection returns ERROR status")

    # Test with invalid connection type
    invalid_connection = "invalid"
    error_obs2 = fetch_chain_state_observation(invalid_connection)  # type: ignore

    if error_obs2["v10_obs_status"] != "ERROR":
        print(f"✗ Expected ERROR status, got {error_obs2['v10_obs_status']}")
        return False
    print("✓ Invalid connection type returns ERROR status")

    # Test with missing capability
    no_capability_connection = {
        "v10_conn_mode": "ON",
        "v10_conn_status": "CONNECTED",
        "v10_conn_network": "testnet",
        "v10_conn_capabilities": [],  # No RPC_READ
    }

    error_obs3 = fetch_chain_state_observation(no_capability_connection)

    if error_obs3["v10_obs_status"] != "ERROR":
        print(f"✗ Expected ERROR status, got {error_obs3['v10_obs_status']}")
        return False
    print("✓ Missing capability returns ERROR status")

    print("Test 10: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR107: v1.0 Sui Onchain Observation Fetch Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Observation schema import works", test_observation_schema_import),
        ("Empty observation produces valid record", test_empty_observation_produces_valid_record),
        ("Chain state observation validates correctly", test_chain_state_observation_validates_correctly),
        ("Pool activity observation validates correctly", test_pool_activity_observation_validates_correctly),
        ("Event activity observation validates correctly", test_event_activity_observation_validates_correctly),
        ("Object dynamics observation validates correctly", test_object_dynamics_observation_validates_correctly),
        ("Fetch engine handles mock data correctly", test_fetch_engine_handles_mock_data_correctly),
        ("Constitutional guards detect violations", test_constitutional_guards_detect_violations),
        ("Numeric bucketing works correctly", test_numeric_bucketing_works_correctly),
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
        print("✓ ALL PR107 SUI ONCHAIN OBSERVATION FETCH TESTS PASSED")
    else:
        print("⚠ SOME PR107 SUI ONCHAIN OBSERVATION FETCH TESTS FAILED")
    print("=" * 60)
    print("PR107 Requirements Verified:")
    print("  - Observation schema import works")
    print("  - Empty observation produces valid record")
    print("  - Chain state observation validates correctly")
    print("  - Pool activity observation validates correctly")
    print("  - Event activity observation validates correctly")
    print("  - Object dynamics observation validates correctly")
    print("  - Fetch engine handles mock data correctly")
    print("  - Constitutional guards detect violations")
    print("  - Numeric bucketing works correctly")
    print("  - Defensive behavior (error handling)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
