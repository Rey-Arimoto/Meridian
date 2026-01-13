#!/usr/bin/env python3
"""
PR148: v1.4 Watchlist Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on watchlist records.
    Guards against prescriptive language, trading verbs, token literals, numeric values, and coupling.

Constitutional Constraints:
    - No prescriptive language: No should/must/need to/recommend/advise
    - No trading verbs: No buy/sell/swap/execute/sign/transfer/bridge/order/trade
    - No token literals: No SUI/USDC/BTC/ETH
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/hence/means you can/means you should
    - No numeric patterns in text: Label-only output

Guards:
    1. Forbidden vocabulary guard (trading verbs + prescriptive words)
    2. Token literal guard
    3. Address pattern guard
    4. Coupling phrase guard
    5. Numeric pattern guard

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


# Reuse forbidden vocabulary
FORBIDDEN_TRADING_VERBS = [
    "buy",
    "sell",
    "swap",
    "execute",
    "sign",
    "transfer",
    "bridge",
    "order",
    "trade",
    "send",
    "broadcast",
    "submit",
    "rebalance",
]

FORBIDDEN_PRESCRIPTIVE_LANGUAGE = [
    "should",
    "must",
    "need to",
    "have to",
    "ought to",
    "require",
    "recommend",
    "suggest",
    "advise",
    "instruct",
]

FORBIDDEN_VOCABULARY = FORBIDDEN_TRADING_VERBS + FORBIDDEN_PRESCRIPTIVE_LANGUAGE

# Forbidden token literals
FORBIDDEN_TOKEN_LITERALS = ["SUI", "USDC", "BTC", "ETH", "DEEP", "CETUS", "SOL", "USDT"]

# Causal coupling patterns
COUPLING_PATTERNS = [
    "therefore",
    "so",
    "hence",
    "means you can",
    "means you should",
    "implies you",
    "suggests you",
]


def check_forbidden_vocabulary(text: str) -> List[str]:
    """
    Check for forbidden vocabulary (trading verbs + prescriptive language).

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for word in FORBIDDEN_VOCABULARY:
        if word.lower() in text_lower:
            warnings.append(
                f"forbidden vocabulary detected: '{word}' "
                f"(watchlist records must not contain trading verbs or prescriptive language)"
            )

    return warnings


def check_token_literals(text: str) -> List[str]:
    """
    Check for token literal patterns.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_upper = text.upper()

    for token in FORBIDDEN_TOKEN_LITERALS:
        if token in text_upper:
            warnings.append(
                f"token literal detected: '{token}' "
                f"(watchlist records must not contain token literals)"
            )

    return warnings


def check_address_patterns(text: str) -> List[str]:
    """
    Check for address patterns (0x...).

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    # Check for 0x followed by hex characters
    if "0x" in text.lower():
        warnings.append(
            "address pattern detected: '0x...' "
            "(watchlist records must not contain addresses)"
        )

    return warnings


def check_coupling_phrases(text: str) -> List[str]:
    """
    Check for causal coupling phrases.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    # Check standard coupling patterns
    for phrase in COUPLING_PATTERNS:
        if phrase.lower() in text_lower:
            warnings.append(
                f"coupling phrase detected: '{phrase}' "
                f"(watchlist records must not contain causal coupling language)"
            )

    return warnings


def check_numeric_patterns(text: str) -> List[str]:
    """
    Check for numeric patterns in text (prohibit standalone numbers).

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    # Check for decimal numbers (e.g., 0.25, 1.5, 100.0)
    if re.search(r'\b\d+\.\d+\b', text):
        warnings.append(
            "numeric pattern detected: decimal number "
            "(watchlist text must not contain raw numeric values)"
        )

    # Check for percentage patterns (e.g., 25%, 50%)
    if re.search(r'\d+%', text):
        warnings.append(
            "numeric pattern detected: percentage "
            "(watchlist text must not contain percentage values)"
        )

    # Check for large standalone integers (e.g., 1000, 500000)
    if re.search(r'\b\d{3,}\b', text):
        warnings.append(
            "numeric pattern detected: large integer "
            "(watchlist text must not contain raw numeric values)"
        )

    return warnings


def check_watchlist_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate watchlist record against constitutional guards.

    Args:
        record: Watchlist record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check summary
    if "v14_watchlist_summary" in record:
        summary = record["v14_watchlist_summary"]
        if isinstance(summary, str):
            warnings.extend(check_forbidden_vocabulary(summary))
            warnings.extend(check_token_literals(summary))
            warnings.extend(check_address_patterns(summary))
            warnings.extend(check_coupling_phrases(summary))
            warnings.extend(check_numeric_patterns(summary))

    # Check items
    if "v14_watchlist_items" in record:
        items = record["v14_watchlist_items"]
        if isinstance(items, list):
            for i, item in enumerate(items):
                if not isinstance(item, dict):
                    continue

                # Check pair_ref for token literals
                pair_ref = item.get("pair_ref")
                if isinstance(pair_ref, str):
                    # Note: pair_ref can contain token symbols (e.g., "deep:SUI/USDC")
                    # This is allowed as it's an identifier, not text
                    pass

                # Check notes
                notes = item.get("notes")
                if isinstance(notes, str):
                    warnings.extend(check_forbidden_vocabulary(notes))
                    warnings.extend(check_token_literals(notes))
                    warnings.extend(check_address_patterns(notes))
                    warnings.extend(check_coupling_phrases(notes))
                    warnings.extend(check_numeric_patterns(notes))

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Watchlist Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean watchlist record (no warnings)
    print("Test 1: Clean watchlist record (no warnings)")
    clean_watchlist = {
        "v14_watchlist_summary": "watchlist contains 1 enabled observation target.",
        "v14_watchlist_items": [
            {
                "pair_ref": "deep:SUI/USDC",
                "source": "deep",
                "profile_ref": "CORE_3W",
                "priority": "CORE",
                "enabled": "ON",
            },
        ],
    }
    clean_warnings = check_watchlist_record(clean_watchlist)
    print(f"Clean watchlist warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty watchlist (prescriptive language)
    print("Test 2: Dirty watchlist (prescriptive language)")
    dirty_prescriptive = {
        "v14_watchlist_summary": "You should monitor SUI/USDC pair.",
    }
    dirty_warnings = check_watchlist_record(dirty_prescriptive)
    print(f"Dirty watchlist warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty watchlist (trading verbs)
    print("Test 3: Dirty watchlist (trading verbs)")
    dirty_trading = {
        "v14_watchlist_summary": "Execute trades on these pairs.",
    }
    dirty_warnings_trading = check_watchlist_record(dirty_trading)
    print(f"Dirty watchlist warnings: {len(dirty_warnings_trading)}")
    if dirty_warnings_trading:
        print("  Warnings:")
        for w in dirty_warnings_trading:
            print(f"    - {w}")
    print()

    # Test 4: Dirty watchlist (numeric patterns)
    print("Test 4: Dirty watchlist (numeric patterns)")
    dirty_numeric = {
        "v14_watchlist_summary": "Monitor with 0.75 weight or 75% priority.",
    }
    dirty_warnings_numeric = check_watchlist_record(dirty_numeric)
    print(f"Dirty watchlist warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 5: Dirty item notes
    print("Test 5: Dirty item notes")
    dirty_notes = {
        "v14_watchlist_items": [
            {
                "pair_ref": "deep:SUI/USDC",
                "source": "deep",
                "profile_ref": "CORE_3W",
                "priority": "CORE",
                "enabled": "ON",
                "notes": "You should buy more volatility at 0x1234.",
            },
        ],
    }
    dirty_warnings_notes = check_watchlist_record(dirty_notes)
    print(f"Dirty notes warnings: {len(dirty_warnings_notes)}")
    if dirty_warnings_notes:
        print("  Warnings:")
        for w in dirty_warnings_notes:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
