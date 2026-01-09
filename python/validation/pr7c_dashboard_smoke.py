#!/usr/bin/env python3
"""
PR7C Validation: Dashboard Smoke Test

Purpose: Verify that pr7c_build_dashboard.py executes successfully.

Requirements:
- Generate sample CSV with minimal required columns
- Execute dashboard builder
- Verify HTML exists, size > 0
- Verify HTML contains required sections
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
    """Create minimal sample CSV for testing dashboard."""

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

    # Generate 30 rows with variety
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

    for i in range(5, 15):
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

    for i in range(15, 25):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.65 + (i-15) * 0.05,
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
            "equity": 1.02 + (i-15) * 0.005,
            "guard_type": "none",
            "guard_reason": "",
            "regime": "volatile_noise",
            "base_action": "pause",
            "decision_reason": "VOLATILE_NOISE: Pause | overlay=PASS_THROUGH",
        })

    for i in range(25, 28):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "env": "test",
            "agent_version": "v0.2",
            "price": 3.80 + (i-25) * 0.10,
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

    for i in range(28, 30):
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

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_dashboard_builder(csv_path: str, temp_dir: str) -> bool:
    """Test pr7c_build_dashboard.py"""
    print("\nTest: Dashboard Builder")
    print("-" * 60)

    script_path = "python/dashboard/pr7c_build_dashboard.py"
    out_file = os.path.join(temp_dir, "dashboard_test.html")

    checks_passed = 0
    checks_total = 0

    # Test 1: Execute with default settings (base64 embed)
    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out", out_file, "--limit", "10"],
            capture_output=True,
            text=True,
            timeout=60,
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
            print(f"✓ HTML file created: {out_file}")
            checks_passed += 1
        else:
            print(f"✗ FAIL: HTML file not created")

        checks_total += 1
        if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
            file_size = os.path.getsize(out_file)
            print(f"✓ HTML file size > 0 bytes ({file_size:,} bytes)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: HTML file is empty")

    except Exception as e:
        print(f"✗ FAIL: Exception during execution: {e}")
        checks_total += 3

    # Test 2: Verify HTML contains required sections
    if os.path.exists(out_file):
        with open(out_file, "r") as f:
            html_content = f.read()

        required_keywords = [
            "Executive Summary",
            "Safety Contract",
            "Timeline",
            "Overlay",
            "Regime",
            "Meridian v0.2 Dashboard",
        ]

        for keyword in required_keywords:
            checks_total += 1
            if keyword in html_content:
                print(f"✓ HTML contains '{keyword}'")
                checks_passed += 1
            else:
                print(f"✗ FAIL: HTML missing '{keyword}'")

        # Check for base64 embedded images (default mode)
        checks_total += 1
        if "data:image/png;base64," in html_content:
            print(f"✓ HTML contains base64 embedded images")
            checks_passed += 1
        else:
            print(f"✗ FAIL: HTML missing base64 embedded images")

    else:
        checks_total += len(required_keywords) + 1

    # Test 3: Test assets-dir mode
    assets_dir = os.path.join(temp_dir, "assets")
    out_file2 = os.path.join(temp_dir, "dashboard_assets_test.html")

    try:
        result = subprocess.run(
            [sys.executable, script_path, csv_path, "--out", out_file2, "--limit", "5", "--assets-dir", assets_dir],
            capture_output=True,
            text=True,
            timeout=60,
        )

        checks_total += 1
        if result.returncode == 0:
            print(f"✓ Assets-dir mode executed successfully")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Assets-dir mode failed")

        checks_total += 1
        if os.path.exists(assets_dir):
            print(f"✓ Assets directory created")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Assets directory not created")

        checks_total += 1
        png_files = [f for f in os.listdir(assets_dir) if f.endswith('.png')] if os.path.exists(assets_dir) else []
        if len(png_files) >= 3:
            print(f"✓ PNGs saved to assets directory ({len(png_files)} files)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Expected 3+ PNGs in assets directory, found {len(png_files)}")

    except Exception as e:
        print(f"✗ FAIL: Exception in assets-dir mode: {e}")
        checks_total += 3

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run PR7C dashboard smoke test"""
    # Diagnostic: Show which Python is being used (only if MERIDIAN_DEBUG=1)
    if os.environ.get("MERIDIAN_DEBUG"):
        print(f"Python executable: {sys.executable}")
        print("")

    print("=" * 60)
    print("PR7C: Dashboard Smoke Test")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample CSV
        csv_path = os.path.join(temp_dir, "sample_log.csv")
        create_sample_csv(csv_path)
        print(f"\n✓ Sample CSV created: {csv_path}")

        # Run test
        passed = test_dashboard_builder(csv_path, temp_dir)

        # Summary
        print("\n" + "=" * 60)
        if passed:
            print("✓ DASHBOARD SMOKE TEST PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ DASHBOARD SMOKE TEST FAILED")
            print("=" * 60)
            return 1


if __name__ == "__main__":
    sys.exit(main())
