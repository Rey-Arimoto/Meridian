#!/usr/bin/env python3
"""
PR123: v1.1 Human Narrative Builder v1 - Smoke Tests

Purpose:
    Validate human narrative builder implementation.
    Narrative = Structural Situation Story (not action/recommendation).

Tests:
    1. Engine import works
    2. Empty/invalid context → ERROR narrative record (valid structure)
    3. Minimal valid context → AVAILABLE narrative
    4. Style=CONCISE produces shorter narrative than DETAILED
    5. Narrative contains only allowed vocabulary (no prescriptive terms)
    6. Token literal detection triggers
    7. Numeric pattern detection triggers
    8. Trading verb detection triggers
    9. Warning-only: exit code always 0
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_narrative_import():
    """Test 1: Engine import works"""
    print("Test 1: Engine import works")
    try:
        from narrative import (
            V11HumanNarrativeSchema,
            build_human_narrative_v1,
            check_narrative_record,
            FORBIDDEN_VOCABULARY,
        )
        print("  ✓ Narrative imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_invalid_context_error_record():
    """Test 2: Empty/invalid context → ERROR narrative record (valid structure)"""
    print("\nTest 2: Empty/invalid context → ERROR narrative record")
    from narrative import build_human_narrative_v1, V11HumanNarrativeSchema

    # Test invalid input (None)
    error_record = build_human_narrative_v1(None)

    # Validate it's a valid ERROR record
    if error_record.get("v11_narrative_status") != "ERROR":
        print(f"  ✗ Expected ERROR status, got {error_record.get('v11_narrative_status')}")
        return False

    # Validate structure
    warnings = V11HumanNarrativeSchema.validate_structure(error_record)
    if len(warnings) > 0:
        print(f"  ✗ ERROR record has validation warnings: {warnings}")
        return False

    print("  ✓ Invalid context produces valid ERROR record")
    return True


def test_minimal_valid_context():
    """Test 3: Minimal valid context → AVAILABLE narrative"""
    print("\nTest 3: Minimal valid context → AVAILABLE narrative")
    from narrative import build_human_narrative_v1

    # Minimal valid explanation context
    context = {
        "v11_explain_status": "AVAILABLE",
        "v11_explain_summary": "test summary.",
        "v11_explain_signals": ["REGIME_MEDIUM", "DRIFT_LOW"],
        "v11_explain_basis": ["v11_regime_level", "v10_drift_level"],
    }

    narrative = build_human_narrative_v1(context)

    # Validate status
    if narrative.get("v11_narrative_status") != "AVAILABLE":
        print(f"  ✗ Expected AVAILABLE status, got {narrative.get('v11_narrative_status')}")
        return False

    # Validate text exists
    text = narrative.get("v11_narrative_text", "")
    if not text or len(text) == 0:
        print("  ✗ Narrative text is empty")
        return False

    print(f"  ✓ Valid context produces AVAILABLE narrative")
    print(f"    Text: {text}")
    return True


def test_style_verbosity():
    """Test 4: Style=CONCISE produces shorter narrative than DETAILED"""
    print("\nTest 4: Style verbosity (CONCISE < DETAILED)")
    from narrative import build_human_narrative_v1

    context = {
        "v11_explain_status": "AVAILABLE",
        "v11_explain_summary": "test",
        "v11_explain_signals": ["REGIME_MEDIUM", "DRIFT_LOW", "PERMISSION_DRY_RUN_ONLY"],
        "v11_explain_basis": ["v11_regime_level", "v10_drift_level", "v10_execution_permission"],
    }

    # Generate CONCISE narrative
    concise = build_human_narrative_v1(context, style="CONCISE")
    concise_text = concise.get("v11_narrative_text", "")

    # Generate DETAILED narrative
    detailed = build_human_narrative_v1(context, style="DETAILED")
    detailed_text = detailed.get("v11_narrative_text", "")

    # CONCISE should be shorter than DETAILED
    if len(concise_text) >= len(detailed_text):
        print(f"  ✗ CONCISE ({len(concise_text)} chars) not shorter than DETAILED ({len(detailed_text)} chars)")
        return False

    print(f"  ✓ CONCISE ({len(concise_text)} chars) < DETAILED ({len(detailed_text)} chars)")
    print(f"    CONCISE: {concise_text}")
    print(f"    DETAILED: {detailed_text}")
    return True


def test_allowed_vocabulary():
    """Test 5: Narrative contains only allowed vocabulary (no prescriptive terms)"""
    print("\nTest 5: Narrative contains only allowed vocabulary")
    from narrative import build_human_narrative_v1, FORBIDDEN_VOCABULARY

    context = {
        "v11_explain_status": "AVAILABLE",
        "v11_explain_summary": "test",
        "v11_explain_signals": ["REGIME_HIGH", "DRIFT_MEDIUM"],
        "v11_explain_basis": ["v11_regime_level", "v10_drift_level"],
    }

    narrative = build_human_narrative_v1(context, style="STANDARD")
    text = narrative.get("v11_narrative_text", "").lower()

    # Check for forbidden words
    found_forbidden = []
    for word in FORBIDDEN_VOCABULARY:
        if word.lower() in text:
            found_forbidden.append(word)

    if found_forbidden:
        print(f"  ✗ Forbidden vocabulary found: {found_forbidden}")
        return False

    print("  ✓ Narrative contains only allowed vocabulary")
    return True


def test_token_literal_detection():
    """Test 6: Token literal detection triggers"""
    print("\nTest 6: Token literal detection triggers")
    from narrative import check_narrative_record

    # Dirty narrative with token literals
    dirty_narrative = {
        "v11_narrative_text": "current situation: SUI and USDC activity detected.",
    }

    warnings = check_narrative_record(dirty_narrative)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect token literals")
        return False

    print(f"  ✓ Guards detected token literals: {len(warnings)} warnings")
    return True


def test_numeric_pattern_detection():
    """Test 7: Numeric pattern detection triggers"""
    print("\nTest 7: Numeric pattern detection triggers")
    from narrative import check_narrative_record

    # Dirty narrative with numeric patterns
    dirty_narrative = {
        "v11_narrative_text": "drift detected with 5 terms added and 3 removed. delta=8.",
    }

    warnings = check_narrative_record(dirty_narrative)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect numeric patterns")
        return False

    print(f"  ✓ Guards detected numeric patterns: {len(warnings)} warnings")
    return True


def test_trading_verb_detection():
    """Test 8: Trading verb detection triggers"""
    print("\nTest 8: Trading verb detection triggers")
    from narrative import check_narrative_record

    # Dirty narrative with trading vocabulary
    dirty_narrative = {
        "v11_narrative_text": "approved. execute swap operations now.",
    }

    warnings = check_narrative_record(dirty_narrative)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect trading verbs")
        return False

    print(f"  ✓ Guards detected trading verbs: {len(warnings)} warnings")
    return True


def test_warning_only_behavior():
    """Test 9: Exit code always 0 (warning-only)"""
    print("\nTest 9: Exit code always 0 (warning-only)")
    from narrative import V11HumanNarrativeSchema, check_narrative_record

    # Test various error conditions - none should raise
    test_cases = [
        {},  # Empty dict
        {"invalid": "record"},  # Invalid structure
        {"v11_narrative_mode": "INVALID"},  # Invalid mode
    ]

    for i, test_case in enumerate(test_cases):
        try:
            # Validation should not raise - just return warnings
            warnings = V11HumanNarrativeSchema.validate_structure(test_case)
            print(f"  ✓ Test case {i+1}: No exception raised, {len(warnings)} warnings returned")
        except Exception as e:
            print(f"  ✗ Test case {i+1}: Exception raised: {e}")
            return False

    # Test check_narrative_record doesn't raise
    try:
        warnings = check_narrative_record({"v11_narrative_text": "invalid text with SUI token"})
        print(f"  ✓ check_narrative_record: No exception raised, {len(warnings)} warnings returned")
    except Exception as e:
        print(f"  ✗ check_narrative_record raised exception: {e}")
        return False

    print("  ✓ All error cases handled defensively (warning-only)")
    return True


def main():
    """Run all smoke tests"""
    print("=" * 60)
    print("PR123: v1.1 Human Narrative Builder v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_narrative_import,
        test_invalid_context_error_record,
        test_minimal_valid_context,
        test_style_verbosity,
        test_allowed_vocabulary,
        test_token_literal_detection,
        test_numeric_pattern_detection,
        test_trading_verb_detection,
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
