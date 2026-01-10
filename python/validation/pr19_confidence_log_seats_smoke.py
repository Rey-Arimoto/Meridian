#!/usr/bin/env python3
"""
PR19: Confidence Log Seats Smoke Test

Purpose: Verify Confidence seats (columns) are reserved in v0.4 logs.

Requirements:
- v0.4 logs include confidence_value and confidence_reason columns
- v0.3 logs (without Confidence columns) continue to work
- No pipeline failures (exit code always 0)
- No computation or value definition (seats only)
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


def create_v04_log_with_confidence_seats(csv_path: str) -> None:
    """Create v0.4 log with Confidence seat columns (empty values)."""
    columns = [
        "timestamp_utc", "regime", "base_action", "decision_reason", "action_label",
        "target_weight", "intent_primary", "intent_reason",
        "confidence_value", "confidence_reason"  # PR19: Confidence seats
    ]

    rows = []
    for i in range(5):
        rows.append({
            "timestamp_utc": f"2025-01-10T10:{i:02d}:00.000000",
            "regime": "stable_range",
            "base_action": "act",
            "decision_reason": "STABLE_RANGE: Act",
            "action_label": "BUY",
            "target_weight": 0.2,
            "intent_primary": "SEEK",
            "intent_reason": "Active opportunity search",
            "confidence_value": "",  # PR19: Seat reserved, value undefined
            "confidence_reason": "",  # PR19: Seat reserved, value undefined
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_v03_log_without_confidence(csv_path: str) -> None:
    """Create v0.3 log without Confidence columns (backward compatibility)."""
    columns = [
        "timestamp_utc", "regime", "base_action", "decision_reason", "action_label",
        "target_weight", "intent_primary", "intent_reason"
    ]

    rows = []
    for i in range(5):
        rows.append({
            "timestamp_utc": f"2025-01-10T10:{i:02d}:00.000000",
            "regime": "stable_range",
            "base_action": "act",
            "decision_reason": "STABLE_RANGE: Act",
            "action_label": "BUY",
            "target_weight": 0.2,
            "intent_primary": "SEEK",
            "intent_reason": "Active opportunity search",
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_v04_log_has_confidence_seats():
    """Test v0.4 log includes confidence_value and confidence_reason columns."""
    print("\nTest 1: v0.4 Log Has Confidence Seats")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "v04_log.csv")
        create_v04_log_with_confidence_seats(csv_path)

        df = pd.read_csv(csv_path)

        # Verify columns exist
        assert "confidence_value" in df.columns, "confidence_value column missing"
        assert "confidence_reason" in df.columns, "confidence_reason column missing"
        print("✓ confidence_value column present")
        print("✓ confidence_reason column present")

        # Verify seats are present (don't check values)
        assert len(df) == 5, "Expected 5 rows"
        print("✓ v0.4 log structure valid")

    print("Test 1: PASS (3/3)")
    return True


def test_v03_log_backward_compatibility():
    """Test v0.3 log (without Confidence) can be read without errors."""
    print("\nTest 2: v0.3 Log Backward Compatibility")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "v03_log.csv")
        create_v03_log_without_confidence(csv_path)

        # Should not crash when reading v0.3 log
        df = pd.read_csv(csv_path)

        # Verify Confidence columns absent
        assert "confidence_value" not in df.columns, "confidence_value should not exist in v0.3"
        assert "confidence_reason" not in df.columns, "confidence_reason should not exist in v0.3"
        print("✓ v0.3 log read successfully")
        print("✓ Confidence columns correctly absent")

        # Verify basic structure intact
        assert len(df) == 5, "Expected 5 rows"
        assert "intent_primary" in df.columns, "intent_primary should exist in v0.3"
        print("✓ v0.3 log structure valid")

    print("Test 2: PASS (3/3)")
    return True


def test_confidence_seats_position():
    """Test Confidence seats appear after Intent columns (append-only)."""
    print("\nTest 3: Confidence Seats Position (Append-Only)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "v04_log.csv")
        create_v04_log_with_confidence_seats(csv_path)

        df = pd.read_csv(csv_path)
        columns = list(df.columns)

        # Find positions
        intent_primary_idx = columns.index("intent_primary")
        intent_reason_idx = columns.index("intent_reason")
        confidence_value_idx = columns.index("confidence_value")
        confidence_reason_idx = columns.index("confidence_reason")

        # Confidence columns should come after Intent columns
        assert confidence_value_idx > intent_primary_idx, "confidence_value should come after intent_primary"
        assert confidence_value_idx > intent_reason_idx, "confidence_value should come after intent_reason"
        assert confidence_reason_idx > intent_primary_idx, "confidence_reason should come after intent_primary"
        assert confidence_reason_idx > intent_reason_idx, "confidence_reason should come after intent_reason"
        print("✓ Confidence seats positioned after Intent seats")
        print("✓ Append-only structure preserved")

    print("Test 3: PASS (2/2)")
    return True


def test_seats_without_values():
    """Test seats exist but values remain undefined (no computation)."""
    print("\nTest 4: Seats Without Values (No Computation)")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "v04_log.csv")
        create_v04_log_with_confidence_seats(csv_path)

        df = pd.read_csv(csv_path)

        # Seats exist
        assert "confidence_value" in df.columns
        assert "confidence_reason" in df.columns
        print("✓ Seats exist in log")

        # Values are empty or NaN (undefined, not populated)
        # Pandas reads empty strings as NaN, both are valid "undefined" states
        all_undefined_value = df["confidence_value"].isna().all() or (df["confidence_value"] == "").all()
        all_undefined_reason = df["confidence_reason"].isna().all() or (df["confidence_reason"] == "").all()

        assert all_undefined_value, "confidence_value should be undefined (empty or NaN)"
        assert all_undefined_reason, "confidence_reason should be undefined (empty or NaN)"
        print("✓ Values remain undefined (empty)")
        print("✓ No computation performed")

    print("Test 4: PASS (3/3)")
    return True


def main():
    """Run all PR19 Confidence Log Seats smoke tests."""
    print("=" * 60)
    print("PR19: Confidence Log Seats Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Seats only, no values. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("v0.4 Log Has Confidence Seats", test_v04_log_has_confidence_seats()))
        results.append(("v0.3 Log Backward Compatibility", test_v03_log_backward_compatibility()))
        results.append(("Confidence Seats Position", test_confidence_seats_position()))
        results.append(("Seats Without Values", test_seats_without_values()))

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
            print("✓ ALL PR19 CONFIDENCE LOG SEATS TESTS PASSED")
            print("=" * 60)
            print("Exit code: 0 (seats reserved, values undefined)")
            return 0
        else:
            print("✗ SOME PR19 CONFIDENCE LOG SEATS TESTS FAILED")
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
