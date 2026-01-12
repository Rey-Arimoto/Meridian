#!/usr/bin/env python3
"""
PR130: v1.2 Role Carrier Qualification v1 Smoke Tests

Purpose:
    Validate role carrier qualification engine and guards.

Tests:
    1. Import works
    2. Empty input → ERROR + DISQUALIFIED
    3. Unknown role type → ERROR + DISQUALIFIED
    4. Perfect GAS_ROLE match → QUALIFIED
    5. Partial GAS_ROLE match (1 failure) → PARTIALLY_QUALIFIED
    6. Complete mismatch (4 failures) → DISQUALIFIED
    7. STABILITY_ROLE qualification
    8. LIQUIDITY_ROLE qualification
    9. VOLATILITY_ROLE qualification
    10. HEDGE_ROLE qualification
    11. Guards detect token literal violation
    12. Guards detect numeric pattern violation
    13. Guards detect role coupling
    14. Warning-only behavior
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from role import (
            V12AssetProfileSchema,
            V12RoleCarrierQualificationSchema,
            get_asset_profile_schema_info,
            get_role_requirements_info,
            get_qualification_schema_info,
            get_qualification_engine_v1_info,
            qualify_asset_for_role_v1,
            check_role_carrier_record,
            check_role_coupling,
            FORBIDDEN_VOCABULARY,
            OBS_LOW,
            OBS_MEDIUM,
            OBS_HIGH,
            CENS_LOW,
            CENS_MEDIUM,
            CENS_HIGH,
            LIQ_LOW,
            LIQ_MEDIUM,
            LIQ_HIGH,
            DEP_NONE,
            DEP_LOW,
            DEP_MEDIUM,
            DEP_HIGH,
            GAS_ROLE,
            STABILITY_ROLE,
            LIQUIDITY_ROLE,
            VOLATILITY_ROLE,
            HEDGE_ROLE,
            QUALIFIED,
            PARTIALLY_QUALIFIED,
            DISQUALIFIED,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_empty_input_error():
    """Test 2: Empty input → ERROR + DISQUALIFIED."""
    print("\nTest 2: Empty input → ERROR + DISQUALIFIED")
    try:
        from role import qualify_asset_for_role_v1, GAS_ROLE, DISQUALIFIED

        # Test with None input
        result = qualify_asset_for_role_v1(None, GAS_ROLE)
        assert result["v12_role_carrier_status"] == "ERROR", "Expected ERROR status"
        assert result["v12_role_carrier_qualification_status"] == DISQUALIFIED, "Expected DISQUALIFIED"
        print(f"  ✓ None input → ERROR + DISQUALIFIED")
        print(f"    Summary: {result['v12_role_carrier_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_unknown_role_type_error():
    """Test 3: Unknown role type → ERROR + DISQUALIFIED."""
    print("\nTest 3: Unknown role type → ERROR + DISQUALIFIED")
    try:
        from role import qualify_asset_for_role_v1, V12AssetProfileSchema, OBS_HIGH, CENS_HIGH, LIQ_HIGH, DEP_LOW, DISQUALIFIED

        # Create valid asset profile
        profile = V12AssetProfileSchema.create_asset_profile(
            observability=OBS_HIGH,
            censorship_resistance=CENS_HIGH,
            liquidatability=LIQ_HIGH,
            dependency=DEP_LOW,
        )

        # Test with unknown role type
        result = qualify_asset_for_role_v1(profile, "UNKNOWN_ROLE")
        assert result["v12_role_carrier_status"] == "ERROR", "Expected ERROR status"
        assert result["v12_role_carrier_qualification_status"] == DISQUALIFIED, "Expected DISQUALIFIED"
        print(f"  ✓ Unknown role type → ERROR + DISQUALIFIED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_perfect_gas_role_match():
    """Test 4: Perfect GAS_ROLE match → QUALIFIED."""
    print("\nTest 4: Perfect GAS_ROLE match → QUALIFIED")
    try:
        from role import qualify_asset_for_role_v1, V12AssetProfileSchema, GAS_ROLE, QUALIFIED
        from role import OBS_HIGH, CENS_HIGH, LIQ_MEDIUM, DEP_LOW

        # Create perfect GAS_ROLE profile
        profile = V12AssetProfileSchema.create_asset_profile(
            observability=OBS_HIGH,
            censorship_resistance=CENS_HIGH,
            liquidatability=LIQ_MEDIUM,
            dependency=DEP_LOW,
        )

        result = qualify_asset_for_role_v1(profile, GAS_ROLE)
        assert result["v12_role_carrier_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_role_carrier_qualification_status"] == QUALIFIED, "Expected QUALIFIED"
        assert len(result["v12_role_carrier_failed_axes"]) == 0, "Expected no failed axes"
        print(f"  ✓ Perfect GAS_ROLE → QUALIFIED")
        print(f"    Summary: {result['v12_role_carrier_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_partial_gas_role_match():
    """Test 5: Partial GAS_ROLE match (1 failure) → PARTIALLY_QUALIFIED."""
    print("\nTest 5: Partial GAS_ROLE match (1 failure) → PARTIALLY_QUALIFIED")
    try:
        from role import qualify_asset_for_role_v1, V12AssetProfileSchema, GAS_ROLE, PARTIALLY_QUALIFIED
        from role import OBS_HIGH, CENS_HIGH, LIQ_LOW, DEP_LOW

        # Create profile with 1 failure (liquidatability too low)
        profile = V12AssetProfileSchema.create_asset_profile(
            observability=OBS_HIGH,
            censorship_resistance=CENS_HIGH,
            liquidatability=LIQ_LOW,  # Fails (needs MEDIUM)
            dependency=DEP_LOW,
        )

        result = qualify_asset_for_role_v1(profile, GAS_ROLE)
        assert result["v12_role_carrier_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_role_carrier_qualification_status"] == PARTIALLY_QUALIFIED, "Expected PARTIALLY_QUALIFIED"
        assert "liquidatability" in result["v12_role_carrier_failed_axes"], "Expected liquidatability failure"
        print(f"  ✓ Partial GAS_ROLE (1 failure) → PARTIALLY_QUALIFIED")
        print(f"    Failed axes: {result['v12_role_carrier_failed_axes']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_complete_mismatch():
    """Test 6: Complete mismatch (4 failures) → DISQUALIFIED."""
    print("\nTest 6: Complete mismatch (4 failures) → DISQUALIFIED")
    try:
        from role import qualify_asset_for_role_v1, V12AssetProfileSchema, GAS_ROLE, DISQUALIFIED
        from role import OBS_LOW, CENS_LOW, LIQ_LOW, DEP_HIGH

        # Create profile with all 4 failures
        profile = V12AssetProfileSchema.create_asset_profile(
            observability=OBS_LOW,
            censorship_resistance=CENS_LOW,
            liquidatability=LIQ_LOW,
            dependency=DEP_HIGH,
        )

        result = qualify_asset_for_role_v1(profile, GAS_ROLE)
        assert result["v12_role_carrier_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_role_carrier_qualification_status"] == DISQUALIFIED, "Expected DISQUALIFIED"
        assert len(result["v12_role_carrier_failed_axes"]) == 4, "Expected 4 failed axes"
        print(f"  ✓ Complete mismatch (4 failures) → DISQUALIFIED")
        print(f"    Failed axes: {result['v12_role_carrier_failed_axes']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_stability_role_qualification():
    """Test 7: STABILITY_ROLE qualification."""
    print("\nTest 7: STABILITY_ROLE qualification")
    try:
        from role import qualify_asset_for_role_v1, V12AssetProfileSchema, STABILITY_ROLE, QUALIFIED
        from role import OBS_MEDIUM, CENS_MEDIUM, LIQ_HIGH, DEP_MEDIUM

        # Create STABILITY_ROLE profile
        profile = V12AssetProfileSchema.create_asset_profile(
            observability=OBS_MEDIUM,
            censorship_resistance=CENS_MEDIUM,
            liquidatability=LIQ_HIGH,
            dependency=DEP_MEDIUM,
        )

        result = qualify_asset_for_role_v1(profile, STABILITY_ROLE)
        assert result["v12_role_carrier_qualification_status"] == QUALIFIED, "Expected QUALIFIED"
        print(f"  ✓ STABILITY_ROLE → QUALIFIED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_liquidity_role_qualification():
    """Test 8: LIQUIDITY_ROLE qualification."""
    print("\nTest 8: LIQUIDITY_ROLE qualification")
    try:
        from role import qualify_asset_for_role_v1, V12AssetProfileSchema, LIQUIDITY_ROLE, QUALIFIED
        from role import OBS_HIGH, CENS_MEDIUM, LIQ_HIGH, DEP_MEDIUM

        # Create LIQUIDITY_ROLE profile
        profile = V12AssetProfileSchema.create_asset_profile(
            observability=OBS_HIGH,
            censorship_resistance=CENS_MEDIUM,
            liquidatability=LIQ_HIGH,
            dependency=DEP_MEDIUM,
        )

        result = qualify_asset_for_role_v1(profile, LIQUIDITY_ROLE)
        assert result["v12_role_carrier_qualification_status"] == QUALIFIED, "Expected QUALIFIED"
        print(f"  ✓ LIQUIDITY_ROLE → QUALIFIED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_volatility_role_qualification():
    """Test 9: VOLATILITY_ROLE qualification."""
    print("\nTest 9: VOLATILITY_ROLE qualification")
    try:
        from role import qualify_asset_for_role_v1, V12AssetProfileSchema, VOLATILITY_ROLE, QUALIFIED
        from role import OBS_MEDIUM, CENS_LOW, LIQ_MEDIUM, DEP_HIGH

        # Create VOLATILITY_ROLE profile
        profile = V12AssetProfileSchema.create_asset_profile(
            observability=OBS_MEDIUM,
            censorship_resistance=CENS_LOW,
            liquidatability=LIQ_MEDIUM,
            dependency=DEP_HIGH,
        )

        result = qualify_asset_for_role_v1(profile, VOLATILITY_ROLE)
        assert result["v12_role_carrier_qualification_status"] == QUALIFIED, "Expected QUALIFIED"
        print(f"  ✓ VOLATILITY_ROLE → QUALIFIED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_hedge_role_qualification():
    """Test 10: HEDGE_ROLE qualification."""
    print("\nTest 10: HEDGE_ROLE qualification")
    try:
        from role import qualify_asset_for_role_v1, V12AssetProfileSchema, HEDGE_ROLE, QUALIFIED
        from role import OBS_MEDIUM, CENS_MEDIUM, LIQ_MEDIUM, DEP_MEDIUM

        # Create HEDGE_ROLE profile
        profile = V12AssetProfileSchema.create_asset_profile(
            observability=OBS_MEDIUM,
            censorship_resistance=CENS_MEDIUM,
            liquidatability=LIQ_MEDIUM,
            dependency=DEP_MEDIUM,
        )

        result = qualify_asset_for_role_v1(profile, HEDGE_ROLE)
        assert result["v12_role_carrier_qualification_status"] == QUALIFIED, "Expected QUALIFIED"
        print(f"  ✓ HEDGE_ROLE → QUALIFIED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_11_token_literal_violation():
    """Test 11: Guards detect token literal violation."""
    print("\nTest 11: Guards detect token literal violation")
    try:
        from role import check_role_carrier_record

        # Test with token literals
        dirty_record = {
            "v12_role_carrier_summary": "asset SUI is QUALIFIED for GAS_ROLE with USDC backing.",
        }
        warnings = check_role_carrier_record(dirty_record)

        assert len(warnings) > 0, "Expected warnings for token literals"
        print(f"  ✓ Token literals detected: {len(warnings)} warnings")
        for w in warnings[:2]:
            print(f"    - {w}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_12_numeric_pattern_violation():
    """Test 12: Guards detect numeric pattern violation."""
    print("\nTest 12: Guards detect numeric pattern violation")
    try:
        from role import check_role_carrier_record

        # Test with numeric patterns
        dirty_record = {
            "v12_role_carrier_summary": "asset scores 85% qualification with 10 axes checked.",
        }
        warnings = check_role_carrier_record(dirty_record)

        assert len(warnings) > 0, "Expected warnings for numeric patterns"
        print(f"  ✓ Numeric patterns detected: {len(warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_13_role_coupling():
    """Test 13: Guards detect role coupling."""
    print("\nTest 13: Guards detect role coupling")
    try:
        from role import check_role_carrier_record, check_role_coupling

        # Test role coupling patterns
        coupling_patterns = [
            "asset QUALIFIED therefore execute trade.",
            "asset DISQUALIFIED so avoid trading.",
            "qualification means we should proceed with swap.",
        ]

        for pattern in coupling_patterns:
            warnings = check_role_coupling(pattern)
            assert len(warnings) > 0, f"Expected warnings for: {pattern}"
            print(f"  ✓ Detected coupling: '{pattern[:40]}...'")

        # Test clean text
        clean_text = "asset labeled QUALIFIED for GAS_ROLE (all axes meet requirements)."
        clean_warnings = check_role_coupling(clean_text)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean text, got: {clean_warnings}"
        print(f"  ✓ Clean text passes: no coupling detected")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_14_warning_only_behavior():
    """Test 14: Warning-only behavior."""
    print("\nTest 14: Warning-only behavior")
    try:
        from role import check_role_carrier_record

        # Test that guards never raise exceptions
        dirty_records = [
            {"v12_role_carrier_summary": "asset SUI with BTC backing is QUALIFIED."},
            {"v12_role_carrier_summary": "qualification score is 90% with 10 checks."},
            {"v12_role_carrier_summary": "address 0x1234567890abcdef is QUALIFIED."},
            {"v12_role_carrier_summary": "QUALIFIED therefore execute trade."},
        ]

        for record in dirty_records:
            try:
                warnings = check_role_carrier_record(record)
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
    print("PR130: v1.2 Role Carrier Qualification v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_empty_input_error,
        test_3_unknown_role_type_error,
        test_4_perfect_gas_role_match,
        test_5_partial_gas_role_match,
        test_6_complete_mismatch,
        test_7_stability_role_qualification,
        test_8_liquidity_role_qualification,
        test_9_volatility_role_qualification,
        test_10_hedge_role_qualification,
        test_11_token_literal_violation,
        test_12_numeric_pattern_violation,
        test_13_role_coupling,
        test_14_warning_only_behavior,
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
