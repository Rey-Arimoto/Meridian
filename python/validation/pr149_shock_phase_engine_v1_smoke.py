#!/usr/bin/env python3
"""
PR149: v1.4 Shock Phase Detection Engine v1 Smoke Tests

Purpose:
    Validate v1.4 shock phase detection engine.

Tests:
    1. Import works
    2. Empty bundle → UNKNOWN (not raise)
    3. Invalid shapes → ERROR + warnings
    4. PRE_SHOCK detection (liquidity_thinning + impulse)
    5. DOWN_SHOCK detection (impulse_down + bid_absorption)
    6. UP_SHOCK detection (impulse_up + ask_absorption)
    7. DOWN_REVERSAL detection (prev down_shock + impulse_up + agg_buy)
    8. UP_REVERSAL detection (prev up_shock + impulse_down + agg_sell)
    9. RECOVERY detection (prev reversal + flat + no_absorption)
    10. NORMAL fallback (impulse present but no rule)
    11. Guard catches forbidden vocab in notes
    12. Defensive: unknown labels in observations → UNKNOWN + warning
    13. Phase direction determination
    14. Observation presence tracking
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            get_shock_phase_engine_v1_info,
            V14ShockPhaseSchema,
            check_shock_record,
            SHOCK_STATUS_AVAILABLE,
            SHOCK_STATUS_UNKNOWN,
            SHOCK_STATUS_ERROR,
            PHASE_UNKNOWN,
            PHASE_NORMAL,
            PHASE_PRE_SHOCK,
            PHASE_UP_SHOCK,
            PHASE_DOWN_SHOCK,
            PHASE_UP_REVERSAL,
            PHASE_DOWN_REVERSAL,
            PHASE_RECOVERY,
            PHASE_ERROR,
            DIRECTION_UP,
            DIRECTION_DOWN,
            DIRECTION_NONE,
            IMPULSE_UP,
            IMPULSE_DOWN,
            IMPULSE_FLAT,
            ASK_ABSORPTION,
            BID_ABSORPTION,
            NO_ABSORPTION,
            AGG_BUY_DOMINANCE,
            AGG_SELL_DOMINANCE,
            FLOW_BALANCED,
            LIQUIDITY_THINNING,
            LIQUIDITY_OK,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_empty_bundle_unknown():
    """Test 2: Empty bundle → UNKNOWN (not raise)."""
    print("\nTest 2: Empty bundle → UNKNOWN (not raise)")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            SHOCK_STATUS_UNKNOWN,
            PHASE_UNKNOWN,
        )

        # Empty bundle
        bundle = {}

        result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        assert shock_record["v14_shock_status"] == SHOCK_STATUS_UNKNOWN, "Expected UNKNOWN status"
        assert shock_record["v14_shock_phase_label"] == PHASE_UNKNOWN, "Expected UNKNOWN phase"
        assert len(result["warnings"]) > 0, "Expected warnings"

        print(f"  ✓ UNKNOWN with {len(result['warnings'])} warning(s)")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_invalid_shapes_error():
    """Test 3: Invalid shapes → ERROR + warnings."""
    print("\nTest 3: Invalid shapes → ERROR + warnings")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            SHOCK_STATUS_ERROR,
            PHASE_ERROR,
        )

        # Invalid bundle (None)
        result = detect_shock_phase_from_bundle_v1(None, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        assert shock_record["v14_shock_status"] == SHOCK_STATUS_ERROR, "Expected ERROR status"
        assert shock_record["v14_shock_phase_label"] == PHASE_ERROR, "Expected ERROR phase"
        assert len(result["warnings"]) > 0, "Expected warnings"

        print(f"  ✓ ERROR with {len(result['warnings'])} warning(s)")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_pre_shock_detection():
    """Test 4: PRE_SHOCK detection (liquidity_thinning + impulse)."""
    print("\nTest 4: PRE_SHOCK detection")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            PHASE_PRE_SHOCK,
            DIRECTION_NONE,
            IMPULSE_UP,
            AGG_BUY_DOMINANCE,
            NO_ABSORPTION,
            LIQUIDITY_THINNING,
        )

        bundle = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": IMPULSE_UP,
                        "absorption_label": NO_ABSORPTION,
                        "flow_dominance_label": AGG_BUY_DOMINANCE,
                        "liquidity_thinning_label": LIQUIDITY_THINNING,
                    }
                }
            }
        }

        result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        assert shock_record["v14_shock_phase_label"] == PHASE_PRE_SHOCK, \
            f"Expected PRE_SHOCK, got {shock_record['v14_shock_phase_label']}"
        assert shock_record["v14_shock_phase_direction"] == DIRECTION_NONE, "Expected NONE direction"

        print(f"  ✓ PRE_SHOCK detected with direction: {shock_record['v14_shock_phase_direction']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_down_shock_detection():
    """Test 5: DOWN_SHOCK detection (impulse_down + bid_absorption)."""
    print("\nTest 5: DOWN_SHOCK detection")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            PHASE_DOWN_SHOCK,
            DIRECTION_DOWN,
            IMPULSE_DOWN,
            BID_ABSORPTION,
            AGG_SELL_DOMINANCE,
            LIQUIDITY_OK,
        )

        bundle = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": IMPULSE_DOWN,
                        "absorption_label": BID_ABSORPTION,
                        "flow_dominance_label": AGG_SELL_DOMINANCE,
                        "liquidity_thinning_label": LIQUIDITY_OK,
                    }
                }
            }
        }

        result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        assert shock_record["v14_shock_phase_label"] == PHASE_DOWN_SHOCK, \
            f"Expected DOWN_SHOCK, got {shock_record['v14_shock_phase_label']}"
        assert shock_record["v14_shock_phase_direction"] == DIRECTION_DOWN, "Expected DOWN direction"

        print(f"  ✓ DOWN_SHOCK detected with direction: {shock_record['v14_shock_phase_direction']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_up_shock_detection():
    """Test 6: UP_SHOCK detection (impulse_up + ask_absorption)."""
    print("\nTest 6: UP_SHOCK detection")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            PHASE_UP_SHOCK,
            DIRECTION_UP,
            IMPULSE_UP,
            ASK_ABSORPTION,
            AGG_BUY_DOMINANCE,
            LIQUIDITY_OK,
        )

        bundle = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": IMPULSE_UP,
                        "absorption_label": ASK_ABSORPTION,
                        "flow_dominance_label": AGG_BUY_DOMINANCE,
                        "liquidity_thinning_label": LIQUIDITY_OK,
                    }
                }
            }
        }

        result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        assert shock_record["v14_shock_phase_label"] == PHASE_UP_SHOCK, \
            f"Expected UP_SHOCK, got {shock_record['v14_shock_phase_label']}"
        assert shock_record["v14_shock_phase_direction"] == DIRECTION_UP, "Expected UP direction"

        print(f"  ✓ UP_SHOCK detected with direction: {shock_record['v14_shock_phase_direction']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_down_reversal_detection():
    """Test 7: DOWN_REVERSAL detection (prev down_shock + impulse_up + agg_buy)."""
    print("\nTest 7: DOWN_REVERSAL detection")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            PHASE_DOWN_REVERSAL,
            PHASE_DOWN_SHOCK,
            DIRECTION_DOWN,
            IMPULSE_UP,
            NO_ABSORPTION,
            AGG_BUY_DOMINANCE,
            LIQUIDITY_OK,
        )

        bundle = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": IMPULSE_UP,
                        "absorption_label": NO_ABSORPTION,
                        "flow_dominance_label": AGG_BUY_DOMINANCE,
                        "liquidity_thinning_label": LIQUIDITY_OK,
                        "shock_state_memory": {
                            "prev_phase": PHASE_DOWN_SHOCK,
                            "prev_phase_age_label": "SHORT",
                        },
                    }
                }
            }
        }

        result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        assert shock_record["v14_shock_phase_label"] == PHASE_DOWN_REVERSAL, \
            f"Expected DOWN_REVERSAL, got {shock_record['v14_shock_phase_label']}"
        assert shock_record["v14_shock_phase_direction"] == DIRECTION_DOWN, "Expected DOWN direction"

        print(f"  ✓ DOWN_REVERSAL detected with direction: {shock_record['v14_shock_phase_direction']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_up_reversal_detection():
    """Test 8: UP_REVERSAL detection (prev up_shock + impulse_down + agg_sell)."""
    print("\nTest 8: UP_REVERSAL detection")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            PHASE_UP_REVERSAL,
            PHASE_UP_SHOCK,
            DIRECTION_UP,
            IMPULSE_DOWN,
            NO_ABSORPTION,
            AGG_SELL_DOMINANCE,
            LIQUIDITY_OK,
        )

        bundle = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": IMPULSE_DOWN,
                        "absorption_label": NO_ABSORPTION,
                        "flow_dominance_label": AGG_SELL_DOMINANCE,
                        "liquidity_thinning_label": LIQUIDITY_OK,
                        "shock_state_memory": {
                            "prev_phase": PHASE_UP_SHOCK,
                            "prev_phase_age_label": "SHORT",
                        },
                    }
                }
            }
        }

        result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        assert shock_record["v14_shock_phase_label"] == PHASE_UP_REVERSAL, \
            f"Expected UP_REVERSAL, got {shock_record['v14_shock_phase_label']}"
        assert shock_record["v14_shock_phase_direction"] == DIRECTION_UP, "Expected UP direction"

        print(f"  ✓ UP_REVERSAL detected with direction: {shock_record['v14_shock_phase_direction']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_recovery_detection():
    """Test 9: RECOVERY detection (prev reversal + flat + no_absorption)."""
    print("\nTest 9: RECOVERY detection")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            PHASE_RECOVERY,
            PHASE_DOWN_REVERSAL,
            DIRECTION_NONE,
            IMPULSE_FLAT,
            NO_ABSORPTION,
            FLOW_BALANCED,
            LIQUIDITY_OK,
        )

        bundle = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": IMPULSE_FLAT,
                        "absorption_label": NO_ABSORPTION,
                        "flow_dominance_label": FLOW_BALANCED,
                        "liquidity_thinning_label": LIQUIDITY_OK,
                        "shock_state_memory": {
                            "prev_phase": PHASE_DOWN_REVERSAL,
                            "prev_phase_age_label": "SHORT",
                        },
                    }
                }
            }
        }

        result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        assert shock_record["v14_shock_phase_label"] == PHASE_RECOVERY, \
            f"Expected RECOVERY, got {shock_record['v14_shock_phase_label']}"
        assert shock_record["v14_shock_phase_direction"] == DIRECTION_NONE, "Expected NONE direction"

        print(f"  ✓ RECOVERY detected with direction: {shock_record['v14_shock_phase_direction']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_normal_fallback():
    """Test 10: NORMAL fallback (impulse present but no rule)."""
    print("\nTest 10: NORMAL fallback")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            PHASE_NORMAL,
            DIRECTION_NONE,
            IMPULSE_FLAT,
            NO_ABSORPTION,
            FLOW_BALANCED,
            LIQUIDITY_OK,
        )

        bundle = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": IMPULSE_FLAT,
                        "absorption_label": NO_ABSORPTION,
                        "flow_dominance_label": FLOW_BALANCED,
                        "liquidity_thinning_label": LIQUIDITY_OK,
                    }
                }
            }
        }

        result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        assert shock_record["v14_shock_phase_label"] == PHASE_NORMAL, \
            f"Expected NORMAL, got {shock_record['v14_shock_phase_label']}"
        assert shock_record["v14_shock_phase_direction"] == DIRECTION_NONE, "Expected NONE direction"

        print(f"  ✓ NORMAL fallback with direction: {shock_record['v14_shock_phase_direction']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_11_guard_forbidden_vocab():
    """Test 11: Guard catches forbidden vocab in notes."""
    print("\nTest 11: Guard catches forbidden vocab in notes")
    try:
        from shock import check_shock_record

        # Dirty shock with forbidden vocabulary
        dirty_shock = {
            "v14_shock_notes": ["You should execute sell trade immediately."],
        }

        warnings = check_shock_record(dirty_shock)
        vocab_warnings = [w for w in warnings if "forbidden vocabulary" in w.lower()]

        assert len(vocab_warnings) > 0, "Expected forbidden vocabulary warnings"

        print(f"  ✓ Forbidden vocabulary detected: {len(vocab_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_12_defensive_unknown_labels():
    """Test 12: Defensive: unknown labels in observations → UNKNOWN + warning."""
    print("\nTest 12: Defensive: unknown labels in observations → UNKNOWN + warning")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            SHOCK_STATUS_UNKNOWN,
            PHASE_UNKNOWN,
            IMPULSE_UNKNOWN,
        )

        # Bundle with all UNKNOWN labels
        bundle = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": IMPULSE_UNKNOWN,
                        "absorption_label": "ABSORPTION_UNKNOWN",
                        "flow_dominance_label": "FLOW_UNKNOWN",
                        "liquidity_thinning_label": "LIQUIDITY_UNKNOWN",
                    }
                }
            }
        }

        result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        assert shock_record["v14_shock_status"] == SHOCK_STATUS_UNKNOWN, "Expected UNKNOWN status"
        assert shock_record["v14_shock_phase_label"] == PHASE_UNKNOWN, "Expected UNKNOWN phase"
        assert len(result["warnings"]) > 0, "Expected warnings"

        print(f"  ✓ UNKNOWN with {len(result['warnings'])} warning(s)")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_13_phase_direction_determination():
    """Test 13: Phase direction determination."""
    print("\nTest 13: Phase direction determination")
    try:
        from shock import (
            detect_shock_phase_from_bundle_v1,
            DIRECTION_UP,
            DIRECTION_DOWN,
            DIRECTION_NONE,
        )

        # Test UP direction (UP_SHOCK)
        bundle_up = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": "IMPULSE_UP",
                        "absorption_label": "ASK_ABSORPTION",
                        "flow_dominance_label": "AGG_BUY_DOMINANCE",
                        "liquidity_thinning_label": "LIQUIDITY_OK",
                    }
                }
            }
        }

        result_up = detect_shock_phase_from_bundle_v1(bundle_up, "deep:wBTC/USDC")
        assert result_up["shock_record"]["v14_shock_phase_direction"] == DIRECTION_UP, "Expected UP direction"

        # Test DOWN direction (DOWN_SHOCK)
        bundle_down = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": "IMPULSE_DOWN",
                        "absorption_label": "BID_ABSORPTION",
                        "flow_dominance_label": "AGG_SELL_DOMINANCE",
                        "liquidity_thinning_label": "LIQUIDITY_OK",
                    }
                }
            }
        }

        result_down = detect_shock_phase_from_bundle_v1(bundle_down, "deep:wBTC/USDC")
        assert result_down["shock_record"]["v14_shock_phase_direction"] == DIRECTION_DOWN, "Expected DOWN direction"

        # Test NONE direction (NORMAL)
        bundle_none = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": "IMPULSE_FLAT",
                        "absorption_label": "NO_ABSORPTION",
                        "flow_dominance_label": "FLOW_BALANCED",
                        "liquidity_thinning_label": "LIQUIDITY_OK",
                    }
                }
            }
        }

        result_none = detect_shock_phase_from_bundle_v1(bundle_none, "deep:wBTC/USDC")
        assert result_none["shock_record"]["v14_shock_phase_direction"] == DIRECTION_NONE, "Expected NONE direction"

        print(f"  ✓ Direction determination: UP, DOWN, NONE")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_14_observation_presence_tracking():
    """Test 14: Observation presence tracking."""
    print("\nTest 14: Observation presence tracking")
    try:
        from shock import detect_shock_phase_from_bundle_v1

        bundle = {
            "artifacts": {
                "observations": {
                    "deep:wBTC/USDC": {
                        "price_impulse_label": "IMPULSE_FLAT",
                        "absorption_label": "NO_ABSORPTION",
                        "flow_dominance_label": "FLOW_BALANCED",
                        "liquidity_thinning_label": "LIQUIDITY_OK",
                    }
                }
            }
        }

        result = detect_shock_phase_from_bundle_v1(bundle, "deep:wBTC/USDC")
        shock_record = result["shock_record"]

        observation_presence = shock_record["v14_shock_observation_presence"]

        assert "price_impulse" in observation_presence, "Expected price_impulse presence"
        assert "absorption" in observation_presence, "Expected absorption presence"
        assert "flow_dominance" in observation_presence, "Expected flow_dominance presence"
        assert "liquidity_thinning" in observation_presence, "Expected liquidity_thinning presence"

        assert observation_presence["price_impulse"] == True, "Expected price_impulse present"
        assert observation_presence["absorption"] == True, "Expected absorption present"
        assert observation_presence["flow_dominance"] == True, "Expected flow_dominance present"
        assert observation_presence["liquidity_thinning"] == True, "Expected liquidity_thinning present"

        print(f"  ✓ Observation presence tracked: {sum(observation_presence.values())}/{len(observation_presence)} present")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR149: v1.4 Shock Phase Detection Engine - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_empty_bundle_unknown,
        test_3_invalid_shapes_error,
        test_4_pre_shock_detection,
        test_5_down_shock_detection,
        test_6_up_shock_detection,
        test_7_down_reversal_detection,
        test_8_up_reversal_detection,
        test_9_recovery_detection,
        test_10_normal_fallback,
        test_11_guard_forbidden_vocab,
        test_12_defensive_unknown_labels,
        test_13_phase_direction_determination,
        test_14_observation_presence_tracking,
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
