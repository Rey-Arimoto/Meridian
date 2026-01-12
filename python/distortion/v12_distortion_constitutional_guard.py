#!/usr/bin/env python3
"""
PR129: v1.2 Distortion Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on distortion records.
    Guards against trading vocabulary, token literals, numeric patterns,
    prescriptive language, and distortion coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No counts, percentages, scores
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - No distortion coupling: No "D1 therefore act", "D4 so execute"

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

# Token literals
TOKEN_LITERALS = {"SUI", "USDC", "BTC", "ETH", "SOL", "AVAX", "MATIC"}

# Regex patterns
ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{6,}\b")
NUMERIC_RE = re.compile(r"(?<![A-Za-z])\d+(\.\d+)?(?![A-Za-z])")

# Distortion coupling pattern
DISTORTION_COUPLING_RE = re.compile(
    r"\b(D0|D1|D2|D3|D4|D5|distortion)\b.{0,40}\b(therefore|so|thus|hence|then|means)\b.{0,40}\b(act|execute|proceed|touch|trade|swap|buy|sell)\b",
    re.IGNORECASE | re.DOTALL,
)


def check_distortion_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate distortion record against constitutional guards.

    Args:
        record: Distortion record to validate

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

    # Check distortion summary
    if "v12_distortion_summary" in record:
        summary = record["v12_distortion_summary"]
        if isinstance(summary, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(summary)
            warnings.extend(token_warnings)

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

            # Numeric pattern guard
            numeric_warnings = check_drift_numeric_patterns(summary)
            warnings.extend(numeric_warnings)

            # Prescriptive language guard
            prescriptive_warnings = check_prescriptive_language(summary)
            warnings.extend(prescriptive_warnings)

            # Distortion coupling guard (NEW)
            coupling_warnings = check_distortion_coupling(summary)
            warnings.extend(coupling_warnings)

    return warnings


def check_distortion_coupling(text: str) -> List[str]:
    """
    Check for distortion coupling patterns (NEW in PR129).

    Detects:
        - "D1 therefore act"
        - "D4 so execute"
        - "distortion means trade"
        - Distortion label coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Distortion label + action coupling
    if DISTORTION_COUPLING_RE.search(text):
        warnings.append("Distortion coupling detected (distortion therefore act).")

    # Pattern 2: Direct distortion type + action proximity
    distortion_action_patterns = [
        r'\b(D[0-5])\b.{0,30}\b(touch|execute|trade|swap|buy|sell|proceed)\b',
        r'\b(liquidation|hollowing|stickiness|event|correlation)\b.{0,30}\b(therefore|so|thus|means)\b.{0,30}\b(action|execute|proceed)\b',
    ]

    for pattern in distortion_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Distortion-action proximity detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Distortion Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean distortion (no warnings)
    print("Test 1: Clean distortion (no warnings)")
    clean_distortion = {
        "v12_distortion_summary": "distortion label classified as D4_EVENT_DISTORTION based on labeled activity patterns.",
    }
    clean_warnings = check_distortion_record(clean_distortion)
    print(f"Clean distortion warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty distortion (token literals)
    print("Test 2: Dirty distortion (token literals)")
    dirty_token = {
        "v12_distortion_summary": "distortion detected for SUI and USDC.",
    }
    dirty_warnings = check_distortion_record(dirty_token)
    print(f"Dirty distortion warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings[:3]:
            print(f"    - {w}")
    print()

    # Test 3: Dirty distortion (numeric patterns)
    print("Test 3: Dirty distortion (numeric patterns)")
    dirty_numeric = {
        "v12_distortion_summary": "detected 5 distortion events with 80% confidence.",
    }
    dirty_warnings_numeric = check_distortion_record(dirty_numeric)
    print(f"Dirty distortion warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 4: Dirty distortion (distortion coupling)
    print("Test 4: Dirty distortion (distortion coupling)")
    dirty_coupling = {
        "v12_distortion_summary": "D1 distortion detected therefore execute liquidation trade.",
    }
    dirty_warnings_coupling = check_distortion_record(dirty_coupling)
    print(f"Dirty distortion warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 5: Dirty distortion (D4 so execute)
    print("Test 5: Dirty distortion (D4 so execute)")
    dirty_d4 = {
        "v12_distortion_summary": "D4 event distortion so proceed with execution.",
    }
    dirty_warnings_d4 = check_distortion_record(dirty_d4)
    print(f"Dirty distortion warnings: {len(dirty_warnings_d4)}")
    if dirty_warnings_d4:
        print("  Warnings:")
        for w in dirty_warnings_d4:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
