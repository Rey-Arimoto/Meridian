#!/usr/bin/env python3
"""
PR127: v1.2 Permission Trajectory Binding v1 Smoke Tests

Purpose:
    Validate permission trajectory signal binding implementation.

Tests:
    1. Import works
    2. Empty/invalid input → ERROR record
    3. Degradation maps correctly
    4. Recovery maps correctly
    5. Suppression maps correctly
    6. Window label is non-numeric (SHORT/MEDIUM/LONG only)
    7. Forbidden vocab detection
    8. Trajectory coupling detection
    9. Warning-only behavior
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from signal import (
            V12PermissionTrajectorySignalSchema,
            get_signal_schema_info,
            bind_permission_trajectory_signal_v1,
            get_binding_v1_info,
            check_signal_record,
            check_signal_trajectory_coupling,
            FORBIDDEN_VOCABULARY,
        )
        from explain.v12_explain_context_permission_trajectory_extension import (
            extend_explanation_context_with_trajectory_signals,
            get_trajectory_signal_types,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_empty_invalid_input_error():
    """Test 2: Empty/invalid input → ERROR record."""
    print("\nTest 2: Empty/invalid input → ERROR record")
    try:
        from signal import bind_permission_trajectory_signal_v1

        # Test with None
        result = bind_permission_trajectory_signal_v1(None)
        assert result["v12_signal_status"] == "ERROR", "Expected ERROR status for None input"
        assert "v12_signal_summary" in result
        print(f"  ✓ None input → ERROR: {result['v12_signal_summary']}")

        # Test with ERROR monitor
        monitor_error = {
            "v12_monitor_status": "ERROR",
            "v12_monitor_summary": "monitor error",
        }
        result2 = bind_permission_trajectory_signal_v1(monitor_error)
        assert result2["v12_signal_status"] == "ERROR", "Expected ERROR status for ERROR monitor"
        print(f"  ✓ ERROR monitor → ERROR signal: {result2['v12_signal_summary']}")

        # Test with UNAVAILABLE monitor
        monitor_unavail = {
            "v12_monitor_status": "UNAVAILABLE",
        }
        result3 = bind_permission_trajectory_signal_v1(monitor_unavail)
        assert result3["v12_signal_status"] == "ERROR", "Expected ERROR status for UNAVAILABLE monitor"
        print(f"  ✓ UNAVAILABLE monitor → ERROR signal")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_degradation_maps_correctly():
    """Test 3: Degradation maps correctly."""
    print("\nTest 3: Degradation maps correctly")
    try:
        from signal import bind_permission_trajectory_signal_v1

        monitor = {
            "v12_monitor_status": "AVAILABLE",
            "v12_monitor_current_permission": "DRY_RUN_ONLY",
            "v12_monitor_suppression_state": "DEGRADING",
            "v12_monitor_transition_events": [
                {
                    "event_type": "DEGRADATION",
                    "from_permission": "ALLOW",
                    "to_permission": "DRY_RUN_ONLY",
                }
            ],
            "v12_monitor_window": "MEDIUM",
        }
        result = bind_permission_trajectory_signal_v1(monitor)

        assert result["v12_signal_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_signal_permission_level"] == "DRY_RUN_ONLY", "Expected DRY_RUN_ONLY level"
        assert result["v12_signal_suppression_state"] == "DEGRADING", "Expected DEGRADING state"
        assert result["v12_signal_transition_label"] == "DEGRADATION", "Expected DEGRADATION label"
        assert result["v12_signal_window_label"] == "MEDIUM", "Expected MEDIUM window"

        print(f"  ✓ DEGRADATION mapped correctly")
        print(f"    Permission level: {result['v12_signal_permission_level']}")
        print(f"    Suppression state: {result['v12_signal_suppression_state']}")
        print(f"    Transition label: {result['v12_signal_transition_label']}")
        print(f"    Summary: {result['v12_signal_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_recovery_maps_correctly():
    """Test 4: Recovery maps correctly."""
    print("\nTest 4: Recovery maps correctly")
    try:
        from signal import bind_permission_trajectory_signal_v1

        monitor = {
            "v12_monitor_status": "AVAILABLE",
            "v12_monitor_current_permission": "DRY_RUN_ONLY",
            "v12_monitor_suppression_state": "RECOVERING",
            "v12_monitor_transition_events": [
                {
                    "event_type": "RECOVERY",
                    "from_permission": "HOLD",
                    "to_permission": "DRY_RUN_ONLY",
                }
            ],
            "v12_monitor_window": "SHORT",
        }
        result = bind_permission_trajectory_signal_v1(monitor)

        assert result["v12_signal_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_signal_permission_level"] == "DRY_RUN_ONLY", "Expected DRY_RUN_ONLY level"
        assert result["v12_signal_suppression_state"] == "RECOVERING", "Expected RECOVERING state"
        assert result["v12_signal_transition_label"] == "RECOVERY", "Expected RECOVERY label"
        assert result["v12_signal_window_label"] == "SHORT", "Expected SHORT window"

        print(f"  ✓ RECOVERY mapped correctly")
        print(f"    Permission level: {result['v12_signal_permission_level']}")
        print(f"    Suppression state: {result['v12_signal_suppression_state']}")
        print(f"    Transition label: {result['v12_signal_transition_label']}")
        print(f"    Window: {result['v12_signal_window_label']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_suppression_maps_correctly():
    """Test 5: Suppression maps correctly."""
    print("\nTest 5: Suppression maps correctly")
    try:
        from signal import bind_permission_trajectory_signal_v1

        monitor = {
            "v12_monitor_status": "AVAILABLE",
            "v12_monitor_current_permission": "HOLD",
            "v12_monitor_suppression_state": "SUPPRESSED",
            "v12_monitor_transition_events": [
                {
                    "event_type": "SUPPRESSION",
                    "from_permission": "DRY_RUN_ONLY",
                    "to_permission": "HOLD",
                }
            ],
            "v12_monitor_window": "LONG",
        }
        result = bind_permission_trajectory_signal_v1(monitor)

        assert result["v12_signal_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_signal_permission_level"] == "HOLD", "Expected HOLD level"
        assert result["v12_signal_suppression_state"] == "SUPPRESSED", "Expected SUPPRESSED state"
        assert result["v12_signal_transition_label"] == "SUPPRESSION", "Expected SUPPRESSION label"
        assert result["v12_signal_window_label"] == "LONG", "Expected LONG window"

        print(f"  ✓ SUPPRESSION mapped correctly")
        print(f"    Permission level: {result['v12_signal_permission_level']}")
        print(f"    Suppression state: {result['v12_signal_suppression_state']}")
        print(f"    Transition label: {result['v12_signal_transition_label']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_window_label_non_numeric():
    """Test 6: Window label is non-numeric (SHORT/MEDIUM/LONG only)."""
    print("\nTest 6: Window label is non-numeric (SHORT/MEDIUM/LONG only)")
    try:
        from signal import V12PermissionTrajectorySignalSchema

        valid_windows = V12PermissionTrajectorySignalSchema.VALID_WINDOW_LABELS
        assert valid_windows == ["SHORT", "MEDIUM", "LONG"], "Expected SHORT/MEDIUM/LONG only"

        # Verify no numeric patterns
        for window in valid_windows:
            assert not any(c.isdigit() for c in window), f"Window label '{window}' contains digits"

        print(f"  ✓ Window labels are non-numeric: {valid_windows}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_forbidden_vocab_detection():
    """Test 7: Forbidden vocab detection."""
    print("\nTest 7: Forbidden vocab detection")
    try:
        from signal import check_signal_record

        # Test with forbidden vocabulary
        dirty_record = {
            "v12_signal_summary": "permission is good and should execute operations.",
        }
        warnings = check_signal_record(dirty_record)

        assert len(warnings) > 0, "Expected warnings for forbidden vocabulary"
        print(f"  ✓ Forbidden vocab detected: {len(warnings)} warnings")
        for w in warnings[:3]:  # Show first 3
            print(f"    - {w}")

        # Test clean record
        clean_record = {
            "v12_signal_summary": "permission level labeled as DRY_RUN_ONLY. suppression state labeled as STABLE.",
        }
        clean_warnings = check_signal_record(clean_record)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean record, got: {clean_warnings}"
        print(f"  ✓ Clean record passes: {len(clean_warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_trajectory_coupling_detection():
    """Test 8: Trajectory coupling detection."""
    print("\nTest 8: Trajectory coupling detection")
    try:
        from signal import check_signal_record, check_signal_trajectory_coupling

        # Test trajectory coupling patterns
        coupling_patterns = [
            "permission level improved therefore execute operation.",
            "state degrading so halt operations.",
            "recovering means proceed with action.",
            "if stable then execute trade.",
        ]

        for pattern in coupling_patterns:
            warnings = check_signal_trajectory_coupling(pattern)
            assert len(warnings) > 0, f"Expected warnings for: {pattern}"
            print(f"  ✓ Detected coupling: '{pattern[:50]}...'")

        # Test clean text
        clean_text = "permission level labeled as DRY_RUN_ONLY."
        clean_warnings = check_signal_trajectory_coupling(clean_text)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean text, got: {clean_warnings}"
        print(f"  ✓ Clean text passes: no coupling detected")

        # Test full record with coupling
        coupling_record = {
            "v12_signal_summary": "level improved therefore proceed with execution.",
        }
        record_warnings = check_signal_record(coupling_record)
        assert any("coupling" in w.lower() for w in record_warnings), "Expected trajectory coupling warning"
        print(f"  ✓ Full record validation catches coupling: {len(record_warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_warning_only_behavior():
    """Test 9: Warning-only behavior."""
    print("\nTest 9: Warning-only behavior")
    try:
        from signal import check_signal_record

        # Test that guards never raise exceptions
        dirty_records = [
            {"v12_signal_summary": "permission with SUI and USDC tokens."},
            {"v12_signal_summary": "detected 5 transitions with 80% confidence."},
            {"v12_signal_summary": "address 0x1234567890abcdef."},
            {"v12_signal_summary": "permission good therefore execute."},
        ]

        for record in dirty_records:
            try:
                warnings = check_signal_record(record)
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
    print("PR127: v1.2 Permission Trajectory Binding v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_empty_invalid_input_error,
        test_3_degradation_maps_correctly,
        test_4_recovery_maps_correctly,
        test_5_suppression_maps_correctly,
        test_6_window_label_non_numeric,
        test_7_forbidden_vocab_detection,
        test_8_trajectory_coupling_detection,
        test_9_warning_only_behavior,
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
