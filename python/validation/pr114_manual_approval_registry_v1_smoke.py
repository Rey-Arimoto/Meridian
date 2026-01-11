#!/usr/bin/env python3
"""
PR114: v1.1 Manual Approval Registry v1 - Smoke Tests

Purpose:
    Validate manual approval registry implementation.
    Registry = State Transition Record (not action/instruction).

Tests:
    1. Engine import works
    2. Empty registry record validates
    3. NOT_REQUIRED ignores events (APPROVE/REQUEST etc.)
    4. REQUEST transitions work (UNREQUESTED→REQUESTED, idempotent)
    5. APPROVE only valid from REQUESTED
    6. REJECT only valid from REQUESTED
    7. EXPIRE only valid from REQUESTED
    8. Invalid event string handled defensively → warnings
    9. Guards detect token literal/numeric pattern/trading verbs
    10. Exit code always 0 (warning-only)
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_engine_import():
    """Test 1: Engine import works"""
    print("Test 1: Engine import works")
    try:
        from approval import (
            V11ApprovalRegistrySchema,
            apply_approval_event_v1,
            validate_registry_record,
        )
        print("  ✓ Registry engine imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_empty_registry_validates():
    """Test 2: Empty registry record validates"""
    print("\nTest 2: Empty registry record validates")
    from approval import V11ApprovalRegistrySchema

    empty = V11ApprovalRegistrySchema.create_empty_record()
    warnings = V11ApprovalRegistrySchema.validate_structure(empty)

    if len(warnings) == 0:
        print("  ✓ Empty registry record validates")
        return True
    else:
        print(f"  ✗ Empty registry record has warnings: {warnings}")
        return False


def test_not_required_ignores_events():
    """Test 3: NOT_REQUIRED ignores events"""
    print("\nTest 3: NOT_REQUIRED ignores events")
    from approval import apply_approval_event_v1

    not_required_gate = {
        "v11_approval_requirement": "NOT_REQUIRED",
    }

    # Try REQUEST event (should be ignored)
    result = apply_approval_event_v1(
        approval_gate_record=not_required_gate,
        registry_record=None,
        event="REQUEST",
    )

    if result.get("v11_registry_state") == "UNREQUESTED" and result.get("v11_registry_event") == "NONE":
        print("  ✓ NOT_REQUIRED ignores REQUEST event")
    else:
        print(f"  ✗ NOT_REQUIRED did not ignore event: state={result.get('v11_registry_state')}, event={result.get('v11_registry_event')}")
        return False

    # Try APPROVE event (should be ignored)
    result = apply_approval_event_v1(
        approval_gate_record=not_required_gate,
        registry_record=None,
        event="APPROVE",
    )

    if result.get("v11_registry_state") == "UNREQUESTED" and result.get("v11_registry_event") == "NONE":
        print("  ✓ NOT_REQUIRED ignores APPROVE event")
        return True
    else:
        print(f"  ✗ NOT_REQUIRED did not ignore APPROVE event")
        return False


def test_request_transitions():
    """Test 4: REQUEST transitions work"""
    print("\nTest 4: REQUEST transitions work")
    from approval import apply_approval_event_v1

    approval_gate = {
        "v11_approval_requirement": "REQUIRED",
    }

    # UNREQUESTED → REQUESTED
    result = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=None,
        event="REQUEST",
    )

    if result.get("v11_registry_state") == "REQUESTED":
        print("  ✓ UNREQUESTED → REQUESTED transition works")
    else:
        print(f"  ✗ UNREQUESTED → REQUESTED failed: {result.get('v11_registry_state')}")
        return False

    # REQUESTED → REQUESTED (idempotent)
    existing_registry = {
        "v11_registry_state": "REQUESTED",
    }
    result = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=existing_registry,
        event="REQUEST",
    )

    if result.get("v11_registry_state") == "REQUESTED":
        print("  ✓ REQUESTED → REQUESTED (idempotent) works")
    else:
        print(f"  ✗ Idempotent REQUEST failed")
        return False

    # APPROVED → REQUESTED (re-request allowed)
    approved_registry = {
        "v11_registry_state": "APPROVED",
    }
    result = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=approved_registry,
        event="REQUEST",
    )

    if result.get("v11_registry_state") == "REQUESTED":
        print("  ✓ APPROVED → REQUESTED (re-request) works")
        return True
    else:
        print(f"  ✗ Re-request from APPROVED failed")
        return False


def test_approve_only_from_requested():
    """Test 5: APPROVE only valid from REQUESTED"""
    print("\nTest 5: APPROVE only valid from REQUESTED")
    from approval import apply_approval_event_v1

    approval_gate = {
        "v11_approval_requirement": "REQUIRED",
    }

    # REQUESTED → APPROVED (valid)
    requested_registry = {
        "v11_registry_state": "REQUESTED",
    }
    result = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=requested_registry,
        event="APPROVE",
    )

    if result.get("v11_registry_state") == "APPROVED":
        print("  ✓ REQUESTED → APPROVED transition works")
    else:
        print(f"  ✗ REQUESTED → APPROVED failed: {result.get('v11_registry_state')}")
        return False

    # UNREQUESTED → APPROVE (invalid, should warn)
    unrequested_registry = {
        "v11_registry_state": "UNREQUESTED",
    }
    result = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=unrequested_registry,
        event="APPROVE",
    )

    if result.get("v11_registry_state") == "UNREQUESTED" and result.get("v11_registry_warnings"):
        print("  ✓ APPROVE from UNREQUESTED produces warning and no state change")
        return True
    else:
        print(f"  ✗ APPROVE from UNREQUESTED did not produce expected warning")
        return False


def test_reject_only_from_requested():
    """Test 6: REJECT only valid from REQUESTED"""
    print("\nTest 6: REJECT only valid from REQUESTED")
    from approval import apply_approval_event_v1

    approval_gate = {
        "v11_approval_requirement": "REQUIRED",
    }

    # REQUESTED → REJECTED (valid)
    requested_registry = {
        "v11_registry_state": "REQUESTED",
    }
    result = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=requested_registry,
        event="REJECT",
    )

    if result.get("v11_registry_state") == "REJECTED":
        print("  ✓ REQUESTED → REJECTED transition works")
    else:
        print(f"  ✗ REQUESTED → REJECTED failed: {result.get('v11_registry_state')}")
        return False

    # UNREQUESTED → REJECT (invalid, should warn)
    unrequested_registry = {
        "v11_registry_state": "UNREQUESTED",
    }
    result = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=unrequested_registry,
        event="REJECT",
    )

    if result.get("v11_registry_state") == "UNREQUESTED" and result.get("v11_registry_warnings"):
        print("  ✓ REJECT from UNREQUESTED produces warning and no state change")
        return True
    else:
        print(f"  ✗ REJECT from UNREQUESTED did not produce expected warning")
        return False


def test_expire_only_from_requested():
    """Test 7: EXPIRE only valid from REQUESTED"""
    print("\nTest 7: EXPIRE only valid from REQUESTED")
    from approval import apply_approval_event_v1

    approval_gate = {
        "v11_approval_requirement": "REQUIRED",
    }

    # REQUESTED → EXPIRED (valid)
    requested_registry = {
        "v11_registry_state": "REQUESTED",
    }
    result = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=requested_registry,
        event="EXPIRE",
    )

    if result.get("v11_registry_state") == "EXPIRED":
        print("  ✓ REQUESTED → EXPIRED transition works")
    else:
        print(f"  ✗ REQUESTED → EXPIRED failed: {result.get('v11_registry_state')}")
        return False

    # UNREQUESTED → EXPIRE (invalid, should warn)
    unrequested_registry = {
        "v11_registry_state": "UNREQUESTED",
    }
    result = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=unrequested_registry,
        event="EXPIRE",
    )

    if result.get("v11_registry_state") == "UNREQUESTED" and result.get("v11_registry_warnings"):
        print("  ✓ EXPIRE from UNREQUESTED produces warning and no state change")
        return True
    else:
        print(f"  ✗ EXPIRE from UNREQUESTED did not produce expected warning")
        return False


def test_invalid_event_defensive():
    """Test 8: Invalid event string handled defensively"""
    print("\nTest 8: Invalid event string handled defensively")
    from approval import apply_approval_event_v1

    approval_gate = {
        "v11_approval_requirement": "REQUIRED",
    }

    # Invalid event string
    result = apply_approval_event_v1(
        approval_gate_record=approval_gate,
        registry_record=None,
        event="INVALID_EVENT",
    )

    if result.get("v11_registry_warnings") and any("Invalid event" in w for w in result["v11_registry_warnings"]):
        print("  ✓ Invalid event produces warning")
    else:
        print(f"  ✗ Invalid event did not produce warning: {result.get('v11_registry_warnings')}")
        return False

    if result.get("v11_registry_event") == "NONE":
        print("  ✓ Invalid event defaults to NONE")
        return True
    else:
        print(f"  ✗ Invalid event did not default to NONE: {result.get('v11_registry_event')}")
        return False


def test_guards_detect_violations():
    """Test 9: Guards detect token literal/numeric pattern/trading verbs"""
    print("\nTest 9: Guards detect token literal/numeric pattern/trading verbs")
    from approval import validate_registry_record

    # Test token literals
    token_registry = {
        "v11_registry_summary": "approval for SUI and USDC operations.",
    }
    warnings = validate_registry_record(token_registry)

    if len(warnings) > 0:
        print(f"  ✓ Token literals detected: {len(warnings)} warnings")
    else:
        print("  ✗ Token literals not detected")
        return False

    # Test numeric patterns
    numeric_registry = {
        "v11_registry_summary": "approval for $1000 transaction at 5% fee.",
    }
    warnings = validate_registry_record(numeric_registry)

    if len(warnings) > 0:
        print(f"  ✓ Numeric patterns detected: {len(warnings)} warnings")
    else:
        print("  ✗ Numeric patterns not detected")
        return False

    # Test trading verbs
    trading_registry = {
        "v11_registry_summary": "approval granted. execute swap operations.",
    }
    warnings = validate_registry_record(trading_registry)

    if len(warnings) > 0:
        print(f"  ✓ Trading verbs detected: {len(warnings)} warnings")
    else:
        print("  ✗ Trading verbs not detected")
        return False

    # Test instructional coupling
    coupling_registry = {
        "v11_registry_summary": "approval granted, proceed with execution.",
    }
    warnings = validate_registry_record(coupling_registry)

    if len(warnings) > 0:
        print(f"  ✓ Instructional coupling detected: {len(warnings)} warnings")
    else:
        print("  ✗ Instructional coupling not detected")
        return False

    # Test clean registry
    clean_registry = {
        "v11_registry_summary": "approval request recorded. registry state set to requested.",
    }
    warnings = validate_registry_record(clean_registry)

    if len(warnings) == 0:
        print("  ✓ Clean registry passes validation")
        return True
    else:
        print(f"  ✗ Clean registry has unexpected warnings: {warnings}")
        return False


def test_warning_only_behavior():
    """Test 10: Exit code always 0 (warning-only)"""
    print("\nTest 10: Exit code always 0 (warning-only)")
    from approval import apply_approval_event_v1

    # Test various error conditions - none should raise
    test_cases = [
        {"approval_gate_record": None, "registry_record": None, "event": None},
        {"approval_gate_record": "invalid", "registry_record": None, "event": "REQUEST"},  # type: ignore
        {"approval_gate_record": {}, "registry_record": "invalid", "event": "APPROVE"},  # type: ignore
        {"approval_gate_record": {"v11_approval_requirement": "REQUIRED"}, "registry_record": None, "event": "INVALID_EVENT"},
    ]

    for i, test_case in enumerate(test_cases):
        try:
            result = apply_approval_event_v1(**test_case)  # type: ignore
            if "v11_registry_state" in result:
                print(f"  ✓ Test case {i+1}: No exception raised, valid record returned")
            else:
                print(f"  ✗ Test case {i+1}: Invalid record structure")
                return False
        except Exception as e:
            print(f"  ✗ Test case {i+1}: Exception raised: {e}")
            return False

    print("  ✓ All error cases handled defensively (warning-only)")
    return True


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("PR114: v1.1 Manual Approval Registry v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_engine_import,
        test_empty_registry_validates,
        test_not_required_ignores_events,
        test_request_transitions,
        test_approve_only_from_requested,
        test_reject_only_from_requested,
        test_expire_only_from_requested,
        test_invalid_event_defensive,
        test_guards_detect_violations,
        test_warning_only_behavior,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"  ✗ Test failed with exception: {e}")
            results.append(False)

    print()
    print("=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    # Exit with code 0 even if tests fail (smoke test, not enforcement)
    if all(results):
        print("\n✓ All smoke tests passed")
        sys.exit(0)
    else:
        print("\n✗ Some smoke tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
