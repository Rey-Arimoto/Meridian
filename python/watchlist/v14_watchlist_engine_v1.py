#!/usr/bin/env python3
"""
PR148: v1.4 Watchlist Engine v1 (READ-ONLY)

Purpose:
    Build watchlist from items and expand to observation plan.
    Watchlist = "What to observe" (pair_ref × source × profile_ref).
    Profile = "How to observe" (windows / cadence / featureset).

API:
    build_watchlist_record_v1(items, profiles=None) -> dict
    expand_watchlist_to_observation_plan_v1(watchlist_record, profiles_record=None) -> dict
    extract_pair_refs_v1(watchlist_record, enabled_only=True) -> list

Rules:
    - Watchlist items do NOT contain windows
    - Windows come from observation profiles
    - Unknown profile_ref → UNKNOWN + warning (watchlist stays AVAILABLE)
    - enabled=OFF excluded from plan (if enabled_only=True)
    - Defensive: Invalid input → valid ERROR record
    - Warning-only: Never raises exceptions

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Non-prescriptive: No should/must/recommend/advise
    - Label-only: No numeric values in text
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from watchlist.v14_watchlist_schema import (
    V14WatchlistSchema,
    WATCHLIST_VERSION_V1,
    WATCHLIST_STATUS_AVAILABLE,
    WATCHLIST_STATUS_ERROR,
    WATCHLIST_MODE_READ_ONLY,
    ENABLED_ON,
    ENABLED_OFF,
)
from watchlist.v14_observation_profile_schema import (
    get_default_profiles,
    get_profile_by_ref,
)


def build_watchlist_record_v1(
    items: Optional[List[Dict[str, Any]]],
    profiles: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Build watchlist record from items.

    Args:
        items: List of watchlist items (minimum: pair_ref, source, profile_ref, priority, enabled)
        profiles: Optional profiles dict (if None, use built-in defaults)

    Returns:
        Dict with:
        - watchlist_record: PR148-compliant watchlist record
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid items
    if items is None or not isinstance(items, list):
        warnings.append("invalid items (expected list, got None or non-list)")
        error_record = V14WatchlistSchema.create_error_record(
            summary="watchlist generation failed: invalid items input."
        )
        return {
            "watchlist_record": error_record,
            "warnings": warnings,
        }

    # Use default profiles if not provided
    if profiles is None:
        profiles = get_default_profiles()

    # Validate items
    validated_items = []
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            warnings.append(f"item {i} is not dict, skipping")
            continue

        # Check required fields
        required_fields = ["pair_ref", "source", "profile_ref", "priority", "enabled"]
        missing_fields = [f for f in required_fields if f not in item]
        if missing_fields:
            warnings.append(f"item {i} missing required fields: {missing_fields}, skipping")
            continue

        # Check for prohibited window field
        if "window" in item or "windows" in item:
            warnings.append(f"item {i} contains prohibited window field (windows belong in profiles), removing")
            # Remove window field
            item = {k: v for k, v in item.items() if k not in ["window", "windows"]}

        # Check if profile_ref exists
        profile_ref = item.get("profile_ref")
        if profile_ref and not get_profile_by_ref(profile_ref, profiles):
            warnings.append(f"item {i} references unknown profile_ref: {profile_ref}")

        validated_items.append(item)

    # Create summary
    enabled_count = sum(1 for item in validated_items if item.get("enabled") == ENABLED_ON)
    if enabled_count == 0:
        summary = "watchlist contains no enabled observation targets."
    elif enabled_count == 1:
        summary = "watchlist contains 1 enabled observation target."
    else:
        summary = f"watchlist contains {enabled_count} enabled observation targets."

    # Create watchlist record
    watchlist_record = V14WatchlistSchema.create_watchlist_record(
        version=WATCHLIST_VERSION_V1,
        status=WATCHLIST_STATUS_AVAILABLE,
        mode=WATCHLIST_MODE_READ_ONLY,
        items=validated_items,
        summary=summary,
    )

    # Validate schema
    schema_errors = V14WatchlistSchema.validate_watchlist_record(watchlist_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    return {
        "watchlist_record": watchlist_record,
        "warnings": warnings,
    }


def expand_watchlist_to_observation_plan_v1(
    watchlist_record: Dict[str, Any],
    profiles_record: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Expand watchlist to observation plan by adding windows from profiles.

    Important: Watchlist has no windows, so this function expands items with
    windows from their referenced profiles.

    Args:
        watchlist_record: Watchlist record
        profiles_record: Optional profiles dict (if None, use built-in defaults)

    Returns:
        Dict with:
        - observation_plan: Expanded observation plan
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid watchlist_record
    if watchlist_record is None or not isinstance(watchlist_record, dict):
        warnings.append("invalid watchlist_record (expected dict, got None or non-dict)")
        return {
            "observation_plan": {
                "status": "ERROR",
                "items": [],
                "summary": "observation plan expansion failed: invalid watchlist record.",
            },
            "warnings": warnings,
        }

    # Use default profiles if not provided
    if profiles_record is None:
        profiles_record = get_default_profiles()

    # Check watchlist status
    watchlist_status = watchlist_record.get("v14_watchlist_status")
    if watchlist_status == WATCHLIST_STATUS_ERROR:
        warnings.append("watchlist_record status is ERROR, cannot expand")
        return {
            "observation_plan": {
                "status": "ERROR",
                "items": [],
                "summary": "observation plan expansion failed: watchlist status is ERROR.",
            },
            "warnings": warnings,
        }

    # Get watchlist items
    watchlist_items = watchlist_record.get("v14_watchlist_items", [])

    # Expand items
    plan_items = []
    for i, item in enumerate(watchlist_items):
        if not isinstance(item, dict):
            warnings.append(f"watchlist item {i} is not dict, skipping")
            continue

        # Skip disabled items (enabled=OFF)
        enabled = item.get("enabled")
        if enabled == ENABLED_OFF:
            continue

        # Get profile
        profile_ref = item.get("profile_ref")
        profile = get_profile_by_ref(profile_ref, profiles_record)

        if profile is None:
            warnings.append(f"item {i} references unknown profile_ref: {profile_ref}, creating UNKNOWN plan item")
            # Create UNKNOWN plan item
            plan_item = {
                "pair_ref": item.get("pair_ref"),
                "source": item.get("source"),
                "profile_ref": profile_ref,
                "windows_enabled": [],
                "cadence_label": "UNKNOWN",
                "featureset_ref": "UNKNOWN",
                "priority": item.get("priority"),
                "enabled": item.get("enabled"),
                "status": "UNKNOWN",
            }
            plan_items.append(plan_item)
            continue

        # Create plan item with windows from profile
        plan_item = {
            "pair_ref": item.get("pair_ref"),
            "source": item.get("source"),
            "profile_ref": profile_ref,
            "windows_enabled": profile.get("windows_enabled", []),
            "cadence_label": profile.get("cadence_label"),
            "featureset_ref": profile.get("featureset_ref"),
            "priority": item.get("priority"),
            "enabled": item.get("enabled"),
            "status": "AVAILABLE",
        }

        # Copy optional fields
        if "notes" in item:
            plan_item["notes"] = item["notes"]

        plan_items.append(plan_item)

    # Create observation plan
    if len(plan_items) == 0:
        summary = "observation plan contains no items."
    elif len(plan_items) == 1:
        summary = "observation plan contains 1 observation target."
    else:
        summary = f"observation plan contains {len(plan_items)} observation targets."

    observation_plan = {
        "status": "AVAILABLE",
        "items": plan_items,
        "summary": summary,
    }

    return {
        "observation_plan": observation_plan,
        "warnings": warnings,
    }


def extract_pair_refs_v1(
    watchlist_record: Dict[str, Any],
    enabled_only: bool = True,
) -> List[str]:
    """
    Extract pair_refs from watchlist record.

    Intended for TS-side data fetch bridge.

    Args:
        watchlist_record: Watchlist record
        enabled_only: If True, only return enabled items (default True)

    Returns:
        List of pair_refs
    """
    # Defensive: Handle invalid watchlist_record
    if watchlist_record is None or not isinstance(watchlist_record, dict):
        return []

    # Get watchlist items
    watchlist_items = watchlist_record.get("v14_watchlist_items", [])

    # Extract pair_refs
    pair_refs = []
    for item in watchlist_items:
        if not isinstance(item, dict):
            continue

        # Check enabled filter
        if enabled_only and item.get("enabled") == ENABLED_OFF:
            continue

        pair_ref = item.get("pair_ref")
        if pair_ref:
            pair_refs.append(pair_ref)

    return pair_refs


def get_watchlist_engine_v1_info() -> Dict[str, Any]:
    """
    Get watchlist engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "watchlist",
        "philosophy": "Watchlist = 'What to observe'. Profile = 'How to observe'. Windows are in profiles, NOT watchlist.",
        "functions": [
            "build_watchlist_record_v1(items, profiles=None)",
            "expand_watchlist_to_observation_plan_v1(watchlist_record, profiles_record=None)",
            "extract_pair_refs_v1(watchlist_record, enabled_only=True)",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "label_output_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Watchlist Engine - Self Test")
    print("=" * 60)
    print()

    # Test 1: Build minimal watchlist
    print("Test 1: Build minimal watchlist")
    items1 = [
        {
            "pair_ref": "deep:SUI/USDC",
            "source": "deep",
            "profile_ref": "CORE_3W",
            "priority": "CORE",
            "enabled": "ON",
        },
    ]
    result1 = build_watchlist_record_v1(items1)
    print(f"Status: {result1['watchlist_record']['v14_watchlist_status']}")
    print(f"Items: {len(result1['watchlist_record']['v14_watchlist_items'])}")
    print(f"Warnings: {len(result1['warnings'])}")
    print()

    # Test 2: Expand watchlist to observation plan
    print("Test 2: Expand watchlist to observation plan")
    result2 = expand_watchlist_to_observation_plan_v1(result1['watchlist_record'])
    print(f"Plan status: {result2['observation_plan']['status']}")
    print(f"Plan items: {len(result2['observation_plan']['items'])}")
    if len(result2['observation_plan']['items']) > 0:
        item = result2['observation_plan']['items'][0]
        print(f"Windows: {item['windows_enabled']}")
    print()

    # Test 3: Extract pair_refs
    print("Test 3: Extract pair_refs")
    pair_refs = extract_pair_refs_v1(result1['watchlist_record'])
    print(f"Pair refs: {pair_refs}")
    print()

    # Test 4: Unknown profile_ref
    print("Test 4: Unknown profile_ref")
    items4 = [
        {
            "pair_ref": "deep:SUI/USDC",
            "source": "deep",
            "profile_ref": "UNKNOWN_PROFILE",
            "priority": "CORE",
            "enabled": "ON",
        },
    ]
    result4 = build_watchlist_record_v1(items4)
    print(f"Status: {result4['watchlist_record']['v14_watchlist_status']}")
    print(f"Warnings: {len(result4['warnings'])}")
    if result4['warnings']:
        for w in result4['warnings']:
            print(f"  - {w}")
    print()

    # Test 5: Expand with unknown profile_ref
    print("Test 5: Expand with unknown profile_ref")
    result5 = expand_watchlist_to_observation_plan_v1(result4['watchlist_record'])
    print(f"Plan status: {result5['observation_plan']['status']}")
    print(f"Plan items: {len(result5['observation_plan']['items'])}")
    if len(result5['observation_plan']['items']) > 0:
        item = result5['observation_plan']['items'][0]
        print(f"Item status: {item.get('status')}")
        print(f"Windows: {item['windows_enabled']}")
    print(f"Warnings: {len(result5['warnings'])}")
    print()

    # Test 6: enabled=OFF excluded from plan
    print("Test 6: enabled=OFF excluded from plan")
    items6 = [
        {
            "pair_ref": "deep:SUI/USDC",
            "source": "deep",
            "profile_ref": "CORE_3W",
            "priority": "CORE",
            "enabled": "OFF",
        },
    ]
    result6 = build_watchlist_record_v1(items6)
    result6_plan = expand_watchlist_to_observation_plan_v1(result6['watchlist_record'])
    print(f"Watchlist items: {len(result6['watchlist_record']['v14_watchlist_items'])}")
    print(f"Plan items: {len(result6_plan['observation_plan']['items'])} (expected 0)")
    print()

    # Test 7: Invalid input (defensive)
    print("Test 7: Invalid input (defensive)")
    result7 = build_watchlist_record_v1(None)
    print(f"Status: {result7['watchlist_record']['v14_watchlist_status']}")
    print(f"Warnings: {len(result7['warnings'])}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
