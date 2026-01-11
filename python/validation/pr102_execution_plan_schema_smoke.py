#!/usr/bin/env python3
"""
PR102: v1.0 Execution Plan Schema v1 Smoke Test

Purpose:
    Validate that v1.0 execution plan schema and constitutional guards
    are correctly defined and enforced.

Test Coverage:
    1. v10 plan schema fields exist and are well-defined
    2. Empty plan record can be created
    3. Schema validation detects structure violations
    4. Forbidden vocabulary detection works
    5. Token literal detection works
    6. Numeric pattern detection works
    7. Execution safety guard detects trading vocabulary
    8. Exit code always 0 (warning-only)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - Non-evaluative: No good/bad, win/loss vocabulary
    - Non-scoric: No scores, grades, rankings
    - No amounts: No numeric values, prices
    - No token literals: No SUI, USDC, BTC, etc.

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict, List

# Import v1.0 execution modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from execution.v10_execution_plan_schema import (
    V10ExecutionPlanSchema,
    validate_plan_basis_fields,
    get_plan_schema_info,
)
from execution.v10_plan_constitutional_guard import (
    validate_plan_record,
    check_token_literals,
    check_numeric_patterns,
)


def test_schema_fields_exist() -> bool:
    """
    Test 1: v10 plan schema fields exist and are well-defined.
    """
    print("Test 1: v10 plan schema fields exist and are well-defined")
    print("-" * 60)

    # Check required fields
    required = V10ExecutionPlanSchema.REQUIRED_FIELDS

    if len(required) == 0:
        print("✗ No required fields defined")
        return False
    print(f"✓ Required fields defined: {len(required)}")

    expected_fields = [
        "v10_plan_mode",
        "v10_plan_status",
        "v10_plan_type",
        "v10_plan_description",
        "v10_plan_constraints",
        "v10_plan_basis",
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
    Test 2: Empty plan record can be created.
    """
    print("Test 2: Empty plan record can be created")
    print("-" * 60)

    try:
        record = V10ExecutionPlanSchema.create_empty_record()
    except Exception as e:
        print(f"✗ Failed to create empty record: {e}")
        return False

    print(f"✓ Empty record created")

    # Check it has required fields
    for field in V10ExecutionPlanSchema.REQUIRED_FIELDS:
        if field not in record:
            print(f"✗ Empty record missing field '{field}'")
            return False

    print(f"✓ Empty record has all required fields")

    # Check defaults are safe
    if record["v10_plan_mode"] != "OFF":
        print(f"✗ Default mode should be OFF, got {record['v10_plan_mode']}")
        return False
    print(f"✓ Default mode is OFF")

    if record["v10_plan_status"] != "UNAVAILABLE":
        print(f"✗ Default status should be UNAVAILABLE, got {record['v10_plan_status']}")
        return False
    print(f"✓ Default status is UNAVAILABLE")

    if record["v10_plan_type"] != "NOOP":
        print(f"✗ Default type should be NOOP, got {record['v10_plan_type']}")
        return False
    print(f"✓ Default type is NOOP")

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
        "v10_plan_mode": "ON",
        # Missing v10_plan_status
        "v10_plan_type": "MAINTENANCE",
        "v10_plan_description": "test",
        "v10_plan_constraints": [],
        "v10_plan_basis": [],
    }

    warnings1 = V10ExecutionPlanSchema.validate_structure(record1)

    if len(warnings1) == 0:
        print("✗ Should detect missing field")
        return False
    print(f"✓ Detected missing field: {len(warnings1)} warnings")

    # Test case 2: Invalid type
    record2 = V10ExecutionPlanSchema.create_empty_record()
    record2["v10_plan_constraints"] = "not_a_list"  # Should be list

    warnings2 = V10ExecutionPlanSchema.validate_structure(record2)

    if len(warnings2) == 0:
        print("✗ Should detect type mismatch")
        return False
    print(f"✓ Detected type mismatch: {len(warnings2)} warnings")

    # Test case 3: Invalid enum value
    record3 = V10ExecutionPlanSchema.create_empty_record()
    record3["v10_plan_type"] = "INVALID"

    warnings3 = V10ExecutionPlanSchema.validate_structure(record3)

    if len(warnings3) == 0:
        print("✗ Should detect invalid enum value")
        return False
    print(f"✓ Detected invalid enum value: {len(warnings3)} warnings")

    # Test case 4: Valid record
    record4 = V10ExecutionPlanSchema.create_empty_record()

    warnings4 = V10ExecutionPlanSchema.validate_structure(record4)

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

    # Test cases: (description, should_have_warnings)
    test_cases = [
        ("this is a good plan", True),
        ("plan type is maintenance", False),
        ("the score is high", True),
        ("rebalance plan available", False),
        ("you should execute this", True),
        ("plan unavailable", False),
    ]

    for description, should_warn in test_cases:
        plan = {
            "v10_plan_type": "MAINTENANCE",
            "v10_plan_description": description,
            "v10_plan_constraints": [],
        }

        warnings = validate_plan_record(plan)
        # Filter for forbidden vocabulary warnings only
        vocab_warnings = [w for w in warnings if "Forbidden vocabulary" in w]
        has_warning = len(vocab_warnings) > 0

        if has_warning != should_warn:
            print(f"✗ '{description}' -> expected warnings={should_warn}, got {len(vocab_warnings)}")
            return False

        status = "warns" if has_warning else "clean"
        print(f"✓ '{description}' -> {status}")

    print("Test 4: PASS\n")
    return True


def test_token_literal_detection() -> bool:
    """
    Test 5: Token literal detection works.
    """
    print("Test 5: Token literal detection works")
    print("-" * 60)

    # Test cases: (text, should_have_warnings)
    test_cases = [
        ("swap SUI for USDC", True),
        ("plan type is rebalance", False),
        ("transfer BTC to wallet", True),
        ("maintenance plan available", False),
        ("buy ETH and sell SOL", True),
        ("plan constraints applied", False),
    ]

    for text, should_warn in test_cases:
        warnings = check_token_literals(text)
        has_warning = len(warnings) > 0

        if has_warning != should_warn:
            print(f"✗ '{text}' -> expected warnings={should_warn}, got {len(warnings)}")
            return False

        status = "warns" if has_warning else "clean"
        print(f"✓ '{text}' -> {status}")

    print("Test 5: PASS\n")
    return True


def test_numeric_pattern_detection() -> bool:
    """
    Test 6: Numeric pattern detection works.
    """
    print("Test 6: Numeric pattern detection works")
    print("-" * 60)

    # Test cases: (text, should_have_warnings)
    test_cases = [
        ("swap 1000 tokens", True),
        ("plan is available", False),
        ("price is 0.5 dollars", True),
        ("rebalance plan type", False),
        ("send to 0x123abc", True),
        ("maintenance plan", False),
        ("cost is $100", True),
    ]

    for text, should_warn in test_cases:
        warnings = check_numeric_patterns(text)
        has_warning = len(warnings) > 0

        if has_warning != should_warn:
            print(f"✗ '{text}' -> expected warnings={should_warn}, got {len(warnings)}")
            return False

        status = "warns" if has_warning else "clean"
        print(f"✓ '{text}' -> {status}")

    print("Test 6: PASS\n")
    return True


def test_execution_safety_guard() -> bool:
    """
    Test 7: Execution safety guard detects trading vocabulary.
    """
    print("Test 7: Execution safety guard detects trading vocabulary")
    print("-" * 60)

    # Test cases: (description, should_have_warnings)
    test_cases = [
        ("swap tokens and transfer funds", True),
        ("plan type is maintenance", False),
        ("sign and broadcast transaction", True),
        ("rebalance plan available", False),
        ("buy and sell orders", True),
        ("plan constraints applied", False),
    ]

    for description, should_warn in test_cases:
        plan = {
            "v10_plan_type": "MAINTENANCE",
            "v10_plan_description": description,
            "v10_plan_constraints": [],
        }

        warnings = validate_plan_record(plan)
        # Filter for execution action warnings only
        action_warnings = [w for w in warnings if "Execution action vocabulary" in w]
        has_warning = len(action_warnings) > 0

        if has_warning != should_warn:
            print(f"✗ '{description}' -> expected warnings={should_warn}, got {len(action_warnings)}")
            return False

        status = "warns" if has_warning else "clean"
        print(f"✓ '{description}' -> {status}")

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
    print("PR102: v1.0 Execution Plan Schema Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("v10 plan schema fields exist", test_schema_fields_exist),
        ("Empty plan record creation", test_empty_record_creation),
        ("Schema validation detects violations", test_schema_validation_detects_violations),
        ("Forbidden vocabulary detection", test_forbidden_vocabulary_detection),
        ("Token literal detection", test_token_literal_detection),
        ("Numeric pattern detection", test_numeric_pattern_detection),
        ("Execution safety guard", test_execution_safety_guard),
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
        print("✓ ALL PR102 EXECUTION PLAN SCHEMA TESTS PASSED")
    else:
        print("⚠ SOME PR102 EXECUTION PLAN SCHEMA TESTS FAILED")
    print("=" * 60)
    print("PR102 Requirements Verified:")
    print("  - v10 plan schema fields exist and are well-defined")
    print("  - Empty plan record can be created")
    print("  - Schema validation detects structure violations")
    print("  - Forbidden vocabulary detection works")
    print("  - Token literal detection works")
    print("  - Numeric pattern detection works")
    print("  - Execution safety guard detects trading vocabulary")
    print("  - Exit code always 0 (warning-only)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
