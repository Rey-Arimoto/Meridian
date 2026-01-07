#!/usr/bin/env python3
"""
PR5 Validation: Safety Overlay Invariants

Purpose: Verify that SafetyOverlay enforces suppression-only safety rules.

Requirements:
- Cooldown prevents weight changes during cooldown period
- MaxDelta limits per-step changes
- Min Threshold ignores small changes
- Fail-Closed returns 0.0 on error/unknown
- Emergency Freeze always returns 0.0
- Exit 0 on PASS, 1 on FAIL
"""

import sys
import os
from datetime import datetime, timedelta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.safety_overlay import SafetyOverlay
from core.meridian_policy_core import MeridianPolicyCore
from core.regime_matrix import Regime


def test_cooldown_enforcement():
    """Validate that cooldown prevents weight changes during cooldown period"""
    print("\nTest 1: Cooldown enforcement")
    print("-" * 60)

    # Create overlay with 60-second cooldown
    overlay = SafetyOverlay(
        enabled=True,
        cooldown_seconds=60,
        max_dw_per_step=1.0,  # Set high so cooldown is the constraint
        min_dw_ignore=0.001,  # Set low so threshold doesn't interfere
    )

    core = MeridianPolicyCore()
    start_time = datetime.utcnow()

    checks_passed = 0
    checks_total = 0

    # First decision: should allow change (no cooldown yet)
    decision1 = core.decide(entropy_bp=4000, current_weight=0.0)
    result1 = overlay.apply(decision1, current_weight=0.0, now_utc=start_time, emergency_freeze=False)

    checks_total += 1
    if result1.final_target_weight == decision1.target_weight:
        print(f"✓ First change allowed: 0.0 → {result1.final_target_weight}")
        checks_passed += 1
    else:
        print(f"✗ FAIL: First change blocked unexpectedly")

    # Second decision 30 seconds later (within cooldown): should be blocked
    time_30s_later = start_time + timedelta(seconds=30)
    decision2 = core.decide(entropy_bp=1000, current_weight=result1.final_target_weight)
    result2 = overlay.apply(decision2, current_weight=result1.final_target_weight, now_utc=time_30s_later, emergency_freeze=False)

    checks_total += 1
    if result2.final_target_weight == result1.final_target_weight:
        print(f"✓ Cooldown enforced: weight unchanged at {result2.final_target_weight} (30s < 60s cooldown)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Cooldown not enforced, weight changed to {result2.final_target_weight}")

    checks_total += 1
    if "COOLDOWN_HOLD" in result2.overlay_rule:
        print(f"✓ Overlay rule indicates cooldown: {result2.overlay_rule}")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Overlay rule doesn't indicate cooldown: {result2.overlay_rule}")

    # Third decision 70 seconds later (after cooldown): should be allowed
    time_70s_later = start_time + timedelta(seconds=70)
    decision3 = core.decide(entropy_bp=7500, current_weight=result1.final_target_weight)
    result3 = overlay.apply(decision3, current_weight=result1.final_target_weight, now_utc=time_70s_later, emergency_freeze=False)

    checks_total += 1
    if result3.final_target_weight == decision3.target_weight:
        print(f"✓ After cooldown: change allowed {result1.final_target_weight} → {result3.final_target_weight}")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Change blocked after cooldown expired")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 1: {status} ({checks_passed}/{checks_total})")
    return passed


def test_max_delta_clamping():
    """Validate that MaxDelta clamps large per-step changes"""
    print("\nTest 2: Max Delta clamping")
    print("-" * 60)

    # Create overlay with max delta = 0.05 (5%)
    overlay = SafetyOverlay(
        enabled=True,
        cooldown_seconds=0,  # Disable cooldown
        max_dw_per_step=0.05,
        min_dw_ignore=0.001,
    )

    core = MeridianPolicyCore()
    now = datetime.utcnow()

    checks_passed = 0
    checks_total = 0

    # Try to change from 0.0 to 0.3 (delta = 0.3, exceeds max 0.05)
    decision = core.decide(entropy_bp=4000, current_weight=0.0)  # target_weight = 0.3
    result = overlay.apply(decision, current_weight=0.0, now_utc=now, emergency_freeze=False)

    checks_total += 1
    if result.final_target_weight == 0.05:
        print(f"✓ Large change clamped: target 0.3 → final 0.05 (max delta)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Expected 0.05, got {result.final_target_weight}")

    checks_total += 1
    if "MAX_DELTA_CLAMP" in result.overlay_rule:
        print(f"✓ Overlay rule indicates clamping: {result.overlay_rule}")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Overlay rule doesn't indicate clamping: {result.overlay_rule}")

    # Try to change from 0.3 to 0.0 (delta = -0.3, exceeds max 0.05)
    overlay.reset()  # Reset state for fresh test
    decision2 = core.decide(entropy_bp=9500, current_weight=0.3)  # target_weight = 0.0
    result2 = overlay.apply(decision2, current_weight=0.3, now_utc=now, emergency_freeze=False)

    checks_total += 1
    if result2.final_target_weight == 0.25:  # 0.3 - 0.05
        print(f"✓ Large decrease clamped: 0.3 → 0.25 (max delta in negative direction)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Expected 0.25, got {result2.final_target_weight}")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 2: {status} ({checks_passed}/{checks_total})")
    return passed


def test_min_threshold_hold():
    """Validate that small changes below MIN_DW_IGNORE are ignored"""
    print("\nTest 3: Min threshold (ignore small changes)")
    print("-" * 60)

    # Create overlay with min ignore = 0.02 (2%)
    overlay = SafetyOverlay(
        enabled=True,
        cooldown_seconds=0,
        max_dw_per_step=1.0,
        min_dw_ignore=0.02,
    )

    now = datetime.utcnow()

    checks_passed = 0
    checks_total = 0

    # Try to change from 0.0 to 0.01 (delta = 0.01, below min 0.02)
    # We'll manually create a result since we need specific target_weight
    from core.meridian_policy_core import PolicyDecision
    from core.regime_matrix import Regime, BaseAction, RegimeClassification

    # Mock decision with small target
    mock_classification = RegimeClassification(
        regime=Regime.STABLE_RANGE,
        reason="test",
        entropy_bp=1000,
        confidence="high"
    )
    small_decision = PolicyDecision(
        regime=Regime.STABLE_RANGE,
        base_action=BaseAction.ACT,
        target_weight=0.01,  # Small change
        reason="test small change",
        regime_classification=mock_classification
    )

    result = overlay.apply(small_decision, current_weight=0.0, now_utc=now, emergency_freeze=False)

    checks_total += 1
    if result.final_target_weight == 0.0:  # Should stay at current
        print(f"✓ Small change ignored: target 0.01 ignored, staying at 0.0 (below 0.02 threshold)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Expected 0.0, got {result.final_target_weight}")

    checks_total += 1
    if "MIN_THRESHOLD_HOLD" in result.overlay_rule:
        print(f"✓ Overlay rule indicates threshold hold: {result.overlay_rule}")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Overlay rule doesn't indicate threshold: {result.overlay_rule}")

    # Change from 0.3 to 0.29 (delta = -0.01, below min 0.02)
    overlay.reset()
    small_decrease = PolicyDecision(
        regime=Regime.EMERGING_TREND,
        base_action=BaseAction.GUARD,
        target_weight=0.29,
        reason="test small decrease",
        regime_classification=mock_classification
    )

    result2 = overlay.apply(small_decrease, current_weight=0.3, now_utc=now, emergency_freeze=False)

    checks_total += 1
    if result2.final_target_weight == 0.3:
        print(f"✓ Small decrease ignored: 0.3 → 0.29 ignored, staying at 0.3")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Expected 0.3, got {result2.final_target_weight}")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 3: {status} ({checks_passed}/{checks_total})")
    return passed


def test_fail_closed_unknown():
    """Validate that UNKNOWN regime and missing decision fail-closed to 0.0"""
    print("\nTest 4: Fail-closed (unknown/error)")
    print("-" * 60)

    overlay = SafetyOverlay(enabled=True, cooldown_seconds=0, max_dw_per_step=1.0, min_dw_ignore=0.001)
    now = datetime.utcnow()

    checks_passed = 0
    checks_total = 0

    # Test 1: Missing decision (None)
    result1 = overlay.apply(decision=None, current_weight=0.5, now_utc=now, emergency_freeze=False)

    checks_total += 1
    if result1.final_target_weight == 0.0:
        print(f"✓ Missing decision → 0.0 (fail-closed)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Missing decision, expected 0.0, got {result1.final_target_weight}")

    checks_total += 1
    if "FAIL_CLOSED_NO_DECISION" in result1.overlay_rule:
        print(f"✓ Overlay rule indicates fail-closed: {result1.overlay_rule}")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Overlay rule doesn't indicate fail-closed: {result1.overlay_rule}")

    # Test 2: UNKNOWN regime
    from core.meridian_policy_core import PolicyDecision
    from core.regime_matrix import Regime, BaseAction, RegimeClassification

    unknown_classification = RegimeClassification(
        regime=Regime.UNKNOWN,
        reason="test unknown",
        entropy_bp=5000,
        confidence="low"
    )
    unknown_decision = PolicyDecision(
        regime=Regime.UNKNOWN,
        base_action=BaseAction.PAUSE,
        target_weight=0.0,
        reason="unknown regime test",
        regime_classification=unknown_classification
    )

    result2 = overlay.apply(unknown_decision, current_weight=0.5, now_utc=now, emergency_freeze=False)

    checks_total += 1
    if result2.final_target_weight == 0.0:
        print(f"✓ UNKNOWN regime → 0.0 (fail-closed)")
        checks_passed += 1
    else:
        print(f"✗ FAIL: UNKNOWN regime, expected 0.0, got {result2.final_target_weight}")

    checks_total += 1
    if "FAIL_CLOSED_UNKNOWN_REGIME" in result2.overlay_rule:
        print(f"✓ Overlay rule indicates unknown regime: {result2.overlay_rule}")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Overlay rule doesn't indicate unknown: {result2.overlay_rule}")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 4: {status} ({checks_passed}/{checks_total})")
    return passed


def test_emergency_freeze_respect():
    """Validate that Emergency Freeze always returns 0.0"""
    print("\nTest 5: Emergency Freeze respect")
    print("-" * 60)

    overlay = SafetyOverlay(enabled=True, cooldown_seconds=0, max_dw_per_step=1.0, min_dw_ignore=0.001)
    core = MeridianPolicyCore()
    now = datetime.utcnow()

    checks_passed = 0
    checks_total = 0

    # Even with a valid decision, emergency_freeze should force 0.0
    decision = core.decide(entropy_bp=4000, current_weight=0.5)

    result = overlay.apply(decision, current_weight=0.5, now_utc=now, emergency_freeze=True)

    checks_total += 1
    if result.final_target_weight == 0.0:
        print(f"✓ Emergency freeze enforced: 0.0 regardless of decision")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Emergency freeze, expected 0.0, got {result.final_target_weight}")

    checks_total += 1
    if "EMERGENCY_FREEZE" in result.overlay_rule:
        print(f"✓ Overlay rule indicates emergency freeze: {result.overlay_rule}")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Overlay rule doesn't indicate emergency: {result.overlay_rule}")

    # Even with no decision and emergency freeze
    result2 = overlay.apply(None, current_weight=0.5, now_utc=now, emergency_freeze=True)

    checks_total += 1
    if result2.final_target_weight == 0.0:
        print(f"✓ Emergency freeze (no decision) → 0.0")
        checks_passed += 1
    else:
        print(f"✗ FAIL: Emergency freeze (no decision), expected 0.0, got {result2.final_target_weight}")

    passed = (checks_passed == checks_total)
    status = "PASS" if passed else "FAIL"
    print(f"\nTest 5: {status} ({checks_passed}/{checks_total})")
    return passed


def main():
    """Run all PR5 safety overlay validations"""
    print("=" * 60)
    print("PR5: Safety Overlay Invariants Validation")
    print("=" * 60)

    results = []

    # Run all tests
    results.append(("Cooldown enforcement", test_cooldown_enforcement()))
    results.append(("Max Delta clamping", test_max_delta_clamping()))
    results.append(("Min threshold hold", test_min_threshold_hold()))
    results.append(("Fail-closed unknown/error", test_fail_closed_unknown()))
    results.append(("Emergency Freeze respect", test_emergency_freeze_respect()))

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
        print("✓ ALL SAFETY OVERLAY INVARIANT TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME SAFETY OVERLAY INVARIANT TESTS FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
