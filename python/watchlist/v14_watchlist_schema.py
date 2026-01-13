#!/usr/bin/env python3
"""
PR148: v1.4 Watchlist Schema (READ-ONLY)

Purpose:
    Define schema for watchlist records.
    Watchlist = "What to observe" (pair_ref × source × profile_ref).
    Windows are NOT in watchlist, but in observation profiles.

Record Prefix:
    v14_watchlist_

Required Fields:
    v14_watchlist_version: "v1"
    v14_watchlist_status: AVAILABLE | ERROR
    v14_watchlist_mode: READ_ONLY
    v14_watchlist_items: List[dict] (watchlist items)
    v14_watchlist_summary: Non-prescriptive summary

Watchlist Item Fields (minimum):
    pair_ref: Unique identifier (e.g., "deep:SUI/USDC", treated as anonymous ID)
    source: Source label (e.g., "deep", "cetus")
    profile_ref: Observation profile reference (e.g., "CORE_3W")
    priority: CORE | EXTENDED | EXPERIMENTAL
    enabled: ON | OFF
    notes: Optional notes

Prohibited:
    - NO window field in watchlist items (windows are in profiles)
    - NO token literals (SUI/USDC/BTC/ETH)
    - NO amounts or numeric values in text
    - NO addresses (0x... patterns)
    - NO trading verbs (buy/sell/swap/execute)
    - NO prescriptive language (should/must/recommend)

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Non-prescriptive: No should/must/recommend/advise
    - Label-only: No numeric values in text
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Watchlist version
WATCHLIST_VERSION_V1 = "v1"

# Watchlist status constants
WATCHLIST_STATUS_AVAILABLE = "AVAILABLE"
WATCHLIST_STATUS_ERROR = "ERROR"

# Watchlist mode constants
WATCHLIST_MODE_READ_ONLY = "READ_ONLY"

# Priority constants
PRIORITY_CORE = "CORE"
PRIORITY_EXTENDED = "EXTENDED"
PRIORITY_EXPERIMENTAL = "EXPERIMENTAL"

# Enabled constants
ENABLED_ON = "ON"
ENABLED_OFF = "OFF"


class V14WatchlistSchema:
    """Schema for watchlist records."""

    # Valid statuses
    VALID_STATUSES = [
        WATCHLIST_STATUS_AVAILABLE,
        WATCHLIST_STATUS_ERROR,
    ]

    # Valid modes
    VALID_MODES = [
        WATCHLIST_MODE_READ_ONLY,
    ]

    # Valid priorities
    VALID_PRIORITIES = [
        PRIORITY_CORE,
        PRIORITY_EXTENDED,
        PRIORITY_EXPERIMENTAL,
    ]

    # Valid enabled values
    VALID_ENABLED = [
        ENABLED_ON,
        ENABLED_OFF,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "v14_watchlist_version",
        "v14_watchlist_status",
        "v14_watchlist_mode",
        "v14_watchlist_items",
        "v14_watchlist_summary",
    ]

    # Required item fields
    REQUIRED_ITEM_FIELDS = [
        "pair_ref",
        "source",
        "profile_ref",
        "priority",
        "enabled",
    ]

    @staticmethod
    def create_watchlist_record(
        version: str = WATCHLIST_VERSION_V1,
        status: str = WATCHLIST_STATUS_AVAILABLE,
        mode: str = WATCHLIST_MODE_READ_ONLY,
        items: Optional[List[Dict[str, Any]]] = None,
        summary: str = "",
    ) -> Dict[str, Any]:
        """
        Create watchlist record.

        Args:
            version: Watchlist version (default "v1")
            status: AVAILABLE | ERROR
            mode: READ_ONLY
            items: List of watchlist items
            summary: Non-prescriptive summary

        Returns:
            Watchlist record
        """
        record = {
            "v14_watchlist_version": version,
            "v14_watchlist_status": status,
            "v14_watchlist_mode": mode,
            "v14_watchlist_items": items if items else [],
            "v14_watchlist_summary": summary,
        }

        return record

    @staticmethod
    def create_error_record(
        summary: str = "watchlist generation failed.",
    ) -> Dict[str, Any]:
        """
        Create error record.

        Args:
            summary: Error summary

        Returns:
            Error record
        """
        return V14WatchlistSchema.create_watchlist_record(
            status=WATCHLIST_STATUS_ERROR,
            items=[],
            summary=summary,
        )

    @staticmethod
    def validate_watchlist_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate watchlist record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V14WatchlistSchema.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate version
        version = record.get("v14_watchlist_version")
        if version != WATCHLIST_VERSION_V1:
            errors.append(f"invalid version: {version} (expected {WATCHLIST_VERSION_V1})")

        # Validate status
        status = record.get("v14_watchlist_status")
        if status not in V14WatchlistSchema.VALID_STATUSES:
            errors.append(f"invalid status: {status}")

        # Validate mode
        mode = record.get("v14_watchlist_mode")
        if mode not in V14WatchlistSchema.VALID_MODES:
            errors.append(f"invalid mode: {mode}")

        # Validate types
        if not isinstance(record.get("v14_watchlist_summary"), str):
            errors.append("summary must be string")

        if not isinstance(record.get("v14_watchlist_items"), list):
            errors.append("items must be list")

        # Validate items
        items = record.get("v14_watchlist_items", [])
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append(f"item {i} must be dict")
                continue

            # Check required item fields
            for field in V14WatchlistSchema.REQUIRED_ITEM_FIELDS:
                if field not in item:
                    errors.append(f"item {i} missing required field: {field}")

            # Validate priority
            priority = item.get("priority")
            if priority and priority not in V14WatchlistSchema.VALID_PRIORITIES:
                errors.append(f"item {i} invalid priority: {priority}")

            # Validate enabled
            enabled = item.get("enabled")
            if enabled and enabled not in V14WatchlistSchema.VALID_ENABLED:
                errors.append(f"item {i} invalid enabled: {enabled}")

            # Check for prohibited window field
            if "window" in item or "windows" in item:
                errors.append(f"item {i} contains prohibited window field (windows belong in profiles, not watchlist)")

        return errors

    @staticmethod
    def create_watchlist_item(
        pair_ref: str,
        source: str,
        profile_ref: str,
        priority: str = PRIORITY_CORE,
        enabled: str = ENABLED_ON,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create watchlist item.

        Args:
            pair_ref: Pair reference (e.g., "deep:SUI/USDC")
            source: Source label (e.g., "deep", "cetus")
            profile_ref: Observation profile reference (e.g., "CORE_3W")
            priority: CORE | EXTENDED | EXPERIMENTAL
            enabled: ON | OFF
            notes: Optional notes

        Returns:
            Watchlist item
        """
        item = {
            "pair_ref": pair_ref,
            "source": source,
            "profile_ref": profile_ref,
            "priority": priority,
            "enabled": enabled,
        }

        if notes is not None:
            item["notes"] = notes

        return item


def get_watchlist_schema_info() -> Dict[str, Any]:
    """
    Get watchlist schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1",
        "schema_type": "watchlist",
        "record_prefix": "v14_watchlist_",
        "valid_statuses": V14WatchlistSchema.VALID_STATUSES,
        "valid_modes": V14WatchlistSchema.VALID_MODES,
        "valid_priorities": V14WatchlistSchema.VALID_PRIORITIES,
        "valid_enabled": V14WatchlistSchema.VALID_ENABLED,
        "philosophy": "Watchlist = 'What to observe' (pair_ref × source × profile_ref). Windows are in profiles, NOT watchlist.",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "no_numeric_values_in_text",
            "no_addresses",
            "no_windows_in_watchlist",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Watchlist Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create valid record
    print("Test 1: Create valid record")
    items = [
        V14WatchlistSchema.create_watchlist_item(
            pair_ref="deep:SUI/USDC",
            source="deep",
            profile_ref="CORE_3W",
            priority=PRIORITY_CORE,
            enabled=ENABLED_ON,
        ),
    ]
    record1 = V14WatchlistSchema.create_watchlist_record(
        status=WATCHLIST_STATUS_AVAILABLE,
        items=items,
        summary="watchlist contains 1 enabled observation target.",
    )
    errors1 = V14WatchlistSchema.validate_watchlist_record(record1)
    print(f"Valid record errors: {len(errors1)}")
    if errors1:
        for e in errors1:
            print(f"  - {e}")
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    record2 = V14WatchlistSchema.create_error_record(
        summary="watchlist generation failed: invalid inputs."
    )
    errors2 = V14WatchlistSchema.validate_watchlist_record(record2)
    print(f"Error record status: {record2['v14_watchlist_status']}")
    print(f"Error record errors: {len(errors2)}")
    print()

    # Test 3: Check window prohibition
    print("Test 3: Check window prohibition")
    items_with_window = [
        {
            "pair_ref": "deep:SUI/USDC",
            "source": "deep",
            "profile_ref": "CORE_3W",
            "priority": PRIORITY_CORE,
            "enabled": ENABLED_ON,
            "window": "SHORT",  # PROHIBITED
        },
    ]
    record3 = V14WatchlistSchema.create_watchlist_record(
        items=items_with_window,
        summary="test",
    )
    errors3 = V14WatchlistSchema.validate_watchlist_record(record3)
    print(f"Record with window field errors: {len(errors3)}")
    if errors3:
        for e in errors3:
            print(f"  - {e}")
    print()

    # Test 4: Get schema info
    print("Test 4: Get schema info")
    info = get_watchlist_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
