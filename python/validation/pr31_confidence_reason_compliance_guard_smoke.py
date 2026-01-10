#!/usr/bin/env python3
"""
PR31: Confidence Reason Compliance Guard Smoke Test

Purpose: Verify compliance validator detects violations of PR21/PR27/PR30.

Requirements:
- validate_confidence_reason detects structure violations (PR27)
- validate_confidence_reason detects vocabulary violations (PR30)
- validate_confidence_reason detects digit presence (hard ban)
- Empty string passes validation (PR21)
- PR29B-generated reasons pass validation
- Exit code always 0 (warning-only)

Non-Goals:
- No quality assessment
- No natural language validation
- No reason improvement
"""

import sys
import os

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from confidence.confidence_reason_compliance import validate_confidence_reason
from confidence.confidence_reason_builder import build_confidence_reason


def test_empty_string_valid():
    """Test empty string passes validation (PR21)."""
    print("\nTest 1: Empty String Valid (PR21)")
    print("-" * 60)

    warnings = validate_confidence_reason("")
    assert isinstance(warnings, list), "Must return list"
    assert len(warnings) == 0, f"Empty string should have no warnings, got: {warnings}"

    print("✓ Empty string → 0 warnings (PR21 compliant)")
    print("Test 1: PASS")
    return True


def test_pr29b_generated_reason_valid():
    """Test PR29B-generated reasons pass validation."""
    print("\nTest 2: PR29B Generated Reason Valid")
    print("-" * 60)

    # Generate reason using PR29B builder
    obs1 = {
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "base_action": "SHIFT",
        "overlay_rule": "ALLOW",
        "entropy_bp": 3200,
        "recent_intent_primary": "IDLE",
        "recent_regime": "stable_range",
    }
    reason1 = build_confidence_reason(obs1)
    warnings1 = validate_confidence_reason(reason1)

    assert len(warnings1) == 0, f"PR29B reason should have no warnings, got: {warnings1}"
    print(f"✓ Full observation → 0 warnings")
    print(f"  Reason: {reason1}")

    # Generate minimal reason
    obs2 = {"intent_primary": "IDLE"}
    reason2 = build_confidence_reason(obs2)
    warnings2 = validate_confidence_reason(reason2)

    assert len(warnings2) == 0, f"PR29B minimal reason should have no warnings, got: {warnings2}"
    print(f"✓ Minimal observation → 0 warnings")
    print(f"  Reason: {reason2}")

    print("Test 2: PASS")
    return True


def test_structure_violation_detected():
    """Test structure violations are detected (PR27)."""
    print("\nTest 3: Structure Violation Detection (PR27)")
    print("-" * 60)

    # Missing sections
    bad_reason1 = "Source:test"
    warnings1 = validate_confidence_reason(bad_reason1)
    assert len(warnings1) > 0, "Missing sections should produce warnings"
    print(f"✓ Missing sections → {len(warnings1)} warning(s)")

    # Wrong order / missing separator
    bad_reason2 = "Source:test Stability:temporal indicators present"
    warnings2 = validate_confidence_reason(bad_reason2)
    assert len(warnings2) > 0, "Wrong separator should produce warnings"
    print(f"✓ Wrong separator → {len(warnings2)} warning(s)")

    # Not starting with Source:
    bad_reason3 = "Stability:temporal indicators present; Source:test; Consistency:all core signals present; Completeness:current observations only"
    warnings3 = validate_confidence_reason(bad_reason3)
    assert len(warnings3) > 0, "Wrong order should produce warnings"
    print(f"✓ Wrong order → {len(warnings3)} warning(s)")

    print("Test 3: PASS")
    return True


def test_digit_violation_detected():
    """Test digit presence is detected (hard ban)."""
    print("\nTest 4: Digit Violation Detection (Hard Ban)")
    print("-" * 60)

    # Reason with digit
    bad_reason1 = "Source:test; Stability:temporal indicators absent; Consistency:3/4 core signals; Completeness:current observations only"
    warnings1 = validate_confidence_reason(bad_reason1)
    assert len(warnings1) > 0, "Digit presence should produce warnings"
    assert any("digit" in w.lower() for w in warnings1), "Should have digit-related warning"
    print(f"✓ Digit in Consistency → {len(warnings1)} warning(s)")

    # Reason with count
    bad_reason2 = "Source:test; Stability:temporal indicators absent; Consistency:all core signals present; Completeness:7 fields"
    warnings2 = validate_confidence_reason(bad_reason2)
    assert len(warnings2) > 0, "Digit presence should produce warnings"
    assert any("digit" in w.lower() for w in warnings2), "Should have digit-related warning"
    print(f"✓ Digit in Completeness → {len(warnings2)} warning(s)")

    print("Test 4: PASS")
    return True


def test_vocabulary_violation_detected():
    """Test vocabulary violations are detected (PR30)."""
    print("\nTest 5: Vocabulary Violation Detection (PR30)")
    print("-" * 60)

    # Invalid Stability vocabulary
    bad_reason1 = "Source:test; Stability:high temporal stability; Consistency:all core signals present; Completeness:current observations only"
    warnings1 = validate_confidence_reason(bad_reason1)
    assert len(warnings1) > 0, "Invalid Stability vocabulary should produce warnings"
    assert any("vocabulary" in w.lower() and "stability" in w.lower() for w in warnings1), "Should have Stability vocabulary warning"
    print(f"✓ Invalid Stability vocabulary → {len(warnings1)} warning(s)")

    # Invalid Consistency vocabulary
    bad_reason2 = "Source:test; Stability:temporal indicators absent; Consistency:good signal coverage; Completeness:current observations only"
    warnings2 = validate_confidence_reason(bad_reason2)
    assert len(warnings2) > 0, "Invalid Consistency vocabulary should produce warnings"
    assert any("vocabulary" in w.lower() and "consistency" in w.lower() for w in warnings2), "Should have Consistency vocabulary warning"
    print(f"✓ Invalid Consistency vocabulary → {len(warnings2)} warning(s)")

    # Invalid Completeness vocabulary
    bad_reason3 = "Source:test; Stability:temporal indicators absent; Consistency:all core signals present; Completeness:rich observations"
    warnings3 = validate_confidence_reason(bad_reason3)
    assert len(warnings3) > 0, "Invalid Completeness vocabulary should produce warnings"
    assert any("vocabulary" in w.lower() and "completeness" in w.lower() for w in warnings3), "Should have Completeness vocabulary warning"
    print(f"✓ Invalid Completeness vocabulary → {len(warnings3)} warning(s)")

    print("Test 5: PASS")
    return True


def test_exit_code_always_zero():
    """Test validator never raises exceptions."""
    print("\nTest 6: Exit Code Always Zero")
    print("-" * 60)

    test_cases = [
        "",
        "invalid",
        "Source:test",
        None,  # Will be handled gracefully
        "Source:test; Stability:temporal indicators present; Consistency:all core signals present; Completeness:current observations only",
    ]

    for i, reason in enumerate(test_cases, 1):
        try:
            if reason is None:
                # Skip None test (validator expects str)
                continue
            warnings = validate_confidence_reason(reason)
            assert isinstance(warnings, list), "Must return list"
            print(f"✓ Test case {i} → no exception")
        except Exception as e:
            assert False, f"Test case {i} raised exception: {e}"

    print("Test 6: PASS")
    return True


def main():
    """Run all PR31 Confidence Reason Compliance Guard smoke tests."""
    print("=" * 60)
    print("PR31: Confidence Reason Compliance Guard Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Validation only. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Empty String Valid", test_empty_string_valid()))
        results.append(("PR29B Generated Reason Valid", test_pr29b_generated_reason_valid()))
        results.append(("Structure Violation Detection", test_structure_violation_detected()))
        results.append(("Digit Violation Detection", test_digit_violation_detected()))
        results.append(("Vocabulary Violation Detection", test_vocabulary_violation_detected()))
        results.append(("Exit Code Always Zero", test_exit_code_always_zero()))

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
            print("✓ ALL PR31 COMPLIANCE GUARD TESTS PASSED")
            print("=" * 60)
            print("PR31 Requirements Verified:")
            print("  - Empty string passes validation (PR21)")
            print("  - PR29B-generated reasons pass validation")
            print("  - Structure violations detected (PR27)")
            print("  - Digit presence detected (hard ban)")
            print("  - Vocabulary violations detected (PR30)")
            print("  - Validator never raises exceptions")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR31 TESTS FAILED")
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
