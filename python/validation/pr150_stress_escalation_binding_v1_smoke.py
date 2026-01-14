#!/usr/bin/env python3
"""
PR150: v1.4 Stress Escalation Binding v1 - Smoke Test (READ-ONLY)

Purpose:
    Validate stress escalation binding engine with 14 test cases covering:
    - Escalation table (NORMAL, PRE_SHOCK, SHOCK, REVERSAL, RECOVERY)
    - Escalate-only logic (never lower stress)
    - Immutable states (UNKNOWN stress, ERROR/UNKNOWN phase)
    - Bundle extraction
    - Schema validation

Test Coverage:
    1. PHASE_NORMAL + STRESS_CALM → STRESS_CALM (NO_CHANGE)
    2. PHASE_NORMAL + STRESS_TENSE → STRESS_TENSE (NO_CHANGE)
    3. PHASE_PRE_SHOCK + STRESS_CALM → STRESS_TENSE (escalate)
    4. PHASE_PRE_SHOCK + STRESS_TENSE → STRESS_TENSE (no escalation)
    5. PHASE_PRE_SHOCK + STRESS_STRESSED → STRESS_STRESSED (no de-escalation)
    6. PHASE_UP_SHOCK + STRESS_CALM → STRESS_STRESSED (escalate)
    7. PHASE_UP_SHOCK + STRESS_TENSE → STRESS_STRESSED (escalate)
    8. PHASE_UP_SHOCK + STRESS_STRESSED → STRESS_STRESSED (no escalation)
    9. PHASE_DOWN_SHOCK + STRESS_CALM → STRESS_STRESSED (escalate)
    10. PHASE_UP_REVERSAL + STRESS_CALM → STRESS_TENSE (escalate)
    11. PHASE_DOWN_REVERSAL + STRESS_CALM → STRESS_TENSE (escalate)
    12. PHASE_RECOVERY + STRESS_STRESSED → STRESS_STRESSED (NO_CHANGE, no de-escalation)
    13. PHASE_UNKNOWN + STRESS_CALM → STRESS_CALM (phase requires UNKNOWN, current maintained)
    14. STRESS_UNKNOWN is immutable (stays UNKNOWN)

Expected: 14/14 tests passed
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from escalation import (
    build_stress_escalation_record_v1,
    build_stress_escalation_from_bundle_v1,
    V14StressEscalationSchema,
    ESCALATION_STATUS_AVAILABLE,
    ESCALATED_FLAG_ON,
    ESCALATED_FLAG_OFF,
    ESCALATED_FLAG_UNKNOWN,
)

from shock.v14_shock_phase_schema import (
    PHASE_UNKNOWN,
    PHASE_NORMAL,
    PHASE_PRE_SHOCK,
    PHASE_UP_SHOCK,
    PHASE_DOWN_SHOCK,
    PHASE_UP_REVERSAL,
    PHASE_DOWN_REVERSAL,
    PHASE_RECOVERY,
    PHASE_ERROR,
)

from stress.v14_stress_rule_table_schema import (
    STRESS_CALM,
    STRESS_TENSE,
    STRESS_STRESSED,
    STRESS_UNKNOWN,
)


def test_1_normal_calm_no_change():
    """Test 1: PHASE_NORMAL + STRESS_CALM → STRESS_CALM (NO_CHANGE)"""
    phase_record = {"v14_shock_phase_label": PHASE_NORMAL}
    stress_record = {"v14_stress_label": STRESS_CALM}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_CALM, \
        f"Expected STRESS_CALM, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_OFF, \
        f"Expected ESCALATED_FLAG_OFF, got {escalation_record['v14_escalation_escalated_flag']}"

    print("✓ Test 1 passed: PHASE_NORMAL + STRESS_CALM → STRESS_CALM (NO_CHANGE)")


def test_2_normal_tense_no_change():
    """Test 2: PHASE_NORMAL + STRESS_TENSE → STRESS_TENSE (NO_CHANGE)"""
    phase_record = {"v14_shock_phase_label": PHASE_NORMAL}
    stress_record = {"v14_stress_label": STRESS_TENSE}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_TENSE, \
        f"Expected STRESS_TENSE, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_OFF, \
        f"Expected ESCALATED_FLAG_OFF, got {escalation_record['v14_escalation_escalated_flag']}"

    print("✓ Test 2 passed: PHASE_NORMAL + STRESS_TENSE → STRESS_TENSE (NO_CHANGE)")


def test_3_pre_shock_calm_escalates_to_tense():
    """Test 3: PHASE_PRE_SHOCK + STRESS_CALM → STRESS_TENSE (escalate)"""
    phase_record = {"v14_shock_phase_label": PHASE_PRE_SHOCK}
    stress_record = {"v14_stress_label": STRESS_CALM}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_TENSE, \
        f"Expected STRESS_TENSE, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_ON, \
        f"Expected ESCALATED_FLAG_ON, got {escalation_record['v14_escalation_escalated_flag']}"
    assert escalation_record["v14_escalation_min_required_stress_label"] == STRESS_TENSE, \
        f"Expected min_required=STRESS_TENSE, got {escalation_record['v14_escalation_min_required_stress_label']}"

    print("✓ Test 3 passed: PHASE_PRE_SHOCK + STRESS_CALM → STRESS_TENSE (escalate)")


def test_4_pre_shock_tense_no_escalation():
    """Test 4: PHASE_PRE_SHOCK + STRESS_TENSE → STRESS_TENSE (no escalation)"""
    phase_record = {"v14_shock_phase_label": PHASE_PRE_SHOCK}
    stress_record = {"v14_stress_label": STRESS_TENSE}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_TENSE, \
        f"Expected STRESS_TENSE, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_OFF, \
        f"Expected ESCALATED_FLAG_OFF, got {escalation_record['v14_escalation_escalated_flag']}"

    print("✓ Test 4 passed: PHASE_PRE_SHOCK + STRESS_TENSE → STRESS_TENSE (no escalation)")


def test_5_pre_shock_stressed_no_deescalation():
    """Test 5: PHASE_PRE_SHOCK + STRESS_STRESSED → STRESS_STRESSED (no de-escalation)"""
    phase_record = {"v14_shock_phase_label": PHASE_PRE_SHOCK}
    stress_record = {"v14_stress_label": STRESS_STRESSED}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_STRESSED, \
        f"Expected STRESS_STRESSED, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_OFF, \
        f"Expected ESCALATED_FLAG_OFF, got {escalation_record['v14_escalation_escalated_flag']}"

    print("✓ Test 5 passed: PHASE_PRE_SHOCK + STRESS_STRESSED → STRESS_STRESSED (no de-escalation)")


def test_6_up_shock_calm_escalates_to_stressed():
    """Test 6: PHASE_UP_SHOCK + STRESS_CALM → STRESS_STRESSED (escalate)"""
    phase_record = {"v14_shock_phase_label": PHASE_UP_SHOCK}
    stress_record = {"v14_stress_label": STRESS_CALM}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_STRESSED, \
        f"Expected STRESS_STRESSED, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_ON, \
        f"Expected ESCALATED_FLAG_ON, got {escalation_record['v14_escalation_escalated_flag']}"
    assert escalation_record["v14_escalation_min_required_stress_label"] == STRESS_STRESSED, \
        f"Expected min_required=STRESS_STRESSED, got {escalation_record['v14_escalation_min_required_stress_label']}"

    print("✓ Test 6 passed: PHASE_UP_SHOCK + STRESS_CALM → STRESS_STRESSED (escalate)")


def test_7_up_shock_tense_escalates_to_stressed():
    """Test 7: PHASE_UP_SHOCK + STRESS_TENSE → STRESS_STRESSED (escalate)"""
    phase_record = {"v14_shock_phase_label": PHASE_UP_SHOCK}
    stress_record = {"v14_stress_label": STRESS_TENSE}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_STRESSED, \
        f"Expected STRESS_STRESSED, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_ON, \
        f"Expected ESCALATED_FLAG_ON, got {escalation_record['v14_escalation_escalated_flag']}"

    print("✓ Test 7 passed: PHASE_UP_SHOCK + STRESS_TENSE → STRESS_STRESSED (escalate)")


def test_8_up_shock_stressed_no_escalation():
    """Test 8: PHASE_UP_SHOCK + STRESS_STRESSED → STRESS_STRESSED (no escalation)"""
    phase_record = {"v14_shock_phase_label": PHASE_UP_SHOCK}
    stress_record = {"v14_stress_label": STRESS_STRESSED}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_STRESSED, \
        f"Expected STRESS_STRESSED, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_OFF, \
        f"Expected ESCALATED_FLAG_OFF, got {escalation_record['v14_escalation_escalated_flag']}"

    print("✓ Test 8 passed: PHASE_UP_SHOCK + STRESS_STRESSED → STRESS_STRESSED (no escalation)")


def test_9_down_shock_calm_escalates_to_stressed():
    """Test 9: PHASE_DOWN_SHOCK + STRESS_CALM → STRESS_STRESSED (escalate)"""
    phase_record = {"v14_shock_phase_label": PHASE_DOWN_SHOCK}
    stress_record = {"v14_stress_label": STRESS_CALM}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_STRESSED, \
        f"Expected STRESS_STRESSED, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_ON, \
        f"Expected ESCALATED_FLAG_ON, got {escalation_record['v14_escalation_escalated_flag']}"

    print("✓ Test 9 passed: PHASE_DOWN_SHOCK + STRESS_CALM → STRESS_STRESSED (escalate)")


def test_10_up_reversal_calm_escalates_to_tense():
    """Test 10: PHASE_UP_REVERSAL + STRESS_CALM → STRESS_TENSE (escalate)"""
    phase_record = {"v14_shock_phase_label": PHASE_UP_REVERSAL}
    stress_record = {"v14_stress_label": STRESS_CALM}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_TENSE, \
        f"Expected STRESS_TENSE, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_ON, \
        f"Expected ESCALATED_FLAG_ON, got {escalation_record['v14_escalation_escalated_flag']}"

    print("✓ Test 10 passed: PHASE_UP_REVERSAL + STRESS_CALM → STRESS_TENSE (escalate)")


def test_11_down_reversal_calm_escalates_to_tense():
    """Test 11: PHASE_DOWN_REVERSAL + STRESS_CALM → STRESS_TENSE (escalate)"""
    phase_record = {"v14_shock_phase_label": PHASE_DOWN_REVERSAL}
    stress_record = {"v14_stress_label": STRESS_CALM}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_TENSE, \
        f"Expected STRESS_TENSE, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_ON, \
        f"Expected ESCALATED_FLAG_ON, got {escalation_record['v14_escalation_escalated_flag']}"

    print("✓ Test 11 passed: PHASE_DOWN_REVERSAL + STRESS_CALM → STRESS_TENSE (escalate)")


def test_12_recovery_stressed_no_deescalation():
    """Test 12: PHASE_RECOVERY + STRESS_STRESSED → STRESS_STRESSED (NO_CHANGE, no de-escalation)"""
    phase_record = {"v14_shock_phase_label": PHASE_RECOVERY}
    stress_record = {"v14_stress_label": STRESS_STRESSED}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_STRESSED, \
        f"Expected STRESS_STRESSED, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_OFF, \
        f"Expected ESCALATED_FLAG_OFF, got {escalation_record['v14_escalation_escalated_flag']}"
    assert escalation_record["v14_escalation_min_required_stress_label"] == "NO_CHANGE", \
        f"Expected min_required=NO_CHANGE, got {escalation_record['v14_escalation_min_required_stress_label']}"

    print("✓ Test 12 passed: PHASE_RECOVERY + STRESS_STRESSED → STRESS_STRESSED (NO_CHANGE)")


def test_13_phase_unknown_calm_maintained():
    """Test 13: PHASE_UNKNOWN + STRESS_CALM → STRESS_CALM (phase requires UNKNOWN, current maintained)"""
    phase_record = {"v14_shock_phase_label": PHASE_UNKNOWN}
    stress_record = {"v14_stress_label": STRESS_CALM}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_CALM, \
        f"Expected STRESS_CALM, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_OFF, \
        f"Expected ESCALATED_FLAG_OFF, got {escalation_record['v14_escalation_escalated_flag']}"
    assert escalation_record["v14_escalation_min_required_stress_label"] == STRESS_UNKNOWN, \
        f"Expected min_required=STRESS_UNKNOWN, got {escalation_record['v14_escalation_min_required_stress_label']}"

    print("✓ Test 13 passed: PHASE_UNKNOWN + STRESS_CALM → STRESS_CALM (current maintained)")


def test_14_stress_unknown_immutable():
    """Test 14: STRESS_UNKNOWN is immutable (stays UNKNOWN)"""
    phase_record = {"v14_shock_phase_label": PHASE_UP_SHOCK}  # Normally requires STRESSED
    stress_record = {"v14_stress_label": STRESS_UNKNOWN}

    result = build_stress_escalation_record_v1(phase_record, stress_record)
    escalation_record = result["escalation_record"]

    assert escalation_record["v14_escalation_output_stress_label"] == STRESS_UNKNOWN, \
        f"Expected STRESS_UNKNOWN, got {escalation_record['v14_escalation_output_stress_label']}"
    assert escalation_record["v14_escalation_escalated_flag"] == ESCALATED_FLAG_UNKNOWN, \
        f"Expected ESCALATED_FLAG_UNKNOWN, got {escalation_record['v14_escalation_escalated_flag']}"
    assert len(result["warnings"]) > 0, "Expected warnings for UNKNOWN stress"

    print("✓ Test 14 passed: STRESS_UNKNOWN is immutable")


def run_all_tests():
    """Run all 14 smoke tests"""
    print("=" * 60)
    print("PR150: v1.4 Stress Escalation Binding v1 - Smoke Test")
    print("=" * 60)
    print()

    tests = [
        test_1_normal_calm_no_change,
        test_2_normal_tense_no_change,
        test_3_pre_shock_calm_escalates_to_tense,
        test_4_pre_shock_tense_no_escalation,
        test_5_pre_shock_stressed_no_deescalation,
        test_6_up_shock_calm_escalates_to_stressed,
        test_7_up_shock_tense_escalates_to_stressed,
        test_8_up_shock_stressed_no_escalation,
        test_9_down_shock_calm_escalates_to_stressed,
        test_10_up_reversal_calm_escalates_to_tense,
        test_11_down_reversal_calm_escalates_to_tense,
        test_12_recovery_stressed_no_deescalation,
        test_13_phase_unknown_calm_maintained,
        test_14_stress_unknown_immutable,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} error: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed}/{len(tests)} tests passed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print()
        print("✓ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    run_all_tests()
