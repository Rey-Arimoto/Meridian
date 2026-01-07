#!/usr/bin/env python3
"""
PR4A Validation: Matrix Invariants

Purpose: Prove that the authoritative REGIME_ACTION_MATRIX enforces
         constitutional constraints.

Requirements:
- Every Regime has a mapping
- get_base_action() returns valid BaseAction for all regimes
- Act forbidden: VOLATILE_NOISE → PAUSE, REGIME_TRANSITION → PAUSE
- Fail-closed: UNKNOWN → PAUSE
- Exit 0 on PASS, 1 on FAIL
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.regime_matrix import (
    Regime,
    BaseAction,
    REGIME_ACTION_MATRIX,
    get_base_action,
)


def test_every_regime_mapped():
    """Validate that every Regime has a mapping in REGIME_ACTION_MATRIX"""
    print("\nTest 1: Every Regime has a mapping")
    print("-" * 60)

    all_regimes = list(Regime)
    checks_passed = 0
    checks_total = len(all_regimes)

    for regime in all_regimes:
        if regime in REGIME_ACTION_MATRIX:
            action = REGIME_ACTION_MATRIX[regime]
            print(f"✓ {regime.value:20s} → {action.value}")
            checks_passed += 1
        else:
            print(f"✗ FAIL: {regime.value} NOT IN MATRIX")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 1: {status} ({checks_passed}/{checks_total})")
    return passed


def test_get_base_action_returns_valid():
    """Validate that get_base_action() returns valid BaseAction for all regimes"""
    print("\nTest 2: get_base_action() returns valid BaseAction")
    print("-" * 60)

    all_regimes = list(Regime)
    checks_passed = 0
    checks_total = len(all_regimes)

    for regime in all_regimes:
        try:
            action = get_base_action(regime)
            if isinstance(action, BaseAction):
                print(f"✓ get_base_action({regime.value:20s}) → {action.value}")
                checks_passed += 1
            else:
                print(f"✗ FAIL: get_base_action({regime.value}) returned non-BaseAction: {type(action)}")
        except Exception as e:
            print(f"✗ FAIL: get_base_action({regime.value}) raised exception: {e}")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 2: {status} ({checks_passed}/{checks_total})")
    return passed


def test_act_forbidden_invariants():
    """
    Validate Act Forbidden constitutional constraints:
    - VOLATILE_NOISE must map to PAUSE (Act forbidden)
    - REGIME_TRANSITION must map to PAUSE (Act forbidden)
    """
    print("\nTest 3: Act Forbidden invariants")
    print("-" * 60)

    checks_passed = 0
    checks_total = 0

    # Check 1: VOLATILE_NOISE → PAUSE
    checks_total += 1
    volatile_action = get_base_action(Regime.VOLATILE_NOISE)
    if volatile_action == BaseAction.PAUSE:
        print(f"✓ VOLATILE_NOISE → PAUSE (Act forbidden)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: VOLATILE_NOISE → {volatile_action.value} (MUST be PAUSE)")

    # Check 2: REGIME_TRANSITION → PAUSE
    checks_total += 1
    transition_action = get_base_action(Regime.REGIME_TRANSITION)
    if transition_action == BaseAction.PAUSE:
        print(f"✓ REGIME_TRANSITION → PAUSE (Act forbidden)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: REGIME_TRANSITION → {transition_action.value} (MUST be PAUSE)")

    # Additional check: No regime with entropy-driven chaos should allow ACT
    # This is a forward-looking safety check
    checks_total += 1
    chaos_regimes = [Regime.VOLATILE_NOISE, Regime.REGIME_TRANSITION]
    no_act_in_chaos = all(get_base_action(r) != BaseAction.ACT for r in chaos_regimes)
    if no_act_in_chaos:
        print(f"✓ No ACT action in high-volatility regimes")
        checks_passed += 1
    else:
        print(f"✗ FAIL: ACT found in high-volatility regimes (constitutional violation)")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 3: {status} ({checks_passed}/{checks_total})")
    return passed


def test_fail_closed_invariant():
    """
    Validate Fail-Closed constraint:
    - UNKNOWN regime must map to PAUSE
    """
    print("\nTest 4: Fail-Closed invariant (UNKNOWN → PAUSE)")
    print("-" * 60)

    checks_passed = 0
    checks_total = 1

    unknown_action = get_base_action(Regime.UNKNOWN)
    if unknown_action == BaseAction.PAUSE:
        print(f"✓ UNKNOWN → PAUSE (Fail-closed)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: UNKNOWN → {unknown_action.value} (MUST be PAUSE for fail-closed)")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 4: {status} ({checks_passed}/{checks_total})")
    return passed


def test_matrix_completeness():
    """
    Validate that REGIME_ACTION_MATRIX has exactly the right number of entries.
    No duplicates, no missing regimes.
    """
    print("\nTest 5: Matrix completeness (all regimes, no duplicates)")
    print("-" * 60)

    checks_passed = 0
    checks_total = 0

    # Check 1: Matrix size matches number of regimes
    checks_total += 1
    num_regimes = len(Regime)
    num_mappings = len(REGIME_ACTION_MATRIX)
    if num_mappings == num_regimes:
        print(f"✓ Matrix size {num_mappings} matches Regime count {num_regimes}")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Matrix size {num_mappings} != Regime count {num_regimes}")

    # Check 2: All actions in matrix are valid BaseActions
    checks_total += 1
    all_valid_actions = all(isinstance(action, BaseAction) for action in REGIME_ACTION_MATRIX.values())
    if all_valid_actions:
        print(f"✓ All matrix values are valid BaseActions")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Some matrix values are not BaseActions")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 5: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run all matrix invariant validations"""
    print("=" * 60)
    print("PR4A: Matrix Invariants Validation")
    print("=" * 60)

    results = []

    # Run all tests
    results.append(("Every Regime mapped", test_every_regime_mapped()))
    results.append(("get_base_action() valid", test_get_base_action_returns_valid()))
    results.append(("Act Forbidden invariants", test_act_forbidden_invariants()))
    results.append(("Fail-Closed invariant", test_fail_closed_invariant()))
    results.append(("Matrix completeness", test_matrix_completeness()))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✓ ALL MATRIX INVARIANT TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME MATRIX INVARIANT TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
