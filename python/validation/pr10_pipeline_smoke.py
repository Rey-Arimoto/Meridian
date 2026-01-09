#!/usr/bin/env python3
"""
PR10 Validation: Pipeline Smoke Test

Purpose: Verify pr10_run_pipeline.py works correctly.

Requirements:
- Good CSV → pipeline exits 0, artifacts created with timestamp
- Bad CSV → pipeline exits 1, PR8B fail-closed maintained
- input_log.csv fixed copy created in artifacts
- Exit 0 on PASS, 1 on FAIL
- Deterministic, no network
"""

import sys
import os
import subprocess
import tempfile
import csv
import shutil
from pathlib import Path


def create_good_csv(csv_path: str) -> None:
    """Create valid sample CSV that passes PR8A."""

    columns = [
        "timestamp_utc", "symbol", "env", "agent_version", "price", "ma",
        "deviation_pct", "entropy_pct", "entropy_bp", "ea_norm", "es_norm",
        "volatility_band", "entropy_state", "action_label", "target_weight",
        "equity", "guard_type", "guard_reason", "regime", "base_action", "decision_reason"
    ]

    rows = []
    prev_weight = 0.0
    for i in range(10):
        # HOLD keeps same weight to pass PR8A
        if i % 5 == 0:
            action = "BUY"
            weight = 0.1
        elif i % 7 == 0:
            action = "SELL"
            weight = 0.0
        else:
            action = "HOLD"
            weight = prev_weight

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
            "equity": 1.0 + i * 0.001,
            "guard_type": "none",
            "guard_reason": "",
            "regime": "stable_range",
            "base_action": "act",
            "decision_reason": "STABLE_RANGE: Act | overlay=MIN_THRESHOLD_HOLD"
        })
        prev_weight = weight

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_bad_csv(csv_path: str) -> None:
    """Create CSV with timestamp regression (fails PR8A)."""

    columns = [
        "timestamp_utc", "symbol", "regime", "base_action", "action_label",
        "target_weight", "entropy_bp", "decision_reason"
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
            "decision_reason": "test | overlay=PASS_THROUGH"
        },
        {
            "timestamp_utc": "2025-01-09T10:01:00.000000",
            "symbol": "sui",
            "regime": "stable_range",
            "base_action": "act",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "entropy_bp": 150,
            "decision_reason": "test | overlay=PASS_THROUGH"
        },
        {
            "timestamp_utc": "2025-01-09T09:59:00.000000",  # Regression!
            "symbol": "sui",
            "regime": "stable_range",
            "base_action": "act",
            "action_label": "HOLD",
            "target_weight": 0.0,
            "entropy_bp": 150,
            "decision_reason": "test | overlay=PASS_THROUGH"
        }
    ]

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_pipeline_good_csv(temp_dir: str, artifacts_dir: str, meridian_root: str) -> bool:
    """Test pipeline with good CSV → exit 0, artifacts created."""
    print("\nTest 1: Good CSV → pipeline exits 0, artifacts created")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "good.csv")
    create_good_csv(csv_path)

    script_path = os.path.join(meridian_root, "python/tools/pr10_run_pipeline.py")

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, "--log", csv_path, "--prefix", "test"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        checks_total += 1
        if result.returncode == 0:
            print(f"✓ Pipeline exited with code 0 (PASS)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Pipeline exited with code {result.returncode}")
            print(f"  stderr: {result.stderr[:500]}")

        # Find the timestamped directory
        artifacts_path = Path(artifacts_dir)
        if artifacts_path.exists():
            timestamp_dirs = [d for d in artifacts_path.iterdir() if d.is_dir() and d.name.startswith("_")]

            checks_total += 1
            if len(timestamp_dirs) > 0:
                print(f"✓ Timestamped directory created: {timestamp_dirs[0].name}")
                checks_passed += 1

                out_dir = timestamp_dirs[0]

                # Check input_log.csv was copied
                checks_total += 1
                input_log_copy = out_dir / "input_log.csv"
                if input_log_copy.exists():
                    print(f"✓ Fixed input log created: input_log.csv")
                    checks_passed += 1
                else:
                    print(f"✗ FAIL: input_log.csv not found in output directory")

                # Check key artifacts exist
                expected_files = ["test_health.md", "test_dashboard.html", "test_performance.md"]
                for filename in expected_files:
                    checks_total += 1
                    if (out_dir / filename).exists():
                        print(f"✓ Artifact created: {filename}")
                        checks_passed += 1
                    else:
                        print(f"✗ FAIL: Artifact missing: {filename}")
            else:
                print(f"✗ FAIL: No timestamped directory created in artifacts/")
                checks_total += 4  # input_log + 3 artifacts
        else:
            print(f"✗ FAIL: artifacts directory not found")
            checks_total += 5

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 6

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 1: {status} ({checks_passed}/{checks_total})")
    return passed


def test_pipeline_bad_csv(temp_dir: str, artifacts_dir: str, meridian_root: str) -> bool:
    """Test pipeline with bad CSV → exit 1, fail-closed."""
    print("\nTest 2: Bad CSV → pipeline exits 1, fail-closed")
    print("-" * 60)

    csv_path = os.path.join(temp_dir, "bad.csv")
    create_bad_csv(csv_path)

    script_path = os.path.join(meridian_root, "python/tools/pr10_run_pipeline.py")

    checks_passed = 0
    checks_total = 0

    try:
        result = subprocess.run(
            [sys.executable, script_path, "--log", csv_path, "--prefix", "test"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        checks_total += 1
        if result.returncode == 1:
            print(f"✓ Pipeline exited with code 1 (FAIL as expected)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Pipeline exited with code {result.returncode} (expected 1)")

        checks_total += 1
        if "PIPELINE FAILED" in result.stdout or "PR8A FAILED" in result.stdout:
            print(f"✓ Output indicates pipeline failure")
            checks_passed += 1
        else:
            print(f"✗ FAIL: Output doesn't indicate failure")

        # Verify input_log.csv was still created (for diagnostics)
        artifacts_path = Path(artifacts_dir)
        if artifacts_path.exists():
            timestamp_dirs = [d for d in artifacts_path.iterdir() if d.is_dir() and d.name.startswith("_")]

            if len(timestamp_dirs) > 0:
                out_dir = max(timestamp_dirs, key=lambda d: d.name)  # Get latest

                checks_total += 1
                input_log_copy = out_dir / "input_log.csv"
                if input_log_copy.exists():
                    print(f"✓ Fixed input log created (for diagnostics)")
                    checks_passed += 1
                else:
                    print(f"⚠ Note: input_log.csv not found")

    except Exception as e:
        print(f"✗ FAIL: Exception: {e}")
        checks_total += 3

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 2: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run all PR10 pipeline smoke tests."""
    # Diagnostic: Show which Python is being used (only if MERIDIAN_DEBUG=1)
    if os.environ.get("MERIDIAN_DEBUG"):
        print(f"Python executable: {sys.executable}")
        print("")

    print("=" * 60)
    print("PR10: Pipeline Smoke Test")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        # Keep artifacts in current directory for testing
        # Pipeline will create artifacts/_timestamp/ directories
        artifacts_dir = "artifacts"

        meridian_root = os.getcwd()

        results = []

        # Track created test artifacts for cleanup
        test_artifact_dirs = []

        # Before each test, note existing artifacts
        if os.path.exists(artifacts_dir):
            existing = set(os.listdir(artifacts_dir))
        else:
            existing = set()

        results.append(("Good CSV → success", test_pipeline_good_csv(temp_dir, artifacts_dir, meridian_root)))
        results.append(("Bad CSV → fail-closed", test_pipeline_bad_csv(temp_dir, artifacts_dir, meridian_root)))

        # Cleanup: Remove test artifacts
        if os.path.exists(artifacts_dir):
            for item in os.listdir(artifacts_dir):
                if item not in existing and item.startswith("_"):
                    test_dir = os.path.join(artifacts_dir, item)
                    if os.path.isdir(test_dir):
                        shutil.rmtree(test_dir)
                        print(f"\nCleaned up test artifact: {test_dir}")

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
            print("✓ ALL PIPELINE SMOKE TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ SOME PIPELINE SMOKE TESTS FAILED")
            print("=" * 60)
            return 1


if __name__ == "__main__":
    sys.exit(main())
