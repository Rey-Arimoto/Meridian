#!/usr/bin/env python3
"""
PR131: v1.2 Role × Distortion × Regime Contribution Model v1 Smoke Tests

Purpose:
    Validate contribution model classification and guards.

Tests:
    1. Import works
    2. Defensive invalid input → ERROR + CONTRIB_UNKNOWN
    3. REGIME_CRITICAL → CONTRIB_STRONGLY_NEGATIVE
    4. INELIGIBLE eligibility → CONTRIB_NEUTRAL
    5. REGIME_MEDIUM × VOLATILITY × D1 with ELIGIBLE_CONSIDERATION_ONLY → CONTRIB_STRONGLY_POSITIVE
    6. REGIME_LOW any → CONTRIB_NEUTRAL
    7. REGIME_HIGH default → CONTRIB_NEGATIVE or CONTRIB_NEUTRAL per rule
    8. build_contribution_cube returns deterministic non-empty results
    9. Guard detects digits in summary
    10. Guard detects token literal in rationale and returns warning (not exception)
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from contribution import (
            V12ContributionSchema,
            get_contribution_schema_info,
            classify_contribution_v1,
            build_contribution_cube_v1,
            contribution_to_explain_signals_v1,
            get_contribution_engine_v1_info,
            check_contribution_record,
            check_contribution_numeric_patterns,
            check_guarantee_language,
            check_contribution_coupling,
            CONTRIB_STRONGLY_POSITIVE,
            CONTRIB_POSITIVE,
            CONTRIB_NEUTRAL,
            CONTRIB_NEGATIVE,
            CONTRIB_STRONGLY_NEGATIVE,
            CONTRIB_UNKNOWN,
            RATIONALE_DISTORTION_CAPTURE_ZONE,
            RATIONALE_STRUCTURE_INTELLIGIBLE,
        )
        from explain.v12_explain_context_contribution_extension import (
            extend_explain_context_with_contribution_v1,
            get_contribution_extension_summary_v1,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_invalid_input_error():
    """Test 2: Defensive invalid input → ERROR + CONTRIB_UNKNOWN."""
    print("\nTest 2: Defensive invalid input → ERROR + CONTRIB_UNKNOWN")
    try:
        from contribution import classify_contribution_v1, CONTRIB_UNKNOWN

        # Test with UNCLASSIFIED inputs
        result = classify_contribution_v1("UNCLASSIFIED", "UNCLASSIFIED", "UNCLASSIFIED")
        assert result["v12_contrib_status"] == "ERROR", "Expected ERROR status"
        assert result["v12_contrib_contribution_label"] == CONTRIB_UNKNOWN, "Expected CONTRIB_UNKNOWN"
        print(f"  ✓ Invalid input → ERROR + CONTRIB_UNKNOWN")
        print(f"    Summary: {result['v12_contrib_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_regime_critical_strongly_negative():
    """Test 3: REGIME_CRITICAL → CONTRIB_STRONGLY_NEGATIVE."""
    print("\nTest 3: REGIME_CRITICAL → CONTRIB_STRONGLY_NEGATIVE")
    try:
        from contribution import classify_contribution_v1, CONTRIB_STRONGLY_NEGATIVE

        result = classify_contribution_v1("REGIME_CRITICAL", "VOLATILITY_ROLE", "D1_LIQUIDATION")
        assert result["v12_contrib_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_contrib_contribution_label"] == CONTRIB_STRONGLY_NEGATIVE, "Expected CONTRIB_STRONGLY_NEGATIVE"
        print(f"  ✓ REGIME_CRITICAL → CONTRIB_STRONGLY_NEGATIVE")
        print(f"    Rationale: {result['v12_contrib_contribution_rationale']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_ineligible_neutral():
    """Test 4: INELIGIBLE eligibility → CONTRIB_NEUTRAL."""
    print("\nTest 4: INELIGIBLE eligibility → CONTRIB_NEUTRAL")
    try:
        from contribution import classify_contribution_v1, CONTRIB_NEUTRAL

        result = classify_contribution_v1(
            "REGIME_MEDIUM",
            "VOLATILITY_ROLE",
            "D1_LIQUIDATION",
            eligibility_label="INELIGIBLE"
        )
        assert result["v12_contrib_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_contrib_contribution_label"] == CONTRIB_NEUTRAL, "Expected CONTRIB_NEUTRAL"
        print(f"  ✓ INELIGIBLE → CONTRIB_NEUTRAL")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_medium_volatility_d1_eligible_consideration_only():
    """Test 5: REGIME_MEDIUM × VOLATILITY × D1 with ELIGIBLE_CONSIDERATION_ONLY → CONTRIB_STRONGLY_POSITIVE."""
    print("\nTest 5: REGIME_MEDIUM × VOLATILITY × D1 × ELIGIBLE_CONSIDERATION_ONLY → CONTRIB_STRONGLY_POSITIVE")
    try:
        from contribution import classify_contribution_v1, CONTRIB_STRONGLY_POSITIVE

        result = classify_contribution_v1(
            "REGIME_MEDIUM",
            "VOLATILITY_ROLE",
            "D1_LIQUIDATION",
            eligibility_label="ELIGIBLE_CONSIDERATION_ONLY"
        )
        assert result["v12_contrib_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_contrib_contribution_label"] == CONTRIB_STRONGLY_POSITIVE, "Expected CONTRIB_STRONGLY_POSITIVE"
        print(f"  ✓ MEDIUM × VOLATILITY × D1 × ELIGIBLE_CONSIDERATION_ONLY → CONTRIB_STRONGLY_POSITIVE")
        print(f"    Rationale: {result['v12_contrib_contribution_rationale']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_regime_low_neutral():
    """Test 6: REGIME_LOW any → CONTRIB_NEUTRAL."""
    print("\nTest 6: REGIME_LOW any → CONTRIB_NEUTRAL")
    try:
        from contribution import classify_contribution_v1, CONTRIB_NEUTRAL

        result = classify_contribution_v1("REGIME_LOW", "VOLATILITY_ROLE", "D1_LIQUIDATION")
        assert result["v12_contrib_contribution_label"] == CONTRIB_NEUTRAL, "Expected CONTRIB_NEUTRAL"
        print(f"  ✓ REGIME_LOW → CONTRIB_NEUTRAL")
        print(f"    Rationale: {result['v12_contrib_contribution_rationale']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_regime_high_classification():
    """Test 7: REGIME_HIGH → CONTRIB_NEGATIVE or CONTRIB_NEUTRAL per rule."""
    print("\nTest 7: REGIME_HIGH → CONTRIB_NEGATIVE or CONTRIB_NEUTRAL per rule")
    try:
        from contribution import classify_contribution_v1, CONTRIB_NEGATIVE, CONTRIB_NEUTRAL

        # VOLATILITY × D1 should be NEUTRAL
        result1 = classify_contribution_v1("REGIME_HIGH", "VOLATILITY_ROLE", "D1_LIQUIDATION")
        assert result1["v12_contrib_contribution_label"] == CONTRIB_NEUTRAL, "Expected CONTRIB_NEUTRAL for VOLATILITY × D1"
        print(f"  ✓ REGIME_HIGH × VOLATILITY × D1 → CONTRIB_NEUTRAL")

        # GAS_ROLE should be NEGATIVE
        result2 = classify_contribution_v1("REGIME_HIGH", "GAS_ROLE", "D1_LIQUIDATION")
        assert result2["v12_contrib_contribution_label"] == CONTRIB_NEGATIVE, "Expected CONTRIB_NEGATIVE for GAS_ROLE"
        print(f"  ✓ REGIME_HIGH × GAS_ROLE → CONTRIB_NEGATIVE")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_build_contribution_cube():
    """Test 8: build_contribution_cube returns deterministic non-empty results."""
    print("\nTest 8: build_contribution_cube returns deterministic non-empty results")
    try:
        from contribution import build_contribution_cube_v1

        # Build small cube
        cube = build_contribution_cube_v1(
            regime_levels=["REGIME_MEDIUM", "REGIME_LOW"],
            role_types=["VOLATILITY_ROLE", "GAS_ROLE"],
            distortion_types=["D1_LIQUIDATION", "D2_RANGE_STICKINESS"],
        )

        # Check non-empty
        assert len(cube) > 0, "Expected non-empty cube"

        # Check deterministic count (2 regimes × 2 roles × 2 distortions = 8)
        expected_count = 2 * 2 * 2
        assert len(cube) == expected_count, f"Expected {expected_count} records, got {len(cube)}"

        # Check all records are valid
        for record in cube:
            assert "v12_contrib_contribution_label" in record, "Expected contribution_label in record"

        print(f"  ✓ Cube generated {len(cube)} records (deterministic)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_guard_detects_digits():
    """Test 9: Guard detects digits in summary."""
    print("\nTest 9: Guard detects digits in summary")
    try:
        from contribution import check_contribution_record

        # Test with digits
        dirty_record = {
            "v12_contrib_summary": "contribution expected to yield 30% annual return with 2 year horizon.",
        }
        warnings = check_contribution_record(dirty_record)

        assert len(warnings) > 0, "Expected warnings for numeric patterns"
        print(f"  ✓ Numeric patterns detected: {len(warnings)} warnings")
        for w in warnings[:3]:
            print(f"    - {w}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_guard_token_literal_warning_only():
    """Test 10: Guard detects token literal in rationale and returns warning (not exception)."""
    print("\nTest 10: Guard detects token literal in rationale and returns warning (not exception)")
    try:
        from contribution import check_contribution_record

        # Test with token literals in rationale (use spaces not underscores for word boundary matching)
        dirty_record = {
            "v12_contrib_summary": "contribution labeled positive.",
            "v12_contrib_contribution_rationale": ["SUI premium zone", "USDC stability buffer"],
        }

        try:
            warnings = check_contribution_record(dirty_record)
            # Should return warnings, not raise
            assert isinstance(warnings, list), "Expected list of warnings"
            assert len(warnings) > 0, f"Expected warnings for token literals, got {len(warnings)}: {warnings}"
            print(f"  ✓ Token literals detected: {len(warnings)} warnings (no exception)")
            for w in warnings[:2]:
                print(f"    - {w}")
        except Exception as e:
            print(f"  ✗ Guard raised exception: {e}")
            return False

        # Test clean rationale
        clean_record = {
            "v12_contrib_summary": "contribution labeled positive.",
            "v12_contrib_contribution_rationale": ["DISTORTION_CAPTURE_ZONE", "STRUCTURE_INTELLIGIBLE"],
        }
        clean_warnings = check_contribution_record(clean_record)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean record, got: {clean_warnings}"
        print(f"  ✓ Clean rationale passes: no warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR131: v1.2 Contribution Model v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_invalid_input_error,
        test_3_regime_critical_strongly_negative,
        test_4_ineligible_neutral,
        test_5_medium_volatility_d1_eligible_consideration_only,
        test_6_regime_low_neutral,
        test_7_regime_high_classification,
        test_8_build_contribution_cube,
        test_9_guard_detects_digits,
        test_10_guard_token_literal_warning_only,
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
