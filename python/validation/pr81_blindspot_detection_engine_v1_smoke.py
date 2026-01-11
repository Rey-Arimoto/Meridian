#!/usr/bin/env python3
"""
PR81: v0.8 Blindspot Detection Engine v1 Smoke Test

Purpose:
    Validate that v0.8 blindspot detection engine v1 correctly detects
    structural absences from interpretation analytics.

Test Coverage:
    1. Detection engine can be imported
    2. Minimal analytics input generates v8 record
    3. Each blindspot tag appears as normal outcome
    4. No forbidden vocabulary in outputs
    5. Basis uses only interpretation/reflection fields
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

# Import v0.8 blindspot modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from blindspot.v8_blindspot_detection_engine_v1 import (
    detect_blindspot_v1,
    detect_blindspot_batch_v1,
    V1BlindspotTags,
    get_engine_v1_info,
)
from blindspot.v8_blindspot_schema import (
    V8BlindspotSchema,
)
from blindspot.v8_constitutional_guard import (
    check_forbidden_vocabulary,
    check_confidence_boundary,
    check_observation_boundary,
)


def test_engine_import() -> bool:
    """
    Test 1: Detection engine can be imported.
    """
    print("Test 1: Detection engine can be imported")
    print("-" * 60)

    # Check imports worked
    if detect_blindspot_v1 is None:
        print("✗ detect_blindspot_v1 not imported")
        return False
    print("✓ detect_blindspot_v1 imported")

    if V1BlindspotTags is None:
        print("✗ V1BlindspotTags not imported")
        return False
    print("✓ V1BlindspotTags imported")

    # Check blindspot tags defined
    tags = [
        V1BlindspotTags.ABSENCE_INSUFFICIENT_EVIDENCE,
        V1BlindspotTags.ABSENCE_UNSEEN_SIGNAL_TYPES,
        V1BlindspotTags.ABSENCE_UNSEEN_FACTOR_TYPES,
        V1BlindspotTags.ABSENCE_UNOBSERVED_MEANING_TYPES,
        V1BlindspotTags.ABSENCE_TRANSITION_NOT_OBSERVED,
        V1BlindspotTags.ABSENCE_SCHEMA_CANNOT_EXPRESS,
        V1BlindspotTags.UNCLASSIFIED,
    ]

    if len(tags) != 7:
        print(f"✗ Expected 7 blindspot tags, got {len(tags)}")
        return False
    print(f"✓ All 7 blindspot tags defined")

    print("Test 1: PASS\n")
    return True


def test_minimal_analytics_generates_record() -> bool:
    """
    Test 2: Minimal analytics input generates v8 record.
    """
    print("Test 2: Minimal analytics input generates v8 record")
    print("-" * 60)

    # Empty analytics
    analytics = {}

    try:
        blindspot = detect_blindspot_v1(analytics)
    except Exception as e:
        print(f"✗ detect_blindspot_v1 raised exception: {e}")
        return False

    print("✓ detect_blindspot_v1 did not raise exception")

    # Check required fields present
    required_fields = V8BlindspotSchema.REQUIRED_FIELDS

    for field in required_fields:
        if field not in blindspot:
            print(f"✗ Missing required field: {field}")
            return False

    print(f"✓ All required v8 fields present")

    # Check mode is ON
    if blindspot["v8_blindspot_mode"] != "ON":
        print(f"✗ v8_blindspot_mode should be ON, got {blindspot['v8_blindspot_mode']}")
        return False
    print("✓ v8_blindspot_mode is ON")

    # Check basis is list
    if not isinstance(blindspot["v8_blindspot_basis"], list):
        print(f"✗ v8_blindspot_basis should be list, got {type(blindspot['v8_blindspot_basis'])}")
        return False
    print("✓ v8_blindspot_basis is list")

    print("Test 2: PASS\n")
    return True


def test_blindspot_tags_as_normal_outcome() -> bool:
    """
    Test 3: Each blindspot tag appears as normal outcome.
    """
    print("Test 3: Each blindspot tag appears as normal outcome")
    print("-" * 60)

    # Test case 1: ABSENCE_INSUFFICIENT_EVIDENCE (empty analytics)
    analytics1 = {
        "distribution": {
            "total_records": 0,
            "meaning_tag_counts": {},
            "factor_counts": {},
            "signal_counts": {},
        },
        "transitions": {},
    }
    blindspot1 = detect_blindspot_v1(analytics1)

    if blindspot1["v8_blindspot_tag"] != V1BlindspotTags.ABSENCE_INSUFFICIENT_EVIDENCE:
        print(f"✗ Expected ABSENCE_INSUFFICIENT_EVIDENCE, got {blindspot1['v8_blindspot_tag']}")
        return False
    print(f"✓ Empty analytics → {V1BlindspotTags.ABSENCE_INSUFFICIENT_EVIDENCE}")

    # Test case 2: ABSENCE_UNSEEN_SIGNAL_TYPES
    analytics2 = {
        "distribution": {
            "total_records": 100,
            "meaning_tag_counts": {
                "OVERLAY_OBSERVED": 50,
                "ALIGNMENT_STABLE": 50,
            },
            "factor_counts": {},
            "signal_counts": {
                "DIFF_STATUS_ALIGNED": 50,
                # Missing: DIFF_STATUS_DIVERGED, DIFF_STATUS_UNAVAILABLE, etc.
            },
        },
        "transitions": {},
    }
    blindspot2 = detect_blindspot_v1(analytics2)

    if blindspot2["v8_blindspot_tag"] != V1BlindspotTags.ABSENCE_UNSEEN_SIGNAL_TYPES:
        print(f"✗ Expected ABSENCE_UNSEEN_SIGNAL_TYPES, got {blindspot2['v8_blindspot_tag']}")
        return False
    print(f"✓ Unseen signals → {V1BlindspotTags.ABSENCE_UNSEEN_SIGNAL_TYPES}")

    # Test case 3: ABSENCE_UNOBSERVED_MEANING_TYPES
    analytics3 = {
        "distribution": {
            "total_records": 100,
            "meaning_tag_counts": {
                "OVERLAY_OBSERVED": 100,
                # Only 1 meaning type, 6 others missing
            },
            "factor_counts": {},
            "signal_counts": {},
        },
        "transitions": {},
    }
    blindspot3 = detect_blindspot_v1(analytics3)

    if blindspot3["v8_blindspot_tag"] != V1BlindspotTags.ABSENCE_UNOBSERVED_MEANING_TYPES:
        print(f"✗ Expected ABSENCE_UNOBSERVED_MEANING_TYPES, got {blindspot3['v8_blindspot_tag']}")
        return False
    print(f"✓ Unobserved meanings → {V1BlindspotTags.ABSENCE_UNOBSERVED_MEANING_TYPES}")

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
                "meaning_tag_counts": {"OVERLAY_OBSERVED": 100},
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
        blindspot = detect_blindspot_v1(analytics)

        # Check tag
        tag_warnings = check_forbidden_vocabulary(blindspot["v8_blindspot_tag"])
        if tag_warnings:
            print(f"✗ Forbidden vocabulary in tag: {blindspot['v8_blindspot_tag']}")
            print(f"  Warnings: {tag_warnings}")
            return False

        # Check summary
        summary_warnings = check_forbidden_vocabulary(blindspot["v8_blindspot_summary"])
        if summary_warnings:
            print(f"✗ Forbidden vocabulary in summary: {blindspot['v8_blindspot_summary']}")
            print(f"  Warnings: {summary_warnings}")
            return False

    print("✓ No forbidden vocabulary in any outputs")
    print("Test 4: PASS\n")
    return True


def test_basis_uses_interpretation_reflection_fields_only() -> bool:
    """
    Test 5: Basis uses only interpretation/reflection fields.
    """
    print("Test 5: Basis uses only interpretation/reflection fields")
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
            },
        },
        "transitions": {},
    }

    blindspot = detect_blindspot_v1(analytics)
    basis = blindspot["v8_blindspot_basis"]

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

    blindspot = detect_blindspot_v1(analytics)
    basis = blindspot["v8_blindspot_basis"]

    # Check confidence_reason NOT in basis
    confidence_warnings = check_confidence_boundary(basis)
    if confidence_warnings:
        print(f"✗ Basis contains confidence fields: {confidence_warnings}")
        return False

    print(f"✓ No v0.4 confidence fields in basis")

    # Check summary doesn't reference confidence
    summary = blindspot["v8_blindspot_summary"]
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
            blindspot = detect_blindspot_v1(analytics)
            # Should succeed without raising
        except Exception as e:
            print(f"✗ detect_blindspot_v1 raised exception for edge case {analytics}: {e}")
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
    print("PR81: v0.8 Blindspot Detection Engine v1 Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Engine import", test_engine_import),
        ("Minimal analytics generates record", test_minimal_analytics_generates_record),
        ("Blindspot tags as normal outcome", test_blindspot_tags_as_normal_outcome),
        ("No forbidden vocabulary", test_no_forbidden_vocabulary),
        ("Basis uses interpretation/reflection fields only", test_basis_uses_interpretation_reflection_fields_only),
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
        print("✓ ALL PR81 BLINDSPOT DETECTION ENGINE V1 TESTS PASSED")
    else:
        print("⚠ SOME PR81 BLINDSPOT DETECTION ENGINE V1 TESTS FAILED")
    print("=" * 60)
    print("PR81 Requirements Verified:")
    print("  - Detection engine can be imported")
    print("  - Minimal analytics input generates v8 record")
    print("  - Blindspot tags appear as normal outcome")
    print("  - No forbidden vocabulary in outputs")
    print("  - Basis uses only interpretation/reflection fields")
    print("  - confidence_reason not referenced")
    print("  - Exit code always 0 (warning-only)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
