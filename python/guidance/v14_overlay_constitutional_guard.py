#!/usr/bin/env python3
"""
PR145: v1.4 Overlay Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on safe band × distortion overlay records.
    Guards against prescriptive language, trading verbs, numeric values, and eligibility coupling.

Constitutional Constraints:
    - No prescriptive language: No should/must/need to/recommend/advise
    - No trading verbs: No buy/sell/swap/execute/sign/transfer/bridge/order/trade
    - No token literals: No SUI/USDC/BTC/ETH
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/hence/means you can/means you should
    - No eligibility coupling: No "eligible therefore", "permission improved so", "allowed because"
    - No numeric patterns in text: Stress labels must not contain raw numbers

Guards:
    1. Forbidden vocabulary guard (trading verbs + prescriptive words)
    2. Token literal guard
    3. Address pattern guard
    4. Coupling phrase guard (causal + eligibility)
    5. Numeric pattern guard (prohibit standalone numbers in text)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


# Reuse forbidden vocabulary from PR144
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

# Eligibility coupling patterns (NEW for PR145)
ELIGIBILITY_COUPLING_PATTERNS = [
    "eligible therefore",
    "permission improved so",
    "allowed because",
    "permitted since",
    "authorized therefore",
    "can proceed because",
    "may proceed since",
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
                f"(overlay records must not contain trading verbs or prescriptive language)"
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
                f"(overlay records must not contain token literals)"
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
            "(overlay records must not contain addresses)"
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
                f"(overlay records must not contain causal coupling language)"
            )

    return warnings


def check_eligibility_coupling(text: str) -> List[str]:
    """
    Check for eligibility coupling phrases (NEW for PR145).

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for phrase in ELIGIBILITY_COUPLING_PATTERNS:
        if phrase.lower() in text_lower:
            warnings.append(
                f"eligibility coupling detected: '{phrase}' "
                f"(overlay records must not link stress state to permission/eligibility)"
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
            "(overlay text must not contain raw numeric values)"
        )

    # Check for percentage patterns (e.g., 25%, 50%)
    if re.search(r'\d+%', text):
        warnings.append(
            "numeric pattern detected: percentage "
            "(overlay text must not contain percentage values)"
        )

    # Check for large standalone integers (e.g., 1000, 500000)
    # Allow small numbers in bucket names (e.g., "BAND_1")
    if re.search(r'\b\d{3,}\b', text):
        warnings.append(
            "numeric pattern detected: large integer "
            "(overlay text must not contain raw numeric values)"
        )

    return warnings


def check_overlay_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate overlay record against constitutional guards.

    Args:
        record: Overlay record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check summary
    if "v14_overlay_summary" in record:
        summary = record["v14_overlay_summary"]
        if isinstance(summary, str):
            warnings.extend(check_forbidden_vocabulary(summary))
            warnings.extend(check_token_literals(summary))
            warnings.extend(check_address_patterns(summary))
            warnings.extend(check_coupling_phrases(summary))
            warnings.extend(check_eligibility_coupling(summary))
            warnings.extend(check_numeric_patterns(summary))

    # Check overlay notes
    if "v14_overlay_notes" in record:
        notes = record["v14_overlay_notes"]
        if isinstance(notes, list):
            for note in notes:
                if isinstance(note, str):
                    warnings.extend(check_forbidden_vocabulary(note))
                    warnings.extend(check_token_literals(note))
                    warnings.extend(check_address_patterns(note))
                    warnings.extend(check_coupling_phrases(note))
                    warnings.extend(check_eligibility_coupling(note))
                    warnings.extend(check_numeric_patterns(note))

    # Check basis (should be label-only, no numbers)
    if "v14_overlay_basis" in record:
        basis = record["v14_overlay_basis"]
        if isinstance(basis, list):
            basis_str = " ".join(str(b) for b in basis)
            warnings.extend(check_token_literals(basis_str))
            warnings.extend(check_address_patterns(basis_str))

    # Check artifacts (should be label-only, no numbers)
    if "v14_overlay_artifacts" in record:
        artifacts = record["v14_overlay_artifacts"]
        if isinstance(artifacts, list):
            artifacts_str = " ".join(str(a) for a in artifacts)
            warnings.extend(check_token_literals(artifacts_str))
            warnings.extend(check_address_patterns(artifacts_str))

    # Check distortion_subtypes (should be label-only)
    if "v14_overlay_distortion_subtypes" in record:
        subtypes = record["v14_overlay_distortion_subtypes"]
        if isinstance(subtypes, list):
            subtypes_str = " ".join(str(s) for s in subtypes)
            warnings.extend(check_token_literals(subtypes_str))
            warnings.extend(check_address_patterns(subtypes_str))

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Overlay Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean overlay record (no warnings)
    print("Test 1: Clean overlay record (no warnings)")
    clean_overlay = {
        "v14_overlay_summary": "safe band distortion overlay assembled for structural stress state.",
        "v14_overlay_notes": [
            "allocation within safe band but distortion signal present indicates structural tension."
        ],
    }
    clean_warnings = check_overlay_record(clean_overlay)
    print(f"Clean overlay warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty overlay (prescriptive language)
    print("Test 2: Dirty overlay (prescriptive language)")
    dirty_prescriptive = {
        "v14_overlay_summary": "You should reduce volatility allocation.",
    }
    dirty_warnings = check_overlay_record(dirty_prescriptive)
    print(f"Dirty overlay warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty overlay (eligibility coupling)
    print("Test 3: Dirty overlay (eligibility coupling)")
    dirty_eligibility = {
        "v14_overlay_summary": "Stress state is CALM therefore you are eligible to proceed.",
    }
    dirty_warnings_eligibility = check_overlay_record(dirty_eligibility)
    print(f"Dirty overlay warnings: {len(dirty_warnings_eligibility)}")
    if dirty_warnings_eligibility:
        print("  Warnings:")
        for w in dirty_warnings_eligibility:
            print(f"    - {w}")
    print()

    # Test 4: Dirty overlay (numeric patterns)
    print("Test 4: Dirty overlay (numeric patterns)")
    dirty_numeric = {
        "v14_overlay_notes": ["Current stress level is 0.75 or 75% of maximum."],
    }
    dirty_warnings_numeric = check_overlay_record(dirty_numeric)
    print(f"Dirty overlay warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
