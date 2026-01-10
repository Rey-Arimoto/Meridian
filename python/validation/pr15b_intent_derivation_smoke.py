#!/usr/bin/env python3
"""
PR15B: Intent Derivation Smoke Test

Purpose: Verify derive_intent_primary() correctly derives Intent from v0.2 logs.

Requirements:
- Correct Intent derivation for each Intent type (PAUSE, STABILIZE, DEFEND, HARVEST, SEEK, IDLE)
- N/A returned when required columns missing
- Priority order respected (PAUSE > STABILIZE > DEFEND > HARVEST > SEEK > IDLE)
- Deterministic (same input → same output)
- No crashes on missing data
- Exit 0 on PASS, 1 on FAIL
"""

import sys
import os
import pandas as pd

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from reporting.pr15b_intent_derivation import derive_intent_primary, derive_intent_with_reason


def test_pause_intent():
    """Test PAUSE Intent derivation."""
    print("\nTest 1: PAUSE Intent")
    print("-" * 60)

    # Case 1: base_action = PAUSE
    df1 = pd.DataFrame({
        "regime": ["stable_range"],
        "base_action": ["PAUSE"],
        "decision_reason": ["test"],
        "action_label": ["HOLD"]
    })
    intent1 = derive_intent_primary(df1)
    assert intent1[0] == "PAUSE", f"Expected PAUSE, got {intent1[0]}"
    print("✓ base_action=PAUSE → PAUSE")

    # Case 2: decision_reason contains "EMERGENCY_FREEZE"
    df2 = pd.DataFrame({
        "regime": ["stable_range"],
        "base_action": ["HOLD"],
        "decision_reason": ["EMERGENCY_FREEZE | overlay=EMERGENCY_FREEZE"],
        "action_label": ["FREEZE"]
    })
    intent2 = derive_intent_primary(df2)
    assert intent2[0] == "PAUSE", f"Expected PAUSE, got {intent2[0]}"
    print("✓ decision_reason contains EMERGENCY_FREEZE → PAUSE")

    # Case 3: decision_reason contains "PAUSE"
    df3 = pd.DataFrame({
        "regime": ["regime_transition"],
        "base_action": ["pause"],
        "decision_reason": ["Critical entropy: PAUSE"],
        "action_label": ["HOLD"]
    })
    intent3 = derive_intent_primary(df3)
    assert intent3[0] == "PAUSE", f"Expected PAUSE, got {intent3[0]}"
    print("✓ decision_reason contains PAUSE → PAUSE")

    print("Test 1: PASS (3/3)")
    return True


def test_stabilize_intent():
    """Test STABILIZE Intent derivation."""
    print("\nTest 2: STABILIZE Intent")
    print("-" * 60)

    # Case 1: regime = REGIME_TRANSITION
    df1 = pd.DataFrame({
        "regime": ["REGIME_TRANSITION"],
        "base_action": ["HOLD"],
        "decision_reason": ["test"],
        "action_label": ["HOLD"]
    })
    intent1 = derive_intent_primary(df1)
    assert intent1[0] == "STABILIZE", f"Expected STABILIZE, got {intent1[0]}"
    print("✓ regime=REGIME_TRANSITION → STABILIZE")

    # Case 2: regime contains "transition"
    df2 = pd.DataFrame({
        "regime": ["post_transition"],
        "base_action": ["HOLD"],
        "decision_reason": ["test"],
        "action_label": ["HOLD"]
    })
    intent2 = derive_intent_primary(df2)
    assert intent2[0] == "STABILIZE", f"Expected STABILIZE, got {intent2[0]}"
    print("✓ regime contains 'transition' → STABILIZE")

    print("Test 2: PASS (2/2)")
    return True


def test_defend_intent():
    """Test DEFEND Intent derivation."""
    print("\nTest 3: DEFEND Intent")
    print("-" * 60)

    # Case 1: regime contains "volatile"
    df1 = pd.DataFrame({
        "regime": ["volatile_noise"],
        "base_action": ["HOLD"],
        "decision_reason": ["test"],
        "action_label": ["HOLD"]
    })
    intent1 = derive_intent_primary(df1)
    assert intent1[0] == "DEFEND", f"Expected DEFEND, got {intent1[0]}"
    print("✓ regime=volatile_noise → DEFEND")

    # Case 2: regime contains "critical"
    df2 = pd.DataFrame({
        "regime": ["critical_state"],
        "base_action": ["HOLD"],
        "decision_reason": ["test"],
        "action_label": ["HOLD"]
    })
    intent2 = derive_intent_primary(df2)
    assert intent2[0] == "DEFEND", f"Expected DEFEND, got {intent2[0]}"
    print("✓ regime contains 'critical' → DEFEND")

    print("Test 3: PASS (2/2)")
    return True


def test_harvest_intent():
    """Test HARVEST Intent derivation."""
    print("\nTest 4: HARVEST Intent")
    print("-" * 60)

    # Case 1: decision_reason contains "mean_reversion"
    df1 = pd.DataFrame({
        "regime": ["emerging_trend"],
        "base_action": ["SHIFT"],
        "decision_reason": ["mean_reversion opportunity"],
        "action_label": ["BUY"]
    })
    intent1 = derive_intent_primary(df1)
    assert intent1[0] == "HARVEST", f"Expected HARVEST, got {intent1[0]}"
    print("✓ decision_reason contains 'mean_reversion' → HARVEST")

    # Case 2: decision_reason contains "harvest"
    df2 = pd.DataFrame({
        "regime": ["emerging_trend"],
        "base_action": ["SHIFT"],
        "decision_reason": ["harvest value from trend"],
        "action_label": ["BUY"]
    })
    intent2 = derive_intent_primary(df2)
    assert intent2[0] == "HARVEST", f"Expected HARVEST, got {intent2[0]}"
    print("✓ decision_reason contains 'harvest' → HARVEST")

    print("Test 4: PASS (2/2)")
    return True


def test_seek_intent():
    """Test SEEK Intent derivation."""
    print("\nTest 5: SEEK Intent")
    print("-" * 60)

    # Case 1: base_action = act (v0.2 active mode)
    df1 = pd.DataFrame({
        "regime": ["stable_range"],
        "base_action": ["act"],
        "decision_reason": ["STABLE_RANGE: Act"],
        "action_label": ["BUY"]
    })
    intent1 = derive_intent_primary(df1)
    assert intent1[0] == "SEEK", f"Expected SEEK, got {intent1[0]}"
    print("✓ base_action=act → SEEK")

    # Case 2: action_label = BUY
    df2 = pd.DataFrame({
        "regime": ["emerging_trend"],
        "base_action": ["guard"],
        "decision_reason": ["test"],
        "action_label": ["BUY"]
    })
    intent2 = derive_intent_primary(df2)
    assert intent2[0] == "SEEK", f"Expected SEEK, got {intent2[0]}"
    print("✓ action_label=BUY → SEEK")

    print("Test 5: PASS (2/2)")
    return True


def test_idle_intent():
    """Test IDLE Intent derivation."""
    print("\nTest 6: IDLE Intent")
    print("-" * 60)

    # Case 1: base_action = HOLD
    df1 = pd.DataFrame({
        "regime": ["stable_range"],
        "base_action": ["HOLD"],
        "decision_reason": ["test"],
        "action_label": ["HOLD"]
    })
    intent1 = derive_intent_primary(df1)
    assert intent1[0] == "IDLE", f"Expected IDLE, got {intent1[0]}"
    print("✓ base_action=HOLD → IDLE")

    # Case 2: action_label = HOLD
    df2 = pd.DataFrame({
        "regime": ["emerging_trend"],
        "base_action": ["guard"],
        "decision_reason": ["test"],
        "action_label": ["HOLD"]
    })
    intent2 = derive_intent_primary(df2)
    assert intent2[0] == "IDLE", f"Expected IDLE, got {intent2[0]}"
    print("✓ action_label=HOLD → IDLE")

    print("Test 6: PASS (2/2)")
    return True


def test_missing_data():
    """Test N/A returned when data missing."""
    print("\nTest 7: Missing Data → N/A")
    print("-" * 60)

    # Case 1: Empty DataFrame
    df1 = pd.DataFrame()
    intent1 = derive_intent_primary(df1)
    assert len(intent1) == 0, "Empty df should return empty series"
    print("✓ Empty DataFrame → empty series")

    # Case 2: Missing required columns
    df2 = pd.DataFrame({
        "timestamp_utc": ["2025-01-01T00:00:00"],
        "price": [1.0]
    })
    intent2 = derive_intent_primary(df2)
    assert intent2[0] == "N/A", f"Expected N/A, got {intent2[0]}"
    print("✓ Missing required columns → N/A")

    # Case 3: Null values in required columns
    df3 = pd.DataFrame({
        "regime": [None],
        "base_action": [None],
        "decision_reason": [None],
        "action_label": [None]
    })
    intent3 = derive_intent_primary(df3)
    assert intent3[0] == "N/A", f"Expected N/A, got {intent3[0]}"
    print("✓ Null values in required columns → N/A")

    print("Test 7: PASS (3/3)")
    return True


def test_priority_order():
    """Test Intent priority order (PAUSE > STABILIZE > DEFEND > HARVEST > SEEK > IDLE)."""
    print("\nTest 8: Priority Order")
    print("-" * 60)

    # Case 1: PAUSE beats STABILIZE
    df1 = pd.DataFrame({
        "regime": ["REGIME_TRANSITION"],
        "base_action": ["PAUSE"],
        "decision_reason": ["EMERGENCY_FREEZE"],
        "action_label": ["HOLD"]
    })
    intent1 = derive_intent_primary(df1)
    assert intent1[0] == "PAUSE", f"PAUSE should beat STABILIZE, got {intent1[0]}"
    print("✓ PAUSE > STABILIZE")

    # Case 2: STABILIZE beats DEFEND
    df2 = pd.DataFrame({
        "regime": ["volatile_transition"],
        "base_action": ["HOLD"],
        "decision_reason": ["test"],
        "action_label": ["HOLD"]
    })
    intent2 = derive_intent_primary(df2)
    assert intent2[0] == "STABILIZE", f"STABILIZE should beat DEFEND, got {intent2[0]}"
    print("✓ STABILIZE > DEFEND")

    # Case 3: DEFEND beats HARVEST
    df3 = pd.DataFrame({
        "regime": ["volatile_noise"],
        "base_action": ["HOLD"],
        "decision_reason": ["mean_reversion detected"],
        "action_label": ["HOLD"]
    })
    intent3 = derive_intent_primary(df3)
    assert intent3[0] == "DEFEND", f"DEFEND should beat HARVEST, got {intent3[0]}"
    print("✓ DEFEND > HARVEST")

    print("Test 8: PASS (3/3)")
    return True


def test_determinism():
    """Test deterministic behavior (same input → same output)."""
    print("\nTest 9: Determinism")
    print("-" * 60)

    df = pd.DataFrame({
        "regime": ["stable_range", "volatile_noise", "REGIME_TRANSITION"],
        "base_action": ["act", "HOLD", "PAUSE"],
        "decision_reason": ["test", "test", "EMERGENCY_FREEZE"],
        "action_label": ["BUY", "HOLD", "HOLD"]
    })

    # Run 10 times
    results = [derive_intent_primary(df) for _ in range(10)]

    # Check all results are identical
    for i in range(1, 10):
        assert results[i].equals(results[0]), f"Run {i} produced different result"

    print(f"✓ 10 runs produced identical results: {results[0].tolist()}")
    print("Test 9: PASS (1/1)")
    return True


def test_intent_with_reason():
    """Test derive_intent_with_reason() helper."""
    print("\nTest 10: Intent with Reason")
    print("-" * 60)

    df = pd.DataFrame({
        "regime": ["stable_range", "volatile_noise"],
        "base_action": ["act", "PAUSE"],
        "decision_reason": ["test", "EMERGENCY_FREEZE"],
        "action_label": ["BUY", "HOLD"]
    })

    result = derive_intent_with_reason(df)

    assert "intent_primary" in result.columns, "Missing intent_primary column"
    assert "intent_reason" in result.columns, "Missing intent_reason column"
    assert result["intent_primary"][0] == "SEEK", f"Expected SEEK, got {result['intent_primary'][0]}"
    assert result["intent_primary"][1] == "PAUSE", f"Expected PAUSE, got {result['intent_primary'][1]}"
    assert len(result["intent_reason"][0]) > 0, "Reason should be non-empty"
    print("✓ derive_intent_with_reason() returns intent + reason")

    print("Test 10: PASS (1/1)")
    return True


def main():
    """Run all PR15B Intent derivation smoke tests."""
    print("=" * 60)
    print("PR15B: Intent Derivation Smoke Test")
    print("=" * 60)

    try:
        results = []
        results.append(("PAUSE Intent", test_pause_intent()))
        results.append(("STABILIZE Intent", test_stabilize_intent()))
        results.append(("DEFEND Intent", test_defend_intent()))
        results.append(("HARVEST Intent", test_harvest_intent()))
        results.append(("SEEK Intent", test_seek_intent()))
        results.append(("IDLE Intent", test_idle_intent()))
        results.append(("Missing Data → N/A", test_missing_data()))
        results.append(("Priority Order", test_priority_order()))
        results.append(("Determinism", test_determinism()))
        results.append(("Intent with Reason", test_intent_with_reason()))

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
            print("✓ ALL PR15B INTENT DERIVATION TESTS PASSED")
            print("=" * 60)
            return 0
        else:
            print("✗ SOME PR15B INTENT DERIVATION TESTS FAILED")
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
        return 1


if __name__ == "__main__":
    sys.exit(main())
