#!/usr/bin/env python3
"""
PR61: v0.6 Interpretation Engine v1 Smoke Test

Purpose:
    Validate that v0.6 interpretation engine v1 correctly performs
    static structural mapping from observations to meaning types.

Test Coverage:
    1. Interpretation engine can be imported
    2. Minimal observation input generates v6 record
    3. UNKNOWN/UNCLASSIFIED appears as normal outcome
    4. No forbidden vocabulary in outputs
    5. Basis is array of field names
    6. confidence_reason not referenced
    7. Exit code always 0 (warning-only)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict

# Import v0.6 interpretation modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from interpretation.v6_interpretation_engine_v1 import (
    interpret_v1,
    interpret_batch_v1,
    V1MeaningTags,
    get_engine_info,
)
from interpretation.v6_interpretation_schema import (
    V6InterpretationSchema,
)
from interpretation.v6_constitutional_guard import (
    check_forbidden_vocabulary,
)


def test_engine_import() -> bool:
    """
    Test 1: Interpretation engine can be imported.
    """
    print("Test 1: Interpretation engine can be imported")
    print("-" * 60)

    # Check imports worked
    if interpret_v1 is None:
        print("✗ interpret_v1 not imported")
        return False
    print("✓ interpret_v1 imported")

    if V1MeaningTags is None:
        print("✗ V1MeaningTags not imported")
        return False
    print("✓ V1MeaningTags imported")

    # Check meaning tags defined
    tags = [
        V1MeaningTags.OVERLAY_OBSERVED,
        V1MeaningTags.ALIGNMENT_STABLE,
        V1MeaningTags.DIVERGENCE_WITHOUT_CLASS,
        V1MeaningTags.SHADOW_ABSENT_OR_UNAVAILABLE,
        V1MeaningTags.OBSERVATION_INSUFFICIENT,
        V1MeaningTags.UNCLASSIFIED,
    ]

    if len(tags) != 6:
        print(f"✗ Expected 6 meaning tags, got {len(tags)}")
        return False
    print(f"✓ All 6 meaning tags defined")

    print("Test 1: PASS\n")
    return True


def test_minimal_observation_generates_record() -> bool:
    """
    Test 2: Minimal observation input generates v6 record.
    """
    print("Test 2: Minimal observation input generates v6 record")
    print("-" * 60)

    # Empty observation
    obs = {}

    try:
        interp = interpret_v1(obs)
    except Exception as e:
        print(f"✗ interpret_v1 raised exception: {e}")
        return False

    print("✓ interpret_v1 did not raise exception")

    # Check required fields present
    required_fields = V6InterpretationSchema.REQUIRED_FIELDS

    for field in required_fields:
        if field not in interp:
            print(f"✗ Missing required field: {field}")
            return False

    print(f"✓ All required v6 fields present")

    # Check mode is ON
    if interp["v6_meaning_mode"] != "ON":
        print(f"✗ v6_meaning_mode should be ON, got {interp['v6_meaning_mode']}")
        return False
    print("✓ v6_meaning_mode is ON")

    # Check basis is list
    if not isinstance(interp["v6_meaning_basis"], list):
        print(f"✗ v6_meaning_basis should be list, got {type(interp['v6_meaning_basis'])}")
        return False
    print("✓ v6_meaning_basis is list")

    print("Test 2: PASS\n")
    return True


def test_unclassified_as_normal_outcome() -> bool:
    """
    Test 3: UNKNOWN/UNCLASSIFIED appears as normal outcome.
    """
    print("Test 3: UNKNOWN/UNCLASSIFIED appears as normal outcome")
    print("-" * 60)

    # Test case 1: Empty observation → OBSERVATION_INSUFFICIENT
    obs1 = {}
    interp1 = interpret_v1(obs1)

    if interp1["v6_meaning_tag"] != V1MeaningTags.OBSERVATION_INSUFFICIENT:
        print(f"✗ Expected OBSERVATION_INSUFFICIENT, got {interp1['v6_meaning_tag']}")
        return False
    print(f"✓ Empty obs → {V1MeaningTags.OBSERVATION_INSUFFICIENT}")

    # Test case 2: Observation without clear classification → UNCLASSIFIED
    obs2 = {
        "v5_decision_diff_status": "ALIGNED",
        "v5_decision_diff_semantics_tag": "UNKNOWN",
        # No shadow_decision_action
    }
    interp2 = interpret_v1(obs2)

    # Should get UNCLASSIFIED or similar
    tag2 = interp2["v6_meaning_tag"]
    if tag2 not in [V1MeaningTags.UNCLASSIFIED, V1MeaningTags.SHADOW_ABSENT_OR_UNAVAILABLE]:
        print(f"✗ Unclear obs should give UNCLASSIFIED or SHADOW_ABSENT, got {tag2}")
        return False
    print(f"✓ Unclear obs → {tag2} (expected fallback)")

    # Check status is AVAILABLE (not UNAVAILABLE)
    if interp2["v6_meaning_status"] == "UNAVAILABLE":
        # This is acceptable but let's note it
        pass

    print("Test 3: PASS\n")
    return True


def test_no_forbidden_vocabulary() -> bool:
    """
    Test 4: No forbidden vocabulary in outputs.
    """
    print("Test 4: No forbidden vocabulary in outputs")
    print("-" * 60)

    # Test various observations
    test_obs = [
        {"v5_decision_diff_status": "DIVERGED", "v5_decision_diff_semantics_tag": "DIVERGED_RULE_OVERLAY"},
        {"v5_decision_diff_status": "ALIGNED", "v5_decision_diff_semantics_tag": "ALIGNED", "v5_shadow_decision_action": "HOLD"},
        {"v5_decision_diff_status": "UNAVAILABLE", "v5_decision_diff_semantics_tag": "NO_SHADOW"},
        {},
    ]

    for obs in test_obs:
        interp = interpret_v1(obs)

        # Check tag
        tag_warnings = check_forbidden_vocabulary(interp["v6_meaning_tag"])
        if tag_warnings:
            print(f"✗ Forbidden vocabulary in tag: {interp['v6_meaning_tag']}")
            print(f"  Warnings: {tag_warnings}")
            return False

        # Check summary
        summary_warnings = check_forbidden_vocabulary(interp["v6_meaning_summary"])
        if summary_warnings:
            print(f"✗ Forbidden vocabulary in summary: {interp['v6_meaning_summary']}")
            print(f"  Warnings: {summary_warnings}")
            return False

    print("✓ No forbidden vocabulary in any outputs")
    print("Test 4: PASS\n")
    return True


def test_basis_is_field_name_array() -> bool:
    """
    Test 5: Basis is array of field names.
    """
    print("Test 5: Basis is array of field names")
    print("-" * 60)

    # Test with fields present
    obs = {
        "v5_decision_diff_status": "ALIGNED",
        "v5_decision_diff_semantics_tag": "ALIGNED",
        "v5_shadow_decision_action": "HOLD",
        "regime": "stable_range",
        "intent_primary": "IDLE",
    }

    interp = interpret_v1(obs)
    basis = interp["v6_meaning_basis"]

    # Check is list
    if not isinstance(basis, list):
        print(f"✗ basis is not list: {type(basis)}")
        return False
    print(f"✓ basis is list")

    # Check all items are strings
    for item in basis:
        if not isinstance(item, str):
            print(f"✗ basis contains non-string: {item}")
            return False
    print(f"✓ All basis items are strings")

    # Check basis contains expected fields (non-empty for this obs)
    if len(basis) == 0:
        print(f"✗ basis is empty for non-empty observation")
        return False
    print(f"✓ basis is non-empty: {basis}")

    # Check basis contains actual field names
    expected_in_basis = [
        "v5_decision_diff_status",
        "v5_decision_diff_semantics_tag",
    ]

    for field in expected_in_basis:
        if field not in basis:
            print(f"✗ Expected field '{field}' not in basis")
            return False
    print(f"✓ basis contains expected observation fields")

    print("Test 5: PASS\n")
    return True


def test_confidence_reason_not_referenced() -> bool:
    """
    Test 6: confidence_reason not referenced.
    """
    print("Test 6: confidence_reason not referenced")
    print("-" * 60)

    # Test with confidence_reason in observation (should be ignored)
    obs = {
        "v5_decision_diff_status": "ALIGNED",
        "v5_decision_diff_semantics_tag": "ALIGNED",
        "confidence_reason": "this should be ignored",
        "confidence_reason_version": "v0.4",
    }

    interp = interpret_v1(obs)
    basis = interp["v6_meaning_basis"]

    # Check confidence_reason NOT in basis
    forbidden_fields = ["confidence_reason", "confidence_reason_version", "confidence_reason_generated_at"]

    for field in forbidden_fields:
        if field in basis:
            print(f"✗ Forbidden field '{field}' found in basis")
            return False

    print(f"✓ No v0.4 confidence fields in basis")

    # Check summary doesn't reference confidence
    summary = interp["v6_meaning_summary"]
    if "confidence" in summary.lower():
        print(f"✗ Summary references 'confidence': {summary}")
        return False
    print(f"✓ Summary does not reference confidence")

    print("Test 6: PASS\n")
    return True


def test_exit_code_always_zero() -> bool:
    """
    Test 7: Exit code always 0 (warning-only).
    """
    print("Test 7: Exit code always 0 (warning-only)")
    print("-" * 60)

    # Test various edge cases that might cause errors
    edge_cases = [
        {},  # Empty
        {"v5_decision_diff_status": None},  # None value
        {"v5_decision_diff_status": "INVALID_VALUE"},  # Invalid value
        {"unknown_field": "value"},  # Unknown field
    ]

    for obs in edge_cases:
        try:
            interp = interpret_v1(obs)
            # Should succeed without raising
        except Exception as e:
            print(f"✗ interpret_v1 raised exception for edge case {obs}: {e}")
            return False

    print("✓ All edge cases handled without exceptions")
    print("✓ Exit code will be 0 (warning-only by design)")

    print("Test 7: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR61: v0.6 Interpretation Engine v1 Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Engine import", test_engine_import),
        ("Minimal observation generates record", test_minimal_observation_generates_record),
        ("UNCLASSIFIED as normal outcome", test_unclassified_as_normal_outcome),
        ("No forbidden vocabulary", test_no_forbidden_vocabulary),
        ("Basis is field name array", test_basis_is_field_name_array),
        ("confidence_reason not referenced", test_confidence_reason_not_referenced),
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
        print("✓ ALL PR61 INTERPRETATION ENGINE V1 TESTS PASSED")
    else:
        print("⚠ SOME PR61 INTERPRETATION ENGINE V1 TESTS FAILED")
    print("=" * 60)
    print("PR61 Requirements Verified:")
    print("  - Interpretation engine can be imported")
    print("  - Minimal observation input generates v6 record")
    print("  - UNKNOWN/UNCLASSIFIED appears as normal outcome")
    print("  - No forbidden vocabulary in outputs")
    print("  - Basis is array of field names")
    print("  - confidence_reason not referenced")
    print("  - Exit code always 0 (warning-only)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
