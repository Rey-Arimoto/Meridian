#!/usr/bin/env python3
"""
PR120: v1.0 Market Structure Drift Detection Engine v1 - Smoke Tests

Purpose:
    Validate market structure drift detection implementation.
    Drift = Structural Language Shift (not evaluation, not prediction).

Tests:
    1. Import works
    2. No delta → DRIFT_NONE
    3. Small delta → DRIFT_LOW
    4. Moderate delta → DRIFT_MEDIUM
    5. Large delta → DRIFT_HIGH or DRIFT_CRITICAL
    6. Evidence contains only term strings (no numbers)
    7. Guard catches numeric patterns in summary/evidence
    8. Guard catches token literals
    9. Exit code always 0 (warning-only)
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_drift_import():
    """Test 1: Import works"""
    print("Test 1: Drift import works")
    try:
        from drift import (
            V10MarketStructureDriftSchema,
            get_drift_schema_info,
            detect_market_structure_drift_v1,
            get_drift_engine_v1_info,
            validate_drift_record,
        )
        print("  ✓ Drift imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_no_drift():
    """Test 2: No delta → DRIFT_NONE"""
    print("\nTest 2: No delta → DRIFT_NONE")
    from drift import detect_market_structure_drift_v1

    # Create identical vocab windows
    vocab_record_1 = {
        "v10_vocab_terms": ["COST_LOW_PRESENT", "LIQUIDITY_LOW_PRESENT", "EVENT_ACTIVITY_ABSENT"],
    }
    window_A = [vocab_record_1]
    window_B = [vocab_record_1]

    drift = detect_market_structure_drift_v1(window_A, window_B)

    if drift.get("v10_drift_level") != "DRIFT_NONE":
        print(f"  ✗ Expected DRIFT_NONE, got {drift.get('v10_drift_level')}")
        return False

    evidence = drift.get("v10_drift_evidence", [])
    if len(evidence) != 0:
        print(f"  ✗ Expected 0 evidence items, got {len(evidence)}")
        return False

    print("  ✓ No delta produces DRIFT_NONE with no evidence")
    return True


def test_low_drift():
    """Test 3: Small delta → DRIFT_LOW"""
    print("\nTest 3: Small delta → DRIFT_LOW")
    from drift import detect_market_structure_drift_v1

    # Create vocab windows with small change (1-2 terms)
    vocab_record_A = {
        "v10_vocab_terms": ["COST_LOW_PRESENT", "LIQUIDITY_LOW_PRESENT", "EVENT_ACTIVITY_ABSENT"],
    }
    vocab_record_B = {
        "v10_vocab_terms": ["COST_LOW_PRESENT", "COST_MEDIUM_PRESENT", "LIQUIDITY_LOW_PRESENT"],
    }
    window_A = [vocab_record_A]
    window_B = [vocab_record_B]

    drift = detect_market_structure_drift_v1(window_A, window_B)

    if drift.get("v10_drift_level") != "DRIFT_LOW":
        print(f"  ✗ Expected DRIFT_LOW, got {drift.get('v10_drift_level')}")
        return False

    evidence = drift.get("v10_drift_evidence", [])
    if len(evidence) == 0:
        print("  ✗ Expected non-empty evidence list")
        return False

    print(f"  ✓ Small delta produces DRIFT_LOW with {len(evidence)} evidence items")
    return True


def test_medium_drift():
    """Test 4: Moderate delta → DRIFT_MEDIUM"""
    print("\nTest 4: Moderate delta → DRIFT_MEDIUM")
    from drift import detect_market_structure_drift_v1

    # Create vocab windows with moderate change (3-4 terms)
    vocab_record_A = {
        "v10_vocab_terms": ["COST_LOW_PRESENT", "LIQUIDITY_LOW_PRESENT"],
    }
    vocab_record_B = {
        "v10_vocab_terms": ["COST_HIGH_PRESENT", "LIQUIDITY_HIGH_PRESENT", "EVENT_ACTIVITY_PRESENT"],
    }
    window_A = [vocab_record_A]
    window_B = [vocab_record_B]

    drift = detect_market_structure_drift_v1(window_A, window_B)

    drift_level = drift.get("v10_drift_level")
    if drift_level not in ["DRIFT_MEDIUM", "DRIFT_HIGH"]:
        print(f"  ✗ Expected DRIFT_MEDIUM or DRIFT_HIGH, got {drift_level}")
        return False

    evidence = drift.get("v10_drift_evidence", [])
    if len(evidence) == 0:
        print("  ✗ Expected non-empty evidence list")
        return False

    print(f"  ✓ Moderate delta produces {drift_level} with {len(evidence)} evidence items")
    return True


def test_high_critical_drift():
    """Test 5: Large delta → DRIFT_HIGH or DRIFT_CRITICAL"""
    print("\nTest 5: Large delta → DRIFT_HIGH or DRIFT_CRITICAL")
    from drift import detect_market_structure_drift_v1

    # Create vocab windows with large change (7+ terms)
    vocab_record_A = {
        "v10_vocab_terms": [
            "COST_LOW_PRESENT",
            "COST_MEDIUM_PRESENT",
            "LIQUIDITY_LOW_PRESENT",
            "EVENT_ACTIVITY_ABSENT",
        ],
    }
    vocab_record_B = {
        "v10_vocab_terms": [
            "COST_HIGH_PRESENT",
            "LIQUIDITY_HIGH_PRESENT",
            "LIQUIDITY_MEDIUM_PRESENT",
            "EVENT_ACTIVITY_PRESENT",
            "OBJECT_DYNAMICS_INCREASE_PRESENT",
        ],
    }
    window_A = [vocab_record_A]
    window_B = [vocab_record_B]

    drift = detect_market_structure_drift_v1(window_A, window_B)

    drift_level = drift.get("v10_drift_level")
    if drift_level not in ["DRIFT_HIGH", "DRIFT_CRITICAL"]:
        print(f"  ✗ Expected DRIFT_HIGH or DRIFT_CRITICAL, got {drift_level}")
        return False

    evidence = drift.get("v10_drift_evidence", [])
    if len(evidence) == 0:
        print("  ✗ Expected non-empty evidence list")
        return False

    print(f"  ✓ Large delta produces {drift_level} with {len(evidence)} evidence items")
    return True


def test_evidence_format():
    """Test 6: Evidence contains only term strings (no numbers)"""
    print("\nTest 6: Evidence contains only term strings (no numbers)")
    from drift import detect_market_structure_drift_v1

    # Create vocab windows with changes
    vocab_record_A = {
        "v10_vocab_terms": ["COST_LOW_PRESENT", "EVENT_ACTIVITY_ABSENT"],
    }
    vocab_record_B = {
        "v10_vocab_terms": ["COST_HIGH_PRESENT", "EVENT_ACTIVITY_PRESENT"],
    }
    window_A = [vocab_record_A]
    window_B = [vocab_record_B]

    drift = detect_market_structure_drift_v1(window_A, window_B)

    evidence = drift.get("v10_drift_evidence", [])

    # Check all evidence items are strings
    for item in evidence:
        if not isinstance(item, str):
            print(f"  ✗ Evidence item is not string: {item}")
            return False

        # Check no numbers in evidence (except in term names like v10_)
        # Evidence should be like "COST_LOW_PRESENT_ADDED" or "EVENT_ACTIVITY_ABSENT_REMOVED"
        if not (item.endswith("_ADDED") or item.endswith("_REMOVED")):
            print(f"  ✗ Evidence item has unexpected format: {item}")
            return False

    # Check summary has no counts
    summary = drift.get("v10_drift_summary", "")
    import re
    # Check for numeric patterns like "3 terms", "5 changes", etc.
    if re.search(r'\d+\s+terms?', summary, re.IGNORECASE):
        print(f"  ✗ Summary contains term count: {summary}")
        return False
    if re.search(r'\d+\s+changes?', summary, re.IGNORECASE):
        print(f"  ✗ Summary contains change count: {summary}")
        return False

    print(f"  ✓ Evidence contains only term strings ({len(evidence)} items), no numeric counts in summary")
    return True


def test_guard_numeric_patterns():
    """Test 7: Guard catches numeric patterns in summary/evidence"""
    print("\nTest 7: Guard catches numeric patterns in summary/evidence")
    from drift import validate_drift_record

    # Create dirty drift with numeric patterns
    dirty_drift = {
        "v10_drift_summary": "market structure drift detected. 5 terms added and 3 terms removed. delta=8.",
        "v10_drift_level": "DRIFT_HIGH",
        "v10_drift_evidence": ["COST_HIGH_PRESENT_ADDED"],
    }

    warnings = validate_drift_record(dirty_drift)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect numeric patterns")
        return False

    print(f"  ✓ Guards detected numeric patterns: {len(warnings)} warnings")
    return True


def test_guard_token_literals():
    """Test 8: Guard catches token literals"""
    print("\nTest 8: Guard catches token literals")
    from drift import validate_drift_record

    # Create dirty drift with token literals
    dirty_drift = {
        "v10_drift_summary": "market structure drift with SUI and USDC activity changes.",
        "v10_drift_level": "DRIFT_LOW",
        "v10_drift_evidence": [],
    }

    warnings = validate_drift_record(dirty_drift)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect token literals")
        return False

    print(f"  ✓ Guards detected token literals: {len(warnings)} warnings")
    return True


def test_warning_only_behavior():
    """Test 9: Exit code always 0 (warning-only)"""
    print("\nTest 9: Exit code always 0 (warning-only)")
    from drift import detect_market_structure_drift_v1

    # Test various error conditions - none should raise
    test_cases = [
        (None, None),
        ([], []),
        ([{"invalid": "record"}], [{"invalid": "record"}]),
        ([{}], [{}]),
    ]

    for i, (window_A, window_B) in enumerate(test_cases):
        try:
            result = detect_market_structure_drift_v1(window_A, window_B)
            if "v10_drift_status" not in result:
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
    print("PR120: v1.0 Market Structure Drift Detection Engine v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_drift_import,
        test_no_drift,
        test_low_drift,
        test_medium_drift,
        test_high_critical_drift,
        test_evidence_format,
        test_guard_numeric_patterns,
        test_guard_token_literals,
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
