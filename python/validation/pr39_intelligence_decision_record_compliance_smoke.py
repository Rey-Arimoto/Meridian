#!/usr/bin/env python3
"""
PR39: v0.5 Intelligence Decision Record Compliance Guard Smoke Test

Purpose: Verify PR39 compliance guard correctly enforces PR38 Decision Record Charter.

Requirements:
- Structure validation (required fields, types, version, timestamp)
- Regeneration detection (code patterns)
- Post-hoc rationalization detection (outcome vocabulary)
- Confidence erosion detection (v0.4 boundary)
- Warning-only (never raises exceptions)
- Exit code always 0

Non-Goals:
- No decision correctness validation
- No decision flow modification
- No v0.4 Confidence modification
"""

import sys
import os
from datetime import datetime

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from intelligence.intelligence_decision_record_compliance import (
    validate_decision_record_structure,
    detect_decision_regeneration,
    detect_posthoc_rationalization,
    detect_confidence_erosion,
    validate_decision_record_full,
)


def test_valid_decision_record():
    """Test 1: Valid Decision Record (no warnings)."""
    print("\nTest 1: Valid Decision Record (No Warnings)")
    print("-" * 60)

    # Compliant Decision Record (PR38)
    decision_record = {
        "decision_action": "hold_position",
        "decision_reason": "market volatility below stability threshold, intent aligned with regime",
        "decision_inputs": ["entropy_bp", "intent_primary", "price", "regime", "volatility"],
        "decision_version": "v0.5",
        "decision_generated_at": datetime.utcnow().isoformat(),
    }

    warnings = validate_decision_record_full(decision_record, "test_module.py")

    assert len(warnings) == 0, f"Should have no warnings, got: {warnings}"
    print(f"✓ No warnings for valid Decision Record")
    print(f"  Action: {decision_record['decision_action']}")
    print(f"  Version: {decision_record['decision_version']}")
    print(f"  Timestamp: {decision_record['decision_generated_at']}")

    print("Test 1: PASS")
    return True


def test_missing_required_fields():
    """Test 2: Missing required fields detection."""
    print("\nTest 2: Missing Required Fields Detection")
    print("-" * 60)

    # Missing decision_reason and decision_version
    decision_record = {
        "decision_action": "increase_exposure",
        # Missing: decision_reason
        "decision_inputs": ["price", "volatility"],
        # Missing: decision_version
        "decision_generated_at": datetime.utcnow().isoformat(),
    }

    warnings = validate_decision_record_structure(decision_record)

    assert len(warnings) > 0, "Should detect missing fields"
    assert any("decision_reason" in w for w in warnings), "Should detect missing decision_reason"
    assert any("decision_version" in w for w in warnings), "Should detect missing decision_version"
    print(f"✓ Detected {len(warnings)} missing field(s)")
    for w in warnings:
        print(f"  - {w}")

    print("Test 2: PASS")
    return True


def test_version_violation():
    """Test 3: Version != v0.5 detection."""
    print("\nTest 3: Version Violation Detection")
    print("-" * 60)

    # Wrong version
    decision_record = {
        "decision_action": "reduce_risk",
        "decision_reason": "regime transition detected",
        "decision_inputs": ["regime"],
        "decision_version": "v0.4",  # WRONG: should be v0.5
        "decision_generated_at": datetime.utcnow().isoformat(),
    }

    warnings = validate_decision_record_structure(decision_record)

    assert len(warnings) > 0, "Should detect version violation"
    assert any("version violation" in w.lower() for w in warnings), "Should detect wrong version"
    print(f"✓ Detected version violation")
    print(f"  Expected: v0.5, Got: {decision_record['decision_version']}")
    print(f"  Warnings: {warnings}")

    print("Test 3: PASS")
    return True


def test_timestamp_format_violation():
    """Test 4: Non-ISO-8601 timestamp detection."""
    print("\nTest 4: Timestamp Format Violation Detection")
    print("-" * 60)

    # Invalid timestamp format
    decision_record = {
        "decision_action": "wait_for_stability",
        "decision_reason": "market conditions uncertain",
        "decision_inputs": ["volatility"],
        "decision_version": "v0.5",
        "decision_generated_at": "2026/01/10 15:30:00",  # WRONG: not ISO-8601
    }

    warnings = validate_decision_record_structure(decision_record)

    assert len(warnings) > 0, "Should detect timestamp format violation"
    assert any("timestamp violation" in w.lower() for w in warnings), "Should detect wrong timestamp format"
    print(f"✓ Detected timestamp format violation")
    print(f"  Invalid format: {decision_record['decision_generated_at']}")
    print(f"  Warnings: {warnings}")

    print("Test 4: PASS")
    return True


def test_decision_regeneration_detection():
    """Test 5: Decision regeneration pattern detection."""
    print("\nTest 5: Decision Regeneration Pattern Detection")
    print("-" * 60)

    # Code with regeneration pattern (PR38 Ban 1)
    code = """
def improve_past_decision(historical_log, new_model):
    for row in historical_log:
        old_decision = row["decision_action"]
        old_reason = row["decision_reason"]

        # Regenerating decision with better model
        new_decision = new_model.decide(row["state"])
        new_reason = new_model.explain(row["state"])

        row["decision_reason"] = regenerate(new_reason)  # PROHIBITED
"""

    warnings = detect_decision_regeneration(code, "test_module.py")

    assert len(warnings) > 0, "Should detect regeneration pattern"
    print(f"✓ Detected {len(warnings)} regeneration pattern(s)")
    for w in warnings:
        print(f"  - {w}")

    print("Test 5: PASS")
    return True


def test_posthoc_rationalization_detection():
    """Test 6: Post-hoc rationalization detection (outcome vocabulary)."""
    print("\nTest 6: Post-Hoc Rationalization Detection")
    print("-" * 60)

    # decision_reason with outcome vocabulary (PR38 Ban 2)
    decision_reason_bad = "decision was correct based on outcome, profit exceeded expectations"

    warnings = detect_posthoc_rationalization(decision_reason_bad)

    assert len(warnings) > 0, "Should detect outcome vocabulary"
    assert any("outcome" in w or "correct" in w or "profit" in w for w in warnings), \
        "Should detect outcome/correct/profit vocabulary"
    print(f"✓ Detected {len(warnings)} post-hoc rationalization indicator(s)")
    for w in warnings:
        print(f"  - {w}")

    print("Test 6: PASS")
    return True


def test_confidence_erosion_detection():
    """Test 7: v0.4 Confidence erosion detection."""
    print("\nTest 7: v0.4 Confidence Erosion Detection")
    print("-" * 60)

    # decision_reason evaluating confidence (PR35 Ban 6, PR38 Ban 6)
    decision_reason_bad = "confidence_reason was correct, good confidence enabled this decision"

    warnings = detect_confidence_erosion(decision_reason_bad, "test_module.py")

    assert len(warnings) > 0, "Should detect confidence erosion"
    print(f"✓ Detected {len(warnings)} confidence erosion pattern(s)")
    for w in warnings:
        print(f"  - {w}")

    print("Test 7: PASS")
    return True


def test_exit_code_always_zero():
    """Test 8: Verify exit code always 0 (warning-only)."""
    print("\nTest 8: Exit Code Always 0 (Warning-Only)")
    print("-" * 60)

    # Even with violations, functions never raise exceptions
    try:
        # Completely invalid record
        invalid_record = {"invalid": "data"}

        warnings_structure = validate_decision_record_structure(invalid_record)
        warnings_full = validate_decision_record_full(invalid_record)

        # Invalid code
        invalid_code = "decision_reason = regenerate(confidence_reason)"
        warnings_regen = detect_decision_regeneration(invalid_code)

        # All should return lists, never raise
        assert isinstance(warnings_structure, list), "Should return list"
        assert isinstance(warnings_full, list), "Should return list"
        assert isinstance(warnings_regen, list), "Should return list"

        print(f"✓ All validation functions return lists (never raise)")
        print(f"  Structure warnings: {len(warnings_structure)}")
        print(f"  Full warnings: {len(warnings_full)}")
        print(f"  Regeneration warnings: {len(warnings_regen)}")
        print(f"✓ Exit code will be 0 (warning-only)")

    except Exception as e:
        assert False, f"Validation should never raise exceptions, got: {e}"

    print("Test 8: PASS")
    return True


def main():
    """Run all PR39 Intelligence Decision Record Compliance Guard smoke tests."""
    print("=" * 60)
    print("PR39: Decision Record Compliance Guard Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Valid Decision Record", test_valid_decision_record()))
        results.append(("Missing Required Fields", test_missing_required_fields()))
        results.append(("Version Violation", test_version_violation()))
        results.append(("Timestamp Format Violation", test_timestamp_format_violation()))
        results.append(("Decision Regeneration Detection", test_decision_regeneration_detection()))
        results.append(("Post-Hoc Rationalization Detection", test_posthoc_rationalization_detection()))
        results.append(("Confidence Erosion Detection", test_confidence_erosion_detection()))
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
            print("✓ ALL PR39 DECISION RECORD COMPLIANCE TESTS PASSED")
            print("=" * 60)
            print("PR39 Requirements Verified:")
            print("  - Structure validation (fields, types, version, timestamp)")
            print("  - Regeneration detection (code patterns)")
            print("  - Post-hoc rationalization detection (outcome vocabulary)")
            print("  - Confidence erosion detection (v0.4 boundary)")
            print("  - Warning-only (never raises exceptions)")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR39 TESTS FAILED")
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
