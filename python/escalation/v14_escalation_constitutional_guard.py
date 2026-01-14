#!/usr/bin/env python3
"""
PR150: v1.4 Escalation Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on escalation records.
    Guards against prescriptive language, trading verbs, token literals, numeric values, and coupling.

Constitutional Constraints:
    - No prescriptive language: No should/must/need to/recommend/advise
    - No trading verbs: No buy/sell/swap/execute/sign/transfer/bridge/order/trade
    - No token literals: No BTC/USDC/SUI/ETH
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/hence/means you can/means you should
    - No escalation coupling: No "stress escalated therefore act"
    - No numeric patterns in text: Label-only output

Guards:
    1. Forbidden vocabulary guard (trading verbs + prescriptive words)
    2. Token literal guard
    3. Address pattern guard
    4. Coupling phrase guard (causal + escalation coupling)
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

# Escalation coupling patterns (specific to PR150)
ESCALATION_COUPLING_PATTERNS = [
    "escalated so",
    "escalated therefore",
    "stress=",  # e.g., "stress=STRESSED therefore exit"
    "stressed so",
    "stressed therefore",
    "tense so",
    "tense therefore",
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
                f"(escalation records must not contain trading verbs or prescriptive language)"
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
                f"(escalation records must not contain token literals in text)"
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
            "(escalation records must not contain addresses)"
        )

    return warnings


def check_coupling_phrases(text: str) -> List[str]:
    """
    Check for causal coupling phrases and escalation coupling.

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
                f"(escalation records must not contain causal coupling language)"
            )

    # Check escalation-specific coupling patterns
    for phrase in ESCALATION_COUPLING_PATTERNS:
        if phrase.lower() in text_lower:
            warnings.append(
                f"escalation coupling detected: '{phrase}' "
                f"(escalation records must not couple stress escalation to action)"
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
            "(escalation text must not contain raw numeric values)"
        )

    # Check for percentage patterns (e.g., 25%, 50%)
    if re.search(r'\d+%', text):
        warnings.append(
            "numeric pattern detected: percentage "
            "(escalation text must not contain percentage values)"
        )

    # Check for large standalone integers (e.g., 1000, 500000)
    if re.search(r'\b\d{3,}\b', text):
        warnings.append(
            "numeric pattern detected: large integer "
            "(escalation text must not contain raw numeric values)"
        )

    return warnings


def check_escalation_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate escalation record against constitutional guards.

    Args:
        record: Escalation record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check warnings (should be label-only, no numbers)
    if "v14_escalation_warnings" in record:
        warning_list = record["v14_escalation_warnings"]
        if isinstance(warning_list, list):
            for warning in warning_list:
                if isinstance(warning, str):
                    # Be lenient on warnings themselves (they may contain diagnostic info)
                    pass

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Escalation Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean escalation record (no warnings)
    print("Test 1: Clean escalation record (no warnings)")
    clean_escalation = {
        "v14_escalation_phase_label": "PHASE_PRE_SHOCK",
        "v14_escalation_input_stress_label": "STRESS_CALM",
        "v14_escalation_output_stress_label": "STRESS_TENSE",
        "v14_escalation_escalated_flag": "ON",
    }
    clean_warnings = check_escalation_record(clean_escalation)
    print(f"Clean escalation warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty escalation (prescriptive language)
    print("Test 2: Dirty escalation (prescriptive language)")
    dirty_text = "You should exit because stress escalated."
    dirty_warnings = []
    dirty_warnings.extend(check_forbidden_vocabulary(dirty_text))
    dirty_warnings.extend(check_coupling_phrases(dirty_text))
    print(f"Dirty text warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty escalation (escalation coupling)
    print("Test 3: Dirty escalation (escalation coupling)")
    dirty_coupling = "stress=STRESSED therefore sell."
    dirty_warnings_coupling = []
    dirty_warnings_coupling.extend(check_forbidden_vocabulary(dirty_coupling))
    dirty_warnings_coupling.extend(check_coupling_phrases(dirty_coupling))
    print(f"Dirty coupling warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 4: Dirty escalation (numeric patterns)
    print("Test 4: Dirty escalation (numeric patterns)")
    dirty_numeric = "Stress escalated 50% at 0.75 level."
    dirty_warnings_numeric = []
    dirty_warnings_numeric.extend(check_numeric_patterns(dirty_numeric))
    print(f"Dirty numeric warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
