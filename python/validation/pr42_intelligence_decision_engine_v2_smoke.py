#!/usr/bin/env python3
"""
PR42: v0.5 Intelligence Decision Engine v2 (Rule Overlay / Regime-Aware) Smoke Test

Purpose: Verify PR42 overlay-based decision engine correctly applies regime-aware rules.

Requirements:
1. default ruleset: final_action == base_action
2. halted ruleset: final_action == "PAUSE"
3. cautious ruleset: base_action="SHIFT" → final_action=="HOLD"
4. decision_reason contains no digits
5. decision_reason contains no outcome/evaluative vocabulary
6. decision_version == "v0.5"
7. decision_inputs is list with used keys
8. exit code 0 (warning-only)

Non-Goals:
- No behavior modification (READ-ONLY)
- No v0.4 confidence modification
- No v0.2 execution modification
"""

import sys
import os
import re

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from intelligence.intelligence_decision_engine_v2 import generate_decision_record_v2


def test_default_ruleset_passthrough():
    """Test 1: default ruleset - final_action == base_action."""
    print("\nTest 1: Default Ruleset (Pass-Through)")
    print("-" * 60)

    test_cases = [
        {"base_action": "HOLD", "intent_primary": "IDLE", "regime": "stable_range"},
        {"base_action": "SHIFT", "intent_primary": "SEEK", "regime": "emerging_trend"},
        {"base_action": "PAUSE", "intent_primary": "WAIT", "regime": "stable_range"},
    ]

    for i, row_dict in enumerate(test_cases):
        decision_record = generate_decision_record_v2(row_dict)
        base_action = row_dict["base_action"]
        final_action = decision_record["decision_action"]

        assert final_action == base_action, \
            f"Default ruleset must pass through base_action: expected '{base_action}', got '{final_action}'"

        print(f"✓ Test case {i+1}: base_action '{base_action}' → decision_action '{final_action}' (pass-through)")

    print("Test 1: PASS")
    return True


def test_halted_ruleset_force_pause():
    """Test 2: halted ruleset - final_action == "PAUSE"."""
    print("\nTest 2: Halted Ruleset (Force PAUSE)")
    print("-" * 60)

    # Test halted regimes
    halted_regimes = ["REGIME_TRANSITION", "volatile_noise"]

    for regime in halted_regimes:
        row_dict = {
            "base_action": "SHIFT",  # Even aggressive action should be halted
            "intent_primary": "SEEK",
            "regime": regime,
        }

        decision_record = generate_decision_record_v2(row_dict)
        final_action = decision_record["decision_action"]

        assert final_action == "PAUSE", \
            f"Halted ruleset must force PAUSE: regime '{regime}' got '{final_action}'"

        print(f"✓ Regime '{regime}': base_action 'SHIFT' → decision_action 'PAUSE' (halted)")

    print("Test 2: PASS")
    return True


def test_cautious_ruleset_suppress_shift():
    """Test 3: cautious ruleset - base_action="SHIFT" → final_action=="HOLD"."""
    print("\nTest 3: Cautious Ruleset (Suppress SHIFT → HOLD)")
    print("-" * 60)

    cautious_intents = ["STABILIZE", "DEFEND", "PAUSE"]

    for intent in cautious_intents:
        row_dict = {
            "base_action": "SHIFT",
            "intent_primary": intent,
            "regime": "emerging_trend",
        }

        decision_record = generate_decision_record_v2(row_dict)
        final_action = decision_record["decision_action"]

        assert final_action == "HOLD", \
            f"Cautious ruleset must suppress SHIFT to HOLD: intent '{intent}' got '{final_action}'"

        print(f"✓ Intent '{intent}': base_action 'SHIFT' → decision_action 'HOLD' (suppressed)")

    print("Test 3: PASS")
    return True


def test_decision_reason_no_digits():
    """Test 4: decision_reason contains no digits (non-numeric requirement)."""
    print("\nTest 4: decision_reason Contains No Digits")
    print("-" * 60)

    test_cases = [
        {"base_action": "HOLD", "intent_primary": "IDLE", "regime": "stable_range"},
        {"base_action": "SHIFT", "intent_primary": "STABILIZE", "regime": "emerging_trend"},  # cautious
        {"base_action": "SHIFT", "intent_primary": "SEEK", "regime": "REGIME_TRANSITION"},  # halted
    ]

    for i, row_dict in enumerate(test_cases):
        decision_record = generate_decision_record_v2(row_dict)
        decision_reason = decision_record["decision_reason"]

        has_digits = bool(re.search(r'\d', decision_reason))

        assert not has_digits, \
            f"decision_reason must not contain digits (non-numeric), got: {decision_reason}"

        print(f"✓ Test case {i+1}: decision_reason contains no digits")
        print(f"  Reason: {decision_reason}")

    print("Test 4: PASS")
    return True


def test_decision_reason_no_outcome_vocabulary():
    """Test 5: decision_reason contains no outcome/evaluative vocabulary."""
    print("\nTest 5: decision_reason Contains No Outcome/Evaluative Vocabulary")
    print("-" * 60)

    # PR39 prohibited patterns
    prohibited_patterns = [
        r'\b(profit|loss|gain|return|pnl|drawdown|sharpe)\b',
        r'\b(correct|incorrect|wrong|right|accurate)\b',
        r'\b(good|bad|better|worse|best|worst)\b',
        r'\b(high|low|higher|lower|strong|weak)\b',
        r'\b(improve|degrade|optimize|maximize|minimize)\b',
    ]

    test_cases = [
        {"base_action": "HOLD", "intent_primary": "IDLE", "regime": "stable_range"},
        {"base_action": "SHIFT", "intent_primary": "STABILIZE", "regime": "emerging_trend"},
        {"base_action": "SHIFT", "intent_primary": "SEEK", "regime": "volatile_noise"},
    ]

    for i, row_dict in enumerate(test_cases):
        decision_record = generate_decision_record_v2(row_dict)
        decision_reason = decision_record["decision_reason"]

        violations = []
        for pattern in prohibited_patterns:
            if re.search(pattern, decision_reason, re.IGNORECASE):
                violations.append(pattern)

        assert len(violations) == 0, \
            f"decision_reason must not contain outcome/evaluative vocabulary, violations: {violations}, reason: {decision_reason}"

        print(f"✓ Test case {i+1}: decision_reason contains no prohibited vocabulary")

    print("Test 5: PASS")
    return True


def test_decision_version_fixed():
    """Test 6: decision_version == "v0.5"."""
    print("\nTest 6: decision_version Fixed to 'v0.5'")
    print("-" * 60)

    test_cases = [
        {"base_action": "HOLD", "intent_primary": "IDLE", "regime": "stable_range"},
        {"base_action": "SHIFT", "intent_primary": "SEEK", "regime": "REGIME_TRANSITION"},
        {},  # Empty row (should still return v0.5)
    ]

    for i, row_dict in enumerate(test_cases):
        decision_record = generate_decision_record_v2(row_dict)
        decision_version = decision_record["decision_version"]

        assert decision_version == "v0.5", \
            f"decision_version must be 'v0.5', got '{decision_version}'"

        print(f"✓ Test case {i+1}: decision_version == 'v0.5' (fixed)")

    print("Test 6: PASS")
    return True


def test_decision_inputs_is_list():
    """Test 7: decision_inputs is list with used keys."""
    print("\nTest 7: decision_inputs Is List with Used Keys")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "confidence_reason": "Source:entropy_bp; ...",
        "timestamp_utc": "2025-01-10T12:00:00Z",
    }

    decision_record = generate_decision_record_v2(row_dict)
    decision_inputs = decision_record["decision_inputs"]

    # Verify it's a list
    assert isinstance(decision_inputs, list), \
        f"decision_inputs must be a list, got {type(decision_inputs)}"

    print(f"✓ decision_inputs is list: {decision_inputs}")

    # Verify it contains expected keys
    expected_keys = ["base_action", "intent_primary", "regime"]
    for key in expected_keys:
        assert key in decision_inputs, \
            f"decision_inputs must contain '{key}', got {decision_inputs}"

    print(f"✓ decision_inputs contains expected keys: {expected_keys}")

    # Verify list is sorted and unique (PR38 spec)
    assert decision_inputs == sorted(set(decision_inputs)), \
        f"decision_inputs must be sorted and unique, got {decision_inputs}"

    print(f"✓ decision_inputs is sorted and unique")

    print("Test 7: PASS")
    return True


def test_exit_code_always_zero():
    """Test 8: Exit code always 0 (warning-only)."""
    print("\nTest 8: Exit Code Always 0 (Warning-Only)")
    print("-" * 60)

    # Test various scenarios (normal, invalid input, missing fields)
    test_cases = [
        {"base_action": "HOLD", "intent_primary": "IDLE"},
        {},  # Empty row
        {"base_action": None},  # None base_action
        {"invalid": "data"},  # Invalid keys
    ]

    for i, row_dict in enumerate(test_cases):
        try:
            decision_record = generate_decision_record_v2(row_dict)
            assert "decision_action" in decision_record, "decision_record must have decision_action"
            print(f"✓ Test case {i+1}: No exception raised, decision_record generated")
        except Exception as e:
            assert False, f"Should never raise exception (warning-only), got: {e}"

    print(f"✓ All test cases handled without exceptions")
    print(f"✓ Exit code will be 0 (warning-only)")

    print("Test 8: PASS")
    return True


def main():
    """Run all PR42 Intelligence Decision Engine v2 smoke tests."""
    print("=" * 60)
    print("PR42: Intelligence Decision Engine v2 Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Default Ruleset (Pass-Through)", test_default_ruleset_passthrough()))
        results.append(("Halted Ruleset (Force PAUSE)", test_halted_ruleset_force_pause()))
        results.append(("Cautious Ruleset (Suppress SHIFT)", test_cautious_ruleset_suppress_shift()))
        results.append(("decision_reason No Digits", test_decision_reason_no_digits()))
        results.append(("decision_reason No Outcome Vocabulary", test_decision_reason_no_outcome_vocabulary()))
        results.append(("decision_version Fixed to 'v0.5'", test_decision_version_fixed()))
        results.append(("decision_inputs Is List", test_decision_inputs_is_list()))
        results.append(("Exit Code Always Zero", test_exit_code_always_zero()))

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
            print("✓ ALL PR42 DECISION ENGINE V2 TESTS PASSED")
            print("=" * 60)
            print("PR42 Requirements Verified:")
            print("  - Default ruleset passes through base_action")
            print("  - Halted ruleset forces PAUSE (safety override)")
            print("  - Cautious ruleset suppresses aggressive actions")
            print("  - decision_reason is non-numeric (no digits)")
            print("  - decision_reason is non-evaluative (no outcome vocab)")
            print("  - decision_version fixed to 'v0.5'")
            print("  - decision_inputs is list with used keys")
            print("  - Warning-only (never raises exceptions)")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR42 TESTS FAILED")
            print("=" * 60)
            print("Exit code: 0 (warning-only, never fails)")
            return 0  # Always exit 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Unexpected exception during validation")
        print(f"{e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("Exit code: 0 (warning-only, never fails)")
        return 0  # Always exit 0


if __name__ == "__main__":
    sys.exit(main())
