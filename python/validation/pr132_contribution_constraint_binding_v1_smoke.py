#!/usr/bin/env python3
"""
PR132: v1.2 Contribution → Constraint Binding v1 Smoke Tests

Purpose:
    Validate contribution constraint binding and guards.

Tests:
    1. Import works
    2. Defensive invalid input → ERROR
    3. REGIME_CRITICAL → BLOCKED
    4. INELIGIBLE → BLOCKED
    5. SUPPRESSED → BLOCKED
    6. REGIME_MEDIUM × VOLATILITY × D1 → PRIMARY
    7. REGIME_HIGH/LOW → SECONDARY
    8. Default → NONE
    9. Guards catch coupling / token literal / numeric pattern
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from bind import (
            V12ContributionConstraintSchema,
            get_contribution_constraint_schema_info,
            bind_contribution_constraints_v1,
            get_contribution_binding_engine_v1_info,
            check_contribution_binding_record,
            check_contribution_zone_coupling,
            CONTRIB_ZONE_NONE,
            CONTRIB_ZONE_SECONDARY,
            CONTRIB_ZONE_PRIMARY,
            CONTRIB_ZONE_BLOCKED,
            CONSTRAINT_CONTRIB_PRIMARY_MEDIUM_VOLATILITY_DISTORTION,
        )
        from bridge.v12_contrib_constraints_to_explain_context_extension import (
            extend_explain_context_with_contribution_constraints_v1,
            get_contribution_constraint_extension_summary_v1,
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
        from bind import bind_contribution_constraints_v1

        # Test with UNCLASSIFIED regime
        result = bind_contribution_constraints_v1(
            regime_record={"v11_regime_level": "UNCLASSIFIED"},
        )
        assert result["v12_contrib_constraint_status"] == "ERROR", "Expected ERROR status"
        print(f"  ✓ Invalid input → ERROR")
        print(f"    Summary: {result['v12_contrib_constraint_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_regime_critical_blocked():
    """Test 3: REGIME_CRITICAL → BLOCKED."""
    print("\nTest 3: REGIME_CRITICAL → BLOCKED")
    try:
        from bind import bind_contribution_constraints_v1, CONTRIB_ZONE_BLOCKED

        result = bind_contribution_constraints_v1(
            regime_record={"v11_regime_level": "REGIME_CRITICAL"},
        )
        assert result["v12_contrib_constraint_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_contrib_constraint_zone_label"] == CONTRIB_ZONE_BLOCKED, "Expected BLOCKED zone"
        print(f"  ✓ REGIME_CRITICAL → BLOCKED")
        print(f"    Constraints: {result['v12_contrib_constraint_labels']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_ineligible_blocked():
    """Test 4: INELIGIBLE → BLOCKED."""
    print("\nTest 4: INELIGIBLE → BLOCKED")
    try:
        from bind import bind_contribution_constraints_v1, CONTRIB_ZONE_BLOCKED

        result = bind_contribution_constraints_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            eligibility_record={"v12_eligibility_status": "INELIGIBLE"},
        )
        assert result["v12_contrib_constraint_zone_label"] == CONTRIB_ZONE_BLOCKED, "Expected BLOCKED zone"
        print(f"  ✓ INELIGIBLE → BLOCKED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_suppressed_blocked():
    """Test 5: SUPPRESSED → BLOCKED."""
    print("\nTest 5: SUPPRESSED → BLOCKED")
    try:
        from bind import bind_contribution_constraints_v1, CONTRIB_ZONE_BLOCKED

        result = bind_contribution_constraints_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            permission_monitor_record={"v12_monitor_suppression_state": "SUPPRESSED"},
        )
        assert result["v12_contrib_constraint_zone_label"] == CONTRIB_ZONE_BLOCKED, "Expected BLOCKED zone"
        print(f"  ✓ SUPPRESSED → BLOCKED")
        print(f"    Constraints: {result['v12_contrib_constraint_labels']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_medium_volatility_d1_primary():
    """Test 6: REGIME_MEDIUM × VOLATILITY × D1 → PRIMARY."""
    print("\nTest 6: REGIME_MEDIUM × VOLATILITY × D1 → PRIMARY")
    try:
        from bind import bind_contribution_constraints_v1, CONTRIB_ZONE_PRIMARY

        result = bind_contribution_constraints_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "VOLATILITY_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        )
        assert result["v12_contrib_constraint_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_contrib_constraint_zone_label"] == CONTRIB_ZONE_PRIMARY, "Expected PRIMARY zone"
        print(f"  ✓ MEDIUM × VOLATILITY × D1 → PRIMARY")
        print(f"    Constraints: {result['v12_contrib_constraint_labels']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_regime_high_low_secondary():
    """Test 7: REGIME_HIGH/LOW → SECONDARY."""
    print("\nTest 7: REGIME_HIGH/LOW → SECONDARY")
    try:
        from bind import bind_contribution_constraints_v1, CONTRIB_ZONE_SECONDARY

        # Test HIGH
        result_high = bind_contribution_constraints_v1(
            regime_record={"v11_regime_level": "REGIME_HIGH"},
        )
        assert result_high["v12_contrib_constraint_zone_label"] == CONTRIB_ZONE_SECONDARY, "Expected SECONDARY for HIGH"
        print(f"  ✓ REGIME_HIGH → SECONDARY")

        # Test LOW
        result_low = bind_contribution_constraints_v1(
            regime_record={"v11_regime_level": "REGIME_LOW"},
        )
        assert result_low["v12_contrib_constraint_zone_label"] == CONTRIB_ZONE_SECONDARY, "Expected SECONDARY for LOW"
        print(f"  ✓ REGIME_LOW → SECONDARY")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_default_none():
    """Test 8: Default → NONE."""
    print("\nTest 8: Default → NONE")
    try:
        from bind import bind_contribution_constraints_v1, CONTRIB_ZONE_NONE

        # MEDIUM × GAS_ROLE (not VOLATILITY) → NONE
        result = bind_contribution_constraints_v1(
            regime_record={"v11_regime_level": "REGIME_MEDIUM"},
            role_record={"v12_role_carrier_role_type": "GAS_ROLE"},
            distortion_record={"v12_distortion_type": "D1_LIQUIDATION"},
        )
        assert result["v12_contrib_constraint_zone_label"] == CONTRIB_ZONE_NONE, "Expected NONE zone"
        print(f"  ✓ Default (MEDIUM × GAS_ROLE) → NONE")
        print(f"    Constraints: {result['v12_contrib_constraint_labels']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_guards_catch_violations():
    """Test 9: Guards catch coupling / token literal / numeric pattern."""
    print("\nTest 9: Guards catch coupling / token literal / numeric pattern")
    try:
        from bind import check_contribution_binding_record

        # Test 9a: Zone coupling
        dirty_coupling = {
            "v12_contrib_constraint_summary": "contribution zone primary therefore execute trade.",
        }
        coupling_warnings = check_contribution_binding_record(dirty_coupling)
        assert len(coupling_warnings) > 0, "Expected warnings for zone coupling"
        print(f"  ✓ Zone coupling detected: {len(coupling_warnings)} warnings")

        # Test 9b: Numeric patterns
        dirty_numeric = {
            "v12_contrib_constraint_summary": "contribution zone primary with 30% return expected.",
        }
        numeric_warnings = check_contribution_binding_record(dirty_numeric)
        assert len(numeric_warnings) > 0, "Expected warnings for numeric patterns"
        print(f"  ✓ Numeric patterns detected: {len(numeric_warnings)} warnings")

        # Test 9c: Token literals in labels (use spaces for word boundary matching)
        dirty_token = {
            "v12_contrib_constraint_summary": "contribution zone primary with SUI and USDC tokens.",
            "v12_contrib_constraint_labels": ["contrib primary zone"],
        }
        token_warnings = check_contribution_binding_record(dirty_token)
        assert len(token_warnings) > 0, f"Expected warnings for token literals, got {len(token_warnings)}: {token_warnings}"
        print(f"  ✓ Token literals detected: {len(token_warnings)} warnings")

        # Test clean record
        clean_record = {
            "v12_contrib_constraint_summary": "contribution zone labeled CONTRIB_ZONE_PRIMARY with constraints: contrib_primary_medium_volatility_distortion.",
            "v12_contrib_constraint_labels": ["contrib_primary_medium_volatility_distortion"],
        }
        clean_warnings = check_contribution_binding_record(clean_record)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean record, got: {clean_warnings}"
        print(f"  ✓ Clean record passes: no warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR132: v1.2 Contribution → Constraint Binding v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_invalid_input_error,
        test_3_regime_critical_blocked,
        test_4_ineligible_blocked,
        test_5_suppressed_blocked,
        test_6_medium_volatility_d1_primary,
        test_7_regime_high_low_secondary,
        test_8_default_none,
        test_9_guards_catch_violations,
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
