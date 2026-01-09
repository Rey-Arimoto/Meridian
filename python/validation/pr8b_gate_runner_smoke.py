#!/usr/bin/env python3
"""
PR8B Validation: Gate Runner Smoke Test

Purpose: Verify pr8b_integrity_gate_runner.py enforces PR8A validation correctly.

Requirements:
- Good CSV → runner exits 0, artifacts generated
- Bad CSV (timestamp regression) → runner exits 1, generation blocked
- Bad CSV (NaN weight) → runner exits 1, generation blocked
- Bad CSV (out-of-bounds weight) → runner exits 1, generation blocked
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
    """Test that good CSV passes validation and generates artifacts."""
    print("\nTest 1: Good CSV → runner exits 0, artifacts generated")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "good.csv")
    create_good_csv(csv_path)

    out_dir = os.path.join(temp_dir, "artifacts_good")
    script_path = "python/tools/pr8b_integrity_gate_runner.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out-dir", out_dir, "--prefix", "test"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        checks_total += 1
        if result.returncode == 0:
            print(f"✓ Runner exited with code 0 (PASS)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Runner exited with code {result.returncode} (expected 0)")
            print(f"  stdout: {result.stdout[:500]}")

        checks_total += 1
        if "PR8A PASSED" in result.stdout:
            print(f"✓ Output contains PR8A PASSED message")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing PR8A PASSED message")

        # Check artifacts were created
        expected_files = [
            "test_health.md",
            "test_dashboard.html",
            "test_investor_report.md",
            "test_timeline.png",
            "test_overlay_hist.png",
            "test_regime_dist.png",
        ]

        for filename in expected_files:
            checks_total += 1
            filepath = os.path.join(out_dir, filename)
            if os.path.exists(filepath):
                print(f"✓ Artifact created: {filename}")
                checks_passed += 1
            else:
                print(f"✗ FAIL: Artifact missing: {filename}")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 9  # Account for all checks

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 1: {status} ({checks_passed}/{checks_total})")
    return passed


def test_bad_csv_timestamp(temp_dir: str) -> bool:
    """Test that CSV with timestamp regression blocks generation."""
    print("\nTest 2: Bad CSV (timestamp regression) → runner exits 1, blocked")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "bad_timestamp.csv")
    create_bad_csv_timestamp_regression(csv_path)

    out_dir = os.path.join(temp_dir, "artifacts_bad_ts")
    script_path = "python/tools/pr8b_integrity_gate_runner.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out-dir", out_dir, "--prefix", "test"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        checks_total += 1
        if result.returncode == 1:
            print(f"✓ Runner exited with code 1 (BLOCKED)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Runner exited with code {result.returncode} (expected 1)")

        checks_total += 1
        if "GENERATION BLOCKED" in result.stdout or "PR8A FAILED" in result.stdout:
            print(f"✓ Output indicates generation was blocked")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output doesn't indicate blocking")

        # Verify dashboard/reports were NOT created (fail-closed)
        blocked_files = [
            "test_dashboard.html",
            "test_investor_report.md",
        ]

        for filename in blocked_files:
            checks_total += 1
            filepath = os.path.join(out_dir, filename)
            if not os.path.exists(filepath):
                print(f"✓ Artifact correctly blocked: {filename}")
                checks_passed += 1
            else:
                print(f"✗ FAIL: Artifact should not exist: {filename}")

        # Health report should still be created (for diagnostics)
        checks_total += 1
        health_path = os.path.join(out_dir, "test_health.md")
        if os.path.exists(health_path):
            print(f"✓ Health report created for diagnostics")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Health report should exist for diagnostics")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 5

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 2: {status} ({checks_passed}/{checks_total})")
    return passed


def test_bad_csv_nan_weight(temp_dir: str) -> bool:
    """Test that CSV with NaN weight blocks generation."""
    print("\nTest 3: Bad CSV (NaN weight) → runner exits 1, blocked")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "bad_nan.csv")
    create_bad_csv_nan_weight(csv_path)

    out_dir = os.path.join(temp_dir, "artifacts_bad_nan")
    script_path = "python/tools/pr8b_integrity_gate_runner.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out-dir", out_dir, "--prefix", "test"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        checks_total += 1
        if result.returncode == 1:
            print(f"✓ Runner exited with code 1 (BLOCKED)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Runner exited with code {result.returncode} (expected 1)")

        checks_total += 1
        if "GENERATION BLOCKED" in result.stdout or "PR8A FAILED" in result.stdout:
            print(f"✓ Output indicates generation was blocked")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output doesn't indicate blocking")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 2

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 3: {status} ({checks_passed}/{checks_total})")
    return passed


def test_bad_csv_out_of_bounds(temp_dir: str) -> bool:
    """Test that CSV with out-of-bounds weight blocks generation."""
    print("\nTest 4: Bad CSV (out-of-bounds weight) → runner exits 1, blocked")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "bad_oob.csv")
    create_bad_csv_out_of_bounds_weight(csv_path)

    out_dir = os.path.join(temp_dir, "artifacts_bad_oob")
    script_path = "python/tools/pr8b_integrity_gate_runner.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out-dir", out_dir, "--prefix", "test"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        checks_total += 1
        if result.returncode == 1:
            print(f"✓ Runner exited with code 1 (BLOCKED)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Runner exited with code {result.returncode} (expected 1)")

        checks_total += 1
        if "GENERATION BLOCKED" in result.stdout or "PR8A FAILED" in result.stdout:
            print(f"✓ Output indicates generation was blocked")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output doesn't indicate blocking")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 2

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 4: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run all PR8B gate runner smoke tests."""
    # Diagnostic: Show which Python is being used (venv enforcement)
    print(f"Python executable: {sys.executable}")
    print("")

    print("=" * 60)
    print("PR8B: Gate Runner Smoke Test")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        results = []
        results.append(("Good CSV → artifacts generated", test_good_csv(temp_dir)))
        results.append(("Bad CSV (timestamp) → blocked", test_bad_csv_timestamp(temp_dir)))
        results.append(("Bad CSV (NaN) → blocked", test_bad_csv_nan_weight(temp_dir)))
        results.append(("Bad CSV (out-of-bounds) → blocked", test_bad_csv_out_of_bounds(temp_dir)))

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
            print("✓ ALL GATE RUNNER SMOKE TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ SOME GATE RUNNER SMOKE TESTS FAILED")
            print("=" * 60)
            return 1


if __name__ == "__main__":
    sys.exit(main())
