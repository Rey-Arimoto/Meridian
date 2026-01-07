#!/usr/bin/env python3
"""
PR4A Validation: Policy Decision Invariants

Purpose: Prove that MeridianPolicyCore.decide() implements regime-first
         decision making and returns complete PolicyDecision objects.

Requirements:
- decide() returns PolicyDecision with all 5 fields populated
- Regime-first consistency: decision.regime == decision.regime_classification.regime
- Base action derived from matrix: decision.base_action == get_base_action(decision.regime)
- PR2 mapping validation for representative entropy values
- Exit 0 on PASS, 1 on FAIL
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.meridian_policy_core import MeridianPolicyCore, PolicyDecision
from core.regime_matrix import Regime, BaseAction, get_base_action


def test_policy_decision_structure():
    """Validate that decide() returns PolicyDecision with all required fields"""
    print("\nTest 1: PolicyDecision structure completeness")
    print("-" * 60)

    core = MeridianPolicyCore()
    decision = core.decide(entropy_bp=4000, current_weight=0.0)

    checks_passed = 0
    checks_total = 0

    # Check 1: Returns PolicyDecision instance
    checks_total += 1
    if isinstance(decision, PolicyDecision):
        print(f"✓ decide() returns PolicyDecision instance")
        checks_passed += 1
    else:
        print(f"✗ FAIL: decide() returned {type(decision)}, expected PolicyDecision")
        return False

    # Check 2-6: All required fields present and populated
    required_fields = ['regime', 'base_action', 'target_weight', 'reason', 'regime_classification']
    for field in required_fields:
        checks_total += 1
        if hasattr(decision, field):
            value = getattr(decision, field)
            if value is not None:
                print(f"✓ PolicyDecision.{field} is populated")
                checks_passed += 1
            else:
                print(f"✗ FAIL: PolicyDecision.{field} is None")
        else:
            print(f"✗ FAIL: PolicyDecision missing field '{field}'")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 1: {status} ({checks_passed}/{checks_total})")
    return passed


def test_regime_first_consistency():
    """
    Validate regime-first consistency:
    decision.regime must match decision.regime_classification.regime
    """
    print("\nTest 2: Regime-first consistency")
    print("-" * 60)

    core = MeridianPolicyCore()

    # Test multiple entropy values
    test_entropies = [1000, 4000, 7500, 9500]
    checks_passed = 0
    checks_total = len(test_entropies)

    for entropy_bp in test_entropies:
        decision = core.decide(entropy_bp=entropy_bp, current_weight=0.0)

        if decision.regime == decision.regime_classification.regime:
            print(f"✓ entropy={entropy_bp}: regime={decision.regime.value} matches classification")
            checks_passed += 1
        else:
            print(f"✗ FAIL: entropy={entropy_bp}: regime={decision.regime.value} != classification={decision.regime_classification.regime.value}")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 2: {status} ({checks_passed}/{checks_total})")
    return passed


def test_base_action_from_matrix():
    """
    Validate that base_action is derived from the matrix:
    decision.base_action must equal get_base_action(decision.regime)
    """
    print("\nTest 3: BaseAction derived from matrix")
    print("-" * 60)

    core = MeridianPolicyCore()

    # Test multiple entropy values covering different regimes
    test_entropies = [1000, 4000, 7500, 9500]
    checks_passed = 0
    checks_total = len(test_entropies)

    for entropy_bp in test_entropies:
        decision = core.decide(entropy_bp=entropy_bp, current_weight=0.0)
        expected_action = get_base_action(decision.regime)

        if decision.base_action == expected_action:
            print(f"✓ entropy={entropy_bp}: {decision.regime.value} → {decision.base_action.value} (matches matrix)")
            checks_passed += 1
        else:
            print(f"✗ FAIL: entropy={entropy_bp}: {decision.regime.value} → {decision.base_action.value}, expected {expected_action.value}")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 3: {status} ({checks_passed}/{checks_total})")
    return passed


def test_pr2_mapping_expectations():
    """
    Validate PR2 target_weight mapping for representative cases:
    - Stable (1000bp): STABLE_RANGE → ACT → 0.0 (preserve PR0)
    - Emerging (4000bp): EMERGING_TREND → GUARD → 0.3
    - Volatile (7500bp): VOLATILE_NOISE → PAUSE → 0.0 (Act forbidden)
    - Critical (9500bp): REGIME_TRANSITION → PAUSE → 0.0
    """
    print("\nTest 4: PR2 mapping expectations")
    print("-" * 60)

    core = MeridianPolicyCore()

    test_cases = [
        {
            'entropy_bp': 1000,
            'expected_regime': Regime.STABLE_RANGE,
            'expected_base_action': BaseAction.ACT,
            'expected_target_weight': 0.0,
            'description': 'Stable (preserve PR0 fail-closed)',
        },
        {
            'entropy_bp': 4000,
            'expected_regime': Regime.EMERGING_TREND,
            'expected_base_action': BaseAction.GUARD,
            'expected_target_weight': 0.3,
            'description': 'Emerging (reuse existing ladder)',
        },
        {
            'entropy_bp': 7500,
            'expected_regime': Regime.VOLATILE_NOISE,
            'expected_base_action': BaseAction.PAUSE,
            'expected_target_weight': 0.0,
            'description': 'Volatile (Act forbidden)',
        },
        {
            'entropy_bp': 9500,
            'expected_regime': Regime.REGIME_TRANSITION,
            'expected_base_action': BaseAction.PAUSE,
            'expected_target_weight': 0.0,
            'description': 'Critical (constitutional freeze)',
        },
    ]

    checks_passed = 0
    checks_total = len(test_cases) * 3  # 3 checks per test case

    for tc in test_cases:
        print(f"\n  Case: entropy={tc['entropy_bp']} ({tc['description']})")

        decision = core.decide(entropy_bp=tc['entropy_bp'], current_weight=0.0)

        # Check regime
        if decision.regime == tc['expected_regime']:
            print(f"    ✓ regime={decision.regime.value}")
            checks_passed += 1
        else:
            print(f"    ✗ regime={decision.regime.value}, expected {tc['expected_regime'].value}")

        # Check base_action
        if decision.base_action == tc['expected_base_action']:
            print(f"    ✓ base_action={decision.base_action.value}")
            checks_passed += 1
        else:
            print(f"    ✗ base_action={decision.base_action.value}, expected {tc['expected_base_action'].value}")

        # Check target_weight
        if decision.target_weight == tc['expected_target_weight']:
            print(f"    ✓ target_weight={decision.target_weight}")
            checks_passed += 1
        else:
            print(f"    ✗ target_weight={decision.target_weight}, expected {tc['expected_target_weight']}")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 4: {status} ({checks_passed}/{checks_total})")
    return passed


def test_reason_field_populated():
    """
    Validate that the reason field contains meaningful information
    """
    print("\nTest 5: Reason field populated with meaningful content")
    print("-" * 60)

    core = MeridianPolicyCore()

    test_entropies = [1000, 4000, 7500, 9500]
    checks_passed = 0
    checks_total = len(test_entropies)

    for entropy_bp in test_entropies:
        decision = core.decide(entropy_bp=entropy_bp, current_weight=0.0)

        # Reason should be non-empty string
        if isinstance(decision.reason, str) and len(decision.reason) > 0:
            # Should mention regime
            if decision.regime.value in decision.reason.lower():
                print(f"✓ entropy={entropy_bp}: reason contains regime info (len={len(decision.reason)})")
                checks_passed += 1
            else:
                print(f"✗ FAIL: entropy={entropy_bp}: reason doesn't mention regime")
        else:
            print(f"✗ FAIL: entropy={entropy_bp}: reason is empty or not a string")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 5: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run all policy decision invariant validations"""
    print("=" * 60)
    print("PR4A: Policy Decision Invariants Validation")
    print("=" * 60)

    results = []

    # Run all tests
    results.append(("PolicyDecision structure", test_policy_decision_structure()))
    results.append(("Regime-first consistency", test_regime_first_consistency()))
    results.append(("BaseAction from matrix", test_base_action_from_matrix()))
    results.append(("PR2 mapping expectations", test_pr2_mapping_expectations()))
    results.append(("Reason field populated", test_reason_field_populated()))

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
        print("✓ ALL POLICY DECISION INVARIANT TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME POLICY DECISION INVARIANT TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
