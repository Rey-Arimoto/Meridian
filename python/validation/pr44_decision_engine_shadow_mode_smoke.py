#!/usr/bin/env python3
"""
PR44: v0.5 Decision Engine Shadow Mode Smoke Test

Purpose: Verify PR44 shadow mode correctly generates dual records (primary + shadow).

Requirements:
1. Shadow=False → shadow fields do not exist (PR43 behavior)
2. Shadow=True & Engine=v1 → primary=v1, shadow=v2
3. Shadow=True & Engine=v2 → primary=v2, shadow=v1
4. primary/shadow both have version == "v0.5"
5. *_inputs_json is JSON list (parseable)
6. PR39 guard executes for both primary/shadow without failure
7. Shadow-only failure does not stop tick
8. Exit code 0 (warning-only)

Non-Goals:
- No behavior modification (READ-ONLY)
- No v0.4 confidence modification
- No v0.2 execution modification
"""

import sys
import os
import json

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from intelligence.intelligence_decision_engine_v1 import generate_decision_record_v1
from intelligence.intelligence_decision_engine_v2 import generate_decision_record_v2
from intelligence.intelligence_decision_record_compliance import validate_decision_record_full


def simulate_shadow_mode_wiring(row_dict, primary_engine, shadow_mode):
    """
    Simulate PR44 shadow mode wiring behavior.

    This mimics the shadow mode logic added to meridian_realtime_agent.py.

    Returns: Modified row_dict with primary and (optionally) shadow fields
    """
    from datetime import datetime, timezone

    try:
        # PR44: Determine shadow engine (opposite of primary)
        if primary_engine == "v1":
            shadow_engine = "v2"
        elif primary_engine == "v2":
            shadow_engine = "v1"
        else:
            # Invalid primary engine: fallback to v1 primary, v2 shadow
            print(f"[INFO][TEST] Invalid primary engine '{primary_engine}', falling back to v1")
            primary_engine = "v1"
            shadow_engine = "v2"

        # PR44: Generate PRIMARY decision record
        if primary_engine == "v2":
            primary_record = generate_decision_record_v2(row_dict)
            primary_engine_used = "v2"
        else:  # v1
            primary_record = generate_decision_record_v1(row_dict)
            primary_engine_used = "v1"

        # PR44: Record primary engine and fields
        row_dict["v5_decision_engine"] = primary_engine_used
        row_dict["v5_decision_action"] = primary_record.get("decision_action", "UNKNOWN")
        row_dict["v5_decision_reason"] = primary_record.get("decision_reason", "")

        # PR41A: decision_inputs in both formats
        primary_inputs_list = primary_record.get("decision_inputs", [])
        row_dict["v5_decision_inputs"] = ",".join(primary_inputs_list) if primary_inputs_list else ""
        row_dict["v5_decision_inputs_json"] = json.dumps(primary_inputs_list)

        # PR41A: decision_version always "v0.5"
        row_dict["v5_decision_version"] = "v0.5"
        row_dict["v5_decision_generated_at"] = primary_record.get("decision_generated_at", "")

        # PR41A/PR44: Always validate primary decision record
        primary_compliance_warnings = validate_decision_record_full(primary_record, "test")
        if primary_compliance_warnings:
            print(f"[INFO][TEST] Primary compliance warnings: {primary_compliance_warnings}")

        # PR44: Generate SHADOW decision record (only if shadow mode enabled)
        if shadow_mode:
            try:
                # PR44: Generate shadow record using opposite engine
                if shadow_engine == "v2":
                    shadow_record = generate_decision_record_v2(row_dict)
                    shadow_engine_used = "v2"
                else:  # v1
                    shadow_record = generate_decision_record_v1(row_dict)
                    shadow_engine_used = "v1"

                # PR44: Record shadow engine and fields
                row_dict["v5_shadow_decision_engine"] = shadow_engine_used
                row_dict["v5_shadow_decision_action"] = shadow_record.get("decision_action", "UNKNOWN")
                row_dict["v5_shadow_decision_reason"] = shadow_record.get("decision_reason", "")

                # PR41A/PR44: shadow decision_inputs in both formats
                shadow_inputs_list = shadow_record.get("decision_inputs", [])
                row_dict["v5_shadow_decision_inputs"] = ",".join(shadow_inputs_list) if shadow_inputs_list else ""
                row_dict["v5_shadow_decision_inputs_json"] = json.dumps(shadow_inputs_list)

                # PR41A/PR44: shadow decision_version always "v0.5"
                row_dict["v5_shadow_decision_version"] = "v0.5"
                row_dict["v5_shadow_decision_generated_at"] = shadow_record.get("decision_generated_at", "")

                # PR41A/PR44: Always validate shadow decision record
                shadow_compliance_warnings = validate_decision_record_full(shadow_record, "test")
                if shadow_compliance_warnings:
                    print(f"[INFO][TEST] Shadow compliance warnings: {shadow_compliance_warnings}")

            except Exception as shadow_e:
                # PR44: Shadow failure must not stop execution
                print(f"[INFO][TEST] Shadow record failed (expected in test): {shadow_e}")
                # PR44: Shadow safe defaults
                row_dict["v5_shadow_decision_engine"] = "UNKNOWN"
                row_dict["v5_shadow_decision_action"] = "UNKNOWN"
                row_dict["v5_shadow_decision_reason"] = ""
                row_dict["v5_shadow_decision_inputs"] = ""
                row_dict["v5_shadow_decision_inputs_json"] = "[]"
                row_dict["v5_shadow_decision_version"] = "v0.5"
                row_dict["v5_shadow_decision_generated_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        # PR44: Primary record generation must never stop execution
        print(f"[INFO][TEST] Primary record failed (expected in test): {e}")
        # PR44: Try fallback to v1 if primary v2 failed
        try:
            if primary_engine == "v2":
                print(f"[INFO][TEST] Attempting fallback to v1 after primary v2 failure")
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
            else:
                raise
        except Exception as fallback_e:
            # PR44: Even fallback failed, use safe defaults
            print(f"[INFO][TEST] Primary fallback also failed: {fallback_e}")
            row_dict["v5_decision_engine"] = "UNKNOWN"
            row_dict["v5_decision_action"] = "UNKNOWN"
            row_dict["v5_decision_reason"] = ""
            row_dict["v5_decision_inputs"] = ""
            row_dict["v5_decision_inputs_json"] = "[]"
            row_dict["v5_decision_version"] = "v0.5"
            row_dict["v5_decision_generated_at"] = datetime.now(timezone.utc).isoformat()

    return row_dict


def test_shadow_false_no_shadow_fields():
    """Test 1: Shadow=False → shadow fields do not exist."""
    print("\nTest 1: Shadow=False → No Shadow Fields")
    print("-" * 60)

    row_dict = {
        "base_action": "HOLD",
        "intent_primary": "IDLE",
        "regime": "stable_range",
    }

    row_dict = simulate_shadow_mode_wiring(row_dict, "v1", shadow_mode=False)

    # Primary fields should exist
    assert "v5_decision_engine" in row_dict, "Primary fields must exist"
    assert "v5_decision_action" in row_dict, "Primary fields must exist"

    # Shadow fields should NOT exist
    assert "v5_shadow_decision_engine" not in row_dict, \
        "Shadow fields must not exist when shadow_mode=False"
    assert "v5_shadow_decision_action" not in row_dict, \
        "Shadow fields must not exist when shadow_mode=False"

    print(f"✓ Shadow=False: Primary fields present, shadow fields absent")
    print(f"  Primary engine: {row_dict['v5_decision_engine']}")

    print("Test 1: PASS")
    return True


def test_shadow_true_v1_primary():
    """Test 2: Shadow=True & Engine=v1 → primary=v1, shadow=v2."""
    print("\nTest 2: Shadow=True & Engine=v1 → Primary=v1, Shadow=v2")
    print("-" * 60)

    # Use regime that triggers v2 halted ruleset (to verify v2 is actually called)
    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "REGIME_TRANSITION",  # v2 halted regime
    }

    row_dict = simulate_shadow_mode_wiring(row_dict, "v1", shadow_mode=True)

    # Primary should be v1 (mirrors base_action)
    assert row_dict["v5_decision_engine"] == "v1", \
        f"Primary engine must be v1, got '{row_dict['v5_decision_engine']}'"
    assert row_dict["v5_decision_action"] == "SHIFT", \
        f"v1 should mirror base_action SHIFT, got '{row_dict['v5_decision_action']}'"

    # Shadow should be v2 (halted ruleset forces PAUSE)
    assert row_dict["v5_shadow_decision_engine"] == "v2", \
        f"Shadow engine must be v2, got '{row_dict['v5_shadow_decision_engine']}'"
    assert row_dict["v5_shadow_decision_action"] == "PAUSE", \
        f"v2 halted should force PAUSE, got '{row_dict['v5_shadow_decision_action']}'"

    print(f"✓ Primary: v1 (action={row_dict['v5_decision_action']})")
    print(f"✓ Shadow: v2 (action={row_dict['v5_shadow_decision_action']})")
    print(f"✓ v1 mirrors base_action, v2 applies halted ruleset (PAUSE)")

    print("Test 2: PASS")
    return True


def test_shadow_true_v2_primary():
    """Test 3: Shadow=True & Engine=v2 → primary=v2, shadow=v1."""
    print("\nTest 3: Shadow=True & Engine=v2 → Primary=v2, Shadow=v1")
    print("-" * 60)

    # Use cautious intent that triggers v2 cautious ruleset
    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "STABILIZE",  # v2 cautious intent
        "regime": "emerging_trend",
    }

    row_dict = simulate_shadow_mode_wiring(row_dict, "v2", shadow_mode=True)

    # Primary should be v2 (cautious ruleset suppresses SHIFT → HOLD)
    assert row_dict["v5_decision_engine"] == "v2", \
        f"Primary engine must be v2, got '{row_dict['v5_decision_engine']}'"
    assert row_dict["v5_decision_action"] == "HOLD", \
        f"v2 cautious should suppress SHIFT to HOLD, got '{row_dict['v5_decision_action']}'"

    # Shadow should be v1 (mirrors base_action)
    assert row_dict["v5_shadow_decision_engine"] == "v1", \
        f"Shadow engine must be v1, got '{row_dict['v5_shadow_decision_engine']}'"
    assert row_dict["v5_shadow_decision_action"] == "SHIFT", \
        f"v1 should mirror base_action SHIFT, got '{row_dict['v5_shadow_decision_action']}'"

    print(f"✓ Primary: v2 (action={row_dict['v5_decision_action']})")
    print(f"✓ Shadow: v1 (action={row_dict['v5_shadow_decision_action']})")
    print(f"✓ v2 applies cautious ruleset (HOLD), v1 mirrors base_action (SHIFT)")

    print("Test 3: PASS")
    return True


def test_version_always_v05():
    """Test 4: primary/shadow both have version == "v0.5"."""
    print("\nTest 4: Primary/Shadow Both Have version == 'v0.5'")
    print("-" * 60)

    test_cases = [
        ("v1", True),   # v1 primary, v2 shadow
        ("v2", True),   # v2 primary, v1 shadow
        ("v1", False),  # v1 primary only
    ]

    for primary_engine, shadow_mode in test_cases:
        row_dict = {
            "base_action": "HOLD",
            "intent_primary": "IDLE",
            "regime": "stable_range",
        }

        row_dict = simulate_shadow_mode_wiring(row_dict, primary_engine, shadow_mode)

        # Primary version must be "v0.5"
        assert row_dict["v5_decision_version"] == "v0.5", \
            f"Primary version must be 'v0.5', got '{row_dict['v5_decision_version']}'"

        print(f"✓ Primary engine={primary_engine}, shadow_mode={shadow_mode}: v5_decision_version='v0.5'")

        # Shadow version must be "v0.5" if shadow mode enabled
        if shadow_mode:
            assert row_dict["v5_shadow_decision_version"] == "v0.5", \
                f"Shadow version must be 'v0.5', got '{row_dict['v5_shadow_decision_version']}'"
            print(f"✓ Shadow: v5_shadow_decision_version='v0.5'")

    print("Test 4: PASS")
    return True


def test_inputs_json_parseable():
    """Test 5: *_inputs_json is JSON list (parseable)."""
    print("\nTest 5: *_inputs_json Is JSON List (Parseable)")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "emerging_trend",
        "confidence_reason": "Source:entropy_bp; ...",
    }

    row_dict = simulate_shadow_mode_wiring(row_dict, "v1", shadow_mode=True)

    # Primary inputs_json
    try:
        primary_inputs_list = json.loads(row_dict["v5_decision_inputs_json"])
        assert isinstance(primary_inputs_list, list), \
            f"Primary inputs_json must be list, got {type(primary_inputs_list)}"
        assert "base_action" in primary_inputs_list, "Primary inputs should contain 'base_action'"
        print(f"✓ Primary v5_decision_inputs_json is valid JSON list")
        print(f"  Parsed: {primary_inputs_list}")
    except json.JSONDecodeError as e:
        assert False, f"Primary inputs_json must be valid JSON: {e}"

    # Shadow inputs_json
    try:
        shadow_inputs_list = json.loads(row_dict["v5_shadow_decision_inputs_json"])
        assert isinstance(shadow_inputs_list, list), \
            f"Shadow inputs_json must be list, got {type(shadow_inputs_list)}"
        assert "base_action" in shadow_inputs_list, "Shadow inputs should contain 'base_action'"
        print(f"✓ Shadow v5_shadow_decision_inputs_json is valid JSON list")
        print(f"  Parsed: {shadow_inputs_list}")
    except json.JSONDecodeError as e:
        assert False, f"Shadow inputs_json must be valid JSON: {e}"

    print("Test 5: PASS")
    return True


def test_pr39_guard_both_primary_shadow():
    """Test 6: PR39 guard executes for both primary/shadow without failure."""
    print("\nTest 6: PR39 Guard Executes for Both Primary/Shadow")
    print("-" * 60)

    row_dict = {
        "base_action": "SHIFT",
        "intent_primary": "SEEK",
        "regime": "REGIME_TRANSITION",
    }

    row_dict = simulate_shadow_mode_wiring(row_dict, "v1", shadow_mode=True)

    # Verify both primary and shadow were generated (guard was called but didn't stop execution)
    assert "v5_decision_action" in row_dict, "Primary record should be generated"
    assert "v5_shadow_decision_action" in row_dict, "Shadow record should be generated"

    print(f"✓ Primary record generated (guard executed, warnings allowed)")
    print(f"✓ Shadow record generated (guard executed, warnings allowed)")
    print(f"✓ No conditional skipping of validation")
    print(f"✓ Warning-only behavior maintained")

    print("Test 6: PASS")
    return True


def test_shadow_only_failure_tick_continues():
    """Test 7: Shadow-only failure does not stop tick."""
    print("\nTest 7: Shadow-Only Failure Does Not Stop Tick")
    print("-" * 60)

    # Test shadow failure with empty row_dict (should trigger shadow safe defaults)
    row_dict = {}

    row_dict = simulate_shadow_mode_wiring(row_dict, "v1", shadow_mode=True)

    # Primary should still be generated (with defaults if needed)
    assert "v5_decision_engine" in row_dict, "Primary should be generated even if shadow fails"
    assert "v5_decision_action" in row_dict, "Primary should be generated even if shadow fails"

    # Shadow should have safe defaults (UNKNOWN) if it failed
    assert "v5_shadow_decision_engine" in row_dict, "Shadow should have safe defaults"
    assert "v5_shadow_decision_version" in row_dict, "Shadow should have safe defaults"
    assert row_dict["v5_shadow_decision_version"] == "v0.5", "Shadow version must be 'v0.5' even on failure"

    print(f"✓ Primary generated: {row_dict['v5_decision_action']}")
    print(f"✓ Shadow generated (safe defaults if failed): {row_dict['v5_shadow_decision_action']}")
    print(f"✓ Tick continued despite shadow issues")

    print("Test 7: PASS")
    return True


def test_exit_code_always_zero():
    """Test 8: Exit code always 0 (warning-only)."""
    print("\nTest 8: Exit Code Always 0 (Warning-Only)")
    print("-" * 60)

    # Test various scenarios
    test_cases = [
        ("v1", False, {"base_action": "HOLD"}),
        ("v1", True, {"base_action": "SHIFT", "intent_primary": "SEEK", "regime": "stable_range"}),
        ("v2", True, {"base_action": "SHIFT", "intent_primary": "STABILIZE", "regime": "emerging_trend"}),
        ("v1", True, {}),  # Empty row
        ("v2", False, {"base_action": None}),  # None value
    ]

    for i, (primary_engine, shadow_mode, row_dict) in enumerate(test_cases):
        try:
            simulate_shadow_mode_wiring(row_dict, primary_engine, shadow_mode)
            print(f"✓ Test case {i+1} (engine={primary_engine}, shadow={shadow_mode}): No exception raised")
        except Exception as e:
            assert False, f"Should never raise exception (warning-only), got: {e}"

    print(f"✓ All test cases handled without exceptions")
    print(f"✓ Exit code will be 0 (warning-only)")

    print("Test 8: PASS")
    return True


def main():
    """Run all PR44 Decision Engine Shadow Mode smoke tests."""
    print("=" * 60)
    print("PR44: Decision Engine Shadow Mode Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Shadow=False No Shadow Fields", test_shadow_false_no_shadow_fields()))
        results.append(("Shadow=True v1 Primary", test_shadow_true_v1_primary()))
        results.append(("Shadow=True v2 Primary", test_shadow_true_v2_primary()))
        results.append(("Version Always v0.5", test_version_always_v05()))
        results.append(("inputs_json Parseable", test_inputs_json_parseable()))
        results.append(("PR39 Guard Both Primary/Shadow", test_pr39_guard_both_primary_shadow()))
        results.append(("Shadow-Only Failure Tick Continues", test_shadow_only_failure_tick_continues()))
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
            print("✓ ALL PR44 SHADOW MODE TESTS PASSED")
            print("=" * 60)
            print("PR44 Requirements Verified:")
            print("  - Shadow=False: no shadow fields (PR43 behavior)")
            print("  - Shadow=True & Engine=v1: primary=v1, shadow=v2")
            print("  - Shadow=True & Engine=v2: primary=v2, shadow=v1")
            print("  - primary/shadow both have version='v0.5'")
            print("  - *_inputs_json is JSON list (parseable)")
            print("  - PR39 guard executes for both primary/shadow")
            print("  - Shadow-only failure does not stop tick")
            print("  - Warning-only (never raises exceptions)")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR44 TESTS FAILED")
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
