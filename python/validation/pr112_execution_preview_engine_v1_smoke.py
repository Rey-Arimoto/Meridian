#!/usr/bin/env python3
"""
PR112: v1.1 Execution Preview Engine v1 - Smoke Tests

Purpose:
    Validate execution preview implementation.
    Preview = Impact Shape Description (not simulation/execution).

Tests:
    1. Engine import works
    2. Empty inputs → valid ERROR preview
    3. NOOP plan → NONE exposure
    4. REBALANCE plan → POOL_TOUCH
    5. REGIME_HIGH → HIGH risk surface
    6. REGIME_CRITICAL → BLOCKED preview
    7. Forbidden vocabulary detection
    8. Warning-only behavior (exit code always 0)
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
        from preview import (
            V11ExecutionPreviewSchema,
            generate_execution_preview_v1,
            validate_preview_record,
        )
        print("  ✓ Preview engine imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_defensive_behavior():
    """Test 2: Empty inputs → valid ERROR preview"""
    print("\nTest 2: Empty inputs → valid ERROR preview")
    from preview import generate_execution_preview_v1

    # Test invalid type
    result = generate_execution_preview_v1(plan_record="invalid")  # type: ignore
    if result.get("v11_preview_status") == "ERROR":
        print("  ✓ Invalid input produces ERROR preview record")
    else:
        print(f"  ✗ Invalid input did not produce ERROR record: {result.get('v11_preview_status')}")
        return False

    # Test unavailable plan
    unavailable_plan = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "UNAVAILABLE",
    }
    result = generate_execution_preview_v1(plan_record=unavailable_plan)
    if result.get("v11_preview_status") == "ERROR":
        print("  ✓ Unavailable plan produces ERROR preview record")
    else:
        print(f"  ✗ Unavailable plan did not produce ERROR record: {result.get('v11_preview_status')}")
        return False

    return True


def test_noop_plan_none_exposure():
    """Test 3: NOOP plan → NONE exposure"""
    print("\nTest 3: NOOP plan → NONE exposure")
    from preview import generate_execution_preview_v1

    noop_plan = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": "NOOP",
    }

    result = generate_execution_preview_v1(plan_record=noop_plan)

    if result.get("v11_preview_exposure_change") == "NONE":
        print("  ✓ NOOP plan maps to NONE exposure change")
    else:
        print(f"  ✗ NOOP plan did not map to NONE: {result.get('v11_preview_exposure_change')}")
        return False

    if result.get("v11_preview_interaction_type") == "NONE":
        print("  ✓ NOOP plan maps to NONE interaction type")
    else:
        print(f"  ✗ NOOP plan did not map to NONE interaction: {result.get('v11_preview_interaction_type')}")
        return False

    return True


def test_rebalance_plan_pool_touch():
    """Test 4: REBALANCE plan → POOL_TOUCH"""
    print("\nTest 4: REBALANCE plan → POOL_TOUCH")
    from preview import generate_execution_preview_v1

    rebalance_plan = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": "REBALANCE",
    }

    result = generate_execution_preview_v1(plan_record=rebalance_plan)

    if result.get("v11_preview_interaction_type") == "POOL_TOUCH":
        print("  ✓ REBALANCE plan maps to POOL_TOUCH interaction")
    else:
        print(f"  ✗ REBALANCE plan did not map to POOL_TOUCH: {result.get('v11_preview_interaction_type')}")
        return False

    # REBALANCE should map to DECREASE or INCREASE (v1 defaults to DECREASE)
    if result.get("v11_preview_exposure_change") in ["DECREASE", "INCREASE"]:
        print(f"  ✓ REBALANCE plan maps to {result.get('v11_preview_exposure_change')} exposure")
    else:
        print(f"  ✗ REBALANCE plan unexpected exposure: {result.get('v11_preview_exposure_change')}")
        return False

    return True


def test_regime_high_risk_surface():
    """Test 5: REGIME_HIGH → HIGH risk surface"""
    print("\nTest 5: REGIME_HIGH → HIGH risk surface")
    from preview import generate_execution_preview_v1

    plan = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": "HEDGE",
    }

    regime_high = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_HIGH",
    }

    result = generate_execution_preview_v1(
        plan_record=plan,
        regime_record=regime_high,
    )

    if result.get("v11_preview_risk_surface") == "HIGH":
        print("  ✓ REGIME_HIGH maps to HIGH risk surface")
    else:
        print(f"  ✗ REGIME_HIGH did not map to HIGH: {result.get('v11_preview_risk_surface')}")
        return False

    if result.get("v11_preview_status") == "AVAILABLE":
        print("  ✓ REGIME_HIGH allows preview AVAILABLE status")
    else:
        print(f"  ✗ REGIME_HIGH unexpected status: {result.get('v11_preview_status')}")
        return False

    return True


def test_regime_critical_blocked():
    """Test 6: REGIME_CRITICAL → BLOCKED preview"""
    print("\nTest 6: REGIME_CRITICAL → BLOCKED preview")
    from preview import generate_execution_preview_v1

    plan = {
        "v10_plan_mode": "ON",
        "v10_plan_status": "AVAILABLE",
        "v10_plan_type": "HEDGE",
    }

    regime_critical = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_CRITICAL",
    }

    result = generate_execution_preview_v1(
        plan_record=plan,
        regime_record=regime_critical,
    )

    if result.get("v11_preview_status") == "BLOCKED":
        print("  ✓ REGIME_CRITICAL produces BLOCKED preview")
    else:
        print(f"  ✗ REGIME_CRITICAL did not produce BLOCKED: {result.get('v11_preview_status')}")
        return False

    if "v11_preview_block_reason" in result:
        print(f"  ✓ BLOCKED preview includes block reason: {result['v11_preview_block_reason']}")
    else:
        print("  ✗ BLOCKED preview missing block reason")
        return False

    return True


def test_forbidden_vocabulary_detection():
    """Test 7: Forbidden vocabulary detection"""
    print("\nTest 7: Forbidden vocabulary detection")
    from preview import validate_preview_record

    # Test trading vocabulary
    dirty_preview_trading = {
        "v11_preview_summary": "plan will execute swap and buy operations.",
    }
    warnings = validate_preview_record(dirty_preview_trading)

    if len(warnings) > 0:
        print(f"  ✓ Trading vocabulary detected: {len(warnings)} warnings")
    else:
        print("  ✗ Trading vocabulary not detected")
        return False

    # Test execution operations
    dirty_preview_exec = {
        "v11_preview_summary": "plan will submit transaction to blockchain.",
    }
    warnings = validate_preview_record(dirty_preview_exec)

    if len(warnings) > 0:
        print(f"  ✓ Execution operations detected: {len(warnings)} warnings")
    else:
        print("  ✗ Execution operations not detected")
        return False

    # Test clean preview
    clean_preview = {
        "v11_preview_summary": "hedge-type plan would reduce exposure with pool interaction under elevated market regime.",
    }
    warnings = validate_preview_record(clean_preview)

    if len(warnings) == 0:
        print("  ✓ Clean preview passes validation")
    else:
        print(f"  ✗ Clean preview has unexpected warnings: {warnings}")
        return False

    return True


def test_warning_only_behavior():
    """Test 8: Warning-only behavior (exit code always 0)"""
    print("\nTest 8: Warning-only behavior (exit code always 0)")
    from preview import generate_execution_preview_v1

    # Test various error conditions - none should raise
    test_cases = [
        None,  # type: ignore
        "invalid",  # type: ignore
        {},
        {"v10_plan_status": "ERROR"},
        {"v10_plan_status": "UNAVAILABLE"},
    ]

    for i, test_case in enumerate(test_cases):
        try:
            result = generate_execution_preview_v1(plan_record=test_case)  # type: ignore
            if "v11_preview_status" in result:
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
    print("PR112: v1.1 Execution Preview Engine v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_engine_import,
        test_defensive_behavior,
        test_noop_plan_none_exposure,
        test_rebalance_plan_pool_touch,
        test_regime_high_risk_surface,
        test_regime_critical_blocked,
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
