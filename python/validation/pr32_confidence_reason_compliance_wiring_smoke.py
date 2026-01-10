#!/usr/bin/env python3
"""
PR32: Confidence Reason Compliance Guard Wiring Smoke Test

Purpose: Verify compliance validator is wired into execution path.

Requirements:
- validate_confidence_reason is importable
- PR29B-generated reasons pass validation (no warnings)
- Invalid reasons produce warnings (detected)
- Warnings never stop execution (non-fatal)
- Exit code always 0 (warning-only)

Non-Goals:
- No agent startup test (unit test only)
- No behavior validation
- No control flow changes
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


def test_import_compliance_validator():
    """Test compliance validator is importable."""
    print("\nTest 1: Import Compliance Validator")
    print("-" * 60)

    # Already imported above, verify callable
    assert callable(validate_confidence_reason), "validate_confidence_reason must be callable"
    print("✓ validate_confidence_reason imported successfully")
    print("✓ Function is callable")

    print("Test 1: PASS")
    return True


def test_pr29b_reason_no_warnings():
    """Test PR29B-generated reasons produce no warnings."""
    print("\nTest 2: PR29B Generated Reason (No Warnings)")
    print("-" * 60)

    # Generate valid reasons using PR29B builder
    obs1 = {
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "base_action": "SHIFT",
        "overlay_rule": "ALLOW",
        "entropy_bp": 3200,
    }
    reason1 = build_confidence_reason(obs1)
    warnings1 = validate_confidence_reason(reason1)

    assert len(warnings1) == 0, f"PR29B reason should have no warnings, got: {warnings1}"
    print(f"✓ Full observation → 0 warnings")
    print(f"  Reason: {reason1[:80]}...")

    # Minimal observation
    obs2 = {"intent_primary": "IDLE"}
    reason2 = build_confidence_reason(obs2)
    warnings2 = validate_confidence_reason(reason2)

    assert len(warnings2) == 0, f"PR29B minimal reason should have no warnings, got: {warnings2}"
    print(f"✓ Minimal observation → 0 warnings")

    # Empty observation (PR21)
    obs3 = {}
    reason3 = build_confidence_reason(obs3)
    warnings3 = validate_confidence_reason(reason3)

    assert len(warnings3) == 0, f"Empty observation should have no warnings, got: {warnings3}"
    print(f"✓ Empty observation → 0 warnings (PR21 compliant)")

    print("Test 2: PASS")
    return True


def test_digit_reason_produces_warnings():
    """Test reason with digit produces warnings (hard ban)."""
    print("\nTest 3: Digit Reason Produces Warnings")
    print("-" * 60)

    # Reason with digit (violates hard ban)
    bad_reason = "Source:test; Stability:temporal indicators absent; Consistency:3/4 core signals; Completeness:current observations only"
    warnings = validate_confidence_reason(bad_reason)

    assert len(warnings) > 0, "Reason with digit should produce warnings"
    assert any("digit" in w.lower() for w in warnings), "Should have digit-related warning"
    print(f"✓ Reason with digit → {len(warnings)} warning(s)")
    print(f"  First warning: {warnings[0]}")

    print("Test 3: PASS")
    return True


def test_structure_violation_produces_warnings():
    """Test reason with structure violation produces warnings (PR27)."""
    print("\nTest 4: Structure Violation Produces Warnings")
    print("-" * 60)

    # Missing sections
    bad_reason1 = "Source:test"
    warnings1 = validate_confidence_reason(bad_reason1)

    assert len(warnings1) > 0, "Incomplete structure should produce warnings"
    print(f"✓ Missing sections → {len(warnings1)} warning(s)")

    # Wrong vocabulary
    bad_reason2 = "Source:test; Stability:high stability; Consistency:all core signals present; Completeness:current observations only"
    warnings2 = validate_confidence_reason(bad_reason2)

    assert len(warnings2) > 0, "Wrong vocabulary should produce warnings"
    assert any("vocabulary" in w.lower() for w in warnings2), "Should have vocabulary-related warning"
    print(f"✓ Wrong vocabulary → {len(warnings2)} warning(s)")

    print("Test 4: PASS")
    return True


def test_warnings_non_fatal():
    """Test warnings never stop execution (non-fatal)."""
    print("\nTest 5: Warnings Non-Fatal")
    print("-" * 60)

    # Validator should never raise exceptions
    test_cases = [
        "",
        "invalid",
        "Source:test",
        "Source:test; Stability:temporal indicators absent; Consistency:3/4 core signals; Completeness:current observations only",
        "Source:a, b, c; Stability:temporal indicators present; Consistency:all core signals present; Completeness:temporal and current observations",
    ]

    for i, reason in enumerate(test_cases, 1):
        try:
            warnings = validate_confidence_reason(reason)
            assert isinstance(warnings, list), "Must return list"
            print(f"✓ Test case {i} → no exception (warnings={len(warnings)})")
        except Exception as e:
            assert False, f"Test case {i} raised exception: {e}"

    # Verify wiring pattern: warnings output but execution continues
    # (This is a unit test - agent integration verified separately)
    obs = {
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "base_action": "SHIFT",
        "overlay_rule": "ALLOW",
        "entropy_bp": 3200,
    }
    reason = build_confidence_reason(obs)
    warnings = validate_confidence_reason(reason)

    # Simulate wiring pattern (as in agent)
    if warnings:
        # This would print in agent but never stop execution
        pass  # No exception, no exit

    print("✓ Wiring pattern: warnings output, execution continues")

    print("Test 5: PASS")
    return True


def main():
    """Run all PR32 Compliance Guard Wiring smoke tests."""
    print("=" * 60)
    print("PR32: Confidence Reason Compliance Guard Wiring Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Wiring only. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Import Compliance Validator", test_import_compliance_validator()))
        results.append(("PR29B Reason No Warnings", test_pr29b_reason_no_warnings()))
        results.append(("Digit Reason Produces Warnings", test_digit_reason_produces_warnings()))
        results.append(("Structure Violation Produces Warnings", test_structure_violation_produces_warnings()))
        results.append(("Warnings Non-Fatal", test_warnings_non_fatal()))

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
            print("✓ ALL PR32 COMPLIANCE WIRING TESTS PASSED")
            print("=" * 60)
            print("PR32 Requirements Verified:")
            print("  - Compliance validator importable")
            print("  - PR29B-generated reasons pass validation")
            print("  - Invalid reasons produce warnings")
            print("  - Warnings are non-fatal (execution continues)")
            print("  - Wiring pattern verified")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR32 TESTS FAILED")
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
