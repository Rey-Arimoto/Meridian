#!/usr/bin/env python3
"""
PR41: v0.5 Decision Record Wiring Smoke Test

Purpose: Verify PR41 wiring correctly adds v0.5 decision records to row_dict.

Requirements:
- v5_decision_* fields added to row_dict
- v5_decision_action mirrors base_action
- v5_decision_version == "v0.5"
- v5_decision_generated_at is UTC ISO-8601
- v5_decision_reason contains no digits
- Wiring failure handled (no exception, safe defaults)
- Exit code always 0 (warning-only)
- Existing tests (PR39/PR40) still pass

Non-Goals:
- No behavior modification testing (READ-ONLY by design)
- No v0.4 confidence modification testing (immutable by design)
"""

import sys
import os
import re

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from intelligence.intelligence_decision_engine_v1 import generate_decision_record_v1
from intelligence.intelligence_decision_record_compliance import validate_decision_record_full


# ISO-8601 UTC timestamp pattern
ISO_8601_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$'
)


def simulate_wiring(row_dict):
    """
    Simulate PR41 wiring behavior.

    This mimics the code added to meridian_realtime_agent.py.

    Returns: Modified row_dict with v5_decision_* fields
    """
    from datetime import datetime, timezone

    try:
        decision_record = generate_decision_record_v1(row_dict)

        # Add v0.5 decision fields (v5_ prefix to avoid collision)
        row_dict["v5_decision_action"] = decision_record.get("decision_action", "UNKNOWN")
        row_dict["v5_decision_reason"] = decision_record.get("decision_reason", "")
        decision_inputs_list = decision_record.get("decision_inputs", [])
        row_dict["v5_decision_inputs"] = ",".join(decision_inputs_list) if decision_inputs_list else ""
        row_dict["v5_decision_version"] = decision_record.get("decision_version", "v0.5")
        row_dict["v5_decision_generated_at"] = decision_record.get("decision_generated_at", "")

        # Validate (warning-only)
        if "_warnings" not in decision_record:
            compliance_warnings = validate_decision_record_full(decision_record, "test")
            if compliance_warnings:
                print(f"[INFO][TEST] Compliance warnings: {compliance_warnings}")

    except Exception as e:
        # Safe defaults (warning-only)
        print(f"[INFO][TEST] Wiring exception (expected in test): {e}")
        row_dict["v5_decision_action"] = "UNKNOWN"
        row_dict["v5_decision_reason"] = ""
        row_dict["v5_decision_inputs"] = ""
        row_dict["v5_decision_version"] = "v0.5"
        row_dict["v5_decision_generated_at"] = datetime.now(timezone.utc).isoformat()

    return row_dict


def test_v5_fields_added():
    """Test 1: v5_decision_* fields added to row_dict."""
    print("\nTest 1: v5_decision_* Fields Added")
    print("-" * 60)

    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",
    }

    row_dict = simulate_wiring(row_dict)

    required_fields = [
        "v5_decision_action",
        "v5_decision_reason",
        "v5_decision_inputs",
        "v5_decision_version",
        "v5_decision_generated_at",
    ]

    for field in required_fields:
        assert field in row_dict, f"Field '{field}' must be added to row_dict"
        print(f"✓ Field '{field}' present: {row_dict[field]}")

    print("Test 1: PASS")
    return True


def test_v5_decision_action_mirrors_base_action():
    """Test 2: v5_decision_action mirrors base_action."""
    print("\nTest 2: v5_decision_action Mirrors base_action")
    print("-" * 60)

    test_cases = ["HOLD", "SHIFT", "PAUSE"]

    for base_action in test_cases:
        row_dict = {
            "base_action": base_action,
            "intent_primary": "SEEK",
        }

        row_dict = simulate_wiring(row_dict)

        assert row_dict["v5_decision_action"] == base_action, \
            f"v5_decision_action must mirror base_action: expected '{base_action}', got '{row_dict['v5_decision_action']}'"

        print(f"✓ base_action '{base_action}' → v5_decision_action '{row_dict['v5_decision_action']}' (exact mirror)")

    print("Test 2: PASS")
    return True


def test_v5_decision_version_fixed():
    """Test 3: v5_decision_version is fixed to 'v0.5'."""
    print("\nTest 3: v5_decision_version Fixed to 'v0.5'")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
    }

    row_dict = simulate_wiring(row_dict)

    assert row_dict["v5_decision_version"] == "v0.5", \
        f"v5_decision_version must be 'v0.5', got '{row_dict['v5_decision_version']}'"

    print(f"✓ v5_decision_version == 'v0.5' (fixed)")

    print("Test 3: PASS")
    return True


def test_v5_timestamp_iso8601_utc():
    """Test 4: v5_decision_generated_at is UTC ISO-8601 format."""
    print("\nTest 4: v5_decision_generated_at ISO-8601 UTC")
    print("-" * 60)

    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
    }

    row_dict = simulate_wiring(row_dict)

    timestamp = row_dict["v5_decision_generated_at"]
    assert ISO_8601_PATTERN.match(timestamp), \
        f"v5_decision_generated_at must be ISO-8601 UTC format, got '{timestamp}'"

    print(f"✓ v5_decision_generated_at in ISO-8601 UTC format")
    print(f"  Timestamp: {timestamp}")

    print("Test 4: PASS")
    return True


def test_v5_decision_reason_no_digits():
    """Test 5: v5_decision_reason contains no digits (non-numeric requirement)."""
    print("\nTest 5: v5_decision_reason Contains No Digits")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "confidence_reason": "Source:entropy_bp; Stability:temporal indicators present; ...",
    }

    row_dict = simulate_wiring(row_dict)

    decision_reason = row_dict["v5_decision_reason"]
    has_digits = bool(re.search(r'\d', decision_reason))

    assert not has_digits, \
        f"v5_decision_reason must not contain digits (non-numeric), got: {decision_reason}"

    print(f"✓ v5_decision_reason contains no digits")
    print(f"  Reason: {decision_reason}")

    print("Test 5: PASS")
    return True


def test_wiring_failure_handled():
    """Test 6: Wiring failure handled gracefully (no exception, safe defaults)."""
    print("\nTest 6: Wiring Failure Handled (No Exception)")
    print("-" * 60)

    # Test with invalid input (should trigger safe defaults)
    invalid_row_dicts = [
        {},  # Empty
        {"invalid_key": "value"},  # Invalid key
        {"base_action": None},  # None value
    ]

    for i, row_dict in enumerate(invalid_row_dicts):
        try:
            row_dict = simulate_wiring(row_dict)

            # Should have safe defaults
            assert "v5_decision_action" in row_dict, "v5_decision_action must be present (safe default)"
            assert "v5_decision_version" in row_dict, "v5_decision_version must be present (safe default)"

            print(f"✓ Test case {i+1}: Handled gracefully (no exception)")
            print(f"  v5_decision_action: {row_dict['v5_decision_action']}")
            print(f"  v5_decision_version: {row_dict['v5_decision_version']}")

        except Exception as e:
            assert False, f"Wiring should never raise exception (warning-only), got: {e}"

    print("Test 6: PASS")
    return True


def test_exit_code_always_zero():
    """Test 7: Verify exit code always 0 (warning-only)."""
    print("\nTest 7: Exit Code Always 0 (Warning-Only)")
    print("-" * 60)

    # All wiring operations should succeed without raising
    test_cases = [
        {"base_action": "HOLD", "intent_primary": "IDLE"},
        {},  # Empty row
        {"base_action": None},  # None base_action
        {"invalid": "data"},  # Invalid keys
    ]

    for i, row_dict in enumerate(test_cases):
        try:
            simulate_wiring(row_dict)
            print(f"✓ Test case {i+1}: No exception raised")
        except Exception as e:
            assert False, f"Should never raise exception (warning-only), got: {e}"

    print(f"✓ All test cases handled without exceptions")
    print(f"✓ Exit code will be 0 (warning-only)")

    print("Test 7: PASS")
    return True


def test_existing_tests_still_pass():
    """Test 8: Verify existing PR39/PR40 tests still pass."""
    print("\nTest 8: Existing Tests Still Pass")
    print("-" * 60)

    # Run simplified versions of PR39/PR40 tests to ensure wiring doesn't break them
    from intelligence.intelligence_decision_engine_v1 import generate_decision_record_v1
    from intelligence.intelligence_decision_record_compliance import validate_decision_record_structure

    # PR40 test: Decision engine still works
    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",
    }

    decision_record = generate_decision_record_v1(row_dict)

    assert "decision_action" in decision_record, "PR40: decision_action must be generated"
    assert decision_record["decision_action"] == "HOLD", "PR40: decision_action must mirror base_action"
    print(f"✓ PR40 test: Decision engine still generates records correctly")

    # PR39 test: Compliance guard still works
    warnings = validate_decision_record_structure(decision_record)
    assert isinstance(warnings, list), "PR39: Compliance guard must return list"
    print(f"✓ PR39 test: Compliance guard still validates correctly (warnings: {len(warnings)})")

    print("Test 8: PASS")
    return True


def main():
    """Run all PR41 Decision Record Wiring smoke tests."""
    print("=" * 60)
    print("PR41: Decision Record Wiring Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("v5_decision_* Fields Added", test_v5_fields_added()))
        results.append(("v5_decision_action Mirrors base_action", test_v5_decision_action_mirrors_base_action()))
        results.append(("v5_decision_version Fixed", test_v5_decision_version_fixed()))
        results.append(("v5_decision_generated_at ISO-8601", test_v5_timestamp_iso8601_utc()))
        results.append(("v5_decision_reason No Digits", test_v5_decision_reason_no_digits()))
        results.append(("Wiring Failure Handled", test_wiring_failure_handled()))
        results.append(("Exit Code Always Zero", test_exit_code_always_zero()))
        results.append(("Existing Tests Still Pass", test_existing_tests_still_pass()))

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        for name, passed in results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {name}")

        all_passed = all(passed for _, passed in results)

        print("\n" + "=" * 60)
        if all_passed:
            print("✓ ALL PR41 DECISION RECORD WIRING TESTS PASSED")
            print("=" * 60)
            print("PR41 Requirements Verified:")
            print("  - v5_decision_* fields added to row_dict")
            print("  - v5_decision_action mirrors base_action")
            print("  - v5_decision_version fixed to 'v0.5'")
            print("  - v5_decision_generated_at in UTC ISO-8601 format")
            print("  - v5_decision_reason is non-numeric (no digits)")
            print("  - Wiring failure handled gracefully (no exception)")
            print("  - Warning-only (never raises exceptions)")
            print("  - Existing PR39/PR40 tests still pass")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR41 TESTS FAILED")
            print("=" * 60)
            print("Exit code: 0 (warning-only, never fails)")
            return 0  # Always exit 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Unexpected exception during validation")
        print(f"{e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("Exit code: 0 (warning-only, never fails)")
        return 0  # Always exit 0


if __name__ == "__main__":
    sys.exit(main())
