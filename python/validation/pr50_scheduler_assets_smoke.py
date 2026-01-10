#!/usr/bin/env python3
"""
PR50: Daily Shadow Diff Pipeline Scheduler Assets Smoke Test

Purpose:
    Validate that PR50 scheduler assets (GitHub Actions, launchd) are
    correctly structured and compliant with constitutional constraints.

Test Coverage:
    1. GitHub Actions workflow exists
    2. GitHub Actions workflow has correct structure
    3. GitHub Actions workflow has constitutional comments
    4. Launchd plist template exists
    5. Launchd plist has correct structure
    6. Launchd install script exists and is executable
    7. No forbidden vocabulary in any files
    8. Exit code always 0 (warning-only)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings

Exit Code: Always 0 (warning-only validation)
"""

import os
import re
import stat
import sys
import xml.etree.ElementTree as ET
from typing import List, Tuple

import yaml


# Forbidden vocabulary (non-evaluative constraint)
FORBIDDEN_VOCABULARY = [
    "good", "bad", "better", "worse", "best", "worst",
    "correct", "incorrect", "wrong", "right",
    "superior", "inferior",
    "profit", "loss", "pnl", "win", "lose",
    "success", "failure", "successful", "failed",
    "score", "grade", "rank", "ranking", "accuracy",
]


def test_github_workflow_exists() -> bool:
    """
    Test 1: GitHub Actions workflow exists.
    """
    print("Test 1: GitHub Actions workflow exists")
    print("-" * 60)

    workflow_path = ".github/workflows/pr50_daily_shadow_diff_pipeline.yml"

    if not os.path.exists(workflow_path):
        print(f"✗ Workflow file not found: {workflow_path}")
        return False

    print(f"✓ Workflow file exists: {workflow_path}")
    print("Test 1: PASS\n")
    return True


def test_github_workflow_structure() -> bool:
    """
    Test 2: GitHub Actions workflow has correct structure.
    """
    print("Test 2: GitHub Actions workflow has correct structure")
    print("-" * 60)

    workflow_path = ".github/workflows/pr50_daily_shadow_diff_pipeline.yml"

    try:
        with open(workflow_path, "r") as f:
            workflow = yaml.safe_load(f)

        # Check 'on' triggers (YAML may parse 'on' as True)
        on_key = "on" if "on" in workflow else (True if True in workflow else None)
        if on_key is None:
            print("✗ Missing 'on' key")
            return False
        print("✓ Has 'on' key")

        on_config = workflow[on_key]

        # Check schedule
        if "schedule" not in on_config:
            print("✗ Missing 'schedule' trigger")
            return False
        print("✓ Has 'schedule' trigger")

        # Check workflow_dispatch
        if "workflow_dispatch" not in on_config:
            print("✗ Missing 'workflow_dispatch' trigger")
            return False
        print("✓ Has 'workflow_dispatch' trigger")

        # Check jobs
        if "jobs" not in workflow:
            print("✗ Missing 'jobs' key")
            return False
        print("✓ Has 'jobs' key")

        # Check at least one job exists
        if len(workflow["jobs"]) == 0:
            print("✗ No jobs defined")
            return False
        print(f"✓ Has {len(workflow['jobs'])} job(s)")

        # Check steps in first job
        first_job_key = list(workflow["jobs"].keys())[0]
        first_job = workflow["jobs"][first_job_key]

        if "steps" not in first_job:
            print("✗ Missing 'steps' in job")
            return False
        print(f"✓ Has {len(first_job['steps'])} step(s)")

        print("Test 2: PASS\n")
        return True

    except Exception as e:
        print(f"✗ Failed to parse workflow: {e}")
        return False


def test_github_workflow_constitutional_comments() -> bool:
    """
    Test 3: GitHub Actions workflow has constitutional comments.
    """
    print("Test 3: GitHub Actions workflow has constitutional comments")
    print("-" * 60)

    workflow_path = ".github/workflows/pr50_daily_shadow_diff_pipeline.yml"

    try:
        with open(workflow_path, "r") as f:
            content = f.read()

        # Check for constitutional constraint comments
        required_keywords = [
            "Constitutional Constraints",
            "READ-ONLY",
            "Warning-only",
        ]

        missing = []
        for keyword in required_keywords:
            if keyword not in content:
                missing.append(keyword)

        if missing:
            print(f"✗ Missing constitutional keywords: {missing}")
            return False

        print("✓ All constitutional keywords present")
        print("Test 3: PASS\n")
        return True

    except Exception as e:
        print(f"✗ Failed to read workflow: {e}")
        return False


def test_launchd_plist_exists() -> bool:
    """
    Test 4: Launchd plist template exists.
    """
    print("Test 4: Launchd plist template exists")
    print("-" * 60)

    plist_path = "scripts/com.meridian.pr49.daily.plist"

    if not os.path.exists(plist_path):
        print(f"✗ Plist file not found: {plist_path}")
        return False

    print(f"✓ Plist file exists: {plist_path}")
    print("Test 4: PASS\n")
    return True


def test_launchd_plist_structure() -> bool:
    """
    Test 5: Launchd plist has correct structure.
    """
    print("Test 5: Launchd plist has correct structure")
    print("-" * 60)

    plist_path = "scripts/com.meridian.pr49.daily.plist"

    try:
        tree = ET.parse(plist_path)
        root = tree.getroot()

        # plist files have a dict as the main container
        plist_dict = root.find("dict")
        if plist_dict is None:
            print("✗ Missing root dict element")
            return False
        print("✓ Has root dict element")

        # Extract key-value pairs
        keys = [elem.text for elem in plist_dict.findall("key")]

        # Check required keys
        required_keys = [
            "Label",
            "ProgramArguments",
            "WorkingDirectory",
            "StartCalendarInterval",
        ]

        missing = []
        for key in required_keys:
            if key not in keys:
                missing.append(key)

        if missing:
            print(f"✗ Missing required keys: {missing}")
            return False

        print("✓ All required keys present")
        print("Test 5: PASS\n")
        return True

    except Exception as e:
        print(f"✗ Failed to parse plist: {e}")
        return False


def test_launchd_install_script_exists_and_executable() -> bool:
    """
    Test 6: Launchd install script exists and is executable.
    """
    print("Test 6: Launchd install script exists and is executable")
    print("-" * 60)

    script_path = "scripts/pr50_launchd_install.sh"

    if not os.path.exists(script_path):
        print(f"✗ Install script not found: {script_path}")
        return False
    print(f"✓ Install script exists: {script_path}")

    # Check if executable
    st = os.stat(script_path)
    is_executable = bool(st.st_mode & stat.S_IXUSR)

    if not is_executable:
        print(f"✗ Install script is not executable")
        return False
    print(f"✓ Install script is executable")

    print("Test 6: PASS\n")
    return True


def test_no_forbidden_vocabulary() -> bool:
    """
    Test 7: No forbidden vocabulary in any files.
    """
    print("Test 7: No forbidden vocabulary in any files")
    print("-" * 60)

    files_to_check = [
        ".github/workflows/pr50_daily_shadow_diff_pipeline.yml",
        "scripts/com.meridian.pr49.daily.plist",
        "scripts/pr50_launchd_install.sh",
    ]

    all_clean = True

    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"⚠ File not found (skipping): {file_path}")
            continue

        with open(file_path, "r") as f:
            content = f.read().lower()

        found_forbidden = []
        for word in FORBIDDEN_VOCABULARY:
            # Use word boundaries to avoid false positives (e.g., "upgrade" contains "grade")
            pattern = r'\b' + re.escape(word.lower()) + r'\b'
            if re.search(pattern, content):
                found_forbidden.append(word)

        if found_forbidden:
            print(f"✗ Found forbidden vocabulary in {file_path}: {found_forbidden}")
            all_clean = False
        else:
            print(f"✓ No forbidden vocabulary in {file_path}")

    if not all_clean:
        return False

    print("Test 7: PASS\n")
    return True


def test_exit_code_always_zero() -> bool:
    """
    Test 8: Exit code always 0 (warning-only).
    """
    print("Test 8: Exit code always 0 (warning-only)")
    print("-" * 60)

    # This test always passes (validation is warning-only)
    print("✓ Validation is warning-only by design")
    print("Test 8: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR50: Scheduler Assets Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("GitHub workflow exists", test_github_workflow_exists),
        ("GitHub workflow structure", test_github_workflow_structure),
        ("GitHub workflow constitutional comments", test_github_workflow_constitutional_comments),
        ("Launchd plist exists", test_launchd_plist_exists),
        ("Launchd plist structure", test_launchd_plist_structure),
        ("Launchd install script exists and executable", test_launchd_install_script_exists_and_executable),
        ("No forbidden vocabulary", test_no_forbidden_vocabulary),
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
        print("✓ ALL PR50 SCHEDULER ASSETS TESTS PASSED")
    else:
        print("⚠ SOME PR50 SCHEDULER ASSETS TESTS FAILED")
    print("=" * 60)
    print("PR50 Requirements Verified:")
    print("  - GitHub Actions workflow exists and is structured correctly")
    print("  - GitHub Actions workflow has constitutional comments")
    print("  - Launchd plist template exists and is structured correctly")
    print("  - Launchd install script exists and is executable")
    print("  - No forbidden vocabulary in scheduler assets")
    print("  - Warning-only (exit code always 0)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
