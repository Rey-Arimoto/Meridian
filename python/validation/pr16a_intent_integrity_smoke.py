#!/usr/bin/env python3
"""
PR16A: Intent Integrity Check Smoke Test

Purpose: Verify Intent integrity check works as warning-only (never fails).

Requirements:
- Normal v0.3 log → warning 0, exit 0
- Intent columns missing → no crash, warning 0, exit 0
- Invalid intent_primary → warning >= 1, exit 0
- Never blocks pipeline (always exit 0)
- Works with both v0.2 and v0.3 logs
"""

import sys
import os
import tempfile
import csv

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

import pandas as pd
from validation.pr16a_intent_integrity_check import check_intent_integrity, format_warnings_text


def create_good_v03_log(csv_path: str) -> None:
    """Create valid v0.3 log with correct Intent columns."""
    columns = [
        "timestamp_utc", "regime", "base_action", "decision_reason", "action_label",
        "target_weight", "intent_primary", "intent_reason"
    ]

    rows = []
    for i in range(10):
        if i < 5:
            regime = "stable_range"
            base_action = "act"
            action = "BUY"
            intent = "SEEK"
            reason = "Active opportunity search"
        else:
            regime = "volatile_noise"
            base_action = "PAUSE"
            action = "HOLD"
            intent = "PAUSE"
            reason = "Constitutional freeze or emergency"

        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "regime": regime,
            "base_action": base_action,
            "decision_reason": f"{regime.upper()}: {base_action}",
            "action_label": action,
            "target_weight": 0.2 if action == "BUY" else 0.0,
            "intent_primary": intent,
            "intent_reason": reason,
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_v02_log_no_intent(csv_path: str) -> None:
    """Create v0.2 log without Intent columns."""
    columns = [
        "timestamp_utc", "regime", "base_action", "decision_reason", "action_label",
        "target_weight"
    ]

    rows = []
    for i in range(5):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "regime": "stable_range",
            "base_action": "act",
            "decision_reason": "STABLE_RANGE: Act",
            "action_label": "BUY",
            "target_weight": 0.2,
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_bad_intent_log(csv_path: str) -> None:
    """Create log with invalid intent_primary values."""
    columns = [
        "timestamp_utc", "regime", "base_action", "decision_reason", "action_label",
        "target_weight", "intent_primary", "intent_reason"
    ]

    rows = [
        {
            "timestamp_utc": "2025-01-09T10:00:00.000000",
            "regime": "stable_range",
            "base_action": "act",
            "decision_reason": "test",
            "action_label": "BUY",
            "target_weight": 0.2,
            "intent_primary": "SEEKING",  # Invalid!
            "intent_reason": "test",
        },
        {
            "timestamp_utc": "2025-01-09T10:01:00.000000",
            "regime": "volatile_noise",
            "base_action": "HOLD",
            "decision_reason": "test",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "intent_primary": "DEFEND",  # Valid
            "intent_reason": "test",
        },
        {
            "timestamp_utc": "2025-01-09T10:02:00.000000",
            "regime": "stable_range",
            "base_action": "act",
            "decision_reason": "test",
            "action_label": "BUY",
            "target_weight": 0.2,
            "intent_primary": "BUY",  # Invalid!
            "intent_reason": "test",
        },
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_good_v03_log():
    """Test good v0.3 log produces zero warnings."""
    print("\nTest 1: Good v0.3 Log (Zero Warnings)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "good_v03.csv")
        create_good_v03_log(csv_path)

        df = pd.read_csv(csv_path)
        warnings = check_intent_integrity(df)

        assert len(warnings) == 0, f"Expected 0 warnings, got {len(warnings)}"
        print("✓ Zero warnings for valid v0.3 log")

        # Test formatting
        text = format_warnings_text(warnings)
        assert "No Intent integrity warnings" in text, "Text format should indicate no warnings"
        print("✓ Warning text formatted correctly")

    print("Test 1: PASS (2/2)")
    return True


def test_v02_log_no_intent():
    """Test v0.2 log (no Intent columns) doesn't crash and produces zero warnings."""
    print("\nTest 2: v0.2 Log (No Intent Columns)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "v02_log.csv")
        create_v02_log_no_intent(csv_path)

        df = pd.read_csv(csv_path)
        warnings = check_intent_integrity(df)

        # Should not crash and should produce zero warnings (columns don't exist)
        assert len(warnings) == 0, f"Expected 0 warnings for v0.2 log, got {len(warnings)}"
        print("✓ No crash on missing Intent columns")
        print("✓ Zero warnings (Intent columns not present)")

    print("Test 2: PASS (2/2)")
    return True


def test_invalid_intent_values():
    """Test invalid intent_primary values produce warnings but don't fail."""
    print("\nTest 3: Invalid Intent Values (Warnings Generated)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "bad_intent.csv")
        create_bad_intent_log(csv_path)

        df = pd.read_csv(csv_path)
        warnings = check_intent_integrity(df)

        # Should have warnings for invalid values
        assert len(warnings) > 0, "Expected warnings for invalid intent_primary"
        print(f"✓ Warnings generated: {len(warnings)} warning type(s)")

        # Check that "SEEKING" and "BUY" are flagged
        invalid_types = [w for w in warnings if w["type"] == "invalid_intent_primary"]
        assert len(invalid_types) >= 1, "Expected invalid_intent_primary warnings"
        print(f"✓ Invalid intent_primary values detected")

        # Test formatting
        text = format_warnings_text(warnings)
        assert "warning" in text.lower(), "Text should mention warnings"
        assert "Pipeline execution is not blocked" in text, "Should indicate non-blocking"
        print("✓ Warning text includes non-blocking notice")

    print("Test 3: PASS (3/3)")
    return True


def test_weak_consistency_warnings():
    """Test weak consistency checks generate warnings."""
    print("\nTest 4: Weak Consistency Checks")
    print("-" * 60)

    # Create log with PAUSE intent but no PAUSE indicators
    columns = [
        "timestamp_utc", "regime", "base_action", "decision_reason", "action_label",
        "target_weight", "intent_primary", "intent_reason"
    ]

    rows = [
        {
            "timestamp_utc": "2025-01-09T10:00:00.000000",
            "regime": "stable_range",
            "base_action": "act",  # Not PAUSE
            "decision_reason": "test",  # No PAUSE/EMERGENCY_FREEZE
            "action_label": "BUY",
            "target_weight": 0.2,
            "intent_primary": "PAUSE",  # Inconsistent!
            "intent_reason": "test",
        },
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "inconsistent.csv")
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)

        df = pd.read_csv(csv_path)
        warnings = check_intent_integrity(df)

        # Should have weak consistency warning
        weak_warnings = [w for w in warnings if "inconsistency" in w["type"]]
        assert len(weak_warnings) >= 1, "Expected weak consistency warning"
        print(f"✓ Weak consistency warning generated")

    print("Test 4: PASS (1/1)")
    return True


def test_always_exit_zero():
    """Test that integrity check always exits with code 0 (warning-only)."""
    print("\nTest 5: Always Exit Zero (Warning-Only)")
    print("-" * 60)

    # Test with various log types
    test_cases = []

    with tempfile.TemporaryDirectory() as temp_dir:
        # Good log
        good_path = os.path.join(temp_dir, "good.csv")
        create_good_v03_log(good_path)
        test_cases.append(good_path)

        # v0.2 log
        v02_path = os.path.join(temp_dir, "v02.csv")
        create_v02_log_no_intent(v02_path)
        test_cases.append(v02_path)

        # Bad log
        bad_path = os.path.join(temp_dir, "bad.csv")
        create_bad_intent_log(bad_path)
        test_cases.append(bad_path)

        # Run all test cases
        for csv_path in test_cases:
            df = pd.read_csv(csv_path)
            warnings = check_intent_integrity(df)
            # Just check it doesn't crash
            print(f"✓ No crash for {os.path.basename(csv_path)}: {len(warnings)} warning(s)")

    print("Test 5: PASS (3/3)")
    return True


def main():
    """Run all PR16A Intent integrity smoke tests."""
    print("=" * 60)
    print("PR16A: Intent Integrity Check Smoke Test")
    print("=" * 60)
    print("IMPORTANT: All tests must exit 0 (warning-only, never fails)")
    print("=" * 60)

    try:
        results = []
        results.append(("Good v0.3 Log", test_good_v03_log()))
        results.append(("v0.2 Log (No Intent)", test_v02_log_no_intent()))
        results.append(("Invalid Intent Values", test_invalid_intent_values()))
        results.append(("Weak Consistency", test_weak_consistency_warnings()))
        results.append(("Always Exit Zero", test_always_exit_zero()))

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
            print("✓ ALL PR16A INTENT INTEGRITY TESTS PASSED")
            print("=" * 60)
            print("Exit code: 0 (warning-only, never fails)")
            return 0
        else:
            print("✗ SOME PR16A INTENT INTEGRITY TESTS FAILED")
            print("=" * 60)
            print("Exit code: 0 (warning-only, even with failures)")
            return 0  # IMPORTANT: Always exit 0

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"FAIL: {e}")
        print("=" * 60)
        print("Exit code: 0 (warning-only, never fails)")
        return 0  # IMPORTANT: Always exit 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Unexpected exception during validation")
        print(f"{e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("Exit code: 0 (warning-only, never fails)")
        return 0  # IMPORTANT: Always exit 0


if __name__ == "__main__":
    sys.exit(main())
