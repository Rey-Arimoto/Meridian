#!/usr/bin/env python3
"""
PR115: v1.0 Pipeline Orchestrator v1 - Smoke Tests

Purpose:
    Validate pipeline orchestrator implementation.
    Orchestrator = Wiring (not decision/action).

Tests:
    1. Orchestrator import works
    2. End-to-end run with mock observations produces all artifacts
    3. Fixed ordering verified (layer list / audit chain order)
    4. Defensive behavior: missing inputs still return valid ERROR artifacts
    5. Guards detect forbidden vocab
    6. Guards detect token literals / numeric patterns / addresses
    7. No execution operations referenced
    8. Exit code always 0 (warning-only)
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_orchestrator_import():
    """Test 1: Orchestrator import works"""
    print("Test 1: Orchestrator import works")
    try:
        from orchestrator import (
            run_pipeline_v1,
            get_pipeline_orchestrator_v1_info,
            validate_orchestrator_artifacts,
        )
        print("  ✓ Orchestrator imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_end_to_end_run_produces_artifacts():
    """Test 2: End-to-end run with mock observations produces all artifacts"""
    print("\nTest 2: End-to-end run with mock observations produces all artifacts")
    from orchestrator import run_pipeline_v1

    # Run pipeline with defaults (mock inputs)
    artifacts = run_pipeline_v1()

    # Check that pipeline completed
    if artifacts.get("pipeline_status") != "COMPLETE":
        print(f"  ✗ Pipeline status not COMPLETE: {artifacts.get('pipeline_status')}")
        return False
    print("  ✓ Pipeline completed")

    # Check that all required artifacts are present
    required_artifacts = [
        "onchain_analytics",
        "regime_record",
        "policy_record",
        "execution_plan",
        "preview_record",
        "approval_gate_record",
        "registry_record",
    ]

    for artifact in required_artifacts:
        if artifact not in artifacts:
            print(f"  ✗ Missing artifact: {artifact}")
            return False

    print(f"  ✓ All {len(required_artifacts)} required artifacts present")

    # Check that pipeline metadata is present
    if "pipeline_version" not in artifacts:
        print("  ✗ Missing pipeline_version")
        return False
    if "pipeline_order" not in artifacts:
        print("  ✗ Missing pipeline_order")
        return False

    print("  ✓ Pipeline metadata present")
    return True


def test_fixed_ordering_verified():
    """Test 3: Fixed ordering verified (layer list / audit chain order)"""
    print("\nTest 3: Fixed ordering verified (layer list / audit chain order)")
    from orchestrator import run_pipeline_v1

    # Run pipeline
    artifacts = run_pipeline_v1()

    # Check pipeline order
    expected_order = [
        "onchain_analytics",
        "regime_record",
        "policy_record",
        "execution_plan",
        "preview_record",
        "approval_gate_record",
        "registry_record",
    ]

    actual_order = artifacts.get("pipeline_order", [])

    if actual_order != expected_order:
        print(f"  ✗ Pipeline order mismatch")
        print(f"    Expected: {expected_order}")
        print(f"    Actual: {actual_order}")
        return False

    print("  ✓ Pipeline order matches expected fixed order")

    # Verify all artifacts appear in order
    for i, artifact_name in enumerate(expected_order):
        if artifact_name not in artifacts:
            print(f"  ✗ Artifact {artifact_name} missing (position {i})")
            return False

    print("  ✓ All artifacts present in correct order")
    return True


def test_defensive_behavior():
    """Test 4: Defensive behavior: missing inputs still return valid ERROR artifacts"""
    print("\nTest 4: Defensive behavior: missing inputs still return valid ERROR artifacts")
    from orchestrator import run_pipeline_v1

    # Test with invalid onchain analytics
    invalid_analytics = "invalid_string"
    artifacts = run_pipeline_v1(onchain_analytics=invalid_analytics)

    # Should still complete with warnings
    if artifacts.get("pipeline_status") != "COMPLETE":
        print(f"  ✗ Pipeline did not complete with invalid analytics: {artifacts.get('pipeline_status')}")
        return False
    print("  ✓ Pipeline completed despite invalid analytics")

    # Should have warnings
    if "pipeline_warnings" not in artifacts or len(artifacts["pipeline_warnings"]) == 0:
        print("  ✗ No warnings generated for invalid analytics")
        return False
    print(f"  ✓ Warnings generated: {len(artifacts['pipeline_warnings'])}")

    # Test with None inputs (should use mocks)
    artifacts_none = run_pipeline_v1(onchain_analytics=None, execution_plan=None)

    if artifacts_none.get("pipeline_status") != "COMPLETE":
        print(f"  ✗ Pipeline did not complete with None inputs")
        return False
    print("  ✓ Pipeline completed with None inputs (using mocks)")

    # All artifacts should still be present
    required_artifacts = ["regime_record", "policy_record", "preview_record", "approval_gate_record", "registry_record"]
    for artifact in required_artifacts:
        if artifact not in artifacts_none:
            print(f"  ✗ Missing artifact with None inputs: {artifact}")
            return False

    print("  ✓ All artifacts present with None inputs")
    return True


def test_guards_detect_forbidden_vocab():
    """Test 5: Guards detect forbidden vocab"""
    print("\nTest 5: Guards detect forbidden vocab")
    from orchestrator import validate_orchestrator_artifacts

    # Test with trading vocabulary
    dirty_artifacts = {
        "pipeline_status": "COMPLETE",
        "regime_record": {
            "v11_regime_summary": "regime classified. execute swap operations.",
        },
    }

    warnings = validate_orchestrator_artifacts(dirty_artifacts)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect trading vocabulary")
        return False

    print(f"  ✓ Guards detected forbidden vocabulary: {len(warnings)} warnings")

    # Test with orchestrator overreach
    overreach_artifacts = {
        "pipeline_status": "orchestrator recommends proceeding with execution.",
    }

    overreach_warnings = validate_orchestrator_artifacts(overreach_artifacts)

    if len(overreach_warnings) == 0:
        print("  ✗ Guards did not detect orchestrator overreach")
        return False

    print(f"  ✓ Guards detected orchestrator overreach: {len(overreach_warnings)} warnings")
    return True


def test_guards_detect_token_literals():
    """Test 6: Guards detect token literals / numeric patterns / addresses"""
    print("\nTest 6: Guards detect token literals / numeric patterns / addresses")
    from orchestrator import validate_orchestrator_artifacts

    # Test token literals
    token_artifacts = {
        "pipeline_warnings": ["SUI and USDC analysis complete"],
    }

    token_warnings = validate_orchestrator_artifacts(token_artifacts)

    if len(token_warnings) == 0:
        print("  ✗ Guards did not detect token literals")
        return False

    print(f"  ✓ Guards detected token literals: {len(token_warnings)} warnings")

    # Test numeric patterns
    numeric_artifacts = {
        "regime_record": {
            "v11_regime_summary": "regime classified with $1000 threshold.",
        },
    }

    numeric_warnings = validate_orchestrator_artifacts(numeric_artifacts)

    if len(numeric_warnings) == 0:
        print("  ✗ Guards did not detect numeric patterns")
        return False

    print(f"  ✓ Guards detected numeric patterns: {len(numeric_warnings)} warnings")

    # Test addresses
    address_artifacts = {
        "regime_record": {
            "v11_regime_summary": "regime classified for 0x1234567890abcdef.",
        },
    }

    address_warnings = validate_orchestrator_artifacts(address_artifacts)

    if len(address_warnings) == 0:
        print("  ✗ Guards did not detect address patterns")
        return False

    print(f"  ✓ Guards detected address patterns: {len(address_warnings)} warnings")
    return True


def test_no_execution_operations():
    """Test 7: No execution operations referenced"""
    print("\nTest 7: No execution operations referenced")
    from orchestrator import run_pipeline_v1

    # Run pipeline
    artifacts = run_pipeline_v1()

    # Check all summaries for execution operations
    execution_keywords = ["execute", "sign", "broadcast", "submit", "transaction"]

    violations = []

    # Check regime record
    if "regime_record" in artifacts and "v11_regime_summary" in artifacts["regime_record"]:
        summary = artifacts["regime_record"]["v11_regime_summary"].lower()
        for keyword in execution_keywords:
            if keyword in summary:
                violations.append(f"regime_record contains '{keyword}'")

    # Check policy record
    if "policy_record" in artifacts and "v11_policy_summary" in artifacts["policy_record"]:
        summary = artifacts["policy_record"]["v11_policy_summary"].lower()
        for keyword in execution_keywords:
            if keyword in summary:
                violations.append(f"policy_record contains '{keyword}'")

    # Check preview record
    if "preview_record" in artifacts and "v11_preview_summary" in artifacts["preview_record"]:
        summary = artifacts["preview_record"]["v11_preview_summary"].lower()
        for keyword in execution_keywords:
            if keyword in summary:
                violations.append(f"preview_record contains '{keyword}'")

    # Check approval gate record
    if "approval_gate_record" in artifacts and "v11_approval_summary" in artifacts["approval_gate_record"]:
        summary = artifacts["approval_gate_record"]["v11_approval_summary"].lower()
        for keyword in execution_keywords:
            if keyword in summary:
                violations.append(f"approval_gate_record contains '{keyword}'")

    # Check registry record
    if "registry_record" in artifacts and "v11_registry_summary" in artifacts["registry_record"]:
        summary = artifacts["registry_record"]["v11_registry_summary"].lower()
        for keyword in execution_keywords:
            if keyword in summary:
                violations.append(f"registry_record contains '{keyword}'")

    if len(violations) > 0:
        print(f"  ✗ Execution operations found:")
        for v in violations:
            print(f"    - {v}")
        return False

    print("  ✓ No execution operations found in artifacts")
    return True


def test_warning_only_behavior():
    """Test 8: Exit code always 0 (warning-only)"""
    print("\nTest 8: Exit code always 0 (warning-only)")
    from orchestrator import run_pipeline_v1

    # Test various error conditions - none should raise
    test_cases = [
        {"onchain_analytics": None, "execution_plan": None},
        {"onchain_analytics": "invalid", "execution_plan": None},
        {"onchain_analytics": None, "execution_plan": "invalid"},
        {"onchain_analytics": {}, "execution_plan": {}},
    ]

    for i, test_case in enumerate(test_cases):
        try:
            result = run_pipeline_v1(**test_case)
            if "pipeline_status" not in result:
                print(f"  ✗ Test case {i+1}: Invalid result structure")
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
    print("PR115: v1.0 Pipeline Orchestrator v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_orchestrator_import,
        test_end_to_end_run_produces_artifacts,
        test_fixed_ordering_verified,
        test_defensive_behavior,
        test_guards_detect_forbidden_vocab,
        test_guards_detect_token_literals,
        test_no_execution_operations,
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
