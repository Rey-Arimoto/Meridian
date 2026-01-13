#!/usr/bin/env python3
"""
PR145: v1.4 Safe Band × Distortion Stress Overlay v1 Smoke Tests

Purpose:
    Validate v1.4 safe band × distortion stress overlay engine.

Tests:
    1. Import works
    2. Minimal bundle → AVAILABLE
    3. Distortion NONE → CALM
    4. Distortion present + MEDIUM → TENSE
    5. Distortion present + HIGH → STRESSED
    6. Constrained bucket (BAND_ZERO) + distortion → STRESSED
    7. Malformed inputs → defensive (no raise) + ERROR + warnings
    8. Forbidden vocab injected → warnings
    9. Token literal injected → warnings
    10. Numeric/address injected → warnings
    11. Eligibility coupling injected → warnings
    12. CRITICAL regime → STRESSED (regardless of distortion)
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from guidance import (
            build_safe_band_distortion_overlay_v1,
            get_overlay_engine_v1_info,
            check_overlay_record,
            V14SafeBandDistortionOverlaySchema,
            OVERLAY_STATUS_AVAILABLE,
            OVERLAY_STATUS_ERROR,
            DISTORTION_PRESENCE_NONE,
            DISTORTION_PRESENCE_PRESENT,
            DISTORTION_PRESENCE_MULTIPLE,
            DISTORTION_PRESENCE_UNKNOWN,
            BAND_STRESS_CALM,
            BAND_STRESS_TENSE,
            BAND_STRESS_STRESSED,
            BAND_STRESS_UNKNOWN,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_minimal_bundle_to_available():
    """Test 2: Minimal bundle → AVAILABLE."""
    print("\nTest 2: Minimal bundle → AVAILABLE")
    try:
        from guidance import (
            build_safe_band_distortion_overlay_v1,
            OVERLAY_STATUS_AVAILABLE,
        )

        # Minimal artifact bundle
        bundle = {
            "artifacts": {
                "regime_record": {
                    "v11_regime_level": "REGIME_MEDIUM",
                },
                "role_safe_band_guidance": {
                    "v14_guidance_roles": {
                        "VOLATILITY_ROLE": {
                            "safe_band_bucket": "BAND_MEDIUM",
                        }
                    }
                },
            }
        }

        result = build_safe_band_distortion_overlay_v1(bundle)
        overlay = result["overlay_record"]

        assert overlay["v14_overlay_status"] == OVERLAY_STATUS_AVAILABLE, "Expected AVAILABLE status"

        print(f"  ✓ AVAILABLE record with status: {overlay['v14_overlay_status']}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_distortion_none_to_calm():
    """Test 3: Distortion NONE → CALM."""
    print("\nTest 3: Distortion NONE → CALM")
    try:
        from guidance import (
            build_safe_band_distortion_overlay_v1,
            DISTORTION_PRESENCE_NONE,
            BAND_STRESS_CALM,
        )

        bundle = {
            "artifacts": {
                "regime_record": {
                    "v11_regime_level": "REGIME_MEDIUM",
                },
                "role_safe_band_guidance": {
                    "v14_guidance_roles": {
                        "VOLATILITY_ROLE": {
                            "safe_band_bucket": "BAND_MEDIUM",
                        }
                    }
                },
                # No distortion artifacts
            }
        }

        result = build_safe_band_distortion_overlay_v1(bundle)
        overlay = result["overlay_record"]

        assert overlay["v14_overlay_distortion_presence"] == DISTORTION_PRESENCE_NONE, "Expected NONE distortion"
        assert overlay["v14_overlay_band_stress_label"] == BAND_STRESS_CALM, "Expected CALM stress"

        print(f"  ✓ CALM stress with NONE distortion")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_distortion_present_medium_to_tense():
    """Test 4: Distortion present + MEDIUM → TENSE."""
    print("\nTest 4: Distortion present + MEDIUM → TENSE")
    try:
        from guidance import (
            build_safe_band_distortion_overlay_v1,
            DISTORTION_PRESENCE_PRESENT,
            BAND_STRESS_TENSE,
        )

        bundle = {
            "artifacts": {
                "regime_record": {
                    "v11_regime_level": "REGIME_MEDIUM",
                },
                "role_safe_band_guidance": {
                    "v14_guidance_roles": {
                        "VOLATILITY_ROLE": {
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

        result = build_safe_band_distortion_overlay_v1(bundle)
        overlay = result["overlay_record"]

        assert overlay["v14_overlay_distortion_presence"] == DISTORTION_PRESENCE_PRESENT, "Expected PRESENT distortion"
        assert overlay["v14_overlay_band_stress_label"] == BAND_STRESS_TENSE, "Expected TENSE stress"

        print(f"  ✓ TENSE stress with PRESENT distortion in MEDIUM regime")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_distortion_present_high_to_stressed():
    """Test 5: Distortion present + HIGH → STRESSED."""
    print("\nTest 5: Distortion present + HIGH → STRESSED")
    try:
        from guidance import (
            build_safe_band_distortion_overlay_v1,
            DISTORTION_PRESENCE_PRESENT,
            BAND_STRESS_STRESSED,
        )

        bundle = {
            "artifacts": {
                "regime_record": {
                    "v11_regime_level": "REGIME_HIGH",
                },
                "role_safe_band_guidance": {
                    "v14_guidance_roles": {
                        "VOLATILITY_ROLE": {
                            "safe_band_bucket": "BAND_LOW",
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

        result = build_safe_band_distortion_overlay_v1(bundle)
        overlay = result["overlay_record"]

        assert overlay["v14_overlay_distortion_presence"] == DISTORTION_PRESENCE_PRESENT, "Expected PRESENT distortion"
        assert overlay["v14_overlay_band_stress_label"] == BAND_STRESS_STRESSED, "Expected STRESSED"

        print(f"  ✓ STRESSED with PRESENT distortion in HIGH regime")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_constrained_bucket_to_stressed():
    """Test 6: Constrained bucket (BAND_ZERO) + distortion → STRESSED."""
    print("\nTest 6: Constrained bucket (BAND_ZERO) + distortion → STRESSED")
    try:
        from guidance import (
            build_safe_band_distortion_overlay_v1,
            BAND_STRESS_STRESSED,
        )

        bundle = {
            "artifacts": {
                "regime_record": {
                    "v11_regime_level": "REGIME_LOW",
                },
                "role_safe_band_guidance": {
                    "v14_guidance_roles": {
                        "VOLATILITY_ROLE": {
                            "safe_band_bucket": "BAND_ZERO",
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

        result = build_safe_band_distortion_overlay_v1(bundle)
        overlay = result["overlay_record"]

        assert overlay["v14_overlay_band_stress_label"] == BAND_STRESS_STRESSED, "Expected STRESSED"

        print(f"  ✓ STRESSED with BAND_ZERO + distortion")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_malformed_inputs_defensive():
    """Test 7: Malformed inputs → defensive (no raise) + ERROR + warnings."""
    print("\nTest 7: Malformed inputs → defensive")
    try:
        from guidance import (
            build_safe_band_distortion_overlay_v1,
            OVERLAY_STATUS_ERROR,
        )

        # Try None input
        result1 = build_safe_band_distortion_overlay_v1(None)
        assert result1["overlay_record"]["v14_overlay_status"] == OVERLAY_STATUS_ERROR, "Expected ERROR for None"
        assert len(result1["warnings"]) > 0, "Expected warnings for None"

        # Try empty dict
        result2 = build_safe_band_distortion_overlay_v1({})
        assert result2["overlay_record"]["v14_overlay_status"] == OVERLAY_STATUS_ERROR, "Expected ERROR for empty"
        assert len(result2["warnings"]) > 0, "Expected warnings for empty"

        # Try missing required artifacts
        result3 = build_safe_band_distortion_overlay_v1({"artifacts": {}})
        assert result3["overlay_record"]["v14_overlay_status"] == OVERLAY_STATUS_ERROR, "Expected ERROR for missing"
        assert len(result3["warnings"]) > 0, "Expected warnings for missing"

        print(f"  ✓ Defensive handling with ERROR + warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_forbidden_vocab_warnings():
    """Test 8: Forbidden vocab injected → warnings."""
    print("\nTest 8: Forbidden vocab injected → warnings")
    try:
        from guidance import check_overlay_record

        # Create dirty overlay with forbidden vocabulary
        dirty_overlay = {
            "v14_overlay_summary": "You should buy more volatility assets.",
            "v14_overlay_notes": ["You must execute this trade immediately."],
        }

        warnings = check_overlay_record(dirty_overlay)

        # Check for forbidden vocabulary warnings
        vocab_warnings = [w for w in warnings if "forbidden vocabulary" in w.lower()]
        assert len(vocab_warnings) > 0, "Expected forbidden vocabulary warnings"

        print(f"  ✓ Forbidden vocabulary detected: {len(vocab_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_token_literal_warnings():
    """Test 9: Token literal injected → warnings."""
    print("\nTest 9: Token literal injected → warnings")
    try:
        from guidance import check_overlay_record

        # Create dirty overlay with token literals
        dirty_overlay = {
            "v14_overlay_summary": "SUI and USDC allocation detected.",
            "v14_overlay_notes": ["BTC distortion present."],
        }

        warnings = check_overlay_record(dirty_overlay)

        # Check for token literal warnings
        token_warnings = [w for w in warnings if "token literal" in w.lower()]
        assert len(token_warnings) > 0, "Expected token literal warnings"

        print(f"  ✓ Token literals detected: {len(token_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_numeric_address_warnings():
    """Test 10: Numeric/address injected → warnings."""
    print("\nTest 10: Numeric/address injected → warnings")
    try:
        from guidance import check_overlay_record

        # Create dirty overlay with numerics and addresses
        dirty_overlay = {
            "v14_overlay_summary": "Stress level is 0.75 or 75% of maximum.",
            "v14_overlay_notes": ["Address 0x1234 detected."],
        }

        warnings = check_overlay_record(dirty_overlay)

        # Check for numeric warnings
        numeric_warnings = [w for w in warnings if "numeric pattern" in w.lower()]
        assert len(numeric_warnings) > 0, "Expected numeric pattern warnings"

        # Check for address warnings
        address_warnings = [w for w in warnings if "address pattern" in w.lower()]
        assert len(address_warnings) > 0, "Expected address pattern warnings"

        print(f"  ✓ Numerics and addresses detected: {len(numeric_warnings) + len(address_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_11_eligibility_coupling_warnings():
    """Test 11: Eligibility coupling injected → warnings."""
    print("\nTest 11: Eligibility coupling injected → warnings")
    try:
        from guidance import check_overlay_record

        # Create dirty overlay with eligibility coupling
        dirty_overlay = {
            "v14_overlay_summary": "Stress state is CALM therefore you are eligible to proceed.",
            "v14_overlay_notes": ["Permission improved so you may execute."],
        }

        warnings = check_overlay_record(dirty_overlay)

        # Check for eligibility coupling warnings
        eligibility_warnings = [w for w in warnings if "eligibility coupling" in w.lower() or "coupling" in w.lower()]
        assert len(eligibility_warnings) > 0, "Expected eligibility coupling warnings"

        print(f"  ✓ Eligibility coupling detected: {len(eligibility_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_12_critical_regime_to_stressed():
    """Test 12: CRITICAL regime → STRESSED (regardless of distortion)."""
    print("\nTest 12: CRITICAL regime → STRESSED")
    try:
        from guidance import (
            build_safe_band_distortion_overlay_v1,
            BAND_STRESS_STRESSED,
        )

        # Test with distortion
        bundle_with_distortion = {
            "artifacts": {
                "regime_record": {
                    "v11_regime_level": "REGIME_CRITICAL",
                },
                "role_safe_band_guidance": {
                    "v14_guidance_roles": {
                        "VOLATILITY_ROLE": {
                            "safe_band_bucket": "BAND_ZERO",
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

        result1 = build_safe_band_distortion_overlay_v1(bundle_with_distortion)
        overlay1 = result1["overlay_record"]
        assert overlay1["v14_overlay_band_stress_label"] == BAND_STRESS_STRESSED, "Expected STRESSED in CRITICAL"

        # Test without distortion (should still be STRESSED)
        bundle_no_distortion = {
            "artifacts": {
                "regime_record": {
                    "v11_regime_level": "REGIME_CRITICAL",
                },
                "role_safe_band_guidance": {
                    "v14_guidance_roles": {
                        "VOLATILITY_ROLE": {
                            "safe_band_bucket": "BAND_ZERO",
                        }
                    }
                },
            }
        }

        result2 = build_safe_band_distortion_overlay_v1(bundle_no_distortion)
        overlay2 = result2["overlay_record"]
        assert overlay2["v14_overlay_band_stress_label"] == BAND_STRESS_STRESSED, "Expected STRESSED in CRITICAL (no distortion)"

        print(f"  ✓ CRITICAL regime always maps to STRESSED")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR145: v1.4 Safe Band × Distortion Stress Overlay - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_minimal_bundle_to_available,
        test_3_distortion_none_to_calm,
        test_4_distortion_present_medium_to_tense,
        test_5_distortion_present_high_to_stressed,
        test_6_constrained_bucket_to_stressed,
        test_7_malformed_inputs_defensive,
        test_8_forbidden_vocab_warnings,
        test_9_token_literal_warnings,
        test_10_numeric_address_warnings,
        test_11_eligibility_coupling_warnings,
        test_12_critical_regime_to_stressed,
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
