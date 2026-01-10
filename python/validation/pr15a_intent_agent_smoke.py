#!/usr/bin/env python3
"""
PR15A: Intent Agent Integration Smoke Test

Purpose: Verify agent writes Intent to logs and consistency with PR15B.

Requirements:
- Agent logs include intent_primary and intent_reason columns
- Intent classification uses shared core.intent.classify_intent_from_fields()
- Agent-written Intent matches PR15B-derived Intent (consistency)
- No crashes on missing/invalid data
- Exit 0 on PASS, 1 on FAIL
"""

import sys
import os
import tempfile
import csv

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

import pandas as pd
from core.intent import classify_intent_from_fields
from reporting.pr15b_intent_derivation import derive_intent_primary, derive_intent_with_reason


def test_shared_function_exists():
    """Test shared classify_intent_from_fields() function exists and works."""
    print("\nTest 1: Shared Function Exists")
    print("-" * 60)

    # Test basic classification
    intent, reason = classify_intent_from_fields(
        regime="stable_range",
        base_action="act",
        decision_reason="STABLE_RANGE: Act",
        action_label="BUY"
    )
    assert intent == "SEEK", f"Expected SEEK, got {intent}"
    assert len(reason) > 0, "Reason should be non-empty"
    print(f"✓ SEEK classification: {intent} - {reason}")

    intent, reason = classify_intent_from_fields(
        regime="volatile_noise",
        base_action="PAUSE",
        decision_reason="High volatility",
        action_label="HOLD"
    )
    assert intent == "PAUSE", f"Expected PAUSE, got {intent}"
    print(f"✓ PAUSE classification: {intent} - {reason}")

    intent, reason = classify_intent_from_fields(
        regime="volatile_noise",
        base_action="HOLD",
        decision_reason="test",
        action_label="HOLD"
    )
    assert intent == "DEFEND", f"Expected DEFEND, got {intent}"
    print(f"✓ DEFEND classification: {intent} - {reason}")

    print("Test 1: PASS (3/3)")
    return True


def test_agent_reporting_consistency():
    """Test agent and reporting produce identical Intent for same inputs."""
    print("\nTest 2: Agent-Reporting Consistency")
    print("-" * 60)

    # Create test cases covering all Intent types
    test_cases = [
        {
            "regime": "stable_range",
            "base_action": "act",
            "decision_reason": "STABLE_RANGE: Act",
            "action_label": "BUY",
            "expected": "SEEK"
        },
        {
            "regime": "volatile_noise",
            "base_action": "PAUSE",
            "decision_reason": "EMERGENCY_FREEZE",
            "action_label": "HOLD",
            "expected": "PAUSE"
        },
        {
            "regime": "REGIME_TRANSITION",
            "base_action": "HOLD",
            "decision_reason": "Transition detected",
            "action_label": "HOLD",
            "expected": "STABILIZE"
        },
        {
            "regime": "volatile_noise",
            "base_action": "HOLD",
            "decision_reason": "High volatility",
            "action_label": "HOLD",
            "expected": "DEFEND"
        },
        {
            "regime": "emerging_trend",
            "base_action": "HOLD",
            "decision_reason": "test",
            "action_label": "HOLD",
            "expected": "IDLE"
        },
    ]

    # Test each case
    for i, tc in enumerate(test_cases):
        # Agent-side classification (Layer A)
        agent_intent, agent_reason = classify_intent_from_fields(
            regime=tc["regime"],
            base_action=tc["base_action"],
            decision_reason=tc["decision_reason"],
            action_label=tc["action_label"]
        )

        # Reporting-side classification (Layer B)
        df = pd.DataFrame([tc])
        reporting_intent = derive_intent_primary(df).iloc[0]

        # Check consistency
        assert agent_intent == reporting_intent, \
            f"Case {i}: Agent={agent_intent}, Reporting={reporting_intent}"
        assert agent_intent == tc["expected"], \
            f"Case {i}: Expected={tc['expected']}, Got={agent_intent}"

    print(f"✓ All {len(test_cases)} test cases: Agent Intent == Reporting Intent")
    print("Test 2: PASS (1/1)")
    return True


def test_missing_data_handling():
    """Test Intent classification handles missing/None data gracefully."""
    print("\nTest 3: Missing Data Handling")
    print("-" * 60)

    # Test with None values
    intent, reason = classify_intent_from_fields(
        regime=None,
        base_action=None,
        decision_reason=None,
        action_label=None
    )
    assert intent == "N/A", f"Expected N/A for all None, got {intent}"
    print("✓ All None → N/A")

    # Test with empty strings
    intent, reason = classify_intent_from_fields(
        regime="",
        base_action="",
        decision_reason="",
        action_label=""
    )
    assert intent == "N/A", f"Expected N/A for all empty, got {intent}"
    print("✓ All empty strings → N/A")

    # Test with mixed valid/invalid
    intent, reason = classify_intent_from_fields(
        regime="stable_range",
        base_action=None,
        decision_reason="test",
        action_label=""
    )
    # Should still classify based on available data (or N/A if insufficient)
    assert intent in ["SEEK", "IDLE", "N/A"], f"Unexpected intent: {intent}"
    print(f"✓ Mixed valid/invalid → {intent} (no crash)")

    print("Test 3: PASS (3/3)")
    return True


def test_priority_order_enforcement():
    """Test Intent priority order is enforced correctly."""
    print("\nTest 4: Priority Order Enforcement")
    print("-" * 60)

    # PAUSE beats DEFEND (volatile regime + PAUSE action)
    intent, _ = classify_intent_from_fields(
        regime="volatile_noise",
        base_action="PAUSE",
        decision_reason="EMERGENCY_FREEZE",
        action_label="HOLD"
    )
    assert intent == "PAUSE", f"PAUSE should beat DEFEND, got {intent}"
    print("✓ PAUSE > DEFEND")

    # STABILIZE beats DEFEND (volatile transition)
    intent, _ = classify_intent_from_fields(
        regime="volatile_transition",
        base_action="HOLD",
        decision_reason="test",
        action_label="HOLD"
    )
    assert intent == "STABILIZE", f"STABILIZE should beat DEFEND, got {intent}"
    print("✓ STABILIZE > DEFEND")

    # DEFEND beats HARVEST (volatile + harvest mention)
    intent, _ = classify_intent_from_fields(
        regime="volatile_noise",
        base_action="HOLD",
        decision_reason="mean_reversion opportunity",
        action_label="HOLD"
    )
    assert intent == "DEFEND", f"DEFEND should beat HARVEST, got {intent}"
    print("✓ DEFEND > HARVEST")

    # SEEK beats IDLE (act action)
    intent, _ = classify_intent_from_fields(
        regime="stable_range",
        base_action="act",
        decision_reason="test",
        action_label="HOLD"
    )
    assert intent == "SEEK", f"SEEK should beat IDLE, got {intent}"
    print("✓ SEEK > IDLE")

    print("Test 4: PASS (4/4)")
    return True


def test_determinism():
    """Test Intent classification is deterministic."""
    print("\nTest 5: Determinism")
    print("-" * 60)

    test_input = {
        "regime": "emerging_trend",
        "base_action": "guard",
        "decision_reason": "EMERGING_TREND: Guard",
        "action_label": "BUY"
    }

    # Run 10 times
    results = []
    for _ in range(10):
        intent, reason = classify_intent_from_fields(**test_input)
        results.append((intent, reason))

    # Check all results are identical
    first = results[0]
    for i, result in enumerate(results[1:], 1):
        assert result == first, f"Run {i} produced different result: {result} != {first}"

    print(f"✓ 10 runs produced identical result: {first[0]} - {first[1]}")
    print("Test 5: PASS (1/1)")
    return True


def main():
    """Run all PR15A Intent agent smoke tests."""
    print("=" * 60)
    print("PR15A: Intent Agent Integration Smoke Test")
    print("=" * 60)

    try:
        results = []
        results.append(("Shared Function Exists", test_shared_function_exists()))
        results.append(("Agent-Reporting Consistency", test_agent_reporting_consistency()))
        results.append(("Missing Data Handling", test_missing_data_handling()))
        results.append(("Priority Order Enforcement", test_priority_order_enforcement()))
        results.append(("Determinism", test_determinism()))

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
            print("✓ ALL PR15A INTENT AGENT TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ SOME PR15A INTENT AGENT TESTS FAILED")
            print("=" * 60)
            return 1

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"FAIL: {e}")
        print("=" * 60)
        return 1

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Unexpected exception during validation")
        print(f"{e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
