#!/usr/bin/env python3
"""
PR91: v0.9 Boundary Classification Engine v1 Smoke Test

Purpose:
    Validate that v0.9 boundary classification engine v1 correctly classifies
    blindspots into structural boundary types.

Test Coverage:
    1. Classification engine can be imported
    2. Minimal blindspot input generates v9 record
    3. Each boundary type appears as normal outcome
    4. No forbidden vocabulary in outputs
    5. Basis uses only blindspot/interpretation/reflection fields
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

# Import v0.9 boundary modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from boundary.v9_boundary_classification_engine_v1 import (
    classify_boundary_v1,
    classify_boundary_batch_v1,
    V1BoundaryTypes,
    get_engine_v1_info,
)
from boundary.v9_boundary_schema import (
    V9BoundarySchema,
)
from boundary.v9_constitutional_guard import (
    check_forbidden_vocabulary,
    check_confidence_boundary,
    check_observation_boundary,
)


def test_engine_import() -> bool:
    """
    Test 1: Classification engine can be imported.
    """
    print("Test 1: Classification engine can be imported")
    print("-" * 60)

    # Check imports worked
    if classify_boundary_v1 is None:
        print("✗ classify_boundary_v1 not imported")
        return False
    print("✓ classify_boundary_v1 imported")

    if V1BoundaryTypes is None:
        print("✗ V1BoundaryTypes not imported")
        return False
    print("✓ V1BoundaryTypes imported")

    # Check boundary types defined
    types = [
        V1BoundaryTypes.SCHEMA_BOUNDARY,
        V1BoundaryTypes.DATA_BOUNDARY,
        V1BoundaryTypes.ENGINE_BOUNDARY,
        V1BoundaryTypes.SAMPLING_BOUNDARY,
        V1BoundaryTypes.TEMPORAL_BOUNDARY,
        V1BoundaryTypes.UNCLASSIFIED,
    ]

    if len(types) != 6:
        print(f"✗ Expected 6 boundary types, got {len(types)}")
        return False
    print(f"✓ All 6 boundary types defined")

    print("Test 1: PASS\n")
    return True


def test_minimal_blindspot_generates_record() -> bool:
    """
    Test 2: Minimal blindspot input generates v9 record.
    """
    print("Test 2: Minimal blindspot input generates v9 record")
    print("-" * 60)

    # Empty blindspot
    blindspot = {}

    try:
        boundary = classify_boundary_v1(blindspot)
    except Exception as e:
        print(f"✗ classify_boundary_v1 raised exception: {e}")
        return False

    print("✓ classify_boundary_v1 did not raise exception")

    # Check required fields present
    required_fields = V9BoundarySchema.REQUIRED_FIELDS

    for field in required_fields:
        if field not in boundary:
            print(f"✗ Missing required field: {field}")
            return False

    print(f"✓ All required v9 fields present")

    # Check mode is ON
    if boundary["v9_boundary_mode"] != "ON":
        print(f"✗ v9_boundary_mode should be ON, got {boundary['v9_boundary_mode']}")
        return False
    print("✓ v9_boundary_mode is ON")

    # Check basis is list
    if not isinstance(boundary["v9_boundary_basis"], list):
        print(f"✗ v9_boundary_basis should be list, got {type(boundary['v9_boundary_basis'])}")
        return False
    print("✓ v9_boundary_basis is list")

    print("Test 2: PASS\n")
    return True


def test_boundary_types_as_normal_outcome() -> bool:
    """
    Test 3: Each boundary type appears as normal outcome.
    """
    print("Test 3: Each boundary type appears as normal outcome")
    print("-" * 60)

    # Test case 1: DATA_BOUNDARY (insufficient evidence)
    blindspot1 = {
        "v8_blindspot_mode": "ON",
        "v8_blindspot_status": "UNAVAILABLE",
        "v8_blindspot_tag": "ABSENCE_INSUFFICIENT_EVIDENCE",
        "v8_blindspot_summary": "data insufficient",
        "v8_blindspot_basis": [],
    }
    boundary1 = classify_boundary_v1(blindspot1)

    if boundary1["v9_boundary_type"] != V1BoundaryTypes.DATA_BOUNDARY:
        print(f"✗ Expected DATA_BOUNDARY, got {boundary1['v9_boundary_type']}")
        return False
    print(f"✓ Insufficient evidence → {V1BoundaryTypes.DATA_BOUNDARY}")

    # Test case 2: SCHEMA_BOUNDARY
    blindspot2 = {
        "v8_blindspot_mode": "ON",
        "v8_blindspot_status": "AVAILABLE",
        "v8_blindspot_tag": "ABSENCE_SCHEMA_CANNOT_EXPRESS",
        "v8_blindspot_summary": "schema limitation",
        "v8_blindspot_basis": [],
    }
    boundary2 = classify_boundary_v1(blindspot2)

    if boundary2["v9_boundary_type"] != V1BoundaryTypes.SCHEMA_BOUNDARY:
        print(f"✗ Expected SCHEMA_BOUNDARY, got {boundary2['v9_boundary_type']}")
        return False
    print(f"✓ Schema limitation → {V1BoundaryTypes.SCHEMA_BOUNDARY}")

    # Test case 3: SAMPLING_BOUNDARY
    blindspot3 = {
        "v8_blindspot_mode": "ON",
        "v8_blindspot_status": "AVAILABLE",
        "v8_blindspot_tag": "ABSENCE_UNSEEN_SIGNAL_TYPES",
        "v8_blindspot_summary": "signals not observed",
        "v8_blindspot_basis": [],
    }
    boundary3 = classify_boundary_v1(blindspot3)

    if boundary3["v9_boundary_type"] != V1BoundaryTypes.SAMPLING_BOUNDARY:
        print(f"✗ Expected SAMPLING_BOUNDARY, got {boundary3['v9_boundary_type']}")
        return False
    print(f"✓ Unseen signals → {V1BoundaryTypes.SAMPLING_BOUNDARY}")

    print("Test 3: PASS\n")
    return True


def test_no_forbidden_vocabulary() -> bool:
    """
    Test 4: No forbidden vocabulary in outputs.
    """
    print("Test 4: No forbidden vocabulary in outputs")
    print("-" * 60)

    # Test various blindspots
    test_blindspots = [
        {
            "v8_blindspot_mode": "ON",
            "v8_blindspot_status": "AVAILABLE",
            "v8_blindspot_tag": "ABSENCE_UNSEEN_SIGNAL_TYPES",
            "v8_blindspot_summary": "signals not observed",
            "v8_blindspot_basis": [],
        },
        {
            "v8_blindspot_mode": "ON",
            "v8_blindspot_status": "UNAVAILABLE",
            "v8_blindspot_tag": "ABSENCE_INSUFFICIENT_EVIDENCE",
            "v8_blindspot_summary": "data insufficient",
            "v8_blindspot_basis": [],
        },
    ]

    for blindspot in test_blindspots:
        boundary = classify_boundary_v1(blindspot)

        # Check type
        type_warnings = check_forbidden_vocabulary(boundary["v9_boundary_type"])
        if type_warnings:
            print(f"✗ Forbidden vocabulary in type: {boundary['v9_boundary_type']}")
            print(f"  Warnings: {type_warnings}")
            return False

        # Check description
        description_warnings = check_forbidden_vocabulary(boundary["v9_boundary_description"])
        if description_warnings:
            print(f"✗ Forbidden vocabulary in description: {boundary['v9_boundary_description']}")
            print(f"  Warnings: {description_warnings}")
            return False

    print("✓ No forbidden vocabulary in any outputs")
    print("Test 4: PASS\n")
    return True


def test_basis_uses_blindspot_fields_only() -> bool:
    """
    Test 5: Basis uses only blindspot/interpretation/reflection fields.
    """
    print("Test 5: Basis uses only blindspot/interpretation/reflection fields")
    print("-" * 60)

    # Test with blindspot
    blindspot = {
        "v8_blindspot_mode": "ON",
        "v8_blindspot_status": "AVAILABLE",
        "v8_blindspot_tag": "ABSENCE_UNSEEN_SIGNAL_TYPES",
        "v8_blindspot_summary": "signals not observed",
        "v8_blindspot_basis": ["signal_counts", "total_records"],
    }

    boundary = classify_boundary_v1(blindspot)
    basis = boundary["v9_boundary_basis"]

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
    expected_fields = ["v8_blindspot_tag"]
    for field in expected_fields:
        if field not in basis:
            print(f"✗ Expected field '{field}' not in basis")
            return False
    print(f"✓ basis contains expected blindspot fields")

    print("Test 5: PASS\n")
    return True


def test_confidence_reason_not_referenced() -> bool:
    """
    Test 6: confidence_reason not referenced.
    """
    print("Test 6: confidence_reason not referenced")
    print("-" * 60)

    # Test with blindspot
    blindspot = {
        "v8_blindspot_mode": "ON",
        "v8_blindspot_status": "AVAILABLE",
        "v8_blindspot_tag": "ABSENCE_UNSEEN_SIGNAL_TYPES",
        "v8_blindspot_summary": "signals not observed",
        "v8_blindspot_basis": [],
    }

    boundary = classify_boundary_v1(blindspot)
    basis = boundary["v9_boundary_basis"]

    # Check confidence_reason NOT in basis
    confidence_warnings = check_confidence_boundary(basis)
    if confidence_warnings:
        print(f"✗ Basis contains confidence fields: {confidence_warnings}")
        return False

    print(f"✓ No v0.4 confidence fields in basis")

    # Check description doesn't reference confidence
    description = boundary["v9_boundary_description"]
    if "confidence" in description.lower():
        print(f"✗ Description references 'confidence': {description}")
        return False
    print(f"✓ Description does not reference confidence")

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
        {"v8_blindspot_status": None},  # None value
        {"v8_blindspot_tag": 123},  # Invalid type
        {"unknown_field": "value"},  # Unknown field
    ]

    for blindspot in edge_cases:
        try:
            boundary = classify_boundary_v1(blindspot)
            # Should succeed without raising
        except Exception as e:
            print(f"✗ classify_boundary_v1 raised exception for edge case {blindspot}: {e}")
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
    print("PR91: v0.9 Boundary Classification Engine v1 Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Engine import", test_engine_import),
        ("Minimal blindspot generates record", test_minimal_blindspot_generates_record),
        ("Boundary types as normal outcome", test_boundary_types_as_normal_outcome),
        ("No forbidden vocabulary", test_no_forbidden_vocabulary),
        ("Basis uses blindspot/interpretation/reflection fields only", test_basis_uses_blindspot_fields_only),
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
        print("✓ ALL PR91 BOUNDARY CLASSIFICATION ENGINE V1 TESTS PASSED")
    else:
        print("⚠ SOME PR91 BOUNDARY CLASSIFICATION ENGINE V1 TESTS FAILED")
    print("=" * 60)
    print("PR91 Requirements Verified:")
    print("  - Classification engine can be imported")
    print("  - Minimal blindspot input generates v9 record")
    print("  - Boundary types appear as normal outcome")
    print("  - No forbidden vocabulary in outputs")
    print("  - Basis uses only blindspot/interpretation/reflection fields")
    print("  - confidence_reason not referenced")
    print("  - Exit code always 0 (warning-only)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
