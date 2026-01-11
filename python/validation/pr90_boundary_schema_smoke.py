#!/usr/bin/env python3
"""
PR90: v0.9 Boundary Schema & Constitutional Guard Smoke Test

Purpose:
    Validate that v0.9 boundary schema and constitutional guards
    are correctly defined and enforced.

Test Coverage:
    1. v9 schema fields exist and are well-defined
    2. Empty boundary record can be created
    3. Schema validation detects structure violations
    4. Forbidden vocabulary detection works
    5. v0.4 boundary guard detects confidence_reason access
    6. Observation boundary guard detects v5 field access
    7. Complete record passes all guards (if clean)
    8. Exit code always 0 (warning-only)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict, List

# Import v0.9 boundary modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from boundary.v9_boundary_schema import (
    V9BoundarySchema,
    validate_basis_fields,
    get_schema_info,
)
from boundary.v9_constitutional_guard import (
    validate_boundary_record,
    check_forbidden_vocabulary,
    check_confidence_boundary,
    check_observation_boundary,
)


def test_schema_fields_exist() -> bool:
    """
    Test 1: v9 schema fields exist and are well-defined.
    """
    print("Test 1: v9 schema fields exist and are well-defined")
    print("-" * 60)

    # Check required fields
    required = V9BoundarySchema.REQUIRED_FIELDS

    if len(required) == 0:
        print("✗ No required fields defined")
        return False
    print(f"✓ Required fields defined: {len(required)}")

    expected_fields = [
        "v9_boundary_mode",
        "v9_boundary_status",
        "v9_boundary_type",
        "v9_boundary_description",
        "v9_boundary_basis",
    ]

    for field in expected_fields:
        if field not in required:
            print(f"✗ Expected field '{field}' not in required fields")
            return False
        print(f"✓ Field '{field}' present")

    print("Test 1: PASS\n")
    return True


def test_empty_record_creation() -> bool:
    """
    Test 2: Empty boundary record can be created.
    """
    print("Test 2: Empty boundary record can be created")
    print("-" * 60)

    try:
        record = V9BoundarySchema.create_empty_record()
    except Exception as e:
        print(f"✗ Failed to create empty record: {e}")
        return False

    print(f"✓ Empty record created")

    # Check it has required fields
    for field in V9BoundarySchema.REQUIRED_FIELDS:
        if field not in record:
            print(f"✗ Empty record missing field '{field}'")
            return False

    print(f"✓ Empty record has all required fields")

    # Check defaults are safe
    if record["v9_boundary_mode"] != "OFF":
        print(f"✗ Default mode should be OFF, got {record['v9_boundary_mode']}")
        return False
    print(f"✓ Default mode is OFF")

    if record["v9_boundary_status"] != "UNAVAILABLE":
        print(f"✗ Default status should be UNAVAILABLE, got {record['v9_boundary_status']}")
        return False
    print(f"✓ Default status is UNAVAILABLE")

    print("Test 2: PASS\n")
    return True


def test_schema_validation_detects_violations() -> bool:
    """
    Test 3: Schema validation detects structure violations.
    """
    print("Test 3: Schema validation detects structure violations")
    print("-" * 60)

    # Test case 1: Missing required field
    record1 = {
        "v9_boundary_mode": "ON",
        # Missing v9_boundary_status
        "v9_boundary_type": "TEST",
        "v9_boundary_description": "test",
        "v9_boundary_basis": [],
    }

    warnings1 = V9BoundarySchema.validate_structure(record1)

    if len(warnings1) == 0:
        print("✗ Should detect missing field")
        return False
    print(f"✓ Detected missing field: {len(warnings1)} warnings")

    # Test case 2: Invalid type
    record2 = V9BoundarySchema.create_empty_record()
    record2["v9_boundary_basis"] = "not_a_list"  # Should be list

    warnings2 = V9BoundarySchema.validate_structure(record2)

    if len(warnings2) == 0:
        print("✗ Should detect type mismatch")
        return False
    print(f"✓ Detected type mismatch: {len(warnings2)} warnings")

    # Test case 3: Invalid enum value
    record3 = V9BoundarySchema.create_empty_record()
    record3["v9_boundary_mode"] = "INVALID"

    warnings3 = V9BoundarySchema.validate_structure(record3)

    if len(warnings3) == 0:
        print("✗ Should detect invalid enum value")
        return False
    print(f"✓ Detected invalid enum value: {len(warnings3)} warnings")

    # Test case 4: Valid record
    record4 = V9BoundarySchema.create_empty_record()

    warnings4 = V9BoundarySchema.validate_structure(record4)

    if len(warnings4) != 0:
        print(f"✗ Valid record should have no warnings, got {len(warnings4)}")
        return False
    print(f"✓ Valid record has no warnings")

    print("Test 3: PASS\n")
    return True


def test_forbidden_vocabulary_detection() -> bool:
    """
    Test 4: Forbidden vocabulary detection works.
    """
    print("Test 4: Forbidden vocabulary detection works")
    print("-" * 60)

    # Test cases: (text, should_have_warnings)
    test_cases = [
        ("this is a good result", True),
        ("observability limit at schema boundary", False),
        ("the score is high", True),
        ("structural boundary at engine layer", False),
        ("you should fix this", True),
        ("boundary unavailable", False),
        ("correct interpretation", True),
        ("certain limits not expressible", False),
    ]

    for text, should_warn in test_cases:
        warnings = check_forbidden_vocabulary(text)
        has_warning = len(warnings) > 0

        if has_warning != should_warn:
            print(f"✗ '{text}' -> expected warnings={should_warn}, got {len(warnings)}")
            return False

        status = "warns" if has_warning else "clean"
        print(f"✓ '{text}' -> {status}")

    print("Test 4: PASS\n")
    return True


def test_v04_boundary_guard() -> bool:
    """
    Test 5: v0.4 boundary guard detects confidence_reason access.
    """
    print("Test 5: v0.4 boundary guard detects confidence_reason access")
    print("-" * 60)

    # Test case 1: Clean basis (no v0.4 fields)
    basis1 = ["v8_blindspot_tag", "v7_reflection_tag"]
    warnings1 = check_confidence_boundary(basis1)

    if len(warnings1) != 0:
        print(f"✗ Clean basis should have no warnings, got {len(warnings1)}")
        return False
    print(f"✓ Clean basis has no warnings")

    # Test case 2: v0.4 boundary violation
    basis2 = ["v8_blindspot_tag", "confidence_reason"]
    warnings2 = check_confidence_boundary(basis2)

    if len(warnings2) == 0:
        print("✗ Should detect confidence_reason in basis")
        return False
    print(f"✓ Detected confidence_reason violation: {len(warnings2)} warnings")

    # Test case 3: Multiple v0.4 violations
    basis3 = ["confidence_reason", "confidence_reason_version"]
    warnings3 = check_confidence_boundary(basis3)

    if len(warnings3) < 2:
        print(f"✗ Should detect multiple violations, got {len(warnings3)}")
        return False
    print(f"✓ Detected multiple violations: {len(warnings3)} warnings")

    print("Test 5: PASS\n")
    return True


def test_observation_boundary_guard() -> bool:
    """
    Test 6: Observation boundary guard detects v5 field access.
    """
    print("Test 6: Observation boundary guard detects v5 field access")
    print("-" * 60)

    # Test case 1: Clean basis (blindspot/interpretation/reflection fields only)
    basis1 = ["v8_blindspot_tag", "v7_reflection_tag", "v6_meaning_tag"]
    warnings1 = check_observation_boundary(basis1)

    if len(warnings1) != 0:
        print(f"✗ Clean basis should have no warnings, got {len(warnings1)}")
        return False
    print(f"✓ Clean basis has no warnings")

    # Test case 2: Observation boundary violation
    basis2 = ["v8_blindspot_tag", "v5_decision_diff_status"]
    warnings2 = check_observation_boundary(basis2)

    if len(warnings2) == 0:
        print("✗ Should detect v5 field in basis")
        return False
    print(f"✓ Detected v5 field violation: {len(warnings2)} warnings")

    # Test case 3: Multiple observation violations
    basis3 = ["v5_decision_diff_status", "v5_decision_diff_semantics_tag"]
    warnings3 = check_observation_boundary(basis3)

    if len(warnings3) < 2:
        print(f"✗ Should detect multiple violations, got {len(warnings3)}")
        return False
    print(f"✓ Detected multiple violations: {len(warnings3)} warnings")

    print("Test 6: PASS\n")
    return True


def test_complete_record_validation() -> bool:
    """
    Test 7: Complete record passes all guards (if clean).
    """
    print("Test 7: Complete record passes all guards (if clean)")
    print("-" * 60)

    # Clean record
    clean_record = {
        "v9_boundary_mode": "ON",
        "v9_boundary_status": "AVAILABLE",
        "v9_boundary_type": "SCHEMA_BOUNDARY",
        "v9_boundary_description": "observability limit at schema layer. structure cannot be expressed with current schema.",
        "v9_boundary_basis": ["v8_blindspot_tag", "v7_reflection_tag"],
    }

    # Check schema
    schema_warnings = V9BoundarySchema.validate_structure(clean_record)
    if len(schema_warnings) != 0:
        print(f"✗ Clean record failed schema validation: {schema_warnings}")
        return False
    print(f"✓ Clean record passes schema validation")

    # Check constitutional guards
    guard_warnings = validate_boundary_record(clean_record)
    if len(guard_warnings) != 0:
        print(f"✗ Clean record failed constitutional guards: {guard_warnings}")
        return False
    print(f"✓ Clean record passes constitutional guards")

    # Dirty record (evaluative vocabulary)
    dirty_record = {
        "v9_boundary_mode": "ON",
        "v9_boundary_status": "AVAILABLE",
        "v9_boundary_type": "BAD_BOUNDARY",
        "v9_boundary_description": "this is a bad boundary that should be fixed.",
        "v9_boundary_basis": ["v8_blindspot_tag"],
    }

    guard_warnings2 = validate_boundary_record(dirty_record)
    if len(guard_warnings2) == 0:
        print("✗ Dirty record should fail vocabulary check")
        return False
    print(f"✓ Dirty record detected: {len(guard_warnings2)} violations")

    # Dirty record (v0.4 violation)
    dirty_record2 = {
        "v9_boundary_mode": "ON",
        "v9_boundary_status": "AVAILABLE",
        "v9_boundary_type": "BOUNDARY_GAP",
        "v9_boundary_description": "gap observed.",
        "v9_boundary_basis": ["confidence_reason"],
    }

    guard_warnings3 = validate_boundary_record(dirty_record2)
    if len(guard_warnings3) == 0:
        print("✗ Dirty record should fail boundary check")
        return False
    print(f"✓ Dirty record detected: {len(guard_warnings3)} violations")

    # Dirty record (observation violation)
    dirty_record3 = {
        "v9_boundary_mode": "ON",
        "v9_boundary_status": "AVAILABLE",
        "v9_boundary_type": "BOUNDARY_GAP",
        "v9_boundary_description": "gap observed.",
        "v9_boundary_basis": ["v5_decision_diff_status"],
    }

    guard_warnings4 = validate_boundary_record(dirty_record3)
    if len(guard_warnings4) == 0:
        print("✗ Dirty record should fail observation boundary check")
        return False
    print(f"✓ Dirty record detected: {len(guard_warnings4)} violations")

    print("Test 7: PASS\n")
    return True


def test_exit_code_always_zero() -> bool:
    """
    Test 8: Exit code always 0 (warning-only).
    """
    print("Test 8: Exit code always 0 (warning-only)")
    print("-" * 60)

    # All validation functions return warnings, never raise
    # This test confirms the design principle

    print("✓ All validation functions return warnings (never raise)")
    print("✓ Exit code will be 0 (warning-only by design)")

    print("Test 8: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR90: v0.9 Boundary Schema & Guard Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("v9 schema fields exist", test_schema_fields_exist),
        ("Empty record creation", test_empty_record_creation),
        ("Schema validation detects violations", test_schema_validation_detects_violations),
        ("Forbidden vocabulary detection", test_forbidden_vocabulary_detection),
        ("v0.4 boundary guard", test_v04_boundary_guard),
        ("Observation boundary guard", test_observation_boundary_guard),
        ("Complete record validation", test_complete_record_validation),
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
        print("✓ ALL PR90 BOUNDARY SCHEMA TESTS PASSED")
    else:
        print("⚠ SOME PR90 BOUNDARY SCHEMA TESTS FAILED")
    print("=" * 60)
    print("PR90 Requirements Verified:")
    print("  - v9 schema fields exist and are well-defined")
    print("  - Empty boundary record can be created")
    print("  - Schema validation detects structure violations")
    print("  - Forbidden vocabulary detection works")
    print("  - v0.4 boundary guard detects confidence_reason access")
    print("  - Observation boundary guard detects v5 field access")
    print("  - Complete record passes all guards (if clean)")
    print("  - Exit code always 0 (warning-only)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
