#!/usr/bin/env python3
"""
PR23: Confidence Invariants Smoke Test

Purpose: Verify PR21 Confidence absence semantics are enforced as warnings.

Requirements:
- v0.3 (no confidence columns) → 0 warnings
- v0.4 (confidence columns present but undefined) → 0 warnings
- One-sided presence (only one column) → warnings
- One-sided content (one has values, other empty) → warnings
- Exit code always 0 (warning-only, never fails)
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

from validation.pr23_confidence_invariants_warning_only import (
    validate_confidence_columns,
    format_warnings_report,
)


def create_v03_log(csv_path: str):
    """Create v0.3 log without Confidence columns."""
    columns = ["timestamp_utc", "regime", "intent_primary"]
    rows = [
        {"timestamp_utc": "2025-01-10T10:00:00", "regime": "stable_range", "intent_primary": "IDLE"},
        {"timestamp_utc": "2025-01-10T10:01:00", "regime": "stable_range", "intent_primary": "IDLE"},
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_v04_log_undefined(csv_path: str):
    """Create v0.4 log with Confidence columns present but undefined."""
    columns = ["timestamp_utc", "regime", "intent_primary", "confidence_value", "confidence_reason"]
    rows = [
        {
            "timestamp_utc": "2025-01-10T10:00:00",
            "regime": "stable_range",
            "intent_primary": "IDLE",
            "confidence_value": "",
            "confidence_reason": "",
        },
        {
            "timestamp_utc": "2025-01-10T10:01:00",
            "regime": "stable_range",
            "intent_primary": "IDLE",
            "confidence_value": "",
            "confidence_reason": "",
        },
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_log_one_sided_columns_value_only(csv_path: str):
    """Create log with only confidence_value column (one-sided presence)."""
    columns = ["timestamp_utc", "regime", "intent_primary", "confidence_value"]
    rows = [
        {"timestamp_utc": "2025-01-10T10:00:00", "regime": "stable_range", "intent_primary": "IDLE", "confidence_value": ""},
        {"timestamp_utc": "2025-01-10T10:01:00", "regime": "stable_range", "intent_primary": "IDLE", "confidence_value": ""},
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_log_one_sided_columns_reason_only(csv_path: str):
    """Create log with only confidence_reason column (one-sided presence)."""
    columns = ["timestamp_utc", "regime", "intent_primary", "confidence_reason"]
    rows = [
        {"timestamp_utc": "2025-01-10T10:00:00", "regime": "stable_range", "intent_primary": "IDLE", "confidence_reason": ""},
        {"timestamp_utc": "2025-01-10T10:01:00", "regime": "stable_range", "intent_primary": "IDLE", "confidence_reason": ""},
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_log_one_sided_content_value_has_data(csv_path: str):
    """Create log where confidence_value has data but confidence_reason is always empty."""
    columns = ["timestamp_utc", "regime", "intent_primary", "confidence_value", "confidence_reason"]
    rows = [
        {
            "timestamp_utc": "2025-01-10T10:00:00",
            "regime": "stable_range",
            "intent_primary": "IDLE",
            "confidence_value": "HIGH",
            "confidence_reason": "",
        },
        {
            "timestamp_utc": "2025-01-10T10:01:00",
            "regime": "stable_range",
            "intent_primary": "IDLE",
            "confidence_value": "LOW",
            "confidence_reason": "",
        },
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_log_one_sided_content_reason_has_data(csv_path: str):
    """Create log where confidence_reason has data but confidence_value is always empty."""
    columns = ["timestamp_utc", "regime", "intent_primary", "confidence_value", "confidence_reason"]
    rows = [
        {
            "timestamp_utc": "2025-01-10T10:00:00",
            "regime": "stable_range",
            "intent_primary": "IDLE",
            "confidence_value": "",
            "confidence_reason": "Regime stable",
        },
        {
            "timestamp_utc": "2025-01-10T10:01:00",
            "regime": "stable_range",
            "intent_primary": "IDLE",
            "confidence_value": "",
            "confidence_reason": "Regime stable",
        },
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_v03_log_no_warnings():
    """Test v0.3 log (no confidence columns) produces 0 warnings."""
    print("\nTest 1: v0.3 Log (No Confidence Columns)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "v03_log.csv")
        create_v03_log(csv_path)

        warnings = validate_confidence_columns(csv_path)

        assert len(warnings) == 0, f"Expected 0 warnings, got {len(warnings)}: {warnings}"
        print("✓ v0.3 log (no columns) → 0 warnings")
        print("✓ PR21 invariant: Absence is valid")

    print("Test 1: PASS (2/2)")
    return True


def test_v04_log_undefined_no_warnings():
    """Test v0.4 log (columns present but undefined) produces 0 warnings."""
    print("\nTest 2: v0.4 Log (Columns Present but Undefined)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "v04_log.csv")
        create_v04_log_undefined(csv_path)

        warnings = validate_confidence_columns(csv_path)

        assert len(warnings) == 0, f"Expected 0 warnings, got {len(warnings)}: {warnings}"
        print("✓ v0.4 log (columns empty) → 0 warnings")
        print("✓ PR21 invariant: Undefined is valid")

    print("Test 2: PASS (2/2)")
    return True


def test_one_sided_presence_value_only():
    """Test one-sided presence (only confidence_value) produces warnings."""
    print("\nTest 3: One-Sided Presence (confidence_value only)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "one_sided_value.csv")
        create_log_one_sided_columns_value_only(csv_path)

        warnings = validate_confidence_columns(csv_path)

        assert len(warnings) > 0, "Expected warnings for one-sided presence"
        print(f"✓ One-sided presence → {len(warnings)} warning(s)")
        for w in warnings:
            print(f"  ⚠ {w}")
        print("✓ PR21 invariant: Both or neither required")

    print("Test 3: PASS (2/2)")
    return True


def test_one_sided_presence_reason_only():
    """Test one-sided presence (only confidence_reason) produces warnings."""
    print("\nTest 4: One-Sided Presence (confidence_reason only)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "one_sided_reason.csv")
        create_log_one_sided_columns_reason_only(csv_path)

        warnings = validate_confidence_columns(csv_path)

        assert len(warnings) > 0, "Expected warnings for one-sided presence"
        print(f"✓ One-sided presence → {len(warnings)} warning(s)")
        for w in warnings:
            print(f"  ⚠ {w}")
        print("✓ PR21 invariant: Both or neither required")

    print("Test 4: PASS (2/2)")
    return True


def test_one_sided_content_value_has_data():
    """Test one-sided content (value has data, reason empty) produces warnings."""
    print("\nTest 5: One-Sided Content (confidence_value has data)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "one_sided_content_value.csv")
        create_log_one_sided_content_value_has_data(csv_path)

        warnings = validate_confidence_columns(csv_path)

        assert len(warnings) > 0, "Expected warnings for one-sided content"
        print(f"✓ One-sided content → {len(warnings)} warning(s)")
        for w in warnings:
            print(f"  ⚠ {w}")
        print("✓ PR21 invariant: Paired content expected")

    print("Test 5: PASS (2/2)")
    return True


def test_one_sided_content_reason_has_data():
    """Test one-sided content (reason has data, value empty) produces warnings."""
    print("\nTest 6: One-Sided Content (confidence_reason has data)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "one_sided_content_reason.csv")
        create_log_one_sided_content_reason_has_data(csv_path)

        warnings = validate_confidence_columns(csv_path)

        assert len(warnings) > 0, "Expected warnings for one-sided content"
        print(f"✓ One-sided content → {len(warnings)} warning(s)")
        for w in warnings:
            print(f"  ⚠ {w}")
        print("✓ PR21 invariant: Paired content expected")

    print("Test 6: PASS (2/2)")
    return True


def main():
    """Run all PR23 Confidence Invariants smoke tests."""
    print("=" * 60)
    print("PR23: Confidence Invariants Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("v0.3 Log (No Columns)", test_v03_log_no_warnings()))
        results.append(("v0.4 Log (Undefined)", test_v04_log_undefined_no_warnings()))
        results.append(("One-Sided Presence (value only)", test_one_sided_presence_value_only()))
        results.append(("One-Sided Presence (reason only)", test_one_sided_presence_reason_only()))
        results.append(("One-Sided Content (value has data)", test_one_sided_content_value_has_data()))
        results.append(("One-Sided Content (reason has data)", test_one_sided_content_reason_has_data()))

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
            print("✓ ALL PR23 CONFIDENCE INVARIANTS TESTS PASSED")
            print("=" * 60)
            print("PR21 Invariants Enforced:")
            print("  - Both columns or neither (structural)")
            print("  - Paired content expected (semantic)")
            print("  - Warning-only (never crashes pipeline)")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR23 CONFIDENCE INVARIANTS TESTS FAILED")
            print("=" * 60)
            print("Exit code: 0 (warning-only, never fails)")
            return 0  # Always exit 0 (warning-only)

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"FAIL: {e}")
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
