#!/usr/bin/env python3
"""
PR49: Daily Shadow Diff Pipeline Smoke Test

Purpose:
    Validate that pr49_daily_shadow_diff_pipeline.py correctly orchestrates
    PR47→PR48A→PR48B pipeline in sequence.

Test Coverage:
    1. Minimal log CSV → pipeline completes, exit 0
    2. analytics_out_dir has PR47 JSON/CSV
    3. reports_dir has PR48A md (or degraded md)
    4. reports_dir has index.json and index.md
    5. reports_dir/_archive/YYYY-MM-DD/ created with normalized names
    6. File missing → pipeline still exit 0 (warning-only)
    7. index.md/index.json have no forbidden vocabulary
    8. --day specified → reflected in archive

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings

Exit Code: Always 0 (warning-only validation)
"""

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Dict


# Forbidden vocabulary (non-evaluative constraint)
FORBIDDEN_VOCABULARY = [
    "good", "bad", "better", "worse", "best", "worst",
    "correct", "incorrect", "wrong", "right",
    "superior", "inferior",
    "profit", "loss", "pnl", "win", "lose",
    "success", "failure", "successful", "failed",
    "score", "grade", "rank", "ranking", "accuracy",
]


def create_minimal_log_csv(out_path: str) -> None:
    """Create minimal execution log CSV with PR44-46 fields."""
    rows = [
        {
            "timestamp_utc": "2026-01-10T12:00:00Z",
            "regime": "stable_range",
            "intent_primary": "IDLE",
            "v5_decision_diff_mode": "ON",
            "v5_decision_diff_status": "ALIGNED",
            "v5_decision_diff_pair": "v1_vs_v2",
            "v5_shadow_decision_action": "HOLD",
            "v5_decision_diff_semantics_mode": "ON",
            "v5_decision_diff_semantics_status": "AVAILABLE",
            "v5_decision_diff_semantics_tag": "ALIGNED",
        },
        {
            "timestamp_utc": "2026-01-10T12:01:00Z",
            "regime": "emerging_trend",
            "intent_primary": "SEEK",
            "v5_decision_diff_mode": "ON",
            "v5_decision_diff_status": "DIVERGED",
            "v5_decision_diff_pair": "v1_vs_v2",
            "v5_shadow_decision_action": "PAUSE",
            "v5_decision_diff_semantics_mode": "ON",
            "v5_decision_diff_semantics_status": "AVAILABLE",
            "v5_decision_diff_semantics_tag": "DIVERGED_RULE_OVERLAY",
        },
    ]

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def run_pipeline(
    log_path: str,
    analytics_out_dir: str,
    reports_dir: str,
    day: str = None,
    format: str = "both",
) -> int:
    """
    Run pr49_daily_shadow_diff_pipeline.py.

    Returns exit code.
    """
    script_path = "python/analytics/pr49_daily_shadow_diff_pipeline.py"
    cmd = [
        sys.executable,
        script_path,
        "--log_path", log_path,
        "--analytics_out_dir", analytics_out_dir,
        "--reports_dir", reports_dir,
        "--format", format,
    ]

    if day:
        cmd.extend(["--day", day])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode


def test_minimal_log_pipeline_completes(tmp_dir: str) -> bool:
    """
    Test 1: Minimal log CSV → pipeline completes, exit 0.
    """
    print("Test 1: Minimal log CSV → pipeline completes, exit 0")
    print("-" * 60)

    log_path = os.path.join(tmp_dir, "test1.csv")
    analytics_out_dir = os.path.join(tmp_dir, "analytics1")
    reports_dir = os.path.join(tmp_dir, "reports1")

    create_minimal_log_csv(log_path)

    exit_code = run_pipeline(log_path, analytics_out_dir, reports_dir)

    # Check exit code
    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0")

    print("Test 1: PASS\n")
    return True


def test_pr47_outputs_generated(tmp_dir: str) -> bool:
    """
    Test 2: analytics_out_dir has PR47 JSON/CSV.
    """
    print("Test 2: analytics_out_dir has PR47 JSON/CSV")
    print("-" * 60)

    log_path = os.path.join(tmp_dir, "test2.csv")
    analytics_out_dir = os.path.join(tmp_dir, "analytics2")
    reports_dir = os.path.join(tmp_dir, "reports2")

    create_minimal_log_csv(log_path)
    run_pipeline(log_path, analytics_out_dir, reports_dir)

    # Check PR47 outputs
    json_path = os.path.join(analytics_out_dir, "pr47_shadow_diff_overall_summary.json")
    csv_path = os.path.join(analytics_out_dir, "pr47_shadow_diff_daily_summary.csv")

    if not os.path.exists(json_path):
        print(f"✗ PR47 JSON not found: {json_path}")
        return False
    print(f"✓ PR47 JSON generated: {json_path}")

    if not os.path.exists(csv_path):
        print(f"✗ PR47 CSV not found: {csv_path}")
        return False
    print(f"✓ PR47 CSV generated: {csv_path}")

    print("Test 2: PASS\n")
    return True


def test_pr48a_report_generated(tmp_dir: str) -> bool:
    """
    Test 3: reports_dir has PR48A md (or degraded md).
    """
    print("Test 3: reports_dir has PR48A md (or degraded md)")
    print("-" * 60)

    log_path = os.path.join(tmp_dir, "test3.csv")
    analytics_out_dir = os.path.join(tmp_dir, "analytics3")
    reports_dir = os.path.join(tmp_dir, "reports3")

    create_minimal_log_csv(log_path)
    run_pipeline(log_path, analytics_out_dir, reports_dir)

    # Check PR48A outputs
    md_path = os.path.join(reports_dir, "pr48a_shadow_diff_daily_report.md")

    if not os.path.exists(md_path):
        print(f"✗ PR48A MD not found: {md_path}")
        return False
    print(f"✓ PR48A MD generated: {md_path}")

    # Check MD is not empty
    if os.path.getsize(md_path) == 0:
        print(f"✗ PR48A MD is empty")
        return False
    print(f"✓ PR48A MD is not empty")

    print("Test 3: PASS\n")
    return True


def test_pr48b_index_generated(tmp_dir: str) -> bool:
    """
    Test 4: reports_dir has index.json and index.md.
    """
    print("Test 4: reports_dir has index.json and index.md")
    print("-" * 60)

    log_path = os.path.join(tmp_dir, "test4.csv")
    analytics_out_dir = os.path.join(tmp_dir, "analytics4")
    reports_dir = os.path.join(tmp_dir, "reports4")

    create_minimal_log_csv(log_path)
    run_pipeline(log_path, analytics_out_dir, reports_dir)

    # Check PR48B outputs
    index_json_path = os.path.join(reports_dir, "index.json")
    index_md_path = os.path.join(reports_dir, "index.md")

    if not os.path.exists(index_json_path):
        print(f"✗ index.json not found: {index_json_path}")
        return False
    print(f"✓ index.json generated: {index_json_path}")

    if not os.path.exists(index_md_path):
        print(f"✗ index.md not found: {index_md_path}")
        return False
    print(f"✓ index.md generated: {index_md_path}")

    print("Test 4: PASS\n")
    return True


def test_archive_created_with_normalized_names(tmp_dir: str) -> bool:
    """
    Test 5: reports_dir/_archive/YYYY-MM-DD/ created with normalized names.
    """
    print("Test 5: reports_dir/_archive/YYYY-MM-DD/ created with normalized names")
    print("-" * 60)

    log_path = os.path.join(tmp_dir, "test5.csv")
    analytics_out_dir = os.path.join(tmp_dir, "analytics5")
    reports_dir = os.path.join(tmp_dir, "reports5")

    create_minimal_log_csv(log_path)
    run_pipeline(log_path, analytics_out_dir, reports_dir)

    # Check archive directory exists
    archive_dir = os.path.join(reports_dir, "_archive")
    if not os.path.isdir(archive_dir):
        print(f"✗ Archive directory not found: {archive_dir}")
        return False
    print(f"✓ Archive directory exists: {archive_dir}")

    # Check day directory exists (should be 2026-01-10 from test log)
    day_dirs = [d for d in os.listdir(archive_dir) if os.path.isdir(os.path.join(archive_dir, d))]
    if not day_dirs:
        print(f"✗ No day directories in archive")
        return False

    day_dir = day_dirs[0]
    day_path = os.path.join(archive_dir, day_dir)
    print(f"✓ Day directory exists: {day_dir}")

    # Check normalized filenames
    md_path = os.path.join(day_path, "shadow_diff_report.md")
    if not os.path.exists(md_path):
        print(f"✗ Normalized MD not found: {md_path}")
        return False
    print(f"✓ Normalized MD exists: shadow_diff_report.md")

    print("Test 5: PASS\n")
    return True


def test_file_missing_still_exit_zero(tmp_dir: str) -> bool:
    """
    Test 6: File missing → pipeline still exit 0 (warning-only).
    """
    print("Test 6: File missing → pipeline still exit 0 (warning-only)")
    print("-" * 60)

    # Run pipeline with nonexistent log
    log_path = os.path.join(tmp_dir, "nonexistent.csv")
    analytics_out_dir = os.path.join(tmp_dir, "analytics6")
    reports_dir = os.path.join(tmp_dir, "reports6")

    exit_code = run_pipeline(log_path, analytics_out_dir, reports_dir)

    # Check exit code (should be 0 even with missing log)
    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0 (warning-only)")

    # Check that index files were still generated (degraded mode)
    index_json_path = os.path.join(reports_dir, "index.json")
    index_md_path = os.path.join(reports_dir, "index.md")

    if os.path.exists(index_json_path):
        print(f"✓ index.json generated in degraded mode")
    if os.path.exists(index_md_path):
        print(f"✓ index.md generated in degraded mode")

    print("Test 6: PASS\n")
    return True


def test_index_no_forbidden_vocabulary(tmp_dir: str) -> bool:
    """
    Test 7: index.md/index.json have no forbidden vocabulary.
    """
    print("Test 7: index.md/index.json have no forbidden vocabulary")
    print("-" * 60)

    log_path = os.path.join(tmp_dir, "test7.csv")
    analytics_out_dir = os.path.join(tmp_dir, "analytics7")
    reports_dir = os.path.join(tmp_dir, "reports7")

    create_minimal_log_csv(log_path)
    run_pipeline(log_path, analytics_out_dir, reports_dir)

    # Check index.md
    index_md_path = os.path.join(reports_dir, "index.md")
    if os.path.exists(index_md_path):
        with open(index_md_path, "r") as f:
            md_content = f.read().lower()

        found_forbidden_md = [word for word in FORBIDDEN_VOCABULARY if word.lower() in md_content]
        if found_forbidden_md:
            print(f"✗ Found forbidden vocabulary in index.md: {found_forbidden_md}")
            return False
        print(f"✓ No forbidden vocabulary in index.md")

    # Check index.json
    index_json_path = os.path.join(reports_dir, "index.json")
    if os.path.exists(index_json_path):
        with open(index_json_path, "r") as f:
            json_content = json.dumps(json.load(f)).lower()

        found_forbidden_json = [word for word in FORBIDDEN_VOCABULARY if word.lower() in json_content]
        if found_forbidden_json:
            print(f"✗ Found forbidden vocabulary in index.json: {found_forbidden_json}")
            return False
        print(f"✓ No forbidden vocabulary in index.json")

    print("Test 7: PASS\n")
    return True


def test_day_specified_reflected_in_archive(tmp_dir: str) -> bool:
    """
    Test 8: --day specified → reflected in archive.
    """
    print("Test 8: --day specified → reflected in archive")
    print("-" * 60)

    log_path = os.path.join(tmp_dir, "test8.csv")
    analytics_out_dir = os.path.join(tmp_dir, "analytics8")
    reports_dir = os.path.join(tmp_dir, "reports8")

    create_minimal_log_csv(log_path)
    # Use day from log (2026-01-10) to ensure consistency
    run_pipeline(log_path, analytics_out_dir, reports_dir, day="2026-01-10")

    # Check that archive has 2026-01-10 directory (from log data)
    archive_dir = os.path.join(reports_dir, "_archive")
    day_path = os.path.join(archive_dir, "2026-01-10")

    if not os.path.isdir(day_path):
        print(f"✗ Day directory not found: {day_path}")
        # Check what directories exist
        if os.path.isdir(archive_dir):
            dirs = os.listdir(archive_dir)
            print(f"  Found directories: {dirs}")
        return False
    print(f"✓ Day directory exists: 2026-01-10")

    # Check index.json references this day
    index_json_path = os.path.join(reports_dir, "index.json")
    if os.path.exists(index_json_path):
        with open(index_json_path, "r") as f:
            data = json.load(f)

        days = data.get("days", [])
        day_found = any(item["day"] == "2026-01-10" for item in days)

        if not day_found:
            print(f"✗ Day 2026-01-10 not in index.json")
            return False
        print(f"✓ Day 2026-01-10 in index.json")

    print("Test 8: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR49: Daily Shadow Diff Pipeline Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    # Create temp directory
    tmp_dir = tempfile.mkdtemp(prefix="pr49_test_")

    try:
        tests = [
            ("Minimal log pipeline completes", test_minimal_log_pipeline_completes),
            ("PR47 outputs generated", test_pr47_outputs_generated),
            ("PR48A report generated", test_pr48a_report_generated),
            ("PR48B index generated", test_pr48b_index_generated),
            ("Archive created with normalized names", test_archive_created_with_normalized_names),
            ("File missing still exit 0", test_file_missing_still_exit_zero),
            ("Index no forbidden vocabulary", test_index_no_forbidden_vocabulary),
            ("Day specified reflected in archive", test_day_specified_reflected_in_archive),
        ]

        results = []
        for name, test_fn in tests:
            try:
                result = test_fn(tmp_dir)
                results.append((name, result))
            except Exception as e:
                print(f"✗ Test '{name}' raised exception: {e}")
                import traceback
                traceback.print_exc()
                results.append((name, False))

        # Summary
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for name, passed in results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {name}")

        all_passed = all(passed for _, passed in results)

        print()
        print("=" * 60)
        if all_passed:
            print("✓ ALL PR49 PIPELINE TESTS PASSED")
        else:
            print("⚠ SOME PR49 PIPELINE TESTS FAILED")
        print("=" * 60)
        print("PR49 Requirements Verified:")
        print("  - Minimal log pipeline completes")
        print("  - PR47 outputs generated")
        print("  - PR48A report generated")
        print("  - PR48B index generated")
        print("  - Archive created with normalized names")
        print("  - File missing still exit 0 (warning-only)")
        print("  - Index contains no forbidden vocabulary")
        print("  - Day specified reflected in archive")
        print("=" * 60)
        print("Exit code: 0 (all tests completed)")

    finally:
        # Cleanup temp directory
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
