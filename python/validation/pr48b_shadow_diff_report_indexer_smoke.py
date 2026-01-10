#!/usr/bin/env python3
"""
PR48B: Shadow Diff Report Indexer Smoke Test

Purpose:
    Validate that pr48b_shadow_diff_report_indexer.py correctly archives
    PR48A reports and generates index files.

Test Coverage:
    1. Empty reports_dir generates index (days empty allowed)
    2. Single md file generates index.md/index.json
    3. md + html both present → both in paths
    4. meta.json generated or updated
    5. latest_day correctly updated
    6. index.md contains no forbidden vocabulary
    7. index.json contains no forbidden vocabulary
    8. Exit code always 0 (warning-only)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings

Exit Code: Always 0 (warning-only validation)
"""

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


def create_minimal_report_md(out_path: str, day: str) -> None:
    """Create minimal report markdown file."""
    content = f"""# Shadow Diff Daily Report

**Generated at:** 2026-01-10T12:00:00Z

**Source:** PR47 outputs
- Date range: {day} to {day}

## Executive Summary

**Ticks Total:** 3

Divergence events were observed.

## Notes

- This report is observational only. No evaluations are made.
"""
    with open(out_path, "w") as f:
        f.write(content)


def create_minimal_report_html(out_path: str, day: str) -> None:
    """Create minimal report HTML file."""
    content = f"""<!DOCTYPE html>
<html>
<head><title>Shadow Diff Report</title></head>
<body>
<h1>Shadow Diff Daily Report</h1>
<p>Date: {day}</p>
</body>
</html>
"""
    with open(out_path, "w") as f:
        f.write(content)


def run_indexer(reports_dir: str, day: str = None) -> int:
    """
    Run pr48b_shadow_diff_report_indexer.py.

    Returns exit code.
    """
    script_path = "python/analytics/pr48b_shadow_diff_report_indexer.py"
    cmd = [sys.executable, script_path, "--reports_dir", reports_dir]

    if day:
        cmd.extend(["--day", day])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode


def test_empty_reports_dir_generates_index(tmp_dir: str) -> bool:
    """
    Test 1: Empty reports_dir generates index (days empty allowed).
    """
    print("Test 1: Empty reports_dir generates index (days empty allowed)")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports1")
    os.makedirs(reports_dir)

    exit_code = run_indexer(reports_dir)

    # Check exit code
    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0")

    # Check index.json generated
    index_json_path = os.path.join(reports_dir, "index.json")
    if not os.path.exists(index_json_path):
        print(f"✗ index.json not generated")
        return False
    print(f"✓ index.json generated")

    # Check index.md generated
    index_md_path = os.path.join(reports_dir, "index.md")
    if not os.path.exists(index_md_path):
        print(f"✗ index.md not generated")
        return False
    print(f"✓ index.md generated")

    # Check days is empty or absent
    with open(index_json_path, "r") as f:
        data = json.load(f)
    if "days" in data and len(data["days"]) > 0:
        print(f"✗ days should be empty for empty directory")
        return False
    print(f"✓ days is empty (as expected)")

    print("Test 1: PASS\n")
    return True


def test_single_md_generates_index(tmp_dir: str) -> bool:
    """
    Test 2: Single md file generates index.md/index.json.
    """
    print("Test 2: Single md file generates index.md/index.json")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports2")
    os.makedirs(reports_dir)

    # Create single MD report
    md_path = os.path.join(reports_dir, "report_2026-01-10.md")
    create_minimal_report_md(md_path, "2026-01-10")

    exit_code = run_indexer(reports_dir)

    # Check exit code
    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0")

    # Check index files generated
    index_json_path = os.path.join(reports_dir, "index.json")
    index_md_path = os.path.join(reports_dir, "index.md")

    if not os.path.exists(index_json_path):
        print(f"✗ index.json not generated")
        return False
    print(f"✓ index.json generated")

    if not os.path.exists(index_md_path):
        print(f"✗ index.md not generated")
        return False
    print(f"✓ index.md generated")

    # Check days contains 2026-01-10
    with open(index_json_path, "r") as f:
        data = json.load(f)

    days = data.get("days", [])
    if len(days) != 1:
        print(f"✗ Expected 1 day, got {len(days)}")
        return False

    if days[0]["day"] != "2026-01-10":
        print(f"✗ Expected day 2026-01-10, got {days[0]['day']}")
        return False
    print(f"✓ Day 2026-01-10 in index")

    print("Test 2: PASS\n")
    return True


def test_md_html_both_in_paths(tmp_dir: str) -> bool:
    """
    Test 3: md + html both present → both in paths.
    """
    print("Test 3: md + html both present → both in paths")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports3")
    os.makedirs(reports_dir)

    # Create MD + HTML
    md_path = os.path.join(reports_dir, "report_2026-01-10.md")
    html_path = os.path.join(reports_dir, "report_2026-01-10.html")
    create_minimal_report_md(md_path, "2026-01-10")
    create_minimal_report_html(html_path, "2026-01-10")

    run_indexer(reports_dir)

    # Check index.json
    index_json_path = os.path.join(reports_dir, "index.json")
    with open(index_json_path, "r") as f:
        data = json.load(f)

    days = data.get("days", [])
    if len(days) != 1:
        print(f"✗ Expected 1 day, got {len(days)}")
        return False

    paths = days[0].get("paths", {})

    if not paths.get("md"):
        print(f"✗ MD path missing in index")
        return False
    print(f"✓ MD path present: {paths['md']}")

    if not paths.get("html"):
        print(f"✗ HTML path missing in index")
        return False
    print(f"✓ HTML path present: {paths['html']}")

    print("Test 3: PASS\n")
    return True


def test_meta_json_generated(tmp_dir: str) -> bool:
    """
    Test 4: meta.json generated or updated.
    """
    print("Test 4: meta.json generated or updated")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports4")
    os.makedirs(reports_dir)

    # Create MD
    md_path = os.path.join(reports_dir, "report_2026-01-10.md")
    create_minimal_report_md(md_path, "2026-01-10")

    run_indexer(reports_dir)

    # Check meta.json in archive
    meta_path = os.path.join(reports_dir, "_archive", "2026-01-10", "meta.json")
    if not os.path.exists(meta_path):
        print(f"✗ meta.json not generated: {meta_path}")
        return False
    print(f"✓ meta.json generated: {meta_path}")

    # Check meta.json content
    with open(meta_path, "r") as f:
        meta = json.load(f)

    if meta.get("day") != "2026-01-10":
        print(f"✗ meta.json day incorrect: {meta.get('day')}")
        return False
    print(f"✓ meta.json day: {meta.get('day')}")

    if "archived_at" not in meta:
        print(f"✗ meta.json missing archived_at")
        return False
    print(f"✓ meta.json archived_at present")

    print("Test 4: PASS\n")
    return True


def test_latest_day_updated(tmp_dir: str) -> bool:
    """
    Test 5: latest_day correctly updated.
    """
    print("Test 5: latest_day correctly updated")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports5")
    os.makedirs(reports_dir)

    # Create reports for multiple days
    for day in ["2026-01-08", "2026-01-10", "2026-01-09"]:
        md_path = os.path.join(reports_dir, f"report_{day}.md")
        create_minimal_report_md(md_path, day)

    run_indexer(reports_dir)

    # Check index.json latest_day
    index_json_path = os.path.join(reports_dir, "index.json")
    with open(index_json_path, "r") as f:
        data = json.load(f)

    latest_day = data.get("latest_day")
    if latest_day != "2026-01-10":
        print(f"✗ latest_day incorrect: {latest_day} (expected 2026-01-10)")
        return False
    print(f"✓ latest_day: {latest_day}")

    print("Test 5: PASS\n")
    return True


def test_index_md_no_forbidden_vocab(tmp_dir: str) -> bool:
    """
    Test 6: index.md contains no forbidden vocabulary.
    """
    print("Test 6: index.md contains no forbidden vocabulary")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports6")
    os.makedirs(reports_dir)

    # Create report
    md_path = os.path.join(reports_dir, "report_2026-01-10.md")
    create_minimal_report_md(md_path, "2026-01-10")

    run_indexer(reports_dir)

    # Check index.md
    index_md_path = os.path.join(reports_dir, "index.md")
    with open(index_md_path, "r") as f:
        content = f.read().lower()

    # Check for forbidden vocabulary
    found_forbidden = []
    for word in FORBIDDEN_VOCABULARY:
        if word.lower() in content:
            found_forbidden.append(word)

    if found_forbidden:
        print(f"✗ Found forbidden vocabulary in index.md: {found_forbidden}")
        return False

    print(f"✓ No forbidden vocabulary found in index.md")
    print("Test 6: PASS\n")
    return True


def test_index_json_no_forbidden_vocab(tmp_dir: str) -> bool:
    """
    Test 7: index.json contains no forbidden vocabulary.
    """
    print("Test 7: index.json contains no forbidden vocabulary")
    print("-" * 60)

    reports_dir = os.path.join(tmp_dir, "reports7")
    os.makedirs(reports_dir)

    # Create report
    md_path = os.path.join(reports_dir, "report_2026-01-10.md")
    create_minimal_report_md(md_path, "2026-01-10")

    run_indexer(reports_dir)

    # Check index.json
    index_json_path = os.path.join(reports_dir, "index.json")
    with open(index_json_path, "r") as f:
        content = json.dumps(json.load(f)).lower()

    # Check for forbidden vocabulary
    found_forbidden = []
    for word in FORBIDDEN_VOCABULARY:
        if word.lower() in content:
            found_forbidden.append(word)

    if found_forbidden:
        print(f"✗ Found forbidden vocabulary in index.json: {found_forbidden}")
        return False

    print(f"✓ No forbidden vocabulary found in index.json")
    print("Test 7: PASS\n")
    return True


def test_exit_code_always_zero(tmp_dir: str) -> bool:
    """
    Test 8: Exit code always 0 (warning-only).
    """
    print("Test 8: Exit code always 0 (warning-only)")
    print("-" * 60)

    test_cases = [
        ("empty directory", lambda d: os.makedirs(d)),
        ("single report", lambda d: (
            os.makedirs(d),
            create_minimal_report_md(os.path.join(d, "report_2026-01-10.md"), "2026-01-10"),
        )),
        ("nonexistent directory", lambda d: None),  # Don't create
    ]

    for name, setup_fn in test_cases:
        reports_dir = os.path.join(tmp_dir, f"reports8_{name.replace(' ', '_')}")

        if setup_fn:
            setup_fn(reports_dir)

        exit_code = run_indexer(reports_dir)

        if exit_code != 0:
            print(f"✗ Test case '{name}': exit code {exit_code} (expected 0)")
            return False
        print(f"✓ Test case '{name}': exit code 0")

    print("Test 8: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR48B: Shadow Diff Report Indexer Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    # Create temp directory
    tmp_dir = tempfile.mkdtemp(prefix="pr48b_test_")

    try:
        tests = [
            ("Empty reports_dir generates index", test_empty_reports_dir_generates_index),
            ("Single md file generates index", test_single_md_generates_index),
            ("md + html both in paths", test_md_html_both_in_paths),
            ("meta.json generated", test_meta_json_generated),
            ("latest_day updated", test_latest_day_updated),
            ("index.md no forbidden vocab", test_index_md_no_forbidden_vocab),
            ("index.json no forbidden vocab", test_index_json_no_forbidden_vocab),
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
            print("✓ ALL PR48B REPORT INDEXER TESTS PASSED")
        else:
            print("⚠ SOME PR48B REPORT INDEXER TESTS FAILED")
        print("=" * 60)
        print("PR48B Requirements Verified:")
        print("  - Empty reports_dir generates index")
        print("  - Single md file generates index")
        print("  - md + html both in paths")
        print("  - meta.json generated")
        print("  - latest_day correctly updated")
        print("  - index.md contains no forbidden vocabulary")
        print("  - index.json contains no forbidden vocabulary")
        print("  - Warning-only (exit code always 0)")
        print("=" * 60)
        print("Exit code: 0 (all tests completed)")

    finally:
        # Cleanup temp directory
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
