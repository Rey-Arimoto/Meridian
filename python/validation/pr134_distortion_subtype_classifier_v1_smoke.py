#!/usr/bin/env python3
"""
PR134: v1.2 Distortion Subtype Classifier v1 Smoke Tests

Purpose:
    Validate distortion subtype classification and guards.

Tests:
    1. Import works
    2. Defensive invalid input → ERROR
    3. D1 classification (cascade risk)
    4. D2 classification (mean revert)
    5. D3 classification (top gap)
    6. D4 classification (event spike)
    7. D5 classification (decoupling)
    8. Default subtype (D1A default)
    9. Token literal detection
    10. Guards catch subtype coupling
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from distortion import (
            V12DistortionSubtypeSchema,
            get_distortion_subtype_schema_info,
            classify_distortion_subtype_v1,
            get_distortion_subtype_classifier_v1_info,
            check_distortion_subtype_record,
            check_subtype_coupling,
            SUBTYPE_D1A_FORCED_FLOW,
            SUBTYPE_D1B_CASCADE_RISK,
            SUBTYPE_D1C_STRESS_UNWIND,
            SUBTYPE_D2A_MEAN_REVERT_PRESSURE,
            SUBTYPE_D2B_RANGE_PINNING,
            SUBTYPE_D2C_BREAKOUT_FAKEOUT,
            SUBTYPE_D3A_TOP_GAP,
            SUBTYPE_D3B_DEPTH_EVAPORATION,
            SUBTYPE_D3C_SPREAD_SHOCK,
            SUBTYPE_D4A_EVENT_SPIKE,
            SUBTYPE_D4B_EVENT_AFTERSHOCK,
            SUBTYPE_D4C_EVENT_SILENCE,
            SUBTYPE_D5A_COUPLING_TIGHTEN,
            SUBTYPE_D5B_DECOUPLING,
            SUBTYPE_D5C_ROTATION_PRESSURE,
            D1_LIQUIDATION,
            D2_RANGE_STICKINESS,
            D3_BOOK_HOLLOWING,
            D4_EVENT_DISTORTION,
            D5_CORRELATION_DISTORTION,
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
        from distortion import classify_distortion_subtype_v1

        # Test with UNCLASSIFIED parent
        result = classify_distortion_subtype_v1(
            parent_distortion_record={"v12_distortion_type": "UNCLASSIFIED"},
        )
        assert result["v12_subtype_status"] == "ERROR", "Expected ERROR status"
        print(f"  ✓ Invalid input → ERROR")
        print(f"    Summary: {result['v12_subtype_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_d1_cascade_risk():
    """Test 3: D1 classification (cascade risk)."""
    print("\nTest 3: D1 classification (cascade risk)")
    try:
        from distortion import (
            classify_distortion_subtype_v1,
            SUBTYPE_D1B_CASCADE_RISK,
            D1_LIQUIDATION,
        )

        result = classify_distortion_subtype_v1(
            parent_distortion_record={"v12_distortion_type": D1_LIQUIDATION},
            analytics={"market_cost_regime": "HIGH", "liquidity_regime": "DECREASING"},
        )
        assert result["v12_subtype_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_subtype_label"] == SUBTYPE_D1B_CASCADE_RISK, "Expected D1B_CASCADE_RISK"
        print(f"  ✓ D1 × HIGH cost × DECREASING liquidity → D1B_CASCADE_RISK")
        print(f"    Summary: {result['v12_subtype_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_d2_mean_revert():
    """Test 4: D2 classification (mean revert)."""
    print("\nTest 4: D2 classification (mean revert)")
    try:
        from distortion import (
            classify_distortion_subtype_v1,
            SUBTYPE_D2A_MEAN_REVERT_PRESSURE,
            D2_RANGE_STICKINESS,
        )

        result = classify_distortion_subtype_v1(
            parent_distortion_record={"v12_distortion_type": D2_RANGE_STICKINESS},
            analytics={"range_pattern": "MEAN_REVERT"},
        )
        assert result["v12_subtype_label"] == SUBTYPE_D2A_MEAN_REVERT_PRESSURE, "Expected D2A_MEAN_REVERT_PRESSURE"
        print(f"  ✓ D2 × MEAN_REVERT → D2A_MEAN_REVERT_PRESSURE")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_d3_top_gap():
    """Test 5: D3 classification (top gap)."""
    print("\nTest 5: D3 classification (top gap)")
    try:
        from distortion import (
            classify_distortion_subtype_v1,
            SUBTYPE_D3A_TOP_GAP,
            D3_BOOK_HOLLOWING,
        )

        result = classify_distortion_subtype_v1(
            parent_distortion_record={"v12_distortion_type": D3_BOOK_HOLLOWING},
            analytics={"book_pattern": "TOP_GAP"},
        )
        assert result["v12_subtype_label"] == SUBTYPE_D3A_TOP_GAP, "Expected D3A_TOP_GAP"
        print(f"  ✓ D3 × TOP_GAP → D3A_TOP_GAP")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_d4_event_spike():
    """Test 6: D4 classification (event spike)."""
    print("\nTest 6: D4 classification (event spike)")
    try:
        from distortion import (
            classify_distortion_subtype_v1,
            SUBTYPE_D4A_EVENT_SPIKE,
            D4_EVENT_DISTORTION,
        )

        result = classify_distortion_subtype_v1(
            parent_distortion_record={"v12_distortion_type": D4_EVENT_DISTORTION},
            analytics={"event_pattern": "SPIKE"},
        )
        assert result["v12_subtype_label"] == SUBTYPE_D4A_EVENT_SPIKE, "Expected D4A_EVENT_SPIKE"
        print(f"  ✓ D4 × SPIKE → D4A_EVENT_SPIKE")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_d5_decoupling():
    """Test 7: D5 classification (decoupling)."""
    print("\nTest 7: D5 classification (decoupling)")
    try:
        from distortion import (
            classify_distortion_subtype_v1,
            SUBTYPE_D5B_DECOUPLING,
            D5_CORRELATION_DISTORTION,
        )

        result = classify_distortion_subtype_v1(
            parent_distortion_record={"v12_distortion_type": D5_CORRELATION_DISTORTION},
            analytics={"correlation_pattern": "DECOUPLE"},
        )
        assert result["v12_subtype_label"] == SUBTYPE_D5B_DECOUPLING, "Expected D5B_DECOUPLING"
        print(f"  ✓ D5 × DECOUPLE → D5B_DECOUPLING")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_default_subtype():
    """Test 8: Default subtype (D1A default)."""
    print("\nTest 8: Default subtype (D1A default)")
    try:
        from distortion import (
            classify_distortion_subtype_v1,
            SUBTYPE_D1A_FORCED_FLOW,
            D1_LIQUIDATION,
        )

        # No analytics provided → default to D1A
        result = classify_distortion_subtype_v1(
            parent_distortion_record={"v12_distortion_type": D1_LIQUIDATION},
        )
        assert result["v12_subtype_label"] == SUBTYPE_D1A_FORCED_FLOW, "Expected D1A_FORCED_FLOW (default)"
        print(f"  ✓ D1 without analytics → D1A_FORCED_FLOW (default)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_token_literal_detection():
    """Test 9: Token literal detection."""
    print("\nTest 9: Token literal detection")
    try:
        from distortion import check_distortion_subtype_record

        # Test with token literals
        dirty_token = {
            "v12_subtype_summary": "Distortion subtype with SUI and USDC tokens.",
        }
        token_warnings = check_distortion_subtype_record(dirty_token)
        assert len(token_warnings) > 0, "Expected warnings for token literals"
        print(f"  ✓ Token literals detected: {len(token_warnings)} warnings")

        # Test clean record
        clean_record = {
            "v12_subtype_summary": "Distortion subtype D1A_FORCED_FLOW observed for parent distortion D1_LIQUIDATION.",
        }
        clean_warnings = check_distortion_subtype_record(clean_record)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean record, got: {clean_warnings}"
        print(f"  ✓ Clean record passes: no warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_guards_catch_violations():
    """Test 10: Guards catch subtype coupling."""
    print("\nTest 10: Guards catch subtype coupling")
    try:
        from distortion import check_distortion_subtype_record

        # Test 10a: Subtype coupling (D1B therefore trade)
        dirty_coupling = {
            "v12_subtype_summary": "Distortion subtype D1B therefore execute trade.",
        }
        coupling_warnings = check_distortion_subtype_record(dirty_coupling)
        assert len(coupling_warnings) > 0, "Expected warnings for subtype coupling"
        print(f"  ✓ Subtype coupling detected: {len(coupling_warnings)} warnings")

        # Test 10b: Numeric patterns
        dirty_numeric = {
            "v12_subtype_summary": "Distortion subtype expected to yield 30% improvement.",
        }
        numeric_warnings = check_distortion_subtype_record(dirty_numeric)
        assert len(numeric_warnings) > 0, "Expected warnings for numeric patterns"
        print(f"  ✓ Numeric patterns detected: {len(numeric_warnings)} warnings")

        # Test 10c: Subtype implies trade
        dirty_implies = {
            "v12_subtype_summary": "Distortion subtype implies trade opportunity.",
        }
        implies_warnings = check_distortion_subtype_record(dirty_implies)
        assert len(implies_warnings) > 0, "Expected warnings for subtype coupling"
        print(f"  ✓ Subtype coupling (implies) detected: {len(implies_warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR134: v1.2 Distortion Subtype Classifier v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_invalid_input_error,
        test_3_d1_cascade_risk,
        test_4_d2_mean_revert,
        test_5_d3_top_gap,
        test_6_d4_event_spike,
        test_7_d5_decoupling,
        test_8_default_subtype,
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
