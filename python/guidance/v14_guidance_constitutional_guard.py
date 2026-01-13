#!/usr/bin/env python3
"""
PR144: v1.4 Guidance Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on role safe band guidance records.
    Guards against prescriptive language, trading verbs, and numeric values in text.

Constitutional Constraints:
    - No prescriptive language: No should/must/need to/recommend/advise
    - No trading verbs: No buy/sell/swap/execute/sign/transfer/bridge/order/trade
    - No token literals: No SUI/USDC/BTC/ETH
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/hence/means you can/means you should
    - No numeric patterns in text: Ratios must not appear in text fields

Guards:
    1. Forbidden vocabulary guard (trading verbs + prescriptive words)
    2. Token literal guard
    3. Address pattern guard
    4. Coupling phrase guard
    5. Numeric pattern guard (prohibit standalone numbers in text)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


# Forbidden trading verbs
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

# Forbidden prescriptive language
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

# Combined forbidden vocabulary
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
                f"(guidance records must not contain trading verbs or prescriptive language)"
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
                f"(guidance records must not contain token literals)"
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
            "(guidance records must not contain addresses)"
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
                f"(guidance records must not contain causal coupling language)"
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
            "(guidance text must not contain raw numeric values)"
        )

    # Check for percentage patterns (e.g., 25%, 50%)
    if re.search(r'\d+%', text):
        warnings.append(
            "numeric pattern detected: percentage "
            "(guidance text must not contain percentage values)"
        )

    # Check for large standalone integers (e.g., 1000, 500000)
    # Allow small numbers in bucket names (e.g., "BAND_1")
    if re.search(r'\b\d{3,}\b', text):
        warnings.append(
            "numeric pattern detected: large integer "
            "(guidance text must not contain raw numeric values)"
        )

    return warnings


def check_guidance_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate guidance record against constitutional guards.

    Args:
        record: Guidance record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check summary
    if "v14_guidance_summary" in record:
        summary = record["v14_guidance_summary"]
        if isinstance(summary, str):
            warnings.extend(check_forbidden_vocabulary(summary))
            warnings.extend(check_token_literals(summary))
            warnings.extend(check_address_patterns(summary))
            warnings.extend(check_coupling_phrases(summary))
            warnings.extend(check_numeric_patterns(summary))

    # Check roles interpretations
    if "v14_guidance_roles" in record:
        roles = record["v14_guidance_roles"]
        if isinstance(roles, dict):
            for role_name, role_entry in roles.items():
                if not isinstance(role_entry, dict):
                    continue

                interpretation = role_entry.get("interpretation")
                if isinstance(interpretation, str):
                    warnings.extend(check_forbidden_vocabulary(interpretation))
                    warnings.extend(check_token_literals(interpretation))
                    warnings.extend(check_address_patterns(interpretation))
                    warnings.extend(check_coupling_phrases(interpretation))
                    warnings.extend(check_numeric_patterns(interpretation))

    # Check basis (should be label-only, no numbers)
    if "v14_guidance_basis" in record:
        basis = record["v14_guidance_basis"]
        if isinstance(basis, list):
            basis_str = " ".join(str(b) for b in basis)
            warnings.extend(check_token_literals(basis_str))
            warnings.extend(check_address_patterns(basis_str))

    # Check artifacts (should be label-only, no numbers)
    if "v14_guidance_artifacts" in record:
        artifacts = record["v14_guidance_artifacts"]
        if isinstance(artifacts, list):
            artifacts_str = " ".join(str(a) for a in artifacts)
            warnings.extend(check_token_literals(artifacts_str))
            warnings.extend(check_address_patterns(artifacts_str))

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Guidance Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean guidance record (no warnings)
    print("Test 1: Clean guidance record (no warnings)")
    clean_guidance = {
        "v14_guidance_summary": "role safe band guidance assembled for current regime label.",
        "v14_guidance_roles": {
            "VOLATILITY_ROLE": {
                "interpretation": "allocation appears within the structurally safe band for the current regime label.",
            }
        },
    }
    clean_warnings = check_guidance_record(clean_guidance)
    print(f"Clean guidance warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty guidance (prescriptive language)
    print("Test 2: Dirty guidance (prescriptive language)")
    dirty_prescriptive = {
        "v14_guidance_summary": "You should buy more volatility assets.",
    }
    dirty_warnings = check_guidance_record(dirty_prescriptive)
    print(f"Dirty guidance warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty guidance (token literals)
    print("Test 3: Dirty guidance (token literals)")
    dirty_tokens = {
        "v14_guidance_summary": "SUI and USDC allocation detected.",
    }
    dirty_warnings_tokens = check_guidance_record(dirty_tokens)
    print(f"Dirty guidance warnings: {len(dirty_warnings_tokens)}")
    if dirty_warnings_tokens:
        print("  Warnings:")
        for w in dirty_warnings_tokens:
            print(f"    - {w}")
    print()

    # Test 4: Dirty guidance (numeric patterns)
    print("Test 4: Dirty guidance (numeric patterns)")
    dirty_numeric = {
        "v14_guidance_summary": "Current allocation is 0.35 or 35% of portfolio.",
    }
    dirty_warnings_numeric = check_guidance_record(dirty_numeric)
    print(f"Dirty guidance warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 5: Dirty guidance (coupling phrases)
    print("Test 5: Dirty guidance (coupling phrases)")
    dirty_coupling = {
        "v14_guidance_summary": "Allocation is within band therefore you should proceed.",
    }
    dirty_warnings_coupling = check_guidance_record(dirty_coupling)
    print(f"Dirty guidance warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
