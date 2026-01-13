#!/usr/bin/env python3
"""
PR144: v1.4 Role Safe Band Guidance v1 Smoke Tests

Purpose:
    Validate v1.4 role safe band guidance engine.

Tests:
    1. Import works
    2. Empty inputs → ERROR record valid
    3. Minimal valid inputs → AVAILABLE
    4. UNKNOWN regime handling
    5. Missing role in portfolio → role status UNKNOWN but record AVAILABLE
    6. Output contains no forbidden vocab
    7. Output contains no token literals
    8. Output contains no address patterns
    9. Output contains no numeric patterns in text fields
    10. Warning-only behavior: guard returns warnings but never raises
    11. CRITICAL regime → VOLATILITY_ROLE gets BAND_ZERO
    12. Status determination works (BELOW/WITHIN/ABOVE)
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from guidance import (
            build_role_safe_band_guidance_v1,
            get_safe_band_engine_v1_info,
            check_guidance_record,
            V14RoleSafeBandSchema,
            GUIDANCE_STATUS_AVAILABLE,
            GUIDANCE_STATUS_ERROR,
            ROLE_VOLATILITY,
            ROLE_LIQUIDITY,
            ROLE_STABILITY,
            ROLE_HEDGE,
            ROLE_GAS,
            REGIME_LOW,
            REGIME_MEDIUM,
            REGIME_HIGH,
            REGIME_CRITICAL,
            STATUS_BELOW_SAFE,
            STATUS_WITHIN_SAFE,
            STATUS_ABOVE_SAFE,
            STATUS_UNKNOWN,
            BAND_ZERO,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_empty_inputs_to_error():
    """Test 2: Empty inputs → ERROR record valid."""
    print("\nTest 2: Empty inputs → ERROR record valid")
    try:
        from guidance import build_role_safe_band_guidance_v1, GUIDANCE_STATUS_ERROR

        result = build_role_safe_band_guidance_v1(None, None)

        guidance = result["guidance_record"]
        assert guidance["v14_guidance_status"] == GUIDANCE_STATUS_ERROR, "Expected ERROR status"

        print(f"  ✓ ERROR record with status: {guidance['v14_guidance_status']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_minimal_valid_inputs():
    """Test 3: Minimal valid inputs → AVAILABLE."""
    print("\nTest 3: Minimal valid inputs → AVAILABLE")
    try:
        from guidance import (
            build_role_safe_band_guidance_v1,
            GUIDANCE_STATUS_AVAILABLE,
            ROLE_VOLATILITY,
            ROLE_LIQUIDITY,
            ROLE_STABILITY,
            ROLE_HEDGE,
            ROLE_GAS,
            REGIME_MEDIUM,
        )

        portfolio = {
            ROLE_VOLATILITY: 0.30,
            ROLE_LIQUIDITY: 0.25,
            ROLE_STABILITY: 0.20,
            ROLE_HEDGE: 0.15,
            ROLE_GAS: 0.10,
        }
        regime = {"v11_regime_level": REGIME_MEDIUM}

        result = build_role_safe_band_guidance_v1(portfolio, regime)
        guidance = result["guidance_record"]

        assert guidance["v14_guidance_status"] == GUIDANCE_STATUS_AVAILABLE, "Expected AVAILABLE status"
        assert len(guidance["v14_guidance_roles"]) == 5, "Expected 5 roles processed"

        print(f"  ✓ AVAILABLE record with {len(guidance['v14_guidance_roles'])} roles")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_unknown_regime_handling():
    """Test 4: UNKNOWN regime handling."""
    print("\nTest 4: UNKNOWN regime handling")
    try:
        from guidance import (
            build_role_safe_band_guidance_v1,
            GUIDANCE_STATUS_AVAILABLE,
            ROLE_VOLATILITY,
            REGIME_UNKNOWN,
        )

        portfolio = {ROLE_VOLATILITY: 0.30}
        regime = {"v11_regime_level": "INVALID_REGIME"}  # Invalid regime

        result = build_role_safe_band_guidance_v1(portfolio, regime)
        guidance = result["guidance_record"]

        # Should still be AVAILABLE but with UNKNOWN regime
        assert guidance["v14_guidance_status"] == GUIDANCE_STATUS_AVAILABLE, "Expected AVAILABLE status"
        assert guidance["v14_guidance_regime_label"] == REGIME_UNKNOWN, "Expected UNKNOWN regime"
        assert len(result["warnings"]) > 0, "Expected warnings for invalid regime"

        print(f"  ✓ UNKNOWN regime handled with {len(result['warnings'])} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_missing_role_in_portfolio():
    """Test 5: Missing role in portfolio → role status UNKNOWN but record AVAILABLE."""
    print("\nTest 5: Missing role in portfolio")
    try:
        from guidance import (
            build_role_safe_band_guidance_v1,
            GUIDANCE_STATUS_AVAILABLE,
            ROLE_VOLATILITY,
            ROLE_STABILITY,
            STATUS_UNKNOWN,
            REGIME_MEDIUM,
        )

        # Only provide 2 roles, missing others
        portfolio = {
            ROLE_VOLATILITY: 0.50,
            # Missing: LIQUIDITY, STABILITY, HEDGE, GAS
        }
        regime = {"v11_regime_level": REGIME_MEDIUM}

        result = build_role_safe_band_guidance_v1(portfolio, regime)
        guidance = result["guidance_record"]

        assert guidance["v14_guidance_status"] == GUIDANCE_STATUS_AVAILABLE, "Expected AVAILABLE status"

        # Check that missing roles have UNKNOWN status
        assert ROLE_STABILITY in guidance["v14_guidance_roles"], "Expected STABILITY_ROLE in output"
        stability_entry = guidance["v14_guidance_roles"][ROLE_STABILITY]
        assert stability_entry["status"] == STATUS_UNKNOWN, "Expected UNKNOWN status for missing role"

        print(f"  ✓ Missing roles handled with UNKNOWN status")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_no_forbidden_vocab():
    """Test 6: Output contains no forbidden vocab."""
    print("\nTest 6: Output contains no forbidden vocab")
    try:
        from guidance import (
            build_role_safe_band_guidance_v1,
            check_guidance_record,
            ROLE_VOLATILITY,
            REGIME_MEDIUM,
        )

        portfolio = {ROLE_VOLATILITY: 0.30}
        regime = {"v11_regime_level": REGIME_MEDIUM}

        result = build_role_safe_band_guidance_v1(portfolio, regime)
        guidance = result["guidance_record"]

        # Run constitutional guard
        guard_warnings = check_guidance_record(guidance)

        # Check for forbidden vocabulary
        vocab_warnings = [w for w in guard_warnings if "forbidden vocabulary" in w.lower()]

        assert len(vocab_warnings) == 0, f"Expected no forbidden vocab warnings, got {len(vocab_warnings)}"

        print(f"  ✓ No forbidden vocabulary detected")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_no_token_literals():
    """Test 7: Output contains no token literals."""
    print("\nTest 7: Output contains no token literals")
    try:
        from guidance import (
            build_role_safe_band_guidance_v1,
            check_guidance_record,
            ROLE_VOLATILITY,
            REGIME_MEDIUM,
        )

        portfolio = {ROLE_VOLATILITY: 0.30}
        regime = {"v11_regime_level": REGIME_MEDIUM}

        result = build_role_safe_band_guidance_v1(portfolio, regime)
        guidance = result["guidance_record"]

        # Run constitutional guard
        guard_warnings = check_guidance_record(guidance)

        # Check for token literals
        token_warnings = [w for w in guard_warnings if "token literal" in w.lower()]

        assert len(token_warnings) == 0, f"Expected no token literal warnings, got {len(token_warnings)}"

        print(f"  ✓ No token literals detected")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_no_address_patterns():
    """Test 8: Output contains no address patterns."""
    print("\nTest 8: Output contains no address patterns")
    try:
        from guidance import (
            build_role_safe_band_guidance_v1,
            check_guidance_record,
            ROLE_VOLATILITY,
            REGIME_MEDIUM,
        )

        portfolio = {ROLE_VOLATILITY: 0.30}
        regime = {"v11_regime_level": REGIME_MEDIUM}

        result = build_role_safe_band_guidance_v1(portfolio, regime)
        guidance = result["guidance_record"]

        # Run constitutional guard
        guard_warnings = check_guidance_record(guidance)

        # Check for address patterns
        address_warnings = [w for w in guard_warnings if "address pattern" in w.lower()]

        assert len(address_warnings) == 0, f"Expected no address pattern warnings, got {len(address_warnings)}"

        print(f"  ✓ No address patterns detected")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_no_numeric_patterns():
    """Test 9: Output contains no numeric patterns in text fields."""
    print("\nTest 9: Output contains no numeric patterns in text fields")
    try:
        from guidance import (
            build_role_safe_band_guidance_v1,
            check_guidance_record,
            ROLE_VOLATILITY,
            REGIME_MEDIUM,
        )

        portfolio = {ROLE_VOLATILITY: 0.30}
        regime = {"v11_regime_level": REGIME_MEDIUM}

        result = build_role_safe_band_guidance_v1(portfolio, regime)
        guidance = result["guidance_record"]

        # Run constitutional guard
        guard_warnings = check_guidance_record(guidance)

        # Check for numeric patterns
        numeric_warnings = [w for w in guard_warnings if "numeric pattern" in w.lower()]

        assert len(numeric_warnings) == 0, f"Expected no numeric pattern warnings, got {len(numeric_warnings)}"

        print(f"  ✓ No numeric patterns detected in text")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_warning_only_behavior():
    """Test 10: Warning-only behavior: guard returns warnings but never raises."""
    print("\nTest 10: Warning-only behavior")
    try:
        from guidance import check_guidance_record

        # Create dirty guidance with violations
        dirty_guidance = {
            "v14_guidance_summary": "You should buy SUI at 0.35 ratio.",
            "v14_guidance_roles": {
                "VOLATILITY_ROLE": {
                    "interpretation": "Execute trade therefore proceed.",
                }
            },
        }

        # Guard should return warnings, not raise
        warnings = check_guidance_record(dirty_guidance)

        assert isinstance(warnings, list), "Expected list of warnings"
        assert len(warnings) > 0, "Expected warnings for violations"

        print(f"  ✓ Guard returned {len(warnings)} warnings without raising")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_11_critical_regime_volatility_zero():
    """Test 11: CRITICAL regime → VOLATILITY_ROLE gets BAND_ZERO."""
    print("\nTest 11: CRITICAL regime → VOLATILITY_ROLE gets BAND_ZERO")
    try:
        from guidance import (
            build_role_safe_band_guidance_v1,
            ROLE_VOLATILITY,
            REGIME_CRITICAL,
            BAND_ZERO,
        )

        portfolio = {ROLE_VOLATILITY: 0.05}
        regime = {"v11_regime_level": REGIME_CRITICAL}

        result = build_role_safe_band_guidance_v1(portfolio, regime)
        guidance = result["guidance_record"]

        volatility_entry = guidance["v14_guidance_roles"][ROLE_VOLATILITY]
        assert volatility_entry["safe_band_bucket"] == BAND_ZERO, f"Expected BAND_ZERO, got {volatility_entry['safe_band_bucket']}"

        print(f"  ✓ CRITICAL regime maps VOLATILITY to BAND_ZERO")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_12_status_determination():
    """Test 12: Status determination works (BELOW/WITHIN/ABOVE)."""
    print("\nTest 12: Status determination")
    try:
        from guidance import (
            build_role_safe_band_guidance_v1,
            ROLE_VOLATILITY,
            REGIME_MEDIUM,
            STATUS_BELOW_SAFE,
            STATUS_WITHIN_SAFE,
            STATUS_ABOVE_SAFE,
        )

        # Test WITHIN_SAFE (MEDIUM regime expects VOLATILITY in BAND_MEDIUM: 25-50%)
        portfolio_within = {ROLE_VOLATILITY: 0.35}  # 35% - should be within
        regime = {"v11_regime_level": REGIME_MEDIUM}

        result_within = build_role_safe_band_guidance_v1(portfolio_within, regime)
        guidance_within = result_within["guidance_record"]
        status_within = guidance_within["v14_guidance_roles"][ROLE_VOLATILITY]["status"]

        assert status_within == STATUS_WITHIN_SAFE, f"Expected WITHIN_SAFE for 35%, got {status_within}"
        print(f"  ✓ WITHIN_SAFE status determined correctly")

        # Test BELOW_SAFE (ratio below band)
        portfolio_below = {ROLE_VOLATILITY: 0.10}  # 10% - should be below BAND_MEDIUM
        result_below = build_role_safe_band_guidance_v1(portfolio_below, regime)
        guidance_below = result_below["guidance_record"]
        status_below = guidance_below["v14_guidance_roles"][ROLE_VOLATILITY]["status"]

        assert status_below == STATUS_BELOW_SAFE, f"Expected BELOW_SAFE for 10%, got {status_below}"
        print(f"  ✓ BELOW_SAFE status determined correctly")

        # Test ABOVE_SAFE (ratio above band)
        portfolio_above = {ROLE_VOLATILITY: 0.80}  # 80% - should be above BAND_MEDIUM
        result_above = build_role_safe_band_guidance_v1(portfolio_above, regime)
        guidance_above = result_above["guidance_record"]
        status_above = guidance_above["v14_guidance_roles"][ROLE_VOLATILITY]["status"]

        assert status_above == STATUS_ABOVE_SAFE, f"Expected ABOVE_SAFE for 80%, got {status_above}"
        print(f"  ✓ ABOVE_SAFE status determined correctly")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR144: v1.4 Role Safe Band Guidance - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_empty_inputs_to_error,
        test_3_minimal_valid_inputs,
        test_4_unknown_regime_handling,
        test_5_missing_role_in_portfolio,
        test_6_no_forbidden_vocab,
        test_7_no_token_literals,
        test_8_no_address_patterns,
        test_9_no_numeric_patterns,
        test_10_warning_only_behavior,
        test_11_critical_regime_volatility_zero,
        test_12_status_determination,
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
