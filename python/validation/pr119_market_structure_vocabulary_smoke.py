#!/usr/bin/env python3
"""
PR119: v1.0 Market Structure Vocabulary Schema & Builder v1 - Smoke Tests

Purpose:
    Validate market structure vocabulary implementation.
    Vocabulary = Market Structure Language (not price, not ownership).

Tests:
    1. Import works
    2. Empty analytics → valid ERROR/AVAILABLE record (defensive)
    3. Presence mapping works for each term family
    4. No token literals allowed
    5. No numeric patterns allowed
    6. No addresses allowed
    7. No trading/execution vocab allowed
    8. Exit code always 0 (warning-only)
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))


def test_vocabulary_import():
    """Test 1: Import works"""
    print("Test 1: Vocabulary import works")
    try:
        from vocabulary import (
            V10MarketStructureVocabularySchema,
            get_vocabulary_schema_info,
            build_market_structure_vocabulary_v1,
            get_vocabulary_builder_v1_info,
            validate_vocabulary_record,
        )
        print("  ✓ Vocabulary imports successful")
        return True
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_defensive_behavior():
    """Test 2: Empty analytics → valid ERROR/AVAILABLE record (defensive)"""
    print("\nTest 2: Empty analytics → valid ERROR/AVAILABLE record (defensive)")
    from vocabulary import build_market_structure_vocabulary_v1

    # Test with None input
    vocab_none = build_market_structure_vocabulary_v1(None)

    if vocab_none.get("v10_vocab_status") != "ERROR":
        print(f"  ✗ None input did not produce ERROR status: {vocab_none.get('v10_vocab_status')}")
        return False
    print("  ✓ None input produces ERROR status")

    # Test with invalid dict
    vocab_empty = build_market_structure_vocabulary_v1({})

    if vocab_empty.get("v10_vocab_status") != "ERROR":
        print(f"  ✗ Empty dict did not produce ERROR status")
        return False
    print("  ✓ Empty dict produces ERROR status")

    # Test with invalid status
    invalid_analytics = {
        "onchain_analytics_status": "ERROR",
    }
    vocab_invalid = build_market_structure_vocabulary_v1(invalid_analytics)

    if vocab_invalid.get("v10_vocab_status") != "ERROR":
        print(f"  ✗ Invalid status did not produce ERROR status")
        return False
    print("  ✓ Invalid status produces ERROR status")

    return True


def test_presence_mapping():
    """Test 3: Presence mapping works for each term family"""
    print("\nTest 3: Presence mapping works for each term family")
    from vocabulary import build_market_structure_vocabulary_v1

    # Create mock analytics with all term families represented
    mock_analytics = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 5, "MEDIUM": 3, "HIGH": 2},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": True, "HIGH": False},
        "event_activity_frequency": {"TRUE": 4, "FALSE": 6},
        "object_dynamics_distribution": {"DECREASE": 1, "STABLE": 7, "INCREASE": 2},
        "observation_count": 10,
    }

    vocab = build_market_structure_vocabulary_v1(mock_analytics)

    if vocab.get("v10_vocab_status") != "AVAILABLE":
        print(f"  ✗ Vocab status not AVAILABLE: {vocab.get('v10_vocab_status')}")
        return False
    print("  ✓ Vocab status is AVAILABLE")

    terms = vocab.get("v10_vocab_terms", [])

    # Check market cost regime presence
    if "COST_LOW_PRESENT" not in terms:
        print("  ✗ Missing COST_LOW_PRESENT term")
        return False
    if "COST_MEDIUM_PRESENT" not in terms:
        print("  ✗ Missing COST_MEDIUM_PRESENT term")
        return False
    if "COST_HIGH_PRESENT" not in terms:
        print("  ✗ Missing COST_HIGH_PRESENT term")
        return False
    print("  ✓ Market cost regime presence terms mapped correctly")

    # Check liquidity regime presence
    if "LIQUIDITY_LOW_PRESENT" not in terms:
        print("  ✗ Missing LIQUIDITY_LOW_PRESENT term")
        return False
    if "LIQUIDITY_MEDIUM_PRESENT" not in terms:
        print("  ✗ Missing LIQUIDITY_MEDIUM_PRESENT term")
        return False
    if "LIQUIDITY_HIGH_PRESENT" in terms:
        print("  ✗ Unexpected LIQUIDITY_HIGH_PRESENT term (should be absent)")
        return False
    print("  ✓ Liquidity regime presence terms mapped correctly")

    # Check event activity
    if "EVENT_ACTIVITY_PRESENT" not in terms:
        print("  ✗ Missing EVENT_ACTIVITY_PRESENT term")
        return False
    print("  ✓ Event activity terms mapped correctly")

    # Check object dynamics presence
    if "OBJECT_DYNAMICS_DECREASE_PRESENT" not in terms:
        print("  ✗ Missing OBJECT_DYNAMICS_DECREASE_PRESENT term")
        return False
    if "OBJECT_DYNAMICS_STABLE_PRESENT" not in terms:
        print("  ✗ Missing OBJECT_DYNAMICS_STABLE_PRESENT term")
        return False
    if "OBJECT_DYNAMICS_INCREASE_PRESENT" not in terms:
        print("  ✗ Missing OBJECT_DYNAMICS_INCREASE_PRESENT term")
        return False
    print("  ✓ Object dynamics presence terms mapped correctly")

    return True


def test_no_token_literals():
    """Test 4: No token literals allowed"""
    print("\nTest 4: No token literals allowed")
    from vocabulary import validate_vocabulary_record

    # Test dirty vocabulary with token literals
    dirty_vocab = {
        "v10_vocab_summary": "market structure vocabulary with SUI and USDC terms.",
        "v10_vocab_terms": ["COST_LOW_PRESENT"],
    }

    warnings = validate_vocabulary_record(dirty_vocab)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect token literals")
        return False

    print(f"  ✓ Guards detected token literals: {len(warnings)} warnings")
    return True


def test_no_numeric_patterns():
    """Test 5: No numeric patterns allowed"""
    print("\nTest 5: No numeric patterns allowed")
    from vocabulary import validate_vocabulary_record

    # Test dirty vocabulary with numeric patterns (forbidden)
    dirty_vocab = {
        "v10_vocab_summary": "market structure vocabulary for $1000 transaction at 5% fee.",
        "v10_vocab_terms": ["COST_LOW_PRESENT"],
    }

    warnings = validate_vocabulary_record(dirty_vocab)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect numeric patterns")
        return False

    print(f"  ✓ Guards detected numeric patterns: {len(warnings)} warnings")
    return True


def test_no_addresses():
    """Test 6: No addresses allowed"""
    print("\nTest 6: No addresses allowed")
    from vocabulary import validate_vocabulary_record

    # Test dirty vocabulary with addresses
    dirty_vocab = {
        "v10_vocab_summary": "market structure vocabulary for address 0x1234567890abcdef.",
        "v10_vocab_terms": ["COST_LOW_PRESENT"],
    }

    warnings = validate_vocabulary_record(dirty_vocab)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect addresses")
        return False

    print(f"  ✓ Guards detected addresses: {len(warnings)} warnings")
    return True


def test_no_trading_execution_vocab():
    """Test 7: No trading/execution vocab allowed"""
    print("\nTest 7: No trading/execution vocab allowed")
    from vocabulary import validate_vocabulary_record

    # Test dirty vocabulary with trading vocabulary
    dirty_vocab = {
        "v10_vocab_summary": "market structure vocabulary. execute swap operations now.",
        "v10_vocab_terms": ["COST_LOW_PRESENT"],
    }

    warnings = validate_vocabulary_record(dirty_vocab)

    if len(warnings) == 0:
        print("  ✗ Guards did not detect trading vocabulary")
        return False

    print(f"  ✓ Guards detected trading vocabulary: {len(warnings)} warnings")

    # Test dirty vocabulary with invalid terms
    dirty_vocab_terms = {
        "v10_vocab_summary": "market structure vocabulary.",
        "v10_vocab_terms": ["COST_LOW_PRESENT", "INVALID_TERM", "TRADE_NOW"],
    }

    term_warnings = validate_vocabulary_record(dirty_vocab_terms)

    if len(term_warnings) == 0:
        print("  ✗ Guards did not detect invalid terms")
        return False

    print(f"  ✓ Guards detected invalid terms: {len(term_warnings)} warnings")
    return True


def test_warning_only_behavior():
    """Test 8: Exit code always 0 (warning-only)"""
    print("\nTest 8: Exit code always 0 (warning-only)")
    from vocabulary import build_market_structure_vocabulary_v1

    # Test various error conditions - none should raise
    test_cases = [
        None,
        {},
        {"invalid": "data"},
        {"onchain_analytics_status": "ERROR"},
    ]

    for i, test_case in enumerate(test_cases):
        try:
            result = build_market_structure_vocabulary_v1(test_case)  # type: ignore
            if "v10_vocab_status" not in result:
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
    print("PR119: v1.0 Market Structure Vocabulary Schema & Builder v1")
    print("Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        test_vocabulary_import,
        test_defensive_behavior,
        test_presence_mapping,
        test_no_token_literals,
        test_no_numeric_patterns,
        test_no_addresses,
        test_no_trading_execution_vocab,
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
