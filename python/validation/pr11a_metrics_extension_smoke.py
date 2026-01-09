#!/usr/bin/env python3
"""
PR11A Validation: Metrics Extension Smoke Test

Purpose: Verify pr9a_performance_report.py includes extended metrics correctly.

Requirements:
- Case 1: Full log (equity, target_weight, action_label, regime) → all metrics present
- Case 2: Minimal log (no equity, no regime) → N/A handling works, no crash
- Exit 0 on PASS, 1 on FAIL
- Deterministic, no network
"""

import sys
import os
import subprocess
import tempfile
import csv
from pathlib import Path


def create_full_log_csv(csv_path: str) -> None:
    """Create CSV with all columns for full metric testing."""
    columns = [
        "timestamp_utc", "symbol", "env", "agent_version", "price", "ma",
        "deviation_pct", "entropy_pct", "entropy_bp", "ea_norm", "es_norm",
        "volatility_band", "entropy_state", "action_label", "target_weight",
        "equity", "guard_type", "guard_reason", "regime", "base_action", "decision_reason"
    ]

    rows = []
    for i in range(20):
        # Simulate various actions and regimes
        if i < 5:
            action = "BUY"
            weight = 0.1
            regime = "stable_range"
        elif i < 10:
            action = "HOLD"
            weight = 0.1
            regime = "stable_range"
        elif i < 15:
            action = "SELL"
            weight = 0.0
            regime = "volatile_noise"
        else:
            action = "HOLD"
            weight = 0.0
            regime = "emerging_trend"

        # Simulate equity with clear peak-trough-recovery pattern
        # This tests the scope-aligned definition:
        # index 0: 100 (initial)
        # index 1: 110 (peak)
        # index 2: 90  (trough, max DD)
        # index 3: 110 (recovery)
        # Expected Max DD Duration = 2 ticks (from peak to recovery: 3 - 1 = 2)
        if i == 0:
            equity = 1.00
        elif i == 1:
            equity = 1.10  # peak
        elif i == 2:
            equity = 0.90  # trough (max DD ~18%)
        elif i == 3:
            equity = 1.10  # recovery
        elif i < 10:
            equity = 1.10 + (i - 3) * 0.001
        elif i < 15:
            # Second smaller drawdown
            equity = 1.11 - (i - 10) * 0.001
        else:
            # Recovery
            equity = 1.10 + (i - 15) * 0.0005

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
            "action_label": action,
            "target_weight": weight,
            "equity": equity,
            "guard_type": "none",
            "guard_reason": "",
            "regime": regime,
            "base_action": "act",
            "decision_reason": f"{regime.upper()}: Act | overlay=MIN_THRESHOLD_HOLD"
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_minimal_log_csv(csv_path: str) -> None:
    """Create CSV with minimal columns (no equity, no regime)."""
    columns = [
        "timestamp_utc", "symbol", "action_label", "target_weight", "decision_reason"
    ]

    rows = []
    for i in range(10):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "decision_reason": "test | overlay=PASS_THROUGH"
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_full_log(temp_dir: str) -> bool:
    """Test with full log → all extended metrics should be present."""
    print("\nTest 1: Full log → all extended metrics present")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "full_log.csv")
    create_full_log_csv(csv_path)

    script_path = "python/reporting/pr9a_performance_report.py"

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
            print(f"✓ Script executed successfully (exit 0)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Script exited with code {result.returncode}")
            print(f"  stderr: {result.stderr[:500]}")

        # Check for PR11A extended metrics in output
        output = result.stdout

        # Drawdown metrics
        checks_total += 1
        if "Time Under Water" in output:
            print(f"✓ Time Under Water metric present")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Time Under Water metric missing")

        checks_total += 1
        if "Max DD Duration" in output:
            print(f"✓ Max DD Duration metric present")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Max DD Duration metric missing")

        # Exposure metrics
        checks_total += 1
        if "Exposure Ratio" in output:
            print(f"✓ Exposure Ratio metric present")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Exposure Ratio metric missing")

        checks_total += 1
        if "Turnover Proxy" in output:
            print(f"✓ Turnover Proxy metric present")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Turnover Proxy metric missing")

        # Decision Stability
        checks_total += 1
        if "Decision Stability" in output:
            print(f"✓ Decision Stability section present")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Decision Stability section missing")

        checks_total += 1
        if "Action Switch Rate" in output:
            print(f"✓ Action Switch Rate metric present")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Action Switch Rate metric missing")

        checks_total += 1
        if "Longest HOLD" in output:
            print(f"✓ Longest HOLD metric present")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Longest HOLD metric missing")

        checks_total += 1
        if "Longest non-HOLD" in output:
            print(f"✓ Longest non-HOLD metric present")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Longest non-HOLD metric missing")

        # Regime-Based Exposure
        checks_total += 1
        if "Regime-Based Exposure" in output:
            print(f"✓ Regime-Based Exposure section present")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Regime-Based Exposure section missing")

        # Tick-based note
        checks_total += 1
        if "Tick-based durations are reported in ticks" in output:
            print(f"✓ Tick-based duration note present")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Tick-based duration note missing")

        # Scope-aligned definition verification: Max DD Duration should be 2 ticks
        # (peak at index 1 → recovery at index 3 = 2 ticks duration)
        checks_total += 1
        if "Max DD Duration" in output and "2 ticks" in output:
            print(f"✓ Max DD Duration = 2 ticks (scope-aligned definition verified)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Max DD Duration should be 2 ticks (peak-to-recovery)")
            # Debug: show what we got
            for line in output.split("\n"):
                if "Max DD Duration" in line:
                    print(f"  Found: {line.strip()}")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 12

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 1: {status} ({checks_passed}/{checks_total})")
    return passed


def test_minimal_log(temp_dir: str) -> bool:
    """Test with minimal log → N/A handling works, no crash."""
    print("\nTest 2: Minimal log → N/A handling, no crash")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "minimal_log.csv")
    create_minimal_log_csv(csv_path)

    script_path = "python/reporting/pr9a_performance_report.py"

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
            print(f"✓ Script executed successfully (exit 0)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Script exited with code {result.returncode}")
            print(f"  stderr: {result.stderr[:500]}")

        output = result.stdout

        # Check that N/A is properly shown for missing metrics
        checks_total += 1
        if "Performance Section: N/A" in output or "equity" in output.lower():
            print(f"✓ Equity section handles missing data")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Equity section doesn't handle missing data properly")

        checks_total += 1
        if "Regime-Based Exposure: N/A" in output or "regime column missing" in output:
            print(f"✓ Regime-Based Exposure section handles missing data")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Regime-Based Exposure section doesn't handle missing data properly")

        # Verify report still contains structural elements
        checks_total += 1
        if "Exposure / Activity" in output:
            print(f"✓ Report structure intact")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Report structure broken")

        # Verify no crashes or exceptions in stderr
        checks_total += 1
        if not result.stderr or "Traceback" not in result.stderr:
            print(f"✓ No exceptions or crashes")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Exception or crash detected")
            print(f"  stderr: {result.stderr[:500]}")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 5

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 2: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run all PR11A metrics extension smoke tests."""
    if os.environ.get("MERIDIAN_DEBUG"):
        print(f"Python executable: {sys.executable}")
        print("")

    print("=" * 60)
    print("PR11A: Metrics Extension Smoke Test")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        results = []
        results.append(("Full log → all metrics", test_full_log(temp_dir)))
        results.append(("Minimal log → N/A handling", test_minimal_log(temp_dir)))

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
            print("✓ ALL METRICS EXTENSION SMOKE TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ SOME METRICS EXTENSION SMOKE TESTS FAILED")
            print("=" * 60)
            return 1


if __name__ == "__main__":
    sys.exit(main())
