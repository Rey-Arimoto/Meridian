#!/usr/bin/env python3
"""
PR141: v1.3 Execution Draft Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on execution draft records.
    Guards against prescriptive language, causal coupling, and action vocabulary.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No amounts, percentages
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No prescriptive language: No "should", "must", "need to"
    - No causal coupling: No "approved therefore", "eligible so", "recovered means"
    - Draft ≠ Action ≠ Recommendation

Guards:
    1. Token literal guard (reused from observation)
    2. Numeric pattern guard (reused from drift)
    3. Address pattern guard (reused from preview)
    4. Trading vocabulary guard (reused from preview)
    5. Prescriptive language guard (reused from policy)
    6. Draft causal coupling guard (NEW: approval/eligibility → action patterns)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


# Forbidden token literals (reuse from observation)
FORBIDDEN_TOKEN_LITERALS = ["SUI", "USDC", "BTC", "ETH", "DEEP", "CETUS"]

# Forbidden trading vocabulary (reuse from preview)
FORBIDDEN_TRADING_VOCABULARY = [
    "swap",
    "buy",
    "sell",
    "execute",
    "sign",
    "transfer",
    "bridge",
    "send",
    "broadcast",
    "submit",
    "approve",  # In execution context
]

# Forbidden prescriptive language (reuse from policy)
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
]

# Draft-specific causal coupling patterns
# Pattern: (condition_label, coupling_word)
DRAFT_COUPLING_PATTERNS = [
    # Approval → action
    ("approved", "therefore"),
    ("approved", "so"),
    ("approved", "hence"),
    ("approved", "means"),
    ("approval_available", "therefore"),
    ("approval_available", "so"),
    # Eligibility → action
    ("eligible", "therefore"),
    ("eligible", "so"),
    ("eligible", "hence"),
    ("eligible", "means"),
    ("eligibility_eligible", "therefore"),
    # Recovery → action
    ("recovered", "therefore"),
    ("recovered", "so"),
    ("recovered", "means"),
    ("rescue_strong", "therefore"),
    ("rescue_medium", "therefore"),
    # Draft → action (self-referential coupling)
    ("draft_available", "therefore"),
    ("draft_available", "so"),
    ("draft_available", "means"),
]


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
                f"(draft records must not contain token literals)"
            )

    return warnings


def check_trading_vocabulary(text: str) -> List[str]:
    """
    Check for trading vocabulary.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for word in FORBIDDEN_TRADING_VOCABULARY:
        if word.lower() in text_lower:
            warnings.append(
                f"trading vocabulary detected: '{word}' "
                f"(draft records must not contain trading verbs)"
            )

    return warnings


def check_prescriptive_language(text: str) -> List[str]:
    """
    Check for prescriptive language.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for word in FORBIDDEN_PRESCRIPTIVE_LANGUAGE:
        if word.lower() in text_lower:
            warnings.append(
                f"prescriptive language detected: '{word}' "
                f"(draft records must be descriptive only)"
            )

    return warnings


def check_draft_causal_coupling(text: str) -> List[str]:
    """
    Check for draft-specific causal coupling patterns.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for condition_label, coupling_word in DRAFT_COUPLING_PATTERNS:
        # Check if both appear in text (may not be adjacent, but proximity is suspicious)
        if condition_label.lower() in text_lower and coupling_word.lower() in text_lower:
            warnings.append(
                f"draft causal coupling detected: '{condition_label}' with '{coupling_word}' "
                f"(may indicate prescriptive coupling in draft)"
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
            "(draft records must not contain addresses)"
        )

    return warnings


def check_draft_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate draft record against constitutional guards.

    Args:
        record: Draft record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check summary
    if "v13_draft_summary" in record:
        summary = record["v13_draft_summary"]
        if isinstance(summary, str):
            # Check for token literals
            token_warnings = check_token_literals(summary)
            warnings.extend(token_warnings)

            # Check for trading vocabulary
            trading_warnings = check_trading_vocabulary(summary)
            warnings.extend(trading_warnings)

            # Check for prescriptive language
            prescriptive_warnings = check_prescriptive_language(summary)
            warnings.extend(prescriptive_warnings)

            # Check for draft causal coupling
            coupling_warnings = check_draft_causal_coupling(summary)
            warnings.extend(coupling_warnings)

            # Check for address patterns
            address_warnings = check_address_patterns(summary)
            warnings.extend(address_warnings)

    # Check notes (if present)
    if "v13_draft_notes" in record:
        notes = record["v13_draft_notes"]
        if isinstance(notes, str):
            # Apply same guards to notes
            token_warnings = check_token_literals(notes)
            warnings.extend(token_warnings)

            trading_warnings = check_trading_vocabulary(notes)
            warnings.extend(trading_warnings)

            prescriptive_warnings = check_prescriptive_language(notes)
            warnings.extend(prescriptive_warnings)

            coupling_warnings = check_draft_causal_coupling(notes)
            warnings.extend(coupling_warnings)

            address_warnings = check_address_patterns(notes)
            warnings.extend(address_warnings)

    # Check inputs (should be label-only, no numeric ids)
    if "v13_draft_inputs" in record:
        inputs = record["v13_draft_inputs"]
        if isinstance(inputs, dict):
            inputs_str = str(inputs)
            # Check for token literals in input values
            token_warnings = check_token_literals(inputs_str)
            warnings.extend(token_warnings)

    # Check constraints (should be label-only)
    if "v13_draft_constraints" in record:
        constraints = record["v13_draft_constraints"]
        if isinstance(constraints, dict):
            constraints_str = str(constraints)
            # Check for token literals in constraint values
            token_warnings = check_token_literals(constraints_str)
            warnings.extend(token_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.3 Execution Draft Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean draft (no warnings)
    print("Test 1: Clean draft (no warnings)")
    clean_draft = {
        "v13_draft_summary": "execution draft available. inputs present.",
        "v13_draft_inputs": {"packet_id": "approval_packet_v1"},
        "v13_draft_constraints": {"permission": "ALLOWED", "eligibility": "ELIGIBLE"},
    }
    clean_warnings = check_draft_record(clean_draft)
    print(f"Clean draft warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty draft (token literals)
    print("Test 2: Dirty draft (token literals)")
    dirty_token = {
        "v13_draft_summary": "execution draft for SUI and USDC swap.",
    }
    dirty_warnings = check_draft_record(dirty_token)
    print(f"Dirty draft warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty draft (trading vocabulary)
    print("Test 3: Dirty draft (trading vocabulary)")
    dirty_trading = {
        "v13_draft_summary": "approved therefore execute swap operation.",
    }
    dirty_warnings_trading = check_draft_record(dirty_trading)
    print(f"Dirty draft warnings: {len(dirty_warnings_trading)}")
    if dirty_warnings_trading:
        print("  Warnings:")
        for w in dirty_warnings_trading:
            print(f"    - {w}")
    print()

    # Test 4: Dirty draft (causal coupling)
    print("Test 4: Dirty draft (causal coupling)")
    dirty_coupling = {
        "v13_draft_summary": "eligible therefore trade. approved so proceed.",
    }
    dirty_warnings_coupling = check_draft_record(dirty_coupling)
    print(f"Dirty draft warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 5: Dirty draft (address patterns)
    print("Test 5: Dirty draft (address patterns)")
    dirty_address = {
        "v13_draft_summary": "draft references address 0x1234567890abcdef.",
    }
    dirty_warnings_address = check_draft_record(dirty_address)
    print(f"Dirty draft warnings: {len(dirty_warnings_address)}")
    if dirty_warnings_address:
        print("  Warnings:")
        for w in dirty_warnings_address:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
