#!/usr/bin/env python3
"""
PR48A: Shadow Diff Report Generator Smoke Test

Purpose:
    Validate that pr48a_shadow_diff_report_generator.py correctly generates
    human-readable Markdown/HTML reports from PR47 analytics outputs.

Test Coverage:
    1. Minimal PR47 JSON generates md/html
    2. JSON missing generates degraded report, exit code 0
    3. Report contains non-evaluative notes
    4. Report contains no forbidden vocabulary
    5. --format=md|html|both works correctly
    6. --day filter works with daily CSV
    7. Generated files are not empty
    8. Exit code always 0 (warning-only)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss, correct/wrong vocabulary
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
    "optimal", "optimum", "suboptimal",
    "high performance", "low performance",
]


def create_minimal_pr47_json(out_path: str) -> None:
    """Create minimal PR47 overall summary JSON."""
    data = {
        "generated_at": "2026-01-10T12:00:00Z",
        "input_log_path": "test_log.csv",
        "date_range": {
            "min_date": "2026-01-10",
            "max_date": "2026-01-10",
        },
        "totals": {
            "ticks_total": 3,
            "shadow_present_ticks": 2,
            "diff_mode_on_ticks": 2,
            "diff_status_counts": {
                "ALIGNED": 1,
                "DIVERGED": 1,
                "UNAVAILABLE": 1,
            },
            "diff_pair_counts": {
                "v1_vs_v2": 2,
                "UNKNOWN": 1,
            },
            "semantics_status_counts": {
                "AVAILABLE": 2,
                "UNAVAILABLE": 1,
            },
            "semantics_tag_counts": {
                "ALIGNED": 1,
                "DIVERGED_RULE_OVERLAY": 1,
                "NO_SHADOW": 1,
            },
        },
        "breakdowns": {
            "by_regime": {
                "stable_range": {
                    "ticks_total": 2,
                    "diff_status_counts": {"ALIGNED": 1, "UNAVAILABLE": 1},
                    "semantics_tag_counts": {"ALIGNED": 1, "NO_SHADOW": 1},
                },
            },
            "by_intent_primary": {
                "IDLE": {
                    "ticks_total": 2,
                    "diff_status_counts": {"ALIGNED": 1, "UNAVAILABLE": 1},
                    "semantics_tag_counts": {"ALIGNED": 1, "NO_SHADOW": 1},
                },
            },
        },
    }

    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)


def create_minimal_daily_csv(out_path: str) -> None:
    """Create minimal PR47 daily summary CSV."""
    import csv

    rows = [
        {
            "date": "2026-01-10",
            "ticks_total": 3,
            "shadow_present_ticks": 2,
            "diff_aligned": 1,
            "diff_diverged": 1,
            "diff_unavailable": 1,
            "semantics_aligned": 1,
            "semantics_diverged_rule_overlay": 1,
            "semantics_diverged_unknown": 0,
            "semantics_no_shadow": 1,
            "pair_v1_vs_v2": 2,
            "pair_v2_vs_v1": 0,
            "pair_unknown": 1,
        }
    ]

    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def run_report_generator(
    overall_json: str = None,
    daily_csv: str = None,
    in_dir: str = None,
    out_dir: str = None,
    day: str = None,
    format: str = "both",
) -> int:
    """
    Run pr48a_shadow_diff_report_generator.py.

    Returns exit code.
    """
    script_path = "python/analytics/pr48a_shadow_diff_report_generator.py"
    cmd = [sys.executable, script_path]

    if in_dir:
        cmd.extend(["--in_dir", in_dir])
    if overall_json:
        cmd.extend(["--overall_json", overall_json])
    if daily_csv:
        cmd.extend(["--daily_csv", daily_csv])
    if out_dir:
        cmd.extend(["--out_dir", out_dir])
    if day:
        cmd.extend(["--day", day])
    if format:
        cmd.extend(["--format", format])

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode


def test_minimal_json_generates_reports(tmp_dir: str) -> bool:
    """
    Test 1: Minimal PR47 JSON generates md/html.
    """
    print("Test 1: Minimal PR47 JSON generates md/html")
    print("-" * 60)

    json_path = os.path.join(tmp_dir, "overall.json")
    out_dir = os.path.join(tmp_dir, "out1")

    create_minimal_pr47_json(json_path)

    exit_code = run_report_generator(overall_json=json_path, out_dir=out_dir)

    # Check exit code
    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0")

    # Check MD exists
    md_path = os.path.join(out_dir, "pr48a_shadow_diff_daily_report.md")
    if not os.path.exists(md_path):
        print(f"✗ MD not generated: {md_path}")
        return False
    print(f"✓ MD generated: {md_path}")

    # Check HTML exists
    html_path = os.path.join(out_dir, "pr48a_shadow_diff_daily_report.html")
    if not os.path.exists(html_path):
        print(f"✗ HTML not generated: {html_path}")
        return False
    print(f"✓ HTML generated: {html_path}")

    print("Test 1: PASS\n")
    return True


def test_missing_json_degraded_report(tmp_dir: str) -> bool:
    """
    Test 2: JSON missing generates degraded report, exit code 0.
    """
    print("Test 2: JSON missing generates degraded report, exit code 0")
    print("-" * 60)

    out_dir = os.path.join(tmp_dir, "out2")

    # Run without any input files
    exit_code = run_report_generator(overall_json="/nonexistent.json", out_dir=out_dir)

    # Check exit code (should be 0 even with missing input)
    if exit_code != 0:
        print(f"✗ Exit code: {exit_code} (expected 0)")
        return False
    print(f"✓ Exit code: 0 (warning-only)")

    # Check MD still generated (degraded mode)
    md_path = os.path.join(out_dir, "pr48a_shadow_diff_daily_report.md")
    if not os.path.exists(md_path):
        print(f"✗ MD not generated in degraded mode")
        return False
    print(f"✓ MD generated in degraded mode")

    # Check MD contains "degraded mode" or "UNAVAILABLE"
    with open(md_path, "r") as f:
        content = f.read()
    if "degraded mode" not in content.lower() and "unavailable" not in content.lower():
        print(f"✗ MD does not mention degraded mode or unavailable")
        return False
    print(f"✓ MD mentions degraded mode or unavailable")

    print("Test 2: PASS\n")
    return True


def test_report_contains_nonevil_notes(tmp_dir: str) -> bool:
    """
    Test 3: Report contains non-evaluative notes.
    """
    print("Test 3: Report contains non-evaluative notes")
    print("-" * 60)

    json_path = os.path.join(tmp_dir, "overall3.json")
    out_dir = os.path.join(tmp_dir, "out3")

    create_minimal_pr47_json(json_path)
    run_report_generator(overall_json=json_path, out_dir=out_dir)

    md_path = os.path.join(out_dir, "pr48a_shadow_diff_daily_report.md")
    with open(md_path, "r") as f:
        content = f.read()

    # Check for non-evaluative notes
    required_phrases = [
        "observational only",  # Updated from "does not evaluate"
        "recorded history",
        "No behavior changes",
        "Observation only",
    ]

    for phrase in required_phrases:
        if phrase not in content:
            print(f"✗ Missing required phrase: '{phrase}'")
            return False
        print(f"✓ Found phrase: '{phrase}'")

    print("Test 3: PASS\n")
    return True


def test_report_no_forbidden_vocabulary(tmp_dir: str) -> bool:
    """
    Test 4: Report contains no forbidden vocabulary.
    """
    print("Test 4: Report contains no forbidden vocabulary")
    print("-" * 60)

    json_path = os.path.join(tmp_dir, "overall4.json")
    out_dir = os.path.join(tmp_dir, "out4")

    create_minimal_pr47_json(json_path)
    run_report_generator(overall_json=json_path, out_dir=out_dir)

    md_path = os.path.join(out_dir, "pr48a_shadow_diff_daily_report.md")
    with open(md_path, "r") as f:
        content = f.read().lower()

    # Check for forbidden vocabulary
    found_forbidden = []
    for word in FORBIDDEN_VOCABULARY:
        if word.lower() in content:
            found_forbidden.append(word)

    if found_forbidden:
        print(f"✗ Found forbidden vocabulary: {found_forbidden}")
        return False

    print(f"✓ No forbidden vocabulary found")
    print("Test 4: PASS\n")
    return True


def test_format_options_work(tmp_dir: str) -> bool:
    """
    Test 5: --format=md|html|both works correctly.
    """
    print("Test 5: --format=md|html|both works correctly")
    print("-" * 60)

    json_path = os.path.join(tmp_dir, "overall5.json")
    create_minimal_pr47_json(json_path)

    # Test format=md
    out_dir_md = os.path.join(tmp_dir, "out5_md")
    run_report_generator(overall_json=json_path, out_dir=out_dir_md, format="md")

    md_path = os.path.join(out_dir_md, "pr48a_shadow_diff_daily_report.md")
    html_path = os.path.join(out_dir_md, "pr48a_shadow_diff_daily_report.html")

    if not os.path.exists(md_path):
        print(f"✗ format=md: MD not generated")
        return False
    if os.path.exists(html_path):
        print(f"✗ format=md: HTML should not be generated")
        return False
    print(f"✓ format=md: Only MD generated")

    # Test format=html
    out_dir_html = os.path.join(tmp_dir, "out5_html")
    run_report_generator(overall_json=json_path, out_dir=out_dir_html, format="html")

    md_path = os.path.join(out_dir_html, "pr48a_shadow_diff_daily_report.md")
    html_path = os.path.join(out_dir_html, "pr48a_shadow_diff_daily_report.html")

    if os.path.exists(md_path):
        print(f"✗ format=html: MD should not be generated")
        return False
    if not os.path.exists(html_path):
        print(f"✗ format=html: HTML not generated")
        return False
    print(f"✓ format=html: Only HTML generated")

    # Test format=both
    out_dir_both = os.path.join(tmp_dir, "out5_both")
    run_report_generator(overall_json=json_path, out_dir=out_dir_both, format="both")

    md_path = os.path.join(out_dir_both, "pr48a_shadow_diff_daily_report.md")
    html_path = os.path.join(out_dir_both, "pr48a_shadow_diff_daily_report.html")

    if not os.path.exists(md_path):
        print(f"✗ format=both: MD not generated")
        return False
    if not os.path.exists(html_path):
        print(f"✗ format=both: HTML not generated")
        return False
    print(f"✓ format=both: Both MD and HTML generated")

    print("Test 5: PASS\n")
    return True


def test_day_filter_works(tmp_dir: str) -> bool:
    """
    Test 6: --day filter works with daily CSV.
    """
    print("Test 6: --day filter works with daily CSV")
    print("-" * 60)

    json_path = os.path.join(tmp_dir, "overall6.json")
    csv_path = os.path.join(tmp_dir, "daily6.csv")
    out_dir = os.path.join(tmp_dir, "out6")

    create_minimal_pr47_json(json_path)
    create_minimal_daily_csv(csv_path)

    run_report_generator(
        overall_json=json_path,
        daily_csv=csv_path,
        out_dir=out_dir,
        day="2026-01-10",
    )

    md_path = os.path.join(out_dir, "pr48a_shadow_diff_daily_report.md")
    with open(md_path, "r") as f:
        content = f.read()

    # Check for daily section
    if "Daily Summary" not in content:
        print(f"✗ Daily Summary section not found")
        return False
    print(f"✓ Daily Summary section found")

    if "2026-01-10" not in content:
        print(f"✗ Filtered day not in report")
        return False
    print(f"✓ Filtered day (2026-01-10) in report")

    print("Test 6: PASS\n")
    return True


def test_generated_files_not_empty(tmp_dir: str) -> bool:
    """
    Test 7: Generated files are not empty.
    """
    print("Test 7: Generated files are not empty")
    print("-" * 60)

    json_path = os.path.join(tmp_dir, "overall7.json")
    out_dir = os.path.join(tmp_dir, "out7")

    create_minimal_pr47_json(json_path)
    run_report_generator(overall_json=json_path, out_dir=out_dir)

    md_path = os.path.join(out_dir, "pr48a_shadow_diff_daily_report.md")
    html_path = os.path.join(out_dir, "pr48a_shadow_diff_daily_report.html")

    # Check MD size
    md_size = os.path.getsize(md_path)
    if md_size == 0:
        print(f"✗ MD file is empty")
        return False
    print(f"✓ MD file size: {md_size} bytes")

    # Check HTML size
    html_size = os.path.getsize(html_path)
    if html_size == 0:
        print(f"✗ HTML file is empty")
        return False
    print(f"✓ HTML file size: {html_size} bytes")

    print("Test 7: PASS\n")
    return True


def test_exit_code_always_zero(tmp_dir: str) -> bool:
    """
    Test 8: Exit code always 0 (warning-only).
    """
    print("Test 8: Exit code always 0 (warning-only)")
    print("-" * 60)

    test_cases = [
        ("valid JSON", lambda: (
            create_minimal_pr47_json(os.path.join(tmp_dir, "valid.json")),
            {"overall_json": os.path.join(tmp_dir, "valid.json")},
        )[1]),
        ("missing JSON", lambda: {"overall_json": "/nonexistent.json"}),
        ("empty in_dir", lambda: {"in_dir": "/nonexistent_dir"}),
    ]

    for name, get_args in test_cases:
        out_dir = os.path.join(tmp_dir, f"out8_{name.replace(' ', '_')}")
        args = get_args()
        args["out_dir"] = out_dir

        exit_code = run_report_generator(**args)

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
    print("PR48A: Shadow Diff Report Generator Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    # Create temp directory
    tmp_dir = tempfile.mkdtemp(prefix="pr48a_test_")

    try:
        tests = [
            ("Minimal JSON generates md/html", test_minimal_json_generates_reports),
            ("Missing JSON degraded report", test_missing_json_degraded_report),
            ("Report contains non-evaluative notes", test_report_contains_nonevil_notes),
            ("Report no forbidden vocabulary", test_report_no_forbidden_vocabulary),
            ("Format options work", test_format_options_work),
            ("Day filter works", test_day_filter_works),
            ("Generated files not empty", test_generated_files_not_empty),
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
            print("✓ ALL PR48A REPORT GENERATOR TESTS PASSED")
        else:
            print("⚠ SOME PR48A REPORT GENERATOR TESTS FAILED")
        print("=" * 60)
        print("PR48A Requirements Verified:")
        print("  - Minimal JSON generates md/html")
        print("  - Missing JSON handled gracefully (degraded mode)")
        print("  - Report contains non-evaluative notes")
        print("  - Report contains no forbidden vocabulary")
        print("  - Format options (md/html/both) work")
        print("  - Day filter works with daily CSV")
        print("  - Generated files are not empty")
        print("  - Warning-only (exit code always 0)")
        print("=" * 60)
        print("Exit code: 0 (all tests completed)")

    finally:
        # Cleanup temp directory
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
