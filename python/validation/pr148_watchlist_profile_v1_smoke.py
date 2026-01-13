#!/usr/bin/env python3
"""
PR148: v1.4 Watchlist + Observation Profile v1 Smoke Tests

Purpose:
    Validate v1.4 watchlist + observation profile engine.

Tests:
    1. Import works
    2. Minimal watchlist builds AVAILABLE
    3. Default profiles exist and valid
    4. Expand plan includes windows from profile
    5. No window field allowed in watchlist items
    6. Unknown profile_ref → plan UNKNOWN + warning
    7. enabled=OFF excluded from plan
    8. Defensive malformed input → ERROR record valid
    9. Guard catches forbidden vocab
    10. Guard catches token literals
    11. Guard catches numeric/address patterns
    12. Guard warning-only (no exceptions)
    13. extract_pair_refs_v1 works
    14. Multiple profiles (CORE_3W, ALERT_ONLY, RESEARCH)
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_1_import_works():
    """Test 1: Import works."""
    print("Test 1: Import works")
    try:
        from watchlist import (
            build_watchlist_record_v1,
            expand_watchlist_to_observation_plan_v1,
            extract_pair_refs_v1,
            get_default_profiles,
            get_watchlist_engine_v1_info,
            V14WatchlistSchema,
            V14ObservationProfileSchema,
            check_watchlist_record,
            WATCHLIST_STATUS_AVAILABLE,
            WATCHLIST_STATUS_ERROR,
            PRIORITY_CORE,
            ENABLED_ON,
            ENABLED_OFF,
            WINDOW_SHORT,
            WINDOW_MEDIUM,
            WINDOW_LONG,
        )
        print("  ✓ All imports successful")
        return True
    except Exception as e:
        print(f"  ✗ Import failed: {e}")
        return False


def test_2_minimal_watchlist_available():
    """Test 2: Minimal watchlist builds AVAILABLE."""
    print("\nTest 2: Minimal watchlist builds AVAILABLE")
    try:
        from watchlist import (
            build_watchlist_record_v1,
            WATCHLIST_STATUS_AVAILABLE,
        )

        items = [
            {
                "pair_ref": "deep:SUI/USDC",
                "source": "deep",
                "profile_ref": "CORE_3W",
                "priority": "CORE",
                "enabled": "ON",
            },
        ]

        result = build_watchlist_record_v1(items)
        watchlist_record = result["watchlist_record"]

        assert watchlist_record["v14_watchlist_status"] == WATCHLIST_STATUS_AVAILABLE, "Expected AVAILABLE status"
        assert len(watchlist_record["v14_watchlist_items"]) == 1, "Expected 1 item"

        print(f"  ✓ AVAILABLE with {len(watchlist_record['v14_watchlist_items'])} item(s)")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_3_default_profiles_exist():
    """Test 3: Default profiles exist and valid."""
    print("\nTest 3: Default profiles exist and valid")
    try:
        from watchlist import get_default_profiles, V14ObservationProfileSchema

        profiles = get_default_profiles()

        # Check default profiles exist
        expected_profiles = ["CORE_3W", "CORE_2W", "ALERT_ONLY", "RESEARCH"]
        for profile_ref in expected_profiles:
            assert profile_ref in profiles, f"Expected profile {profile_ref} not found"

            # Validate profile
            profile = profiles[profile_ref]
            errors = V14ObservationProfileSchema.validate_profile(profile)
            assert len(errors) == 0, f"Profile {profile_ref} has validation errors: {errors}"

        print(f"  ✓ {len(profiles)} default profiles exist and valid")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_4_expand_plan_includes_windows():
    """Test 4: Expand plan includes windows from profile."""
    print("\nTest 4: Expand plan includes windows from profile")
    try:
        from watchlist import (
            build_watchlist_record_v1,
            expand_watchlist_to_observation_plan_v1,
            WINDOW_SHORT,
            WINDOW_MEDIUM,
            WINDOW_LONG,
        )

        # Build watchlist with CORE_3W profile
        items = [
            {
                "pair_ref": "deep:SUI/USDC",
                "source": "deep",
                "profile_ref": "CORE_3W",
                "priority": "CORE",
                "enabled": "ON",
            },
        ]

        result = build_watchlist_record_v1(items)
        watchlist_record = result["watchlist_record"]

        # Expand to observation plan
        plan_result = expand_watchlist_to_observation_plan_v1(watchlist_record)
        observation_plan = plan_result["observation_plan"]

        assert len(observation_plan["items"]) == 1, "Expected 1 plan item"

        plan_item = observation_plan["items"][0]
        windows = plan_item["windows_enabled"]

        # CORE_3W should have SHORT, MEDIUM, LONG
        assert WINDOW_SHORT in windows, "Expected SHORT window"
        assert WINDOW_MEDIUM in windows, "Expected MEDIUM window"
        assert WINDOW_LONG in windows, "Expected LONG window"

        print(f"  ✓ Plan includes windows from profile: {windows}")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_5_no_window_field_in_watchlist():
    """Test 5: No window field allowed in watchlist items."""
    print("\nTest 5: No window field allowed in watchlist items")
    try:
        from watchlist import build_watchlist_record_v1

        # Try to include window field (prohibited)
        items = [
            {
                "pair_ref": "deep:SUI/USDC",
                "source": "deep",
                "profile_ref": "CORE_3W",
                "priority": "CORE",
                "enabled": "ON",
                "window": "SHORT",  # PROHIBITED
            },
        ]

        result = build_watchlist_record_v1(items)
        warnings = result["warnings"]

        # Should have warning about prohibited window field
        window_warnings = [w for w in warnings if "window" in w.lower()]
        assert len(window_warnings) > 0, "Expected warning about prohibited window field"

        print(f"  ✓ Window field detected and warned: {len(window_warnings)} warning(s)")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_6_unknown_profile_ref():
    """Test 6: Unknown profile_ref → plan UNKNOWN + warning."""
    print("\nTest 6: Unknown profile_ref → plan UNKNOWN + warning")
    try:
        from watchlist import (
            build_watchlist_record_v1,
            expand_watchlist_to_observation_plan_v1,
        )

        # Use unknown profile_ref
        items = [
            {
                "pair_ref": "deep:SUI/USDC",
                "source": "deep",
                "profile_ref": "UNKNOWN_PROFILE",
                "priority": "CORE",
                "enabled": "ON",
            },
        ]

        result = build_watchlist_record_v1(items)
        watchlist_record = result["watchlist_record"]
        warnings = result["warnings"]

        # Should have warning about unknown profile_ref
        profile_warnings = [w for w in warnings if "unknown profile_ref" in w.lower()]
        assert len(profile_warnings) > 0, "Expected warning about unknown profile_ref"

        # Expand to plan
        plan_result = expand_watchlist_to_observation_plan_v1(watchlist_record)
        observation_plan = plan_result["observation_plan"]

        assert len(observation_plan["items"]) == 1, "Expected 1 plan item"

        plan_item = observation_plan["items"][0]
        assert plan_item["status"] == "UNKNOWN", "Expected UNKNOWN status for item with unknown profile"

        print(f"  ✓ Unknown profile_ref → UNKNOWN + {len(profile_warnings)} warning(s)")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_7_enabled_off_excluded():
    """Test 7: enabled=OFF excluded from plan."""
    print("\nTest 7: enabled=OFF excluded from plan")
    try:
        from watchlist import (
            build_watchlist_record_v1,
            expand_watchlist_to_observation_plan_v1,
        )

        # Create watchlist with enabled=OFF
        items = [
            {
                "pair_ref": "deep:SUI/USDC",
                "source": "deep",
                "profile_ref": "CORE_3W",
                "priority": "CORE",
                "enabled": "OFF",
            },
        ]

        result = build_watchlist_record_v1(items)
        watchlist_record = result["watchlist_record"]

        # Watchlist should have 1 item
        assert len(watchlist_record["v14_watchlist_items"]) == 1, "Expected 1 watchlist item"

        # Expand to plan
        plan_result = expand_watchlist_to_observation_plan_v1(watchlist_record)
        observation_plan = plan_result["observation_plan"]

        # Plan should have 0 items (enabled=OFF excluded)
        assert len(observation_plan["items"]) == 0, "Expected 0 plan items (enabled=OFF excluded)"

        print(f"  ✓ enabled=OFF excluded from plan")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_8_malformed_inputs_defensive():
    """Test 8: Defensive malformed input → ERROR record valid."""
    print("\nTest 8: Defensive malformed input → ERROR record valid")
    try:
        from watchlist import (
            build_watchlist_record_v1,
            WATCHLIST_STATUS_ERROR,
        )

        # Try None input
        result = build_watchlist_record_v1(None)
        watchlist_record = result["watchlist_record"]

        assert watchlist_record["v14_watchlist_status"] == WATCHLIST_STATUS_ERROR, "Expected ERROR status"
        assert len(result["warnings"]) > 0, "Expected warnings"

        print(f"  ✓ Defensive handling: ERROR with {len(result['warnings'])} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_9_guard_forbidden_vocab():
    """Test 9: Guard catches forbidden vocab."""
    print("\nTest 9: Guard catches forbidden vocab")
    try:
        from watchlist import check_watchlist_record

        # Dirty watchlist with forbidden vocabulary
        dirty_watchlist = {
            "v14_watchlist_summary": "You should execute trades on these pairs.",
        }

        warnings = check_watchlist_record(dirty_watchlist)
        vocab_warnings = [w for w in warnings if "forbidden vocabulary" in w.lower()]

        assert len(vocab_warnings) > 0, "Expected forbidden vocabulary warnings"

        print(f"  ✓ Forbidden vocabulary detected: {len(vocab_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_10_guard_token_literals():
    """Test 10: Guard catches token literals."""
    print("\nTest 10: Guard catches token literals")
    try:
        from watchlist import check_watchlist_record

        # Dirty watchlist with token literals
        dirty_watchlist = {
            "v14_watchlist_summary": "Monitor SUI and USDC pairs.",
        }

        warnings = check_watchlist_record(dirty_watchlist)
        token_warnings = [w for w in warnings if "token literal" in w.lower()]

        assert len(token_warnings) > 0, "Expected token literal warnings"

        print(f"  ✓ Token literals detected: {len(token_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_11_guard_numeric_address_patterns():
    """Test 11: Guard catches numeric/address patterns."""
    print("\nTest 11: Guard catches numeric/address patterns")
    try:
        from watchlist import check_watchlist_record

        # Dirty watchlist with numerics and addresses
        dirty_watchlist = {
            "v14_watchlist_summary": "Monitor with 0.75 priority at address 0x1234.",
        }

        warnings = check_watchlist_record(dirty_watchlist)
        numeric_warnings = [w for w in warnings if "numeric pattern" in w.lower()]
        address_warnings = [w for w in warnings if "address pattern" in w.lower()]

        assert len(numeric_warnings) > 0, "Expected numeric pattern warnings"
        assert len(address_warnings) > 0, "Expected address pattern warnings"

        print(f"  ✓ Numerics and addresses detected: {len(numeric_warnings) + len(address_warnings)} warnings")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_12_guard_warning_only():
    """Test 12: Guard warning-only (no exceptions)."""
    print("\nTest 12: Guard warning-only (no exceptions)")
    try:
        from watchlist import check_watchlist_record

        # Very dirty watchlist with multiple violations
        very_dirty_watchlist = {
            "v14_watchlist_summary": "You must buy SUI at 0x1234 with 0.5 ratio.",
        }

        # Guard should return warnings, not raise
        warnings = check_watchlist_record(very_dirty_watchlist)

        assert isinstance(warnings, list), "Expected list of warnings"
        assert len(warnings) > 0, "Expected warnings for violations"

        print(f"  ✓ Guard returned {len(warnings)} warnings without raising")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_13_extract_pair_refs():
    """Test 13: extract_pair_refs_v1 works."""
    print("\nTest 13: extract_pair_refs_v1 works")
    try:
        from watchlist import (
            build_watchlist_record_v1,
            extract_pair_refs_v1,
        )

        # Build watchlist with multiple items
        items = [
            {
                "pair_ref": "deep:SUI/USDC",
                "source": "deep",
                "profile_ref": "CORE_3W",
                "priority": "CORE",
                "enabled": "ON",
            },
            {
                "pair_ref": "cetus:SUI/USDC",
                "source": "cetus",
                "profile_ref": "CORE_3W",
                "priority": "CORE",
                "enabled": "ON",
            },
            {
                "pair_ref": "deep:DEEP/USDC",
                "source": "deep",
                "profile_ref": "ALERT_ONLY",
                "priority": "EXTENDED",
                "enabled": "OFF",
            },
        ]

        result = build_watchlist_record_v1(items)
        watchlist_record = result["watchlist_record"]

        # Extract pair_refs (enabled_only=True)
        pair_refs_enabled = extract_pair_refs_v1(watchlist_record, enabled_only=True)
        assert len(pair_refs_enabled) == 2, "Expected 2 enabled pair_refs"
        assert "deep:SUI/USDC" in pair_refs_enabled, "Expected deep:SUI/USDC"
        assert "cetus:SUI/USDC" in pair_refs_enabled, "Expected cetus:SUI/USDC"

        # Extract pair_refs (enabled_only=False)
        pair_refs_all = extract_pair_refs_v1(watchlist_record, enabled_only=False)
        assert len(pair_refs_all) == 3, "Expected 3 total pair_refs"

        print(f"  ✓ Extracted {len(pair_refs_enabled)} enabled, {len(pair_refs_all)} total pair_refs")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_14_multiple_profiles():
    """Test 14: Multiple profiles (CORE_3W, ALERT_ONLY, RESEARCH)."""
    print("\nTest 14: Multiple profiles (CORE_3W, ALERT_ONLY, RESEARCH)")
    try:
        from watchlist import (
            build_watchlist_record_v1,
            expand_watchlist_to_observation_plan_v1,
            WINDOW_SHORT,
            WINDOW_MEDIUM,
            WINDOW_LONG,
        )

        # Build watchlist with multiple profiles
        items = [
            {
                "pair_ref": "deep:SUI/USDC",
                "source": "deep",
                "profile_ref": "CORE_3W",
                "priority": "CORE",
                "enabled": "ON",
            },
            {
                "pair_ref": "deep:DEEP/USDC",
                "source": "deep",
                "profile_ref": "ALERT_ONLY",
                "priority": "EXTENDED",
                "enabled": "ON",
            },
            {
                "pair_ref": "cetus:SUI/USDC",
                "source": "cetus",
                "profile_ref": "RESEARCH",
                "priority": "EXPERIMENTAL",
                "enabled": "ON",
            },
        ]

        result = build_watchlist_record_v1(items)
        watchlist_record = result["watchlist_record"]

        # Expand to plan
        plan_result = expand_watchlist_to_observation_plan_v1(watchlist_record)
        observation_plan = plan_result["observation_plan"]

        assert len(observation_plan["items"]) == 3, "Expected 3 plan items"

        # Check CORE_3W
        core_3w_item = [item for item in observation_plan["items"] if item["profile_ref"] == "CORE_3W"][0]
        assert len(core_3w_item["windows_enabled"]) == 3, "Expected 3 windows for CORE_3W"
        assert WINDOW_SHORT in core_3w_item["windows_enabled"], "Expected SHORT in CORE_3W"
        assert WINDOW_MEDIUM in core_3w_item["windows_enabled"], "Expected MEDIUM in CORE_3W"
        assert WINDOW_LONG in core_3w_item["windows_enabled"], "Expected LONG in CORE_3W"

        # Check ALERT_ONLY
        alert_item = [item for item in observation_plan["items"] if item["profile_ref"] == "ALERT_ONLY"][0]
        assert len(alert_item["windows_enabled"]) == 1, "Expected 1 window for ALERT_ONLY"
        assert WINDOW_SHORT in alert_item["windows_enabled"], "Expected SHORT in ALERT_ONLY"

        # Check RESEARCH
        research_item = [item for item in observation_plan["items"] if item["profile_ref"] == "RESEARCH"][0]
        assert len(research_item["windows_enabled"]) == 2, "Expected 2 windows for RESEARCH"
        assert WINDOW_MEDIUM in research_item["windows_enabled"], "Expected MEDIUM in RESEARCH"
        assert WINDOW_LONG in research_item["windows_enabled"], "Expected LONG in RESEARCH"

        print(f"  ✓ Multiple profiles expanded correctly")
        return True
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 70)
    print("PR148: v1.4 Watchlist + Observation Profile - Smoke Tests")
    print("=" * 70)

    tests = [
        test_1_import_works,
        test_2_minimal_watchlist_available,
        test_3_default_profiles_exist,
        test_4_expand_plan_includes_windows,
        test_5_no_window_field_in_watchlist,
        test_6_unknown_profile_ref,
        test_7_enabled_off_excluded,
        test_8_malformed_inputs_defensive,
        test_9_guard_forbidden_vocab,
        test_10_guard_token_literals,
        test_11_guard_numeric_address_patterns,
        test_12_guard_warning_only,
        test_13_extract_pair_refs,
        test_14_multiple_profiles,
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
