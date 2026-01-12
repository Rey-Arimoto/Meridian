#!/usr/bin/env python3
"""
PR133: v1.2 Rescue Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on rescue relation records.
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
    - NEW: No rescue coupling: No "rescue therefore act", "救えるので触ってよい"

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

# Rescue coupling pattern (NEW in PR133)
RESCUE_COUPLING_RE = re.compile(
    r"\b(rescue|rescued|rescuer|buffer|anchor|dampen|continuity|escape|BUFFER|ANCHOR|DAMPEN|CONTINUITY|ESCAPE)\b.{0,40}\b(therefore|so|thus|hence|then|means|implies)\b.{0,40}\b(act|execute|proceed|touch|trade|swap|buy|sell|sign|transfer|broadcast)\\b",
    re.IGNORECASE | re.DOTALL,
)

# Japanese rescue coupling patterns
RESCUE_COUPLING_JP_RE = re.compile(
    r"(救|バッファ|アンカー|ダンプ).{0,20}(ので|から|ため).{0,20}(触|実行|取引|スワップ)",
    re.IGNORECASE,
)


def check_rescue_relation_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate rescue relation record against constitutional guards.

    Args:
        record: Rescue relation record to validate

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
    Check for rescue coupling patterns (NEW in PR133).

    Detects:
        - "rescue therefore act"
        - "buffer so trade"
        - "dampen means proceed"
        - "救えるので触ってよい"
        - Rescue edge type coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Rescue + action coupling (English)
    if RESCUE_COUPLING_RE.search(text):
        warnings.append("Rescue coupling detected (rescue therefore act).")

    # Pattern 2: Japanese rescue coupling
    if RESCUE_COUPLING_JP_RE.search(text):
        warnings.append("Rescue coupling detected (Japanese: 救えるので触ってよい).")

    # Pattern 3: Direct rescue term + action proximity
    rescue_action_patterns = [
        r'\b(rescue|buffer|anchor|dampen|continuity|escape)\b.{0,30}\b(touch|execute|trade|swap|buy|sell|proceed|act)\\b',
        r'\b(edge|relation)\b.{0,30}\b(therefore|so|thus|means)\b.{0,30}\b(action|execute|proceed)\\b',
    ]

    for pattern in rescue_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Rescue-action proximity detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Rescue Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean rescue record (no warnings)
    print("Test 1: Clean rescue record (no warnings)")
    clean_record = {
        "v12_rescue_summary": "Role rescue relation from STABILITY_ROLE to VOLATILITY_ROLE may provide edge type BUFFER with strength MODERATE.",
        "v12_rescue_edge_type": "BUFFER",
    }
    clean_warnings = check_rescue_relation_record(clean_record)
    print(f"Clean record warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty rescue record (numeric patterns)
    print("Test 2: Dirty rescue record (numeric patterns)")
    dirty_numeric = {
        "v12_rescue_summary": "Role rescue relation expected to yield 30% improvement in stability.",
    }
    dirty_warnings = check_rescue_relation_record(dirty_numeric)
    print(f"Dirty record warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings[:2]:
            print(f"    - {w}")
    print()

    # Test 3: Dirty rescue record (rescue coupling)
    print("Test 3: Dirty rescue record (rescue coupling)")
    dirty_coupling = {
        "v12_rescue_summary": "Role rescue relation buffer therefore execute trade.",
    }
    dirty_warnings_coupling = check_rescue_relation_record(dirty_coupling)
    print(f"Dirty record warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 4: Dirty rescue record (rescued so proceed)
    print("Test 4: Dirty rescue record (rescued so proceed)")
    dirty_rescued = {
        "v12_rescue_summary": "Role rescued by buffer so proceed with swap.",
    }
    dirty_warnings_rescued = check_rescue_relation_record(dirty_rescued)
    print(f"Dirty record warnings: {len(dirty_warnings_rescued)}")
    if dirty_warnings_rescued:
        print("  Warnings:")
        for w in dirty_warnings_rescued:
            print(f"    - {w}")
    print()

    # Test 5: Dirty rescue record (token literals)
    print("Test 5: Dirty rescue record (token literals)")
    dirty_token = {
        "v12_rescue_summary": "Role rescue relation with SUI and USDC tokens.",
    }
    dirty_warnings_token = check_rescue_relation_record(dirty_token)
    print(f"Dirty record warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token[:2]:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
