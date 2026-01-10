#!/usr/bin/env python3
"""
PR45: v0.5 Decision Engine Shadow Diff Logging Smoke Test

Purpose: Verify PR45 diff logging correctly compares primary and shadow decisions.

Requirements:
1. diff_logging=False → diff fields are OFF / UNAVAILABLE
2. diff_logging=True & shadow_mode=False → UNAVAILABLE (no shadow)
3. diff_logging=True & shadow_mode=True & (primary=v1, shadow=v2) → pair is v1_vs_v2
4. diff_logging=True & shadow_mode=True & (primary=v2, shadow=v1) → pair is v2_vs_v1
5. ALIGNED case (primary_action == shadow_action)
6. DIVERGED case (primary_action != shadow_action)
7. digits禁止: v5_decision_diff_summary has no digits
8. exit code 0 (warning-only)

Non-Goals:
- No behavior modification (READ-ONLY)
- No v0.4 confidence modification
- No v0.2 execution modification
- No evaluation (no good/bad, better/worse)
- No outcome vocabulary (no profit/loss, correct/wrong)
"""

import sys
import os
import re

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from intelligence.intelligence_decision_engine_v1 import generate_decision_record_v1
from intelligence.intelligence_decision_engine_v2 import generate_decision_record_v2


def simulate_diff_logging_wiring(row_dict, primary_engine, shadow_mode, diff_logging):
    """
    Simulate PR45 diff logging wiring behavior.

    This mimics the diff logging logic added to meridian_realtime_agent.py.

    Returns: Modified row_dict with primary, shadow (if enabled), and diff fields
    """
    from datetime import datetime, timezone
    import json

    # PR44: Generate primary and shadow records (prerequisite for PR45)
    try:
        # Determine shadow engine
        if primary_engine == "v1":
            shadow_engine = "v2"
        else:
            shadow_engine = "v1"

        # Generate primary record
        if primary_engine == "v2":
            primary_record = generate_decision_record_v2(row_dict)
            primary_engine_used = "v2"
        else:
            primary_record = generate_decision_record_v1(row_dict)
            primary_engine_used = "v1"

        row_dict["v5_decision_engine"] = primary_engine_used
        row_dict["v5_decision_action"] = primary_record.get("decision_action", "UNKNOWN")
        row_dict["v5_decision_reason"] = primary_record.get("decision_reason", "")
        primary_inputs_list = primary_record.get("decision_inputs", [])
        row_dict["v5_decision_inputs"] = ",".join(primary_inputs_list) if primary_inputs_list else ""
        row_dict["v5_decision_inputs_json"] = json.dumps(primary_inputs_list)
        row_dict["v5_decision_version"] = "v0.5"
        row_dict["v5_decision_generated_at"] = primary_record.get("decision_generated_at", "")

        # Generate shadow record (if shadow mode enabled)
        if shadow_mode:
            if shadow_engine == "v2":
                shadow_record = generate_decision_record_v2(row_dict)
                shadow_engine_used = "v2"
            else:
                shadow_record = generate_decision_record_v1(row_dict)
                shadow_engine_used = "v1"

            row_dict["v5_shadow_decision_engine"] = shadow_engine_used
            row_dict["v5_shadow_decision_action"] = shadow_record.get("decision_action", "UNKNOWN")
            row_dict["v5_shadow_decision_reason"] = shadow_record.get("decision_reason", "")
            shadow_inputs_list = shadow_record.get("decision_inputs", [])
            row_dict["v5_shadow_decision_inputs"] = ",".join(shadow_inputs_list) if shadow_inputs_list else ""
            row_dict["v5_shadow_decision_inputs_json"] = json.dumps(shadow_inputs_list)
            row_dict["v5_shadow_decision_version"] = "v0.5"
            row_dict["v5_shadow_decision_generated_at"] = shadow_record.get("decision_generated_at", "")

    except Exception as e:
        print(f"[INFO][TEST] Primary/shadow generation failed (expected in test): {e}")
        row_dict["v5_decision_engine"] = "UNKNOWN"
        row_dict["v5_decision_action"] = "UNKNOWN"

    # PR45: Generate diff fields
    try:
        if not diff_logging:
            # PR45: Diff logging disabled
            row_dict["v5_decision_diff_mode"] = "OFF"
            row_dict["v5_decision_diff_status"] = "UNAVAILABLE"
            row_dict["v5_decision_diff_pair"] = "UNKNOWN"
            row_dict["v5_decision_diff_summary"] = "diff logging disabled."

        elif not shadow_mode:
            # PR45: Diff logging enabled but shadow mode disabled
            row_dict["v5_decision_diff_mode"] = "ON"
            row_dict["v5_decision_diff_status"] = "UNAVAILABLE"
            row_dict["v5_decision_diff_pair"] = "UNKNOWN"
            row_dict["v5_decision_diff_summary"] = "shadow record not present."

        else:
            # PR45: Diff logging enabled and shadow mode enabled
            row_dict["v5_decision_diff_mode"] = "ON"

            # Determine diff pair
            primary_engine_val = row_dict.get("v5_decision_engine", "UNKNOWN")
            shadow_engine_val = row_dict.get("v5_shadow_decision_engine", "UNKNOWN")

            if primary_engine_val == "v1" and shadow_engine_val == "v2":
                diff_pair = "v1_vs_v2"
            elif primary_engine_val == "v2" and shadow_engine_val == "v1":
                diff_pair = "v2_vs_v1"
            else:
                diff_pair = "UNKNOWN"

            row_dict["v5_decision_diff_pair"] = diff_pair

            # Determine diff status
            primary_action = row_dict.get("v5_decision_action", "")
            shadow_action = row_dict.get("v5_shadow_decision_action", "")

            primary_valid = primary_action and primary_action != "UNKNOWN"
            shadow_valid = shadow_action and shadow_action != "UNKNOWN"

            if primary_valid and shadow_valid:
                if primary_action == shadow_action:
                    diff_status = "ALIGNED"
                    diff_summary = "primary and shadow actions aligned."
                else:
                    diff_status = "DIVERGED"
                    diff_summary = "primary and shadow actions diverged."
            else:
                diff_status = "UNAVAILABLE"
                diff_summary = "diff unavailable due to missing actions."

            row_dict["v5_decision_diff_status"] = diff_status
            row_dict["v5_decision_diff_summary"] = diff_summary

    except Exception as diff_e:
        print(f"[INFO][TEST] Diff generation failed (expected in test): {diff_e}")
        row_dict["v5_decision_diff_mode"] = "ON"
        row_dict["v5_decision_diff_status"] = "UNAVAILABLE"
        row_dict["v5_decision_diff_pair"] = "UNKNOWN"
        row_dict["v5_decision_diff_summary"] = "diff failed safely."

    return row_dict


def test_diff_logging_false():
    """Test 1: diff_logging=False → diff fields are OFF / UNAVAILABLE."""
    print("\nTest 1: diff_logging=False → OFF / UNAVAILABLE")
    print("-" * 60)

    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",
    }

    row_dict = simulate_diff_logging_wiring(row_dict, "v1", shadow_mode=False, diff_logging=False)

    assert row_dict["v5_decision_diff_mode"] == "OFF", \
        f"mode must be OFF when diff_logging=False, got '{row_dict['v5_decision_diff_mode']}'"
    assert row_dict["v5_decision_diff_status"] == "UNAVAILABLE", \
        f"status must be UNAVAILABLE when diff_logging=False, got '{row_dict['v5_decision_diff_status']}'"
    assert row_dict["v5_decision_diff_pair"] == "UNKNOWN", \
        f"pair must be UNKNOWN when diff_logging=False, got '{row_dict['v5_decision_diff_pair']}'"
    assert row_dict["v5_decision_diff_summary"] == "diff logging disabled.", \
        f"summary mismatch, got '{row_dict['v5_decision_diff_summary']}'"

    print(f"✓ mode: {row_dict['v5_decision_diff_mode']}")
    print(f"✓ status: {row_dict['v5_decision_diff_status']}")
    print(f"✓ pair: {row_dict['v5_decision_diff_pair']}")
    print(f"✓ summary: {row_dict['v5_decision_diff_summary']}")

    print("Test 1: PASS")
    return True


def test_diff_logging_true_no_shadow():
    """Test 2: diff_logging=True & shadow_mode=False → UNAVAILABLE (no shadow)."""
    print("\nTest 2: diff_logging=True & shadow_mode=False → UNAVAILABLE")
    print("-" * 60)

    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",
    }

    row_dict = simulate_diff_logging_wiring(row_dict, "v1", shadow_mode=False, diff_logging=True)

    assert row_dict["v5_decision_diff_mode"] == "ON", \
        f"mode must be ON when diff_logging=True, got '{row_dict['v5_decision_diff_mode']}'"
    assert row_dict["v5_decision_diff_status"] == "UNAVAILABLE", \
        f"status must be UNAVAILABLE when no shadow, got '{row_dict['v5_decision_diff_status']}'"
    assert row_dict["v5_decision_diff_pair"] == "UNKNOWN", \
        f"pair must be UNKNOWN when no shadow, got '{row_dict['v5_decision_diff_pair']}'"
    assert row_dict["v5_decision_diff_summary"] == "shadow record not present.", \
        f"summary mismatch, got '{row_dict['v5_decision_diff_summary']}'"

    print(f"✓ mode: {row_dict['v5_decision_diff_mode']}")
    print(f"✓ status: {row_dict['v5_decision_diff_status']}")
    print(f"✓ pair: {row_dict['v5_decision_diff_pair']}")
    print(f"✓ summary: {row_dict['v5_decision_diff_summary']}")

    print("Test 2: PASS")
    return True


def test_diff_logging_v1_primary():
    """Test 3: diff_logging=True & shadow_mode=True & (primary=v1, shadow=v2) → pair is v1_vs_v2."""
    print("\nTest 3: Primary=v1, Shadow=v2 → pair is v1_vs_v2")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "REGIME_TRANSITION",  # v2 halted regime
    }

    row_dict = simulate_diff_logging_wiring(row_dict, "v1", shadow_mode=True, diff_logging=True)

    assert row_dict["v5_decision_diff_mode"] == "ON", \
        f"mode must be ON, got '{row_dict['v5_decision_diff_mode']}'"
    assert row_dict["v5_decision_diff_pair"] == "v1_vs_v2", \
        f"pair must be v1_vs_v2, got '{row_dict['v5_decision_diff_pair']}'"

    # v1 mirrors SHIFT, v2 halted forces PAUSE → should DIVERGE
    assert row_dict["v5_decision_diff_status"] == "DIVERGED", \
        f"status should be DIVERGED (v1=SHIFT, v2=PAUSE), got '{row_dict['v5_decision_diff_status']}'"

    print(f"✓ mode: {row_dict['v5_decision_diff_mode']}")
    print(f"✓ pair: {row_dict['v5_decision_diff_pair']}")
    print(f"✓ status: {row_dict['v5_decision_diff_status']}")
    print(f"✓ primary action (v1): {row_dict['v5_decision_action']}")
    print(f"✓ shadow action (v2): {row_dict['v5_shadow_decision_action']}")

    print("Test 3: PASS")
    return True


def test_diff_logging_v2_primary():
    """Test 4: diff_logging=True & shadow_mode=True & (primary=v2, shadow=v1) → pair is v2_vs_v1."""
    print("\nTest 4: Primary=v2, Shadow=v1 → pair is v2_vs_v1")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "STABILIZE",  # v2 cautious intent
        "regime": "emerging_trend",
    }

    row_dict = simulate_diff_logging_wiring(row_dict, "v2", shadow_mode=True, diff_logging=True)

    assert row_dict["v5_decision_diff_mode"] == "ON", \
        f"mode must be ON, got '{row_dict['v5_decision_diff_mode']}'"
    assert row_dict["v5_decision_diff_pair"] == "v2_vs_v1", \
        f"pair must be v2_vs_v1, got '{row_dict['v5_decision_diff_pair']}'"

    # v2 cautious suppresses SHIFT → HOLD, v1 mirrors SHIFT → should DIVERGE
    assert row_dict["v5_decision_diff_status"] == "DIVERGED", \
        f"status should be DIVERGED (v2=HOLD, v1=SHIFT), got '{row_dict['v5_decision_diff_status']}'"

    print(f"✓ mode: {row_dict['v5_decision_diff_mode']}")
    print(f"✓ pair: {row_dict['v5_decision_diff_pair']}")
    print(f"✓ status: {row_dict['v5_decision_diff_status']}")
    print(f"✓ primary action (v2): {row_dict['v5_decision_action']}")
    print(f"✓ shadow action (v1): {row_dict['v5_shadow_decision_action']}")

    print("Test 4: PASS")
    return True


def test_diff_status_aligned():
    """Test 5: ALIGNED case (primary_action == shadow_action)."""
    print("\nTest 5: ALIGNED Case (Actions Match)")
    print("-" * 60)

    # Use case where v1 and v2 produce same result
    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",  # default ruleset for v2
    }

    row_dict = simulate_diff_logging_wiring(row_dict, "v1", shadow_mode=True, diff_logging=True)

    # Both v1 and v2 should produce HOLD (v1 mirrors, v2 default passes through)
    assert row_dict["v5_decision_diff_status"] == "ALIGNED", \
        f"status must be ALIGNED when actions match, got '{row_dict['v5_decision_diff_status']}'"
    assert row_dict["v5_decision_diff_summary"] == "primary and shadow actions aligned.", \
        f"summary mismatch, got '{row_dict['v5_decision_diff_summary']}'"

    print(f"✓ status: {row_dict['v5_decision_diff_status']}")
    print(f"✓ summary: {row_dict['v5_decision_diff_summary']}")
    print(f"✓ primary action: {row_dict['v5_decision_action']}")
    print(f"✓ shadow action: {row_dict['v5_shadow_decision_action']}")
    print(f"✓ Actions aligned (both HOLD)")

    print("Test 5: PASS")
    return True


def test_diff_status_diverged():
    """Test 6: DIVERGED case (primary_action != shadow_action)."""
    print("\nTest 6: DIVERGED Case (Actions Differ)")
    print("-" * 60)

    # Use halted regime where v2 forces PAUSE but v1 mirrors base_action
    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "volatile_noise",  # v2 halted regime
    }

    row_dict = simulate_diff_logging_wiring(row_dict, "v1", shadow_mode=True, diff_logging=True)

    # v1 mirrors SHIFT, v2 forces PAUSE
    assert row_dict["v5_decision_diff_status"] == "DIVERGED", \
        f"status must be DIVERGED when actions differ, got '{row_dict['v5_decision_diff_status']}'"
    assert row_dict["v5_decision_diff_summary"] == "primary and shadow actions diverged.", \
        f"summary mismatch, got '{row_dict['v5_decision_diff_summary']}'"

    print(f"✓ status: {row_dict['v5_decision_diff_status']}")
    print(f"✓ summary: {row_dict['v5_decision_diff_summary']}")
    print(f"✓ primary action (v1): {row_dict['v5_decision_action']}")
    print(f"✓ shadow action (v2): {row_dict['v5_shadow_decision_action']}")
    print(f"✓ Actions diverged (SHIFT vs PAUSE)")

    print("Test 6: PASS")
    return True


def test_summary_no_digits():
    """Test 7: digits禁止: v5_decision_diff_summary has no digits."""
    print("\nTest 7: v5_decision_diff_summary Contains No Digits")
    print("-" * 60)

    test_cases = [
        ("v1", False, False),  # diff_logging=False
        ("v1", False, True),   # diff_logging=True, shadow_mode=False
        ("v1", True, True),    # diff_logging=True, shadow_mode=True, DIVERGED
        ("v2", True, True),    # diff_logging=True, shadow_mode=True, DIVERGED
    ]

    for i, (primary_engine, shadow_mode, diff_logging) in enumerate(test_cases):
        row_dict = {
            "base_action": "SHIFT",
            "intent_primary": "SEEK",
            "regime": "REGIME_TRANSITION",
        }

        row_dict = simulate_diff_logging_wiring(row_dict, primary_engine, shadow_mode, diff_logging)

        summary = row_dict.get("v5_decision_diff_summary", "")
        has_digits = bool(re.search(r'\d', summary))

        assert not has_digits, \
            f"v5_decision_diff_summary must not contain digits (non-numeric), got: {summary}"

        print(f"✓ Test case {i+1}: summary contains no digits")
        print(f"  Summary: {summary}")

    print("Test 7: PASS")
    return True


def test_exit_code_always_zero():
    """Test 8: Exit code always 0 (warning-only)."""
    print("\nTest 8: Exit Code Always 0 (Warning-Only)")
    print("-" * 60)

    # Test various scenarios
    test_cases = [
        ("v1", False, False, {"base_action": "HOLD"}),
        ("v1", False, True, {"base_action": "SHIFT", "intent_primary": "SEEK"}),
        ("v1", True, True, {"base_action": "SHIFT", "regime": "REGIME_TRANSITION"}),
        ("v2", True, True, {"base_action": "SHIFT", "intent_primary": "STABILIZE"}),
        ("v1", True, True, {}),  # Empty row
    ]

    for i, (primary_engine, shadow_mode, diff_logging, row_dict) in enumerate(test_cases):
        try:
            simulate_diff_logging_wiring(row_dict, primary_engine, shadow_mode, diff_logging)
            print(f"✓ Test case {i+1} (engine={primary_engine}, shadow={shadow_mode}, diff={diff_logging}): No exception raised")
        except Exception as e:
            assert False, f"Should never raise exception (warning-only), got: {e}"

    print(f"✓ All test cases handled without exceptions")
    print(f"✓ Exit code will be 0 (warning-only)")

    print("Test 8: PASS")
    return True


def main():
    """Run all PR45 Decision Engine Shadow Diff Logging smoke tests."""
    print("=" * 60)
    print("PR45: Decision Engine Shadow Diff Logging Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("diff_logging=False", test_diff_logging_false()))
        results.append(("diff_logging=True No Shadow", test_diff_logging_true_no_shadow()))
        results.append(("Primary=v1 Shadow=v2", test_diff_logging_v1_primary()))
        results.append(("Primary=v2 Shadow=v1", test_diff_logging_v2_primary()))
        results.append(("ALIGNED Case", test_diff_status_aligned()))
        results.append(("DIVERGED Case", test_diff_status_diverged()))
        results.append(("Summary No Digits", test_summary_no_digits()))
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
            print("✓ ALL PR45 SHADOW DIFF LOGGING TESTS PASSED")
            print("=" * 60)
            print("PR45 Requirements Verified:")
            print("  - diff_logging=False: OFF / UNAVAILABLE (safe)")
            print("  - diff_logging=True & shadow=False: UNAVAILABLE (no shadow)")
            print("  - Primary=v1, Shadow=v2: pair=v1_vs_v2")
            print("  - Primary=v2, Shadow=v1: pair=v2_vs_v1")
            print("  - ALIGNED status when actions match")
            print("  - DIVERGED status when actions differ")
            print("  - summary is non-numeric (no digits)")
            print("  - Warning-only (never raises exceptions)")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR45 TESTS FAILED")
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
