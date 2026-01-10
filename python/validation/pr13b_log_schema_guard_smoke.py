#!/usr/bin/env python3
"""
PR13B: v0.2 Log Schema Guard — Smoke Validation Test

This test verifies that:
1. validate_log_row_v0_2 correctly detects missing v0.2 columns in row dicts
2. validate_existing_log_header correctly detects missing v0.2 columns in CSV headers
3. Both functions return proper (ok, missing) tuples

Exit 0 on PASS, 1 on FAIL.
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

from config import V0_2_REQUIRED_COLUMNS
from realtime.meridian_realtime_agent import validate_log_row_v0_2
from realtime.run_realtime import validate_existing_log_header


def test_validate_log_row_v0_2():
    """Test row validation logic."""
    print("Testing validate_log_row_v0_2...")

    # Test 1: Complete v0.2 row
    complete_row = {
        "timestamp_utc": "2026-01-10T00:00:00",
        "symbol": "sui",
        "regime": "stable_range",
        "base_action": "HOLD",
        "decision_reason": "Low entropy",
        "price": 1.0,
    }
    ok, missing = validate_log_row_v0_2(complete_row)
    assert ok is True, f"Complete row should pass validation, got missing={missing}"
    assert missing == [], f"Complete row should have no missing columns, got {missing}"
    print("  ✓ Complete v0.2 row passes")

    # Test 2: Missing regime
    incomplete_row = {
        "timestamp_utc": "2026-01-10T00:00:00",
        "symbol": "sui",
        "base_action": "HOLD",
        "decision_reason": "Low entropy",
    }
    ok, missing = validate_log_row_v0_2(incomplete_row)
    assert ok is False, "Row missing 'regime' should fail"
    assert "regime" in missing, f"Missing list should include 'regime', got {missing}"
    print("  ✓ Missing 'regime' detected")

    # Test 3: Missing all v0.2 columns
    v01_row = {
        "timestamp_utc": "2026-01-10T00:00:00",
        "symbol": "sui",
        "price": 1.0,
    }
    ok, missing = validate_log_row_v0_2(v01_row)
    assert ok is False, "v0.1 row should fail"
    assert set(missing) == set(V0_2_REQUIRED_COLUMNS), \
        f"Should report all v0.2 columns missing, got {missing}"
    print("  ✓ v0.1 row (all v0.2 columns missing) detected")


def test_validate_existing_log_header():
    """Test CSV header validation logic."""
    print("\nTesting validate_existing_log_header...")

    # Test 1: Non-existent file
    ok, missing = validate_existing_log_header("/nonexistent/path/to/log.csv")
    assert ok is True, "Non-existent file should return ok=True"
    assert missing == [], f"Non-existent file should have no missing columns, got {missing}"
    print("  ✓ Non-existent file returns ok=True")

    # Test 2: Complete v0.2 CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp_utc", "symbol", "price",
            "regime", "base_action", "decision_reason"
        ])
        writer.writerow([
            "2026-01-10T00:00:00", "sui", "1.0",
            "stable_range", "HOLD", "Low entropy"
        ])
        temp_v02_path = f.name

    try:
        ok, missing = validate_existing_log_header(temp_v02_path)
        assert ok is True, f"v0.2 CSV should pass, got missing={missing}"
        assert missing == [], f"v0.2 CSV should have no missing columns, got {missing}"
        print("  ✓ v0.2 CSV with all required columns passes")
    finally:
        os.unlink(temp_v02_path)

    # Test 3: v0.1 CSV (missing v0.2 columns)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_utc", "symbol", "price"])
        writer.writerow(["2026-01-10T00:00:00", "sui", "1.0"])
        temp_v01_path = f.name

    try:
        ok, missing = validate_existing_log_header(temp_v01_path)
        assert ok is False, "v0.1 CSV should fail"
        assert set(missing) == set(V0_2_REQUIRED_COLUMNS), \
            f"Should report all v0.2 columns missing, got {missing}"
        print("  ✓ v0.1 CSV (missing v0.2 columns) detected")
    finally:
        os.unlink(temp_v01_path)

    # Test 4: Empty CSV
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        temp_empty_path = f.name

    try:
        ok, missing = validate_existing_log_header(temp_empty_path)
        assert ok is False, "Empty CSV should fail"
        assert set(missing) == set(V0_2_REQUIRED_COLUMNS), \
            f"Empty CSV should report all columns missing, got {missing}"
        print("  ✓ Empty CSV detected as invalid")
    finally:
        os.unlink(temp_empty_path)


def main():
    print("=" * 70)
    print("PR13B: v0.2 Log Schema Guard — Smoke Validation Test")
    print("=" * 70)
    print()

    try:
        test_validate_log_row_v0_2()
        test_validate_existing_log_header()

        print()
        print("=" * 70)
        print("PASS: All PR13B validations passed")
        print("=" * 70)
        return 0

    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"FAIL: {e}")
        print("=" * 70)
        return 1

    except Exception as e:
        print()
        print("=" * 70)
        print(f"ERROR: Unexpected exception during validation")
        print(f"{e}")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
