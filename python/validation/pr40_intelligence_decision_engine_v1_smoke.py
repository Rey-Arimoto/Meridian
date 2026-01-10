#!/usr/bin/env python3
"""
PR40: v0.5 Intelligence Decision Engine v1 Smoke Test

Purpose: Verify PR40 decision engine correctly mirrors base_action and generates PR38-compliant records.

Requirements:
- base_action mirroring (exact copy)
- PR38 required fields present
- decision_version == "v0.5"
- decision_generated_at is UTC ISO-8601
- decision_inputs contains "base_action"
- Missing base_action handled (UNKNOWN, no exception)
- decision_reason contains no digits
- decision_reason contains no outcome vocabulary
- Exit code always 0 (warning-only)

Non-Goals:
- No behavior modification testing (READ-ONLY)
- No v0.4 confidence modification testing (immutable by design)
"""

import sys
import os
import re

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from intelligence.intelligence_decision_engine_v1 import generate_decision_record_v1


# ISO-8601 UTC timestamp pattern
ISO_8601_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?$'
)

# PR38 required fields
REQUIRED_FIELDS = [
    "decision_action",
    "decision_reason",
    "decision_inputs",
    "decision_version",
    "decision_generated_at",
]

# PR39: Prohibited outcome vocabulary
OUTCOME_VOCABULARY = [
    "outcome", "result", "profit", "loss", "pnl",
    "success", "failure", "win", "lose",
    "correct", "incorrect", "right", "wrong",
]


def test_base_action_mirroring():
    """Test 1: base_action is mirrored exactly to decision_action."""
    print("\nTest 1: Base Action Mirroring (Exact Copy)")
    print("-" * 60)

    # Test various base_action values
    test_cases = ["HOLD", "SHIFT", "PAUSE", "INCREASE", "REDUCE"]

    for base_action in test_cases:
        row_dict = {
            "base_action": base_action,
            "intent_primary": "SEEK",
            "regime": "stable_range",
        }

        decision_record = generate_decision_record_v1(row_dict)

        assert "decision_action" in decision_record, "decision_action must be present"
        assert decision_record["decision_action"] == base_action, \
            f"decision_action must mirror base_action exactly: expected '{base_action}', got '{decision_record['decision_action']}'"

        print(f"✓ base_action '{base_action}' → decision_action '{decision_record['decision_action']}' (exact mirror)")

    print("Test 1: PASS")
    return True


def test_pr38_required_fields():
    """Test 2: Decision record has all PR38 required fields."""
    print("\nTest 2: PR38 Required Fields Present")
    print("-" * 60)

    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",
    }

    decision_record = generate_decision_record_v1(row_dict)

    for field in REQUIRED_FIELDS:
        assert field in decision_record, f"PR38 required field '{field}' must be present"
        print(f"✓ Field '{field}' present: {decision_record[field]}")

    print("Test 2: PASS")
    return True


def test_decision_version_fixed():
    """Test 3: decision_version is fixed to 'v0.5'."""
    print("\nTest 3: Decision Version Fixed to 'v0.5'")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
    }

    decision_record = generate_decision_record_v1(row_dict)

    assert "decision_version" in decision_record, "decision_version must be present"
    assert decision_record["decision_version"] == "v0.5", \
        f"decision_version must be 'v0.5', got '{decision_record['decision_version']}'"

    print(f"✓ decision_version == 'v0.5' (fixed)")

    print("Test 3: PASS")
    return True


def test_timestamp_iso8601_utc():
    """Test 4: decision_generated_at is UTC ISO-8601 format."""
    print("\nTest 4: Timestamp UTC ISO-8601 Format")
    print("-" * 60)

    row_dict = {
        "base_action": "PAUSE",
        "intent_primary": "HARVEST",
    }

    decision_record = generate_decision_record_v1(row_dict)

    assert "decision_generated_at" in decision_record, "decision_generated_at must be present"

    timestamp = decision_record["decision_generated_at"]
    assert ISO_8601_PATTERN.match(timestamp), \
        f"decision_generated_at must be ISO-8601 UTC format, got '{timestamp}'"

    print(f"✓ decision_generated_at in ISO-8601 UTC format")
    print(f"  Timestamp: {timestamp}")

    print("Test 4: PASS")
    return True


def test_decision_inputs_contains_base_action():
    """Test 5: decision_inputs contains 'base_action'."""
    print("\nTest 5: Decision Inputs Contains 'base_action'")
    print("-" * 60)

    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",
        "confidence_reason": "Source:entropy_bp; Stability:temporal indicators present; ...",
        "confidence_reason_version": "v0.4",
    }

    decision_record = generate_decision_record_v1(row_dict)

    assert "decision_inputs" in decision_record, "decision_inputs must be present"
    assert isinstance(decision_record["decision_inputs"], list), \
        "decision_inputs must be a list"

    decision_inputs = decision_record["decision_inputs"]
    assert "base_action" in decision_inputs, \
        "decision_inputs must contain 'base_action'"

    print(f"✓ decision_inputs contains 'base_action'")
    print(f"  All inputs: {decision_inputs}")

    print("Test 5: PASS")
    return True


def test_missing_base_action_handled():
    """Test 6: Missing base_action handled gracefully (UNKNOWN, no exception)."""
    print("\nTest 6: Missing Base Action Handled (UNKNOWN, No Exception)")
    print("-" * 60)

    # Row without base_action
    row_dict = {
        "intent_primary": "IDLE",
        "regime": "stable_range",
    }

    try:
        decision_record = generate_decision_record_v1(row_dict)

        assert "decision_action" in decision_record, "decision_action must be present"
        assert decision_record["decision_action"] == "UNKNOWN", \
            f"decision_action must be 'UNKNOWN' when base_action missing, got '{decision_record['decision_action']}'"

        # Check for warning
        if "_warnings" in decision_record:
            print(f"✓ Warning generated: {decision_record['_warnings']}")

        print(f"✓ Missing base_action handled gracefully (decision_action == 'UNKNOWN')")
        print(f"✓ No exception raised")

    except Exception as e:
        assert False, f"Should not raise exception for missing base_action, got: {e}"

    print("Test 6: PASS")
    return True


def test_decision_reason_no_digits():
    """Test 7: decision_reason contains no digits (non-numeric requirement)."""
    print("\nTest 7: Decision Reason Contains No Digits")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "confidence_reason": "Source:entropy_bp; Stability:temporal indicators present; ...",
    }

    decision_record = generate_decision_record_v1(row_dict)

    assert "decision_reason" in decision_record, "decision_reason must be present"

    decision_reason = decision_record["decision_reason"]
    has_digits = bool(re.search(r'\d', decision_reason))

    assert not has_digits, \
        f"decision_reason must not contain digits (non-numeric requirement), got: {decision_reason}"

    print(f"✓ decision_reason contains no digits (non-numeric)")
    print(f"  Reason: {decision_reason}")

    print("Test 7: PASS")
    return True


def test_decision_reason_no_outcome_vocabulary():
    """Test 8: decision_reason contains no outcome vocabulary (no post-hoc rationalization)."""
    print("\nTest 8: Decision Reason Contains No Outcome Vocabulary")
    print("-" * 60)

    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",
    }

    decision_record = generate_decision_record_v1(row_dict)

    assert "decision_reason" in decision_record, "decision_reason must be present"

    decision_reason = decision_record["decision_reason"].lower()
    found_outcome_vocab = []

    for vocab in OUTCOME_VOCABULARY:
        if vocab in decision_reason:
            found_outcome_vocab.append(vocab)

    assert len(found_outcome_vocab) == 0, \
        f"decision_reason must not contain outcome vocabulary (no post-hoc rationalization), found: {found_outcome_vocab}"

    print(f"✓ decision_reason contains no outcome vocabulary")
    print(f"  Reason: {decision_record['decision_reason']}")

    print("Test 8: PASS")
    return True


def test_exit_code_always_zero():
    """Test 9: Verify exit code always 0 (warning-only, never raises)."""
    print("\nTest 9: Exit Code Always 0 (Warning-Only)")
    print("-" * 60)

    # Test with various invalid inputs
    test_cases = [
        {},  # Empty row
        {"invalid_key": "value"},  # Invalid key (not in allowlist)
        {"base_action": None},  # None base_action
        {"base_action": 123},  # Wrong type
        {"base_action": ""},  # Empty string
    ]

    for i, row_dict in enumerate(test_cases):
        try:
            decision_record = generate_decision_record_v1(row_dict)

            # Should always return a dict, never raise
            assert isinstance(decision_record, dict), \
                f"Should return dict, got {type(decision_record)}"

            print(f"✓ Test case {i+1}: No exception raised")

        except Exception as e:
            assert False, f"Should never raise exception (warning-only), got: {e}"

    print(f"✓ All test cases handled without exceptions")
    print(f"✓ Exit code will be 0 (warning-only)")

    print("Test 9: PASS")
    return True


def main():
    """Run all PR40 Intelligence Decision Engine v1 smoke tests."""
    print("=" * 60)
    print("PR40: Intelligence Decision Engine v1 Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Base Action Mirroring", test_base_action_mirroring()))
        results.append(("PR38 Required Fields", test_pr38_required_fields()))
        results.append(("Decision Version Fixed", test_decision_version_fixed()))
        results.append(("Timestamp ISO-8601 UTC", test_timestamp_iso8601_utc()))
        results.append(("Decision Inputs Contains base_action", test_decision_inputs_contains_base_action()))
        results.append(("Missing Base Action Handled", test_missing_base_action_handled()))
        results.append(("Decision Reason No Digits", test_decision_reason_no_digits()))
        results.append(("Decision Reason No Outcome Vocab", test_decision_reason_no_outcome_vocabulary()))
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
            print("✓ ALL PR40 DECISION ENGINE V1 TESTS PASSED")
            print("=" * 60)
            print("PR40 Requirements Verified:")
            print("  - base_action mirrored exactly to decision_action")
            print("  - PR38 required fields present and valid")
            print("  - decision_version fixed to 'v0.5'")
            print("  - decision_generated_at in UTC ISO-8601 format")
            print("  - decision_inputs contains 'base_action'")
            print("  - Missing base_action handled (UNKNOWN, no exception)")
            print("  - decision_reason is non-numeric (no digits)")
            print("  - decision_reason has no outcome vocabulary")
            print("  - Warning-only (never raises exceptions)")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR40 TESTS FAILED")
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
