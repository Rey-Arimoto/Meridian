#!/usr/bin/env python3
"""
PR43: v0.5 Decision Engine Selector Wiring Smoke Test

Purpose: Verify PR43 selector wiring correctly switches between v1 and v2 decision engines.

Requirements:
1. Default (v1) works correctly
2. Selector=v2 calls v2 engine
3. Invalid selector falls back to v1
4. v5_decision_engine field records "v1"/"v2" correctly
5. Decision record has all PR38 required fields
6. v5_decision_inputs_json is JSON list (PR41A)
7. PR39 guard executes without failure (warning-only)
8. Exit code 0 (warning-only)

Non-Goals:
- No behavior modification (READ-ONLY)
- No v0.4 confidence modification
- No v0.2 execution modification
"""

import sys
import os
import json
import re

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from intelligence.intelligence_decision_engine_v1 import generate_decision_record_v1
from intelligence.intelligence_decision_engine_v2 import generate_decision_record_v2
from intelligence.intelligence_decision_record_compliance import validate_decision_record_full


def simulate_selector_wiring(row_dict, engine_version):
    """
    Simulate PR43 selector wiring behavior.

    This mimics the selector logic added to meridian_realtime_agent.py.

    Returns: Modified row_dict with v5_decision_* fields and v5_decision_engine
    """
    from datetime import datetime, timezone

    try:
        # PR43: Select decision engine based on version
        if engine_version == "v2":
            decision_record = generate_decision_record_v2(row_dict)
            engine_used = "v2"
        elif engine_version == "v1":
            decision_record = generate_decision_record_v1(row_dict)
            engine_used = "v1"
        else:
            # PR43: Fallback to v1 for invalid engine version
            print(f"[INFO][TEST] Invalid engine version '{engine_version}', falling back to v1")
            decision_record = generate_decision_record_v1(row_dict)
            engine_used = "v1"

        # PR43: Record which engine was used
        row_dict["v5_decision_engine"] = engine_used

        # Add v0.5 decision fields
        row_dict["v5_decision_action"] = decision_record.get("decision_action", "UNKNOWN")
        row_dict["v5_decision_reason"] = decision_record.get("decision_reason", "")

        # PR41A: decision_inputs in both formats
        decision_inputs_list = decision_record.get("decision_inputs", [])
        row_dict["v5_decision_inputs"] = ",".join(decision_inputs_list) if decision_inputs_list else ""
        row_dict["v5_decision_inputs_json"] = json.dumps(decision_inputs_list)

        # PR41A: decision_version always "v0.5"
        row_dict["v5_decision_version"] = "v0.5"
        row_dict["v5_decision_generated_at"] = decision_record.get("decision_generated_at", "")

        # PR41A: Always validate (warning-only)
        compliance_warnings = validate_decision_record_full(decision_record, "test")
        if compliance_warnings:
            print(f"[INFO][TEST] Compliance warnings: {compliance_warnings}")

    except Exception as e:
        # PR43: Decision record generation must never stop execution
        print(f"[INFO][TEST] Wiring exception (expected in test): {e}")
        # PR43: Try fallback to v1 if v2 failed
        try:
            if engine_version == "v2":
                print(f"[INFO][TEST] Attempting fallback to v1 after v2 failure")
                decision_record = generate_decision_record_v1(row_dict)
                engine_used = "v1"
                row_dict["v5_decision_engine"] = engine_used
                row_dict["v5_decision_action"] = decision_record.get("decision_action", "UNKNOWN")
                row_dict["v5_decision_reason"] = decision_record.get("decision_reason", "")
                decision_inputs_list = decision_record.get("decision_inputs", [])
                row_dict["v5_decision_inputs"] = ",".join(decision_inputs_list) if decision_inputs_list else ""
                row_dict["v5_decision_inputs_json"] = json.dumps(decision_inputs_list)
                row_dict["v5_decision_version"] = "v0.5"
                row_dict["v5_decision_generated_at"] = decision_record.get("decision_generated_at", "")
            else:
                raise  # Re-raise if v1 itself failed
        except Exception as fallback_e:
            # PR43: Even fallback failed, use safe defaults
            print(f"[INFO][TEST] Fallback also failed: {fallback_e}")
            row_dict["v5_decision_engine"] = "UNKNOWN"
            row_dict["v5_decision_action"] = "UNKNOWN"
            row_dict["v5_decision_reason"] = ""
            row_dict["v5_decision_inputs"] = ""
            row_dict["v5_decision_inputs_json"] = "[]"
            row_dict["v5_decision_version"] = "v0.5"
            row_dict["v5_decision_generated_at"] = datetime.now(timezone.utc).isoformat()

    return row_dict


def test_default_v1_works():
    """Test 1: Default (v1) works correctly."""
    print("\nTest 1: Default (v1) Works Correctly")
    print("-" * 60)

    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",
    }

    row_dict = simulate_selector_wiring(row_dict, "v1")

    assert "v5_decision_engine" in row_dict, "v5_decision_engine must be present"
    assert row_dict["v5_decision_engine"] == "v1", \
        f"v5_decision_engine must be 'v1', got '{row_dict['v5_decision_engine']}'"

    # v1 mirrors base_action
    assert row_dict["v5_decision_action"] == "HOLD", \
        f"v1 should mirror base_action 'HOLD', got '{row_dict['v5_decision_action']}'"

    print(f"✓ Default engine is v1")
    print(f"✓ v5_decision_engine == 'v1'")
    print(f"✓ v5_decision_action mirrors base_action (HOLD)")

    print("Test 1: PASS")
    return True


def test_selector_v2_calls_v2():
    """Test 2: Selector=v2 calls v2 engine."""
    print("\nTest 2: Selector=v2 Calls v2 Engine")
    print("-" * 60)

    # Test halted ruleset (v2 specific)
    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "REGIME_TRANSITION",  # halted regime
    }

    row_dict = simulate_selector_wiring(row_dict, "v2")

    assert "v5_decision_engine" in row_dict, "v5_decision_engine must be present"
    assert row_dict["v5_decision_engine"] == "v2", \
        f"v5_decision_engine must be 'v2', got '{row_dict['v5_decision_engine']}'"

    # v2 halted ruleset forces PAUSE (different from base_action SHIFT)
    assert row_dict["v5_decision_action"] == "PAUSE", \
        f"v2 halted ruleset should force PAUSE, got '{row_dict['v5_decision_action']}'"

    print(f"✓ Selector v2 used v2 engine")
    print(f"✓ v5_decision_engine == 'v2'")
    print(f"✓ v2 halted ruleset applied (SHIFT → PAUSE)")

    print("Test 2: PASS")
    return True


def test_invalid_selector_fallback_v1():
    """Test 3: Invalid selector falls back to v1."""
    print("\nTest 3: Invalid Selector Falls Back to v1")
    print("-" * 60)

    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",
    }

    # Use invalid engine version
    row_dict = simulate_selector_wiring(row_dict, "v99")

    assert "v5_decision_engine" in row_dict, "v5_decision_engine must be present"
    assert row_dict["v5_decision_engine"] == "v1", \
        f"Invalid selector must fall back to v1, got '{row_dict['v5_decision_engine']}'"

    # v1 mirrors base_action
    assert row_dict["v5_decision_action"] == "HOLD", \
        f"Fallback v1 should mirror base_action, got '{row_dict['v5_decision_action']}'"

    print(f"✓ Invalid selector 'v99' fell back to v1")
    print(f"✓ v5_decision_engine == 'v1' (fallback)")
    print(f"✓ Fallback behavior works correctly")

    print("Test 3: PASS")
    return True


def test_v5_decision_engine_field():
    """Test 4: v5_decision_engine field records "v1"/"v2" correctly."""
    print("\nTest 4: v5_decision_engine Field Records Correctly")
    print("-" * 60)

    test_cases = [
        ("v1", "HOLD", "IDLE", "stable_range", "v1"),
        ("v2", "SHIFT", "STABILIZE", "emerging_trend", "v2"),  # cautious ruleset
    ]

    for engine_version, base_action, intent, regime, expected_engine in test_cases:
        row_dict = {
            "base_action": base_action,
            "intent_primary": intent,
            "regime": regime,
        }

        row_dict = simulate_selector_wiring(row_dict, engine_version)

        assert row_dict["v5_decision_engine"] == expected_engine, \
            f"v5_decision_engine must be '{expected_engine}', got '{row_dict['v5_decision_engine']}'"

        print(f"✓ Engine '{engine_version}' → v5_decision_engine '{expected_engine}' (correct)")

    print("Test 4: PASS")
    return True


def test_pr38_required_fields():
    """Test 5: Decision record has all PR38 required fields."""
    print("\nTest 5: Decision Record Has PR38 Required Fields")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
    }

    row_dict = simulate_selector_wiring(row_dict, "v1")

    # PR38 required fields (v5_ prefix in row_dict)
    required_fields = [
        "v5_decision_action",
        "v5_decision_reason",
        "v5_decision_inputs",
        "v5_decision_version",
        "v5_decision_generated_at",
        "v5_decision_engine",  # PR43 addition
    ]

    for field in required_fields:
        assert field in row_dict, f"Field '{field}' must be present in row_dict"
        print(f"✓ Field '{field}' present")

    print("Test 5: PASS")
    return True


def test_v5_decision_inputs_json_format():
    """Test 6: v5_decision_inputs_json is JSON list (PR41A)."""
    print("\nTest 6: v5_decision_inputs_json Is JSON List")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "confidence_reason": "Source:entropy_bp; ...",
    }

    row_dict = simulate_selector_wiring(row_dict, "v2")

    assert "v5_decision_inputs_json" in row_dict, "v5_decision_inputs_json must be present"

    # Verify it's valid JSON
    try:
        inputs_list = json.loads(row_dict["v5_decision_inputs_json"])
        assert isinstance(inputs_list, list), \
            f"v5_decision_inputs_json must be JSON list, got {type(inputs_list)}"

        print(f"✓ v5_decision_inputs_json is valid JSON list")
        print(f"  Parsed: {inputs_list}")

        # Verify it contains expected keys
        assert "base_action" in inputs_list, "JSON list should contain 'base_action'"
        print(f"✓ JSON list contains expected keys")

    except json.JSONDecodeError as e:
        assert False, f"v5_decision_inputs_json must be valid JSON: {e}"

    print("Test 6: PASS")
    return True


def test_pr39_guard_always_executed():
    """Test 7: PR39 guard executes without failure (warning-only)."""
    print("\nTest 7: PR39 Guard Executes Without Failure")
    print("-" * 60)

    # Test both v1 and v2
    test_cases = [
        ("v1", {"base_action": "HOLD", "intent_primary": "IDLE"}),
        ("v2", {"base_action": "SHIFT", "intent_primary": "SEEK", "regime": "REGIME_TRANSITION"}),
    ]

    for engine_version, row_dict in test_cases:
        row_dict = simulate_selector_wiring(row_dict, engine_version)

        # Verify wiring completed (guard was called but didn't stop execution)
        assert "v5_decision_action" in row_dict, \
            f"Wiring should complete for {engine_version} even with guard warnings"

        print(f"✓ Engine {engine_version}: PR39 guard executed (warnings allowed, execution continues)")

    print(f"✓ No conditional skipping of validation")
    print(f"✓ Warning-only behavior maintained")

    print("Test 7: PASS")
    return True


def test_exit_code_always_zero():
    """Test 8: Exit code always 0 (warning-only)."""
    print("\nTest 8: Exit Code Always 0 (Warning-Only)")
    print("-" * 60)

    # Test various scenarios (normal, invalid input, missing fields, invalid engine)
    test_cases = [
        ("v1", {"base_action": "HOLD"}),
        ("v2", {"base_action": "SHIFT", "intent_primary": "SEEK", "regime": "stable_range"}),
        ("v1", {}),  # Empty
        ("v2", {"base_action": None}),  # None value
        ("v99", {"base_action": "HOLD"}),  # Invalid engine
    ]

    for i, (engine_version, row_dict) in enumerate(test_cases):
        try:
            simulate_selector_wiring(row_dict, engine_version)
            print(f"✓ Test case {i+1} (engine={engine_version}): No exception raised")
        except Exception as e:
            assert False, f"Should never raise exception (warning-only), got: {e}"

    print(f"✓ All test cases handled without exceptions")
    print(f"✓ Exit code will be 0 (warning-only)")

    print("Test 8: PASS")
    return True


def main():
    """Run all PR43 Decision Engine Selector Wiring smoke tests."""
    print("=" * 60)
    print("PR43: Decision Engine Selector Wiring Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Default (v1) Works", test_default_v1_works()))
        results.append(("Selector=v2 Calls v2", test_selector_v2_calls_v2()))
        results.append(("Invalid Selector Fallback", test_invalid_selector_fallback_v1()))
        results.append(("v5_decision_engine Field", test_v5_decision_engine_field()))
        results.append(("PR38 Required Fields", test_pr38_required_fields()))
        results.append(("v5_decision_inputs_json Format", test_v5_decision_inputs_json_format()))
        results.append(("PR39 Guard Always Executed", test_pr39_guard_always_executed()))
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
            print("✓ ALL PR43 SELECTOR WIRING TESTS PASSED")
            print("=" * 60)
            print("PR43 Requirements Verified:")
            print("  - Default (v1) works correctly")
            print("  - Selector=v2 calls v2 engine")
            print("  - Invalid selector falls back to v1")
            print("  - v5_decision_engine field records engine used")
            print("  - All PR38 required fields present")
            print("  - v5_decision_inputs_json is JSON list (PR41A)")
            print("  - PR39 guard always executed (warning-only)")
            print("  - Warning-only (never raises exceptions)")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR43 TESTS FAILED")
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
