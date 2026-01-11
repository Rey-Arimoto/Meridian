#!/usr/bin/env python3
"""
PR113: v1.1 Human Approval Gate v1 - Smoke Tests

Purpose:
    Validate human approval gate implementation.
    Approval Gate = State Machine (not action/recommendation).

Tests:
    1. Import works
    2. Empty inputs → valid record (defensive)
    3. Preview BLOCKED → REQUIRED_STRICT
    4. Permission HOLD → REQUIRED_STRICT
    5. Regime CRITICAL → REQUIRED_STRICT
    6. Permission DRY_RUN_ONLY → REQUIRED
    7. Regime HIGH → REQUIRED
    8. Guards detect forbidden vocab / token literals / numeric patterns / trading verbs
    9. Warning-only behavior (exit code always 0)
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_gate_import():
    """Test 1: Import works"""
    print("Test 1: Import works")
    try:
        from approval import (
            V11ApprovalSchema,
            gate_human_approval_v1,
            validate_approval_record,
        )
        print("  ✓ Approval gate imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_defensive_behavior():
    """Test 2: Empty inputs → valid record (defensive)"""
    print("\nTest 2: Empty inputs → valid record (defensive)")
    from approval import gate_human_approval_v1

    # Test with no inputs
    result = gate_human_approval_v1()
    if "v11_approval_requirement" in result and "v11_approval_state" in result:
        print(f"  ✓ No inputs produces valid record: requirement={result.get('v11_approval_requirement')}")
    else:
        print(f"  ✗ No inputs did not produce valid record")
        return False

    # Test with invalid inputs
    result = gate_human_approval_v1(execution_record="invalid")  # type: ignore
    if "v11_approval_requirement" in result:
        print("  ✓ Invalid inputs produce valid record (defensive)")
    else:
        print("  ✗ Invalid inputs did not produce valid record")
        return False

    return True


def test_preview_blocked_required_strict():
    """Test 3: Preview BLOCKED → REQUIRED_STRICT"""
    print("\nTest 3: Preview BLOCKED → REQUIRED_STRICT")
    from approval import gate_human_approval_v1

    preview_blocked = {
        "v11_preview_mode": "ON",
        "v11_preview_status": "BLOCKED",
        "v11_preview_block_reason": "regime critical observed",
    }

    result = gate_human_approval_v1(preview_record=preview_blocked)

    if result.get("v11_approval_requirement") == "REQUIRED_STRICT":
        print("  ✓ Preview BLOCKED maps to REQUIRED_STRICT")
    else:
        print(f"  ✗ Preview BLOCKED did not map to REQUIRED_STRICT: {result.get('v11_approval_requirement')}")
        return False

    if result.get("v11_approval_state") == "UNREQUESTED":
        print("  ✓ Approval state is UNREQUESTED")
    else:
        print(f"  ✗ Approval state not UNREQUESTED: {result.get('v11_approval_state')}")
        return False

    return True


def test_permission_hold_required_strict():
    """Test 4: Permission HOLD → REQUIRED_STRICT"""
    print("\nTest 4: Permission HOLD → REQUIRED_STRICT")
    from approval import gate_human_approval_v1

    execution_hold = {
        "v10_execution_mode": "ON",
        "v10_execution_permission": "HOLD",
    }

    result = gate_human_approval_v1(execution_record=execution_hold)

    if result.get("v11_approval_requirement") == "REQUIRED_STRICT":
        print("  ✓ Permission HOLD maps to REQUIRED_STRICT")
    else:
        print(f"  ✗ Permission HOLD did not map to REQUIRED_STRICT: {result.get('v11_approval_requirement')}")
        return False

    if result.get("v11_approval_state") == "UNREQUESTED":
        print("  ✓ Approval state is UNREQUESTED")
    else:
        print(f"  ✗ Approval state not UNREQUESTED: {result.get('v11_approval_state')}")
        return False

    return True


def test_regime_critical_required_strict():
    """Test 5: Regime CRITICAL → REQUIRED_STRICT"""
    print("\nTest 5: Regime CRITICAL → REQUIRED_STRICT")
    from approval import gate_human_approval_v1

    regime_critical = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_CRITICAL",
    }

    result = gate_human_approval_v1(regime_record=regime_critical)

    if result.get("v11_approval_requirement") == "REQUIRED_STRICT":
        print("  ✓ Regime CRITICAL maps to REQUIRED_STRICT")
    else:
        print(f"  ✗ Regime CRITICAL did not map to REQUIRED_STRICT: {result.get('v11_approval_requirement')}")
        return False

    if result.get("v11_approval_state") == "UNREQUESTED":
        print("  ✓ Approval state is UNREQUESTED")
    else:
        print(f"  ✗ Approval state not UNREQUESTED: {result.get('v11_approval_state')}")
        return False

    return True


def test_permission_dry_run_required():
    """Test 6: Permission DRY_RUN_ONLY → REQUIRED"""
    print("\nTest 6: Permission DRY_RUN_ONLY → REQUIRED")
    from approval import gate_human_approval_v1

    execution_dry_run = {
        "v10_execution_mode": "ON",
        "v10_execution_permission": "DRY_RUN_ONLY",
    }

    result = gate_human_approval_v1(execution_record=execution_dry_run)

    if result.get("v11_approval_requirement") == "REQUIRED":
        print("  ✓ Permission DRY_RUN_ONLY maps to REQUIRED")
    else:
        print(f"  ✗ Permission DRY_RUN_ONLY did not map to REQUIRED: {result.get('v11_approval_requirement')}")
        return False

    if result.get("v11_approval_state") == "UNREQUESTED":
        print("  ✓ Approval state is UNREQUESTED")
    else:
        print(f"  ✗ Approval state not UNREQUESTED: {result.get('v11_approval_state')}")
        return False

    return True


def test_regime_high_required():
    """Test 7: Regime HIGH → REQUIRED"""
    print("\nTest 7: Regime HIGH → REQUIRED")
    from approval import gate_human_approval_v1

    regime_high = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_HIGH",
    }

    result = gate_human_approval_v1(regime_record=regime_high)

    if result.get("v11_approval_requirement") == "REQUIRED":
        print("  ✓ Regime HIGH maps to REQUIRED")
    else:
        print(f"  ✗ Regime HIGH did not map to REQUIRED: {result.get('v11_approval_requirement')}")
        return False

    if result.get("v11_approval_state") == "UNREQUESTED":
        print("  ✓ Approval state is UNREQUESTED")
    else:
        print(f"  ✗ Approval state not UNREQUESTED: {result.get('v11_approval_state')}")
        return False

    return True


def test_forbidden_vocabulary_detection():
    """Test 8: Guards detect forbidden vocab / token literals / numeric patterns / trading verbs"""
    print("\nTest 8: Guards detect forbidden vocab / token literals / numeric patterns / trading verbs")
    from approval import validate_approval_record

    # Test trading vocabulary
    dirty_approval_trading = {
        "v11_approval_summary": "approval granted. proceed to execute swap operations.",
    }
    warnings = validate_approval_record(dirty_approval_trading)

    if len(warnings) > 0:
        print(f"  ✓ Trading vocabulary detected: {len(warnings)} warnings")
    else:
        print("  ✗ Trading vocabulary not detected")
        return False

    # Test approval-specific vocabulary (go ahead, proceed)
    dirty_approval_specific = {
        "v11_approval_summary": "approval granted. go ahead and proceed with execution.",
    }
    warnings = validate_approval_record(dirty_approval_specific)

    if len(warnings) > 0:
        print(f"  ✓ Approval-specific vocabulary detected: {len(warnings)} warnings")
    else:
        print("  ✗ Approval-specific vocabulary not detected")
        return False

    # Test token literals
    dirty_approval_token = {
        "v11_approval_summary": "approval for SUI and USDC operations.",
    }
    warnings = validate_approval_record(dirty_approval_token)

    if len(warnings) > 0:
        print(f"  ✓ Token literals detected: {len(warnings)} warnings")
    else:
        print("  ✗ Token literals not detected")
        return False

    # Test numeric patterns
    dirty_approval_numeric = {
        "v11_approval_summary": "approval for $1000 transaction at 5% fee.",
    }
    warnings = validate_approval_record(dirty_approval_numeric)

    if len(warnings) > 0:
        print(f"  ✓ Numeric patterns detected: {len(warnings)} warnings")
    else:
        print("  ✗ Numeric patterns not detected")
        return False

    # Test clean approval
    clean_approval = {
        "v11_approval_summary": "approval required under critical regime conditions. no approval requested.",
    }
    warnings = validate_approval_record(clean_approval)

    if len(warnings) == 0:
        print("  ✓ Clean approval passes validation")
    else:
        print(f"  ✗ Clean approval has unexpected warnings: {warnings}")
        return False

    return True


def test_warning_only_behavior():
    """Test 9: Warning-only behavior (exit code always 0)"""
    print("\nTest 9: Warning-only behavior (exit code always 0)")
    from approval import gate_human_approval_v1

    # Test various conditions - none should raise
    test_cases = [
        {},
        {"execution_record": None},
        {"execution_record": "invalid"},  # type: ignore
        {"regime_record": {"invalid": "structure"}},
    ]

    for i, test_case in enumerate(test_cases):
        try:
            result = gate_human_approval_v1(**test_case)  # type: ignore
            if "v11_approval_requirement" in result:
                print(f"  ✓ Test case {i+1}: No exception raised, valid record returned")
            else:
                print(f"  ✗ Test case {i+1}: Invalid record structure")
                return False
        except Exception as e:
            print(f"  ✗ Test case {i+1}: Exception raised: {e}")
            return False

    print("  ✓ All cases handled defensively (warning-only)")
    return True


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("PR113: v1.1 Human Approval Gate v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_gate_import,
        test_defensive_behavior,
        test_preview_blocked_required_strict,
        test_permission_hold_required_strict,
        test_regime_critical_required_strict,
        test_permission_dry_run_required,
        test_regime_high_required,
        test_forbidden_vocabulary_detection,
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
