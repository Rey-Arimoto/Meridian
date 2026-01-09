#!/usr/bin/env python3
"""
PR8A Validation: Data Health Smoke Test

Purpose: Verify pr8a_log_integrity_invariants.py and pr8a_data_health_report.py work correctly.

Requirements:
- Create good CSV → invariants PASS (exit 0)
- Create bad CSVs → invariants FAIL (exit 1)
  - Bad case 1: timestamp regression
  - Bad case 2: NaN target_weight
  - Bad case 3: out-of-bounds target_weight
- Verify report script runs without crash
- Exit 0 on PASS, 1 on FAIL
- Deterministic, no network
"""

import sys
import os
import subprocess
import tempfile
import csv
from pathlib import Path


def create_good_csv(csv_path: str) -> None:
    """Create valid sample CSV."""

    columns = [
        "timestamp_utc",
        "symbol",
        "env",
        "agent_version",
        "price",
        "ma",
        "deviation_pct",
        "entropy_pct",
        "entropy_bp",
        "ea_norm",
        "es_norm",
        "volatility_band",
        "entropy_state",
        "action_label",
        "target_weight",
        "equity",
        "guard_type",
        "guard_reason",
        "regime",
        "base_action",
        "decision_reason",
    ]

    rows = []
    for i in range(10):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.50 + i * 0.01,
            "ma": 3.48,
            "deviation_pct": 0.5,
            "entropy_pct": 1.5,
            "entropy_bp": 150,
            "ea_norm": 0.1,
            "es_norm": 0.05,
            "volatility_band": "low",
            "entropy_state": "calm",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "equity": 1.0,
            "guard_type": "none",
            "guard_reason": "",
            "regime": "stable_range",
            "base_action": "act",
            "decision_reason": "STABLE_RANGE: Act | overlay=MIN_THRESHOLD_HOLD",
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_bad_csv_timestamp_regression(csv_path: str) -> None:
    """Create CSV with timestamp regression."""

    columns = [
        "timestamp_utc",
        "symbol",
        "regime",
        "base_action",
        "action_label",
        "target_weight",
        "entropy_bp",
        "decision_reason",
    ]

    rows = [
        {
            "timestamp_utc": "2025-01-09T10:00:00.000000",
            "symbol": "sui",
            "regime": "stable_range",
            "base_action": "act",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "entropy_bp": 150,
            "decision_reason": "test | overlay=PASS_THROUGH",
        },
        {
            "timestamp_utc": "2025-01-09T10:01:00.000000",
            "symbol": "sui",
            "regime": "stable_range",
            "base_action": "act",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "entropy_bp": 150,
            "decision_reason": "test | overlay=PASS_THROUGH",
        },
        # Timestamp regression here
        {
            "timestamp_utc": "2025-01-09T09:59:00.000000",  # Goes backwards!
            "symbol": "sui",
            "regime": "stable_range",
            "base_action": "act",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "entropy_bp": 150,
            "decision_reason": "test | overlay=PASS_THROUGH",
        },
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_bad_csv_nan_weight(csv_path: str) -> None:
    """Create CSV with NaN target_weight."""

    columns = [
        "timestamp_utc",
        "symbol",
        "regime",
        "base_action",
        "action_label",
        "target_weight",
        "entropy_bp",
        "decision_reason",
    ]

    rows = [
        {
            "timestamp_utc": "2025-01-09T10:00:00.000000",
            "symbol": "sui",
            "regime": "stable_range",
            "base_action": "act",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "entropy_bp": 150,
            "decision_reason": "test | overlay=PASS_THROUGH",
        },
        {
            "timestamp_utc": "2025-01-09T10:01:00.000000",
            "symbol": "sui",
            "regime": "stable_range",
            "base_action": "act",
            "action_label": "HOLD",
            "target_weight": "",  # Will become NaN
            "entropy_bp": 150,
            "decision_reason": "test | overlay=PASS_THROUGH",
        },
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_bad_csv_out_of_bounds_weight(csv_path: str) -> None:
    """Create CSV with out-of-bounds target_weight."""

    columns = [
        "timestamp_utc",
        "symbol",
        "regime",
        "base_action",
        "action_label",
        "target_weight",
        "entropy_bp",
        "decision_reason",
    ]

    rows = [
        {
            "timestamp_utc": "2025-01-09T10:00:00.000000",
            "symbol": "sui",
            "regime": "stable_range",
            "base_action": "act",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "entropy_bp": 150,
            "decision_reason": "test | overlay=PASS_THROUGH",
        },
        {
            "timestamp_utc": "2025-01-09T10:01:00.000000",
            "symbol": "sui",
            "regime": "stable_range",
            "base_action": "act",
            "action_label": "HOLD",
            "target_weight": 1.5,  # Out of bounds!
            "entropy_bp": 150,
            "decision_reason": "test | overlay=PASS_THROUGH",
        },
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_good_csv(temp_dir: str) -> bool:
    """Test that good CSV passes validation."""
    print("\nTest 1: Good CSV → PASS")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "good.csv")
    create_good_csv(csv_path)

    script_path = "python/validation/pr8a_log_integrity_invariants.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        checks_total += 1
        if result.returncode == 0:
            print(f"✓ Validation exited with code 0 (PASS)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Validation exited with code {result.returncode} (expected 0)")
            print(f"  stdout: {result.stdout[:500]}")

        checks_total += 1
        if "ALL LOG INTEGRITY INVARIANTS PASSED" in result.stdout:
            print(f"✓ Output contains PASS message")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing PASS message")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 2

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 1: {status} ({checks_passed}/{checks_total})")
    return passed


def test_bad_csv_timestamp(temp_dir: str) -> bool:
    """Test that CSV with timestamp regression fails validation."""
    print("\nTest 2: Bad CSV (timestamp regression) → FAIL")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "bad_timestamp.csv")
    create_bad_csv_timestamp_regression(csv_path)

    script_path = "python/validation/pr8a_log_integrity_invariants.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        checks_total += 1
        if result.returncode == 1:
            print(f"✓ Validation exited with code 1 (FAIL)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Validation exited with code {result.returncode} (expected 1)")

        checks_total += 1
        if "timestamp regressions" in result.stdout or "SOME LOG INTEGRITY INVARIANTS FAILED" in result.stdout:
            print(f"✓ Output indicates timestamp issues")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output doesn't indicate timestamp issues")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 2

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 2: {status} ({checks_passed}/{checks_total})")
    return passed


def test_bad_csv_nan_weight(temp_dir: str) -> bool:
    """Test that CSV with NaN weight fails validation."""
    print("\nTest 3: Bad CSV (NaN weight) → FAIL")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "bad_nan.csv")
    create_bad_csv_nan_weight(csv_path)

    script_path = "python/validation/pr8a_log_integrity_invariants.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        checks_total += 1
        if result.returncode == 1:
            print(f"✓ Validation exited with code 1 (FAIL)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Validation exited with code {result.returncode} (expected 1)")

        checks_total += 1
        if "NaN" in result.stdout or "SOME LOG INTEGRITY INVARIANTS FAILED" in result.stdout:
            print(f"✓ Output indicates NaN issues")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output doesn't indicate NaN issues")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 2

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 3: {status} ({checks_passed}/{checks_total})")
    return passed


def test_bad_csv_out_of_bounds(temp_dir: str) -> bool:
    """Test that CSV with out-of-bounds weight fails validation."""
    print("\nTest 4: Bad CSV (out-of-bounds weight) → FAIL")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "bad_oob.csv")
    create_bad_csv_out_of_bounds_weight(csv_path)

    script_path = "python/validation/pr8a_log_integrity_invariants.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        checks_total += 1
        if result.returncode == 1:
            print(f"✓ Validation exited with code 1 (FAIL)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Validation exited with code {result.returncode} (expected 1)")

        checks_total += 1
        if "out-of-bounds" in result.stdout or "outside" in result.stdout or "SOME LOG INTEGRITY INVARIANTS FAILED" in result.stdout:
            print(f"✓ Output indicates out-of-bounds issues")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output doesn't indicate out-of-bounds issues")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 2

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 4: {status} ({checks_passed}/{checks_total})")
    return passed


def test_report_script(temp_dir: str) -> bool:
    """Test that report script runs without crash."""
    print("\nTest 5: Report Script Execution")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "report_test.csv")
    create_good_csv(csv_path)

    script_path = "python/reporting/pr8a_data_health_report.py"
    out_path = os.path.join(temp_dir, "health_report.md")

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out", out_path],
            capture_output=True,
            text=True,
            timeout=30,
        )

        checks_total += 1
        if result.returncode == 0:
            print(f"✓ Report script exited with code 0")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Report script exited with code {result.returncode}")

        checks_total += 1
        if "Data Health Report" in result.stdout:
            print(f"✓ Report output contains expected content")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Report output missing expected content")

        checks_total += 1
        if os.path.exists(out_path):
            print(f"✓ Markdown report file created")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Markdown report file not created")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 3

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 5: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run all PR8A data health smoke tests."""
    # Diagnostic: Show which Python is being used (only if MERIDIAN_DEBUG=1)
    if os.environ.get("MERIDIAN_DEBUG"):
        print(f"Python executable: {sys.executable}")
        print("")

    print("=" * 60)
    print("PR8A: Data Health Smoke Test")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        results = []
        results.append(("Good CSV → PASS", test_good_csv(temp_dir)))
        results.append(("Bad CSV (timestamp) → FAIL", test_bad_csv_timestamp(temp_dir)))
        results.append(("Bad CSV (NaN) → FAIL", test_bad_csv_nan_weight(temp_dir)))
        results.append(("Bad CSV (out-of-bounds) → FAIL", test_bad_csv_out_of_bounds(temp_dir)))
        results.append(("Report Script", test_report_script(temp_dir)))

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
            print("✓ ALL DATA HEALTH SMOKE TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ SOME DATA HEALTH SMOKE TESTS FAILED")
            print("=" * 60)
            return 1


if __name__ == "__main__":
    sys.exit(main())
