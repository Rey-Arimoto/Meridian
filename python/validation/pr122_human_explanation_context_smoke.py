#!/usr/bin/env python3
"""
PR122: v1.1 Human Explanation Context Schema v1 - Smoke Tests

Purpose:
    Validate human explanation context implementation.
    Explanation Context = Structural Situation Summary (not action/recommendation).

Tests:
    1. Import works
    2. Empty record valid
    3. Full record valid
    4. Guards detect token literals
    5. Guards detect numeric patterns
    6. Guards detect trading vocabulary
    7. Guards detect prescriptive coupling (NEW)
    8. Signals are label-only (no embedded values)
    9. Exit code always 0 (warning-only)
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_explanation_import():
    """Test 1: Import works"""
    print("Test 1: Explanation context import works")
    try:
        from explain import (
            V11HumanExplanationContextSchema,
            get_explanation_schema_info,
            validate_explanation_context,
            check_prescriptive_coupling,
        )
        print("  ✓ Explanation context imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_empty_record():
    """Test 2: Empty record valid"""
    print("\nTest 2: Empty record valid")
    from explain import V11HumanExplanationContextSchema

    # Create empty record
    empty = V11HumanExplanationContextSchema.create_empty_record()

    # Validate required fields
    if empty.get("v11_explain_mode") != "ON":
        print(f"  ✗ Expected mode ON, got {empty.get('v11_explain_mode')}")
        return False

    if empty.get("v11_explain_status") != "UNAVAILABLE":
        print(f"  ✗ Expected status UNAVAILABLE, got {empty.get('v11_explain_status')}")
        return False

    # Validate structure
    warnings = V11HumanExplanationContextSchema.validate_structure(empty)
    if len(warnings) > 0:
        print(f"  ✗ Empty record has validation warnings: {warnings}")
        return False

    print("  ✓ Empty record is valid")
    return True


def test_full_record():
    """Test 3: Full record valid"""
    print("\nTest 3: Full record valid")
    from explain import V11HumanExplanationContextSchema

    # Create full record
    explanation = V11HumanExplanationContextSchema.create_explanation_record(
        summary="current structural situation: regime medium, drift low, permission dry-run-only.",
        signals=["REGIME_MEDIUM", "DRIFT_LOW", "PERMISSION_DRY_RUN_ONLY"],
        basis=["v11_regime_level", "v10_drift_level", "v10_execution_permission"],
        artifacts=["pr110_regime_record", "pr120_drift_record", "pr101_execution_record"],
    )

    # Validate required fields
    if explanation.get("v11_explain_mode") != "ON":
        print(f"  ✗ Expected mode ON, got {explanation.get('v11_explain_mode')}")
        return False

    if explanation.get("v11_explain_status") != "AVAILABLE":
        print(f"  ✗ Expected status AVAILABLE, got {explanation.get('v11_explain_status')}")
        return False

    # Validate signals
    signals = explanation.get("v11_explain_signals", [])
    if len(signals) != 3:
        print(f"  ✗ Expected 3 signals, got {len(signals)}")
        return False

    # Validate basis
    basis = explanation.get("v11_explain_basis", [])
    if len(basis) != 3:
        print(f"  ✗ Expected 3 basis fields, got {len(basis)}")
        return False

    # Validate artifacts
    artifacts = explanation.get("v11_explain_artifacts", [])
    if len(artifacts) != 3:
        print(f"  ✗ Expected 3 artifacts, got {len(artifacts)}")
        return False

    # Validate structure
    warnings = V11HumanExplanationContextSchema.validate_structure(explanation)
    if len(warnings) > 0:
        print(f"  ✗ Full record has validation warnings: {warnings}")
        return False

    print("  ✓ Full record is valid")
    return True


def test_guards_detect_token_literals():
    """Test 4: Guards detect token literals"""
    print("\nTest 4: Guards detect token literals")
    from explain import validate_explanation_context

    # Dirty context with token literals
    dirty_token = {
        "v11_explain_summary": "current situation: SUI and USDC activity detected at address 0x1234.",
        "v11_explain_signals": [],
    }

    warnings = validate_explanation_context(dirty_token)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect token literals")
        return False

    print(f"  ✓ Guards detected token literals: {len(warnings)} warnings")
    return True


def test_guards_detect_numeric_patterns():
    """Test 5: Guards detect numeric patterns"""
    print("\nTest 5: Guards detect numeric patterns")
    from explain import validate_explanation_context

    # Dirty context with numeric patterns
    dirty_numeric = {
        "v11_explain_summary": "drift detected with 5 terms added and 3 removed. delta=8. 50% change rate.",
        "v11_explain_signals": [],
    }

    warnings = validate_explanation_context(dirty_numeric)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect numeric patterns")
        return False

    print(f"  ✓ Guards detected numeric patterns: {len(warnings)} warnings")
    return True


def test_guards_detect_trading_vocabulary():
    """Test 6: Guards detect trading vocabulary"""
    print("\nTest 6: Guards detect trading vocabulary")
    from explain import validate_explanation_context

    # Dirty context with trading vocabulary
    dirty_trading = {
        "v11_explain_summary": "approved. execute swap operations now. transfer funds and sign transaction.",
        "v11_explain_signals": [],
    }

    warnings = validate_explanation_context(dirty_trading)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect trading vocabulary")
        return False

    print(f"  ✓ Guards detected trading vocabulary: {len(warnings)} warnings")
    return True


def test_guards_detect_prescriptive_coupling():
    """Test 7: Guards detect prescriptive coupling (NEW)"""
    print("\nTest 7: Guards detect prescriptive coupling")
    from explain import validate_explanation_context

    # Test case 1: "if approved then execute"
    dirty_coupling_1 = {
        "v11_explain_summary": "approval state available. if approved then execute the swap operation.",
        "v11_explain_signals": [],
    }

    warnings_1 = validate_explanation_context(dirty_coupling_1)
    if len(warnings_1) == 0:
        print("  ✗ Guards did not detect 'if approved then execute' coupling")
        return False

    # Test case 2: "approved therefore execute"
    dirty_coupling_2 = {
        "v11_explain_summary": "approved therefore execute trade.",
        "v11_explain_signals": [],
    }

    warnings_2 = validate_explanation_context(dirty_coupling_2)
    if len(warnings_2) == 0:
        print("  ✗ Guards did not detect 'approved therefore execute' coupling")
        return False

    # Test case 3: "upon approval execute"
    dirty_coupling_3 = {
        "v11_explain_summary": "upon approval execute the transaction.",
        "v11_explain_signals": [],
    }

    warnings_3 = validate_explanation_context(dirty_coupling_3)
    if len(warnings_3) == 0:
        print("  ✗ Guards did not detect 'upon approval execute' coupling")
        return False

    print(f"  ✓ Guards detected prescriptive coupling in all test cases")
    return True


def test_signals_label_only():
    """Test 8: Signals are label-only (no embedded values)"""
    print("\nTest 8: Signals are label-only (no embedded values)")
    from explain import validate_explanation_context

    # Clean signals (label-only)
    clean_signals = {
        "v11_explain_summary": "test",
        "v11_explain_signals": ["REGIME_MEDIUM", "DRIFT_LOW", "PERMISSION_DRY_RUN_ONLY"],
    }

    clean_warnings = validate_explanation_context(clean_signals)
    if len(clean_warnings) > 0:
        print(f"  ✗ Clean signals triggered warnings: {clean_warnings}")
        return False

    # Dirty signals (contains "5 added" pattern which should be caught)
    dirty_signals = {
        "v11_explain_summary": "test",
        "v11_explain_signals": ["REGIME_MEDIUM", "5 added"],  # Invalid - contains numeric pattern
    }

    dirty_warnings = validate_explanation_context(dirty_signals)
    if len(dirty_warnings) == 0:
        print("  ✗ Guards did not detect invalid signal pattern")
        return False

    print(f"  ✓ Signals are validated as label-only")
    return True


def test_warning_only_behavior():
    """Test 9: Exit code always 0 (warning-only)"""
    print("\nTest 9: Exit code always 0 (warning-only)")
    from explain import V11HumanExplanationContextSchema

    # Test various error conditions - none should raise
    test_cases = [
        {},  # Empty dict
        {"invalid": "record"},  # Invalid structure
        {"v11_explain_mode": "INVALID"},  # Invalid mode
    ]

    for i, test_case in enumerate(test_cases):
        try:
            # Validation should not raise - just return warnings
            warnings = V11HumanExplanationContextSchema.validate_structure(test_case)
            print(f"  ✓ Test case {i+1}: No exception raised, {len(warnings)} warnings returned")
        except Exception as e:
            print(f"  ✗ Test case {i+1}: Exception raised: {e}")
            return False

    print("  ✓ All error cases handled defensively (warning-only)")
    return True


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("PR122: v1.1 Human Explanation Context Schema v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_explanation_import,
        test_empty_record,
        test_full_record,
        test_guards_detect_token_literals,
        test_guards_detect_numeric_patterns,
        test_guards_detect_trading_vocabulary,
        test_guards_detect_prescriptive_coupling,
        test_signals_label_only,
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
