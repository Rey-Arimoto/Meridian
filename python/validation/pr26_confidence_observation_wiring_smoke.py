#!/usr/bin/env python3
"""
PR26: Confidence Observation Wiring Smoke Test

Purpose: Verify observation context builder provides fixed keyset.

Requirements:
- build_confidence_observation is importable and callable
- Returns dict with fixed allowed keyset
- Handles missing observations gracefully
- Works with evaluate_confidence without crashes
- Exit code always 0 (warning-only)

Non-Goals:
- No observation value validation
- No Confidence logic testing
- No behavior changes
"""

import sys
import os

# Add repo_root/python to sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PY_ROOT = os.path.join(REPO_ROOT, "python")
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from confidence.confidence_observation import build_confidence_observation
from confidence.confidence_evaluator import evaluate_confidence


# Allowed keyset from PR26 specification
REQUIRED_KEYS = {"intent_primary", "regime", "base_action", "overlay_rule", "entropy_bp"}
OPTIONAL_KEYS = {
    "recent_intent_primary",
    "recent_regime",
    "recent_base_action",
    "recent_overlay_rule",
    "data_health_flag",
}
ALLOWED_KEYS = REQUIRED_KEYS | OPTIONAL_KEYS


def test_builder_exists():
    """Test observation builder function exists and is callable."""
    print("\nTest 1: Observation Builder Exists")
    print("-" * 60)

    # Verify function exists
    assert callable(build_confidence_observation), "build_confidence_observation must be callable"
    print("✓ build_confidence_observation function exists")

    # Verify function returns dict
    obs = build_confidence_observation(
        intent_primary="IDLE",
        regime="stable_range",
        base_action="HOLD",
        overlay_rule="ALLOW",
        entropy_bp=5000,
    )
    assert isinstance(obs, dict), "build_confidence_observation must return dict"
    print("✓ Returns dict")

    print("Test 1: PASS (2/2)")
    return True


def test_required_keys_present():
    """Test required keys are present in observation."""
    print("\nTest 2: Required Keys Present")
    print("-" * 60)

    obs = build_confidence_observation(
        intent_primary="IDLE",
        regime="stable_range",
        base_action="HOLD",
        overlay_rule="ALLOW",
        entropy_bp=5000,
    )

    # Verify all required keys present
    for key in REQUIRED_KEYS:
        assert key in obs, f"Required key '{key}' missing from observation"
        print(f"✓ Required key present: {key}")

    print("Test 2: PASS (5/5)")
    return True


def test_keyset_restricted():
    """Test observation dict only contains allowed keys."""
    print("\nTest 3: Keyset Restricted (No Arbitrary Keys)")
    print("-" * 60)

    # Full observation with all optional keys
    obs = build_confidence_observation(
        intent_primary="IDLE",
        regime="stable_range",
        base_action="HOLD",
        overlay_rule="ALLOW",
        entropy_bp=5000,
        recent_intent_primary="IDLE,SEEK,IDLE",
        recent_regime="stable_range,emerging_trend,stable_range",
        recent_base_action="HOLD,SHIFT,HOLD",
        recent_overlay_rule="ALLOW,ALLOW,ALLOW",
        data_health_flag="PASS",
    )

    # Verify all keys in observation are allowed
    for key in obs.keys():
        assert key in ALLOWED_KEYS, f"Unexpected key '{key}' in observation (not in allowed set)"

    print(f"✓ All {len(obs)} keys in allowed set")
    print(f"  Keys: {sorted(obs.keys())}")

    print("Test 3: PASS (1/1)")
    return True


def test_missing_observations_graceful():
    """Test graceful handling of missing optional observations."""
    print("\nTest 4: Missing Observations Handled Gracefully")
    print("-" * 60)

    # Minimal observation (required keys only)
    obs = build_confidence_observation(
        intent_primary="IDLE",
        regime="stable_range",
        base_action="HOLD",
        overlay_rule="ALLOW",
        entropy_bp=5000,
    )

    # Should succeed without optional keys
    assert isinstance(obs, dict), "Should return dict even with minimal input"
    print("✓ Minimal observation succeeds")

    # Required keys must be present
    for key in REQUIRED_KEYS:
        assert key in obs, f"Required key '{key}' must be present"
    print("✓ Required keys present")

    # Optional keys may be absent
    optional_present = [key for key in OPTIONAL_KEYS if key in obs]
    print(f"✓ Optional keys gracefully handled ({len(optional_present)} present)")

    print("Test 4: PASS (3/3)")
    return True


def test_integration_with_evaluator():
    """Test observation builder integrates with Confidence evaluator."""
    print("\nTest 5: Integration with Confidence Evaluator")
    print("-" * 60)

    # Build observation
    obs = build_confidence_observation(
        intent_primary="IDLE",
        regime="stable_range",
        base_action="HOLD",
        overlay_rule="ALLOW",
        entropy_bp=5000,
    )

    # Should work with evaluator
    try:
        value, reason = evaluate_confidence(obs)
        assert isinstance(value, str), "Evaluator must return string value"
        assert isinstance(reason, str), "Evaluator must return string reason"
        print("✓ Observation passes to evaluator without crash")
        print(f"  Result: ({repr(value)}, {repr(reason)})")
    except Exception as e:
        assert False, f"Integration with evaluator failed: {e}"

    print("Test 5: PASS (1/1)")
    return True


def test_empty_observations():
    """Test handling of empty observation values."""
    print("\nTest 6: Empty Observation Values")
    print("-" * 60)

    # Empty observations should be handled gracefully
    obs = build_confidence_observation(
        intent_primary="",
        regime="",
        base_action="",
        overlay_rule="",
        entropy_bp=0,
    )

    assert isinstance(obs, dict), "Should return dict with empty values"
    print("✓ Empty values handled gracefully")

    # Required keys must still be present (even if empty)
    for key in REQUIRED_KEYS:
        assert key in obs, f"Required key '{key}' must be present even if empty"
    print("✓ Required keys present (even if empty)")

    print("Test 6: PASS (2/2)")
    return True


def main():
    """Run all PR26 Confidence Observation Wiring smoke tests."""
    print("=" * 60)
    print("PR26: Confidence Observation Wiring Smoke Test")
    print("=" * 60)
    print("IMPORTANT: READ-ONLY wiring. No behavior changes. Exit code always 0.")
    print("=" * 60)

    try:
        results = []
        results.append(("Builder Exists", test_builder_exists()))
        results.append(("Required Keys Present", test_required_keys_present()))
        results.append(("Keyset Restricted", test_keyset_restricted()))
        results.append(("Missing Observations Graceful", test_missing_observations_graceful()))
        results.append(("Integration with Evaluator", test_integration_with_evaluator()))
        results.append(("Empty Observation Values", test_empty_observations()))

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        for name, passed in results:
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {name}")

        all_passed = all(passed for _, passed in results)

        print("\n" + "=" * 60)
        if all_passed:
            print("✓ ALL PR26 CONFIDENCE OBSERVATION WIRING TESTS PASSED")
            print("=" * 60)
            print("PR26 Requirements Verified:")
            print("  - Observation builder exists and is callable")
            print("  - Required keys always present")
            print("  - Keyset restricted to allowed keys only")
            print("  - Missing observations handled gracefully")
            print("  - Integration with evaluator successful")
            print("  - Empty values handled gracefully")
            print("=" * 60)
            print("Exit code: 0 (all tests passed)")
            return 0
        else:
            print("✗ SOME PR26 CONFIDENCE OBSERVATION WIRING TESTS FAILED")
            print("=" * 60)
            print("Exit code: 0 (warning-only, never fails)")
            return 0  # Always exit 0 (warning-only)

    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"FAIL: {e}")
        print("=" * 60)
        print("Exit code: 0 (warning-only, never fails)")
        return 0  # Always exit 0

    except Exception as e:
        print()
        print("=" * 60)
        print(f"ERROR: Unexpected exception during validation")
        print(f"{e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        print("Exit code: 0 (warning-only, never fails)")
        return 0  # Always exit 0


if __name__ == "__main__":
    sys.exit(main())
