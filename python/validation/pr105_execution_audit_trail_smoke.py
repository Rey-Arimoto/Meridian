#!/usr/bin/env python3
"""
PR105: v1.0 Execution Audit Trail v1 Smoke Test

Purpose:
    Validate that v1.0 execution audit trail correctly
    builds causal chain from artifact records.

Test Coverage:
    1. Engine import works
    2. Empty input produces UNAVAILABLE audit trail
    3. Single layer produces valid audit trail
    4. Multiple layers produce ordered chain
    5. Chain maintains fixed layer order
    6. No token literals in generated audit trails
    7. No numeric patterns in generated audit trails
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

# Import v1.0 audit modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from audit.v10_execution_audit_trail_engine_v1 import (
    build_execution_audit_trail_v1,
    get_audit_trail_engine_v1_info,
)
from audit.v10_execution_audit_trail_schema import V10ExecutionAuditTrailSchema
from audit.v10_audit_constitutional_guard import validate_v10_audit_trail_record


def test_engine_import() -> bool:
    """
    Test 1: Engine import works.
    """
    print("Test 1: Engine import works")
    print("-" * 60)

    try:
        from audit.v10_execution_audit_trail_engine_v1 import (
            build_execution_audit_trail_v1,
        )
        print("✓ Engine import successful")
    except ImportError as e:
        print(f"✗ Engine import failed: {e}")
        return False

    print("Test 1: PASS\n")
    return True


def test_empty_input_produces_unavailable() -> bool:
    """
    Test 2: Empty input produces UNAVAILABLE audit trail.
    """
    print("Test 2: Empty input produces UNAVAILABLE audit trail")
    print("-" * 60)

    trail = build_execution_audit_trail_v1()

    if trail["v10_audit_mode"] != "OFF":
        print(f"✗ Expected mode OFF, got {trail['v10_audit_mode']}")
        return False
    print("✓ Audit mode is OFF")

    if trail["v10_audit_status"] != "UNAVAILABLE":
        print(f"✗ Expected status UNAVAILABLE, got {trail['v10_audit_status']}")
        return False
    print("✓ Audit status is UNAVAILABLE")

    if len(trail["v10_audit_chain"]) != 0:
        print(f"✗ Expected empty chain, got {len(trail['v10_audit_chain'])} events")
        return False
    print("✓ Chain is empty")

    print("Test 2: PASS\n")
    return True


def test_single_layer_produces_valid_trail() -> bool:
    """
    Test 3: Single layer produces valid audit trail.
    """
    print("Test 3: Single layer produces valid audit trail")
    print("-" * 60)

    blindspot = {
        "v8_blindspot_tag": "ABSENCE_INSUFFICIENT_EVIDENCE",
        "v8_blindspot_basis": ["meaning_tag_counts"],
    }

    trail = build_execution_audit_trail_v1(blindspot_record=blindspot)

    if trail["v10_audit_mode"] != "ON":
        print(f"✗ Expected mode ON, got {trail['v10_audit_mode']}")
        return False
    print("✓ Audit mode is ON")

    if trail["v10_audit_status"] != "AVAILABLE":
        print(f"✗ Expected status AVAILABLE, got {trail['v10_audit_status']}")
        return False
    print("✓ Audit status is AVAILABLE")

    chain = trail["v10_audit_chain"]
    if len(chain) != 1:
        print(f"✗ Expected 1 chain event, got {len(chain)}")
        return False
    print("✓ Chain has 1 event")

    if chain[0]["layer"] != "BLINDSPOT":
        print(f"✗ Expected layer BLINDSPOT, got {chain[0]['layer']}")
        return False
    print("✓ Layer is BLINDSPOT")

    # Validate structure
    warnings = V10ExecutionAuditTrailSchema.validate_structure(trail)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid audit trail structure")

    print("Test 3: PASS\n")
    return True


def test_multiple_layers_produce_ordered_chain() -> bool:
    """
    Test 4: Multiple layers produce ordered chain.
    """
    print("Test 4: Multiple layers produce ordered chain")
    print("-" * 60)

    blindspot = {"v8_blindspot_tag": "ABSENCE_INSUFFICIENT_EVIDENCE"}
    boundary = {"v9_boundary_type": "DATA_BOUNDARY"}
    permission = {"v10_execution_permission": "HOLD"}

    trail = build_execution_audit_trail_v1(
        blindspot_record=blindspot,
        boundary_record=boundary,
        permission_record=permission,
    )

    chain = trail["v10_audit_chain"]
    if len(chain) != 3:
        print(f"✗ Expected 3 chain events, got {len(chain)}")
        return False
    print(f"✓ Chain has 3 events")

    # Check layer order
    expected_layers = ["BLINDSPOT", "BOUNDARY", "PERMISSION"]
    for i, expected_layer in enumerate(expected_layers):
        if chain[i]["layer"] != expected_layer:
            print(f"✗ Expected layer {expected_layer} at position {i}, got {chain[i]['layer']}")
            return False

    print(f"✓ Chain layers in correct order: {expected_layers}")

    print("Test 4: PASS\n")
    return True


def test_chain_maintains_fixed_order() -> bool:
    """
    Test 5: Chain maintains fixed layer order.
    """
    print("Test 5: Chain maintains fixed layer order")
    print("-" * 60)

    # Test: provide layers in reverse order
    # Engine should still emit them in fixed order
    simulation = {"v10_simulation_type": "PLAN_APPLICABILITY_SCAN"}
    plan = {"v10_plan_type": "MAINTENANCE"}
    permission = {"v10_execution_permission": "DRY_RUN_ONLY"}

    trail = build_execution_audit_trail_v1(
        simulation_record=simulation,
        plan_record=plan,
        permission_record=permission,
    )

    chain = trail["v10_audit_chain"]

    # Expected order (fixed): PERMISSION → PLAN → SIMULATION
    expected_order = ["PERMISSION", "PLAN", "SIMULATION"]
    actual_order = [event["layer"] for event in chain]

    if actual_order != expected_order:
        print(f"✗ Expected order {expected_order}, got {actual_order}")
        return False

    print(f"✓ Chain maintains fixed order: {actual_order}")

    print("Test 5: PASS\n")
    return True


def test_no_token_literals() -> bool:
    """
    Test 6: No token literals in generated audit trails.
    """
    print("Test 6: No token literals in generated audit trails")
    print("-" * 60)

    # Generate audit trails for various layer combinations
    test_cases = [
        {"blindspot_record": {"v8_blindspot_tag": "ABSENCE_INSUFFICIENT_EVIDENCE"}},
        {"boundary_record": {"v9_boundary_type": "DATA_BOUNDARY"}},
        {"permission_record": {"v10_execution_permission": "HOLD"}},
        {"plan_record": {"v10_plan_type": "NOOP"}},
        {"simulation_record": {"v10_simulation_type": "PLAN_APPLICABILITY_SCAN"}},
    ]

    for kwargs in test_cases:
        trail = build_execution_audit_trail_v1(**kwargs)
        warnings = validate_v10_audit_trail_record(trail)

        # Filter for token literal warnings
        token_warnings = [w for w in warnings if "Token literal" in w]

        if token_warnings:
            print(f"✗ {list(kwargs.keys())[0]} has token literal violations:")
            for w in token_warnings:
                print(f"  {w}")
            return False

    print("✓ No token literals in any generated audit trails")

    print("Test 6: PASS\n")
    return True


def test_no_numeric_patterns() -> bool:
    """
    Test 7: No numeric patterns in generated audit trails.
    """
    print("Test 7: No numeric patterns in generated audit trails")
    print("-" * 60)

    # Generate full chain audit trail
    blindspot = {"v8_blindspot_tag": "ABSENCE_INSUFFICIENT_EVIDENCE"}
    boundary = {"v9_boundary_type": "DATA_BOUNDARY"}
    permission = {"v10_execution_permission": "HOLD"}
    plan = {"v10_plan_type": "NOOP"}
    simulation = {"v10_simulation_type": "PLAN_APPLICABILITY_SCAN"}

    trail = build_execution_audit_trail_v1(
        blindspot_record=blindspot,
        boundary_record=boundary,
        permission_record=permission,
        plan_record=plan,
        simulation_record=simulation,
    )

    warnings = validate_v10_audit_trail_record(trail)

    # Filter for numeric pattern warnings
    numeric_warnings = [w for w in warnings if "Numeric pattern" in w or "Currency symbol" in w or "Address pattern" in w]

    if numeric_warnings:
        print(f"✗ Audit trail has numeric pattern violations:")
        for w in numeric_warnings:
            print(f"  {w}")
        return False

    print("✓ No numeric patterns in generated audit trail")

    print("Test 7: PASS\n")
    return True


def test_warning_only_behavior() -> bool:
    """
    Test 8: Warning-only behavior (exit code always 0).
    """
    print("Test 8: Warning-only behavior (exit code always 0)")
    print("-" * 60)

    # Test with None inputs
    try:
        trail1 = build_execution_audit_trail_v1(None, None, None, None, None, None)
        print("✓ None inputs handled gracefully")
    except Exception as e:
        print(f"✗ None inputs raised exception: {e}")
        return False

    # Test with invalid types
    try:
        trail2 = build_execution_audit_trail_v1(
            blindspot_record="invalid",  # type: ignore
        )
        print("✓ Invalid type handled gracefully")
    except Exception as e:
        print(f"✗ Invalid type raised exception: {e}")
        return False

    # Test with empty dicts
    try:
        trail3 = build_execution_audit_trail_v1(
            blindspot_record={},
            boundary_record={},
        )
        print("✓ Empty dicts handled gracefully")
    except Exception as e:
        print(f"✗ Empty dicts raised exception: {e}")
        return False

    print("✓ All edge cases handled without raising")

    print("Test 8: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR105: v1.0 Execution Audit Trail Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Engine import works", test_engine_import),
        ("Empty input produces UNAVAILABLE", test_empty_input_produces_unavailable),
        ("Single layer produces valid trail", test_single_layer_produces_valid_trail),
        ("Multiple layers produce ordered chain", test_multiple_layers_produce_ordered_chain),
        ("Chain maintains fixed order", test_chain_maintains_fixed_order),
        ("No token literals", test_no_token_literals),
        ("No numeric patterns", test_no_numeric_patterns),
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
        print("✓ ALL PR105 EXECUTION AUDIT TRAIL TESTS PASSED")
    else:
        print("⚠ SOME PR105 EXECUTION AUDIT TRAIL TESTS FAILED")
    print("=" * 60)
    print("PR105 Requirements Verified:")
    print("  - Engine import works")
    print("  - Empty input produces UNAVAILABLE")
    print("  - Single layer produces valid trail")
    print("  - Multiple layers produce ordered chain")
    print("  - Chain maintains fixed order")
    print("  - No token literals")
    print("  - No numeric patterns")
    print("  - Warning-only behavior (exit code always 0)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
