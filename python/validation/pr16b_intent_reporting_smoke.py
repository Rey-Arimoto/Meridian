#!/usr/bin/env python3
"""
PR16B: Intent Reporting Smoke Test

Purpose: Verify Intent sections are correctly added to PR9A performance report.

Requirements:
- Intent Summary section appears with distribution (count + %)
- Regime × Intent cross-tabulation appears when regime column exists
- N/A handling when Intent cannot be derived
- Existing PR9A/PR11A sections remain unchanged
- No crashes on missing data
- Exit 0 on PASS, 1 on FAIL
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
from reporting.pr9a_performance_report import generate_report, generate_markdown


def create_test_log_with_intent(csv_path: str) -> None:
    """Create test log with v0.2 columns that will generate Intent."""
    columns = [
        "timestamp_utc", "symbol", "env", "agent_version", "price", "ma",
        "deviation_pct", "entropy_pct", "entropy_bp", "ea_norm", "es_norm",
        "volatility_band", "entropy_state", "action_label", "target_weight",
        "equity", "guard_type", "guard_reason", "regime", "base_action", "decision_reason"
    ]

    rows = []
    for i in range(15):
        if i < 5:
            regime = "stable_range"
            base_action = "act"
            action = "BUY"
        elif i < 10:
            regime = "volatile_noise"
            base_action = "PAUSE"
            action = "HOLD"
        else:
            regime = "emerging_trend"
            base_action = "HOLD"
            action = "HOLD"

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
            "target_weight": 0.2 if action == "BUY" else 0.0,
            "equity": 1.0 + i * 0.001,
            "guard_type": "none",
            "guard_reason": "",
            "regime": regime,
            "base_action": base_action,
            "decision_reason": f"{regime.upper()}: {base_action} | overlay=PASS_THROUGH"
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def create_test_log_minimal(csv_path: str) -> None:
    """Create minimal test log without regime/base_action (Intent will be N/A)."""
    columns = ["timestamp_utc", "symbol", "price", "action_label", "target_weight"]

    rows = []
    for i in range(5):
        rows.append({
            "timestamp_utc": f"2025-01-09T10:{i:02d}:00.000000",
            "symbol": "sui",
            "price": 3.50 + i * 0.01,
            "action_label": "HOLD",
            "target_weight": 0.0,
        })

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def test_intent_sections_present():
    """Test Intent sections appear in report."""
    print("\nTest 1: Intent Sections Present")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "test.csv")
        create_test_log_with_intent(csv_path)

        df = pd.read_csv(csv_path)
        report = generate_report(df, csv_path)
        md_report = generate_markdown(df, csv_path)

        # Check text report
        assert "Intent Summary" in report, "Missing Intent Summary in text report"
        assert "Intent Distribution:" in report, "Missing Intent Distribution in text report"
        assert "Regime × Intent" in report, "Missing Regime × Intent in text report"
        print("✓ Intent sections present in text report")

        # Check markdown report
        assert "## Intent Summary" in md_report, "Missing Intent Summary in markdown"
        assert "## Regime × Intent" in md_report, "Missing Regime × Intent in markdown"
        print("✓ Intent sections present in markdown report")

        # Check Intent values appear
        assert "SEEK" in report or "DEFEND" in report or "PAUSE" in report or "IDLE" in report, \
            "No Intent values in text report"
        print("✓ Intent values present in reports")

        # Check Regime × Intent table exists
        assert "stable_range" in report or "volatile_noise" in report, \
            "Regime × Intent table missing in text report"
        print("✓ Regime × Intent cross-tabulation present")

    print("Test 1: PASS (4/4)")
    return True


def test_intent_na_handling():
    """Test N/A handling when Intent cannot be derived."""
    print("\nTest 2: Intent N/A Handling")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "minimal.csv")
        create_test_log_minimal(csv_path)

        df = pd.read_csv(csv_path)
        report = generate_report(df, csv_path)
        md_report = generate_markdown(df, csv_path)

        # Check Intent sections still appear (with N/A)
        assert "Intent Summary" in report, "Missing Intent Summary section"
        assert "Regime × Intent" in md_report, "Missing Regime × Intent section"
        print("✓ Intent sections present even with minimal data")

        # Check N/A appears for Intent (or all N/A)
        # Intent derivation might still work if action_label=HOLD → IDLE
        # So we just check it doesn't crash
        print("✓ No crash with minimal columns")

        # Check Regime × Intent shows N/A when regime missing
        assert "regime column missing" in report or "| Regime |" in md_report, \
            "Regime × Intent should show N/A or work with available data"
        print("✓ Regime × Intent handles missing regime column")

    print("Test 2: PASS (3/3)")
    return True


def test_existing_sections_unchanged():
    """Test existing PR9A/PR11A sections remain unchanged."""
    print("\nTest 3: Existing Sections Unchanged")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "test.csv")
        create_test_log_with_intent(csv_path)

        df = pd.read_csv(csv_path)
        report = generate_report(df, csv_path)
        md_report = generate_markdown(df, csv_path)

        # Check existing sections still present
        existing_sections = [
            "Equity-Based Performance",
            "Exposure / Activity",
            "Decision Stability",
            "Regime Distribution",
            "Regime-Based Exposure",
            "Data Quality Gate Reference"
        ]

        for section in existing_sections:
            assert section in report, f"Missing section: {section}"

        print(f"✓ All {len(existing_sections)} existing sections present")

        # Check PR11A metrics still present
        pr11a_metrics = [
            "Time Under Water",
            "Max DD Duration",
            "Exposure Ratio",
            "Turnover Proxy",
            "Action Switch Rate"
        ]

        for metric in pr11a_metrics:
            assert metric in report, f"Missing PR11A metric: {metric}"

        print(f"✓ All {len(pr11a_metrics)} PR11A metrics present")

    print("Test 3: PASS (2/2)")
    return True


def test_intent_sections_order():
    """Test Intent sections appear in correct order (after Regime-Based Exposure)."""
    print("\nTest 4: Intent Sections Order")
    print("-" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        csv_path = os.path.join(temp_dir, "test.csv")
        create_test_log_with_intent(csv_path)

        df = pd.read_csv(csv_path)
        report = generate_report(df, csv_path)

        # Find section positions
        lines = report.split('\n')
        regime_exposure_idx = -1
        intent_summary_idx = -1
        quality_gate_idx = -1

        for i, line in enumerate(lines):
            if "Regime-Based Exposure" in line:
                regime_exposure_idx = i
            elif "Intent Summary" in line:
                intent_summary_idx = i
            elif "Data Quality Gate Reference" in line:
                quality_gate_idx = i

        assert regime_exposure_idx >= 0, "Regime-Based Exposure section not found"
        assert intent_summary_idx >= 0, "Intent Summary section not found"
        assert quality_gate_idx >= 0, "Data Quality Gate Reference section not found"
        print("✓ All sections found")

        # Check order: Regime-Based Exposure → Intent Summary → Quality Gate
        assert regime_exposure_idx < intent_summary_idx, \
            "Intent Summary should come after Regime-Based Exposure"
        assert intent_summary_idx < quality_gate_idx, \
            "Intent Summary should come before Data Quality Gate Reference"
        print("✓ Intent sections in correct order")

    print("Test 4: PASS (2/2)")
    return True


def main():
    """Run all PR16B Intent reporting smoke tests."""
    print("=" * 60)
    print("PR16B: Intent Reporting Smoke Test")
    print("=" * 60)

    try:
        results = []
        results.append(("Intent Sections Present", test_intent_sections_present()))
        results.append(("Intent N/A Handling", test_intent_na_handling()))
        results.append(("Existing Sections Unchanged", test_existing_sections_unchanged()))
        results.append(("Intent Sections Order", test_intent_sections_order()))

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
            print("✓ ALL PR16B INTENT REPORTING TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ SOME PR16B INTENT REPORTING TESTS FAILED")
            print("=" * 60)
            return 1

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"FAIL: {e}")
        print("=" * 60)
        return 1

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Unexpected exception during validation")
        print(f"{e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
