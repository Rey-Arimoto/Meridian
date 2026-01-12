#!/usr/bin/env python3
"""
PR130: v1.2 Role Requirements Schema v1 (READ-ONLY)

Purpose:
    Define requirements for each role type.
    Requirements = minimum/maximum thresholds per axis.

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No amounts: No numeric values in output
    - No addresses: No 0x... patterns

Role Types:
    - GAS_ROLE: Network operation utility carrier
    - STABILITY_ROLE: Value stability carrier
    - LIQUIDITY_ROLE: Market depth carrier
    - VOLATILITY_ROLE: Price movement carrier
    - HEDGE_ROLE: Directional offset carrier

v12_role_ Prefix:
    All role fields use v12_role_ prefix.
"""

from typing import Any, Dict, List, Optional

from .v12_asset_profile_schema import (
    OBS_LOW,
    OBS_MEDIUM,
    OBS_HIGH,
    CENS_LOW,
    CENS_MEDIUM,
    CENS_HIGH,
    LIQ_LOW,
    LIQ_MEDIUM,
    LIQ_HIGH,
    DEP_NONE,
    DEP_LOW,
    DEP_MEDIUM,
    DEP_HIGH,
)


# Role type constants
GAS_ROLE = "GAS_ROLE"
STABILITY_ROLE = "STABILITY_ROLE"
LIQUIDITY_ROLE = "LIQUIDITY_ROLE"
VOLATILITY_ROLE = "VOLATILITY_ROLE"
HEDGE_ROLE = "HEDGE_ROLE"

VALID_ROLE_TYPES = [
    GAS_ROLE,
    STABILITY_ROLE,
    LIQUIDITY_ROLE,
    VOLATILITY_ROLE,
    HEDGE_ROLE,
]


# Role requirements (min/max thresholds per axis)
ROLE_REQUIREMENTS = {
    GAS_ROLE: {
        "min_observability": OBS_HIGH,
        "min_censorship_resistance": CENS_HIGH,
        "min_liquidatability": LIQ_MEDIUM,
        "max_dependency": DEP_LOW,
        "description": "network operation utility carrier",
    },
    STABILITY_ROLE: {
        "min_observability": OBS_MEDIUM,
        "min_censorship_resistance": CENS_MEDIUM,
        "min_liquidatability": LIQ_HIGH,
        "max_dependency": DEP_MEDIUM,
        "description": "value stability carrier",
    },
    LIQUIDITY_ROLE: {
        "min_observability": OBS_HIGH,
        "min_censorship_resistance": CENS_MEDIUM,
        "min_liquidatability": LIQ_HIGH,
        "max_dependency": DEP_MEDIUM,
        "description": "market depth carrier",
    },
    VOLATILITY_ROLE: {
        "min_observability": OBS_MEDIUM,
        "min_censorship_resistance": CENS_LOW,
        "min_liquidatability": LIQ_MEDIUM,
        "max_dependency": DEP_HIGH,
        "description": "price movement carrier",
    },
    HEDGE_ROLE: {
        "min_observability": OBS_MEDIUM,
        "min_censorship_resistance": CENS_MEDIUM,
        "min_liquidatability": LIQ_MEDIUM,
        "max_dependency": DEP_MEDIUM,
        "description": "directional offset carrier",
    },
}


# Axis level ordering (for comparison)
OBSERVABILITY_ORDER = [OBS_LOW, OBS_MEDIUM, OBS_HIGH]
CENSORSHIP_RESISTANCE_ORDER = [CENS_LOW, CENS_MEDIUM, CENS_HIGH]
LIQUIDATABILITY_ORDER = [LIQ_LOW, LIQ_MEDIUM, LIQ_HIGH]
DEPENDENCY_ORDER = [DEP_NONE, DEP_LOW, DEP_MEDIUM, DEP_HIGH]


def get_axis_level(value: str, axis_order: List[str]) -> int:
    """
    Get numeric level for axis value (for comparison).

    Args:
        value: Axis value
        axis_order: Ordered list of valid values

    Returns:
        Numeric level (0-based index, -1 if invalid)
    """
    try:
        return axis_order.index(value)
    except ValueError:
        return -1


def meets_minimum(actual: str, required: str, axis_order: List[str]) -> bool:
    """
    Check if actual value meets minimum requirement.

    Args:
        actual: Actual value
        required: Required minimum value
        axis_order: Ordered list of valid values

    Returns:
        True if actual >= required
    """
    actual_level = get_axis_level(actual, axis_order)
    required_level = get_axis_level(required, axis_order)

    # If either is invalid, fail safe
    if actual_level < 0 or required_level < 0:
        return False

    return actual_level >= required_level


def meets_maximum(actual: str, required: str, axis_order: List[str]) -> bool:
    """
    Check if actual value meets maximum requirement.

    Args:
        actual: Actual value
        required: Required maximum value
        axis_order: Ordered list of valid values

    Returns:
        True if actual <= required
    """
    actual_level = get_axis_level(actual, axis_order)
    required_level = get_axis_level(required, axis_order)

    # If either is invalid, fail safe
    if actual_level < 0 or required_level < 0:
        return False

    return actual_level <= required_level


def get_role_requirements(role_type: str) -> Optional[Dict[str, Any]]:
    """
    Get role requirements for given role type.

    Args:
        role_type: Role type

    Returns:
        Role requirements dict or None if invalid
    """
    return ROLE_REQUIREMENTS.get(role_type)


def get_role_requirements_info() -> Dict[str, Any]:
    """
    Get role requirements information.

    Returns:
        Dict with role requirements metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "role_requirements",
        "valid_role_types": VALID_ROLE_TYPES,
        "role_requirements": ROLE_REQUIREMENTS,
        "axis_orderings": {
            "observability": OBSERVABILITY_ORDER,
            "censorship_resistance": CENSORSHIP_RESISTANCE_ORDER,
            "liquidatability": LIQUIDATABILITY_ORDER,
            "dependency": DEPENDENCY_ORDER,
        },
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "no_token_literals",
            "no_amounts",
            "no_addresses",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Role Requirements Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Get role requirements
    print("Test 1: Get role requirements")
    for role_type in VALID_ROLE_TYPES:
        reqs = get_role_requirements(role_type)
        print(f"{role_type}:")
        print(f"  Description: {reqs['description']}")
        print(f"  Min observability: {reqs['min_observability']}")
        print(f"  Min censorship resistance: {reqs['min_censorship_resistance']}")
        print(f"  Min liquidatability: {reqs['min_liquidatability']}")
        print(f"  Max dependency: {reqs['max_dependency']}")
        print()

    # Test 2: meets_minimum
    print("Test 2: meets_minimum")
    test_cases = [
        (OBS_HIGH, OBS_MEDIUM, OBSERVABILITY_ORDER, True),
        (OBS_LOW, OBS_MEDIUM, OBSERVABILITY_ORDER, False),
        (CENS_HIGH, CENS_HIGH, CENSORSHIP_RESISTANCE_ORDER, True),
    ]
    for actual, required, order, expected in test_cases:
        result = meets_minimum(actual, required, order)
        status = "✓" if result == expected else "✗"
        print(f"  {status} meets_minimum({actual}, {required}) = {result} (expected {expected})")
    print()

    # Test 3: meets_maximum
    print("Test 3: meets_maximum")
    test_cases = [
        (DEP_LOW, DEP_MEDIUM, DEPENDENCY_ORDER, True),
        (DEP_HIGH, DEP_LOW, DEPENDENCY_ORDER, False),
        (DEP_LOW, DEP_LOW, DEPENDENCY_ORDER, True),
    ]
    for actual, required, order, expected in test_cases:
        result = meets_maximum(actual, required, order)
        status = "✓" if result == expected else "✗"
        print(f"  {status} meets_maximum({actual}, {required}) = {result} (expected {expected})")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
