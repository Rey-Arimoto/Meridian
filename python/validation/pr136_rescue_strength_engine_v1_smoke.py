#!/usr/bin/env python3
"""
PR136: v1.2 Rescue Strength Classification Engine v1 Smoke Tests

Purpose:
    Validate rescue strength classification and guards.

Tests:
    1. Import works
    2. Defensive invalid input → RESCUE_NONE
    3. REGIME_CRITICAL → RESCUE_NONE
    4. INELIGIBLE → RESCUE_NONE
    5. EDGE_LEAK → RESCUE_NONE
    6. STRONG strict case with ALLOW_RESCUE_STRONG
    7. No STRONG for VOLATILITY_ROLE or EDGE_AMPLIFY
    8. ELIGIBLE_DRY_RUN_ONLY caps to WEAK
    9. Coupling detection
    10. Warning-only behavior
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
            V12RescueStrengthSchema,
            get_rescue_strength_schema_info,
            classify_rescue_strength_v1,
            get_rescue_strength_engine_v1_info,
            check_rescue_strength_record,
            check_rescue_coupling,
            RESCUE_NONE,
            RESCUE_WEAK,
            RESCUE_MEDIUM,
            RESCUE_STRONG,
            VALID_RESCUE_STRENGTHS,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_defensive_invalid_input():
    """Test 2: Defensive invalid input → RESCUE_NONE."""
    print("\nTest 2: Defensive invalid input → RESCUE_NONE")
    try:
        from rescue import classify_rescue_strength_v1, RESCUE_NONE

        # Test with UNCLASSIFIED inputs (defensive)
        result = classify_rescue_strength_v1(
            regime_record={"v11_regime_level": "UNCLASSIFIED"},
        )
        assert result["v12_rescue_strength"] == RESCUE_NONE, "Expected RESCUE_NONE (defensive)"
        assert result["v12_rescue_status"] == "AVAILABLE", "Expected AVAILABLE status"
        print(f"  ✓ Invalid input → RESCUE_NONE (defensive)")
        print(f"    Summary: {result['v12_rescue_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_critical_none():
    """Test 3: REGIME_CRITICAL → RESCUE_NONE."""
    print("\nTest 3: REGIME_CRITICAL → RESCUE_NONE")
    try:
        from rescue import classify_rescue_strength_v1, RESCUE_NONE

        result = classify_rescue_strength_v1(
            regime_record={"v11_regime_level": "REGIME_CRITICAL"},
            role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
            edge_record={"v12_edge_type": "EDGE_SHIELD"},
        )
        assert result["v12_rescue_strength"] == RESCUE_NONE, "Expected RESCUE_NONE"
        assert "REGIME_CRITICAL" in result["v12_rescue_warnings"][0], "Expected CRITICAL warning"
        print(f"  ✓ REGIME_CRITICAL → RESCUE_NONE")
        print(f"    Warning: {result['v12_rescue_warnings'][0]}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_ineligible_none():
    """Test 4: INELIGIBLE → RESCUE_NONE."""
    print("\nTest 4: INELIGIBLE → RESCUE_NONE")
    try:
        from rescue import classify_rescue_strength_v1, RESCUE_NONE

        result = classify_rescue_strength_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
            edge_record={"v12_edge_type": "EDGE_SHIELD"},
            eligibility_record={"v12_eligibility_status": "INELIGIBLE"},
        )
        assert result["v12_rescue_strength"] == RESCUE_NONE, "Expected RESCUE_NONE"
        assert "INELIGIBLE" in result["v12_rescue_warnings"][0], "Expected INELIGIBLE warning"
        print(f"  ✓ INELIGIBLE → RESCUE_NONE")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_leak_none():
    """Test 5: EDGE_LEAK → RESCUE_NONE."""
    print("\nTest 5: EDGE_LEAK → RESCUE_NONE")
    try:
        from rescue import classify_rescue_strength_v1, RESCUE_NONE

        result = classify_rescue_strength_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
            edge_record={"v12_edge_type": "EDGE_LEAK"},
        )
        assert result["v12_rescue_strength"] == RESCUE_NONE, "Expected RESCUE_NONE"
        assert "EDGE_LEAK" in result["v12_rescue_warnings"][0], "Expected LEAK warning"
        print(f"  ✓ EDGE_LEAK → RESCUE_NONE")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_strong_strict_allow():
    """Test 6: STRONG strict case with ALLOW_RESCUE_STRONG."""
    print("\nTest 6: STRONG strict case with ALLOW_RESCUE_STRONG")
    try:
        from rescue import classify_rescue_strength_v1, RESCUE_STRONG

        # STRONG requires:
        # - REGIME_MEDIUM
        # - EDGE_SHIELD
        # - role in {STABILITY_ROLE, HEDGE_ROLE}
        # - distortion in {D1_LIQUIDATION, D4_EVENT_DISTORTION, D5_CORRELATION_DISTORTION}
        # - constraint_binding contains "ALLOW_RESCUE_STRONG"
        # - eligibility != INELIGIBLE

        result = classify_rescue_strength_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
            edge_record={"v12_edge_type": "EDGE_SHIELD"},
            eligibility_record={"v12_eligibility_status": "ELIGIBLE_CONSIDERATION_ONLY"},
            constraint_binding_record={"v12_contrib_constraint_labels": ["ALLOW_RESCUE_STRONG"]},
        )
        assert result["v12_rescue_strength"] == RESCUE_STRONG, "Expected RESCUE_STRONG"
        assert result["v12_rescue_status"] == "AVAILABLE", "Expected AVAILABLE status"
        print(f"  ✓ STRONG (strict) with ALLOW_RESCUE_STRONG")
        print(f"    Summary: {result['v12_rescue_summary']}")

        # Test HEDGE_ROLE also yields STRONG
        result_hedge = classify_rescue_strength_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "HEDGE_ROLE"},
            distortion_record={"v12_distortion_type": "D4_EVENT_DISTORTION"},
            edge_record={"v12_edge_type": "EDGE_SHIELD"},
            eligibility_record={"v12_eligibility_status": "ELIGIBLE_CONSIDERATION_ONLY"},
            constraint_binding_record={"v12_contrib_constraint_labels": ["ALLOW_RESCUE_STRONG"]},
        )
        assert result_hedge["v12_rescue_strength"] == RESCUE_STRONG, "Expected STRONG for HEDGE_ROLE"
        print(f"  ✓ STRONG also works for HEDGE_ROLE + D4_EVENT_DISTORTION")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_no_strong_for_volatility_amplify():
    """Test 7: No STRONG for VOLATILITY_ROLE or EDGE_AMPLIFY."""
    print("\nTest 7: No STRONG for VOLATILITY_ROLE or EDGE_AMPLIFY")
    try:
        from rescue import classify_rescue_strength_v1, RESCUE_STRONG

        # Test 7a: VOLATILITY_ROLE should NOT get STRONG (even with ALLOW_RESCUE_STRONG)
        result_volatility = classify_rescue_strength_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "VOLATILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
            edge_record={"v12_edge_type": "EDGE_SHIELD"},
            eligibility_record={"v12_eligibility_status": "ELIGIBLE_CONSIDERATION_ONLY"},
            constraint_binding_record={"v12_contrib_constraint_labels": ["ALLOW_RESCUE_STRONG"]},
        )
        assert result_volatility["v12_rescue_strength"] != RESCUE_STRONG, "VOLATILITY_ROLE should NOT get STRONG"
        print(f"  ✓ VOLATILITY_ROLE does NOT get STRONG: {result_volatility['v12_rescue_strength']}")

        # Test 7b: EDGE_AMPLIFY should NOT get STRONG
        result_amplify = classify_rescue_strength_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
            edge_record={"v12_edge_type": "EDGE_AMPLIFY"},
            eligibility_record={"v12_eligibility_status": "ELIGIBLE_CONSIDERATION_ONLY"},
            constraint_binding_record={"v12_contrib_constraint_labels": ["ALLOW_RESCUE_STRONG"]},
        )
        assert result_amplify["v12_rescue_strength"] != RESCUE_STRONG, "EDGE_AMPLIFY should NOT get STRONG"
        print(f"  ✓ EDGE_AMPLIFY does NOT get STRONG: {result_amplify['v12_rescue_strength']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_dry_run_only_caps_to_weak():
    """Test 8: ELIGIBLE_DRY_RUN_ONLY caps to WEAK."""
    print("\nTest 8: ELIGIBLE_DRY_RUN_ONLY caps to WEAK")
    try:
        from rescue import classify_rescue_strength_v1, RESCUE_WEAK

        # Even with all STRONG conditions, DRY_RUN_ONLY caps at WEAK
        result = classify_rescue_strength_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "STABILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
            edge_record={"v12_edge_type": "EDGE_SHIELD"},
            eligibility_record={"v12_eligibility_status": "ELIGIBLE_DRY_RUN_ONLY"},
            constraint_binding_record={"v12_contrib_constraint_labels": ["ALLOW_RESCUE_STRONG"]},
        )
        assert result["v12_rescue_strength"] == RESCUE_WEAK, "Expected WEAK (capped)"
        assert "DRY_RUN_ONLY" in result["v12_rescue_warnings"][0], "Expected DRY_RUN_ONLY warning"
        print(f"  ✓ ELIGIBLE_DRY_RUN_ONLY caps to WEAK")
        print(f"    Warning: {result['v12_rescue_warnings'][0]}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_coupling_detection():
    """Test 9: Coupling detection."""
    print("\nTest 9: Coupling detection")
    try:
        from rescue import check_rescue_strength_record

        # Test 9a: Rescue coupling (RESCUE_STRONG therefore trade)
        dirty_coupling = {
            "v12_rescue_summary": "Rescue strength RESCUE_STRONG therefore execute trade.",
        }
        coupling_warnings = check_rescue_strength_record(dirty_coupling)
        assert len(coupling_warnings) > 0, "Expected warnings for rescue coupling"
        print(f"  ✓ Rescue coupling detected: {len(coupling_warnings)} warnings")

        # Test 9b: Strong rescue means proceed
        dirty_means = {
            "v12_rescue_summary": "Strong rescue means proceed with swap.",
        }
        means_warnings = check_rescue_strength_record(dirty_means)
        assert len(means_warnings) > 0, "Expected warnings for rescue coupling"
        print(f"  ✓ Rescue coupling (means proceed) detected: {len(means_warnings)} warnings")

        # Test 9c: Clean record (no coupling)
        clean_record = {
            "v12_rescue_summary": "Rescue strength RESCUE_STRONG may indicate structural pattern for REGIME_MEDIUM × STABILITY_ROLE × D1_LIQUIDATION × EDGE_SHIELD.",
        }
        clean_warnings = check_rescue_strength_record(clean_record)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean record, got: {clean_warnings}"
        print(f"  ✓ Clean record passes: no warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_warning_only_behavior():
    """Test 10: Warning-only behavior."""
    print("\nTest 10: Warning-only behavior")
    try:
        from rescue import check_rescue_strength_record

        # Guards should warn, not fail
        # Test with multiple violations (token literals, numeric patterns, coupling)
        dirty_record = {
            "v12_rescue_summary": "Rescue strength with SUI tokens yielding 30% improvement therefore execute trade.",
        }
        warnings = check_rescue_strength_record(dirty_record)

        # Should have warnings for:
        # - Token literals (SUI)
        # - Numeric patterns (30%)
        # - Rescue coupling (therefore execute trade)
        assert len(warnings) > 0, "Expected warnings for violations"
        print(f"  ✓ Guards emit warnings (not errors): {len(warnings)} warnings")
        print(f"    Example warnings:")
        for w in warnings[:3]:
            print(f"      - {w}")

        # Function should return warnings list, not raise exception
        print(f"  ✓ Warning-only behavior verified (no exceptions raised)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR136: v1.2 Rescue Strength Classification Engine v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_defensive_invalid_input,
        test_3_critical_none,
        test_4_ineligible_none,
        test_5_leak_none,
        test_6_strong_strict_allow,
        test_7_no_strong_for_volatility_amplify,
        test_8_dry_run_only_caps_to_weak,
        test_9_coupling_detection,
        test_10_warning_only_behavior,
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
