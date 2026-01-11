#!/usr/bin/env python3
"""
PR121: v1.0 Drift → Reflection/Boundary/Execution Binding v1 - Smoke Tests

Purpose:
    Validate drift binding into downstream constitutional layers.
    Drift = first-class input to explainability chain.

Tests:
    1. Import works
    2. DRIFT_CRITICAL → HOLD override + constraint label
    3. DRIFT_HIGH → DRY_RUN_ONLY override + constraint label
    4. LOW/MEDIUM/NONE → no override; constraint label appended
    5. Reflection attachment adds only safe addenda/artifact links
    6. Boundary hinting stays non-prescriptive
    7. Guards detect numeric patterns
    8. Guards detect token literals/addresses
    9. Guards detect trading/execution vocab
    10. Exit code always 0 (warning-only)
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_drift_binding_import():
    """Test 1: Import works"""
    print("Test 1: Drift binding import works")
    try:
        from bridge.v10_drift_to_reflection_attachment_v1 import (
            attach_drift_to_reflection_v1,
            get_drift_reflection_attachment_v1_info,
        )
        from boundary.v10_drift_boundary_hint_engine_v1 import (
            hint_boundary_with_drift_v1,
            get_drift_boundary_hint_v1_info,
        )
        from policy.v10_drift_execution_policy_binding_v1 import (
            bind_drift_to_execution_policy_v1,
            get_drift_execution_binding_v1_info,
        )
        from policy.v10_drift_policy_constitutional_guard import (
            validate_drift_policy_binding,
            check_prescriptive_language,
        )
        print("  ✓ Drift binding imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_drift_critical_to_hold():
    """Test 2: DRIFT_CRITICAL → HOLD override + constraint label"""
    print("\nTest 2: DRIFT_CRITICAL → HOLD override + constraint label")
    from policy.v10_drift_execution_policy_binding_v1 import bind_drift_to_execution_policy_v1
    from execution.v10_execution_schema import V10ExecutionSchema

    # Create execution record with UNKNOWN permission
    execution = V10ExecutionSchema.create_empty_record()
    execution["v10_execution_permission"] = "UNKNOWN"

    # Create DRIFT_CRITICAL record
    drift_critical = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "AVAILABLE",
        "v10_drift_level": "DRIFT_CRITICAL",
    }

    # Bind drift to execution
    enhanced = bind_drift_to_execution_policy_v1(execution, drift_critical)

    # Check permission override
    if enhanced.get("v10_execution_permission") != "HOLD":
        print(f"  ✗ Expected HOLD, got {enhanced.get('v10_execution_permission')}")
        return False
    print("  ✓ Permission overridden to HOLD")

    # Check constraint label
    constraints = enhanced.get("v10_execution_constraints", [])
    if "drift_critical_observed" not in constraints:
        print(f"  ✗ Missing drift_critical_observed in constraints: {constraints}")
        return False
    print("  ✓ Constraint label 'drift_critical_observed' added")

    return True


def test_drift_high_to_dry_run_only():
    """Test 3: DRIFT_HIGH → DRY_RUN_ONLY override + constraint label"""
    print("\nTest 3: DRIFT_HIGH → DRY_RUN_ONLY override + constraint label")
    from policy.v10_drift_execution_policy_binding_v1 import bind_drift_to_execution_policy_v1
    from execution.v10_execution_schema import V10ExecutionSchema

    # Create execution record with UNKNOWN permission
    execution = V10ExecutionSchema.create_empty_record()
    execution["v10_execution_permission"] = "UNKNOWN"

    # Create DRIFT_HIGH record
    drift_high = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "AVAILABLE",
        "v10_drift_level": "DRIFT_HIGH",
    }

    # Bind drift to execution
    enhanced = bind_drift_to_execution_policy_v1(execution, drift_high)

    # Check permission override
    if enhanced.get("v10_execution_permission") != "DRY_RUN_ONLY":
        print(f"  ✗ Expected DRY_RUN_ONLY, got {enhanced.get('v10_execution_permission')}")
        return False
    print("  ✓ Permission overridden to DRY_RUN_ONLY")

    # Check constraint label
    constraints = enhanced.get("v10_execution_constraints", [])
    if "drift_high_observed" not in constraints:
        print(f"  ✗ Missing drift_high_observed in constraints: {constraints}")
        return False
    print("  ✓ Constraint label 'drift_high_observed' added")

    return True


def test_low_medium_none_no_override():
    """Test 4: LOW/MEDIUM/NONE → no override; constraint label appended"""
    print("\nTest 4: LOW/MEDIUM/NONE → no override; constraint label appended")
    from policy.v10_drift_execution_policy_binding_v1 import bind_drift_to_execution_policy_v1
    from execution.v10_execution_schema import V10ExecutionSchema

    test_levels = ["DRIFT_LOW", "DRIFT_MEDIUM", "DRIFT_NONE"]
    expected_labels = ["drift_low_observed", "drift_medium_observed", "drift_none_observed"]

    for drift_level, expected_label in zip(test_levels, expected_labels):
        # Create execution record with UNKNOWN permission
        execution = V10ExecutionSchema.create_empty_record()
        execution["v10_execution_permission"] = "UNKNOWN"

        # Create drift record
        drift = {
            "v10_drift_mode": "ON",
            "v10_drift_status": "AVAILABLE",
            "v10_drift_level": drift_level,
        }

        # Bind drift to execution
        enhanced = bind_drift_to_execution_policy_v1(execution, drift)

        # Check permission NOT overridden (stays UNKNOWN)
        if enhanced.get("v10_execution_permission") != "UNKNOWN":
            print(f"  ✗ {drift_level}: Permission should stay UNKNOWN, got {enhanced.get('v10_execution_permission')}")
            return False

        # Check constraint label
        constraints = enhanced.get("v10_execution_constraints", [])
        if expected_label not in constraints:
            print(f"  ✗ {drift_level}: Missing {expected_label} in constraints: {constraints}")
            return False

    print("  ✓ LOW/MEDIUM/NONE: No override, constraint labels added")
    return True


def test_reflection_attachment_safe():
    """Test 5: Reflection attachment adds only safe addenda/artifact links"""
    print("\nTest 5: Reflection attachment adds only safe addenda/artifact links")
    from bridge.v10_drift_to_reflection_attachment_v1 import attach_drift_to_reflection_v1
    from reflection.v7_reflection_schema import V7ReflectionSchema

    # Create reflection record
    reflection = V7ReflectionSchema.create_empty_record()
    reflection["v7_reflection_tag"] = "MEANING_COVERAGE_NARROW"
    reflection["v7_reflection_summary"] = "limited meaning types observed."

    # Create drift record
    drift = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "AVAILABLE",
        "v10_drift_level": "DRIFT_MEDIUM",
    }

    # Attach drift to reflection
    enhanced = attach_drift_to_reflection_v1(reflection, drift)

    # Check artifacts added
    artifacts = enhanced.get("v7_reflection_artifacts", [])
    if "pr120_drift_record" not in artifacts:
        print(f"  ✗ Missing pr120_drift_record in artifacts: {artifacts}")
        return False

    # Check basis added
    basis = enhanced.get("v7_reflection_basis", [])
    if "v10_drift_level" not in basis:
        print(f"  ✗ Missing v10_drift_level in basis: {basis}")
        return False

    # Check reflection tag NOT modified
    if enhanced.get("v7_reflection_tag") != "MEANING_COVERAGE_NARROW":
        print(f"  ✗ Reflection tag was modified: {enhanced.get('v7_reflection_tag')}")
        return False

    print("  ✓ Reflection attachment adds only safe addenda/artifact links")
    return True


def test_boundary_hinting_non_prescriptive():
    """Test 6: Boundary hinting stays non-prescriptive"""
    print("\nTest 6: Boundary hinting stays non-prescriptive")
    from boundary.v10_drift_boundary_hint_engine_v1 import hint_boundary_with_drift_v1
    from boundary.v9_boundary_schema import V9BoundarySchema

    # Create boundary record
    boundary = V9BoundarySchema.create_empty_record()
    boundary["v9_boundary_type"] = "SAMPLING_BOUNDARY"
    boundary["v9_boundary_description"] = "sampling boundary detected."

    # Create DRIFT_CRITICAL record
    drift_critical = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "AVAILABLE",
        "v10_drift_level": "DRIFT_CRITICAL",
    }

    # Hint boundary with drift
    enhanced = hint_boundary_with_drift_v1(boundary, drift_critical)

    # Check description enhanced
    description = enhanced.get("v9_boundary_description", "")
    if "observability unstable under critical drift" not in description:
        print(f"  ✗ Expected drift hint in description: {description}")
        return False

    # Check no prescriptive language (should, must, pause, stop)
    prescriptive_patterns = ["should", "must", "pause", "stop", "halt"]
    for pattern in prescriptive_patterns:
        if pattern in description.lower():
            print(f"  ✗ Prescriptive language detected: '{pattern}' in description")
            return False

    print("  ✓ Boundary hinting stays non-prescriptive")
    return True


def test_guards_detect_numeric_patterns():
    """Test 7: Guards detect numeric patterns"""
    print("\nTest 7: Guards detect numeric patterns")
    from policy.v10_drift_policy_constitutional_guard import validate_drift_policy_binding

    # Dirty binding with numeric patterns
    dirty_binding = {
        "v10_execution_summary": "drift detected with 5 terms added and 3 terms removed. delta=8.",
        "v10_execution_constraints": [],
    }

    warnings = validate_drift_policy_binding(dirty_binding)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect numeric patterns")
        return False

    print(f"  ✓ Guards detected numeric patterns: {len(warnings)} warnings")
    return True


def test_guards_detect_token_literals_addresses():
    """Test 8: Guards detect token literals/addresses"""
    print("\nTest 8: Guards detect token literals/addresses")
    from policy.v10_drift_policy_constitutional_guard import validate_drift_policy_binding

    # Dirty binding with token literals
    dirty_token = {
        "v10_execution_summary": "drift detected with SUI and USDC activity. address 0x1234.",
        "v10_execution_constraints": [],
    }

    warnings = validate_drift_policy_binding(dirty_token)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect token literals/addresses")
        return False

    print(f"  ✓ Guards detected token literals/addresses: {len(warnings)} warnings")
    return True


def test_guards_detect_trading_execution_vocab():
    """Test 9: Guards detect trading/execution vocab"""
    print("\nTest 9: Guards detect trading/execution vocab")
    from policy.v10_drift_policy_constitutional_guard import validate_drift_policy_binding

    # Dirty binding with trading vocabulary
    dirty_trading = {
        "v10_execution_summary": "drift detected. execute swap operations now. transfer funds and sign transaction.",
        "v10_execution_constraints": [],
    }

    warnings = validate_drift_policy_binding(dirty_trading)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect trading/execution vocabulary")
        return False

    print(f"  ✓ Guards detected trading/execution vocabulary: {len(warnings)} warnings")
    return True


def test_warning_only_behavior():
    """Test 10: Exit code always 0 (warning-only)"""
    print("\nTest 10: Exit code always 0 (warning-only)")
    from policy.v10_drift_execution_policy_binding_v1 import bind_drift_to_execution_policy_v1

    # Test various error conditions - none should raise
    test_cases = [
        (None, None),
        ({}, {}),
        ({"invalid": "execution"}, {"invalid": "drift"}),
    ]

    for i, (execution, drift) in enumerate(test_cases):
        try:
            result = bind_drift_to_execution_policy_v1(execution, drift)
            # Check that result is a dict (defensive behavior)
            if not isinstance(result, dict):
                print(f"  ✗ Test case {i+1}: Result is not a dict: {type(result)}")
                return False
            print(f"  ✓ Test case {i+1}: No exception raised, valid result returned")
        except Exception as e:
            print(f"  ✗ Test case {i+1}: Exception raised: {e}")
            return False

    print("  ✓ All error cases handled defensively (warning-only)")
    return True


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("PR121: v1.0 Drift → Reflection/Boundary/Execution Binding v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_drift_binding_import,
        test_drift_critical_to_hold,
        test_drift_high_to_dry_run_only,
        test_low_medium_none_no_override,
        test_reflection_attachment_safe,
        test_boundary_hinting_non_prescriptive,
        test_guards_detect_numeric_patterns,
        test_guards_detect_token_literals_addresses,
        test_guards_detect_trading_execution_vocab,
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
