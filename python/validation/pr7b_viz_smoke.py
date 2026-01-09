#!/usr/bin/env python3
"""
PR7B Validation: Visualization Smoke Test

Purpose: Verify that all 3 visualization scripts execute successfully.
- pr7b_timeline_plot.py
- pr7b_overlay_histogram.py
- pr7b_regime_distribution.py

Requirements:
- Generate sample CSV with minimal required columns
- Execute all 3 scripts
- Verify exit codes and PNG existence
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
    """Create minimal sample CSV for testing visualization."""

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

    # Sample data rows - enough variety for visualization
    rows = []

    # Generate 20 rows with variety
    base_time = "2025-01-09T10:00:00.000000"

    # Row 1-5: STABLE_RANGE with MIN_THRESHOLD_HOLD
    for i in range(5):
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

    # Row 6-10: EMERGING_TREND with MAX_DELTA_CLAMP and BUY
    for i in range(5, 10):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.52 + (i-5) * 0.02,
            "ma": 3.49,
            "deviation_pct": 1.0,
            "entropy_pct": 4.2,
            "entropy_bp": 420,
            "ea_norm": 0.28,
            "es_norm": 0.14,
            "volatility_band": "moderate",
            "entropy_state": "emerging",
            "action_label": "BUY" if i == 5 else "HOLD",
            "target_weight": 0.05 if i >= 5 else 0.0,
            "equity": 1.01 + (i-5) * 0.002,
            "guard_type": "none",
            "guard_reason": "",
            "regime": "emerging_trend",
            "base_action": "guard",
            "decision_reason": f"EMERGING_TREND: Guard | overlay={'MAX_DELTA_CLAMP_0.300→0.050' if i == 5 else 'COOLDOWN_HOLD_60s'}",
        })

    # Row 11-15: VOLATILE_NOISE with PAUSE
    for i in range(10, 15):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.65 + (i-10) * 0.05,
            "ma": 3.52,
            "deviation_pct": 3.5,
            "entropy_pct": 75.0,
            "entropy_bp": 7500,
            "ea_norm": 0.85,
            "es_norm": 0.90,
            "volatility_band": "high",
            "entropy_state": "volatile",
            "action_label": "HOLD",
            "target_weight": 0.05,
            "equity": 1.02 + (i-10) * 0.005,
            "guard_type": "none",
            "guard_reason": "",
            "regime": "volatile_noise",
            "base_action": "pause",
            "decision_reason": "VOLATILE_NOISE: Pause | overlay=PASS_THROUGH",
        })

    # Row 16-18: REGIME_TRANSITION with EMERGENCY_FREEZE
    for i in range(15, 18):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.80 + (i-15) * 0.10,
            "ma": 3.55,
            "deviation_pct": 7.0,
            "entropy_pct": 92.0,
            "entropy_bp": 9200,
            "ea_norm": 0.95,
            "es_norm": 0.97,
            "volatility_band": "critical",
            "entropy_state": "crisis",
            "action_label": "FREEZE",
            "target_weight": 0.0,
            "equity": 1.04,
            "guard_type": "entropy_freeze",
            "guard_reason": "9200bp >= 9000bp",
            "regime": "REGIME_TRANSITION",
            "base_action": "PAUSE",
            "decision_reason": "EMERGENCY_FREEZE | overlay=EMERGENCY_FREEZE",
        })

    # Row 19-20: POST_STRESS_RESET with FAIL_CLOSED
    for i in range(18, 20):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.50,
            "ma": 3.48,
            "deviation_pct": 0.5,
            "entropy_pct": 2.0,
            "entropy_bp": 200,
            "ea_norm": 0.15,
            "es_norm": 0.05,
            "volatility_band": "low",
            "entropy_state": "recovery",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "equity": 1.00,
            "guard_type": "none",
            "guard_reason": "",
            "regime": "post_stress_reset",
            "base_action": "pause",
            "decision_reason": "POST_STRESS_RESET: Pause | overlay=PASS_THROUGH",
        })

    # Write CSV
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_timeline_plot(csv_path: str, temp_dir: str) -> bool:
    """Test pr7b_timeline_plot.py"""
    print("\nTest 1: Timeline Plot")
    print("-" * 60)

    script_path = "python/viz/pr7b_timeline_plot.py"
    out_file = os.path.join(temp_dir, "timeline_test.png")

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out", out_file, "--limit", "20"],
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
            print(f"  stderr: {result.stderr}")

        checks_total += 1
        if os.path.exists(out_file):
            print(f"✓ PNG file created: {out_file}")
            checks_passed += 1
        else:
            print(f"✗ FAIL: PNG file not created")

        checks_total += 1
        if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
            print(f"✓ PNG file size > 0 bytes ({os.path.getsize(out_file)} bytes)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: PNG file is empty")

    except Exception as e:
        print(f"✗ FAIL: Exception during execution: {e}")
        checks_total += 3

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 1: {status} ({checks_passed}/{checks_total})")
    return passed


def test_overlay_histogram(csv_path: str, temp_dir: str) -> bool:
    """Test pr7b_overlay_histogram.py"""
    print("\nTest 2: Overlay Histogram")
    print("-" * 60)

    script_path = "python/viz/pr7b_overlay_histogram.py"
    out_file = os.path.join(temp_dir, "overlay_hist_test.png")

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
            print(f"  stderr: {result.stderr}")

        checks_total += 1
        if os.path.exists(out_file):
            print(f"✓ PNG file created: {out_file}")
            checks_passed += 1
        else:
            print(f"✗ FAIL: PNG file not created")

        checks_total += 1
        if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
            print(f"✓ PNG file size > 0 bytes ({os.path.getsize(out_file)} bytes)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: PNG file is empty")

        # Check stdout contains distribution
        checks_total += 1
        if "Overlay Distribution:" in result.stdout:
            print(f"✓ Stdout contains overlay distribution")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Stdout missing overlay distribution")

    except Exception as e:
        print(f"✗ FAIL: Exception during execution: {e}")
        checks_total += 4

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 2: {status} ({checks_passed}/{checks_total})")
    return passed


def test_regime_distribution(csv_path: str, temp_dir: str) -> bool:
    """Test pr7b_regime_distribution.py"""
    print("\nTest 3: Regime Distribution")
    print("-" * 60)

    script_path = "python/viz/pr7b_regime_distribution.py"
    out_file = os.path.join(temp_dir, "regime_dist_test.png")

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
            print(f"  stderr: {result.stderr}")

        checks_total += 1
        if os.path.exists(out_file):
            print(f"✓ PNG file created: {out_file}")
            checks_passed += 1
        else:
            print(f"✗ FAIL: PNG file not created")

        checks_total += 1
        if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
            print(f"✓ PNG file size > 0 bytes ({os.path.getsize(out_file)} bytes)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: PNG file is empty")

        # Check stdout contains distribution
        checks_total += 1
        if "Regime Distribution:" in result.stdout:
            print(f"✓ Stdout contains regime distribution")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Stdout missing regime distribution")

    except Exception as e:
        print(f"✗ FAIL: Exception during execution: {e}")
        checks_total += 4

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 3: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run all PR7B visualization smoke tests"""
    # Diagnostic: Show which Python is being used (only if MERIDIAN_DEBUG=1)
    if os.environ.get("MERIDIAN_DEBUG"):
        print(f"Python executable: {sys.executable}")
        print("")

    print("=" * 60)
    print("PR7B: Visualization Smoke Test")
    print("=" * 60)

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample CSV
        csv_path = os.path.join(temp_dir, "sample_log.csv")
        create_sample_csv(csv_path)
        print(f"\n✓ Sample CSV created: {csv_path}")

        # Run tests
        results = []
        results.append(("Timeline Plot", test_timeline_plot(csv_path, temp_dir)))
        results.append(("Overlay Histogram", test_overlay_histogram(csv_path, temp_dir)))
        results.append(("Regime Distribution", test_regime_distribution(csv_path, temp_dir)))

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
            print("✓ ALL VISUALIZATION SMOKE TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ SOME VISUALIZATION SMOKE TESTS FAILED")
            print("=" * 60)
            return 1


if __name__ == "__main__":
    sys.exit(main())
