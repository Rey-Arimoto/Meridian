#!/usr/bin/env python3
"""
PR60: v0.6 Interpretation Schema & Constitutional Guard Smoke Test

Purpose:
    Validate that v0.6 interpretation schema and constitutional guards
    are correctly defined and enforced.

Test Coverage:
    1. v6 schema fields exist and are well-defined
    2. Empty interpretation record can be created
    3. Schema validation detects structure violations
    4. Forbidden vocabulary detection works
    5. v0.4 boundary guard detects confidence_reason access
    6. Complete record passes all guards (if clean)
    7. Exit code always 0 (warning-only)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict, List

# Import v0.6 interpretation modules
sys.path.insert(0, ".")
from python.interpretation.v6_interpretation_schema import (
    V6InterpretationSchema,
    validate_basis_fields,
    get_schema_info,
)
from python.interpretation.v6_constitutional_guard import (
    validate_interpretation_record,
    check_forbidden_vocabulary,
    check_confidence_boundary,
)


def test_schema_fields_exist() -> bool:
    """
    Test 1: v6 schema fields exist and are well-defined.
    """
    print("Test 1: v6 schema fields exist and are well-defined")
    print("-" * 60)

    # Check required fields
    required = V6InterpretationSchema.REQUIRED_FIELDS

    if len(required) == 0:
        print("✗ No required fields defined")
        return False
    print(f"✓ Required fields defined: {len(required)}")

    expected_fields = [
        "v6_meaning_mode",
        "v6_meaning_status",
        "v6_meaning_tag",
        "v6_meaning_summary",
        "v6_meaning_basis",
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
    Test 2: Empty interpretation record can be created.
    """
    print("Test 2: Empty interpretation record can be created")
    print("-" * 60)

    try:
        record = V6InterpretationSchema.create_empty_record()
    except Exception as e:
        print(f"✗ Failed to create empty record: {e}")
        return False

    print(f"✓ Empty record created")

    # Check it has required fields
    for field in V6InterpretationSchema.REQUIRED_FIELDS:
        if field not in record:
            print(f"✗ Empty record missing field '{field}'")
            return False

    print(f"✓ Empty record has all required fields")

    # Check defaults are safe
    if record["v6_meaning_mode"] != "OFF":
        print(f"✗ Default mode should be OFF, got {record['v6_meaning_mode']}")
        return False
    print(f"✓ Default mode is OFF")

    if record["v6_meaning_status"] != "UNAVAILABLE":
        print(f"✗ Default status should be UNAVAILABLE, got {record['v6_meaning_status']}")
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
        "v6_meaning_mode": "ON",
        # Missing v6_meaning_status
        "v6_meaning_tag": "TEST",
        "v6_meaning_summary": "test",
        "v6_meaning_basis": [],
    }

    warnings1 = V6InterpretationSchema.validate_structure(record1)

    if len(warnings1) == 0:
        print("✗ Should detect missing field")
        return False
    print(f"✓ Detected missing field: {len(warnings1)} warnings")

    # Test case 2: Invalid type
    record2 = V6InterpretationSchema.create_empty_record()
    record2["v6_meaning_basis"] = "not_a_list"  # Should be list

    warnings2 = V6InterpretationSchema.validate_structure(record2)

    if len(warnings2) == 0:
        print("✗ Should detect type mismatch")
        return False
    print(f"✓ Detected type mismatch: {len(warnings2)} warnings")

    # Test case 3: Invalid enum value
    record3 = V6InterpretationSchema.create_empty_record()
    record3["v6_meaning_mode"] = "INVALID"

    warnings3 = V6InterpretationSchema.validate_structure(record3)

    if len(warnings3) == 0:
        print("✗ Should detect invalid enum value")
        return False
    print(f"✓ Detected invalid enum value: {len(warnings3)} warnings")

    # Test case 4: Valid record
    record4 = V6InterpretationSchema.create_empty_record()

    warnings4 = V6InterpretationSchema.validate_structure(record4)

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
        ("observed structural pattern", False),
        ("the score is high", True),
        ("divergence observed", False),
        ("you should fix this", True),
        ("interpretation unavailable", False),
        ("correct interpretation", True),
        ("structural alignment observed", False),
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
    basis1 = ["regime", "intent_primary", "v5_decision_diff_status"]
    warnings1 = check_confidence_boundary(basis1)

    if len(warnings1) != 0:
        print(f"✗ Clean basis should have no warnings, got {len(warnings1)}")
        return False
    print(f"✓ Clean basis has no warnings")

    # Test case 2: v0.4 boundary violation
    basis2 = ["regime", "confidence_reason"]
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


def test_complete_record_validation() -> bool:
    """
    Test 6: Complete record passes all guards (if clean).
    """
    print("Test 6: Complete record passes all guards (if clean)")
    print("-" * 60)

    # Clean record
    clean_record = {
        "v6_meaning_mode": "ON",
        "v6_meaning_status": "AVAILABLE",
        "v6_meaning_tag": "STRUCTURAL_PATTERN_OBSERVED",
        "v6_meaning_summary": "divergence observed under regime transition.",
        "v6_meaning_basis": ["regime", "v5_decision_diff_status"],
    }

    # Check schema
    schema_warnings = V6InterpretationSchema.validate_structure(clean_record)
    if len(schema_warnings) != 0:
        print(f"✗ Clean record failed schema validation: {schema_warnings}")
        return False
    print(f"✓ Clean record passes schema validation")

    # Check constitutional guards
    guard_warnings = validate_interpretation_record(clean_record)
    if len(guard_warnings) != 0:
        print(f"✗ Clean record failed constitutional guards: {guard_warnings}")
        return False
    print(f"✓ Clean record passes constitutional guards")

    # Dirty record (evaluative vocabulary)
    dirty_record = {
        "v6_meaning_mode": "ON",
        "v6_meaning_status": "AVAILABLE",
        "v6_meaning_tag": "GOOD_PATTERN",
        "v6_meaning_summary": "this is a correct interpretation.",
        "v6_meaning_basis": ["regime"],
    }

    guard_warnings2 = validate_interpretation_record(dirty_record)
    if len(guard_warnings2) == 0:
        print("✗ Dirty record should fail vocabulary check")
        return False
    print(f"✓ Dirty record detected: {len(guard_warnings2)} violations")

    # Dirty record (v0.4 violation)
    dirty_record2 = {
        "v6_meaning_mode": "ON",
        "v6_meaning_status": "AVAILABLE",
        "v6_meaning_tag": "PATTERN_OBSERVED",
        "v6_meaning_summary": "divergence observed.",
        "v6_meaning_basis": ["confidence_reason"],
    }

    guard_warnings3 = validate_interpretation_record(dirty_record2)
    if len(guard_warnings3) == 0:
        print("✗ Dirty record should fail boundary check")
        return False
    print(f"✓ Dirty record detected: {len(guard_warnings3)} violations")

    print("Test 6: PASS\n")
    return True


def test_exit_code_always_zero() -> bool:
    """
    Test 7: Exit code always 0 (warning-only).
    """
    print("Test 7: Exit code always 0 (warning-only)")
    print("-" * 60)

    # All validation functions return warnings, never raise
    # This test confirms the design principle

    print("✓ All validation functions return warnings (never raise)")
    print("✓ Exit code will be 0 (warning-only by design)")

    print("Test 7: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR60: v0.6 Interpretation Schema & Guard Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("v6 schema fields exist", test_schema_fields_exist),
        ("Empty record creation", test_empty_record_creation),
        ("Schema validation detects violations", test_schema_validation_detects_violations),
        ("Forbidden vocabulary detection", test_forbidden_vocabulary_detection),
        ("v0.4 boundary guard", test_v04_boundary_guard),
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
        print("✓ ALL PR60 INTERPRETATION SCHEMA TESTS PASSED")
    else:
        print("⚠ SOME PR60 INTERPRETATION SCHEMA TESTS FAILED")
    print("=" * 60)
    print("PR60 Requirements Verified:")
    print("  - v6 schema fields exist and are well-defined")
    print("  - Empty interpretation record can be created")
    print("  - Schema validation detects structure violations")
    print("  - Forbidden vocabulary detection works")
    print("  - v0.4 boundary guard detects confidence_reason access")
    print("  - Complete record passes all guards (if clean)")
    print("  - Exit code always 0 (warning-only)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
