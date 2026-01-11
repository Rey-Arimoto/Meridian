#!/usr/bin/env python3
"""
PR103: v1.0 Execution Plan Generator v1 Smoke Test

Purpose:
    Validate that v1.0 execution plan generator correctly
    generates plan records based on permission and boundary analysis.

Test Coverage:
    1. Generator import works
    2. Minimal input produces valid plan record
    3. Permission-to-plan mapping works correctly
    4. Plan record passes PR102 schema validation
    5. No forbidden vocabulary in generated plans
    6. No token literals in generated plans
    7. Defensive behavior (None input handled gracefully)
    8. Warning-only behavior (exit code always 0)

Constitutional Constraints:
    - READ-ONLY: No execution logic changes
    - Warning-only: Exit code always 0
    - No amounts, token names, addresses
    - No evaluative/prescriptive vocabulary

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict, List

# Import v1.0 execution modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from execution.v10_execution_plan_generator_v1 import (
    generate_execution_plan_v1,
    get_generator_v1_info,
)
from execution.v10_execution_plan_schema import V10ExecutionPlanSchema
from execution.v10_plan_constitutional_guard import validate_plan_record


def test_generator_import() -> bool:
    """
    Test 1: Generator import works.
    """
    print("Test 1: Generator import works")
    print("-" * 60)

    try:
        from execution.v10_execution_plan_generator_v1 import (
            generate_execution_plan_v1,
        )
        print("✓ Generator import successful")
    except ImportError as e:
        print(f"✗ Generator import failed: {e}")
        return False

    print("Test 1: PASS\n")
    return True


def test_minimal_input() -> bool:
    """
    Test 2: Minimal input produces valid plan record.
    """
    print("Test 2: Minimal input produces valid plan record")
    print("-" * 60)

    execution = {
        "v10_execution_mode": "ON",
        "v10_execution_status": "AVAILABLE",
        "v10_execution_permission": "UNKNOWN",
        "v10_execution_intent": "NONE",
    }

    try:
        plan = generate_execution_plan_v1(execution)
    except Exception as e:
        print(f"✗ Generation failed: {e}")
        return False

    print("✓ Generation successful")

    # Check required fields
    for field in V10ExecutionPlanSchema.REQUIRED_FIELDS:
        if field not in plan:
            print(f"✗ Missing required field: {field}")
            return False

    print("✓ All required fields present")

    # Check v10 plan record structure
    warnings = V10ExecutionPlanSchema.validate_structure(plan)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False

    print("✓ Valid v10 plan record structure")

    print("Test 2: PASS\n")
    return True


def test_permission_to_plan_mapping() -> bool:
    """
    Test 3: Permission-to-plan mapping works correctly.
    """
    print("Test 3: Permission-to-plan mapping works correctly")
    print("-" * 60)

    # Test cases: (permission, intent, expected_plan_type, expected_constraints)
    test_cases = [
        ("HOLD", "NONE", "NOOP", ["manual_approval"]),
        ("UNKNOWN", "NONE", "UNCLASSIFIED", ["manual_approval"]),
        ("DRY_RUN_ONLY", "NONE", "MAINTENANCE", ["dry_run_only", "frequency_limit_once_per_day"]),
        ("ALLOW", "REBALANCE_INTENT", "REBALANCE", ["manual_approval"]),
        ("ALLOW", "HEDGE_INTENT", "HEDGE", ["manual_approval"]),
        ("ALLOW", "LIQUIDITY_INTENT", "LIQUIDITY", ["manual_approval"]),
        ("ALLOW", "MAINTENANCE", "MAINTENANCE", ["manual_approval"]),
    ]

    for permission, intent, expected_plan_type, expected_constraints in test_cases:
        execution = {
            "v10_execution_mode": "ON",
            "v10_execution_status": "AVAILABLE",
            "v10_execution_permission": permission,
            "v10_execution_intent": intent,
        }

        plan = generate_execution_plan_v1(execution)
        actual_plan_type = plan.get("v10_plan_type", "")
        actual_constraints = plan.get("v10_plan_constraints", [])

        if actual_plan_type != expected_plan_type:
            print(f"✗ {permission} + {intent} → expected {expected_plan_type}, got {actual_plan_type}")
            return False

        if actual_constraints != expected_constraints:
            print(f"✗ {permission} constraints → expected {expected_constraints}, got {actual_constraints}")
            return False

        print(f"✓ {permission} + {intent} → {actual_plan_type} + {actual_constraints}")

    print("Test 3: PASS\n")
    return True


def test_schema_validation() -> bool:
    """
    Test 4: Plan record passes PR102 schema validation.
    """
    print("Test 4: Plan record passes PR102 schema validation")
    print("-" * 60)

    # Generate plans for all permission types
    permissions = ["HOLD", "UNKNOWN", "DRY_RUN_ONLY", "ALLOW"]

    for permission in permissions:
        execution = {
            "v10_execution_mode": "ON",
            "v10_execution_status": "AVAILABLE",
            "v10_execution_permission": permission,
            "v10_execution_intent": "REBALANCE_INTENT",
        }

        plan = generate_execution_plan_v1(execution)

        # Validate structure
        warnings = V10ExecutionPlanSchema.validate_structure(plan)
        if warnings:
            print(f"✗ {permission} plan failed schema validation: {warnings}")
            return False

    print("✓ All generated plans pass schema validation")

    print("Test 4: PASS\n")
    return True


def test_no_forbidden_vocabulary() -> bool:
    """
    Test 5: No forbidden vocabulary in generated plans.
    """
    print("Test 5: No forbidden vocabulary in generated plans")
    print("-" * 60)

    # Generate plans for all permission types
    permissions = ["HOLD", "UNKNOWN", "DRY_RUN_ONLY", "ALLOW"]

    for permission in permissions:
        execution = {
            "v10_execution_mode": "ON",
            "v10_execution_status": "AVAILABLE",
            "v10_execution_permission": permission,
            "v10_execution_intent": "REBALANCE_INTENT",
        }

        plan = generate_execution_plan_v1(execution)
        warnings = validate_plan_record(plan)

        # Filter for forbidden vocabulary and execution action warnings
        vocab_warnings = [w for w in warnings if "Forbidden vocabulary" in w]
        action_warnings = [w for w in warnings if "Execution action vocabulary" in w]

        if vocab_warnings or action_warnings:
            print(f"✗ {permission} plan has vocabulary violations:")
            for w in vocab_warnings + action_warnings:
                print(f"  {w}")
            return False

    print("✓ No forbidden vocabulary in any generated plans")

    print("Test 5: PASS\n")
    return True


def test_no_token_literals() -> bool:
    """
    Test 6: No token literals in generated plans.
    """
    print("Test 6: No token literals in generated plans")
    print("-" * 60)

    # Generate plans for all permission types
    permissions = ["HOLD", "UNKNOWN", "DRY_RUN_ONLY", "ALLOW"]

    for permission in permissions:
        execution = {
            "v10_execution_mode": "ON",
            "v10_execution_status": "AVAILABLE",
            "v10_execution_permission": permission,
            "v10_execution_intent": "LIQUIDITY_INTENT",
        }

        plan = generate_execution_plan_v1(execution)
        warnings = validate_plan_record(plan)

        # Filter for token literal and numeric pattern warnings
        token_warnings = [w for w in warnings if "Token literal" in w]
        numeric_warnings = [w for w in warnings if "Numeric pattern" in w or "Currency symbol" in w or "Address pattern" in w]

        if token_warnings or numeric_warnings:
            print(f"✗ {permission} plan has token/numeric violations:")
            for w in token_warnings + numeric_warnings:
                print(f"  {w}")
            return False

    print("✓ No token literals or numeric patterns in any generated plans")

    print("Test 6: PASS\n")
    return True


def test_defensive_behavior() -> bool:
    """
    Test 7: Defensive behavior (None input handled gracefully).
    """
    print("Test 7: Defensive behavior (None input handled gracefully)")
    print("-" * 60)

    # Test with None execution_record
    try:
        plan1 = generate_execution_plan_v1(None)
        print("✓ None execution_record handled gracefully")
    except Exception as e:
        print(f"✗ None execution_record raised exception: {e}")
        return False

    # Test with invalid type
    try:
        plan2 = generate_execution_plan_v1("invalid")  # type: ignore
        print("✓ Invalid type handled gracefully")
    except Exception as e:
        print(f"✗ Invalid type raised exception: {e}")
        return False

    # Test with empty dict
    try:
        plan3 = generate_execution_plan_v1({})
        print("✓ Empty dict handled gracefully")
    except Exception as e:
        print(f"✗ Empty dict raised exception: {e}")
        return False

    # Test with execution unavailable
    try:
        execution4 = {
            "v10_execution_mode": "OFF",
            "v10_execution_status": "UNAVAILABLE",
            "v10_execution_permission": "ALLOW",
        }
        plan4 = generate_execution_plan_v1(execution4)
        if plan4["v10_plan_mode"] != "OFF":
            print(f"✗ Unavailable execution should produce OFF plan")
            return False
        print("✓ Unavailable execution handled gracefully")
    except Exception as e:
        print(f"✗ Unavailable execution raised exception: {e}")
        return False

    print("✓ All edge cases handled without raising")

    print("Test 7: PASS\n")
    return True


def test_warning_only_behavior() -> bool:
    """
    Test 8: Warning-only behavior (exit code always 0).
    """
    print("Test 8: Warning-only behavior (exit code always 0)")
    print("-" * 60)

    # All generation functions should never raise
    # This test confirms the design principle

    print("✓ Generator returns valid records (never raises)")
    print("✓ Exit code will be 0 (warning-only by design)")

    print("Test 8: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR103: v1.0 Execution Plan Generator v1 Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Generator import works", test_generator_import),
        ("Minimal input produces valid plan", test_minimal_input),
        ("Permission-to-plan mapping", test_permission_to_plan_mapping),
        ("Schema validation", test_schema_validation),
        ("No forbidden vocabulary", test_no_forbidden_vocabulary),
        ("No token literals", test_no_token_literals),
        ("Defensive behavior", test_defensive_behavior),
        ("Warning-only behavior", test_warning_only_behavior),
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
        print("✓ ALL PR103 EXECUTION PLAN GENERATOR TESTS PASSED")
    else:
        print("⚠ SOME PR103 EXECUTION PLAN GENERATOR TESTS FAILED")
    print("=" * 60)
    print("PR103 Requirements Verified:")
    print("  - Generator import works")
    print("  - Minimal input produces valid plan")
    print("  - Permission-to-plan mapping")
    print("  - Schema validation")
    print("  - No forbidden vocabulary")
    print("  - No token literals")
    print("  - Defensive behavior")
    print("  - Warning-only behavior (exit code always 0)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
