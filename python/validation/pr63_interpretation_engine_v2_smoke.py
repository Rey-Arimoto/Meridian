#!/usr/bin/env python3
"""
PR63: v0.6 Interpretation Engine v2 Smoke Test

Purpose:
    Validate that v0.6 interpretation engine v2 correctly performs
    compositional structural mapping from observations to meaning types.

Test Coverage:
    1. Interpretation engine v2 can be imported
    2. v2 output has factors and signals
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

from interpretation.v6_interpretation_engine_v2 import (
    interpret_v2,
    interpret_batch_v2,
    V2PrimaryMeaning,
    V2Factors,
    V2Signals,
    get_engine_v2_info,
)
from interpretation.v6_interpretation_schema import (
    V6InterpretationSchema,
)
from interpretation.v6_constitutional_guard import (
    check_forbidden_vocabulary,
)


def test_engine_v2_import() -> bool:
    """
    Test 1: Interpretation engine v2 can be imported.
    """
    print("Test 1: Interpretation engine v2 can be imported")
    print("-" * 60)

    # Check imports worked
    if interpret_v2 is None:
        print("✗ interpret_v2 not imported")
        return False
    print("✓ interpret_v2 imported")

    if V2PrimaryMeaning is None:
        print("✗ V2PrimaryMeaning not imported")
        return False
    print("✓ V2PrimaryMeaning imported")

    if V2Factors is None:
        print("✗ V2Factors not imported")
        return False
    print("✓ V2Factors imported")

    if V2Signals is None:
        print("✗ V2Signals not imported")
        return False
    print("✓ V2Signals imported")

    # Check engine info
    engine_info = get_engine_v2_info()

    if engine_info.get("engine_version") != "v2":
        print(f"✗ Expected engine_version=v2, got {engine_info.get('engine_version')}")
        return False
    print("✓ Engine version is v2")

    if engine_info.get("engine_type") != "compositional_structural_mapping":
        print(f"✗ Expected compositional_structural_mapping, got {engine_info.get('engine_type')}")
        return False
    print("✓ Engine type is compositional_structural_mapping")

    print("Test 1: PASS\n")
    return True


def test_v2_output_has_factors_and_signals() -> bool:
    """
    Test 2: v2 output has factors and signals.
    """
    print("Test 2: v2 output has factors and signals")
    print("-" * 60)

    # Test observation with rich structure
    obs = {
        "v5_decision_diff_status": "DIVERGED",
        "v5_decision_diff_semantics_tag": "DIVERGED_RULE_OVERLAY",
        "v5_shadow_decision_action": "PAUSE",
        "regime": "stable_range",
        "intent_primary": "IDLE",
    }

    try:
        interp = interpret_v2(obs)
    except Exception as e:
        print(f"✗ interpret_v2 raised exception: {e}")
        return False

    print("✓ interpret_v2 did not raise exception")

    # Check v6_meaning_factors exists
    if "v6_meaning_factors" not in interp:
        print("✗ Missing v6_meaning_factors field")
        return False
    print("✓ v6_meaning_factors field present")

    # Check v6_meaning_signals exists
    if "v6_meaning_signals" not in interp:
        print("✗ Missing v6_meaning_signals field")
        return False
    print("✓ v6_meaning_signals field present")

    # Check factors is list
    if not isinstance(interp["v6_meaning_factors"], list):
        print(f"✗ factors is not list: {type(interp['v6_meaning_factors'])}")
        return False
    print("✓ factors is list")

    # Check signals is list
    if not isinstance(interp["v6_meaning_signals"], list):
        print(f"✗ signals is not list: {type(interp['v6_meaning_signals'])}")
        return False
    print("✓ signals is list")

    # Check factors is non-empty for this observation
    if len(interp["v6_meaning_factors"]) == 0:
        print("✗ factors is empty for rich observation")
        return False
    print(f"✓ factors is non-empty: {interp['v6_meaning_factors']}")

    # Check signals is non-empty for this observation
    if len(interp["v6_meaning_signals"]) == 0:
        print("✗ signals is empty for rich observation")
        return False
    print(f"✓ signals is non-empty: {interp['v6_meaning_signals']}")

    # Check primary meaning still exists
    if "v6_meaning_tag" not in interp:
        print("✗ Missing v6_meaning_tag field")
        return False
    print(f"✓ primary meaning present: {interp['v6_meaning_tag']}")

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
    interp1 = interpret_v2(obs1)

    if interp1["v6_meaning_tag"] != V2PrimaryMeaning.OBSERVATION_INSUFFICIENT:
        print(f"✗ Expected OBSERVATION_INSUFFICIENT, got {interp1['v6_meaning_tag']}")
        return False
    print(f"✓ Empty obs → {V2PrimaryMeaning.OBSERVATION_INSUFFICIENT}")

    # Test case 2: Unclear observation → UNCLASSIFIED or similar
    obs2 = {
        "v5_decision_diff_status": "ALIGNED",
        "v5_decision_diff_semantics_tag": "UNKNOWN",
        # No shadow
    }
    interp2 = interpret_v2(obs2)

    tag2 = interp2["v6_meaning_tag"]
    if tag2 not in [V2PrimaryMeaning.UNCLASSIFIED, V2PrimaryMeaning.SHADOW_ABSENT_OR_UNAVAILABLE]:
        print(f"✗ Unclear obs should give UNCLASSIFIED or SHADOW_ABSENT, got {tag2}")
        return False
    print(f"✓ Unclear obs → {tag2} (expected fallback)")

    # Check that factors and signals exist even for UNCLASSIFIED
    if "v6_meaning_factors" not in interp2:
        print("✗ UNCLASSIFIED should still have factors")
        return False
    print("✓ UNCLASSIFIED has factors")

    if "v6_meaning_signals" not in interp2:
        print("✗ UNCLASSIFIED should still have signals")
        return False
    print("✓ UNCLASSIFIED has signals")

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
        {
            "v5_decision_diff_status": "DIVERGED",
            "v5_decision_diff_semantics_tag": "DIVERGED_RULE_OVERLAY",
            "regime": "stable_range",
        },
        {
            "v5_decision_diff_status": "ALIGNED",
            "v5_decision_diff_semantics_tag": "ALIGNED",
            "v5_shadow_decision_action": "HOLD",
        },
        {
            "v5_decision_diff_status": "UNAVAILABLE",
            "v5_decision_diff_semantics_tag": "NO_SHADOW",
        },
        {},
    ]

    for obs in test_obs:
        interp = interpret_v2(obs)

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

        # Check factors
        for factor in interp["v6_meaning_factors"]:
            factor_warnings = check_forbidden_vocabulary(factor)
            if factor_warnings:
                print(f"✗ Forbidden vocabulary in factor: {factor}")
                print(f"  Warnings: {factor_warnings}")
                return False

        # Check signals
        for signal in interp["v6_meaning_signals"]:
            signal_warnings = check_forbidden_vocabulary(signal)
            if signal_warnings:
                print(f"✗ Forbidden vocabulary in signal: {signal}")
                print(f"  Warnings: {signal_warnings}")
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

    interp = interpret_v2(obs)
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

    interp = interpret_v2(obs)
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

    # Check factors don't reference confidence
    for factor in interp["v6_meaning_factors"]:
        if "confidence" in factor.lower():
            print(f"✗ Factor references 'confidence': {factor}")
            return False
    print(f"✓ Factors do not reference confidence")

    # Check signals don't reference confidence
    for signal in interp["v6_meaning_signals"]:
        if "confidence" in signal.lower():
            print(f"✗ Signal references 'confidence': {signal}")
            return False
    print(f"✓ Signals do not reference confidence")

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
            interp = interpret_v2(obs)
            # Should succeed without raising
        except Exception as e:
            print(f"✗ interpret_v2 raised exception for edge case {obs}: {e}")
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
    print("PR63: v0.6 Interpretation Engine v2 Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Engine v2 import", test_engine_v2_import),
        ("v2 output has factors and signals", test_v2_output_has_factors_and_signals),
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
        print("✓ ALL PR63 INTERPRETATION ENGINE V2 TESTS PASSED")
    else:
        print("⚠ SOME PR63 INTERPRETATION ENGINE V2 TESTS FAILED")
    print("=" * 60)
    print("PR63 Requirements Verified:")
    print("  - Interpretation engine v2 can be imported")
    print("  - v2 output has factors and signals")
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
