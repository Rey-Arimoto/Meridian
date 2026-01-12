#!/usr/bin/env python3
"""
PR133: v1.2 Role Rescue Relation v1 Smoke Tests

Purpose:
    Validate role rescue relation classification and guards.

Tests:
    1. Import works
    2. Defensive invalid input → ERROR
    3. REGIME_CRITICAL → NONE
    4. Hard boundary → NONE
    5. SUPPRESSED → NONE
    6. INELIGIBLE → NONE
    7. REGIME_MEDIUM + STABILITY→VOLATILITY + D1 → BUFFER MODERATE
    8. REGIME_HIGH cap → WEAK
    9. REGIME_MEDIUM + GAS→VOLATILITY → CONTINUITY WEAK
    10. Guards catch rescue coupling
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from rescue import (
            V12RoleRescueRelationSchema,
            get_rescue_relation_schema_info,
            classify_role_rescue_relation_v1,
            get_role_rescue_relation_engine_v1_info,
            check_rescue_relation_record,
            check_rescue_coupling,
            RESCUE_EDGE_BUFFER,
            RESCUE_EDGE_ANCHOR,
            RESCUE_EDGE_CONTINUITY,
            RESCUE_EDGE_DAMPEN,
            RESCUE_EDGE_UNCLASSIFIED,
            RESCUE_STRENGTH_NONE,
            RESCUE_STRENGTH_WEAK,
            RESCUE_STRENGTH_MODERATE,
            RESCUE_STRENGTH_STRONG,
            ROLE_GAS,
            ROLE_STABILITY,
            ROLE_LIQUIDITY,
            ROLE_VOLATILITY,
            ROLE_HEDGE,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_invalid_input_error():
    """Test 2: Defensive invalid input → ERROR."""
    print("\nTest 2: Defensive invalid input → ERROR")
    try:
        from rescue import classify_role_rescue_relation_v1, ROLE_STABILITY, ROLE_VOLATILITY

        # Test with UNCLASSIFIED regime
        result = classify_role_rescue_relation_v1(
            regime_record={"v11_regime_level": "UNCLASSIFIED"},
            role_from=ROLE_STABILITY,
            role_to=ROLE_VOLATILITY,
        )
        assert result["v12_rescue_status"] == "ERROR", "Expected ERROR status"
        print(f"  ✓ Invalid input → ERROR")
        print(f"    Summary: {result['v12_rescue_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_regime_critical_none():
    """Test 3: REGIME_CRITICAL → NONE."""
    print("\nTest 3: REGIME_CRITICAL → NONE")
    try:
        from rescue import classify_role_rescue_relation_v1, RESCUE_STRENGTH_NONE, ROLE_STABILITY, ROLE_VOLATILITY

        result = classify_role_rescue_relation_v1(
            regime_record={"v11_regime_level": "REGIME_CRITICAL"},
            role_from=ROLE_STABILITY,
            role_to=ROLE_VOLATILITY,
        )
        assert result["v12_rescue_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_rescue_strength"] == RESCUE_STRENGTH_NONE, "Expected NONE strength"
        print(f"  ✓ REGIME_CRITICAL → NONE")
        print(f"    Warnings: {result.get('v12_rescue_warnings', [])}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_hard_boundary_none():
    """Test 4: Hard boundary → NONE."""
    print("\nTest 4: Hard boundary → NONE")
    try:
        from rescue import classify_role_rescue_relation_v1, RESCUE_STRENGTH_NONE, ROLE_STABILITY, ROLE_VOLATILITY

        result = classify_role_rescue_relation_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            boundary_record={"v11_boundary_type": "SCHEMA_BOUNDARY"},
            role_from=ROLE_STABILITY,
            role_to=ROLE_VOLATILITY,
        )
        assert result["v12_rescue_strength"] == RESCUE_STRENGTH_NONE, "Expected NONE strength"
        print(f"  ✓ Hard boundary → NONE")
        print(f"    Warnings: {result.get('v12_rescue_warnings', [])}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_suppressed_none():
    """Test 5: SUPPRESSED → NONE."""
    print("\nTest 5: SUPPRESSED → NONE")
    try:
        from rescue import classify_role_rescue_relation_v1, RESCUE_STRENGTH_NONE, ROLE_STABILITY, ROLE_VOLATILITY

        result = classify_role_rescue_relation_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            permission_monitor_record={"v12_monitor_suppression_state": "SUPPRESSED"},
            role_from=ROLE_STABILITY,
            role_to=ROLE_VOLATILITY,
        )
        assert result["v12_rescue_strength"] == RESCUE_STRENGTH_NONE, "Expected NONE strength"
        print(f"  ✓ SUPPRESSED → NONE")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_ineligible_none():
    """Test 6: INELIGIBLE → NONE."""
    print("\nTest 6: INELIGIBLE → NONE")
    try:
        from rescue import classify_role_rescue_relation_v1, RESCUE_STRENGTH_NONE, ROLE_STABILITY, ROLE_VOLATILITY

        result = classify_role_rescue_relation_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            eligibility_record={"v12_eligibility_status": "INELIGIBLE"},
            role_from=ROLE_STABILITY,
            role_to=ROLE_VOLATILITY,
        )
        assert result["v12_rescue_strength"] == RESCUE_STRENGTH_NONE, "Expected NONE strength"
        print(f"  ✓ INELIGIBLE → NONE")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_medium_stability_volatility_d1_buffer_moderate():
    """Test 7: MEDIUM + STABILITY→VOLATILITY + D1 → BUFFER MODERATE."""
    print("\nTest 7: MEDIUM + STABILITY→VOLATILITY + D1 → BUFFER MODERATE")
    try:
        from rescue import (
            classify_role_rescue_relation_v1,
            RESCUE_EDGE_BUFFER,
            RESCUE_STRENGTH_MODERATE,
            ROLE_STABILITY,
            ROLE_VOLATILITY,
        )

        result = classify_role_rescue_relation_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
            role_from=ROLE_STABILITY,
            role_to=ROLE_VOLATILITY,
        )
        assert result["v12_rescue_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_rescue_edge_type"] == RESCUE_EDGE_BUFFER, "Expected BUFFER edge"
        assert result["v12_rescue_strength"] == RESCUE_STRENGTH_MODERATE, "Expected MODERATE strength"
        print(f"  ✓ MEDIUM × STABILITY→VOLATILITY × D1 → BUFFER MODERATE")
        print(f"    Summary: {result['v12_rescue_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_high_cap_weak():
    """Test 8: REGIME_HIGH cap → WEAK."""
    print("\nTest 8: REGIME_HIGH cap → WEAK")
    try:
        from rescue import classify_role_rescue_relation_v1, RESCUE_STRENGTH_WEAK, ROLE_STABILITY, ROLE_VOLATILITY

        result = classify_role_rescue_relation_v1(
            regime_record={"v11_regime_level": "REGIME_HIGH"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
            role_from=ROLE_STABILITY,
            role_to=ROLE_VOLATILITY,
        )
        assert result["v12_rescue_strength"] == RESCUE_STRENGTH_WEAK, "Expected WEAK strength (capped)"
        print(f"  ✓ REGIME_HIGH → max WEAK")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_gas_volatility_continuity_weak():
    """Test 9: MEDIUM + GAS→VOLATILITY → CONTINUITY WEAK."""
    print("\nTest 9: MEDIUM + GAS→VOLATILITY → CONTINUITY WEAK")
    try:
        from rescue import (
            classify_role_rescue_relation_v1,
            RESCUE_EDGE_CONTINUITY,
            RESCUE_STRENGTH_WEAK,
            ROLE_GAS,
            ROLE_VOLATILITY,
        )

        result = classify_role_rescue_relation_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
            role_from=ROLE_GAS,
            role_to=ROLE_VOLATILITY,
        )
        assert result["v12_rescue_edge_type"] == RESCUE_EDGE_CONTINUITY, "Expected CONTINUITY edge"
        assert result["v12_rescue_strength"] == RESCUE_STRENGTH_WEAK, "Expected WEAK strength"
        print(f"  ✓ GAS→VOLATILITY → CONTINUITY WEAK")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_guards_catch_violations():
    """Test 10: Guards catch rescue coupling."""
    print("\nTest 10: Guards catch rescue coupling")
    try:
        from rescue import check_rescue_relation_record

        # Test 10a: Rescue coupling (buffer therefore trade)
        dirty_coupling = {
            "v12_rescue_summary": "Role rescue relation buffer therefore execute trade.",
        }
        coupling_warnings = check_rescue_relation_record(dirty_coupling)
        assert len(coupling_warnings) > 0, "Expected warnings for rescue coupling"
        print(f"  ✓ Rescue coupling detected: {len(coupling_warnings)} warnings")

        # Test 10b: Numeric patterns
        dirty_numeric = {
            "v12_rescue_summary": "Role rescue relation expected to yield 30% improvement.",
        }
        numeric_warnings = check_rescue_relation_record(dirty_numeric)
        assert len(numeric_warnings) > 0, "Expected warnings for numeric patterns"
        print(f"  ✓ Numeric patterns detected: {len(numeric_warnings)} warnings")

        # Test 10c: Token literals
        dirty_token = {
            "v12_rescue_summary": "Role rescue relation with SUI and USDC tokens.",
        }
        token_warnings = check_rescue_relation_record(dirty_token)
        assert len(token_warnings) > 0, "Expected warnings for token literals"
        print(f"  ✓ Token literals detected: {len(token_warnings)} warnings")

        # Test clean record
        clean_record = {
            "v12_rescue_summary": "Role rescue relation from STABILITY_ROLE to VOLATILITY_ROLE may provide edge type BUFFER with strength MODERATE.",
        }
        clean_warnings = check_rescue_relation_record(clean_record)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean record, got: {clean_warnings}"
        print(f"  ✓ Clean record passes: no warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR133: v1.2 Role Rescue Relation v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_invalid_input_error,
        test_3_regime_critical_none,
        test_4_hard_boundary_none,
        test_5_suppressed_none,
        test_6_ineligible_none,
        test_7_medium_stability_volatility_d1_buffer_moderate,
        test_8_high_cap_weak,
        test_9_gas_volatility_continuity_weak,
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
