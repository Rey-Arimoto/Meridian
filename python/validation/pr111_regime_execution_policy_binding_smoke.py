#!/usr/bin/env python3
"""
PR111: v1.1 Regime → Execution Policy Binding v1 - Smoke Tests

Purpose:
    Validate regime-execution policy binding implementation.
    Binding = Constitutional Gate (not action).

Tests:
    1. Schema import works
    2. Empty/invalid regime input produces valid policy record (defensive)
    3. REGIME_CRITICAL → permission override HOLD
    4. REGIME_HIGH → permission override DRY_RUN_ONLY
    5. MEDIUM/LOW → no override (UNKNOWN)
    6. Plan constraints appended correctly (labels only)
    7. Forbidden vocabulary detection works
    8. Token literal / numeric pattern guards enforced
    9. Warning-only behavior (exit code always 0)
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_schema_import():
    """Test 1: Schema import works"""
    print("Test 1: Schema import works")
    try:
        from policy import (
            V11RegimeExecutionPolicySchema,
            bind_regime_to_execution_policy_v1,
            validate_policy_record,
        )
        print("  ✓ Policy schema imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_defensive_behavior():
    """Test 2: Empty/invalid regime input produces valid policy record"""
    print("\nTest 2: Empty/invalid regime input produces valid policy record")
    from policy import bind_regime_to_execution_policy_v1

    # Test invalid type
    result = bind_regime_to_execution_policy_v1("invalid")  # type: ignore
    policy = result["policy_record"]

    if policy.get("v11_policy_status") == "ERROR":
        print("  ✓ Invalid input produces ERROR policy record")
    else:
        print(f"  ✗ Invalid input did not produce ERROR record: {policy.get('v11_policy_status')}")
        return False

    # Test unavailable regime
    unavailable_regime = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "UNAVAILABLE",
    }
    result = bind_regime_to_execution_policy_v1(unavailable_regime)
    policy = result["policy_record"]

    if policy.get("v11_policy_status") == "ERROR":
        print("  ✓ Unavailable regime produces ERROR policy record")
    else:
        print(f"  ✗ Unavailable regime did not produce ERROR record: {policy.get('v11_policy_status')}")
        return False

    return True


def test_regime_critical_hold():
    """Test 3: REGIME_CRITICAL → permission override HOLD"""
    print("\nTest 3: REGIME_CRITICAL → permission override HOLD")
    from policy import bind_regime_to_execution_policy_v1

    regime = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_CRITICAL",
        "v11_regime_basis": ["observation_count"],
    }

    result = bind_regime_to_execution_policy_v1(regime)
    policy = result["policy_record"]

    if policy.get("v11_execution_permission_override") == "HOLD":
        print("  ✓ REGIME_CRITICAL maps to HOLD override")
    else:
        print(f"  ✗ REGIME_CRITICAL did not map to HOLD: {policy.get('v11_execution_permission_override')}")
        return False

    if "regime_critical_observed" in policy.get("v11_plan_constraints_append", []):
        print("  ✓ REGIME_CRITICAL appends regime_critical_observed constraint")
    else:
        print(f"  ✗ Missing regime_critical_observed constraint: {policy.get('v11_plan_constraints_append')}")
        return False

    return True


def test_regime_high_dry_run():
    """Test 4: REGIME_HIGH → permission override DRY_RUN_ONLY"""
    print("\nTest 4: REGIME_HIGH → permission override DRY_RUN_ONLY")
    from policy import bind_regime_to_execution_policy_v1

    regime = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_HIGH",
        "v11_regime_basis": ["market_cost_regime_counts", "liquidity_regime_presence"],
    }

    result = bind_regime_to_execution_policy_v1(regime)
    policy = result["policy_record"]

    if policy.get("v11_execution_permission_override") == "DRY_RUN_ONLY":
        print("  ✓ REGIME_HIGH maps to DRY_RUN_ONLY override")
    else:
        print(f"  ✗ REGIME_HIGH did not map to DRY_RUN_ONLY: {policy.get('v11_execution_permission_override')}")
        return False

    if "regime_high_observed" in policy.get("v11_plan_constraints_append", []):
        print("  ✓ REGIME_HIGH appends regime_high_observed constraint")
    else:
        print(f"  ✗ Missing regime_high_observed constraint: {policy.get('v11_plan_constraints_append')}")
        return False

    return True


def test_regime_medium_low_no_override():
    """Test 5: MEDIUM/LOW → no override (UNKNOWN)"""
    print("\nTest 5: MEDIUM/LOW → no override (UNKNOWN)")
    from policy import bind_regime_to_execution_policy_v1

    # Test REGIME_MEDIUM
    medium_regime = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_MEDIUM",
        "v11_regime_basis": ["market_cost_regime_counts"],
    }

    result = bind_regime_to_execution_policy_v1(medium_regime)
    policy = result["policy_record"]

    if policy.get("v11_execution_permission_override") == "UNKNOWN":
        print("  ✓ REGIME_MEDIUM maps to UNKNOWN (no override)")
    else:
        print(f"  ✗ REGIME_MEDIUM did not map to UNKNOWN: {policy.get('v11_execution_permission_override')}")
        return False

    # Test REGIME_LOW
    low_regime = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_LOW",
        "v11_regime_basis": ["market_cost_regime_counts"],
    }

    result = bind_regime_to_execution_policy_v1(low_regime)
    policy = result["policy_record"]

    if policy.get("v11_execution_permission_override") == "UNKNOWN":
        print("  ✓ REGIME_LOW maps to UNKNOWN (no override)")
    else:
        print(f"  ✗ REGIME_LOW did not map to UNKNOWN: {policy.get('v11_execution_permission_override')}")
        return False

    return True


def test_plan_constraints_applied():
    """Test 6: Plan constraints appended correctly (labels only)"""
    print("\nTest 6: Plan constraints appended correctly (labels only)")
    from policy import bind_regime_to_execution_policy_v1

    regime = {
        "v11_regime_mode": "ON",
        "v11_regime_status": "AVAILABLE",
        "v11_regime_level": "REGIME_HIGH",
        "v11_regime_basis": ["market_cost_regime_counts"],
    }

    plan_record = {
        "v10_plan_type": "MAINTENANCE",
        "v10_plan_constraints": ["dry_run_only"],
    }

    result = bind_regime_to_execution_policy_v1(regime, plan_record=plan_record)
    updated_plan = result["plan_record"]

    constraints = updated_plan.get("v10_plan_constraints", [])
    if "regime_high_observed" in constraints and "dry_run_only" in constraints:
        print("  ✓ Plan constraints appended correctly")
    else:
        print(f"  ✗ Plan constraints not appended correctly: {constraints}")
        return False

    # Verify no duplicates
    if len(constraints) == len(set(constraints)):
        print("  ✓ No duplicate constraints")
    else:
        print(f"  ✗ Duplicate constraints found: {constraints}")
        return False

    return True


def test_forbidden_vocabulary_detection():
    """Test 7: Forbidden vocabulary detection works"""
    print("\nTest 7: Forbidden vocabulary detection works")
    from policy import validate_policy_record

    # Test action vocabulary
    dirty_policy = {
        "v11_policy_summary": "regime high. recommend reducing positions immediately.",
    }
    warnings = validate_policy_record(dirty_policy)

    if len(warnings) > 0:
        print(f"  ✓ Forbidden vocabulary detected: {len(warnings)} warnings")
    else:
        print("  ✗ Forbidden vocabulary not detected")
        return False

    # Test clean policy
    clean_policy = {
        "v11_policy_summary": "regime binding applied. execution limited to simulation under elevated regime conditions.",
        "v11_plan_constraints_append": ["regime_high_observed"],
    }
    warnings = validate_policy_record(clean_policy)

    if len(warnings) == 0:
        print("  ✓ Clean policy passes validation")
    else:
        print(f"  ✗ Clean policy has unexpected warnings: {warnings}")
        return False

    return True


def test_token_literal_numeric_guards():
    """Test 8: Token literal / numeric pattern guards enforced"""
    print("\nTest 8: Token literal / numeric pattern guards enforced")
    from policy import validate_policy_record

    # Test token literals
    token_policy = {
        "v11_policy_summary": "policy binding for SUI and USDC trading.",
    }
    warnings = validate_policy_record(token_policy)

    if len(warnings) > 0:
        print(f"  ✓ Token literals detected: {len(warnings)} warnings")
    else:
        print("  ✗ Token literals not detected")
        return False

    # Test numeric patterns in constraints
    numeric_policy = {
        "v11_plan_constraints_append": ["frequency_limit_5_times", "regime_high_observed"],
    }
    warnings = validate_policy_record(numeric_policy)

    if len(warnings) > 0:
        print(f"  ✓ Numeric patterns in constraints detected: {len(warnings)} warnings")
    else:
        print("  ✗ Numeric patterns not detected")
        return False

    return True


def test_warning_only_behavior():
    """Test 9: Warning-only behavior (exit code always 0)"""
    print("\nTest 9: Warning-only behavior (exit code always 0)")
    from policy import bind_regime_to_execution_policy_v1

    # Test various error conditions - none should raise
    test_cases = [
        None,  # type: ignore
        "invalid",  # type: ignore
        {},
        {"v11_regime_status": "ERROR"},
        {"v11_regime_status": "UNAVAILABLE"},
    ]

    for i, test_case in enumerate(test_cases):
        try:
            result = bind_regime_to_execution_policy_v1(test_case)  # type: ignore
            policy = result["policy_record"]
            if "v11_policy_status" in policy:
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
    print("PR111: v1.1 Regime → Execution Policy Binding v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_schema_import,
        test_defensive_behavior,
        test_regime_critical_hold,
        test_regime_high_dry_run,
        test_regime_medium_low_no_override,
        test_plan_constraints_applied,
        test_forbidden_vocabulary_detection,
        test_token_literal_numeric_guards,
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
