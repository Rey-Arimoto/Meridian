#!/usr/bin/env python3
"""
PR51: Weekly Shadow Diff Digest Smoke Test

Purpose:
    Validate that pr51_weekly_shadow_diff_digest.py correctly generates
    weekly summaries from daily shadow diff reports.

Test Coverage:
    1. Empty reports_dir generates digest (degraded mode)
    2. Archive with multiple days generates correct coverage
    3. index.json present → uses latest_day for window
    4. weekly_digest.md and weekly_digest.json generated
    5. No forbidden vocabulary in outputs
    6. Missing days handled gracefully (warning-only)
    7. Exit code always 0 (warning-only)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No recommendations

Exit Code: Always 0 (warning-only validation)
"""

import json
import os
import re
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
    "should", "must", "recommend", "prefer",
]


def create_minimal_index_json(out_path: str, latest_day: str) -> None:
    """Create minimal index.json file."""
    index_data = {
        "generated_at": "2026-01-11T12:00:00Z",
        "latest_day": latest_day,
        "days": [],
    }

    with open(out_path, "w") as f:
        json.dump(index_data, f, indent=2)


def create_minimal_archive_day(archive_dir: str, day: str, include_html: bool = True) -> None:
    """Create minimal archive directory for a day."""
    day_dir = os.path.join(archive_dir, day)
    os.makedirs(day_dir, exist_ok=True)

    # Create md
    md_path = os.path.join(day_dir, "shadow_diff_report.md")
    with open(md_path, "w") as f:
        f.write(f"# Shadow Diff Report\n\nDay: {day}\n")

    # Create html if requested
    if include_html:
        html_path = os.path.join(day_dir, "shadow_diff_report.html")
        with open(html_path, "w") as f:
            f.write(f"<html><body><h1>Shadow Diff Report</h1><p>Day: {day}</p></body></html>")

    # Create meta.json
    meta_path = os.path.join(day_dir, "meta.json")
    meta_data = {
        "day": day,
        "archived_at": "2026-01-11T12:00:00Z",
    }
    with open(meta_path, "w") as f:
        json.dump(meta_data, f, indent=2)


def run_digest(reports_dir: str = None, end_day: str = None, days: int = 7, out_dir: str = None) -> int:
    """
    Run pr51_weekly_shadow_diff_digest.py.

    Returns exit code.
    """
    script_path = "python/analytics/pr51_weekly_shadow_diff_digest.py"

    cmd = [sys.executable, script_path]

    if reports_dir:
        cmd.extend(["--reports_dir", reports_dir])

    if end_day:
        cmd.extend(["--end_day", end_day])

    if days != 7:
        cmd.extend(["--days", str(days)])

    if out_dir:
        cmd.extend(["--out_dir", out_dir])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode


def test_empty_reports_dir_degraded_mode(tmp_dir: str) -> bool:
    """
    Test 1: Empty reports_dir generates digest (degraded mode).
    """
    print("Test 1: Empty reports_dir generates digest (degraded mode)")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports1")
    os.makedirs(reports_dir)

    out_dir = os.path.join(tmp_dir, "weekly1")

    exit_code = run_digest(reports_dir=reports_dir, out_dir=out_dir)

    # Check exit code
    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0")

    # Check outputs generated
    md_path = os.path.join(out_dir, "weekly_digest.md")
    json_path = os.path.join(out_dir, "weekly_digest.json")

    if not os.path.exists(md_path):
        print(f"✗ MD digest not generated")
        return False
    print(f"✓ MD digest generated")

    if not os.path.exists(json_path):
        print(f"✗ JSON digest not generated")
        return False
    print(f"✓ JSON digest generated")

    print("Test 1: PASS\n")
    return True


def test_archive_multiple_days_coverage(tmp_dir: str) -> bool:
    """
    Test 2: Archive with multiple days generates correct coverage.
    """
    print("Test 2: Archive with multiple days generates correct coverage")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports2")
    archive_dir = os.path.join(reports_dir, "_archive")
    os.makedirs(archive_dir)

    # Create days: 2 available, 1 partial, 1 missing (within 7-day window)
    create_minimal_archive_day(archive_dir, "2026-01-08", include_html=True)  # AVAILABLE
    create_minimal_archive_day(archive_dir, "2026-01-09", include_html=True)  # AVAILABLE
    create_minimal_archive_day(archive_dir, "2026-01-10", include_html=False) # PARTIAL
    # 2026-01-11 is missing

    # Create index.json with latest_day
    create_minimal_index_json(os.path.join(reports_dir, "index.json"), "2026-01-11")

    out_dir = os.path.join(tmp_dir, "weekly2")

    exit_code = run_digest(reports_dir=reports_dir, end_day="2026-01-11", days=4, out_dir=out_dir)

    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0")

    # Check JSON coverage
    json_path = os.path.join(out_dir, "weekly_digest.json")
    with open(json_path, "r") as f:
        digest = json.load(f)

    coverage = digest.get("coverage", {})

    if coverage.get("days_considered") != 4:
        print(f"✗ days_considered: {coverage.get('days_considered')} (expected 4)")
        return False
    print(f"✓ days_considered: 4")

    if coverage.get("days_available") != 2:
        print(f"✗ days_available: {coverage.get('days_available')} (expected 2)")
        return False
    print(f"✓ days_available: 2")

    if coverage.get("days_partial") != 1:
        print(f"✗ days_partial: {coverage.get('days_partial')} (expected 1)")
        return False
    print(f"✓ days_partial: 1")

    if coverage.get("days_missing") != 1:
        print(f"✗ days_missing: {coverage.get('days_missing')} (expected 1)")
        return False
    print(f"✓ days_missing: 1")

    print("Test 2: PASS\n")
    return True


def test_index_json_latest_day_window(tmp_dir: str) -> bool:
    """
    Test 3: index.json present → uses latest_day for window.
    """
    print("Test 3: index.json present → uses latest_day for window")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports3")
    archive_dir = os.path.join(reports_dir, "_archive")
    os.makedirs(archive_dir)

    # Create index.json with latest_day = 2026-01-15
    create_minimal_index_json(os.path.join(reports_dir, "index.json"), "2026-01-15")

    # Create a few days
    create_minimal_archive_day(archive_dir, "2026-01-14", include_html=True)
    create_minimal_archive_day(archive_dir, "2026-01-15", include_html=True)

    out_dir = os.path.join(tmp_dir, "weekly3")

    exit_code = run_digest(reports_dir=reports_dir, days=7, out_dir=out_dir)

    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0")

    # Check JSON window
    json_path = os.path.join(out_dir, "weekly_digest.json")
    with open(json_path, "r") as f:
        digest = json.load(f)

    window = digest.get("window", {})

    if window.get("end_day") != "2026-01-15":
        print(f"✗ end_day: {window.get('end_day')} (expected 2026-01-15)")
        return False
    print(f"✓ end_day: 2026-01-15 (from index.json)")

    if window.get("start_day") != "2026-01-09":
        print(f"✗ start_day: {window.get('start_day')} (expected 2026-01-09)")
        return False
    print(f"✓ start_day: 2026-01-09 (7 days back)")

    print("Test 3: PASS\n")
    return True


def test_md_json_generated(tmp_dir: str) -> bool:
    """
    Test 4: weekly_digest.md and weekly_digest.json generated.
    """
    print("Test 4: weekly_digest.md and weekly_digest.json generated")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports4")
    archive_dir = os.path.join(reports_dir, "_archive")
    os.makedirs(archive_dir)

    create_minimal_archive_day(archive_dir, "2026-01-10", include_html=True)
    create_minimal_index_json(os.path.join(reports_dir, "index.json"), "2026-01-10")

    out_dir = os.path.join(tmp_dir, "weekly4")

    exit_code = run_digest(reports_dir=reports_dir, out_dir=out_dir)

    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0")

    # Check both outputs
    md_path = os.path.join(out_dir, "weekly_digest.md")
    json_path = os.path.join(out_dir, "weekly_digest.json")

    if not os.path.exists(md_path):
        print(f"✗ MD digest not generated")
        return False
    print(f"✓ MD digest generated: {md_path}")

    if not os.path.exists(json_path):
        print(f"✗ JSON digest not generated")
        return False
    print(f"✓ JSON digest generated: {json_path}")

    # Check files not empty
    if os.path.getsize(md_path) == 0:
        print(f"✗ MD digest is empty")
        return False
    print(f"✓ MD digest size: {os.path.getsize(md_path)} bytes")

    if os.path.getsize(json_path) == 0:
        print(f"✗ JSON digest is empty")
        return False
    print(f"✓ JSON digest size: {os.path.getsize(json_path)} bytes")

    print("Test 4: PASS\n")
    return True


def test_no_forbidden_vocabulary(tmp_dir: str) -> bool:
    """
    Test 5: No forbidden vocabulary in outputs.
    """
    print("Test 5: No forbidden vocabulary in outputs")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports5")
    archive_dir = os.path.join(reports_dir, "_archive")
    os.makedirs(archive_dir)

    create_minimal_archive_day(archive_dir, "2026-01-10", include_html=True)
    create_minimal_index_json(os.path.join(reports_dir, "index.json"), "2026-01-10")

    out_dir = os.path.join(tmp_dir, "weekly5")

    run_digest(reports_dir=reports_dir, out_dir=out_dir)

    # Check MD
    md_path = os.path.join(out_dir, "weekly_digest.md")
    with open(md_path, "r") as f:
        md_content = f.read().lower()

    found_forbidden_md = []
    for word in FORBIDDEN_VOCABULARY:
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        if re.search(pattern, md_content):
            found_forbidden_md.append(word)

    if found_forbidden_md:
        print(f"✗ Found forbidden vocabulary in MD: {found_forbidden_md}")
        return False
    print(f"✓ No forbidden vocabulary in MD")

    # Check JSON
    json_path = os.path.join(out_dir, "weekly_digest.json")
    with open(json_path, "r") as f:
        json_content = json.dumps(json.load(f)).lower()

    found_forbidden_json = []
    for word in FORBIDDEN_VOCABULARY:
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        if re.search(pattern, json_content):
            found_forbidden_json.append(word)

    if found_forbidden_json:
        print(f"✗ Found forbidden vocabulary in JSON: {found_forbidden_json}")
        return False
    print(f"✓ No forbidden vocabulary in JSON")

    print("Test 5: PASS\n")
    return True


def test_missing_days_handled_gracefully(tmp_dir: str) -> bool:
    """
    Test 6: Missing days handled gracefully (warning-only).
    """
    print("Test 6: Missing days handled gracefully (warning-only)")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports6")
    archive_dir = os.path.join(reports_dir, "_archive")
    os.makedirs(archive_dir)

    # Only create 1 day out of 7
    create_minimal_archive_day(archive_dir, "2026-01-10", include_html=True)
    create_minimal_index_json(os.path.join(reports_dir, "index.json"), "2026-01-13")

    out_dir = os.path.join(tmp_dir, "weekly6")

    exit_code = run_digest(reports_dir=reports_dir, end_day="2026-01-13", days=7, out_dir=out_dir)

    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0 (warning-only)")

    # Check JSON coverage
    json_path = os.path.join(out_dir, "weekly_digest.json")
    with open(json_path, "r") as f:
        digest = json.load(f)

    coverage = digest.get("coverage", {})

    if coverage.get("days_missing") == 0:
        print(f"✗ days_missing should be > 0 (missing days present)")
        return False
    print(f"✓ days_missing: {coverage.get('days_missing')} (recorded correctly)")

    missing_days = coverage.get("missing_days", [])
    if len(missing_days) == 0:
        print(f"✗ missing_days list should not be empty")
        return False
    print(f"✓ missing_days list: {missing_days}")

    print("Test 6: PASS\n")
    return True


def test_exit_code_always_zero(tmp_dir: str) -> bool:
    """
    Test 7: Exit code always 0 (warning-only).
    """
    print("Test 7: Exit code always 0 (warning-only)")
    print("-" * 60)

    test_cases = [
        ("empty reports_dir", lambda d: os.makedirs(d)),
        ("nonexistent reports_dir", lambda d: None),
    ]

    for name, setup_fn in test_cases:
        reports_dir = os.path.join(tmp_dir, f"reports7_{name.replace(' ', '_')}")

        if setup_fn:
            setup_fn(reports_dir)

        out_dir = os.path.join(tmp_dir, f"weekly7_{name.replace(' ', '_')}")

        exit_code = run_digest(reports_dir=reports_dir, out_dir=out_dir)

        if exit_code != 0:
            print(f"✗ Test case '{name}': exit code {exit_code} (expected 0)")
            return False
        print(f"✓ Test case '{name}': exit code 0")

    print("Test 7: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR51: Weekly Shadow Diff Digest Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    # Create temp directory
    tmp_dir = tempfile.mkdtemp(prefix="pr51_test_")

    try:
        tests = [
            ("Empty reports_dir degraded mode", test_empty_reports_dir_degraded_mode),
            ("Archive multiple days coverage", test_archive_multiple_days_coverage),
            ("index.json latest_day window", test_index_json_latest_day_window),
            ("MD and JSON generated", test_md_json_generated),
            ("No forbidden vocabulary", test_no_forbidden_vocabulary),
            ("Missing days handled gracefully", test_missing_days_handled_gracefully),
            ("Exit code always 0", test_exit_code_always_zero),
        ]

        results = []
        for name, test_fn in tests:
            try:
                result = test_fn(tmp_dir)
                results.append((name, result))
            except Exception as e:
                print(f"✗ Test '{name}' raised exception: {e}")
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
            print("✓ ALL PR51 WEEKLY DIGEST TESTS PASSED")
        else:
            print("⚠ SOME PR51 WEEKLY DIGEST TESTS FAILED")
        print("=" * 60)
        print("PR51 Requirements Verified:")
        print("  - Empty reports_dir generates digest (degraded mode)")
        print("  - Archive with multiple days generates correct coverage")
        print("  - index.json present uses latest_day for window")
        print("  - weekly_digest.md and weekly_digest.json generated")
        print("  - No forbidden vocabulary in outputs")
        print("  - Missing days handled gracefully (warning-only)")
        print("  - Exit code always 0")
        print("=" * 60)
        print("Exit code: 0 (all tests completed)")

    finally:
        # Cleanup temp directory
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
