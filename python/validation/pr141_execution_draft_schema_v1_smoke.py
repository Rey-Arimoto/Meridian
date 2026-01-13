#!/usr/bin/env python3
"""
PR141: v1.3 Execution Draft Schema v1 Smoke Tests

Purpose:
    Validate execution draft schema and constitutional guards.

Tests:
    1. Import works
    2. Empty → ERROR record validates
    3. Valid AVAILABLE record validates
    4. Forbidden vocab detection
    5. Token literal detection
    6. Numeric pattern detection (addresses)
    7. Coupling detection
    8. Warning-only behavior (exit 0)
    9. Schema validation catches missing fields
    10. Action class validation
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from draft import (
            V13ExecutionDraftSchema,
            get_draft_schema_info,
            check_draft_record,
            DRAFT_VERSION_V1,
            DRAFT_STATUS_AVAILABLE,
            DRAFT_STATUS_ERROR,
            DRAFT_MODE_READ_ONLY,
            ACTION_CLASS_NONE,
            ACTION_CLASS_DRAFT_ONLY,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_empty_to_error_record():
    """Test 2: Empty → ERROR record validates."""
    print("\nTest 2: Empty → ERROR record validates")
    try:
        from draft import V13ExecutionDraftSchema, DRAFT_STATUS_ERROR

        error_record = V13ExecutionDraftSchema.create_error_record(
            summary="no approval packet provided."
        )

        assert error_record["v13_draft_status"] == DRAFT_STATUS_ERROR, "Expected ERROR status"

        errors = V13ExecutionDraftSchema.validate_draft_record(error_record)
        assert len(errors) == 0, f"Expected no validation errors, got {len(errors)}"

        print(f"  ✓ ERROR record validates correctly")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_valid_available_record():
    """Test 3: Valid AVAILABLE record validates."""
    print("\nTest 3: Valid AVAILABLE record validates")
    try:
        from draft import V13ExecutionDraftSchema, DRAFT_STATUS_AVAILABLE, ACTION_CLASS_DRAFT_ONLY

        record = V13ExecutionDraftSchema.create_draft_record(
            status=DRAFT_STATUS_AVAILABLE,
            summary="execution draft available.",
            inputs={"packet_id": "approval_packet_v1"},
            constraints={"permission": "ALLOWED", "eligibility": "ELIGIBLE"},
            intended_shape={"action_class": ACTION_CLASS_DRAFT_ONLY},
            basis=["v13_approval_packet"],
        )

        assert record["v13_draft_status"] == DRAFT_STATUS_AVAILABLE, "Expected AVAILABLE status"

        errors = V13ExecutionDraftSchema.validate_draft_record(record)
        assert len(errors) == 0, f"Expected no validation errors, got {len(errors)}"

        print(f"  ✓ AVAILABLE record validates correctly")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_forbidden_vocab_detection():
    """Test 4: Forbidden vocab detection."""
    print("\nTest 4: Forbidden vocab detection")
    try:
        from draft import check_draft_record

        dirty_record = {
            "v13_draft_summary": "System must execute swap operation.",
        }

        warnings = check_draft_record(dirty_record)
        assert len(warnings) > 0, "Expected warnings for forbidden vocab"

        # Check for prescriptive and trading vocabulary
        warnings_text = " ".join(warnings).lower()
        has_prescriptive = "must" in warnings_text or "prescriptive" in warnings_text
        has_trading = "swap" in warnings_text or "trading" in warnings_text

        assert has_prescriptive or has_trading, "Expected prescriptive or trading warnings"

        print(f"  ✓ Forbidden vocab detected: {len(warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_token_literal_detection():
    """Test 5: Token literal detection."""
    print("\nTest 5: Token literal detection")
    try:
        from draft import check_draft_record

        dirty_record = {
            "v13_draft_summary": "Draft references SUI and USDC tokens.",
        }

        warnings = check_draft_record(dirty_record)
        assert len(warnings) > 0, "Expected warnings for token literals"

        # Check for SUI and USDC detection
        warnings_text = " ".join(warnings)
        assert "SUI" in warnings_text or "USDC" in warnings_text, "Expected token literal warnings"

        print(f"  ✓ Token literals detected: {len(warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_numeric_pattern_detection():
    """Test 6: Numeric pattern detection (addresses)."""
    print("\nTest 6: Numeric pattern detection (addresses)")
    try:
        from draft import check_draft_record

        dirty_record = {
            "v13_draft_summary": "Draft references address 0x1234567890abcdef.",
        }

        warnings = check_draft_record(dirty_record)
        assert len(warnings) > 0, "Expected warnings for address patterns"

        # Check for address detection
        warnings_text = " ".join(warnings).lower()
        assert "address" in warnings_text or "0x" in warnings_text, "Expected address pattern warnings"

        print(f"  ✓ Address patterns detected: {len(warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_coupling_detection():
    """Test 7: Coupling detection."""
    print("\nTest 7: Coupling detection")
    try:
        from draft import check_draft_record

        dirty_record = {
            "v13_draft_summary": "Approved therefore execute. Eligible so trade.",
        }

        warnings = check_draft_record(dirty_record)
        assert len(warnings) > 0, "Expected warnings for coupling"

        # Check for coupling detection
        warnings_text = " ".join(warnings).lower()
        has_coupling = "coupling" in warnings_text or "therefore" in warnings_text or "so" in warnings_text

        assert has_coupling, "Expected coupling warnings"

        print(f"  ✓ Coupling detected: {len(warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_warning_only_behavior():
    """Test 8: Warning-only behavior (exit 0)."""
    print("\nTest 8: Warning-only behavior (exit 0)")
    try:
        from draft import check_draft_record

        # Very dirty record with multiple violations
        dirty_record = {
            "v13_draft_summary": "Approved therefore execute SUI swap at 0x123. Must trade USDC.",
        }

        # Should return warnings, not raise exception
        warnings = check_draft_record(dirty_record)
        assert len(warnings) > 0, "Expected warnings"

        print(f"  ✓ Guards emit warnings (not errors): {len(warnings)} warnings")
        print(f"    Example warnings:")
        for w in warnings[:3]:
            print(f"      - {w}")

        print(f"  ✓ Warning-only behavior verified (no exceptions raised)")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_schema_validation_missing_fields():
    """Test 9: Schema validation catches missing fields."""
    print("\nTest 9: Schema validation catches missing fields")
    try:
        from draft import V13ExecutionDraftSchema

        # Invalid record with missing fields
        invalid_record = {
            "v13_draft_version": "v1",
            "v13_draft_status": "AVAILABLE",
        }

        errors = V13ExecutionDraftSchema.validate_draft_record(invalid_record)
        assert len(errors) > 0, "Expected validation errors for missing fields"

        # Check that required fields are detected
        errors_text = " ".join(errors).lower()
        assert "missing" in errors_text, "Expected 'missing' in error messages"

        print(f"  ✓ Missing fields detected: {len(errors)} errors")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_action_class_validation():
    """Test 10: Action class validation."""
    print("\nTest 10: Action class validation")
    try:
        from draft import V13ExecutionDraftSchema, ACTION_CLASS_NONE, ACTION_CLASS_DRAFT_ONLY

        # Valid action class: NONE
        record1 = V13ExecutionDraftSchema.create_draft_record(
            summary="draft with NONE action class.",
            intended_shape={"action_class": ACTION_CLASS_NONE},
        )
        errors1 = V13ExecutionDraftSchema.validate_draft_record(record1)
        assert len(errors1) == 0, f"Expected no errors for NONE action class, got {len(errors1)}"
        print(f"  ✓ ACTION_CLASS_NONE validates")

        # Valid action class: DRAFT_ONLY
        record2 = V13ExecutionDraftSchema.create_draft_record(
            summary="draft with DRAFT_ONLY action class.",
            intended_shape={"action_class": ACTION_CLASS_DRAFT_ONLY},
        )
        errors2 = V13ExecutionDraftSchema.validate_draft_record(record2)
        assert len(errors2) == 0, f"Expected no errors for DRAFT_ONLY action class, got {len(errors2)}"
        print(f"  ✓ ACTION_CLASS_DRAFT_ONLY validates")

        # Invalid action class
        record3 = V13ExecutionDraftSchema.create_draft_record(
            summary="draft with invalid action class.",
            intended_shape={"action_class": "INVALID_CLASS"},
        )
        errors3 = V13ExecutionDraftSchema.validate_draft_record(record3)
        assert len(errors3) > 0, "Expected errors for invalid action class"
        print(f"  ✓ Invalid action class detected: {len(errors3)} errors")

        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR141: v1.3 Execution Draft Schema v1 - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_empty_to_error_record,
        test_3_valid_available_record,
        test_4_forbidden_vocab_detection,
        test_5_token_literal_detection,
        test_6_numeric_pattern_detection,
        test_7_coupling_detection,
        test_8_warning_only_behavior,
        test_9_schema_validation_missing_fields,
        test_10_action_class_validation,
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
