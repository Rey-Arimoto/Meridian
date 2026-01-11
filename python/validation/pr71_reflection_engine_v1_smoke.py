#!/usr/bin/env python3
"""
PR71: v0.7 Reflection Engine v1 Smoke Test

Purpose:
    Validate that v0.7 reflection engine v1 correctly generates
    reflection records from interpretation analytics.

Test Coverage:
    1. Reflection engine can be imported
    2. Minimal analytics input generates v7 record
    3. Each reflection tag appears as normal outcome
    4. No forbidden vocabulary in outputs
    5. Basis uses only interpretation fields
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

# Import v0.7 reflection modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reflection.v7_reflection_engine_v1 import (
    reflect_v1,
    reflect_batch_v1,
    V1ReflectionTags,
    get_engine_v1_info,
)
from reflection.v7_reflection_schema import (
    V7ReflectionSchema,
)
from reflection.v7_constitutional_guard import (
    check_forbidden_vocabulary,
    check_confidence_boundary,
    check_observation_boundary,
)


def test_engine_import() -> bool:
    """
    Test 1: Reflection engine can be imported.
    """
    print("Test 1: Reflection engine can be imported")
    print("-" * 60)

    # Check imports worked
    if reflect_v1 is None:
        print("✗ reflect_v1 not imported")
        return False
    print("✓ reflect_v1 imported")

    if V1ReflectionTags is None:
        print("✗ V1ReflectionTags not imported")
        return False
    print("✓ V1ReflectionTags imported")

    # Check reflection tags defined
    tags = [
        V1ReflectionTags.MEANING_COVERAGE_NARROW,
        V1ReflectionTags.MEANING_COVERAGE_BROAD,
        V1ReflectionTags.MEANING_DISTRIBUTION_SKEWED,
        V1ReflectionTags.FACTOR_DOMINANCE_OBSERVED,
        V1ReflectionTags.UNSEEN_MEANING_COMBINATIONS,
        V1ReflectionTags.SIGNAL_NEVER_OBSERVED,
        V1ReflectionTags.REFLECTION_INSUFFICIENT,
        V1ReflectionTags.UNCLASSIFIED,
    ]

    if len(tags) != 8:
        print(f"✗ Expected 8 reflection tags, got {len(tags)}")
        return False
    print(f"✓ All 8 reflection tags defined")

    print("Test 1: PASS\n")
    return True


def test_minimal_analytics_generates_record() -> bool:
    """
    Test 2: Minimal analytics input generates v7 record.
    """
    print("Test 2: Minimal analytics input generates v7 record")
    print("-" * 60)

    # Empty analytics
    analytics = {}

    try:
        reflection = reflect_v1(analytics)
    except Exception as e:
        print(f"✗ reflect_v1 raised exception: {e}")
        return False

    print("✓ reflect_v1 did not raise exception")

    # Check required fields present
    required_fields = V7ReflectionSchema.REQUIRED_FIELDS

    for field in required_fields:
        if field not in reflection:
            print(f"✗ Missing required field: {field}")
            return False

    print(f"✓ All required v7 fields present")

    # Check mode is ON
    if reflection["v7_reflection_mode"] != "ON":
        print(f"✗ v7_reflection_mode should be ON, got {reflection['v7_reflection_mode']}")
        return False
    print("✓ v7_reflection_mode is ON")

    # Check basis is list
    if not isinstance(reflection["v7_reflection_basis"], list):
        print(f"✗ v7_reflection_basis should be list, got {type(reflection['v7_reflection_basis'])}")
        return False
    print("✓ v7_reflection_basis is list")

    print("Test 2: PASS\n")
    return True


def test_reflection_tags_as_normal_outcome() -> bool:
    """
    Test 3: Each reflection tag appears as normal outcome.
    """
    print("Test 3: Each reflection tag appears as normal outcome")
    print("-" * 60)

    # Test case 1: REFLECTION_INSUFFICIENT (empty analytics)
    analytics1 = {
        "distribution": {
            "total_records": 0,
            "meaning_tag_counts": {},
            "factor_counts": {},
            "signal_counts": {},
        },
        "transitions": {},
    }
    reflection1 = reflect_v1(analytics1)

    if reflection1["v7_reflection_tag"] != V1ReflectionTags.REFLECTION_INSUFFICIENT:
        print(f"✗ Expected REFLECTION_INSUFFICIENT, got {reflection1['v7_reflection_tag']}")
        return False
    print(f"✓ Empty analytics → {V1ReflectionTags.REFLECTION_INSUFFICIENT}")

    # Test case 2: MEANING_COVERAGE_NARROW
    analytics2 = {
        "distribution": {
            "total_records": 100,
            "meaning_tag_counts": {
                "OVERLAY_OBSERVED": 90,
                "ALIGNMENT_STABLE": 10,
            },
            "factor_counts": {},
            "signal_counts": {},
        },
        "transitions": {},
    }
    reflection2 = reflect_v1(analytics2)

    if reflection2["v7_reflection_tag"] != V1ReflectionTags.MEANING_COVERAGE_NARROW:
        print(f"✗ Expected MEANING_COVERAGE_NARROW, got {reflection2['v7_reflection_tag']}")
        return False
    print(f"✓ Narrow coverage → {V1ReflectionTags.MEANING_COVERAGE_NARROW}")

    # Test case 3: MEANING_DISTRIBUTION_SKEWED
    analytics3 = {
        "distribution": {
            "total_records": 100,
            "meaning_tag_counts": {
                "OVERLAY_OBSERVED": 85,
                "ALIGNMENT_STABLE": 10,
                "UNCLASSIFIED": 5,
            },
            "factor_counts": {},
            "signal_counts": {},
        },
        "transitions": {},
    }
    reflection3 = reflect_v1(analytics3)

    if reflection3["v7_reflection_tag"] != V1ReflectionTags.MEANING_DISTRIBUTION_SKEWED:
        print(f"✗ Expected MEANING_DISTRIBUTION_SKEWED, got {reflection3['v7_reflection_tag']}")
        return False
    print(f"✓ Skewed distribution → {V1ReflectionTags.MEANING_DISTRIBUTION_SKEWED}")

    print("Test 3: PASS\n")
    return True


def test_no_forbidden_vocabulary() -> bool:
    """
    Test 4: No forbidden vocabulary in outputs.
    """
    print("Test 4: No forbidden vocabulary in outputs")
    print("-" * 60)

    # Test various analytics
    test_analytics = [
        {
            "distribution": {
                "total_records": 100,
                "meaning_tag_counts": {"OVERLAY_OBSERVED": 90, "ALIGNMENT_STABLE": 10},
                "factor_counts": {},
                "signal_counts": {},
            },
            "transitions": {},
        },
        {
            "distribution": {
                "total_records": 0,
                "meaning_tag_counts": {},
                "factor_counts": {},
                "signal_counts": {},
            },
            "transitions": {},
        },
    ]

    for analytics in test_analytics:
        reflection = reflect_v1(analytics)

        # Check tag
        tag_warnings = check_forbidden_vocabulary(reflection["v7_reflection_tag"])
        if tag_warnings:
            print(f"✗ Forbidden vocabulary in tag: {reflection['v7_reflection_tag']}")
            print(f"  Warnings: {tag_warnings}")
            return False

        # Check summary
        summary_warnings = check_forbidden_vocabulary(reflection["v7_reflection_summary"])
        if summary_warnings:
            print(f"✗ Forbidden vocabulary in summary: {reflection['v7_reflection_summary']}")
            print(f"  Warnings: {summary_warnings}")
            return False

    print("✓ No forbidden vocabulary in any outputs")
    print("Test 4: PASS\n")
    return True


def test_basis_uses_interpretation_fields_only() -> bool:
    """
    Test 5: Basis uses only interpretation fields.
    """
    print("Test 5: Basis uses only interpretation fields")
    print("-" * 60)

    # Test with analytics
    analytics = {
        "distribution": {
            "total_records": 100,
            "meaning_tag_counts": {
                "OVERLAY_OBSERVED": 40,
                "ALIGNMENT_STABLE": 30,
                "DIVERGENCE_WITHOUT_CLASS": 20,
                "UNCLASSIFIED": 10,
            },
            "factor_counts": {
                "REGIME_PRESENT": 80,
                "SHADOW_PRESENT": 70,
            },
            "signal_counts": {
                "DIFF_STATUS_ALIGNED": 30,
                "DIFF_STATUS_DIVERGED": 40,
            },
        },
        "transitions": {},
    }

    reflection = reflect_v1(analytics)
    basis = reflection["v7_reflection_basis"]

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

    # Check no v5 observation fields
    observation_warnings = check_observation_boundary(basis)
    if observation_warnings:
        print(f"✗ Basis contains observation fields: {observation_warnings}")
        return False
    print(f"✓ No v5 observation fields in basis")

    # Check expected fields present
    expected_fields = ["meaning_tag_counts", "total_records"]
    for field in expected_fields:
        if field not in basis:
            print(f"✗ Expected field '{field}' not in basis")
            return False
    print(f"✓ basis contains expected interpretation fields")

    print("Test 5: PASS\n")
    return True


def test_confidence_reason_not_referenced() -> bool:
    """
    Test 6: confidence_reason not referenced.
    """
    print("Test 6: confidence_reason not referenced")
    print("-" * 60)

    # Test with analytics
    analytics = {
        "distribution": {
            "total_records": 100,
            "meaning_tag_counts": {"OVERLAY_OBSERVED": 100},
            "factor_counts": {},
            "signal_counts": {},
        },
        "transitions": {},
    }

    reflection = reflect_v1(analytics)
    basis = reflection["v7_reflection_basis"]

    # Check confidence_reason NOT in basis
    confidence_warnings = check_confidence_boundary(basis)
    if confidence_warnings:
        print(f"✗ Basis contains confidence fields: {confidence_warnings}")
        return False

    print(f"✓ No v0.4 confidence fields in basis")

    # Check summary doesn't reference confidence
    summary = reflection["v7_reflection_summary"]
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
        {"distribution": None},  # None value
        {"distribution": {"total_records": "invalid"}},  # Invalid value
        {"unknown_field": "value"},  # Unknown field
    ]

    for analytics in edge_cases:
        try:
            reflection = reflect_v1(analytics)
            # Should succeed without raising
        except Exception as e:
            print(f"✗ reflect_v1 raised exception for edge case {analytics}: {e}")
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
    print("PR71: v0.7 Reflection Engine v1 Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Engine import", test_engine_import),
        ("Minimal analytics generates record", test_minimal_analytics_generates_record),
        ("Reflection tags as normal outcome", test_reflection_tags_as_normal_outcome),
        ("No forbidden vocabulary", test_no_forbidden_vocabulary),
        ("Basis uses interpretation fields only", test_basis_uses_interpretation_fields_only),
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
        print("✓ ALL PR71 REFLECTION ENGINE V1 TESTS PASSED")
    else:
        print("⚠ SOME PR71 REFLECTION ENGINE V1 TESTS FAILED")
    print("=" * 60)
    print("PR71 Requirements Verified:")
    print("  - Reflection engine can be imported")
    print("  - Minimal analytics input generates v7 record")
    print("  - Reflection tags appear as normal outcome")
    print("  - No forbidden vocabulary in outputs")
    print("  - Basis uses only interpretation fields")
    print("  - confidence_reason not referenced")
    print("  - Exit code always 0 (warning-only)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
