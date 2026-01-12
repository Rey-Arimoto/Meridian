#!/usr/bin/env python3
"""
PR126: v1.2 Continuous Permission Monitor v1 Smoke Tests

Purpose:
    Validate continuous permission monitor implementation.

Tests:
    1. Import works
    2. Empty window → ERROR record
    3. Constant permission → STABLE
    4. ALLOW→DRY_RUN_ONLY → DEGRADING + event emitted
    5. DRY_RUN_ONLY→HOLD → SUPPRESSED + event emitted
    6. HOLD→DRY_RUN_ONLY → RECOVERING + event emitted
    7. Guards catch forbidden vocab
    8. No token/numeric/address patterns
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
        from monitor import (
            V12PermissionMonitorSchema,
            get_monitor_schema_info,
            monitor_permission_v1,
            get_monitor_v1_info,
            check_monitor_record,
            check_trajectory_coupling,
            FORBIDDEN_VOCABULARY,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_empty_window_error():
    """Test 2: Empty window → ERROR record."""
    print("\nTest 2: Empty window → ERROR record")
    try:
        from monitor import monitor_permission_v1

        # Test with None
        result = monitor_permission_v1(None)
        assert result["v12_monitor_status"] == "ERROR", "Expected ERROR status for None input"
        assert "v12_monitor_summary" in result
        print(f"  ✓ None input → ERROR: {result['v12_monitor_summary']}")

        # Test with empty list
        result2 = monitor_permission_v1([])
        assert result2["v12_monitor_status"] == "ERROR", "Expected ERROR status for empty list"
        print(f"  ✓ Empty list → ERROR: {result2['v12_monitor_summary']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_constant_permission_stable():
    """Test 3: Constant permission → STABLE."""
    print("\nTest 3: Constant permission → STABLE")
    try:
        from monitor import monitor_permission_v1

        # Constant ALLOW
        window = [
            {"v10_execution_permission": "ALLOW"},
            {"v10_execution_permission": "ALLOW"},
            {"v10_execution_permission": "ALLOW"},
        ]
        result = monitor_permission_v1(window)

        assert result["v12_monitor_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_monitor_current_permission"] == "ALLOW", "Expected ALLOW permission"
        assert result["v12_monitor_suppression_state"] == "STABLE", "Expected STABLE state"
        assert len(result["v12_monitor_transition_events"]) == 0, "Expected no transitions"
        print(f"  ✓ Constant ALLOW → STABLE")
        print(f"    Current permission: {result['v12_monitor_current_permission']}")
        print(f"    Suppression state: {result['v12_monitor_suppression_state']}")
        print(f"    Transitions: {len(result['v12_monitor_transition_events'])}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_allow_to_dry_run_degrading():
    """Test 4: ALLOW→DRY_RUN_ONLY → DEGRADING + event emitted."""
    print("\nTest 4: ALLOW→DRY_RUN_ONLY → DEGRADING + event emitted")
    try:
        from monitor import monitor_permission_v1

        window = [
            {"v10_execution_permission": "ALLOW"},
            {"v10_execution_permission": "DRY_RUN_ONLY"},
        ]
        result = monitor_permission_v1(window)

        assert result["v12_monitor_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_monitor_current_permission"] == "DRY_RUN_ONLY", "Expected DRY_RUN_ONLY"
        assert result["v12_monitor_suppression_state"] == "DEGRADING", "Expected DEGRADING state"
        assert len(result["v12_monitor_transition_events"]) == 1, "Expected 1 transition event"

        event = result["v12_monitor_transition_events"][0]
        assert event["event_type"] == "DEGRADATION", "Expected DEGRADATION event"
        assert event["from_permission"] == "ALLOW", "Expected from ALLOW"
        assert event["to_permission"] == "DRY_RUN_ONLY", "Expected to DRY_RUN_ONLY"

        print(f"  ✓ ALLOW→DRY_RUN_ONLY → DEGRADING")
        print(f"    Event: {event['event_type']}")
        print(f"    From: {event['from_permission']} → To: {event['to_permission']}")
        print(f"    Suppression state: {result['v12_monitor_suppression_state']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_dry_run_to_hold_suppressed():
    """Test 5: DRY_RUN_ONLY→HOLD → SUPPRESSED + event emitted."""
    print("\nTest 5: DRY_RUN_ONLY→HOLD → SUPPRESSED + event emitted")
    try:
        from monitor import monitor_permission_v1

        window = [
            {"v10_execution_permission": "DRY_RUN_ONLY"},
            {"v10_execution_permission": "HOLD"},
        ]
        result = monitor_permission_v1(window)

        assert result["v12_monitor_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_monitor_current_permission"] == "HOLD", "Expected HOLD"
        assert result["v12_monitor_suppression_state"] == "SUPPRESSED", "Expected SUPPRESSED state"
        assert len(result["v12_monitor_transition_events"]) == 1, "Expected 1 transition event"

        event = result["v12_monitor_transition_events"][0]
        assert event["event_type"] == "SUPPRESSION", "Expected SUPPRESSION event"
        assert event["from_permission"] == "DRY_RUN_ONLY", "Expected from DRY_RUN_ONLY"
        assert event["to_permission"] == "HOLD", "Expected to HOLD"

        print(f"  ✓ DRY_RUN_ONLY→HOLD → SUPPRESSED")
        print(f"    Event: {event['event_type']}")
        print(f"    From: {event['from_permission']} → To: {event['to_permission']}")
        print(f"    Suppression state: {result['v12_monitor_suppression_state']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_hold_to_dry_run_recovering():
    """Test 6: HOLD→DRY_RUN_ONLY → RECOVERING + event emitted."""
    print("\nTest 6: HOLD→DRY_RUN_ONLY → RECOVERING + event emitted")
    try:
        from monitor import monitor_permission_v1

        window = [
            {"v10_execution_permission": "HOLD"},
            {"v10_execution_permission": "DRY_RUN_ONLY"},
        ]
        result = monitor_permission_v1(window)

        assert result["v12_monitor_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert result["v12_monitor_current_permission"] == "DRY_RUN_ONLY", "Expected DRY_RUN_ONLY"
        assert result["v12_monitor_suppression_state"] == "RECOVERING", "Expected RECOVERING state"
        assert len(result["v12_monitor_transition_events"]) == 1, "Expected 1 transition event"

        event = result["v12_monitor_transition_events"][0]
        assert event["event_type"] == "RECOVERY", "Expected RECOVERY event"
        assert event["from_permission"] == "HOLD", "Expected from HOLD"
        assert event["to_permission"] == "DRY_RUN_ONLY", "Expected to DRY_RUN_ONLY"

        print(f"  ✓ HOLD→DRY_RUN_ONLY → RECOVERING")
        print(f"    Event: {event['event_type']}")
        print(f"    From: {event['from_permission']} → To: {event['to_permission']}")
        print(f"    Suppression state: {result['v12_monitor_suppression_state']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_guards_catch_forbidden_vocab():
    """Test 7: Guards catch forbidden vocab."""
    print("\nTest 7: Guards catch forbidden vocab")
    try:
        from monitor import check_monitor_record

        # Test with forbidden vocabulary
        dirty_record = {
            "v12_monitor_summary": "permission is good and should execute operations.",
        }
        warnings = check_monitor_record(dirty_record)

        assert len(warnings) > 0, "Expected warnings for forbidden vocabulary"
        print(f"  ✓ Forbidden vocab detected: {len(warnings)} warnings")
        for w in warnings[:3]:  # Show first 3
            print(f"    - {w}")

        # Test clean record
        clean_record = {
            "v12_monitor_summary": "current permission labeled as DRY_RUN_ONLY. suppression state labeled as STABLE.",
        }
        clean_warnings = check_monitor_record(clean_record)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean record, got: {clean_warnings}"
        print(f"  ✓ Clean record passes: {len(clean_warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_no_token_numeric_address_patterns():
    """Test 8: No token/numeric/address patterns."""
    print("\nTest 8: No token/numeric/address patterns")
    try:
        from monitor import check_monitor_record

        # Test with token literals
        token_record = {
            "v12_monitor_summary": "detected transition for SUI and USDC tokens.",
        }
        token_warnings = check_monitor_record(token_record)
        assert len(token_warnings) > 0, "Expected warnings for token literals"
        print(f"  ✓ Token literals detected: {len(token_warnings)} warnings")

        # Test with numeric patterns
        numeric_record = {
            "v12_monitor_summary": "detected 5 transitions in window with 80% confidence.",
        }
        numeric_warnings = check_monitor_record(numeric_record)
        assert len(numeric_warnings) > 0, "Expected warnings for numeric patterns"
        print(f"  ✓ Numeric patterns detected: {len(numeric_warnings)} warnings")

        # Test with address patterns
        address_record = {
            "v12_monitor_summary": "permission changed at address 0x1234567890abcdef.",
        }
        address_warnings = check_monitor_record(address_record)
        assert len(address_warnings) > 0, "Expected warnings for address patterns"
        print(f"  ✓ Address patterns detected: {len(address_warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_trajectory_coupling_guard():
    """Test 9: Trajectory coupling guard (NEW)."""
    print("\nTest 9: Trajectory coupling guard (NEW)")
    try:
        from monitor import check_monitor_record, check_trajectory_coupling

        # Test trajectory coupling patterns
        coupling_patterns = [
            "permission improved therefore execute operation.",
            "state is suppressed so stop operations.",
            "recovering therefore proceed with action.",
            "if permission allowed then execute trade.",
        ]

        for pattern in coupling_patterns:
            warnings = check_trajectory_coupling(pattern)
            assert len(warnings) > 0, f"Expected warnings for: {pattern}"
            print(f"  ✓ Detected coupling: '{pattern[:50]}...'")

        # Test clean text
        clean_text = "current permission labeled as DRY_RUN_ONLY."
        clean_warnings = check_trajectory_coupling(clean_text)
        assert len(clean_warnings) == 0, f"Expected no warnings for clean text, got: {clean_warnings}"
        print(f"  ✓ Clean text passes: no coupling detected")

        # Test full record with coupling
        coupling_record = {
            "v12_monitor_summary": "permission allowed therefore proceed with execution.",
        }
        record_warnings = check_monitor_record(coupling_record)
        assert any("coupling" in w.lower() for w in record_warnings), "Expected trajectory coupling warning"
        print(f"  ✓ Full record validation catches coupling: {len(record_warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR126: v1.2 Continuous Permission Monitor v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_empty_window_error,
        test_3_constant_permission_stable,
        test_4_allow_to_dry_run_degrading,
        test_5_dry_run_to_hold_suppressed,
        test_6_hold_to_dry_run_recovering,
        test_7_guards_catch_forbidden_vocab,
        test_8_no_token_numeric_address_patterns,
        test_9_trajectory_coupling_guard,
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
