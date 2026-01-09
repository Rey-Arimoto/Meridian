#!/usr/bin/env python3
"""
PR9A Validation: Performance Report Smoke Test

Purpose: Verify pr9a_performance_report.py generates reports correctly.

Requirements:
- Case 1: CSV with equity → report generated, total_return_pct present
- Case 2: CSV without equity → report generated, Performance section = N/A
- Exit 0 on PASS, 1 on FAIL
- Deterministic, no network
"""

import sys
import os
import subprocess
import tempfile
import csv
from pathlib import Path


def create_csv_with_equity(csv_path: str) -> None:
    """Create sample CSV with equity column."""

    columns = [
        "timestamp_utc",
        "symbol",
        "regime",
        "base_action",
        "action_label",
        "target_weight",
        "equity",
        "entropy_bp",
        "decision_reason",
    ]

    rows = []
    for i in range(10):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "regime": "stable_range" if i < 5 else "emerging_trend",
            "base_action": "act",
            "action_label": "HOLD" if i % 3 == 0 else "BUY",
            "target_weight": 0.0 if i % 3 == 0 else 0.1,
            "equity": 1.0 + i * 0.01,  # Equity increases from 1.0 to 1.09
            "entropy_bp": 150 + i * 10,
            "decision_reason": "STABLE_RANGE: Act | overlay=MIN_THRESHOLD_HOLD",
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_csv_without_equity(csv_path: str) -> None:
    """Create sample CSV without equity column."""

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

    rows = []
    for i in range(10):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "regime": "stable_range",
            "base_action": "act",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "entropy_bp": 150,
            "decision_reason": "test | overlay=PASS_THROUGH",
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_report_with_equity(temp_dir: str) -> bool:
    """Test report generation with equity column."""
    print("\nTest 1: CSV with equity → report generated")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "with_equity.csv")
    create_csv_with_equity(csv_path)

    out_file = os.path.join(temp_dir, "performance_with_equity.md")
    script_path = "python/reporting/pr9a_performance_report.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out", out_file],
            capture_output=True,
            text=True,
            timeout=30,
        )

        checks_total += 1
        if result.returncode == 0:
            print(f"✓ Script executed successfully (exit 0)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Script exited with code {result.returncode}")
            print(f"  stderr: {result.stderr[:500]}")

        checks_total += 1
        if "Total Return" in result.stdout:
            print(f"✓ Output contains 'Total Return'")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing 'Total Return'")

        checks_total += 1
        if "Max Drawdown" in result.stdout:
            print(f"✓ Output contains 'Max Drawdown'")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing 'Max Drawdown'")

        checks_total += 1
        if "HOLD Ratio" in result.stdout:
            print(f"✓ Output contains 'HOLD Ratio'")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing 'HOLD Ratio'")

        checks_total += 1
        if os.path.exists(out_file):
            print(f"✓ Markdown file created: {out_file}")
            checks_passed += 1

            # Check markdown content
            with open(out_file, "r") as f:
                md_content = f.read()

            checks_total += 1
            if "PR9A: Performance & Risk Summary Report" in md_content:
                print(f"✓ Markdown contains report title")
                checks_passed += 1
            else:
                print(f"✗ FAIL: Markdown missing report title")

            checks_total += 1
            if "Total Return" in md_content:
                print(f"✓ Markdown contains 'Total Return'")
                checks_passed += 1
            else:
                print(f"✗ FAIL: Markdown missing 'Total Return'")
        else:
            print(f"✗ FAIL: Markdown file not created")
            checks_total += 2

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 7

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 1: {status} ({checks_passed}/{checks_total})")
    return passed


def test_report_without_equity(temp_dir: str) -> bool:
    """Test report generation without equity column."""
    print("\nTest 2: CSV without equity → Performance section N/A")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "without_equity.csv")
    create_csv_without_equity(csv_path)

    out_file = os.path.join(temp_dir, "performance_without_equity.md")
    script_path = "python/reporting/pr9a_performance_report.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out", out_file],
            capture_output=True,
            text=True,
            timeout=30,
        )

        checks_total += 1
        if result.returncode == 0:
            print(f"✓ Script executed successfully (exit 0)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Script exited with code {result.returncode}")

        checks_total += 1
        if "Performance Section: N/A" in result.stdout:
            print(f"✓ Output contains 'Performance Section: N/A'")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output should indicate N/A for performance")

        checks_total += 1
        if "HOLD Ratio" in result.stdout:
            print(f"✓ Output still contains 'HOLD Ratio' (non-equity metrics)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing 'HOLD Ratio'")

        checks_total += 1
        if os.path.exists(out_file):
            print(f"✓ Markdown file created")
            checks_passed += 1

            with open(out_file, "r") as f:
                md_content = f.read()

            checks_total += 1
            if "Performance Section" in md_content and "N/A" in md_content:
                print(f"✓ Markdown indicates N/A for performance section")
                checks_passed += 1
            else:
                print(f"✗ FAIL: Markdown should indicate N/A for performance")
        else:
            print(f"✗ FAIL: Markdown file not created")
            checks_total += 1

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 5

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 2: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run all PR9A performance smoke tests."""
    # Diagnostic: Show which Python is being used (only if MERIDIAN_DEBUG=1)
    if os.environ.get("MERIDIAN_DEBUG"):
        print(f"Python executable: {sys.executable}")
        print("")

    print("=" * 60)
    print("PR9A: Performance Report Smoke Test")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        results = []
        results.append(("CSV with equity", test_report_with_equity(temp_dir)))
        results.append(("CSV without equity", test_report_without_equity(temp_dir)))

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
            print("✓ ALL PERFORMANCE REPORT SMOKE TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ SOME PERFORMANCE REPORT SMOKE TESTS FAILED")
            print("=" * 60)
            return 1


if __name__ == "__main__":
    sys.exit(main())
