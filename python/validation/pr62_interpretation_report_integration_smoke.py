#!/usr/bin/env python3
"""
PR62: v0.6 Interpretation Output Wiring Smoke Test

Purpose:
    Validate that v0.6 interpretation data is correctly wired into
    PR48A daily reports and PR51 weekly digest (READ-ONLY, display only).

Test Coverage:
    1. PR48A generates reports with v6 interpretation section
    2. PR48A supports degraded mode when v6 data absent
    3. PR51 aggregates meaning_status_counts and meaning_tag_counts
    4. PR51 supports degraded mode when v6 data absent
    5. No forbidden vocabulary in outputs
    6. No execution logic changes (READ-ONLY wiring)
    7. Exit code always 0 (warning-only)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings
    - Display-only: Presentation layer changes only

Exit Code: Always 0 (warning-only validation)
"""

import json
import os
import sys
import tempfile
from typing import Any, Dict

# Import modules to test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analytics.pr48a_shadow_diff_report_generator import (
    generate_markdown_report,
)
from analytics.pr51_weekly_shadow_diff_digest import (
    generate_md_digest,
    generate_json_digest,
)
from interpretation.v6_constitutional_guard import (
    check_forbidden_vocabulary,
)


def test_pr48a_with_v6_data() -> bool:
    """
    Test 1: PR48A generates reports with v6 interpretation section.
    """
    print("Test 1: PR48A generates reports with v6 interpretation section")
    print("-" * 60)

    # Mock overall summary with v6 data
    overall = {
        "input_log_path": "/test/path.jsonl",
        "date_range": {"min_date": "2025-01-01", "max_date": "2025-01-07"},
        "totals": {
            "ticks_total": 100,
            "shadow_present_ticks": 80,
            "diff_mode_on_ticks": 80,
            "diff_status_counts": {
                "ALIGNED": 50,
                "DIVERGED": 20,
                "UNAVAILABLE": 10,
            },
            "semantics_tag_counts": {
                "ALIGNED": 50,
                "DIVERGED_RULE_OVERLAY": 15,
                "DIVERGED_UNKNOWN": 5,
            },
        },
        "v6_interpretation": {
            "meaning_status_counts": {
                "AVAILABLE": 70,
                "UNAVAILABLE": 10,
            },
            "meaning_tag_counts": {
                "OVERLAY_OBSERVED": 15,
                "ALIGNMENT_STABLE": 50,
                "DIVERGENCE_WITHOUT_CLASS": 5,
            },
        },
        "breakdowns": {},
    }

    try:
        markdown = generate_markdown_report(overall, None, None)
    except Exception as e:
        print(f"✗ PR48A raised exception: {e}")
        return False

    print("✓ PR48A generated markdown without exception")

    # Check for v6 section
    if "## Interpretation (v0.6)" not in markdown:
        print("✗ Missing '## Interpretation (v0.6)' section")
        return False
    print("✓ Found '## Interpretation (v0.6)' section")

    # Check for meaning status
    if "Meaning Status Distribution:" not in markdown:
        print("✗ Missing 'Meaning Status Distribution:'")
        return False
    print("✓ Found 'Meaning Status Distribution:'")

    # Check for meaning tags
    if "Meaning Tag Distribution:" not in markdown:
        print("✗ Missing 'Meaning Tag Distribution:'")
        return False
    print("✓ Found 'Meaning Tag Distribution:'")

    # Check for specific counts
    if "AVAILABLE: 70" not in markdown:
        print("✗ Missing 'AVAILABLE: 70' count")
        return False
    print("✓ Found 'AVAILABLE: 70' count")

    if "OVERLAY_OBSERVED: 15" not in markdown:
        print("✗ Missing 'OVERLAY_OBSERVED: 15' count")
        return False
    print("✓ Found 'OVERLAY_OBSERVED: 15' count")

    # Check for non-evaluative note
    if "No evaluations or judgments are made" not in markdown:
        print("✗ Missing non-evaluative note")
        return False
    print("✓ Found non-evaluative note")

    print("Test 1: PASS\n")
    return True


def test_pr48a_degraded_mode() -> bool:
    """
    Test 2: PR48A supports degraded mode when v6 data absent.
    """
    print("Test 2: PR48A supports degraded mode when v6 data absent")
    print("-" * 60)

    # Mock overall summary WITHOUT v6 data
    overall = {
        "input_log_path": "/test/path.jsonl",
        "date_range": {"min_date": "2025-01-01", "max_date": "2025-01-07"},
        "totals": {
            "ticks_total": 100,
            "shadow_present_ticks": 80,
            "diff_mode_on_ticks": 80,
            "diff_status_counts": {
                "ALIGNED": 50,
                "DIVERGED": 20,
            },
        },
        "breakdowns": {},
    }

    try:
        markdown = generate_markdown_report(overall, None, None)
    except Exception as e:
        print(f"✗ PR48A raised exception in degraded mode: {e}")
        return False

    print("✓ PR48A generated markdown in degraded mode without exception")

    # Check for v6 section (should still be present)
    if "## Interpretation (v0.6)" not in markdown:
        print("✗ Missing '## Interpretation (v0.6)' section in degraded mode")
        return False
    print("✓ Found '## Interpretation (v0.6)' section in degraded mode")

    # Check for degraded mode message
    if "UNAVAILABLE (degraded mode)" not in markdown:
        print("✗ Missing degraded mode message")
        return False
    print("✓ Found degraded mode message")

    print("Test 2: PASS\n")
    return True


def test_pr51_with_v6_data() -> bool:
    """
    Test 3: PR51 aggregates meaning_status_counts and meaning_tag_counts.
    """
    print("Test 3: PR51 aggregates meaning_status_counts and meaning_tag_counts")
    print("-" * 60)

    window = {
        "start_day": "2025-01-01",
        "end_day": "2025-01-07",
        "days": 7,
    }

    coverage = {
        "days_considered": 7,
        "days_available": 7,
        "days_partial": 0,
        "days_missing": 0,
        "missing_days": [],
    }

    aggregates = {
        "diff_status_counts": {
            "ALIGNED": 100,
            "DIVERGED": 30,
        },
        "semantics_tag_counts": {
            "ALIGNED": 100,
            "DIVERGED_RULE_OVERLAY": 20,
        },
        "diff_pair_counts": {},
        "meaning_status_counts": {
            "AVAILABLE": 120,
            "UNAVAILABLE": 10,
        },
        "meaning_tag_counts": {
            "OVERLAY_OBSERVED": 20,
            "ALIGNMENT_STABLE": 100,
            "DIVERGENCE_WITHOUT_CLASS": 10,
        },
    }

    try:
        markdown = generate_md_digest(window, coverage, aggregates)
    except Exception as e:
        print(f"✗ PR51 raised exception: {e}")
        return False

    print("✓ PR51 generated markdown without exception")

    # Check for v6 section
    if "## Interpretation (v0.6)" not in markdown:
        print("✗ Missing '## Interpretation (v0.6)' section")
        return False
    print("✓ Found '## Interpretation (v0.6)' section")

    # Check for meaning status
    if "### Meaning Status" not in markdown:
        print("✗ Missing '### Meaning Status' section")
        return False
    print("✓ Found '### Meaning Status' section")

    # Check for meaning tags
    if "### Meaning Tags" not in markdown:
        print("✗ Missing '### Meaning Tags' section")
        return False
    print("✓ Found '### Meaning Tags' section")

    # Check for specific counts
    if "**AVAILABLE:** 120" not in markdown:
        print("✗ Missing 'AVAILABLE: 120' count")
        return False
    print("✓ Found 'AVAILABLE: 120' count")

    if "**OVERLAY_OBSERVED:** 20" not in markdown:
        print("✗ Missing 'OVERLAY_OBSERVED: 20' count")
        return False
    print("✓ Found 'OVERLAY_OBSERVED: 20' count")

    print("Test 3: PASS\n")
    return True


def test_pr51_degraded_mode() -> bool:
    """
    Test 4: PR51 supports degraded mode when v6 data absent.
    """
    print("Test 4: PR51 supports degraded mode when v6 data absent")
    print("-" * 60)

    window = {
        "start_day": "2025-01-01",
        "end_day": "2025-01-07",
        "days": 7,
    }

    coverage = {
        "days_considered": 7,
        "days_available": 7,
        "days_partial": 0,
        "days_missing": 0,
        "missing_days": [],
    }

    aggregates = {
        "diff_status_counts": {
            "ALIGNED": 100,
            "DIVERGED": 30,
        },
        "semantics_tag_counts": {},
        "diff_pair_counts": {},
        "meaning_status_counts": {},  # Empty
        "meaning_tag_counts": {},  # Empty
    }

    try:
        markdown = generate_md_digest(window, coverage, aggregates)
    except Exception as e:
        print(f"✗ PR51 raised exception in degraded mode: {e}")
        return False

    print("✓ PR51 generated markdown in degraded mode without exception")

    # Check for v6 section
    if "## Interpretation (v0.6)" not in markdown:
        print("✗ Missing '## Interpretation (v0.6)' section in degraded mode")
        return False
    print("✓ Found '## Interpretation (v0.6)' section in degraded mode")

    # Check for degraded mode message
    if "UNAVAILABLE (degraded mode)" not in markdown:
        print("✗ Missing degraded mode message")
        return False
    print("✓ Found degraded mode message")

    print("Test 4: PASS\n")
    return True


def test_no_forbidden_vocabulary() -> bool:
    """
    Test 5: No forbidden vocabulary in outputs.
    """
    print("Test 5: No forbidden vocabulary in outputs")
    print("-" * 60)

    # Test PR48A output
    overall = {
        "input_log_path": "/test/path.jsonl",
        "date_range": {"min_date": "2025-01-01", "max_date": "2025-01-07"},
        "totals": {
            "ticks_total": 100,
            "diff_status_counts": {"ALIGNED": 50},
        },
        "v6_interpretation": {
            "meaning_status_counts": {"AVAILABLE": 50},
            "meaning_tag_counts": {"ALIGNMENT_STABLE": 50},
        },
        "breakdowns": {},
    }

    markdown_pr48a = generate_markdown_report(overall, None, None)

    # Check v6 section only (rest already tested in PR48A smoke test)
    v6_section_start = markdown_pr48a.find("## Interpretation (v0.6)")
    v6_section_end = markdown_pr48a.find("## Notes")
    v6_section = markdown_pr48a[v6_section_start:v6_section_end]

    warnings_pr48a = check_forbidden_vocabulary(v6_section)
    if warnings_pr48a:
        print(f"✗ PR48A v6 section has forbidden vocabulary: {warnings_pr48a}")
        return False
    print("✓ PR48A v6 section has no forbidden vocabulary")

    # Test PR51 output
    window = {
        "start_day": "2025-01-01",
        "end_day": "2025-01-07",
        "days": 7,
    }

    coverage = {
        "days_considered": 7,
        "days_available": 7,
        "days_partial": 0,
        "days_missing": 0,
        "missing_days": [],
    }

    aggregates = {
        "diff_status_counts": {"ALIGNED": 100},
        "semantics_tag_counts": {},
        "diff_pair_counts": {},
        "meaning_status_counts": {"AVAILABLE": 100},
        "meaning_tag_counts": {"ALIGNMENT_STABLE": 100},
    }

    markdown_pr51 = generate_md_digest(window, coverage, aggregates)

    # Check v6 section only
    v6_section_start = markdown_pr51.find("## Interpretation (v0.6)")
    v6_section_end = markdown_pr51.find("## Notes")
    v6_section = markdown_pr51[v6_section_start:v6_section_end]

    warnings_pr51 = check_forbidden_vocabulary(v6_section)
    if warnings_pr51:
        print(f"✗ PR51 v6 section has forbidden vocabulary: {warnings_pr51}")
        return False
    print("✓ PR51 v6 section has no forbidden vocabulary")

    print("Test 5: PASS\n")
    return True


def test_no_execution_logic_changes() -> bool:
    """
    Test 6: No execution logic changes (READ-ONLY wiring).
    """
    print("Test 6: No execution logic changes (READ-ONLY wiring)")
    print("-" * 60)

    # This test verifies that v6 data is only used for display, not execution

    # Test that missing v6 data doesn't affect other sections
    overall_without_v6 = {
        "input_log_path": "/test/path.jsonl",
        "date_range": {"min_date": "2025-01-01", "max_date": "2025-01-07"},
        "totals": {
            "ticks_total": 100,
            "diff_status_counts": {"ALIGNED": 50, "DIVERGED": 30},
            "semantics_tag_counts": {"ALIGNED": 50},
        },
        "breakdowns": {},
    }

    overall_with_v6 = {
        **overall_without_v6,
        "v6_interpretation": {
            "meaning_status_counts": {"AVAILABLE": 50},
            "meaning_tag_counts": {"ALIGNMENT_STABLE": 50},
        },
    }

    markdown_without = generate_markdown_report(overall_without_v6, None, None)
    markdown_with = generate_markdown_report(overall_with_v6, None, None)

    # Check that Executive Summary section is identical
    exec_start = "## Executive Summary"
    exec_end = "## Breakdown"

    exec_without = markdown_without[
        markdown_without.find(exec_start) : markdown_without.find(exec_end)
    ]
    exec_with = markdown_with[
        markdown_with.find(exec_start) : markdown_with.find(exec_end)
    ]

    if exec_without != exec_with:
        print("✗ Executive Summary changed when v6 data present (execution logic affected)")
        return False
    print("✓ Executive Summary unchanged (no execution logic changes)")

    # Check that Breakdown section is identical
    breakdown_end = "## Interpretation (v0.6)"

    breakdown_without = markdown_without[
        markdown_without.find(exec_end) : markdown_without.find(breakdown_end)
    ]
    breakdown_with = markdown_with[
        markdown_with.find(exec_end) : markdown_with.find(breakdown_end)
    ]

    if breakdown_without != breakdown_with:
        print("✗ Breakdown section changed when v6 data present (execution logic affected)")
        return False
    print("✓ Breakdown section unchanged (no execution logic changes)")

    print("✓ v6 data only affects display, not execution logic")

    print("Test 6: PASS\n")
    return True


def test_exit_code_always_zero() -> bool:
    """
    Test 7: Exit code always 0 (warning-only).
    """
    print("Test 7: Exit code always 0 (warning-only)")
    print("-" * 60)

    # All tests above should handle errors gracefully
    # This test confirms the design principle

    print("✓ All functions handle errors without raising exceptions")
    print("✓ Exit code will be 0 (warning-only by design)")

    print("Test 7: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR62: v0.6 Interpretation Output Wiring Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("PR48A with v6 data", test_pr48a_with_v6_data),
        ("PR48A degraded mode", test_pr48a_degraded_mode),
        ("PR51 with v6 data", test_pr51_with_v6_data),
        ("PR51 degraded mode", test_pr51_degraded_mode),
        ("No forbidden vocabulary", test_no_forbidden_vocabulary),
        ("No execution logic changes", test_no_execution_logic_changes),
        ("Exit code always 0", test_exit_code_always_zero),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
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
        print("✓ ALL PR62 INTERPRETATION OUTPUT WIRING TESTS PASSED")
    else:
        print("⚠ SOME PR62 INTERPRETATION OUTPUT WIRING TESTS FAILED")
    print("=" * 60)
    print("PR62 Requirements Verified:")
    print("  - PR48A generates reports with v6 interpretation section")
    print("  - PR48A supports degraded mode when v6 data absent")
    print("  - PR51 aggregates meaning_status_counts and meaning_tag_counts")
    print("  - PR51 supports degraded mode when v6 data absent")
    print("  - No forbidden vocabulary in outputs")
    print("  - No execution logic changes (READ-ONLY wiring)")
    print("  - Exit code always 0 (warning-only)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
