#!/usr/bin/env python3
"""
PR28: Confidence Reason Generation Stub Smoke Test

Purpose: Verify reason builder produces PR27-compliant structure.

Requirements:
- build_confidence_reason is importable and callable
- Never raises exceptions (even with empty observation)
- Returns empty string OR PR27-compliant structure
- evaluate_confidence returns (str, str) with builder-generated reason
- Exit code always 0 (warning-only)

PR27 Structure:
Source:<text>; Stability:<text>; Consistency:<text>; Completeness:<text>

Non-Goals:
- No semantic content validation
- No reason usage testing
- No behavior changes
"""

import sys
import os
import re

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from confidence.confidence_reason_builder import build_confidence_reason
from confidence.confidence_evaluator import evaluate_confidence


# PR27 structure pattern (allow empty components)
PR27_PATTERN = re.compile(r'^Source:.*; Stability:.*; Consistency:.*; Completeness:.*$')


def test_builder_exists():
    """Test reason builder function exists and is callable."""
    print("\nTest 1: Reason Builder Exists")
    print("-" * 60)

    # Verify function exists
    assert callable(build_confidence_reason), "build_confidence_reason must be callable"
    print("✓ build_confidence_reason function exists")

    # Verify function returns string
    obs = {"intent_primary": "IDLE", "regime": "stable_range"}
    result = build_confidence_reason(obs)
    assert isinstance(result, str), "build_confidence_reason must return string"
    print("✓ Returns string")

    print("Test 1: PASS (2/2)")
    return True


def test_builder_no_exceptions():
    """Test builder never raises exceptions."""
    print("\nTest 2: Builder Never Raises Exceptions")
    print("-" * 60)

    # Test with empty observation
    try:
        result = build_confidence_reason({})
        assert isinstance(result, str)
        print("✓ Empty observation → no exception")
    except Exception as e:
        assert False, f"Empty observation should not raise exception: {e}"

    # Test with partial observation
    try:
        result = build_confidence_reason({"entropy_bp": 5000})
        assert isinstance(result, str)
        print("✓ Partial observation → no exception")
    except Exception as e:
        assert False, f"Partial observation should not raise exception: {e}"

    # Test with full observation
    try:
        result = build_confidence_reason({
            "intent_primary": "IDLE",
            "regime": "stable_range",
            "base_action": "HOLD",
            "overlay_rule": "ALLOW",
            "entropy_bp": 5000,
        })
        assert isinstance(result, str)
        print("✓ Full observation → no exception")
    except Exception as e:
        assert False, f"Full observation should not raise exception: {e}"

    print("Test 2: PASS (3/3)")
    return True


def test_builder_structure_compliance():
    """Test builder returns empty string OR PR27-compliant structure."""
    print("\nTest 3: Builder Structure Compliance (PR27)")
    print("-" * 60)

    obs = {"intent_primary": "IDLE", "regime": "stable_range"}
    result = build_confidence_reason(obs)

    # Empty string is always valid (PR21 absence semantics)
    if result == "":
        print("✓ Builder returns empty string (undefined - PR21 compliant)")
        print("Test 3: PASS (1/1)")
        return True

    # Non-empty must match PR27 structure
    if PR27_PATTERN.match(result):
        print(f"✓ Builder returns PR27-compliant structure")
        print(f"  Result: {result}")
        print("Test 3: PASS (1/1)")
        return True

    # If neither empty nor PR27-compliant, fail
    assert False, f"Builder returned non-compliant string: {repr(result)}"


def test_evaluator_with_builder():
    """Test evaluator uses builder for confidence_reason."""
    print("\nTest 4: Evaluator Integration with Builder")
    print("-" * 60)

    obs = {"intent_primary": "IDLE", "regime": "stable_range"}

    # Call evaluator
    value, reason = evaluate_confidence(obs)

    # Verify return types
    assert isinstance(value, str), "confidence_value must be string"
    assert isinstance(reason, str), "confidence_reason must be string"
    print("✓ Evaluator returns (str, str)")

    # Verify reason is empty or PR27-compliant
    if reason == "":
        print("✓ confidence_reason: empty string (undefined)")
    elif PR27_PATTERN.match(reason):
        print(f"✓ confidence_reason: PR27-compliant")
        print(f"  Reason: {reason}")
    else:
        assert False, f"confidence_reason not compliant: {repr(reason)}"

    print("Test 4: PASS (2/2)")
    return True


def test_deterministic():
    """Test builder is deterministic (same input → same output)."""
    print("\nTest 5: Builder Deterministic")
    print("-" * 60)

    obs = {"intent_primary": "IDLE", "regime": "stable_range", "entropy_bp": 5000}

    # Call multiple times with same input
    result1 = build_confidence_reason(obs)
    result2 = build_confidence_reason(obs)

    assert result1 == result2, "Same observation must produce same reason (determinism)"
    print("✓ Deterministic: same observation → same reason")
    print(f"  Result: {repr(result1)}")

    print("Test 5: PASS (1/1)")
    return True


def test_pr21_compliance():
    """Test PR21 absence semantics (empty string always valid)."""
    print("\nTest 6: PR21 Absence Semantics Compliance")
    print("-" * 60)

    # Empty string is always valid
    result = build_confidence_reason({})

    # Either empty or PR27-compliant is acceptable
    if result == "":
        print("✓ Empty observation → empty string (PR21 compliant)")
    elif PR27_PATTERN.match(result):
        print("✓ Empty observation → PR27 structure (also valid)")
    else:
        assert False, f"Result must be empty or PR27-compliant: {repr(result)}"

    print("Test 6: PASS (1/1)")
    return True


def main():
    """Run all PR28 Confidence Reason Stub smoke tests."""
    print("=" * 60)
    print("PR28: Confidence Reason Generation Stub Smoke Test")
    print("=" * 60)
    print("IMPORTANT: READ-ONLY stub. No behavior changes. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Builder Exists", test_builder_exists()))
        results.append(("Builder Never Raises Exceptions", test_builder_no_exceptions()))
        results.append(("Builder Structure Compliance", test_builder_structure_compliance()))
        results.append(("Evaluator Integration", test_evaluator_with_builder()))
        results.append(("Builder Deterministic", test_deterministic()))
        results.append(("PR21 Compliance", test_pr21_compliance()))

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
            print("✓ ALL PR28 CONFIDENCE REASON STUB TESTS PASSED")
            print("=" * 60)
            print("PR28 Requirements Verified:")
            print("  - Reason builder exists and is callable")
            print("  - Builder never raises exceptions")
            print("  - Builder returns empty or PR27-compliant structure")
            print("  - Evaluator integration successful")
            print("  - Builder is deterministic")
            print("  - PR21 absence semantics preserved")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR28 CONFIDENCE REASON STUB TESTS FAILED")
            print("=" * 60)
            print("Exit code: 0 (warning-only, never fails)")
            return 0  # Always exit 0 (warning-only)

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"FAIL: {e}")
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
