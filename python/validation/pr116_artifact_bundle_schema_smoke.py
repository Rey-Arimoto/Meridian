#!/usr/bin/env python3
"""
PR116: v1.0 Artifact Bundle Schema v1 - Smoke Tests

Purpose:
    Validate artifact bundle schema implementation.
    Bundle = Container (not decision/evaluation).

Tests:
    1. Schema import works
    2. Empty bundle valid
    3. Minimal bundle with subset artifacts valid
    4. Full bundle with all artifacts valid
    5. Ordering consistency enforced
    6. Guard detects forbidden vocab/token literals/numeric patterns
    7. Defensive behavior works
    8. Exit code always 0
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
        from bundle import (
            V10ArtifactBundleSchema,
            get_bundle_schema_info,
            build_artifact_bundle_v1,
            get_bundle_builder_v1_info,
            validate_bundle_record,
        )
        print("  ✓ Bundle schema imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_empty_bundle_valid():
    """Test 2: Empty bundle valid"""
    print("\nTest 2: Empty bundle valid")
    from bundle import V10ArtifactBundleSchema

    empty = V10ArtifactBundleSchema.create_empty_record()
    warnings = V10ArtifactBundleSchema.validate_structure(empty)

    if len(warnings) == 0:
        print("  ✓ Empty bundle validates")
        return True
    else:
        print(f"  ✗ Empty bundle has warnings: {warnings}")
        return False


def test_minimal_bundle_valid():
    """Test 3: Minimal bundle with subset artifacts valid"""
    print("\nTest 3: Minimal bundle with subset artifacts valid")
    from bundle import V10ArtifactBundleSchema

    minimal_bundle = V10ArtifactBundleSchema.create_bundle_record(
        layers=["REGIME", "POLICY_BINDING"],
        artifacts={
            "REGIME": {"v11_regime_level": "LOW"},
            "POLICY_BINDING": {"v11_execution_permission_override": "DRY_RUN_ONLY"},
        },
        summary="artifact bundle with 2 layers. subset of pipeline.",
        basis=["pipeline_artifacts"],
    )

    # Validate structure
    warnings = V10ArtifactBundleSchema.validate_structure(minimal_bundle)

    if len(warnings) == 0:
        print("  ✓ Minimal bundle validates")
    else:
        print(f"  ✗ Minimal bundle has warnings: {warnings}")
        return False

    # Check that bundle has expected layers
    if len(minimal_bundle.get("v10_bundle_layers", [])) < 2:
        print(f"  ✗ Expected at least 2 layers, got {len(minimal_bundle.get('v10_bundle_layers', []))}")
        return False

    print(f"  ✓ Minimal bundle created with {len(minimal_bundle.get('v10_bundle_layers', []))} layers")
    return True


def test_full_bundle_valid():
    """Test 4: Full bundle with all artifacts valid"""
    print("\nTest 4: Full bundle with all artifacts valid")
    from bundle import build_artifact_bundle_v1

    # Create full orchestrator output
    full_output = {
        "onchain_analytics": {"onchain_analytics_mode": "ON"},
        "regime_record": {"v11_regime_level": "LOW"},
        "policy_record": {"v11_execution_permission_override": "DRY_RUN_ONLY"},
        "execution_plan": {"v10_plan_type": "MAINTENANCE"},
        "preview_record": {"v11_preview_mode": "ON"},
        "approval_gate_record": {"v11_approval_requirement": "NOT_REQUIRED"},
        "registry_record": {"v11_registry_state": "UNREQUESTED"},
    }

    bundle = build_artifact_bundle_v1(full_output)

    if bundle.get("v10_bundle_status") != "AVAILABLE":
        print(f"  ✗ Bundle status not AVAILABLE: {bundle.get('v10_bundle_status')}")
        return False
    print("  ✓ Bundle status is AVAILABLE")

    # Check that all expected layers are present
    expected_layers = [
        "ANALYTICS",
        "REGIME",
        "POLICY_BINDING",
        "PLAN",
        "PREVIEW",
        "APPROVAL_GATE",
        "APPROVAL_REGISTRY",
    ]

    actual_layers = bundle.get("v10_bundle_layers", [])

    if set(actual_layers) != set(expected_layers):
        print(f"  ✗ Layer set mismatch")
        print(f"    Expected: {sorted(expected_layers)}")
        print(f"    Actual: {sorted(actual_layers)}")
        return False

    print(f"  ✓ All {len(expected_layers)} layers present")
    return True


def test_ordering_consistency():
    """Test 5: Ordering consistency enforced"""
    print("\nTest 5: Ordering consistency enforced")
    from bundle import validate_bundle_record

    # Test bundle with mismatched layers and artifacts
    inconsistent_bundle = {
        "v10_bundle_summary": "artifact bundle.",
        "v10_bundle_layers": ["REGIME", "POLICY_BINDING"],
        "v10_bundle_artifacts": {
            "REGIME": {},
            "POLICY_BINDING": {},
            "PREVIEW": {},  # Not in layers list
        },
    }

    warnings = validate_bundle_record(inconsistent_bundle)

    # Should have warnings about ordering inconsistency
    if len(warnings) == 0:
        print("  ✗ Guards did not detect ordering inconsistency")
        return False

    print(f"  ✓ Guards detected ordering inconsistency: {len(warnings)} warnings")

    # Test bundle with consistent ordering
    consistent_bundle = {
        "v10_bundle_summary": "artifact bundle with consistent ordering.",
        "v10_bundle_layers": ["REGIME", "POLICY_BINDING"],
        "v10_bundle_artifacts": {
            "REGIME": {},
            "POLICY_BINDING": {},
        },
    }

    consistent_warnings = validate_bundle_record(consistent_bundle)

    # May have 0 warnings or warnings from other checks, but not ordering warnings
    # Just verify no exception
    print(f"  ✓ Consistent bundle validated (warnings: {len(consistent_warnings)})")
    return True


def test_guards_detect_forbidden_vocab():
    """Test 6: Guards detect forbidden vocab"""
    print("\nTest 6: Guards detect forbidden vocab")
    from bundle import validate_bundle_record

    # Test with trading vocabulary
    dirty_bundle = {
        "v10_bundle_summary": "artifact bundle complete. execute swap operations.",
        "v10_bundle_layers": ["REGIME"],
        "v10_bundle_artifacts": {"REGIME": {}},
    }

    warnings = validate_bundle_record(dirty_bundle)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect trading vocabulary")
        return False

    print(f"  ✓ Guards detected forbidden vocabulary: {len(warnings)} warnings")

    # Test with bundle overreach
    overreach_bundle = {
        "v10_bundle_summary": "bundle recommends executing operations.",
    }

    overreach_warnings = validate_bundle_record(overreach_bundle)

    if len(overreach_warnings) == 0:
        print("  ✗ Guards did not detect bundle overreach")
        return False

    print(f"  ✓ Guards detected bundle overreach: {len(overreach_warnings)} warnings")
    return True


def test_guards_detect_token_literals():
    """Test 7: Guards detect token literals / numeric patterns / addresses"""
    print("\nTest 7: Guards detect token literals / numeric patterns / addresses")
    from bundle import validate_bundle_record

    # Test token literals
    token_bundle = {
        "v10_bundle_summary": "artifact bundle with SUI and USDC layers.",
    }

    token_warnings = validate_bundle_record(token_bundle)

    if len(token_warnings) == 0:
        print("  ✗ Guards did not detect token literals")
        return False

    print(f"  ✓ Guards detected token literals: {len(token_warnings)} warnings")

    # Test numeric patterns
    numeric_bundle = {
        "v10_bundle_summary": "artifact bundle for $1000 operation.",
    }

    numeric_warnings = validate_bundle_record(numeric_bundle)

    if len(numeric_warnings) == 0:
        print("  ✗ Guards did not detect numeric patterns")
        return False

    print(f"  ✓ Guards detected numeric patterns: {len(numeric_warnings)} warnings")

    # Test addresses
    address_bundle = {
        "v10_bundle_summary": "artifact bundle for 0x1234567890abcdef.",
    }

    address_warnings = validate_bundle_record(address_bundle)

    if len(address_warnings) == 0:
        print("  ✗ Guards did not detect address patterns")
        return False

    print(f"  ✓ Guards detected address patterns: {len(address_warnings)} warnings")
    return True


def test_warning_only_behavior():
    """Test 8: Exit code always 0 (warning-only)"""
    print("\nTest 8: Exit code always 0 (warning-only)")
    from bundle import build_artifact_bundle_v1

    # Test various error conditions - none should raise
    test_cases = [
        None,
        "invalid",
        {},
        {"invalid": "data"},
        {"regime_record": "not_a_dict"},
    ]

    for i, test_case in enumerate(test_cases):
        try:
            result = build_artifact_bundle_v1(test_case)  # type: ignore
            if "v10_bundle_status" not in result:
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
    print("PR116: v1.0 Artifact Bundle Schema v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_schema_import,
        test_empty_bundle_valid,
        test_minimal_bundle_valid,
        test_full_bundle_valid,
        test_ordering_consistency,
        test_guards_detect_forbidden_vocab,
        test_guards_detect_token_literals,
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
