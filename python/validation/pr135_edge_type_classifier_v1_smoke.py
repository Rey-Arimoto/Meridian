#!/usr/bin/env python3
"""
PR135: v1.2 Edge Type Classification Engine v1 Smoke Tests

Purpose:
    Validate edge type classification and guards.

Tests:
    1. Import works
    2. Defensive invalid input → EDGE_NEUTRAL
    3. MEDIUM + VOLATILITY + D1 → EDGE_AMPLIFY
    4. CRITICAL → EDGE_SHIELD
    5. HIGH + LIQUIDITY + D3 → EDGE_LEAK
    6. LOW → EDGE_NEUTRAL
    7. STABILITY + D1 → EDGE_SHIELD
    8. GAS_ROLE → EDGE_SHIELD
    9. Token literal detection
    10. Guards catch edge coupling
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from edge import (
            V12EdgeTypeSchema,
            get_edge_type_schema_info,
            classify_edge_type_v1,
            get_edge_type_classifier_v1_info,
            check_edge_type_record,
            check_edge_coupling,
            EDGE_NONE,
            EDGE_AMPLIFY,
            EDGE_SHIELD,
            EDGE_LEAK,
            EDGE_NEUTRAL,
            VALID_EDGE_TYPES,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_defensive_invalid_input():
    """Test 2: Defensive invalid input → EDGE_NEUTRAL."""
    print("\nTest 2: Defensive invalid input → EDGE_NEUTRAL")
    try:
        from edge import classify_edge_type_v1, EDGE_NEUTRAL

        # Test with UNCLASSIFIED inputs (defensive)
        result = classify_edge_type_v1(
            regime_record={"v11_regime_level": "UNCLASSIFIED"},
        )
        assert result["v12_edge_type"] == EDGE_NEUTRAL, "Expected EDGE_NEUTRAL (defensive)"
        print(f"  ✓ Invalid input → EDGE_NEUTRAL (defensive)")
        print(f"    Summary: {result['v12_edge_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_medium_volatility_d1_amplify():
    """Test 3: MEDIUM + VOLATILITY + D1 → EDGE_AMPLIFY."""
    print("\nTest 3: MEDIUM + VOLATILITY + D1 → EDGE_AMPLIFY")
    try:
        from edge import classify_edge_type_v1, EDGE_AMPLIFY

        result = classify_edge_type_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "VOLATILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        )
        assert result["v12_edge_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_edge_type"] == EDGE_AMPLIFY, "Expected EDGE_AMPLIFY"
        print(f"  ✓ MEDIUM × VOLATILITY × D1 → EDGE_AMPLIFY")
        print(f"    Summary: {result['v12_edge_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_critical_shield():
    """Test 4: CRITICAL → EDGE_SHIELD."""
    print("\nTest 4: CRITICAL → EDGE_SHIELD")
    try:
        from edge import classify_edge_type_v1, EDGE_SHIELD

        result = classify_edge_type_v1(
            regime_record={"v11_regime_level": "REGIME_CRITICAL"},
            role_record={"v12_role_carrier_role_type": "VOLATILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        )
        assert result["v12_edge_type"] == EDGE_SHIELD, "Expected EDGE_SHIELD"
        print(f"  ✓ REGIME_CRITICAL → EDGE_SHIELD")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_high_liquidity_d3_leak():
    """Test 5: HIGH + LIQUIDITY + D3 → EDGE_LEAK."""
    print("\nTest 5: HIGH + LIQUIDITY + D3 → EDGE_LEAK")
    try:
        from edge import classify_edge_type_v1, EDGE_LEAK

        result = classify_edge_type_v1(
            regime_record={"v11_regime_level": "REGIME_HIGH"},
            role_record={"v12_role_carrier_role_type": "LIQUIDITY_ROLE"},
            distortion_record={"v12_distortion_type": "D3_BOOK_HOLLOWING"},
        )
        assert result["v12_edge_type"] == EDGE_LEAK, "Expected EDGE_LEAK"
        print(f"  ✓ HIGH × LIQUIDITY × D3 → EDGE_LEAK")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_low_neutral():
    """Test 6: LOW → EDGE_NEUTRAL."""
    print("\nTest 6: LOW → EDGE_NEUTRAL")
    try:
        from edge import classify_edge_type_v1, EDGE_NEUTRAL

        result = classify_edge_type_v1(
            regime_record={"v11_regime_level": "REGIME_LOW"},
            role_record={"v12_role_carrier_role_type": "VOLATILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        )
        assert result["v12_edge_type"] == EDGE_NEUTRAL, "Expected EDGE_NEUTRAL"
        print(f"  ✓ REGIME_LOW → EDGE_NEUTRAL")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_stability_d1_shield():
    """Test 7: STABILITY + D1 → EDGE_SHIELD."""
    print("\nTest 7: STABILITY + D1 → EDGE_SHIELD")
    try:
        from edge import classify_edge_type_v1, EDGE_SHIELD

        result = classify_edge_type_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        )
        assert result["v12_edge_type"] == EDGE_SHIELD, "Expected EDGE_SHIELD"
        print(f"  ✓ STABILITY × D1 → EDGE_SHIELD")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_gas_role_shield():
    """Test 8: GAS_ROLE → EDGE_SHIELD."""
    print("\nTest 8: GAS_ROLE → EDGE_SHIELD")
    try:
        from edge import classify_edge_type_v1, EDGE_SHIELD

        result = classify_edge_type_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "GAS_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        )
        assert result["v12_edge_type"] == EDGE_SHIELD, "Expected EDGE_SHIELD"
        print(f"  ✓ GAS_ROLE → EDGE_SHIELD")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_token_literal_detection():
    """Test 9: Token literal detection."""
    print("\nTest 9: Token literal detection")
    try:
        from edge import check_edge_type_record

        # Test with token literals
        dirty_token = {
            "v12_edge_summary": "Edge type with SUI and USDC tokens.",
        }
        token_warnings = check_edge_type_record(dirty_token)
        assert len(token_warnings) > 0, "Expected warnings for token literals"
        print(f"  ✓ Token literals detected: {len(token_warnings)} warnings")

        # Test clean record
        clean_record = {
            "v12_edge_summary": "Edge type EDGE_AMPLIFY may indicate structural pattern for REGIME_MEDIUM × VOLATILITY_ROLE × D1_LIQUIDATION.",
        }
        clean_warnings = check_edge_type_record(clean_record)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean record, got: {clean_warnings}"
        print(f"  ✓ Clean record passes: no warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_guards_catch_violations():
    """Test 10: Guards catch edge coupling."""
    print("\nTest 10: Guards catch edge coupling")
    try:
        from edge import check_edge_type_record

        # Test 10a: Edge coupling (EDGE_AMPLIFY therefore trade)
        dirty_coupling = {
            "v12_edge_summary": "Edge type EDGE_AMPLIFY therefore execute trade.",
        }
        coupling_warnings = check_edge_type_record(dirty_coupling)
        assert len(coupling_warnings) > 0, "Expected warnings for edge coupling"
        print(f"  ✓ Edge coupling detected: {len(coupling_warnings)} warnings")

        # Test 10b: Numeric patterns
        dirty_numeric = {
            "v12_edge_summary": "Edge type expected to yield 30% improvement.",
        }
        numeric_warnings = check_edge_type_record(dirty_numeric)
        assert len(numeric_warnings) > 0, "Expected warnings for numeric patterns"
        print(f"  ✓ Numeric patterns detected: {len(numeric_warnings)} warnings")

        # Test 10c: EDGE_SHIELD so stop
        dirty_shield = {
            "v12_edge_summary": "Edge type EDGE_SHIELD so stop trading.",
        }
        shield_warnings = check_edge_type_record(dirty_shield)
        assert len(shield_warnings) > 0, "Expected warnings for edge coupling"
        print(f"  ✓ Edge coupling (shield so stop) detected: {len(shield_warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR135: v1.2 Edge Type Classification Engine v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_defensive_invalid_input,
        test_3_medium_volatility_d1_amplify,
        test_4_critical_shield,
        test_5_high_liquidity_d3_leak,
        test_6_low_neutral,
        test_7_stability_d1_shield,
        test_8_gas_role_shield,
        test_9_token_literal_detection,
        test_10_guards_catch_violations,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)

    if all(results):
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
