#!/usr/bin/env python3
"""
PR151: v1.4 Rebalance Template Guidance v1 - Smoke Test (READ-ONLY)

Purpose:
    Validate rebalance template guidance engine with 14 test cases covering:
    - Import works
    - Empty/minimal bundle
    - Guard rules (FREEZE, STRESSED)
    - Shock phase rules (DOWN_SHOCK, DOWN_REVERSAL, UP_SHOCK, UP_REVERSAL)
    - NORMAL + trend rules (UP_TREND, DOWN_TREND, RANGE)
    - Missing trend handling
    - Constitutional guards (token names, numeric ratios)
    - Defensive error handling

Test Coverage:
    1. Import works
    2. Minimal bundle (empty) → TPL_UNKNOWN + warnings
    3. Guard: action_shape=FREEZE_STATE → TPL_RISK_0
    4. Guard: stress=STRESSED → TPL_RISK_0
    5. DOWN_SHOCK → TPL_RISK_0
    6. DOWN_REVERSAL → TPL_RISK_50
    7. UP_SHOCK → TPL_RISK_90
    8. UP_REVERSAL → TPL_RISK_0
    9. NORMAL + UP_TREND → TPL_RISK_90
    10. NORMAL + DOWN_TREND → TPL_RISK_20
    11. NORMAL + RANGE → TPL_RISK_50
    12. NORMAL + trend missing → TPL_UNKNOWN (safe)
    13. Constitutional guard catches token literal (inject "wBTC") → warning
    14. Defensive invalid bundle → ERROR record validates

Expected: 14/14 tests passed
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rebalance import (
    build_rebalance_template_guidance_v1,
    V14RebalanceTemplateSchema,
    TPL_UNKNOWN,
    TPL_RISK_0,
    TPL_RISK_20,
    TPL_RISK_50,
    TPL_RISK_90,
    RULE_GUARD_FREEZE,
    RULE_GUARD_STRESSED,
    RULE_DOWN_SHOCK,
    RULE_DOWN_REVERSAL,
    RULE_UP_SHOCK,
    RULE_UP_REVERSAL,
    RULE_NORMAL_UP_TREND,
    RULE_NORMAL_DOWN_TREND,
    RULE_NORMAL_RANGE,
    RULE_FALLBACK_UNKNOWN,
    TREND_UP_TREND,
    TREND_DOWN_TREND,
    TREND_RANGE,
    TREND_UNKNOWN,
    check_token_names,
    check_numeric_ratios_in_text,
    REBALANCE_STATUS_AVAILABLE,
    REBALANCE_STATUS_ERROR,
)


def test_1_import_works():
    """Test 1: Import works"""
    assert TPL_UNKNOWN is not None
    assert TPL_RISK_0 is not None
    assert build_rebalance_template_guidance_v1 is not None
    print("✓ Test 1 passed: Import works")


def test_2_minimal_bundle_unknown():
    """Test 2: Minimal bundle (empty) → AVAILABLE + TPL_UNKNOWN + warnings"""
    bundle = {"artifacts": {}}
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_status"] == REBALANCE_STATUS_AVAILABLE, \
        f"Expected AVAILABLE, got {rebalance_record['v14_rebalance_status']}"
    assert rebalance_record["v14_rebalance_template_id"] == TPL_UNKNOWN, \
        f"Expected TPL_UNKNOWN, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_FALLBACK_UNKNOWN, \
        f"Expected RULE_FALLBACK_UNKNOWN, got {rebalance_record['v14_rebalance_rule_id']}"
    assert len(result["warnings"]) > 0, "Expected warnings for missing inputs"

    print("✓ Test 2 passed: Minimal bundle → TPL_UNKNOWN + warnings")


def test_3_guard_freeze_state():
    """Test 3: Guard: action_shape=FREEZE_STATE → TPL_RISK_0"""
    bundle = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_NORMAL"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "FREEZE_STATE"},
            "trend_record": {"v14_trend_label": "UP_TREND"},
        }
    }
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_template_id"] == TPL_RISK_0, \
        f"Expected TPL_RISK_0, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_GUARD_FREEZE, \
        f"Expected RULE_GUARD_FREEZE, got {rebalance_record['v14_rebalance_rule_id']}"

    print("✓ Test 3 passed: FREEZE_STATE → TPL_RISK_0 (guard)")


def test_4_guard_stressed():
    """Test 4: Guard: stress=STRESSED → TPL_RISK_0"""
    bundle = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_NORMAL"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_STRESSED"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            "trend_record": {"v14_trend_label": "UP_TREND"},
        }
    }
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_template_id"] == TPL_RISK_0, \
        f"Expected TPL_RISK_0, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_GUARD_STRESSED, \
        f"Expected RULE_GUARD_STRESSED, got {rebalance_record['v14_rebalance_rule_id']}"

    print("✓ Test 4 passed: STRESSED → TPL_RISK_0 (guard)")


def test_5_down_shock():
    """Test 5: DOWN_SHOCK → TPL_RISK_0"""
    bundle = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_DOWN_SHOCK"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            "trend_record": {"v14_trend_label": "UNKNOWN"},
        }
    }
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_template_id"] == TPL_RISK_0, \
        f"Expected TPL_RISK_0, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_DOWN_SHOCK, \
        f"Expected RULE_DOWN_SHOCK, got {rebalance_record['v14_rebalance_rule_id']}"

    print("✓ Test 5 passed: DOWN_SHOCK → TPL_RISK_0")


def test_6_down_reversal():
    """Test 6: DOWN_REVERSAL → TPL_RISK_50"""
    bundle = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_DOWN_REVERSAL"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            "trend_record": {"v14_trend_label": "UNKNOWN"},
        }
    }
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_template_id"] == TPL_RISK_50, \
        f"Expected TPL_RISK_50, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_DOWN_REVERSAL, \
        f"Expected RULE_DOWN_REVERSAL, got {rebalance_record['v14_rebalance_rule_id']}"

    print("✓ Test 6 passed: DOWN_REVERSAL → TPL_RISK_50")


def test_7_up_shock():
    """Test 7: UP_SHOCK → TPL_RISK_90"""
    bundle = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_UP_SHOCK"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            "trend_record": {"v14_trend_label": "UNKNOWN"},
        }
    }
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_template_id"] == TPL_RISK_90, \
        f"Expected TPL_RISK_90, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_UP_SHOCK, \
        f"Expected RULE_UP_SHOCK, got {rebalance_record['v14_rebalance_rule_id']}"

    print("✓ Test 7 passed: UP_SHOCK → TPL_RISK_90")


def test_8_up_reversal():
    """Test 8: UP_REVERSAL → TPL_RISK_0"""
    bundle = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_UP_REVERSAL"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            "trend_record": {"v14_trend_label": "UNKNOWN"},
        }
    }
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_template_id"] == TPL_RISK_0, \
        f"Expected TPL_RISK_0, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_UP_REVERSAL, \
        f"Expected RULE_UP_REVERSAL, got {rebalance_record['v14_rebalance_rule_id']}"

    print("✓ Test 8 passed: UP_REVERSAL → TPL_RISK_0")


def test_9_normal_up_trend():
    """Test 9: NORMAL + UP_TREND → TPL_RISK_90"""
    bundle = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_NORMAL"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            "trend_record": {"v14_trend_label": "UP_TREND"},
        }
    }
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_template_id"] == TPL_RISK_90, \
        f"Expected TPL_RISK_90, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_NORMAL_UP_TREND, \
        f"Expected RULE_NORMAL_UP_TREND, got {rebalance_record['v14_rebalance_rule_id']}"

    print("✓ Test 9 passed: NORMAL + UP_TREND → TPL_RISK_90")


def test_10_normal_down_trend():
    """Test 10: NORMAL + DOWN_TREND → TPL_RISK_20"""
    bundle = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_NORMAL"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            "trend_record": {"v14_trend_label": "DOWN_TREND"},
        }
    }
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_template_id"] == TPL_RISK_20, \
        f"Expected TPL_RISK_20, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_NORMAL_DOWN_TREND, \
        f"Expected RULE_NORMAL_DOWN_TREND, got {rebalance_record['v14_rebalance_rule_id']}"

    print("✓ Test 10 passed: NORMAL + DOWN_TREND → TPL_RISK_20")


def test_11_normal_range():
    """Test 11: NORMAL + RANGE → TPL_RISK_50"""
    bundle = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_NORMAL"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            "trend_record": {"v14_trend_label": "RANGE"},
        }
    }
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_template_id"] == TPL_RISK_50, \
        f"Expected TPL_RISK_50, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_NORMAL_RANGE, \
        f"Expected RULE_NORMAL_RANGE, got {rebalance_record['v14_rebalance_rule_id']}"

    print("✓ Test 11 passed: NORMAL + RANGE → TPL_RISK_50")


def test_12_normal_trend_missing():
    """Test 12: NORMAL + trend missing → TPL_UNKNOWN (safe)"""
    bundle = {
        "artifacts": {
            "shock_phase_record": {"v14_shock_phase_label": "PHASE_NORMAL"},
            "stress_escalation_record": {"v14_escalation_output_stress_label": "STRESS_CALM"},
            "action_shape_record": {"v14_action_shape_label": "NORMAL_STATE"},
            # trend_record missing
        }
    }
    result = build_rebalance_template_guidance_v1(bundle)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_template_id"] == TPL_UNKNOWN, \
        f"Expected TPL_UNKNOWN, got {rebalance_record['v14_rebalance_template_id']}"
    assert rebalance_record["v14_rebalance_rule_id"] == RULE_FALLBACK_UNKNOWN, \
        f"Expected RULE_FALLBACK_UNKNOWN, got {rebalance_record['v14_rebalance_rule_id']}"
    assert any("missing trend_record" in w for w in result["warnings"]), \
        "Expected warning for missing trend_record"

    print("✓ Test 12 passed: NORMAL + trend missing → TPL_UNKNOWN (safe)")


def test_13_constitutional_guard_token_literal():
    """Test 13: Constitutional guard catches token literal (inject \"wBTC\") → warning"""
    # Test guard function directly
    dirty_text = "Rebalance to wBTC 90%."
    token_warnings = check_token_names(dirty_text)
    ratio_warnings = check_numeric_ratios_in_text(dirty_text, "free_text")

    assert len(token_warnings) > 0, "Expected warning for token name 'wBTC'"
    assert len(ratio_warnings) > 0, "Expected warning for numeric ratio '90%'"

    print("✓ Test 13 passed: Constitutional guard catches token literal + ratio")


def test_14_defensive_invalid_bundle():
    """Test 14: Defensive invalid bundle → ERROR record validates"""
    # Pass invalid bundle (None)
    result = build_rebalance_template_guidance_v1(None)
    rebalance_record = result["rebalance_record"]

    assert rebalance_record["v14_rebalance_status"] == REBALANCE_STATUS_ERROR, \
        f"Expected ERROR, got {rebalance_record['v14_rebalance_status']}"

    # Validate ERROR record
    is_valid, validation_warnings = V14RebalanceTemplateSchema.validate_rebalance_record(rebalance_record)
    assert is_valid, f"ERROR record should validate. Warnings: {validation_warnings}"

    print("✓ Test 14 passed: Invalid bundle → ERROR record validates")


def run_all_tests():
    """Run all 14 smoke tests"""
    print("=" * 60)
    print("PR151: v1.4 Rebalance Template Guidance v1 - Smoke Test")
    print("=" * 60)
    print()

    tests = [
        test_1_import_works,
        test_2_minimal_bundle_unknown,
        test_3_guard_freeze_state,
        test_4_guard_stressed,
        test_5_down_shock,
        test_6_down_reversal,
        test_7_up_shock,
        test_8_up_reversal,
        test_9_normal_up_trend,
        test_10_normal_down_trend,
        test_11_normal_range,
        test_12_normal_trend_missing,
        test_13_constitutional_guard_token_literal,
        test_14_defensive_invalid_bundle,
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
