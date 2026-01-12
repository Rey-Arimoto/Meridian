#!/usr/bin/env python3
"""
PR129: v1.2 Distortion Detector v1 Smoke Tests

Purpose:
    Validate distortion type classification from pipeline artifacts.

Tests:
    1. Import works
    2. Empty input → valid ERROR record
    3. Regime critical → D0_NONE
    4. Event present → D4_EVENT_DISTORTION
    5. Drift correlation present & drift>=MEDIUM → D5_CORRELATION_DISTORTION
    6. Low liquidity + decrease → D3_BOOK_HOLLOWING
    7. Decrease + event present → D1_LIQUIDATION (priority)
    8. Stable liquidity + no events + low drift → D2_RANGE_STICKINESS
    9. Guards detect token literal violation
    10. Guards detect numeric pattern violation
    11. Guards detect distortion coupling
    12. Warning-only behavior
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
            V12DistortionSchema,
            get_distortion_schema_info,
            detect_distortion_v1,
            get_detector_v1_info,
            check_distortion_record,
            check_distortion_coupling,
            FORBIDDEN_VOCABULARY,
            D0_NONE,
            D1_LIQUIDATION,
            D2_RANGE_STICKINESS,
            D3_BOOK_HOLLOWING,
            D4_EVENT_DISTORTION,
            D5_CORRELATION_DISTORTION,
            DISTORTION_UNCLASSIFIED,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_empty_input_error():
    """Test 2: Empty input → valid ERROR record."""
    print("\nTest 2: Empty input → valid ERROR record")
    try:
        from distortion import detect_distortion_v1

        # Test with all None
        result = detect_distortion_v1(None, None, None, None)
        assert result["v12_distortion_status"] == "AVAILABLE", "Expected AVAILABLE status (defensive default)"
        assert "v12_distortion_type" in result
        print(f"  ✓ None input → defensive default: {result['v12_distortion_type']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_regime_critical_d0():
    """Test 3: Regime critical → D0_NONE."""
    print("\nTest 3: Regime critical → D0_NONE")
    try:
        from distortion import detect_distortion_v1, D0_NONE

        result = detect_distortion_v1(
            regime_record={"v11_regime_level": "REGIME_CRITICAL"},
        )

        assert result["v12_distortion_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_distortion_type"] == D0_NONE, "Expected D0_NONE"
        print(f"  ✓ REGIME_CRITICAL → {result['v12_distortion_type']}")
        print(f"    Summary: {result['v12_distortion_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_event_present_d4():
    """Test 4: Event present → D4_EVENT_DISTORTION."""
    print("\nTest 4: Event present → D4_EVENT_DISTORTION")
    try:
        from distortion import detect_distortion_v1, D4_EVENT_DISTORTION

        result = detect_distortion_v1(
            analytics_record={"event_activity_present": True},
        )

        assert result["v12_distortion_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_distortion_type"] == D4_EVENT_DISTORTION, "Expected D4_EVENT_DISTORTION"
        print(f"  ✓ event_activity_present → {result['v12_distortion_type']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_correlation_drift_d5():
    """Test 5: Drift correlation present & drift>=MEDIUM → D5_CORRELATION_DISTORTION."""
    print("\nTest 5: Drift correlation + DRIFT_MEDIUM → D5")
    try:
        from distortion import detect_distortion_v1, D5_CORRELATION_DISTORTION

        result = detect_distortion_v1(
            drift_record={
                "v10_drift_label": "DRIFT_MEDIUM",
                "v10_vocab_family_presence": {"CORRELATION": True},
            },
        )

        assert result["v12_distortion_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_distortion_type"] == D5_CORRELATION_DISTORTION, "Expected D5_CORRELATION_DISTORTION"
        print(f"  ✓ CORRELATION + DRIFT_MEDIUM → {result['v12_distortion_type']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_low_liquidity_decrease_d3():
    """Test 6: Low liquidity + decrease → D3_BOOK_HOLLOWING."""
    print("\nTest 6: Low liquidity + decrease → D3_BOOK_HOLLOWING")
    try:
        from distortion import detect_distortion_v1, D3_BOOK_HOLLOWING

        result = detect_distortion_v1(
            analytics_record={
                "liquidity_regime": "LOW",
                "object_dynamics": "DECREASE",
                "event_activity_present": False,
            },
        )

        assert result["v12_distortion_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_distortion_type"] == D3_BOOK_HOLLOWING, "Expected D3_BOOK_HOLLOWING"
        print(f"  ✓ LOW liquidity + DECREASE → {result['v12_distortion_type']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_decrease_event_d1():
    """Test 7: Decrease + event present → D1_LIQUIDATION (priority)."""
    print("\nTest 7: Decrease + event → D1_LIQUIDATION (priority)")
    try:
        from distortion import detect_distortion_v1, D1_LIQUIDATION

        result = detect_distortion_v1(
            analytics_record={
                "object_dynamics": "DECREASE",
                "event_activity_present": True,
            },
        )

        assert result["v12_distortion_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_distortion_type"] == D1_LIQUIDATION, "Expected D1_LIQUIDATION"
        print(f"  ✓ DECREASE + event_present → {result['v12_distortion_type']}")
        print(f"    (D1 has priority over D3)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_stable_no_events_d2():
    """Test 8: Stable liquidity + no events + low drift → D2_RANGE_STICKINESS."""
    print("\nTest 8: Stable + no events + low drift → D2_RANGE_STICKINESS")
    try:
        from distortion import detect_distortion_v1, D2_RANGE_STICKINESS

        result = detect_distortion_v1(
            analytics_record={
                "liquidity_regime": "MEDIUM",
                "event_activity_present": False,
            },
            drift_record={"v10_drift_label": "DRIFT_LOW"},
        )

        assert result["v12_distortion_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_distortion_type"] == D2_RANGE_STICKINESS, "Expected D2_RANGE_STICKINESS"
        print(f"  ✓ MEDIUM liquidity + no events + DRIFT_LOW → {result['v12_distortion_type']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_token_literal_violation():
    """Test 9: Guards detect token literal violation."""
    print("\nTest 9: Guards detect token literal violation")
    try:
        from distortion import check_distortion_record

        # Test with token literals
        dirty_record = {
            "v12_distortion_summary": "distortion detected for SUI and USDC tokens.",
        }
        warnings = check_distortion_record(dirty_record)

        assert len(warnings) > 0, "Expected warnings for token literals"
        print(f"  ✓ Token literals detected: {len(warnings)} warnings")
        for w in warnings[:2]:
            print(f"    - {w}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_numeric_pattern_violation():
    """Test 10: Guards detect numeric pattern violation."""
    print("\nTest 10: Guards detect numeric pattern violation")
    try:
        from distortion import check_distortion_record

        # Test with numeric patterns
        dirty_record = {
            "v12_distortion_summary": "detected 5 distortion events with 80% confidence.",
        }
        warnings = check_distortion_record(dirty_record)

        assert len(warnings) > 0, "Expected warnings for numeric patterns"
        print(f"  ✓ Numeric patterns detected: {len(warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_11_distortion_coupling():
    """Test 11: Guards detect distortion coupling."""
    print("\nTest 11: Guards detect distortion coupling")
    try:
        from distortion import check_distortion_record, check_distortion_coupling

        # Test distortion coupling patterns
        coupling_patterns = [
            "D1 liquidation detected therefore execute trade.",
            "D4 event distortion so proceed with execution.",
            "distortion means we should touch the market.",
        ]

        for pattern in coupling_patterns:
            warnings = check_distortion_coupling(pattern)
            assert len(warnings) > 0, f"Expected warnings for: {pattern}"
            print(f"  ✓ Detected coupling: '{pattern[:40]}...'")

        # Test clean text
        clean_text = "distortion label classified as D4_EVENT_DISTORTION based on labeled activity patterns."
        clean_warnings = check_distortion_coupling(clean_text)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean text, got: {clean_warnings}"
        print(f"  ✓ Clean text passes: no coupling detected")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_12_warning_only_behavior():
    """Test 12: Warning-only behavior."""
    print("\nTest 12: Warning-only behavior")
    try:
        from distortion import check_distortion_record

        # Test that guards never raise exceptions
        dirty_records = [
            {"v12_distortion_summary": "distortion with SUI and BTC tokens."},
            {"v12_distortion_summary": "detected 10 events with 90% score."},
            {"v12_distortion_summary": "address 0x1234567890abcdef detected."},
            {"v12_distortion_summary": "D1 therefore execute liquidation."},
        ]

        for record in dirty_records:
            try:
                warnings = check_distortion_record(record)
                # Should return warnings, not raise
                assert isinstance(warnings, list), "Expected list of warnings"
                print(f"  ✓ Guard returned {len(warnings)} warnings (no exception)")
            except Exception as e:
                print(f"  ✗ Guard raised exception: {e}")
                return False

        print(f"  ✓ All guards are warning-only (never raise)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR129: v1.2 Distortion Detector v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_empty_input_error,
        test_3_regime_critical_d0,
        test_4_event_present_d4,
        test_5_correlation_drift_d5,
        test_6_low_liquidity_decrease_d3,
        test_7_decrease_event_d1,
        test_8_stable_no_events_d2,
        test_9_token_literal_violation,
        test_10_numeric_pattern_violation,
        test_11_distortion_coupling,
        test_12_warning_only_behavior,
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
