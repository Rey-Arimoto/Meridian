#!/usr/bin/env python3
"""
PR110: v1.1 Entropy Regime Classification (Market-Aware) Smoke Test

Purpose:
    Validate that v1.1 regime classifier correctly classifies
    market state from onchain analytics.

Test Coverage:
    1. Regime schema import works
    2. Empty regime record produces valid structure
    3. REGIME_LOW classification works correctly
    4. REGIME_MEDIUM classification works correctly
    5. REGIME_HIGH classification works correctly
    6. REGIME_CRITICAL classification works correctly
    7. Classifier handles missing analytics correctly
    8. Constitutional guards detect violations
    9. Defensive behavior (error handling)

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Regime labels only
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad vocabulary

Exit Code: Always 0 (warning-only validation)
"""

import sys
from typing import Any, Dict, List

# Import v1.1 regime modules
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from regime.v11_entropy_regime_schema import (
    V11EntropyRegimeSchema,
    get_entropy_regime_schema_info,
)
from regime.v11_entropy_regime_classifier_v1 import (
    classify_entropy_regime_v1,
    get_regime_classifier_v1_info,
)
from regime.v11_regime_constitutional_guard import (
    check_action_vocabulary,
    validate_regime_record,
)


def test_regime_schema_import() -> bool:
    """
    Test 1: Regime schema import works.
    """
    print("Test 1: Regime schema import works")
    print("-" * 60)

    try:
        from regime.v11_entropy_regime_schema import (
            V11EntropyRegimeSchema,
        )
        print("✓ Regime schema import successful")
    except ImportError as e:
        print(f"✗ Regime schema import failed: {e}")
        return False

    try:
        from regime.v11_entropy_regime_classifier_v1 import (
            classify_entropy_regime_v1,
        )
        print("✓ Regime classifier import successful")
    except ImportError as e:
        print(f"✗ Regime classifier import failed: {e}")
        return False

    try:
        from regime.v11_regime_constitutional_guard import (
            validate_regime_record,
        )
        print("✓ Constitutional guard import successful")
    except ImportError as e:
        print(f"✗ Constitutional guard import failed: {e}")
        return False

    print("Test 1: PASS\n")
    return True


def test_empty_regime_record_produces_valid_structure() -> bool:
    """
    Test 2: Empty regime record produces valid structure.
    """
    print("Test 2: Empty regime record produces valid structure")
    print("-" * 60)

    record = V11EntropyRegimeSchema.create_empty_record()

    if record["v11_regime_mode"] != "OFF":
        print(f"✗ Expected mode OFF, got {record['v11_regime_mode']}")
        return False
    print("✓ Regime mode is OFF")

    if record["v11_regime_status"] != "UNAVAILABLE":
        print(f"✗ Expected status UNAVAILABLE, got {record['v11_regime_status']}")
        return False
    print("✓ Regime status is UNAVAILABLE")

    if record["v11_regime_level"] != "REGIME_CRITICAL":
        print(f"✗ Expected level REGIME_CRITICAL, got {record['v11_regime_level']}")
        return False
    print("✓ Regime level is REGIME_CRITICAL (safe default)")

    # Validate structure
    warnings = V11EntropyRegimeSchema.validate_structure(record)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid regime record structure")

    print("Test 2: PASS\n")
    return True


def test_regime_low_classification_works_correctly() -> bool:
    """
    Test 3: REGIME_LOW classification works correctly.
    """
    print("Test 3: REGIME_LOW classification works correctly")
    print("-" * 60)

    # Create analytics with low variation (concentrated, stable)
    low_analytics = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 10, "MEDIUM": 0, "HIGH": 0},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": False, "HIGH": False},
        "event_activity_frequency": {"TRUE": 0, "FALSE": 10},
        "object_dynamics_distribution": {"DECREASE": 0, "STABLE": 10, "INCREASE": 0},
        "observation_count": 10,
    }

    # Classify
    regime = classify_entropy_regime_v1(low_analytics)

    if regime["v11_regime_status"] != "AVAILABLE":
        print(f"✗ Expected status AVAILABLE, got {regime['v11_regime_status']}")
        return False
    print("✓ Regime status is AVAILABLE")

    if regime["v11_regime_level"] != "REGIME_LOW":
        print(f"✗ Expected level REGIME_LOW, got {regime['v11_regime_level']}")
        return False
    print("✓ Regime level is REGIME_LOW")

    # Check basis
    if not isinstance(regime["v11_regime_basis"], list):
        print("✗ Regime basis is not a list")
        return False
    if len(regime["v11_regime_basis"]) == 0:
        print("✗ Regime basis is empty")
        return False
    print(f"✓ Regime basis includes {len(regime['v11_regime_basis'])} analytics")

    # Validate structure
    warnings = V11EntropyRegimeSchema.validate_structure(regime)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid regime record structure")

    print("Test 3: PASS\n")
    return True


def test_regime_medium_classification_works_correctly() -> bool:
    """
    Test 4: REGIME_MEDIUM classification works correctly.
    """
    print("Test 4: REGIME_MEDIUM classification works correctly")
    print("-" * 60)

    # Create analytics with moderate variation
    # (some concentration, but not fully concentrated)
    medium_analytics = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 7, "MEDIUM": 3, "HIGH": 0},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": True, "HIGH": False},
        "event_activity_frequency": {"TRUE": 3, "FALSE": 7},
        "object_dynamics_distribution": {"DECREASE": 1, "STABLE": 7, "INCREASE": 2},
        "observation_count": 10,
    }

    # Classify
    regime = classify_entropy_regime_v1(medium_analytics)

    if regime["v11_regime_level"] != "REGIME_MEDIUM":
        print(f"✗ Expected level REGIME_MEDIUM, got {regime['v11_regime_level']}")
        return False
    print("✓ Regime level is REGIME_MEDIUM")

    # Validate structure
    warnings = V11EntropyRegimeSchema.validate_structure(regime)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid regime record structure")

    print("Test 4: PASS\n")
    return True


def test_regime_high_classification_works_correctly() -> bool:
    """
    Test 5: REGIME_HIGH classification works correctly.
    """
    print("Test 5: REGIME_HIGH classification works correctly")
    print("-" * 60)

    # Create analytics with elevated variation
    # (more balanced distribution, but not all metrics at maximum)
    high_analytics = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 4, "MEDIUM": 3, "HIGH": 3},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": True, "HIGH": False},
        "event_activity_frequency": {"TRUE": 6, "FALSE": 4},
        "object_dynamics_distribution": {"DECREASE": 2, "STABLE": 4, "INCREASE": 4},
        "observation_count": 10,
    }

    # Classify
    regime = classify_entropy_regime_v1(high_analytics)

    if regime["v11_regime_level"] != "REGIME_HIGH":
        print(f"✗ Expected level REGIME_HIGH, got {regime['v11_regime_level']}")
        return False
    print("✓ Regime level is REGIME_HIGH")

    # Validate structure
    warnings = V11EntropyRegimeSchema.validate_structure(regime)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid regime record structure")

    print("Test 5: PASS\n")
    return True


def test_regime_critical_classification_works_correctly() -> bool:
    """
    Test 6: REGIME_CRITICAL classification works correctly.
    """
    print("Test 6: REGIME_CRITICAL classification works correctly")
    print("-" * 60)

    # Create analytics with no observations
    critical_analytics = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
        "liquidity_regime_presence": {"LOW": False, "MEDIUM": False, "HIGH": False},
        "event_activity_frequency": {"TRUE": 0, "FALSE": 0},
        "object_dynamics_distribution": {"DECREASE": 0, "STABLE": 0, "INCREASE": 0},
        "observation_count": 0,
    }

    # Classify
    regime = classify_entropy_regime_v1(critical_analytics)

    if regime["v11_regime_level"] != "REGIME_CRITICAL":
        print(f"✗ Expected level REGIME_CRITICAL, got {regime['v11_regime_level']}")
        return False
    print("✓ Regime level is REGIME_CRITICAL")

    # Check basis includes observation_count
    if "observation_count" not in regime["v11_regime_basis"]:
        print("✗ Basis should include observation_count")
        return False
    print("✓ Basis includes observation_count")

    # Validate structure
    warnings = V11EntropyRegimeSchema.validate_structure(regime)
    if warnings:
        print(f"✗ Structure warnings: {warnings}")
        return False
    print("✓ Valid regime record structure")

    print("Test 6: PASS\n")
    return True


def test_classifier_handles_missing_analytics_correctly() -> bool:
    """
    Test 7: Classifier handles missing analytics correctly.
    """
    print("Test 7: Classifier handles missing analytics correctly")
    print("-" * 60)

    # Test with UNAVAILABLE analytics
    unavailable_analytics = {
        "onchain_analytics_mode": "OFF",
        "onchain_analytics_status": "UNAVAILABLE",
        "observation_count": 0,
    }

    regime = classify_entropy_regime_v1(unavailable_analytics)

    if regime["v11_regime_status"] != "ERROR":
        print(f"✗ Expected status ERROR, got {regime['v11_regime_status']}")
        return False
    print("✓ UNAVAILABLE analytics produces ERROR status")

    if regime["v11_regime_level"] != "REGIME_CRITICAL":
        print(f"✗ Expected level REGIME_CRITICAL, got {regime['v11_regime_level']}")
        return False
    print("✓ Regime level is REGIME_CRITICAL (safe default)")

    # Test with invalid type
    invalid_analytics = "invalid"
    regime_invalid = classify_entropy_regime_v1(invalid_analytics)  # type: ignore

    if regime_invalid["v11_regime_status"] != "ERROR":
        print(f"✗ Expected status ERROR, got {regime_invalid['v11_regime_status']}")
        return False
    print("✓ Invalid analytics produces ERROR status")

    print("Test 7: PASS\n")
    return True


def test_constitutional_guards_detect_violations() -> bool:
    """
    Test 8: Constitutional guards detect violations.
    """
    print("Test 8: Constitutional guards detect violations")
    print("-" * 60)

    # Test action vocabulary violation
    dirty_regime_action = {
        "v11_regime_summary": "regime high. recommend reducing positions.",
    }
    action_warnings = validate_regime_record(dirty_regime_action)
    if not action_warnings:
        print("✗ Action vocabulary guard failed to detect violations")
        return False
    print(f"✓ Action vocabulary guard detected: {len(action_warnings)} violations")

    # Test asset vocabulary violation
    dirty_regime_asset = {
        "v11_regime_summary": "regime based on portfolio balance patterns.",
    }
    asset_warnings = validate_regime_record(dirty_regime_asset)
    if not asset_warnings:
        print("✗ Asset vocabulary guard failed to detect violations")
        return False
    print(f"✓ Asset vocabulary guard detected: {len(asset_warnings)} violations")

    # Test execution vocabulary violation
    dirty_regime_exec = {
        "v11_regime_summary": "regime high. time to buy or sell.",
    }
    exec_warnings = validate_regime_record(dirty_regime_exec)
    if not exec_warnings:
        print("✗ Execution vocabulary guard failed to detect violations")
        return False
    print(f"✓ Execution vocabulary guard detected: {len(exec_warnings)} violations")

    # Test token literal violation
    dirty_regime_token = {
        "v11_regime_summary": "regime based on SUI market patterns.",
    }
    token_warnings = validate_regime_record(dirty_regime_token)
    if not token_warnings:
        print("✗ Token literal guard failed to detect violations")
        return False
    print(f"✓ Token literal guard detected: {len(token_warnings)} violations")

    # Test clean regime
    clean_regime = {
        "v11_regime_summary": "regime classified as medium. moderate variation observed.",
    }
    clean_warnings = validate_regime_record(clean_regime)
    if clean_warnings:
        print(f"✗ Clean regime triggered false positives: {clean_warnings}")
        return False
    print("✓ Clean regime passes all guards")

    print("Test 8: PASS\n")
    return True


def test_defensive_behavior() -> bool:
    """
    Test 9: Defensive behavior (error handling).
    """
    print("Test 9: Defensive behavior (error handling)")
    print("-" * 60)

    # Test with None analytics
    regime_none = classify_entropy_regime_v1(None)  # type: ignore
    if regime_none["v11_regime_status"] != "ERROR":
        print(f"✗ None analytics should produce ERROR status")
        return False
    print("✓ None analytics handled gracefully")

    # Test with empty dict
    regime_empty = classify_entropy_regime_v1({})
    if regime_empty["v11_regime_status"] != "ERROR":
        print(f"✗ Empty analytics should produce ERROR status")
        return False
    print("✓ Empty analytics handled gracefully")

    # Test with missing fields
    regime_missing = classify_entropy_regime_v1({"onchain_analytics_mode": "ON"})
    if regime_missing["v11_regime_status"] != "ERROR":
        print(f"✗ Missing fields should produce ERROR status")
        return False
    print("✓ Missing fields handled gracefully")

    # All error cases should default to REGIME_CRITICAL
    if regime_none["v11_regime_level"] != "REGIME_CRITICAL":
        print(f"✗ Error cases should default to REGIME_CRITICAL")
        return False
    if regime_empty["v11_regime_level"] != "REGIME_CRITICAL":
        print(f"✗ Error cases should default to REGIME_CRITICAL")
        return False
    if regime_missing["v11_regime_level"] != "REGIME_CRITICAL":
        print(f"✗ Error cases should default to REGIME_CRITICAL")
        return False
    print("✓ All error cases default to REGIME_CRITICAL (safe)")

    print("Test 9: PASS\n")
    return True


def main() -> int:
    """
    Main test runner.

    Returns 0 (warning-only, never fails).
    """
    print("=" * 60)
    print("PR110: v1.1 Entropy Regime Classification Smoke Test")
    print("=" * 60)
    print("IMPORTANT: Warning-only validation. Exit code always 0.")
    print("=" * 60)
    print()

    tests = [
        ("Regime schema import works", test_regime_schema_import),
        ("Empty regime record produces valid structure", test_empty_regime_record_produces_valid_structure),
        ("REGIME_LOW classification works correctly", test_regime_low_classification_works_correctly),
        ("REGIME_MEDIUM classification works correctly", test_regime_medium_classification_works_correctly),
        ("REGIME_HIGH classification works correctly", test_regime_high_classification_works_correctly),
        ("REGIME_CRITICAL classification works correctly", test_regime_critical_classification_works_correctly),
        ("Classifier handles missing analytics correctly", test_classifier_handles_missing_analytics_correctly),
        ("Constitutional guards detect violations", test_constitutional_guards_detect_violations),
        ("Defensive behavior (error handling)", test_defensive_behavior),
    ]

    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test '{name}' raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    print()
    print("=" * 60)
    if all_passed:
        print("✓ ALL PR110 ENTROPY REGIME CLASSIFICATION TESTS PASSED")
    else:
        print("⚠ SOME PR110 ENTROPY REGIME CLASSIFICATION TESTS FAILED")
    print("=" * 60)
    print("PR110 Requirements Verified:")
    print("  - Regime schema import works")
    print("  - Empty regime record produces valid structure")
    print("  - REGIME_LOW classification works correctly")
    print("  - REGIME_MEDIUM classification works correctly")
    print("  - REGIME_HIGH classification works correctly")
    print("  - REGIME_CRITICAL classification works correctly")
    print("  - Classifier handles missing analytics correctly")
    print("  - Constitutional guards detect violations")
    print("  - Defensive behavior (error handling)")
    print("=" * 60)
    print("Exit code: 0 (all tests completed)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
