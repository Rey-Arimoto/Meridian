#!/usr/bin/env python3
"""
PR131: v1.2 Contribution Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on contribution records.
    Guards against numeric patterns, token literals, return guarantee language,
    prescriptive language, and contribution coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No numeric patterns: No digits, %, decimals, ratios, time periods
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - No return guarantee language: No "guaranteed", "assured", "risk-free", "annual return"
    - No backtest/prediction language: No "backtest", "predicted", "expected return"
    - No contribution coupling: No "++ therefore trade", "-- therefore stop"

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


# Forbidden vocabulary (evaluative/scoric/prescriptive)
FORBIDDEN_VOCABULARY = [
    # Evaluative
    "good", "bad", "better", "worse", "best", "worst",
    "correct", "incorrect", "right", "wrong",
    "optimal", "suboptimal", "ideal", "poor",
    # Scoric
    "score", "grade", "rating", "rank",
    # Prescriptive
    "should", "must", "need to", "have to",
    "recommend", "suggest", "advise",
    # Imperative
    "do", "don't", "perform", "execute",
    "go ahead", "proceed", "continue", "stop",
]

# Return guarantee vocabulary
GUARANTEE_VOCABULARY = [
    "guaranteed", "assured", "risk-free", "stable yield",
    "annual return", "expected return", "assured return",
    "backtest", "predicted", "forecasted", "projected",
    "optimization", "maximize", "minimize",
]

# Token literals
TOKEN_LITERALS = {"SUI", "USDC", "BTC", "ETH", "SOL", "AVAX", "MATIC", "DEEP", "CETUS"}

# Regex patterns
ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{6,}\b")
# Numeric pattern: any digit sequence, percentage, decimal, ratio
NUMERIC_RE = re.compile(r"(?<![A-Za-z_])\d+(\.\d+)?(?![A-Za-z_])|%|\d+x|\d+:\d+")

# Contribution coupling pattern
CONTRIBUTION_COUPLING_RE = re.compile(
    r"\b(CONTRIB_STRONGLY_POSITIVE|CONTRIB_POSITIVE|CONTRIB_NEGATIVE|CONTRIB_STRONGLY_NEGATIVE|strongly.positive|positive|negative|strongly.negative|\+\+|\+|--|-)\b.{0,40}\b(therefore|so|thus|hence|then|means)\b.{0,40}\b(act|execute|proceed|touch|trade|swap|buy|sell|stop|avoid|pause)\b",
    re.IGNORECASE | re.DOTALL,
)


def check_contribution_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate contribution record against constitutional guards.

    Args:
        record: Contribution record to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import existing guards
    from observation.v10_observation_constitutional_guard import (
        check_observation_token_literals,
    )
    from drift.v10_drift_constitutional_guard import (
        check_drift_numeric_patterns,
    )
    from preview.v11_preview_constitutional_guard import (
        check_trading_vocabulary,
        check_execution_operations,
        check_address_patterns,
    )
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )
    from policy.v10_drift_policy_constitutional_guard import (
        check_prescriptive_language,
    )

    warnings = []

    # Check contribution summary
    if "v12_contrib_summary" in record:
        summary = record["v12_contrib_summary"]
        if isinstance(summary, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(summary)
            warnings.extend(token_warnings)

            # Numeric pattern guard (CRITICAL for contribution model)
            numeric_warnings = check_contribution_numeric_patterns(summary)
            warnings.extend(numeric_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(summary)
            warnings.extend(trading_warnings)

            # Execution operation guard
            execution_warnings = check_execution_operations(summary)
            warnings.extend(execution_warnings)

            # Address pattern guard
            address_warnings = check_address_patterns(summary)
            warnings.extend(address_warnings)

            # Forbidden vocabulary guard
            vocab_warnings = check_forbidden_vocabulary(summary)
            warnings.extend(vocab_warnings)

            # Prescriptive language guard
            prescriptive_warnings = check_prescriptive_language(summary)
            warnings.extend(prescriptive_warnings)

            # Guarantee language guard (NEW)
            guarantee_warnings = check_guarantee_language(summary)
            warnings.extend(guarantee_warnings)

            # Contribution coupling guard (NEW)
            coupling_warnings = check_contribution_coupling(summary)
            warnings.extend(coupling_warnings)

    # Check contribution rationale
    if "v12_contrib_contribution_rationale" in record:
        rationale_list = record["v12_contrib_contribution_rationale"]
        if isinstance(rationale_list, list):
            for rationale_item in rationale_list:
                if isinstance(rationale_item, str):
                    # Token literals guard
                    token_warnings = check_observation_token_literals(rationale_item)
                    warnings.extend(token_warnings)

                    # Numeric pattern guard
                    numeric_warnings = check_contribution_numeric_patterns(rationale_item)
                    warnings.extend(numeric_warnings)

                    # Guarantee language guard
                    guarantee_warnings = check_guarantee_language(rationale_item)
                    warnings.extend(guarantee_warnings)

    return warnings


def check_contribution_numeric_patterns(text: str) -> List[str]:
    """
    Check for numeric patterns (CRITICAL for contribution model).

    Detects:
        - Digits (any digit sequence)
        - Percentages (%)
        - Decimals (e.g., "0.5", "1.2")
        - Ratios (e.g., "1:2", "3x")
        - Time periods (years, months, days with numbers)

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Any numeric pattern
    if NUMERIC_RE.search(text):
        warnings.append("Numeric pattern detected (digits/percentages/decimals prohibited in contribution model).")

    # Pattern 2: Time period patterns
    time_patterns = [
        r'\b\d+\s*(year|years|month|months|day|days|hour|hours|minute|minutes)\b',
        r'\bannual\s+return\b',
        r'\bper\s+year\b',
        r'\bYoY\b',
        r'\bMoM\b',
    ]

    for pattern in time_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Time period pattern detected: '{pattern}' in text")

    return warnings


def check_guarantee_language(text: str) -> List[str]:
    """
    Check for return guarantee language (NEW in PR131).

    Detects:
        - "guaranteed", "assured", "risk-free"
        - "annual return", "expected return"
        - "backtest", "predicted", "forecasted"
        - "optimization", "maximize", "minimize"

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    text_lower = text.lower()

    for vocab in GUARANTEE_VOCABULARY:
        if vocab in text_lower:
            warnings.append(f"Guarantee language detected: '{vocab}' (prohibited in contribution model).")

    return warnings


def check_contribution_coupling(text: str) -> List[str]:
    """
    Check for contribution coupling patterns (NEW in PR131).

    Detects:
        - "++ therefore trade"
        - "strongly positive so execute"
        - "negative therefore stop"
        - Contribution label coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Contribution label + action coupling
    if CONTRIBUTION_COUPLING_RE.search(text):
        warnings.append("Contribution coupling detected (contribution label therefore act).")

    # Pattern 2: Direct contribution status + action proximity
    contrib_action_patterns = [
        r'\b(positive|negative|neutral)\b.{0,30}\b(touch|execute|trade|swap|buy|sell|proceed|avoid|stop)\b',
        r'\b(contribution|contrib)\b.{0,30}\b(therefore|so|thus|means)\b.{0,30}\b(action|execute|proceed)\b',
    ]

    for pattern in contrib_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Contribution-action proximity detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Contribution Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean contribution (no warnings)
    print("Test 1: Clean contribution (no warnings)")
    clean_record = {
        "v12_contrib_summary": "contribution labeled CONTRIB_STRONGLY_POSITIVE for REGIME_MEDIUM × VOLATILITY_ROLE × D1_LIQUIDATION.",
        "v12_contrib_contribution_rationale": ["DISTORTION_CAPTURE_ZONE", "STRUCTURE_INTELLIGIBLE"],
    }
    clean_warnings = check_contribution_record(clean_record)
    print(f"Clean record warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty contribution (numeric patterns)
    print("Test 2: Dirty contribution (numeric patterns)")
    dirty_numeric = {
        "v12_contrib_summary": "contribution expected to yield 30% annual return.",
    }
    dirty_warnings = check_contribution_record(dirty_numeric)
    print(f"Dirty record warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings[:3]:
            print(f"    - {w}")
    print()

    # Test 3: Dirty contribution (guarantee language)
    print("Test 3: Dirty contribution (guarantee language)")
    dirty_guarantee = {
        "v12_contrib_summary": "contribution guaranteed to maximize returns with risk-free backtest.",
    }
    dirty_warnings_guarantee = check_contribution_record(dirty_guarantee)
    print(f"Dirty record warnings: {len(dirty_warnings_guarantee)}")
    if dirty_warnings_guarantee:
        print("  Warnings:")
        for w in dirty_warnings_guarantee:
            print(f"    - {w}")
    print()

    # Test 4: Dirty contribution (contribution coupling)
    print("Test 4: Dirty contribution (contribution coupling)")
    dirty_coupling = {
        "v12_contrib_summary": "contribution strongly positive therefore execute trade.",
    }
    dirty_warnings_coupling = check_contribution_record(dirty_coupling)
    print(f"Dirty record warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 5: Dirty contribution (token literals in rationale)
    print("Test 5: Dirty contribution (token literals in rationale)")
    dirty_token = {
        "v12_contrib_summary": "contribution labeled positive.",
        "v12_contrib_contribution_rationale": ["SUI_PREMIUM_ZONE", "USDC_STABILITY"],
    }
    dirty_warnings_token = check_contribution_record(dirty_token)
    print(f"Dirty record warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token[:2]:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
