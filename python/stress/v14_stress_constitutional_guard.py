#!/usr/bin/env python3
"""
PR146: v1.4 Stress Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on stress rule table records.
    Guards against prescriptive language, trading verbs, and numeric values.

Constitutional Constraints:
    - No prescriptive language: No should/must/need to/recommend/advise
    - No trading verbs: No buy/sell/swap/execute/sign/transfer/bridge/order/trade
    - No token literals: No SUI/USDC/BTC/ETH
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/hence/means you can/means you should
    - No numeric patterns in text: Stress labels must not contain raw numbers

Guards:
    1. Forbidden vocabulary guard (trading verbs + prescriptive words)
    2. Token literal guard
    3. Address pattern guard
    4. Coupling phrase guard (causal)
    5. Numeric pattern guard (prohibit standalone numbers in text)

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
                f"(stress records must not contain trading verbs or prescriptive language)"
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
                f"(stress records must not contain token literals)"
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
            "(stress records must not contain addresses)"
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

    for phrase in COUPLING_PATTERNS:
        if phrase.lower() in text_lower:
            warnings.append(
                f"coupling phrase detected: '{phrase}' "
                f"(stress records must not contain causal coupling language)"
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
            "(stress text must not contain raw numeric values)"
        )

    # Check for percentage patterns (e.g., 25%, 50%)
    if re.search(r'\d+%', text):
        warnings.append(
            "numeric pattern detected: percentage "
            "(stress text must not contain percentage values)"
        )

    # Check for large standalone integers (e.g., 1000, 500000)
    # Allow small numbers in basis names (e.g., "BASIS_1")
    if re.search(r'\b\d{3,}\b', text):
        warnings.append(
            "numeric pattern detected: large integer "
            "(stress text must not contain raw numeric values)"
        )

    return warnings


def check_stress_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate stress record against constitutional guards.

    Args:
        record: Stress record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check summary
    if "v14_stress_summary" in record:
        summary = record["v14_stress_summary"]
        if isinstance(summary, str):
            warnings.extend(check_forbidden_vocabulary(summary))
            warnings.extend(check_token_literals(summary))
            warnings.extend(check_address_patterns(summary))
            warnings.extend(check_coupling_phrases(summary))
            warnings.extend(check_numeric_patterns(summary))

    # Check notes (if present)
    if "v14_stress_notes" in record:
        notes = record["v14_stress_notes"]
        if isinstance(notes, list):
            for note in notes:
                if isinstance(note, str):
                    warnings.extend(check_forbidden_vocabulary(note))
                    warnings.extend(check_token_literals(note))
                    warnings.extend(check_address_patterns(note))
                    warnings.extend(check_coupling_phrases(note))
                    warnings.extend(check_numeric_patterns(note))

    # Check basis (should be label-only, no numbers)
    if "v14_stress_basis" in record:
        basis = record["v14_stress_basis"]
        if isinstance(basis, list):
            basis_str = " ".join(str(b) for b in basis)
            warnings.extend(check_token_literals(basis_str))
            warnings.extend(check_address_patterns(basis_str))

    # Check artifacts (should be label-only, no numbers)
    if "v14_stress_artifacts" in record:
        artifacts = record["v14_stress_artifacts"]
        if isinstance(artifacts, list):
            artifacts_str = " ".join(str(a) for a in artifacts)
            warnings.extend(check_token_literals(artifacts_str))
            warnings.extend(check_address_patterns(artifacts_str))

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Stress Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean stress record (no warnings)
    print("Test 1: Clean stress record (no warnings)")
    clean_stress = {
        "v14_stress_summary": "stress label determined from fixed table.",
        "v14_stress_basis": ["BASIS_REGIME_MEDIUM", "BASIS_BAND_SAFE", "BASIS_NO_DISTORTION"],
    }
    clean_warnings = check_stress_record(clean_stress)
    print(f"Clean stress warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty stress (prescriptive language)
    print("Test 2: Dirty stress (prescriptive language)")
    dirty_prescriptive = {
        "v14_stress_summary": "You should reduce volatility exposure.",
    }
    dirty_warnings = check_stress_record(dirty_prescriptive)
    print(f"Dirty stress warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty stress (token literals)
    print("Test 3: Dirty stress (token literals)")
    dirty_tokens = {
        "v14_stress_summary": "SUI and USDC stress level high.",
    }
    dirty_warnings_tokens = check_stress_record(dirty_tokens)
    print(f"Dirty stress warnings: {len(dirty_warnings_tokens)}")
    if dirty_warnings_tokens:
        print("  Warnings:")
        for w in dirty_warnings_tokens:
            print(f"    - {w}")
    print()

    # Test 4: Dirty stress (numeric patterns)
    print("Test 4: Dirty stress (numeric patterns)")
    dirty_numeric = {
        "v14_stress_summary": "Current stress level is 0.75 or 75% of maximum.",
    }
    dirty_warnings_numeric = check_stress_record(dirty_numeric)
    print(f"Dirty stress warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 5: Dirty stress (coupling phrases)
    print("Test 5: Dirty stress (coupling phrases)")
    dirty_coupling = {
        "v14_stress_summary": "Stress is STRESSED therefore you should exit.",
    }
    dirty_warnings_coupling = check_stress_record(dirty_coupling)
    print(f"Dirty stress warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
