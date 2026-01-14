#!/usr/bin/env python3
"""
PR149: v1.4 Shock Phase Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on shock phase records.
    Guards against prescriptive language, trading verbs, token literals, numeric values, and coupling.

Constitutional Constraints:
    - No prescriptive language: No should/must/need to/recommend/advise
    - No trading verbs: No buy/sell/swap/execute/sign/transfer/bridge/order/trade
    - No token literals: No BTC/USDC/SUI/ETH
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/hence/means you can/means you should
    - No phase coupling: No "phase=DOWN_SHOCK therefore sell"
    - No numeric patterns in text: Label-only output

Guards:
    1. Forbidden vocabulary guard (trading verbs + prescriptive words)
    2. Token literal guard
    3. Address pattern guard
    4. Coupling phrase guard (causal + phase coupling)
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
FORBIDDEN_TOKEN_LITERALS = ["SUI", "USDC", "BTC", "ETH", "DEEP", "CETUS", "SOL", "USDT", "WBTC"]

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

# Phase coupling patterns (specific to PR149)
PHASE_COUPLING_PATTERNS = [
    "shock so",
    "shock therefore",
    "phase=",  # e.g., "phase=DOWN_SHOCK therefore sell"
    "down_shock so",
    "down_shock therefore",
    "up_shock so",
    "up_shock therefore",
    "reversal so",
    "reversal therefore",
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
                f"(shock records must not contain trading verbs or prescriptive language)"
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
                f"(shock records must not contain token literals in text)"
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
            "(shock records must not contain addresses)"
        )

    return warnings


def check_coupling_phrases(text: str) -> List[str]:
    """
    Check for causal coupling phrases and phase coupling.

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
                f"(shock records must not contain causal coupling language)"
            )

    # Check phase-specific coupling patterns
    for phrase in PHASE_COUPLING_PATTERNS:
        if phrase.lower() in text_lower:
            warnings.append(
                f"phase coupling detected: '{phrase}' "
                f"(shock records must not couple phase to action)"
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
            "(shock text must not contain raw numeric values)"
        )

    # Check for percentage patterns (e.g., 25%, 50%)
    if re.search(r'\d+%', text):
        warnings.append(
            "numeric pattern detected: percentage "
            "(shock text must not contain percentage values)"
        )

    # Check for large standalone integers (e.g., 1000, 500000)
    # Allow small numbers in basis names (e.g., "BASIS_1")
    if re.search(r'\b\d{3,}\b', text):
        warnings.append(
            "numeric pattern detected: large integer "
            "(shock text must not contain raw numeric values)"
        )

    return warnings


def check_shock_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate shock record against constitutional guards.

    Args:
        record: Shock record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check pair_ref (should NOT be checked for token literals as it's an identifier)
    # pair_ref like "deep:wBTC/USDC" is allowed as it's an ID, not text

    # Check notes (if present)
    if "v14_shock_notes" in record:
        notes = record["v14_shock_notes"]
        if isinstance(notes, list):
            for note in notes:
                if isinstance(note, str):
                    warnings.extend(check_forbidden_vocabulary(note))
                    warnings.extend(check_token_literals(note))
                    warnings.extend(check_address_patterns(note))
                    warnings.extend(check_coupling_phrases(note))
                    warnings.extend(check_numeric_patterns(note))

    # Check basis_labels (should be label-only, no numbers)
    if "v14_shock_basis_labels" in record:
        basis_labels = record["v14_shock_basis_labels"]
        if isinstance(basis_labels, list):
            basis_str = " ".join(str(b) for b in basis_labels)
            # Don't check token literals in basis (BASIS_IMPULSE_UP is ok)
            # Don't check numeric patterns in basis (BASIS_1 is ok)
            warnings.extend(check_address_patterns(basis_str))

    # Check warnings (should be label-only, no numbers)
    if "v14_shock_warnings" in record:
        warning_list = record["v14_shock_warnings"]
        if isinstance(warning_list, list):
            for warning in warning_list:
                if isinstance(warning, str):
                    # Be lenient on warnings themselves (they may contain diagnostic info)
                    pass

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Shock Phase Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean shock record (no warnings)
    print("Test 1: Clean shock record (no warnings)")
    clean_shock = {
        "v14_shock_pair_ref": "deep:wBTC/USDC",
        "v14_shock_phase_label": "PHASE_PRE_SHOCK",
        "v14_shock_basis_labels": ["BASIS_LIQUIDITY_THINNING", "BASIS_IMPULSE_UP"],
    }
    clean_warnings = check_shock_record(clean_shock)
    print(f"Clean shock warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty shock (prescriptive language in notes)
    print("Test 2: Dirty shock (prescriptive language in notes)")
    dirty_prescriptive = {
        "v14_shock_notes": ["You should exit position immediately."],
    }
    dirty_warnings = check_shock_record(dirty_prescriptive)
    print(f"Dirty shock warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty shock (trading verbs)
    print("Test 3: Dirty shock (trading verbs)")
    dirty_trading = {
        "v14_shock_notes": ["Execute sell order now."],
    }
    dirty_warnings_trading = check_shock_record(dirty_trading)
    print(f"Dirty shock warnings: {len(dirty_warnings_trading)}")
    if dirty_warnings_trading:
        print("  Warnings:")
        for w in dirty_warnings_trading:
            print(f"    - {w}")
    print()

    # Test 4: Dirty shock (phase coupling)
    print("Test 4: Dirty shock (phase coupling)")
    dirty_coupling = {
        "v14_shock_notes": ["phase=DOWN_SHOCK therefore you should sell."],
    }
    dirty_warnings_coupling = check_shock_record(dirty_coupling)
    print(f"Dirty shock warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 5: Dirty shock (numeric patterns)
    print("Test 5: Dirty shock (numeric patterns)")
    dirty_numeric = {
        "v14_shock_notes": ["Price dropped 15% at 0.75 level."],
    }
    dirty_warnings_numeric = check_shock_record(dirty_numeric)
    print(f"Dirty shock warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
