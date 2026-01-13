#!/usr/bin/env python3
"""
PR146: v1.4 Stress Rule Table v1 Smoke Tests

Purpose:
    Validate v1.4 stress rule table engine.

Tests:
    1. Import works
    2. Minimal inputs mapping works (LOW + SAFE + NONE → CALM)
    3. Missing table key → UNKNOWN + warning
    4. Defensive invalid regime label → ERROR record valid
    5. Regime CRITICAL always STRESSED
    6. Band OUTSIDE always STRESSED
    7. Distortion PRESENT increases stress (MEDIUM + SAFE + NONE→TENSE vs PRESENT→STRESSED)
    8. Bundle path: minimal bundle (regime only) → UNKNOWN (not crash)
    9. Bundle path: full bundle with distortions → expected label
    10. Constitutional guard catches forbidden vocab
    11. Constitutional guard catches token literals
    12. Constitutional guard catches coupling phrases
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from stress import (
            build_stress_label_from_inputs_v1,
            build_stress_label_from_bundle_v1,
            get_stress_engine_v1_info,
            check_stress_record,
            V14StressRuleTableSchema,
            STRESS_STATUS_AVAILABLE,
            STRESS_STATUS_ERROR,
            STRESS_CALM,
            STRESS_TENSE,
            STRESS_STRESSED,
            STRESS_UNKNOWN,
            BAND_SAFE,
            BAND_EDGE,
            BAND_OUTSIDE,
            BAND_UNKNOWN,
            DIST_NONE,
            DIST_PRESENT,
            DIST_UNKNOWN,
            REGIME_LOW,
            REGIME_MEDIUM,
            REGIME_HIGH,
            REGIME_CRITICAL,
            REGIME_UNKNOWN,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_minimal_inputs_mapping():
    """Test 2: Minimal inputs mapping works (LOW + SAFE + NONE → CALM)."""
    print("\nTest 2: Minimal inputs mapping (LOW + SAFE + NONE → CALM)")
    try:
        from stress import (
            build_stress_label_from_inputs_v1,
            STRESS_CALM,
            REGIME_LOW,
            BAND_SAFE,
            DIST_NONE,
        )

        result = build_stress_label_from_inputs_v1(
            regime_label=REGIME_LOW,
            band_bucket=BAND_SAFE,
            distortion_presence=DIST_NONE,
        )

        stress = result["stress_record"]
        assert stress["v14_stress_label"] == STRESS_CALM, f"Expected CALM, got {stress['v14_stress_label']}"

        print(f"  ✓ Mapping works: LOW + SAFE + NONE → {stress['v14_stress_label']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_missing_key_to_unknown():
    """Test 3: Missing table key → UNKNOWN + warning."""
    print("\nTest 3: Missing table key → UNKNOWN + warning")
    try:
        from stress import (
            lookup_stress_label_v1,
            STRESS_UNKNOWN,
        )

        # Use invalid regime label (not in table)
        label, basis, warnings = lookup_stress_label_v1(
            regime_label="INVALID_REGIME",
            band_bucket="SAFE",
            distortion_presence="NONE",
        )

        assert label == STRESS_UNKNOWN, f"Expected UNKNOWN, got {label}"
        assert len(warnings) > 0, "Expected warnings for missing key"

        print(f"  ✓ Missing key → UNKNOWN with {len(warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_defensive_invalid_inputs():
    """Test 4: Defensive invalid regime label → ERROR record valid."""
    print("\nTest 4: Defensive invalid inputs → ERROR record valid")
    try:
        from stress import (
            build_stress_label_from_bundle_v1,
            STRESS_STATUS_ERROR,
        )

        # Try None input
        result = build_stress_label_from_bundle_v1(None)
        stress = result["stress_record"]

        assert stress["v14_stress_status"] == STRESS_STATUS_ERROR, "Expected ERROR status"
        assert len(result["warnings"]) > 0, "Expected warnings"

        print(f"  ✓ Defensive handling: ERROR status with {len(result['warnings'])} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_critical_always_stressed():
    """Test 5: Regime CRITICAL always STRESSED."""
    print("\nTest 5: Regime CRITICAL always STRESSED")
    try:
        from stress import (
            build_stress_label_from_inputs_v1,
            STRESS_STRESSED,
            REGIME_CRITICAL,
            BAND_SAFE,
            BAND_EDGE,
            DIST_NONE,
            DIST_PRESENT,
        )

        # Test all combinations with CRITICAL
        test_cases = [
            (BAND_SAFE, DIST_NONE),
            (BAND_SAFE, DIST_PRESENT),
            (BAND_EDGE, DIST_NONE),
            (BAND_EDGE, DIST_PRESENT),
        ]

        for band, dist in test_cases:
            result = build_stress_label_from_inputs_v1(
                regime_label=REGIME_CRITICAL,
                band_bucket=band,
                distortion_presence=dist,
            )
            stress = result["stress_record"]
            assert stress["v14_stress_label"] == STRESS_STRESSED, \
                f"Expected STRESSED for CRITICAL+{band}+{dist}, got {stress['v14_stress_label']}"

        print(f"  ✓ CRITICAL always maps to STRESSED (tested {len(test_cases)} cases)")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_outside_always_stressed():
    """Test 6: Band OUTSIDE always STRESSED."""
    print("\nTest 6: Band OUTSIDE always STRESSED")
    try:
        from stress import (
            build_stress_label_from_inputs_v1,
            STRESS_STRESSED,
            REGIME_LOW,
            REGIME_MEDIUM,
            REGIME_HIGH,
            BAND_OUTSIDE,
            DIST_NONE,
            DIST_PRESENT,
        )

        # Test all combinations with OUTSIDE
        test_cases = [
            (REGIME_LOW, DIST_NONE),
            (REGIME_LOW, DIST_PRESENT),
            (REGIME_MEDIUM, DIST_NONE),
            (REGIME_HIGH, DIST_PRESENT),
        ]

        for regime, dist in test_cases:
            result = build_stress_label_from_inputs_v1(
                regime_label=regime,
                band_bucket=BAND_OUTSIDE,
                distortion_presence=dist,
            )
            stress = result["stress_record"]
            assert stress["v14_stress_label"] == STRESS_STRESSED, \
                f"Expected STRESSED for {regime}+OUTSIDE+{dist}, got {stress['v14_stress_label']}"

        print(f"  ✓ OUTSIDE always maps to STRESSED (tested {len(test_cases)} cases)")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_distortion_increases_stress():
    """Test 7: Distortion PRESENT increases stress (MEDIUM + SAFE + NONE→TENSE vs PRESENT→STRESSED)."""
    print("\nTest 7: Distortion PRESENT increases stress")
    try:
        from stress import (
            build_stress_label_from_inputs_v1,
            STRESS_TENSE,
            STRESS_STRESSED,
            REGIME_MEDIUM,
            BAND_SAFE,
            DIST_NONE,
            DIST_PRESENT,
        )

        # Without distortion
        result1 = build_stress_label_from_inputs_v1(
            regime_label=REGIME_MEDIUM,
            band_bucket=BAND_SAFE,
            distortion_presence=DIST_NONE,
        )
        stress1 = result1["stress_record"]
        assert stress1["v14_stress_label"] == STRESS_TENSE, f"Expected TENSE, got {stress1['v14_stress_label']}"

        # With distortion
        result2 = build_stress_label_from_inputs_v1(
            regime_label=REGIME_MEDIUM,
            band_bucket=BAND_SAFE,
            distortion_presence=DIST_PRESENT,
        )
        stress2 = result2["stress_record"]
        assert stress2["v14_stress_label"] == STRESS_STRESSED, f"Expected STRESSED, got {stress2['v14_stress_label']}"

        print(f"  ✓ Distortion increases stress: NONE→TENSE, PRESENT→STRESSED")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_bundle_minimal():
    """Test 8: Bundle path: minimal bundle (regime only) → UNKNOWN (not crash)."""
    print("\nTest 8: Bundle path: minimal bundle → UNKNOWN")
    try:
        from stress import (
            build_stress_label_from_bundle_v1,
            STRESS_UNKNOWN,
        )

        # Minimal bundle (only regime, no safe_band_guidance)
        bundle = {
            "artifacts": {
                "regime_record": {
                    "v11_regime_level": "REGIME_MEDIUM",
                },
            }
        }

        result = build_stress_label_from_bundle_v1(bundle)
        stress = result["stress_record"]

        # Should be UNKNOWN due to missing safe_band_guidance
        assert stress["v14_stress_label"] == STRESS_UNKNOWN, f"Expected UNKNOWN, got {stress['v14_stress_label']}"
        assert len(result["warnings"]) > 0, "Expected warnings for missing components"

        print(f"  ✓ Minimal bundle → UNKNOWN with {len(result['warnings'])} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_bundle_full():
    """Test 9: Bundle path: full bundle with distortions → expected label."""
    print("\nTest 9: Bundle path: full bundle with distortions")
    try:
        from stress import (
            build_stress_label_from_bundle_v1,
            STRESS_TENSE,
        )

        # Full bundle
        bundle = {
            "artifacts": {
                "regime_record": {
                    "v11_regime_level": "REGIME_LOW",
                },
                "role_safe_band_guidance": {
                    "v14_guidance_roles": {
                        "VOLATILITY_ROLE": {
                            "status": "WITHIN_SAFE",  # → SAFE
                            "safe_band_bucket": "BAND_MEDIUM",
                        }
                    }
                },
                "distortion_catalog_record": {
                    "v12_distortion_records": [
                        {"distortion_subtype": "SUBTYPE_A"}
                    ]
                },
            }
        }

        result = build_stress_label_from_bundle_v1(bundle)
        stress = result["stress_record"]

        # LOW + SAFE + PRESENT → TENSE
        assert stress["v14_stress_label"] == STRESS_TENSE, f"Expected TENSE, got {stress['v14_stress_label']}"

        print(f"  ✓ Full bundle → {stress['v14_stress_label']} (expected)")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_forbidden_vocab():
    """Test 10: Constitutional guard catches forbidden vocab."""
    print("\nTest 10: Constitutional guard catches forbidden vocab")
    try:
        from stress import check_stress_record

        # Dirty stress with forbidden vocab
        dirty_stress = {
            "v14_stress_summary": "You should buy more volatility assets.",
        }

        warnings = check_stress_record(dirty_stress)
        vocab_warnings = [w for w in warnings if "forbidden vocabulary" in w.lower()]

        assert len(vocab_warnings) > 0, "Expected forbidden vocabulary warnings"

        print(f"  ✓ Forbidden vocabulary detected: {len(vocab_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_11_token_literals():
    """Test 11: Constitutional guard catches token literals."""
    print("\nTest 11: Constitutional guard catches token literals")
    try:
        from stress import check_stress_record

        # Dirty stress with token literals
        dirty_stress = {
            "v14_stress_summary": "SUI and USDC stress detected.",
        }

        warnings = check_stress_record(dirty_stress)
        token_warnings = [w for w in warnings if "token literal" in w.lower()]

        assert len(token_warnings) > 0, "Expected token literal warnings"

        print(f"  ✓ Token literals detected: {len(token_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_12_coupling_phrases():
    """Test 12: Constitutional guard catches coupling phrases."""
    print("\nTest 12: Constitutional guard catches coupling phrases")
    try:
        from stress import check_stress_record

        # Dirty stress with coupling
        dirty_stress = {
            "v14_stress_summary": "Stress is STRESSED therefore you must exit.",
        }

        warnings = check_stress_record(dirty_stress)
        coupling_warnings = [w for w in warnings if "coupling" in w.lower() or "forbidden vocabulary" in w.lower()]

        assert len(coupling_warnings) > 0, "Expected coupling warnings"

        print(f"  ✓ Coupling phrases detected: {len(coupling_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR146: v1.4 Stress Rule Table - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_minimal_inputs_mapping,
        test_3_missing_key_to_unknown,
        test_4_defensive_invalid_inputs,
        test_5_critical_always_stressed,
        test_6_outside_always_stressed,
        test_7_distortion_increases_stress,
        test_8_bundle_minimal,
        test_9_bundle_full,
        test_10_forbidden_vocab,
        test_11_token_literals,
        test_12_coupling_phrases,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            results.append(False)

    print("\n" + "=" * 70)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)

    if all(results):
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print("\n✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
