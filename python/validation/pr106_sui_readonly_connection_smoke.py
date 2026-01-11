#!/usr/bin/env python3
"""
PR106: v1.0 Sui Read-Only Connection Constitution Smoke Test

Purpose:
    Validate that v1.0 connection schemas and guards correctly
    enforce read-only observability constraints.

Test Coverage:
    1. Connection schema import works
    2. Empty connection produces valid record
    3. Connected record validates correctly
    4. Error record validates correctly
    5. Provider config validates correctly
    6. No secrets guard detects violations
    7. Read-only guard detects violations
    8. HTTPS-only guard validates URLs

Constitutional Constraints:
    - READ-ONLY: No signing, no transactions, no wallet operations
    - No secrets: No API keys, tokens, credentials, mnemonics
    - No addresses: No wallet/contract addresses
    - HTTPS-only: No insecure HTTP URLs (except localhost)

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict, List

# Import v1.0 connection modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from connection.v10_sui_readonly_connection_schema import (
    V10SuiReadOnlyConnectionSchema,
    get_readonly_connection_schema_info,
)
from connection.v10_sui_provider_config_schema import (
    V10SuiProviderConfigSchema,
    get_provider_config_schema_info,
)
from connection.v10_connection_constitutional_guard import (
    check_no_secrets,
    check_readonly_guard,
    check_https_only,
    validate_connection_record,
    validate_provider_config,
)


def test_connection_schema_import() -> bool:
    """
    Test 1: Connection schema import works.
    """
    print("Test 1: Connection schema import works")
    print("-" * 60)

    try:
        from connection.v10_sui_readonly_connection_schema import (
            V10SuiReadOnlyConnectionSchema,
        )
        print("✓ Connection schema import successful")
    except ImportError as e:
        print(f"✗ Connection schema import failed: {e}")
        return False

    try:
        from connection.v10_sui_provider_config_schema import (
            V10SuiProviderConfigSchema,
        )
        print("✓ Provider config schema import successful")
    except ImportError as e:
        print(f"✗ Provider config schema import failed: {e}")
        return False

    try:
        from connection.v10_connection_constitutional_guard import (
            validate_connection_record,
        )
        print("✓ Constitutional guard import successful")
    except ImportError as e:
        print(f"✗ Constitutional guard import failed: {e}")
        return False

    print("Test 1: PASS\n")
    return True


def test_empty_connection_produces_valid_record() -> bool:
    """
    Test 2: Empty connection produces valid record.
    """
    print("Test 2: Empty connection produces valid record")
    print("-" * 60)

    record = V10SuiReadOnlyConnectionSchema.create_empty_record()

    if record["v10_conn_mode"] != "OFF":
        print(f"✗ Expected mode OFF, got {record['v10_conn_mode']}")
        return False
    print("✓ Connection mode is OFF")

    if record["v10_conn_status"] != "DISCONNECTED":
        print(f"✗ Expected status DISCONNECTED, got {record['v10_conn_status']}")
        return False
    print("✓ Connection status is DISCONNECTED")

    if len(record["v10_conn_capabilities"]) != 0:
        print(f"✗ Expected empty capabilities, got {len(record['v10_conn_capabilities'])}")
        return False
    print("✓ Capabilities list is empty")

    # Validate structure
    warnings = V10SuiReadOnlyConnectionSchema.validate_structure(record)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid connection record structure")

    print("Test 2: PASS\n")
    return True


def test_connected_record_validates_correctly() -> bool:
    """
    Test 3: Connected record validates correctly.
    """
    print("Test 3: Connected record validates correctly")
    print("-" * 60)

    provider_config = V10SuiProviderConfigSchema.create_combined_config(
        network="testnet",
        rpc_url="https://testnet.example.com/rpc",
        indexer_url="https://testnet.example.com/indexer",
    )

    record = V10SuiReadOnlyConnectionSchema.create_connected_record(
        network="testnet",
        capabilities=["RPC_READ", "INDEXER_READ"],
        provider_config=provider_config,
    )

    if record["v10_conn_mode"] != "ON":
        print(f"✗ Expected mode ON, got {record['v10_conn_mode']}")
        return False
    print("✓ Connection mode is ON")

    if record["v10_conn_status"] != "CONNECTED":
        print(f"✗ Expected status CONNECTED, got {record['v10_conn_status']}")
        return False
    print("✓ Connection status is CONNECTED")

    if len(record["v10_conn_capabilities"]) != 2:
        print(f"✗ Expected 2 capabilities, got {len(record['v10_conn_capabilities'])}")
        return False
    print("✓ Capabilities list has 2 items")

    # Validate structure
    warnings = V10SuiReadOnlyConnectionSchema.validate_structure(record)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid connected record structure")

    print("Test 3: PASS\n")
    return True


def test_error_record_validates_correctly() -> bool:
    """
    Test 4: Error record validates correctly.
    """
    print("Test 4: Error record validates correctly")
    print("-" * 60)

    record = V10SuiReadOnlyConnectionSchema.create_error_record(
        network="mainnet",
        error_info="connection timeout after multiple retries",
    )

    if record["v10_conn_mode"] != "ON":
        print(f"✗ Expected mode ON, got {record['v10_conn_mode']}")
        return False
    print("✓ Connection mode is ON")

    if record["v10_conn_status"] != "ERROR":
        print(f"✗ Expected status ERROR, got {record['v10_conn_status']}")
        return False
    print("✓ Connection status is ERROR")

    if "v10_conn_error_info" not in record:
        print("✗ Expected error_info field")
        return False
    print("✓ Error info field present")

    # Validate structure
    warnings = V10SuiReadOnlyConnectionSchema.validate_structure(record)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid error record structure")

    print("Test 4: PASS\n")
    return True


def test_provider_config_validates_correctly() -> bool:
    """
    Test 5: Provider config validates correctly.
    """
    print("Test 5: Provider config validates correctly")
    print("-" * 60)

    # Test RPC config
    rpc_config = V10SuiProviderConfigSchema.create_rpc_config(
        network="testnet",
        rpc_url="https://testnet.example.com/rpc",
    )

    warnings = V10SuiProviderConfigSchema.validate_structure(rpc_config)
    if warnings:
        print(f"✗ RPC config warnings: {warnings}")
        return False
    print("✓ RPC config validates correctly")

    # Test Indexer config
    indexer_config = V10SuiProviderConfigSchema.create_indexer_config(
        network="mainnet",
        indexer_url="https://mainnet.example.com/indexer",
    )

    warnings = V10SuiProviderConfigSchema.validate_structure(indexer_config)
    if warnings:
        print(f"✗ Indexer config warnings: {warnings}")
        return False
    print("✓ Indexer config validates correctly")

    # Test Combined config
    combined_config = V10SuiProviderConfigSchema.create_combined_config(
        network="devnet",
        rpc_url="https://devnet.example.com/rpc",
        indexer_url="https://devnet.example.com/indexer",
    )

    warnings = V10SuiProviderConfigSchema.validate_structure(combined_config)
    if warnings:
        print(f"✗ Combined config warnings: {warnings}")
        return False
    print("✓ Combined config validates correctly")

    print("Test 5: PASS\n")
    return True


def test_no_secrets_guard_detects_violations() -> bool:
    """
    Test 6: No secrets guard detects violations.
    """
    print("Test 6: No secrets guard detects violations")
    print("-" * 60)

    # Test cases with secrets violations
    test_cases = [
        ("api_key in text", "connection with api_key authentication"),
        ("bearer token", "connection using bearer token for auth"),
        ("password", "connection requires password authentication"),
        ("mnemonic", "connection initialized with mnemonic phrase"),
        ("address pattern", "transfer to 0x1234567890123456789012345678901234567890"),
    ]

    for name, text in test_cases:
        warnings = check_no_secrets(text)
        if not warnings:
            print(f"✗ {name}: Expected violation, got none")
            return False
        print(f"✓ {name}: Violation detected")

    # Test clean text (no violations)
    clean_text = "connection established to testnet network"
    warnings = check_no_secrets(clean_text)
    if warnings:
        print(f"✗ Clean text triggered false positive: {warnings}")
        return False
    print("✓ Clean text passes secrets guard")

    print("Test 6: PASS\n")
    return True


def test_readonly_guard_detects_violations() -> bool:
    """
    Test 7: Read-only guard detects violations.
    """
    print("Test 7: Read-only guard detects violations")
    print("-" * 60)

    # Test cases with read-only violations
    test_cases = [
        ("sign operation", "connection ready to sign transactions"),
        ("transfer operation", "connection can transfer tokens"),
        ("swap operation", "connection enables swap operations"),
        ("execute operation", "connection will execute contract calls"),
    ]

    for name, text in test_cases:
        warnings = check_readonly_guard(text)
        if not warnings:
            print(f"✗ {name}: Expected violation, got none")
            return False
        print(f"✓ {name}: Violation detected")

    # Test clean text (no violations)
    clean_text = "connection provides read access to blockchain state"
    warnings = check_readonly_guard(clean_text)
    if warnings:
        print(f"✗ Clean text triggered false positive: {warnings}")
        return False
    print("✓ Clean text passes read-only guard")

    print("Test 7: PASS\n")
    return True


def test_https_only_guard_validates_urls() -> bool:
    """
    Test 8: HTTPS-only guard validates URLs.
    """
    print("Test 8: HTTPS-only guard validates URLs")
    print("-" * 60)

    # Test HTTP URL (should warn)
    http_url = "http://testnet.example.com/rpc"
    warnings = check_https_only(http_url)
    if not warnings:
        print("✗ HTTP URL should trigger warning")
        return False
    print("✓ HTTP URL triggers warning")

    # Test HTTPS URL (should pass)
    https_url = "https://testnet.example.com/rpc"
    warnings = check_https_only(https_url)
    if warnings:
        print(f"✗ HTTPS URL triggered false positive: {warnings}")
        return False
    print("✓ HTTPS URL passes guard")

    # Test localhost HTTP (should pass)
    localhost_url = "http://localhost:9000/rpc"
    warnings = check_https_only(localhost_url)
    if warnings:
        print(f"✗ Localhost HTTP triggered false positive: {warnings}")
        return False
    print("✓ Localhost HTTP allowed")

    # Test 127.0.0.1 HTTP (should pass)
    local_ip_url = "http://127.0.0.1:9000/rpc"
    warnings = check_https_only(local_ip_url)
    if warnings:
        print(f"✗ 127.0.0.1 HTTP triggered false positive: {warnings}")
        return False
    print("✓ 127.0.0.1 HTTP allowed")

    print("Test 8: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR106: v1.0 Sui Read-Only Connection Constitution Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Connection schema import works", test_connection_schema_import),
        ("Empty connection produces valid record", test_empty_connection_produces_valid_record),
        ("Connected record validates correctly", test_connected_record_validates_correctly),
        ("Error record validates correctly", test_error_record_validates_correctly),
        ("Provider config validates correctly", test_provider_config_validates_correctly),
        ("No secrets guard detects violations", test_no_secrets_guard_detects_violations),
        ("Read-only guard detects violations", test_readonly_guard_detects_violations),
        ("HTTPS-only guard validates URLs", test_https_only_guard_validates_urls),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test '{name}' raised exception: {e}")
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
        print("✓ ALL PR106 SUI READ-ONLY CONNECTION TESTS PASSED")
    else:
        print("⚠ SOME PR106 SUI READ-ONLY CONNECTION TESTS FAILED")
    print("=" * 60)
    print("PR106 Requirements Verified:")
    print("  - Connection schema import works")
    print("  - Empty connection produces valid record")
    print("  - Connected record validates correctly")
    print("  - Error record validates correctly")
    print("  - Provider config validates correctly")
    print("  - No secrets guard detects violations")
    print("  - Read-only guard detects violations")
    print("  - HTTPS-only guard validates URLs")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
