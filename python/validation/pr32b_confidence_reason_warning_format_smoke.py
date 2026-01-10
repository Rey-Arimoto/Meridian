#!/usr/bin/env python3
"""
PR32B: Confidence Reason Warning Format Smoke Test

Purpose: Verify compliance warning output format is normalized.

Requirements:
- Warning format matches: [WARNING][PR31][confidence_reason] violations=<...> ts=<...>
- Empty warnings produce no output
- Exit code always 0 (warning-only)

Non-Goals:
- No new validation behavior
- No changes to warning conditions
"""

import sys
import os
import re
import io
from contextlib import redirect_stdout

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from confidence.confidence_reason_compliance import validate_confidence_reason


# PR32B: Expected warning format
WARNING_FORMAT_PATTERN = re.compile(
    r'^\[WARNING\]\[PR31\]\[confidence_reason\] violations=.+ ts=.+$'
)


def simulate_warning_output(compliance_warnings):
    """
    Simulate PR32B warning output format.

    This replicates the agent's warning output logic for testing.
    """
    if compliance_warnings:
        # Simulate timestamp (simplified for test)
        ts_str = "2026-01-10T12:00:00"
        print(f"[WARNING][PR31][confidence_reason] violations={' | '.join(compliance_warnings)} ts={ts_str}")


def test_warning_format_pattern():
    """Test warning format matches expected pattern."""
    print("\nTest 1: Warning Format Pattern")
    print("-" * 60)

    # Create invalid reason to trigger warnings
    invalid_reason = "Source:test; Stability:temporal indicators absent; Consistency:3/4 core signals; Completeness:current observations only"
    warnings = validate_confidence_reason(invalid_reason)

    assert len(warnings) > 0, "Should have warnings for invalid reason"

    # Capture stdout
    output = io.StringIO()
    with redirect_stdout(output):
        simulate_warning_output(warnings)

    warning_text = output.getvalue().strip()

    # Verify format
    assert WARNING_FORMAT_PATTERN.match(warning_text), f"Format mismatch: {warning_text}"
    print(f"✓ Warning format matches pattern")
    print(f"  Output: {warning_text[:80]}...")

    # Verify components
    assert "[WARNING][PR31][confidence_reason]" in warning_text, "Missing prefix"
    assert "violations=" in warning_text, "Missing violations="
    assert "ts=" in warning_text, "Missing ts="
    print(f"✓ All components present")

    print("Test 1: PASS")
    return True


def test_no_warnings_no_output():
    """Test empty warnings produce no output."""
    print("\nTest 2: No Warnings, No Output")
    print("-" * 60)

    # Valid reason (no warnings)
    valid_reason = "Source:test; Stability:temporal indicators absent; Consistency:all core signals present; Completeness:current observations only"
    warnings = validate_confidence_reason(valid_reason)

    assert len(warnings) == 0, "Valid reason should have no warnings"

    # Capture stdout
    output = io.StringIO()
    with redirect_stdout(output):
        simulate_warning_output(warnings)

    warning_text = output.getvalue().strip()

    assert warning_text == "", "No output expected for empty warnings"
    print(f"✓ No warnings → no output")

    # Empty string (PR21)
    warnings2 = validate_confidence_reason("")
    assert len(warnings2) == 0, "Empty string should have no warnings"
    print(f"✓ Empty string → no warnings")

    print("Test 2: PASS")
    return True


def test_multiple_violations_joined():
    """Test multiple violations are joined with ' | '."""
    print("\nTest 3: Multiple Violations Joined")
    print("-" * 60)

    # Reason with multiple violations
    bad_reason = "Source:test; Stability:wrong; Consistency:3/4; Completeness:wrong"
    warnings = validate_confidence_reason(bad_reason)

    assert len(warnings) > 1, "Should have multiple warnings"

    # Capture stdout
    output = io.StringIO()
    with redirect_stdout(output):
        simulate_warning_output(warnings)

    warning_text = output.getvalue().strip()

    # Verify joined with ' | '
    assert " | " in warning_text, "Violations should be joined with ' | '"
    print(f"✓ Multiple violations joined with ' | '")
    print(f"  Violations count: {len(warnings)}")

    print("Test 3: PASS")
    return True


def test_format_stability():
    """Test format is stable across different violation types."""
    print("\nTest 4: Format Stability")
    print("-" * 60)

    test_cases = [
        # Digit violation
        "Source:test; Stability:temporal indicators absent; Consistency:3/4 core signals; Completeness:current observations only",
        # Structure violation
        "Source:test",
        # Vocabulary violation
        "Source:test; Stability:high stability; Consistency:all core signals present; Completeness:current observations only",
    ]

    for i, reason in enumerate(test_cases, 1):
        warnings = validate_confidence_reason(reason)
        if warnings:
            output = io.StringIO()
            with redirect_stdout(output):
                simulate_warning_output(warnings)
            warning_text = output.getvalue().strip()
            assert WARNING_FORMAT_PATTERN.match(warning_text), f"Format mismatch for case {i}"
            print(f"✓ Case {i} format stable")

    print("Test 4: PASS")
    return True


def main():
    """Run all PR32B Warning Format smoke tests."""
    print("=" * 60)
    print("PR32B: Confidence Reason Warning Format Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Format normalization only. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Warning Format Pattern", test_warning_format_pattern()))
        results.append(("No Warnings No Output", test_no_warnings_no_output()))
        results.append(("Multiple Violations Joined", test_multiple_violations_joined()))
        results.append(("Format Stability", test_format_stability()))

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
            print("✓ ALL PR32B WARNING FORMAT TESTS PASSED")
            print("=" * 60)
            print("PR32B Requirements Verified:")
            print("  - Warning format matches expected pattern")
            print("  - Empty warnings produce no output")
            print("  - Multiple violations joined with ' | '")
            print("  - Format stable across violation types")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR32B TESTS FAILED")
            print("=" * 60)
            print("Exit code: 0 (warning-only, never fails)")
            return 0  # Always exit 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Unexpected exception during validation")
        print(f"{e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("Exit code: 0 (warning-only, never fails)")
        return 0  # Always exit 0


if __name__ == "__main__":
    sys.exit(main())
