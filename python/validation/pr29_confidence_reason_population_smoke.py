#!/usr/bin/env python3
"""
PR29: Confidence Reason Population Smoke Test

Purpose: Verify reason builder generates structured confidence_reason.

Requirements:
- build_confidence_reason returns PR27-compliant structure
- Handles empty observation gracefully
- Same input produces same output (repeatability)
- Never raises exceptions
- Exit code always 0 (warning-only)

PR27 Structure:
Source:<text>; Stability:<text>; Consistency:<text>; Completeness:<text>

Non-Goals:
- No semantic content validation
- No reason quality assessment
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

# PR27 structure pattern
PR27_PATTERN = re.compile(r'^Source:.*; Stability:.*; Consistency:.*; Completeness:.*$')


def test_empty_observation():
    """Test empty observation produces valid result."""
    print("\nTest 1: Empty Observation Handling")
    print("-" * 60)

    result = build_confidence_reason({})
    assert isinstance(result, str), "Must return string"

    # Empty string is valid (PR21)
    if result == "":
        print("✓ Empty observation → empty string (PR21 compliant)")
    elif PR27_PATTERN.match(result):
        print("✓ Empty observation → structured reason (PR27 compliant)")
        print(f"  Result: {result}")
    else:
        assert False, f"Result must be empty or PR27-compliant: {repr(result)}"

    print("Test 1: PASS")
    return True


def test_minimal_observation():
    """Test minimal observation produces all 4 sections."""
    print("\nTest 2: Minimal Observation Structure")
    print("-" * 60)

    obs = {"intent_primary": "IDLE"}
    result = build_confidence_reason(obs)

    assert isinstance(result, str), "Must return string"
    assert result != "", "Minimal observation should produce structured reason"
    assert PR27_PATTERN.match(result), f"Must match PR27 structure: {repr(result)}"

    # Verify all 4 sections present
    assert "Source:" in result, "Source section missing"
    assert "Stability:" in result, "Stability section missing"
    assert "Consistency:" in result, "Consistency section missing"
    assert "Completeness:" in result, "Completeness section missing"

    print("✓ All 4 PR27 sections present")
    print(f"  Result: {result}")
    print("Test 2: PASS")
    return True


def test_repeatability():
    """Test same input produces same output."""
    print("\nTest 3: Repeatability")
    print("-" * 60)

    obs = {
        "intent_primary": "IDLE",
        "regime": "stable_range",
        "entropy_bp": 5000,
    }

    result1 = build_confidence_reason(obs)
    result2 = build_confidence_reason(obs)

    assert result1 == result2, "Same observation must produce same reason"
    print("✓ Repeatable: same observation → same reason")
    print(f"  Result: {result1}")
    print("Test 3: PASS")
    return True


def test_full_observation():
    """Test full observation with all fields."""
    print("\nTest 4: Full Observation")
    print("-" * 60)

    obs = {
        "intent_primary": "IDLE",
        "regime": "stable_range",
        "base_action": "HOLD",
        "overlay_rule": "ALLOW",
        "entropy_bp": 5000,
        "recent_intent_primary": "IDLE",
        "recent_regime": "stable_range",
    }

    result = build_confidence_reason(obs)

    assert isinstance(result, str), "Must return string"
    assert PR27_PATTERN.match(result), f"Must match PR27 structure: {repr(result)}"

    print("✓ Full observation → PR27-compliant structure")
    print(f"  Result: {result}")
    print("Test 4: PASS")
    return True


def test_no_exceptions():
    """Test builder never raises exceptions."""
    print("\nTest 5: No Exceptions")
    print("-" * 60)

    test_cases = [
        {},
        {"intent_primary": "IDLE"},
        {"entropy_bp": 5000},
        {"recent_intent_primary": "IDLE", "recent_regime": "stable_range"},
    ]

    for i, obs in enumerate(test_cases, 1):
        try:
            result = build_confidence_reason(obs)
            assert isinstance(result, str)
            print(f"✓ Test case {i} → no exception")
        except Exception as e:
            assert False, f"Test case {i} raised exception: {e}"

    print("Test 5: PASS")
    return True


def main():
    """Run all PR29 Confidence Reason Population smoke tests."""
    print("=" * 60)
    print("PR29: Confidence Reason Population Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Minimal population. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Empty Observation", test_empty_observation()))
        results.append(("Minimal Observation Structure", test_minimal_observation()))
        results.append(("Repeatability", test_repeatability()))
        results.append(("Full Observation", test_full_observation()))
        results.append(("No Exceptions", test_no_exceptions()))

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
            print("✓ ALL PR29 CONFIDENCE REASON POPULATION TESTS PASSED")
            print("=" * 60)
            print("PR29 Requirements Verified:")
            print("  - Empty observation handled gracefully")
            print("  - Minimal observation produces all 4 PR27 sections")
            print("  - Same observation produces same reason")
            print("  - Full observation produces structured reason")
            print("  - Builder never raises exceptions")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR29 TESTS FAILED")
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
