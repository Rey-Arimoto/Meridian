#!/usr/bin/env python3
"""
PR143: v1.3 Execution Gate (Always-Blocked) v1 Smoke Tests

Purpose:
    Validate v1.3 execution gate engine (draft → block reasons).

Tests:
    1. Import works
    2. Empty draft → ERROR record, gate_state BLOCKED, has REASON_INVALID_DRAFT
    3. Valid draft (SIMULATION_ONLY) → AVAILABLE, BLOCKED, includes REASON_SIMULATION_ONLY
    4. Valid draft (HUMAN_REVIEW_REQUIRED) → includes REASON_HUMAN_REVIEW_REQUIRED
    5. Draft with HARD constraint → includes REASON_HARD_CONSTRAINT
    6. Draft with SUPPRESSED constraint → includes REASON_SUPPRESSED
    7. Missing inputs_present flags → includes REASON_MISSING_INPUTS
    8. From bundle path works: bundle contains "execution_draft"
    9. Constitutional guard detects forbidden coupling phrase (warning)
    10. Defensive: never raises, exit 0 always
    11. Gate state is always BLOCKED (never ALLOW)
    12. REASON_NO_EXECUTION_LOGIC always present
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from gate import (
            build_execution_gate_from_draft_v1,
            build_execution_gate_from_bundle_v1,
            get_execution_gate_engine_v1_info,
            check_gate_record,
            V13ExecutionGateSchema,
            GATE_STATE_BLOCKED,
            REASON_INVALID_DRAFT,
            REASON_NO_ACTION_SHAPE,
            REASON_HUMAN_REVIEW_REQUIRED,
            REASON_SIMULATION_ONLY,
            REASON_CONSIDERATION_ONLY,
            REASON_HARD_CONSTRAINT,
            REASON_SUPPRESSED,
            REASON_MISSING_INPUTS,
            REASON_NO_EXECUTION_LOGIC,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_empty_draft_to_error():
    """Test 2: Empty draft → ERROR record, gate_state BLOCKED, has REASON_INVALID_DRAFT."""
    print("\nTest 2: Empty draft → ERROR record")
    try:
        from gate import build_execution_gate_from_draft_v1, GATE_STATE_BLOCKED, REASON_INVALID_DRAFT

        result = build_execution_gate_from_draft_v1(None)

        gate = result["execution_gate"]
        assert gate["v13_gate_status"] == "ERROR", "Expected ERROR status"
        assert gate["v13_gate_gate_state"] == GATE_STATE_BLOCKED, "Expected BLOCKED state"
        assert REASON_INVALID_DRAFT in gate["v13_gate_block_reasons"], "Expected REASON_INVALID_DRAFT"

        print(f"  ✓ ERROR record with BLOCKED state")
        print(f"  ✓ Block reasons: {gate['v13_gate_block_reasons']}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_simulation_only_draft():
    """Test 3: Valid draft (SIMULATION_ONLY) → AVAILABLE, BLOCKED, includes REASON_SIMULATION_ONLY."""
    print("\nTest 3: Valid draft (SIMULATION_ONLY)")
    try:
        from gate import build_execution_gate_from_draft_v1, GATE_STATE_BLOCKED, REASON_SIMULATION_ONLY

        draft = {
            "v13_draft_version": "v1",
            "v13_draft_status": "AVAILABLE",
            "v13_draft_mode": "READ_ONLY",
            "v13_draft_summary": "execution draft available.",
            "v13_draft_inputs": {"regime_record_present": "true", "drift_record_present": "true"},
            "v13_draft_constraints": {"permission": "PERMISSION_ALLOWED"},
            "v13_draft_intended_shape": {"action_class": "SIMULATION_ONLY"},
            "v13_draft_basis": [],
            "v13_draft_artifacts": [],
            "v13_draft_warnings": [],
        }

        result = build_execution_gate_from_draft_v1(draft)
        gate = result["execution_gate"]

        assert gate["v13_gate_status"] == "AVAILABLE", "Expected AVAILABLE status"
        assert gate["v13_gate_gate_state"] == GATE_STATE_BLOCKED, "Expected BLOCKED state"
        assert REASON_SIMULATION_ONLY in gate["v13_gate_block_reasons"], "Expected REASON_SIMULATION_ONLY"

        print(f"  ✓ AVAILABLE record with BLOCKED state")
        print(f"  ✓ Block reasons include REASON_SIMULATION_ONLY")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_human_review_required():
    """Test 4: Valid draft (HUMAN_REVIEW_REQUIRED) → includes REASON_HUMAN_REVIEW_REQUIRED."""
    print("\nTest 4: Valid draft (HUMAN_REVIEW_REQUIRED)")
    try:
        from gate import build_execution_gate_from_draft_v1, REASON_HUMAN_REVIEW_REQUIRED

        draft = {
            "v13_draft_version": "v1",
            "v13_draft_status": "AVAILABLE",
            "v13_draft_mode": "READ_ONLY",
            "v13_draft_summary": "execution draft available.",
            "v13_draft_inputs": {"regime_record_present": "true", "drift_record_present": "true"},
            "v13_draft_constraints": {"boundary": "BOUNDARY_REQUIRED"},
            "v13_draft_intended_shape": {"action_class": "HUMAN_REVIEW_REQUIRED"},
            "v13_draft_basis": [],
            "v13_draft_artifacts": [],
            "v13_draft_warnings": [],
        }

        result = build_execution_gate_from_draft_v1(draft)
        gate = result["execution_gate"]

        assert REASON_HUMAN_REVIEW_REQUIRED in gate["v13_gate_block_reasons"], "Expected REASON_HUMAN_REVIEW_REQUIRED"

        print(f"  ✓ Block reasons include REASON_HUMAN_REVIEW_REQUIRED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_hard_constraint():
    """Test 5: Draft with HARD constraint → includes REASON_HARD_CONSTRAINT."""
    print("\nTest 5: Draft with HARD constraint")
    try:
        from gate import build_execution_gate_from_draft_v1, REASON_HARD_CONSTRAINT

        draft = {
            "v13_draft_version": "v1",
            "v13_draft_status": "AVAILABLE",
            "v13_draft_mode": "READ_ONLY",
            "v13_draft_summary": "execution draft available.",
            "v13_draft_inputs": {"regime_record_present": "true", "drift_record_present": "true"},
            "v13_draft_constraints": {"boundary": "HARD_LIMIT"},
            "v13_draft_intended_shape": {"action_class": "SIMULATION_ONLY"},
            "v13_draft_basis": [],
            "v13_draft_artifacts": [],
            "v13_draft_warnings": [],
        }

        result = build_execution_gate_from_draft_v1(draft)
        gate = result["execution_gate"]

        assert REASON_HARD_CONSTRAINT in gate["v13_gate_block_reasons"], "Expected REASON_HARD_CONSTRAINT"

        print(f"  ✓ Block reasons include REASON_HARD_CONSTRAINT")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_suppressed_constraint():
    """Test 6: Draft with SUPPRESSED constraint → includes REASON_SUPPRESSED."""
    print("\nTest 6: Draft with SUPPRESSED constraint")
    try:
        from gate import build_execution_gate_from_draft_v1, REASON_SUPPRESSED

        draft = {
            "v13_draft_version": "v1",
            "v13_draft_status": "AVAILABLE",
            "v13_draft_mode": "READ_ONLY",
            "v13_draft_summary": "execution draft available.",
            "v13_draft_inputs": {"regime_record_present": "true", "drift_record_present": "true"},
            "v13_draft_constraints": {"permission": "PERMISSION_SUPPRESSED"},
            "v13_draft_intended_shape": {"action_class": "NO_ACTION"},
            "v13_draft_basis": [],
            "v13_draft_artifacts": [],
            "v13_draft_warnings": [],
        }

        result = build_execution_gate_from_draft_v1(draft)
        gate = result["execution_gate"]

        assert REASON_SUPPRESSED in gate["v13_gate_block_reasons"], "Expected REASON_SUPPRESSED"

        print(f"  ✓ Block reasons include REASON_SUPPRESSED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_missing_inputs():
    """Test 7: Missing inputs_present flags → includes REASON_MISSING_INPUTS."""
    print("\nTest 7: Missing inputs_present flags")
    try:
        from gate import build_execution_gate_from_draft_v1, REASON_MISSING_INPUTS

        draft = {
            "v13_draft_version": "v1",
            "v13_draft_status": "AVAILABLE",
            "v13_draft_mode": "READ_ONLY",
            "v13_draft_summary": "execution draft available.",
            "v13_draft_inputs": {},  # Missing inputs
            "v13_draft_constraints": {"permission": "PERMISSION_ALLOWED"},
            "v13_draft_intended_shape": {"action_class": "SIMULATION_ONLY"},
            "v13_draft_basis": [],
            "v13_draft_artifacts": [],
            "v13_draft_warnings": [],
        }

        result = build_execution_gate_from_draft_v1(draft)
        gate = result["execution_gate"]

        assert REASON_MISSING_INPUTS in gate["v13_gate_block_reasons"], "Expected REASON_MISSING_INPUTS"

        print(f"  ✓ Block reasons include REASON_MISSING_INPUTS")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_from_bundle_path():
    """Test 8: From bundle path works: bundle contains 'execution_draft'."""
    print("\nTest 8: From bundle path")
    try:
        from gate import build_execution_gate_from_bundle_v1, GATE_STATE_BLOCKED

        draft = {
            "v13_draft_version": "v1",
            "v13_draft_status": "AVAILABLE",
            "v13_draft_mode": "READ_ONLY",
            "v13_draft_summary": "execution draft available.",
            "v13_draft_inputs": {"regime_record_present": "true", "drift_record_present": "true"},
            "v13_draft_constraints": {"permission": "PERMISSION_ALLOWED"},
            "v13_draft_intended_shape": {"action_class": "SIMULATION_ONLY"},
            "v13_draft_basis": [],
            "v13_draft_artifacts": [],
            "v13_draft_warnings": [],
        }

        bundle = {
            "execution_draft": draft
        }

        result = build_execution_gate_from_bundle_v1(bundle)
        gate = result["execution_gate"]

        assert gate["v13_gate_gate_state"] == GATE_STATE_BLOCKED, "Expected BLOCKED state"

        print(f"  ✓ Gate from bundle works")
        print(f"  ✓ Gate state: BLOCKED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_constitutional_guard_coupling():
    """Test 9: Constitutional guard detects forbidden coupling phrase (warning)."""
    print("\nTest 9: Constitutional guard detects coupling")
    try:
        from gate import check_gate_record

        dirty_gate = {
            "v13_gate_summary": "Gate approved therefore execute trade operation.",
            "v13_gate_gate_state": "BLOCKED",
        }

        warnings = check_gate_record(dirty_gate)
        assert len(warnings) > 0, "Expected warnings for forbidden coupling"

        # Check for coupling detection
        warnings_text = " ".join(warnings).lower()
        has_coupling = "coupling" in warnings_text or "approved" in warnings_text or "execute" in warnings_text

        assert has_coupling, "Expected coupling or action warnings"

        print(f"  ✓ Constitutional guard detected forbidden patterns: {len(warnings)} warnings")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_defensive_never_raises():
    """Test 10: Defensive: never raises, exit 0 always."""
    print("\nTest 10: Defensive behavior (never raises)")
    try:
        from gate import build_execution_gate_from_draft_v1, build_execution_gate_from_bundle_v1

        # Test 10a: None draft
        result1 = build_execution_gate_from_draft_v1(None)
        assert isinstance(result1, dict), "Expected dict even with None input"
        print(f"  ✓ None draft handled defensively")

        # Test 10b: Empty dict
        result2 = build_execution_gate_from_draft_v1({})
        assert isinstance(result2, dict), "Expected dict even with empty input"
        print(f"  ✓ Empty dict handled defensively")

        # Test 10c: Invalid bundle
        result3 = build_execution_gate_from_bundle_v1(None)
        assert isinstance(result3, dict), "Expected dict even with None bundle"
        print(f"  ✓ None bundle handled defensively")

        # Test 10d: Bundle without draft
        result4 = build_execution_gate_from_bundle_v1({"other": "data"})
        assert isinstance(result4, dict), "Expected dict even without draft in bundle"
        print(f"  ✓ Bundle without draft handled defensively")

        print(f"  ✓ All invalid inputs handled without raising exceptions")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_11_gate_state_always_blocked():
    """Test 11: Gate state is always BLOCKED (never ALLOW)."""
    print("\nTest 11: Gate state is always BLOCKED")
    try:
        from gate import build_execution_gate_from_draft_v1, GATE_STATE_BLOCKED

        # Test with various draft configurations
        test_cases = [
            {"v13_draft_status": "AVAILABLE", "v13_draft_intended_shape": {"action_class": "SIMULATION_ONLY"}},
            {"v13_draft_status": "AVAILABLE", "v13_draft_intended_shape": {"action_class": "HUMAN_REVIEW_REQUIRED"}},
            {"v13_draft_status": "ERROR", "v13_draft_intended_shape": {"action_class": "NO_ACTION"}},
        ]

        for draft_config in test_cases:
            draft = {
                "v13_draft_version": "v1",
                "v13_draft_mode": "READ_ONLY",
                "v13_draft_summary": "test draft.",
                "v13_draft_inputs": {},
                "v13_draft_constraints": {},
                "v13_draft_basis": [],
                "v13_draft_artifacts": [],
                "v13_draft_warnings": [],
                **draft_config
            }

            result = build_execution_gate_from_draft_v1(draft)
            gate = result["execution_gate"]

            assert gate["v13_gate_gate_state"] == GATE_STATE_BLOCKED, f"Expected BLOCKED state, got {gate['v13_gate_gate_state']}"

        print(f"  ✓ Gate state is ALWAYS BLOCKED (tested {len(test_cases)} configurations)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_12_no_execution_logic_always_present():
    """Test 12: REASON_NO_EXECUTION_LOGIC always present."""
    print("\nTest 12: REASON_NO_EXECUTION_LOGIC always present")
    try:
        from gate import build_execution_gate_from_draft_v1, REASON_NO_EXECUTION_LOGIC

        # Test with various draft configurations
        test_cases = [
            {"action_class": "SIMULATION_ONLY"},
            {"action_class": "HUMAN_REVIEW_REQUIRED"},
            {"action_class": "NO_ACTION"},
            {"action_class": "CONSIDERATION_ONLY"},
        ]

        for intended_shape in test_cases:
            draft = {
                "v13_draft_version": "v1",
                "v13_draft_status": "AVAILABLE",
                "v13_draft_mode": "READ_ONLY",
                "v13_draft_summary": "test draft.",
                "v13_draft_inputs": {"regime_record_present": "true", "drift_record_present": "true"},
                "v13_draft_constraints": {},
                "v13_draft_intended_shape": intended_shape,
                "v13_draft_basis": [],
                "v13_draft_artifacts": [],
                "v13_draft_warnings": [],
            }

            result = build_execution_gate_from_draft_v1(draft)
            gate = result["execution_gate"]

            assert REASON_NO_EXECUTION_LOGIC in gate["v13_gate_block_reasons"], f"Expected REASON_NO_EXECUTION_LOGIC in {intended_shape}"

        print(f"  ✓ REASON_NO_EXECUTION_LOGIC ALWAYS present (tested {len(test_cases)} configurations)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR143: v1.3 Execution Gate (Always-Blocked) - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_empty_draft_to_error,
        test_3_simulation_only_draft,
        test_4_human_review_required,
        test_5_hard_constraint,
        test_6_suppressed_constraint,
        test_7_missing_inputs,
        test_8_from_bundle_path,
        test_9_constitutional_guard_coupling,
        test_10_defensive_never_raises,
        test_11_gate_state_always_blocked,
        test_12_no_execution_logic_always_present,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)

    if all(results):
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
