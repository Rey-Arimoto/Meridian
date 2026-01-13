#!/usr/bin/env python3
"""
PR142: v1.3 Approval Packet → Execution Draft Binding v1 Smoke Tests

Purpose:
    Validate v1.3 binding engine for packet → draft mapping.

Tests:
    1. Import works
    2. Bind from artifact bundle → returns dict, no exception
    3. Bind from approval packet → returns dict, no exception
    4. Intended shape mapping (INELIGIBLE → NO_ACTION)
    5. Intended shape mapping (REQUIRED → HUMAN_REVIEW_REQUIRED)
    6. Intended shape mapping (default → SIMULATION_ONLY)
    7. Label-only projection (no numeric values)
    8. Source presence only (inputs are flags, not values)
    9. Invalid inputs → ERROR records defensively
    10. Schema validation passes
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from bind import (
            build_execution_draft_from_bundle_v1,
            build_execution_draft_from_packet_v1,
            get_binding_engine_v1_info,
            check_binding_output,
            check_label_only_constraints,
            check_source_presence_only_inputs,
            check_intended_shape_structural,
            VALID_ACTION_CLASSES,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_bind_from_artifact_bundle():
    """Test 2: Bind from artifact bundle → returns dict, no exception."""
    print("\nTest 2: Bind from artifact bundle")
    try:
        from bind import build_execution_draft_from_bundle_v1

        artifact_bundle = {
            "artifacts": {
                "regime_record": {"v11_regime_level": "REGIME_MEDIUM"},
                "drift_record": {"v10_drift_level": "DRIFT_LOW"},
                "permission_record": {"v10_permission_label": "PERMISSION_ALLOWED"},
                "trajectory_record": {"v11_trajectory_signal": "IMPROVING"},
                "eligibility_record": {"v11_eligibility_label": "ELIGIBLE"},
            }
        }

        result = build_execution_draft_from_bundle_v1(artifact_bundle)

        assert isinstance(result, dict), "Expected dict result"
        assert "execution_draft" in result, "Expected execution_draft key"
        assert "warnings" in result, "Expected warnings key"

        draft = result["execution_draft"]
        assert draft["v13_draft_status"] in ["AVAILABLE", "ERROR"], "Expected AVAILABLE or ERROR"

        print(f"  ✓ Returns dict with all expected keys")
        print(f"  ✓ Draft status: {draft['v13_draft_status']}")
        print(f"  ✓ Warnings: {len(result['warnings'])}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_bind_from_approval_packet():
    """Test 3: Bind from approval packet → returns dict, no exception."""
    print("\nTest 3: Bind from approval packet")
    try:
        from bind import build_execution_draft_from_packet_v1

        approval_packet = {
            "v11_packet_status": "AVAILABLE",
            "v11_packet_permission_label": "PERMISSION_ALLOWED",
            "v11_packet_trajectory_signal": "IMPROVING",
            "v11_packet_eligibility_label": "ELIGIBLE",
            "v11_packet_artifacts": ["regime_record", "drift_record"],
        }

        result = build_execution_draft_from_packet_v1(approval_packet)

        assert isinstance(result, dict), "Expected dict result"
        assert "execution_draft" in result, "Expected execution_draft key"
        assert "warnings" in result, "Expected warnings key"

        draft = result["execution_draft"]
        assert draft["v13_draft_status"] in ["AVAILABLE", "ERROR"], "Expected AVAILABLE or ERROR"

        print(f"  ✓ Returns dict with all expected keys")
        print(f"  ✓ Draft status: {draft['v13_draft_status']}")
        print(f"  ✓ Warnings: {len(result['warnings'])}")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_intended_shape_ineligible():
    """Test 4: Intended shape mapping (INELIGIBLE → NO_ACTION)."""
    print("\nTest 4: Intended shape mapping (INELIGIBLE → NO_ACTION)")
    try:
        from bind import build_execution_draft_from_bundle_v1

        bundle = {
            "artifacts": {
                "regime_record": {"v11_regime_level": "REGIME_MEDIUM"},
                "drift_record": {"v10_drift_level": "DRIFT_LOW"},
                "eligibility_record": {"v11_eligibility_label": "INELIGIBLE"},
            }
        }

        result = build_execution_draft_from_bundle_v1(bundle)
        draft = result["execution_draft"]

        intended_shape = draft["v13_draft_intended_shape"]
        action_class = intended_shape.get("action_class")

        assert action_class == "NO_ACTION", f"Expected NO_ACTION, got {action_class}"

        print(f"  ✓ INELIGIBLE mapped to NO_ACTION")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_intended_shape_required():
    """Test 5: Intended shape mapping (REQUIRED → HUMAN_REVIEW_REQUIRED)."""
    print("\nTest 5: Intended shape mapping (REQUIRED → HUMAN_REVIEW_REQUIRED)")
    try:
        from bind import build_execution_draft_from_bundle_v1

        bundle = {
            "artifacts": {
                "regime_record": {"v11_regime_level": "REGIME_MEDIUM"},
                "drift_record": {"v10_drift_level": "DRIFT_LOW"},
                "boundary_record": {"v11_boundary_signal": "BOUNDARY_REQUIRED"},
            }
        }

        result = build_execution_draft_from_bundle_v1(bundle)
        draft = result["execution_draft"]

        intended_shape = draft["v13_draft_intended_shape"]
        action_class = intended_shape.get("action_class")

        assert action_class == "HUMAN_REVIEW_REQUIRED", f"Expected HUMAN_REVIEW_REQUIRED, got {action_class}"

        print(f"  ✓ REQUIRED mapped to HUMAN_REVIEW_REQUIRED")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_intended_shape_default():
    """Test 6: Intended shape mapping (default → SIMULATION_ONLY)."""
    print("\nTest 6: Intended shape mapping (default → SIMULATION_ONLY)")
    try:
        from bind import build_execution_draft_from_bundle_v1

        bundle = {
            "artifacts": {
                "regime_record": {"v11_regime_level": "REGIME_MEDIUM"},
                "drift_record": {"v10_drift_level": "DRIFT_LOW"},
                "permission_record": {"v10_permission_label": "PERMISSION_ALLOWED"},
                "eligibility_record": {"v11_eligibility_label": "ELIGIBLE"},
            }
        }

        result = build_execution_draft_from_bundle_v1(bundle)
        draft = result["execution_draft"]

        intended_shape = draft["v13_draft_intended_shape"]
        action_class = intended_shape.get("action_class")

        assert action_class == "SIMULATION_ONLY", f"Expected SIMULATION_ONLY, got {action_class}"

        print(f"  ✓ Default mapped to SIMULATION_ONLY")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_label_only_projection():
    """Test 7: Label-only projection (no numeric values)."""
    print("\nTest 7: Label-only projection (no numeric values)")
    try:
        from bind import build_execution_draft_from_bundle_v1

        bundle = {
            "artifacts": {
                "regime_record": {"v11_regime_level": "REGIME_MEDIUM"},
                "drift_record": {"v10_drift_level": "DRIFT_LOW"},
                "permission_record": {"v10_permission_label": "PERMISSION_ALLOWED"},
            }
        }

        result = build_execution_draft_from_bundle_v1(bundle)
        draft = result["execution_draft"]

        # Check that constraints are label-only
        constraints = draft["v13_draft_constraints"]
        for key, value in constraints.items():
            # Should be string labels, not numeric values
            assert isinstance(value, str), f"Constraint '{key}' should be string, got {type(value)}"
            # Should not contain large numeric patterns
            import re
            assert not re.search(r'\d{4,}', value), f"Constraint '{key}' contains numeric pattern: {value}"

        print(f"  ✓ Constraints are label-only (no numeric values)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_source_presence_only():
    """Test 8: Source presence only (inputs are flags, not values)."""
    print("\nTest 8: Source presence only (inputs are flags, not values)")
    try:
        from bind import build_execution_draft_from_bundle_v1

        bundle = {
            "artifacts": {
                "regime_record": {"v11_regime_level": "REGIME_MEDIUM"},
                "drift_record": {"v10_drift_level": "DRIFT_LOW"},
            }
        }

        result = build_execution_draft_from_bundle_v1(bundle)
        draft = result["execution_draft"]

        # Check that inputs are source presence flags only
        inputs = draft["v13_draft_inputs"]
        for key, value in inputs.items():
            # Should be string presence flags like "true" or status labels
            assert isinstance(value, str), f"Input '{key}' should be string, got {type(value)}"
            # Should not contain large numeric patterns (addresses, amounts, etc.)
            import re
            assert not re.search(r'\d{4,}', value), f"Input '{key}' contains numeric pattern: {value}"

        print(f"  ✓ Inputs are source presence only (no values)")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_invalid_inputs_defensive():
    """Test 9: Invalid inputs → ERROR records defensively."""
    print("\nTest 9: Invalid inputs → ERROR records defensively")
    try:
        from bind import build_execution_draft_from_bundle_v1, build_execution_draft_from_packet_v1

        # Test 9a: None input for bundle
        result_none = build_execution_draft_from_bundle_v1(None)
        assert isinstance(result_none, dict), "Expected dict even with None input"
        assert result_none["execution_draft"]["v13_draft_status"] == "ERROR", "Expected ERROR status"
        print(f"  ✓ None bundle input handled defensively")

        # Test 9b: Empty dict for bundle
        result_empty = build_execution_draft_from_bundle_v1({})
        assert isinstance(result_empty, dict), "Expected dict even with empty input"
        print(f"  ✓ Empty bundle handled defensively")

        # Test 9c: None input for packet
        result_packet_none = build_execution_draft_from_packet_v1(None)
        assert isinstance(result_packet_none, dict), "Expected dict even with None input"
        assert result_packet_none["execution_draft"]["v13_draft_status"] == "ERROR", "Expected ERROR status"
        print(f"  ✓ None packet input handled defensively")

        # Test 9d: Packet with non-AVAILABLE status
        result_packet_error = build_execution_draft_from_packet_v1({"v11_packet_status": "ERROR"})
        assert isinstance(result_packet_error, dict), "Expected dict even with ERROR packet"
        assert result_packet_error["execution_draft"]["v13_draft_status"] == "ERROR", "Expected ERROR status"
        print(f"  ✓ ERROR packet handled defensively")

        print(f"  ✓ All invalid inputs handled without raising exceptions")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_schema_validation():
    """Test 10: Schema validation passes."""
    print("\nTest 10: Schema validation passes")
    try:
        from bind import build_execution_draft_from_bundle_v1
        from draft import V13ExecutionDraftSchema

        bundle = {
            "artifacts": {
                "regime_record": {"v11_regime_level": "REGIME_MEDIUM"},
                "drift_record": {"v10_drift_level": "DRIFT_LOW"},
                "permission_record": {"v10_permission_label": "PERMISSION_ALLOWED"},
                "eligibility_record": {"v11_eligibility_label": "ELIGIBLE"},
            }
        }

        result = build_execution_draft_from_bundle_v1(bundle)
        draft = result["execution_draft"]

        # Validate against PR141 schema
        errors = V13ExecutionDraftSchema.validate_draft_record(draft)
        assert len(errors) == 0, f"Expected no schema errors, got {len(errors)}: {errors}"

        print(f"  ✓ Draft record validates against PR141 schema")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR142: v1.3 Packet → Draft Binding Engine - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_bind_from_artifact_bundle,
        test_3_bind_from_approval_packet,
        test_4_intended_shape_ineligible,
        test_5_intended_shape_required,
        test_6_intended_shape_default,
        test_7_label_only_projection,
        test_8_source_presence_only,
        test_9_invalid_inputs_defensive,
        test_10_schema_validation,
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
