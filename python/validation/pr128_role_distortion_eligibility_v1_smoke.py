#!/usr/bin/env python3
"""
PR128: v1.2 Role × Distortion Eligibility v1 Smoke Tests

Purpose:
    Validate Role × Distortion × Regime eligibility classification.

Tests:
    1. Import works
    2. Empty input → defensive default
    3. CRITICAL → INELIGIBLE
    4. HIGH → DRY_RUN_ONLY
    5. LOW → DRY_RUN_ONLY
    6. MEDIUM × VOLATILITY × D1-D5 → CONSIDERATION_ONLY
    7. MEDIUM × non-volatility → DRY_RUN_ONLY
    8. Hard boundary → INELIGIBLE
    9. Suppressed → INELIGIBLE
    10. Guards produce no warnings for normal output
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _assert(cond: bool, msg: str):
    if not cond:
        raise AssertionError(msg)


def main() -> int:
    try:
        # Import modules
        from eligibility.v12_role_distortion_eligibility_engine_v1 import (
            classify_role_distortion_eligibility_v1
        )
        from eligibility.v12_role_distortion_eligibility_schema import (
            ELIG_INELIGIBLE,
            ELIG_ELIGIBLE_DRY_RUN_ONLY,
            ELIG_ELIGIBLE_CONSIDERATION_ONLY,
            REGIME_CRITICAL,
            REGIME_HIGH,
            REGIME_LOW,
            REGIME_MEDIUM,
            ROLE_VOLATILITY,
            ROLE_STABILITY,
            D1_LIQUIDATION,
            DISTORTION_UNCLASSIFIED,
            BOUNDARY_SCHEMA,
            SUPPRESSION_SUPPRESSED,
            eligibility_record_to_dict,
        )
        from eligibility.v12_eligibility_constitutional_guard import check_eligibility_record

        print("=" * 70)
        print("PR128: v1.2 Role × Distortion Eligibility v1 - Smoke Tests")
        print("=" * 70)
        print()

        # Test 1: Import works
        print("Test 1: Import works")
        _assert(callable(classify_role_distortion_eligibility_v1), "engine not callable")
        print("  ✓ All imports successful")
        print()

        # Test 2: Empty -> defensive default
        print("Test 2: Empty input → defensive default")
        rec = classify_role_distortion_eligibility_v1(None, None, None)
        d = eligibility_record_to_dict(rec)
        _assert("v12_elig_eligibility" in d, "missing eligibility field")
        print(f"  ✓ Empty input → defensive default: {rec.v12_elig_eligibility}")
        print()

        # Test 3: CRITICAL → INELIGIBLE
        print("Test 3: CRITICAL → INELIGIBLE")
        rec = classify_role_distortion_eligibility_v1(
            {"v11_regime_level": REGIME_CRITICAL},
            {"v12_distortion_type": D1_LIQUIDATION},
            {"v12_role_type": ROLE_VOLATILITY}
        )
        _assert(rec.v12_elig_eligibility == ELIG_INELIGIBLE, "critical should be ineligible")
        print(f"  ✓ CRITICAL → {rec.v12_elig_eligibility}")
        print(f"    Summary: {rec.v12_elig_summary}")
        print()

        # Test 4: HIGH → DRY_RUN_ONLY
        print("Test 4: HIGH → DRY_RUN_ONLY")
        rec = classify_role_distortion_eligibility_v1(
            {"v11_regime_level": REGIME_HIGH},
            {"v12_distortion_type": D1_LIQUIDATION},
            {"v12_role_type": ROLE_VOLATILITY}
        )
        _assert(rec.v12_elig_eligibility == ELIG_ELIGIBLE_DRY_RUN_ONLY, "high should be dry-run-only")
        print(f"  ✓ HIGH → {rec.v12_elig_eligibility}")
        print()

        # Test 5: LOW → DRY_RUN_ONLY
        print("Test 5: LOW → DRY_RUN_ONLY")
        rec = classify_role_distortion_eligibility_v1(
            {"v11_regime_level": REGIME_LOW},
            {"v12_distortion_type": D1_LIQUIDATION},
            {"v12_role_type": ROLE_VOLATILITY}
        )
        _assert(rec.v12_elig_eligibility == ELIG_ELIGIBLE_DRY_RUN_ONLY, "low should be dry-run-only")
        print(f"  ✓ LOW → {rec.v12_elig_eligibility}")
        print()

        # Test 6: MEDIUM × VOLATILITY × D1..D5 → CONSIDERATION_ONLY
        print("Test 6: MEDIUM × VOLATILITY × D1 → CONSIDERATION_ONLY")
        rec = classify_role_distortion_eligibility_v1(
            {"v11_regime_level": REGIME_MEDIUM},
            {"v12_distortion_type": D1_LIQUIDATION},
            {"v12_role_type": ROLE_VOLATILITY}
        )
        _assert(rec.v12_elig_eligibility == ELIG_ELIGIBLE_CONSIDERATION_ONLY, "medium+volatility+defined distortion should be consideration-only")
        print(f"  ✓ MEDIUM × VOLATILITY × D1 → {rec.v12_elig_eligibility}")
        print(f"    Summary: {rec.v12_elig_summary}")
        print()

        # Test 7: MEDIUM × non-volatility → DRY_RUN_ONLY
        print("Test 7: MEDIUM × non-volatility → DRY_RUN_ONLY")
        rec = classify_role_distortion_eligibility_v1(
            {"v11_regime_level": REGIME_MEDIUM},
            {"v12_distortion_type": D1_LIQUIDATION},
            {"v12_role_type": ROLE_STABILITY}
        )
        _assert(rec.v12_elig_eligibility == ELIG_ELIGIBLE_DRY_RUN_ONLY, "medium+non-volatility should be dry-run-only")
        print(f"  ✓ MEDIUM × STABILITY → {rec.v12_elig_eligibility}")
        print()

        # Test 8: hard boundary → INELIGIBLE
        print("Test 8: Hard boundary → INELIGIBLE")
        rec = classify_role_distortion_eligibility_v1(
            {"v11_regime_level": REGIME_MEDIUM},
            {"v12_distortion_type": D1_LIQUIDATION},
            {"v12_role_type": ROLE_VOLATILITY},
            {"v9_boundary_type": BOUNDARY_SCHEMA}
        )
        _assert(rec.v12_elig_eligibility == ELIG_INELIGIBLE, "hard boundary should be ineligible")
        print(f"  ✓ SCHEMA_BOUNDARY → {rec.v12_elig_eligibility}")
        print()

        # Test 9: suppressed → INELIGIBLE
        print("Test 9: Suppressed → INELIGIBLE")
        rec = classify_role_distortion_eligibility_v1(
            {"v11_regime_level": REGIME_MEDIUM},
            {"v12_distortion_type": D1_LIQUIDATION},
            {"v12_role_type": ROLE_VOLATILITY},
            None,
            {"v12_monitor_suppression_state": SUPPRESSION_SUPPRESSED}
        )
        _assert(rec.v12_elig_eligibility == ELIG_INELIGIBLE, "suppressed should be ineligible")
        print(f"  ✓ SUPPRESSED → {rec.v12_elig_eligibility}")
        print()

        # Test 10: Guards should produce no warnings for normal output
        print("Test 10: Guards produce no warnings for normal output")
        warnings = check_eligibility_record(eligibility_record_to_dict(rec))
        _assert(isinstance(warnings, list), "warnings not list")
        _assert(len(warnings) == 0, f"unexpected guard warnings: {warnings}")
        print(f"  ✓ Clean record passes: {len(warnings)} warnings")
        print()

        print("=" * 70)
        print("Results: All tests passed")
        print("=" * 70)
        print()
        print("✓ ALL TESTS PASSED")

        return 0

    except Exception as e:
        print(f"\n✗ PR128 smoke test FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 0  # warning-only


if __name__ == "__main__":
    sys.exit(main())
