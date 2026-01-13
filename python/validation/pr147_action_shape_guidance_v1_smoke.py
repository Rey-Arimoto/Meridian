#!/usr/bin/env python3
"""
PR147: v1.4 Action Shape Guidance v1 Smoke Tests

Purpose:
    Validate v1.4 action shape guidance engine.

Tests:
    1. Import works
    2. Minimal bundle (stress UNKNOWN) → AVAILABLE with UNKNOWN shape
    3. CALM + DRY_RUN_ONLY → OBSERVE_ONLY
    4. TENSE + CONSIDERATION_ONLY → CONSIDER_ONLY
    5. TENSE + DRY_RUN_ONLY → SIMULATION_ONLY
    6. STRESSED → FREEZE_STATE
    7. INELIGIBLE → NO_ACTION
    8. Malformed inputs → ERROR record valid + warnings
    9. Forbidden vocab injection → warnings
    10. Token literal injection → warnings
    11. Numeric/address injection → warnings
    12. Coupling phrase injection → warnings
    13. Guard is warning-only (no exceptions)
    14. Stress conflict detection (PR146 vs PR145)
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from action import (
            build_action_shape_from_bundle_v1,
            get_action_shape_engine_v1_info,
            check_action_record,
            V14ActionShapeSchema,
            ACTION_STATUS_AVAILABLE,
            ACTION_STATUS_ERROR,
            ACTION_SHAPE_UNKNOWN,
            ACTION_SHAPE_NO_ACTION,
            ACTION_SHAPE_OBSERVE_ONLY,
            ACTION_SHAPE_SIMULATION_ONLY,
            ACTION_SHAPE_CONSIDER_ONLY,
            ACTION_SHAPE_FREEZE_STATE,
            ACTION_SCOPE_GLOBAL,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_minimal_bundle_unknown():
    """Test 2: Minimal bundle (stress UNKNOWN) → AVAILABLE with UNKNOWN shape."""
    print("\nTest 2: Minimal bundle (stress UNKNOWN) → AVAILABLE")
    try:
        from action import (
            build_action_shape_from_bundle_v1,
            ACTION_STATUS_AVAILABLE,
            ACTION_SHAPE_UNKNOWN,
        )

        # Minimal bundle with UNKNOWN stress
        bundle = {
            "artifacts": {
                "stress_rule": {
                    "v14_stress_label": "UNKNOWN",
                },
            }
        }

        result = build_action_shape_from_bundle_v1(bundle)
        action = result["action_record"]

        assert action["v14_action_status"] == ACTION_STATUS_AVAILABLE, "Expected AVAILABLE status"
        assert action["v14_action_action_shape"] == ACTION_SHAPE_UNKNOWN, "Expected UNKNOWN shape"

        print(f"  ✓ AVAILABLE with shape: {action['v14_action_action_shape']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_calm_dry_run_observe():
    """Test 3: CALM + DRY_RUN_ONLY → OBSERVE_ONLY."""
    print("\nTest 3: CALM + DRY_RUN_ONLY → OBSERVE_ONLY")
    try:
        from action import (
            build_action_shape_from_bundle_v1,
            ACTION_SHAPE_OBSERVE_ONLY,
        )

        bundle = {
            "artifacts": {
                "stress_rule": {
                    "v14_stress_label": "CALM",
                },
                "eligibility": {
                    "v12_eligibility_label": "ELIGIBLE_DRY_RUN_ONLY",
                },
            }
        }

        result = build_action_shape_from_bundle_v1(bundle)
        action = result["action_record"]

        assert action["v14_action_action_shape"] == ACTION_SHAPE_OBSERVE_ONLY, \
            f"Expected OBSERVE_ONLY, got {action['v14_action_action_shape']}"

        print(f"  ✓ Shape: {action['v14_action_action_shape']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_tense_consideration_consider():
    """Test 4: TENSE + CONSIDERATION_ONLY → CONSIDER_ONLY."""
    print("\nTest 4: TENSE + CONSIDERATION_ONLY → CONSIDER_ONLY")
    try:
        from action import (
            build_action_shape_from_bundle_v1,
            ACTION_SHAPE_CONSIDER_ONLY,
        )

        bundle = {
            "artifacts": {
                "stress_rule": {
                    "v14_stress_label": "TENSE",
                },
                "eligibility": {
                    "v12_eligibility_label": "ELIGIBLE_CONSIDERATION_ONLY",
                },
            }
        }

        result = build_action_shape_from_bundle_v1(bundle)
        action = result["action_record"]

        assert action["v14_action_action_shape"] == ACTION_SHAPE_CONSIDER_ONLY, \
            f"Expected CONSIDER_ONLY, got {action['v14_action_action_shape']}"

        print(f"  ✓ Shape: {action['v14_action_action_shape']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_tense_dry_run_simulation():
    """Test 5: TENSE + DRY_RUN_ONLY → SIMULATION_ONLY."""
    print("\nTest 5: TENSE + DRY_RUN_ONLY → SIMULATION_ONLY")
    try:
        from action import (
            build_action_shape_from_bundle_v1,
            ACTION_SHAPE_SIMULATION_ONLY,
        )

        bundle = {
            "artifacts": {
                "stress_rule": {
                    "v14_stress_label": "TENSE",
                },
                "eligibility": {
                    "v12_eligibility_label": "ELIGIBLE_DRY_RUN_ONLY",
                },
            }
        }

        result = build_action_shape_from_bundle_v1(bundle)
        action = result["action_record"]

        assert action["v14_action_action_shape"] == ACTION_SHAPE_SIMULATION_ONLY, \
            f"Expected SIMULATION_ONLY, got {action['v14_action_action_shape']}"

        print(f"  ✓ Shape: {action['v14_action_action_shape']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_stressed_freeze():
    """Test 6: STRESSED → FREEZE_STATE."""
    print("\nTest 6: STRESSED → FREEZE_STATE")
    try:
        from action import (
            build_action_shape_from_bundle_v1,
            ACTION_SHAPE_FREEZE_STATE,
        )

        bundle = {
            "artifacts": {
                "stress_rule": {
                    "v14_stress_label": "STRESSED",
                },
                "eligibility": {
                    "v12_eligibility_label": "ELIGIBLE_DRY_RUN_ONLY",
                },
            }
        }

        result = build_action_shape_from_bundle_v1(bundle)
        action = result["action_record"]

        assert action["v14_action_action_shape"] == ACTION_SHAPE_FREEZE_STATE, \
            f"Expected FREEZE_STATE, got {action['v14_action_action_shape']}"

        print(f"  ✓ Shape: {action['v14_action_action_shape']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_ineligible_no_action():
    """Test 7: INELIGIBLE → NO_ACTION."""
    print("\nTest 7: INELIGIBLE → NO_ACTION")
    try:
        from action import (
            build_action_shape_from_bundle_v1,
            ACTION_SHAPE_NO_ACTION,
        )

        bundle = {
            "artifacts": {
                "stress_rule": {
                    "v14_stress_label": "CALM",
                },
                "eligibility": {
                    "v12_eligibility_label": "INELIGIBLE",
                },
            }
        }

        result = build_action_shape_from_bundle_v1(bundle)
        action = result["action_record"]

        assert action["v14_action_action_shape"] == ACTION_SHAPE_NO_ACTION, \
            f"Expected NO_ACTION, got {action['v14_action_action_shape']}"

        print(f"  ✓ Shape: {action['v14_action_action_shape']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_malformed_inputs_defensive():
    """Test 8: Malformed inputs → ERROR record valid + warnings."""
    print("\nTest 8: Malformed inputs → ERROR record valid")
    try:
        from action import (
            build_action_shape_from_bundle_v1,
            ACTION_STATUS_ERROR,
        )

        # Try None input
        result = build_action_shape_from_bundle_v1(None)
        action = result["action_record"]

        assert action["v14_action_status"] == ACTION_STATUS_ERROR, "Expected ERROR status"
        assert len(result["warnings"]) > 0, "Expected warnings"

        print(f"  ✓ Defensive handling: ERROR with {len(result['warnings'])} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_forbidden_vocab_warnings():
    """Test 9: Forbidden vocab injection → warnings."""
    print("\nTest 9: Forbidden vocab injection → warnings")
    try:
        from action import check_action_record

        # Dirty action with forbidden vocabulary
        dirty_action = {
            "v14_action_summary": "You should buy more volatility assets.",
        }

        warnings = check_action_record(dirty_action)
        vocab_warnings = [w for w in warnings if "forbidden vocabulary" in w.lower()]

        assert len(vocab_warnings) > 0, "Expected forbidden vocabulary warnings"

        print(f"  ✓ Forbidden vocabulary detected: {len(vocab_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_token_literal_warnings():
    """Test 10: Token literal injection → warnings."""
    print("\nTest 10: Token literal injection → warnings")
    try:
        from action import check_action_record

        # Dirty action with token literals
        dirty_action = {
            "v14_action_summary": "SUI and USDC action detected.",
        }

        warnings = check_action_record(dirty_action)
        token_warnings = [w for w in warnings if "token literal" in w.lower()]

        assert len(token_warnings) > 0, "Expected token literal warnings"

        print(f"  ✓ Token literals detected: {len(token_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_11_numeric_address_warnings():
    """Test 11: Numeric/address injection → warnings."""
    print("\nTest 11: Numeric/address injection → warnings")
    try:
        from action import check_action_record

        # Dirty action with numerics and addresses
        dirty_action = {
            "v14_action_summary": "Action level is 0.75 or 75% of maximum at address 0x1234.",
        }

        warnings = check_action_record(dirty_action)
        numeric_warnings = [w for w in warnings if "numeric pattern" in w.lower()]
        address_warnings = [w for w in warnings if "address pattern" in w.lower()]

        assert len(numeric_warnings) > 0, "Expected numeric pattern warnings"
        assert len(address_warnings) > 0, "Expected address pattern warnings"

        print(f"  ✓ Numerics and addresses detected: {len(numeric_warnings) + len(address_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_12_coupling_phrase_warnings():
    """Test 12: Coupling phrase injection → warnings."""
    print("\nTest 12: Coupling phrase injection → warnings")
    try:
        from action import check_action_record

        # Dirty action with coupling
        dirty_action = {
            "v14_action_summary": "Stress is STRESSED therefore you should exit.",
        }

        warnings = check_action_record(dirty_action)
        coupling_warnings = [w for w in warnings if "coupling" in w.lower() or "forbidden vocabulary" in w.lower()]

        assert len(coupling_warnings) > 0, "Expected coupling warnings"

        print(f"  ✓ Coupling phrases detected: {len(coupling_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_13_guard_warning_only():
    """Test 13: Guard is warning-only (no exceptions)."""
    print("\nTest 13: Guard is warning-only (no exceptions)")
    try:
        from action import check_action_record

        # Very dirty action with multiple violations
        very_dirty_action = {
            "v14_action_summary": "You must buy SUI at 0.35 ratio because stress is STRESSED so execute trade.",
        }

        # Guard should return warnings, not raise
        warnings = check_action_record(very_dirty_action)

        assert isinstance(warnings, list), "Expected list of warnings"
        assert len(warnings) > 0, "Expected warnings for violations"

        print(f"  ✓ Guard returned {len(warnings)} warnings without raising")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_14_stress_conflict_detection():
    """Test 14: Stress conflict detection (PR146 vs PR145)."""
    print("\nTest 14: Stress conflict detection (PR146 vs PR145)")
    try:
        from action import (
            build_action_shape_from_bundle_v1,
            ACTION_SHAPE_FREEZE_STATE,
        )

        # Bundle with conflicting stress labels
        bundle = {
            "artifacts": {
                "stress_rule": {
                    "v14_stress_label": "STRESSED",  # PR146
                },
                "stress_overlay": {
                    "v14_overlay_band_stress_label": "CALM",  # PR145 (conflict)
                },
                "eligibility": {
                    "v12_eligibility_label": "ELIGIBLE_DRY_RUN_ONLY",
                },
            }
        }

        result = build_action_shape_from_bundle_v1(bundle)
        action = result["action_record"]

        # Should use PR146 (priority)
        assert action["v14_action_action_shape"] == ACTION_SHAPE_FREEZE_STATE, \
            "Expected FREEZE_STATE from PR146"

        # Should have conflict warning
        conflict_warnings = [w for w in result["warnings"] if "conflict" in w.lower()]
        assert len(conflict_warnings) > 0, "Expected conflict warning"

        print(f"  ✓ Conflict detected and PR146 prioritized: {len(conflict_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR147: v1.4 Action Shape Guidance - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_minimal_bundle_unknown,
        test_3_calm_dry_run_observe,
        test_4_tense_consideration_consider,
        test_5_tense_dry_run_simulation,
        test_6_stressed_freeze,
        test_7_ineligible_no_action,
        test_8_malformed_inputs_defensive,
        test_9_forbidden_vocab_warnings,
        test_10_token_literal_warnings,
        test_11_numeric_address_warnings,
        test_12_coupling_phrase_warnings,
        test_13_guard_warning_only,
        test_14_stress_conflict_detection,
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
