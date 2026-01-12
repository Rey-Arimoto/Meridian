#!/usr/bin/env python3
"""
PR136: v1.2 Rescue Strength Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on rescue strength records.
    Guards against numeric patterns, token literals, trading vocabulary,
    prescriptive language, and rescue coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No numeric patterns: No digits, %, decimals
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - NEW: No rescue coupling: No "RESCUE_STRONG therefore trade", "strong rescue means proceed"

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


# Forbidden vocabulary (evaluative/scoric/prescriptive) - reuse from existing guards
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

# Rescue coupling pattern (NEW in PR136 - enhanced from PR133)
RESCUE_COUPLING_RE = re.compile(
    r"\b(RESCUE_STRONG|RESCUE_MEDIUM|RESCUE_WEAK|RESCUE_NONE|rescue|strong|medium|weak)\b.{0,40}\b(therefore|so|thus|hence|then|means|implies)\b.{0,40}\b(act|execute|proceed|touch|trade|swap|buy|sell|sign|transfer|broadcast)\\b",
    re.IGNORECASE | re.DOTALL,
)


def check_rescue_strength_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate rescue strength record against constitutional guards.

    Args:
        record: Rescue strength record to validate

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

    # Check rescue summary
    if "v12_rescue_summary" in record:
        summary = record["v12_rescue_summary"]
        if isinstance(summary, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(summary)
            warnings.extend(token_warnings)

            # Numeric pattern guard
            numeric_warnings = check_drift_numeric_patterns(summary)
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

            # Rescue coupling guard (NEW)
            coupling_warnings = check_rescue_coupling(summary)
            warnings.extend(coupling_warnings)

    # Check rescue warnings field
    if "v12_rescue_warnings" in record:
        rescue_warnings = record["v12_rescue_warnings"]
        if isinstance(rescue_warnings, list):
            for warning in rescue_warnings:
                if isinstance(warning, str):
                    # Token literals guard
                    token_warnings = check_observation_token_literals(warning)
                    warnings.extend(token_warnings)

                    # Numeric pattern guard
                    numeric_warnings = check_drift_numeric_patterns(warning)
                    warnings.extend(numeric_warnings)

    return warnings


def check_rescue_coupling(text: str) -> List[str]:
    """
    Check for rescue coupling patterns (NEW in PR136).

    Detects:
        - "RESCUE_STRONG therefore trade"
        - "strong rescue means proceed"
        - "rescue therefore act"
        - Rescue strength coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Rescue strength + action coupling
    if RESCUE_COUPLING_RE.search(text):
        warnings.append("Rescue coupling detected (rescue strength therefore act).")

    # Pattern 2: Direct rescue strength label + action proximity
    rescue_action_patterns = [
        r'\b(RESCUE_STRONG|RESCUE_MEDIUM|RESCUE_WEAK|strong|medium|weak)\b.{0,30}\b(touch|execute|trade|swap|buy|sell|proceed|act)\\b',
        r'\b(rescue|strength)\b.{0,30}\b(therefore|so|thus|means|implies)\b.{0,30}\b(action|execute|proceed)\\b',
    ]

    for pattern in rescue_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Rescue-action proximity detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Rescue Strength Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean rescue strength record (no warnings)
    print("Test 1: Clean rescue strength record (no warnings)")
    clean_record = {
        "v12_rescue_summary": "Rescue strength RESCUE_STRONG may indicate structural pattern for REGIME_MEDIUM × STABILITY_ROLE × D1_LIQUIDATION × EDGE_SHIELD.",
    }
    clean_warnings = check_rescue_strength_record(clean_record)
    print(f"Clean record warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty rescue strength record (numeric patterns)
    print("Test 2: Dirty rescue strength record (numeric patterns)")
    dirty_numeric = {
        "v12_rescue_summary": "Rescue strength expected to yield 30% improvement.",
    }
    dirty_warnings = check_rescue_strength_record(dirty_numeric)
    print(f"Dirty record warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings[:2]:
            print(f"    - {w}")
    print()

    # Test 3: Dirty rescue strength record (rescue coupling)
    print("Test 3: Dirty rescue strength record (rescue coupling)")
    dirty_coupling = {
        "v12_rescue_summary": "Rescue strength RESCUE_STRONG therefore execute trade.",
    }
    dirty_warnings_coupling = check_rescue_strength_record(dirty_coupling)
    print(f"Dirty record warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 4: Dirty rescue strength record (strong rescue means proceed)
    print("Test 4: Dirty rescue strength record (strong rescue means proceed)")
    dirty_means = {
        "v12_rescue_summary": "Strong rescue means proceed with swap.",
    }
    dirty_warnings_means = check_rescue_strength_record(dirty_means)
    print(f"Dirty record warnings: {len(dirty_warnings_means)}")
    if dirty_warnings_means:
        print("  Warnings:")
        for w in dirty_warnings_means:
            print(f"    - {w}")
    print()

    # Test 5: Dirty rescue strength record (token literals)
    print("Test 5: Dirty rescue strength record (token literals)")
    dirty_token = {
        "v12_rescue_summary": "Rescue strength with SUI and USDC tokens.",
    }
    dirty_warnings_token = check_rescue_strength_record(dirty_token)
    print(f"Dirty record warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token[:2]:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
