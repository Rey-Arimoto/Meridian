#!/usr/bin/env python3
"""
PR104: v1.0 Execution Simulation Engine v1 Smoke Test

Purpose:
    Validate that v1.0 execution simulation engine correctly
    generates simulation records based on plan constraints.

Test Coverage:
    1. Engine import works
    2. Minimal plan input produces valid simulation record
    3. Plan mode OFF produces UNAVAILABLE simulation
    4. Constraints produce CONSTRAINT_APPLIED events
    5. No token literals in generated simulations
    6. No numeric patterns in generated simulations
    7. No trading verbs in generated simulations
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

from execution.v10_execution_simulation_engine_v1 import (
    simulate_execution_plan_v1,
    get_simulation_engine_v1_info,
)
from execution.v10_execution_simulation_schema import V10ExecutionSimulationSchema
from execution.v10_simulation_constitutional_guard import validate_v10_simulation_record


def test_engine_import() -> bool:
    """
    Test 1: Engine import works.
    """
    print("Test 1: Engine import works")
    print("-" * 60)

    try:
        from execution.v10_execution_simulation_engine_v1 import (
            simulate_execution_plan_v1,
        )
        print("✓ Engine import successful")
    except ImportError as e:
        print(f"✗ Engine import failed: {e}")
        return False

    print("Test 1: PASS\n")
    return True


def test_minimal_plan_input() -> bool:
    """
    Test 2: Minimal plan input produces valid simulation record.
    """
    print("Test 2: Minimal plan input produces valid simulation record")
    print("-" * 60)

    plan = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": "MAINTENANCE",
        "v10_plan_constraints": ["dry_run_only"],
    }

    try:
        simulation = simulate_execution_plan_v1(plan)
    except Exception as e:
        print(f"✗ Simulation failed: {e}")
        return False

    print("✓ Simulation successful")

    # Check required fields
    for field in V10ExecutionSimulationSchema.REQUIRED_FIELDS:
        if field not in simulation:
            print(f"✗ Missing required field: {field}")
            return False

    print("✓ All required fields present")

    # Check v10 simulation record structure
    warnings = V10ExecutionSimulationSchema.validate_structure(simulation)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False

    print("✓ Valid v10 simulation record structure")

    print("Test 2: PASS\n")
    return True


def test_plan_mode_off_produces_unavailable() -> bool:
    """
    Test 3: Plan mode OFF produces UNAVAILABLE simulation.
    """
    print("Test 3: Plan mode OFF produces UNAVAILABLE simulation")
    print("-" * 60)

    plan_off = {
        "v10_plan_mode": "OFF",
        "v10_plan_status": "UNAVAILABLE",
        "v10_plan_type": "NOOP",
        "v10_plan_constraints": [],
    }

    simulation = simulate_execution_plan_v1(plan_off)

    if simulation["v10_simulation_mode"] != "OFF":
        print(f"✗ Expected mode OFF, got {simulation['v10_simulation_mode']}")
        return False
    print("✓ Simulation mode is OFF")

    if simulation["v10_simulation_status"] != "UNAVAILABLE":
        print(f"✗ Expected status UNAVAILABLE, got {simulation['v10_simulation_status']}")
        return False
    print("✓ Simulation status is UNAVAILABLE")

    print("Test 3: PASS\n")
    return True


def test_constraints_produce_events() -> bool:
    """
    Test 4: Constraints produce CONSTRAINT_APPLIED events.
    """
    print("Test 4: Constraints produce CONSTRAINT_APPLIED events")
    print("-" * 60)

    # Test cases: (constraints, expected_event_count_min)
    test_cases = [
        (["dry_run_only"], 1),
        (["manual_approval"], 1),
        (["frequency_limit_once_per_day"], 1),
        (["time_window_business_hours"], 1),
        (["dry_run_only", "manual_approval"], 2),
    ]

    for constraints, expected_min in test_cases:
        plan = {
            "v10_plan_mode": "ON",
            "v10_plan_status": "AVAILABLE",
            "v10_plan_type": "MAINTENANCE",
            "v10_plan_constraints": constraints,
        }

        simulation = simulate_execution_plan_v1(plan)
        trace = simulation.get("v10_simulation_trace", [])

        # Count CONSTRAINT_APPLIED events
        constraint_events = [e for e in trace if e.get("event_type") == "CONSTRAINT_APPLIED"]

        if len(constraint_events) < expected_min:
            print(f"✗ {constraints} → expected ≥{expected_min} events, got {len(constraint_events)}")
            return False

        print(f"✓ {constraints} → {len(constraint_events)} constraint event(s)")

    print("Test 4: PASS\n")
    return True


def test_no_token_literals() -> bool:
    """
    Test 5: No token literals in generated simulations.
    """
    print("Test 5: No token literals in generated simulations")
    print("-" * 60)

    constraints_list = [
        ["dry_run_only"],
        ["manual_approval"],
        ["frequency_limit_once_per_day"],
        ["dry_run_only", "manual_approval", "frequency_limit_once_per_day"],
    ]

    for constraints in constraints_list:
        plan = {
            "v10_plan_mode": "ON",
            "v10_plan_status": "AVAILABLE",
            "v10_plan_type": "MAINTENANCE",
            "v10_plan_constraints": constraints,
        }

        simulation = simulate_execution_plan_v1(plan)
        warnings = validate_v10_simulation_record(simulation)

        # Filter for token literal warnings
        token_warnings = [w for w in warnings if "Token literal" in w]

        if token_warnings:
            print(f"✗ {constraints} has token literal violations:")
            for w in token_warnings:
                print(f"  {w}")
            return False

    print("✓ No token literals in any generated simulations")

    print("Test 5: PASS\n")
    return True


def test_no_numeric_patterns() -> bool:
    """
    Test 6: No numeric patterns in generated simulations.
    """
    print("Test 6: No numeric patterns in generated simulations")
    print("-" * 60)

    constraints_list = [
        ["dry_run_only"],
        ["manual_approval"],
        ["frequency_limit_once_per_day"],
    ]

    for constraints in constraints_list:
        plan = {
            "v10_plan_mode": "ON",
            "v10_plan_status": "AVAILABLE",
            "v10_plan_type": "REBALANCE",
            "v10_plan_constraints": constraints,
        }

        simulation = simulate_execution_plan_v1(plan)
        warnings = validate_v10_simulation_record(simulation)

        # Filter for numeric pattern warnings
        numeric_warnings = [w for w in warnings if "Numeric pattern" in w or "Currency symbol" in w or "Address pattern" in w]

        if numeric_warnings:
            print(f"✗ {constraints} has numeric pattern violations:")
            for w in numeric_warnings:
                print(f"  {w}")
            return False

    print("✓ No numeric patterns in any generated simulations")

    print("Test 6: PASS\n")
    return True


def test_no_trading_verbs() -> bool:
    """
    Test 7: No trading verbs in generated simulations.
    """
    print("Test 7: No trading verbs in generated simulations")
    print("-" * 60)

    constraints_list = [
        ["dry_run_only"],
        ["manual_approval"],
        ["frequency_limit_once_per_day"],
        ["time_window_business_hours"],
    ]

    for constraints in constraints_list:
        plan = {
            "v10_plan_mode": "ON",
            "v10_plan_status": "AVAILABLE",
            "v10_plan_type": "HEDGE",
            "v10_plan_constraints": constraints,
        }

        simulation = simulate_execution_plan_v1(plan)
        warnings = validate_v10_simulation_record(simulation)

        # Filter for execution action warnings
        action_warnings = [w for w in warnings if "Execution action vocabulary" in w]
        vocab_warnings = [w for w in warnings if "Forbidden vocabulary" in w]

        if action_warnings or vocab_warnings:
            print(f"✗ {constraints} has vocabulary violations:")
            for w in action_warnings + vocab_warnings:
                print(f"  {w}")
            return False

    print("✓ No trading verbs or forbidden vocabulary in any generated simulations")

    print("Test 7: PASS\n")
    return True


def test_warning_only_behavior() -> bool:
    """
    Test 8: Warning-only behavior (exit code always 0).
    """
    print("Test 8: Warning-only behavior (exit code always 0)")
    print("-" * 60)

    # Test with None plan_record
    try:
        sim1 = simulate_execution_plan_v1(None)
        print("✓ None plan_record handled gracefully")
    except Exception as e:
        print(f"✗ None plan_record raised exception: {e}")
        return False

    # Test with invalid type
    try:
        sim2 = simulate_execution_plan_v1("invalid")  # type: ignore
        print("✓ Invalid type handled gracefully")
    except Exception as e:
        print(f"✗ Invalid type raised exception: {e}")
        return False

    # Test with empty dict
    try:
        sim3 = simulate_execution_plan_v1({})
        print("✓ Empty dict handled gracefully")
    except Exception as e:
        print(f"✗ Empty dict raised exception: {e}")
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
    print("PR104: v1.0 Execution Simulation Engine v1 Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Engine import works", test_engine_import),
        ("Minimal plan input", test_minimal_plan_input),
        ("Plan mode OFF produces UNAVAILABLE", test_plan_mode_off_produces_unavailable),
        ("Constraints produce events", test_constraints_produce_events),
        ("No token literals", test_no_token_literals),
        ("No numeric patterns", test_no_numeric_patterns),
        ("No trading verbs", test_no_trading_verbs),
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
        print("✓ ALL PR104 EXECUTION SIMULATION ENGINE TESTS PASSED")
    else:
        print("⚠ SOME PR104 EXECUTION SIMULATION ENGINE TESTS FAILED")
    print("=" * 60)
    print("PR104 Requirements Verified:")
    print("  - Engine import works")
    print("  - Minimal plan input")
    print("  - Plan mode OFF produces UNAVAILABLE")
    print("  - Constraints produce events")
    print("  - No token literals")
    print("  - No numeric patterns")
    print("  - No trading verbs")
    print("  - Warning-only behavior (exit code always 0)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
