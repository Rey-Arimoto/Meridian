#!/usr/bin/env python3
"""
PR7A Validation: Reporting Smoke Test

Purpose: Verify that all 3 reporting scripts execute successfully.
- pr7a_decision_explainer.py
- pr7a_safety_summary.py
- pr7a_investor_report.py

Requirements:
- Generate sample CSV with minimal required columns
- Execute all 3 scripts
- Verify exit codes and output existence
- Exit 0 on PASS, 1 on FAIL
- Deterministic, no network
"""

import sys
import os
import subprocess
import tempfile
import csv
from pathlib import Path


def create_sample_csv(csv_path: str) -> None:
    """Create minimal sample CSV for testing."""

    # Minimal required columns
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

    # Sample data rows
    rows = [
        # Row 1: Normal HOLD with MIN_THRESHOLD_HOLD
        {
            "timestamp_utc": "2025-01-09T10:00:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.5000,
            "ma": 3.4800,
            "deviation_pct": 0.57,
            "entropy_pct": 1.50,
            "entropy_bp": 150,
            "ea_norm": 0.100,
            "es_norm": 0.050,
            "volatility_band": "low",
            "entropy_state": "calm",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "equity": 1.0000,
            "guard_type": "none",
            "guard_reason": "",
            "regime": "stable_range",
            "base_action": "act",
            "decision_reason": "STABLE_RANGE: Act (preserve PR0 fail-closed) | overlay=MIN_THRESHOLD_HOLD",
        },
        # Row 2: BUY with MAX_DELTA_CLAMP
        {
            "timestamp_utc": "2025-01-09T10:01:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.5200,
            "ma": 3.4900,
            "deviation_pct": 0.86,
            "entropy_pct": 4.20,
            "entropy_bp": 420,
            "ea_norm": 0.280,
            "es_norm": 0.140,
            "volatility_band": "moderate",
            "entropy_state": "emerging",
            "action_label": "BUY",
            "target_weight": 0.05,
            "equity": 1.0100,
            "guard_type": "none",
            "guard_reason": "",
            "regime": "emerging_trend",
            "base_action": "guard",
            "decision_reason": "EMERGING_TREND: Guard (ladder: 0.3) | overlay=MAX_DELTA_CLAMP_0.300→0.050",
        },
        # Row 3: HOLD with COOLDOWN_HOLD
        {
            "timestamp_utc": "2025-01-09T10:02:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.5100,
            "ma": 3.4950,
            "deviation_pct": 0.43,
            "entropy_pct": 3.80,
            "entropy_bp": 380,
            "ea_norm": 0.260,
            "es_norm": 0.120,
            "volatility_band": "moderate",
            "entropy_state": "emerging",
            "action_label": "HOLD",
            "target_weight": 0.05,
            "equity": 1.0120,
            "guard_type": "none",
            "guard_reason": "",
            "regime": "emerging_trend",
            "base_action": "guard",
            "decision_reason": "EMERGING_TREND: Guard | overlay=COOLDOWN_HOLD_120s",
        },
        # Row 4: HOLD in VOLATILE_NOISE
        {
            "timestamp_utc": "2025-01-09T10:03:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.6500,
            "ma": 3.5200,
            "deviation_pct": 3.69,
            "entropy_pct": 75.00,
            "entropy_bp": 7500,
            "ea_norm": 0.850,
            "es_norm": 0.900,
            "volatility_band": "high",
            "entropy_state": "volatile",
            "action_label": "HOLD",
            "target_weight": 0.05,
            "equity": 1.0250,
            "guard_type": "none",
            "guard_reason": "",
            "regime": "volatile_noise",
            "base_action": "pause",
            "decision_reason": "VOLATILE_NOISE: Pause (Act forbidden) | overlay=PASS_THROUGH",
        },
        # Row 5: FREEZE with EMERGENCY_FREEZE
        {
            "timestamp_utc": "2025-01-09T10:04:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.8000,
            "ma": 3.5500,
            "deviation_pct": 7.04,
            "entropy_pct": 92.00,
            "entropy_bp": 9200,
            "ea_norm": 0.950,
            "es_norm": 0.970,
            "volatility_band": "critical",
            "entropy_state": "crisis",
            "action_label": "FREEZE",
            "target_weight": 0.0,
            "equity": 1.0400,
            "guard_type": "entropy_freeze",
            "guard_reason": "9200bp >= 9000bp",
            "regime": "REGIME_TRANSITION",
            "base_action": "PAUSE",
            "decision_reason": "EMERGENCY_FREEZE | overlay=EMERGENCY_FREEZE",
        },
    ]

    # Write CSV
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_decision_explainer(csv_path: str, temp_dir: str) -> bool:
    """Test pr7a_decision_explainer.py"""
    print("\nTest 1: Decision Explainer")
    print("-" * 60)

    script_path = "python/reporting/pr7a_decision_explainer.py"

    checks_passed = 0
    checks_total = 0

    # Test 1: Run with --limit 3
    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--limit", "3"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        checks_total += 1
        if result.returncode == 0:
            print(f"✓ Script executed successfully (exit 0)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Script exited with code {result.returncode}")
            print(f"  stderr: {result.stderr}")

        # Check output contains expected keywords
        output = result.stdout
        checks_total += 1
        if "Tick #1" in output and "Tick #2" in output:
            print(f"✓ Output contains tick explanations")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing tick explanations")

        checks_total += 1
        if "Market State" in output and "Constitutional Decision" in output:
            print(f"✓ Output contains structured sections")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing structured sections")

    except Exception as e:
        print(f"✗ FAIL: Exception during execution: {e}")
        checks_total += 3

    # Test 2: Run with --out
    out_file = os.path.join(temp_dir, "explainer_out.txt")
    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--limit", "2", "--out", out_file],
            capture_output=True,
            text=True,
            timeout=10,
        )

        checks_total += 1
        if result.returncode == 0 and os.path.exists(out_file):
            print(f"✓ Output file created successfully")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output file not created")

    except Exception as e:
        print(f"✗ FAIL: Exception with --out: {e}")
        checks_total += 1

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 1: {status} ({checks_passed}/{checks_total})")
    return passed


def test_safety_summary(csv_path: str) -> bool:
    """Test pr7a_safety_summary.py"""
    print("\nTest 2: Safety Summary")
    print("-" * 60)

    script_path = "python/reporting/pr7a_safety_summary.py"

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path],
            capture_output=True,
            text=True,
            timeout=10,
        )

        checks_total += 1
        if result.returncode == 0:
            print(f"✓ Script executed successfully (exit 0)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Script exited with code {result.returncode}")
            print(f"  stderr: {result.stderr}")

        # Check output contains expected sections
        output = result.stdout
        checks_total += 1
        if "Action Distribution" in output:
            print(f"✓ Output contains Action Distribution")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing Action Distribution")

        checks_total += 1
        if "Safety Overlay Distribution" in output:
            print(f"✓ Output contains Safety Overlay Distribution")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing Safety Overlay Distribution")

        checks_total += 1
        if "Regime Distribution" in output:
            print(f"✓ Output contains Regime Distribution")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output missing Regime Distribution")

        checks_total += 1
        if "Doing Nothing" in output or "HOLD" in output:
            print(f"✓ Output emphasizes 'doing nothing'")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output doesn't emphasize 'doing nothing'")

    except Exception as e:
        print(f"✗ FAIL: Exception during execution: {e}")
        checks_total += 5

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 2: {status} ({checks_passed}/{checks_total})")
    return passed


def test_investor_report(csv_path: str, temp_dir: str) -> bool:
    """Test pr7a_investor_report.py"""
    print("\nTest 3: Investor Report")
    print("-" * 60)

    script_path = "python/reporting/pr7a_investor_report.py"
    out_file = os.path.join(temp_dir, "investor_report.md")

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out", out_file],
            capture_output=True,
            text=True,
            timeout=10,
        )

        checks_total += 1
        if result.returncode == 0:
            print(f"✓ Script executed successfully (exit 0)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Script exited with code {result.returncode}")
            print(f"  stderr: {result.stderr}")

        checks_total += 1
        if os.path.exists(out_file):
            print(f"✓ Markdown file created: {out_file}")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Markdown file not created")

        # Read and validate markdown content
        if os.path.exists(out_file):
            with open(out_file, "r") as f:
                content = f.read()

            checks_total += 1
            if "# Meridian v0.2 Investor Report" in content:
                print(f"✓ Markdown contains report header")
                checks_passed += 1
            else:
                print(f"✗ FAIL: Markdown missing report header")

            checks_total += 1
            if "Regime Distribution" in content:
                print(f"✓ Markdown contains Regime Distribution")
                checks_passed += 1
            else:
                print(f"✗ FAIL: Markdown missing Regime Distribution")

            checks_total += 1
            if "Safety Overlay Analysis" in content:
                print(f"✓ Markdown contains Safety Overlay Analysis")
                checks_passed += 1
            else:
                print(f"✗ FAIL: Markdown missing Safety Overlay Analysis")

            checks_total += 1
            if "Why Low Trade Count is Rational" in content:
                print(f"✓ Markdown explains low trade count rationality")
                checks_passed += 1
            else:
                print(f"✗ FAIL: Markdown doesn't explain trade count")
        else:
            checks_total += 4

    except Exception as e:
        print(f"✗ FAIL: Exception during execution: {e}")
        checks_total += 6

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 3: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run all PR7A reporting smoke tests"""
    # Diagnostic: Show which Python is being used (venv enforcement)
    print(f"Python executable: {sys.executable}")
    print("")

    print("=" * 60)
    print("PR7A: Reporting Smoke Test")
    print("=" * 60)

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample CSV
        csv_path = os.path.join(temp_dir, "sample_log.csv")
        create_sample_csv(csv_path)
        print(f"\n✓ Sample CSV created: {csv_path}")

        # Run tests
        results = []
        results.append(("Decision Explainer", test_decision_explainer(csv_path, temp_dir)))
        results.append(("Safety Summary", test_safety_summary(csv_path)))
        results.append(("Investor Report", test_investor_report(csv_path, temp_dir)))

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
            print("✓ ALL REPORTING SMOKE TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ SOME REPORTING SMOKE TESTS FAILED")
            print("=" * 60)
            return 1


if __name__ == "__main__":
    sys.exit(main())
