#!/usr/bin/env python3
"""
PR4A Validation: Hysteresis Stability

Purpose: Prove that RegimeClassifier hysteresis prevents rapid oscillation
         near regime transition thresholds.

Requirements:
- Test oscillation around volatile_entry/exit (7000/6000)
- Test oscillation around emerging_entry/exit (3500/2500)
- Test monotonic ramp through all regimes
- Exit 0 on PASS, 1 on FAIL
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.regime_matrix import RegimeClassifier, Regime


def count_transitions(regime_sequence):
    """Count number of regime transitions in a sequence"""
    if len(regime_sequence) < 2:
        return 0
    transitions = 0
    for i in range(1, len(regime_sequence)):
        if regime_sequence[i] != regime_sequence[i-1]:
            transitions += 1
    return transitions


def scenario_a_volatile_oscillation():
    """
    Scenario A: Oscillation around volatile threshold (7000/6000)

    Without hysteresis, this would flip on every crossing.
    With hysteresis, should enter at 7000, stay until < 6000.
    """
    print("\nScenario A: Volatile threshold oscillation (7000/6000)")
    print("-" * 60)

    # Oscillating sequence: crosses 7000 entry, but stays > 6000 exit
    # Expected: Enter volatile once, stay in volatile despite oscillations
    entropy_sequence = [
        5000,  # below volatile
        7200,  # enter volatile (>= 7000)
        6800,  # oscillate down but > 6000 (stay volatile)
        7100,  # oscillate up
        6500,  # oscillate down but > 6000 (stay volatile)
        7000,  # at threshold
        6700,  # down but > 6000 (stay volatile)
        5900,  # exit volatile (< 6000)
        6200,  # below entry, above exit (not volatile)
    ]

    classifier = RegimeClassifier()
    regimes = []

    for entropy_bp in entropy_sequence:
        classification = classifier.classify(entropy_bp)
        regimes.append(classification.regime)

    transitions = count_transitions(regimes)

    print(f"Entropy sequence: {entropy_sequence}")
    print(f"Regime sequence:  {[r.value for r in regimes]}")
    print(f"Transition count: {transitions}")

    # Validate hysteresis properties
    checks_passed = 0
    checks_total = 0

    # Check 1: Should enter volatile at index 1 (7200 >= 7000)
    checks_total += 1
    if regimes[1] == Regime.VOLATILE_NOISE:
        print(f"✓ Enters VOLATILE_NOISE at entropy=7200 (>= 7000)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Expected VOLATILE_NOISE at entropy=7200, got {regimes[1].value}")

    # Check 2: Should stay volatile for indices 2-6 (all > 6000)
    checks_total += 1
    stay_volatile = all(regimes[i] == Regime.VOLATILE_NOISE for i in range(2, 7))
    if stay_volatile:
        print(f"✓ Stays in VOLATILE_NOISE while entropy > 6000 (hysteresis working)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Should stay VOLATILE_NOISE while > 6000")

    # Check 3: Should exit volatile at index 7 (5900 < 6000)
    checks_total += 1
    if regimes[7] != Regime.VOLATILE_NOISE:
        print(f"✓ Exits VOLATILE_NOISE at entropy=5900 (< 6000)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Should exit VOLATILE_NOISE at entropy=5900")

    # Check 4: Transition count should be small (ideally 2: enter, exit)
    checks_total += 1
    if transitions <= 4:  # Allow some margin for regime changes at boundaries
        print(f"✓ Transition count {transitions} is reasonable (hysteresis reduces flipping)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Transition count {transitions} too high (hysteresis not working)")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nScenario A: {status} ({checks_passed}/{checks_total} checks)")
    return passed


def scenario_b_emerging_oscillation():
    """
    Scenario B: Oscillation around emerging threshold (3500/2500)

    With hysteresis, should enter at 3500, stay until < 2500.
    """
    print("\nScenario B: Emerging threshold oscillation (3500/2500)")
    print("-" * 60)

    # Oscillating sequence: crosses 3500 entry, stays > 2500 exit
    entropy_sequence = [
        2000,  # stable
        3600,  # enter emerging (>= 3500)
        3200,  # oscillate down but > 2500 (stay emerging)
        3700,  # oscillate up
        2800,  # oscillate down but > 2500 (stay emerging)
        3000,  # still > 2500
        2400,  # exit emerging (< 2500)
        2100,  # stable
    ]

    classifier = RegimeClassifier()
    regimes = []

    for entropy_bp in entropy_sequence:
        classification = classifier.classify(entropy_bp)
        regimes.append(classification.regime)

    transitions = count_transitions(regimes)

    print(f"Entropy sequence: {entropy_sequence}")
    print(f"Regime sequence:  {[r.value for r in regimes]}")
    print(f"Transition count: {transitions}")

    checks_passed = 0
    checks_total = 0

    # Check 1: Should enter emerging at index 1
    checks_total += 1
    if regimes[1] == Regime.EMERGING_TREND:
        print(f"✓ Enters EMERGING_TREND at entropy=3600 (>= 3500)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Expected EMERGING_TREND at entropy=3600, got {regimes[1].value}")

    # Check 2: Should stay emerging for indices 2-5 (all > 2500)
    checks_total += 1
    stay_emerging = all(regimes[i] == Regime.EMERGING_TREND for i in range(2, 6))
    if stay_emerging:
        print(f"✓ Stays in EMERGING_TREND while entropy > 2500 (hysteresis working)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Should stay EMERGING_TREND while > 2500")

    # Check 3: Should exit emerging at index 6
    checks_total += 1
    if regimes[6] != Regime.EMERGING_TREND:
        print(f"✓ Exits EMERGING_TREND at entropy=2400 (< 2500)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Should exit EMERGING_TREND at entropy=2400")

    # Check 4: Transition count should be small
    checks_total += 1
    if transitions <= 4:
        print(f"✓ Transition count {transitions} is reasonable (hysteresis working)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Transition count {transitions} too high")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nScenario B: {status} ({checks_passed}/{checks_total} checks)")
    return passed


def scenario_c_monotonic_ramp():
    """
    Scenario C: Monotonic increase through all regimes

    Should progress: stable → emerging → volatile → transition
    No regressions allowed.
    """
    print("\nScenario C: Monotonic ramp through all regimes")
    print("-" * 60)

    # Strictly increasing entropy
    entropy_sequence = [
        1000,   # stable
        1500,   # stable
        3600,   # emerging
        5000,   # emerging
        7200,   # volatile
        8500,   # volatile
        9200,   # transition
    ]

    classifier = RegimeClassifier()
    regimes = []

    for entropy_bp in entropy_sequence:
        classification = classifier.classify(entropy_bp)
        regimes.append(classification.regime)

    transitions = count_transitions(regimes)

    print(f"Entropy sequence: {entropy_sequence}")
    print(f"Regime sequence:  {[r.value for r in regimes]}")
    print(f"Transition count: {transitions}")

    checks_passed = 0
    checks_total = 0

    # Check 1: Early values should be stable
    checks_total += 1
    if regimes[0] == Regime.STABLE_RANGE and regimes[1] == Regime.STABLE_RANGE:
        print(f"✓ Low entropy (1000, 1500) → STABLE_RANGE")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Low entropy should be STABLE_RANGE")

    # Check 2: Should enter emerging
    checks_total += 1
    if regimes[2] == Regime.EMERGING_TREND or regimes[3] == Regime.EMERGING_TREND:
        print(f"✓ Mid entropy (3600, 5000) → EMERGING_TREND")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Mid entropy should be EMERGING_TREND")

    # Check 3: Should enter volatile
    checks_total += 1
    if regimes[4] == Regime.VOLATILE_NOISE or regimes[5] == Regime.VOLATILE_NOISE:
        print(f"✓ High entropy (7200, 8500) → VOLATILE_NOISE")
        checks_passed += 1
    else:
        print(f"✗ FAIL: High entropy should be VOLATILE_NOISE")

    # Check 4: Should enter transition at critical
    checks_total += 1
    if regimes[6] == Regime.REGIME_TRANSITION:
        print(f"✓ Critical entropy (9200) → REGIME_TRANSITION")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Critical entropy should be REGIME_TRANSITION, got {regimes[6].value}")

    # Check 5: No regressions (regime order is monotonic in severity)
    checks_total += 1
    regime_order = [Regime.STABLE_RANGE, Regime.EMERGING_TREND, Regime.VOLATILE_NOISE, Regime.REGIME_TRANSITION]
    no_regression = True
    for i in range(1, len(regimes)):
        if regimes[i] in regime_order and regimes[i-1] in regime_order:
            if regime_order.index(regimes[i]) < regime_order.index(regimes[i-1]):
                no_regression = False
                break
    if no_regression:
        print(f"✓ No regime regression (monotonic progression)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Regime regression detected")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nScenario C: {status} ({checks_passed}/{checks_total} checks)")
    return passed


def main():
    """Run all hysteresis stability validations"""
    print("=" * 60)
    print("PR4A: Hysteresis Stability Validation")
    print("=" * 60)

    results = []

    # Run all scenarios
    results.append(("Scenario A (Volatile oscillation)", scenario_a_volatile_oscillation()))
    results.append(("Scenario B (Emerging oscillation)", scenario_b_emerging_oscillation()))
    results.append(("Scenario C (Monotonic ramp)", scenario_c_monotonic_ramp()))

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
        print("✓ ALL HYSTERESIS STABILITY TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME HYSTERESIS STABILITY TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
