#!/usr/bin/env python3
"""
PR135: v1.2 Edge Type Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on edge type records.
    Guards against numeric patterns, token literals, trading vocabulary,
    prescriptive language, and edge coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No numeric patterns: No digits, %, decimals
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - NEW: No edge coupling: No "EDGE_AMPLIFY therefore trade", "EDGE_SHIELD so stop"

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

# Edge coupling pattern (NEW in PR135)
EDGE_COUPLING_RE = re.compile(
    r"\b(EDGE_AMPLIFY|EDGE_SHIELD|EDGE_LEAK|EDGE_NEUTRAL|EDGE_NONE|edge|amplify|shield|leak|neutral)\b.{0,40}\b(therefore|so|thus|hence|then|means|implies)\b.{0,40}\b(act|execute|proceed|touch|trade|swap|buy|sell|sign|transfer|broadcast|stop|avoid|pause)\\b",
    re.IGNORECASE | re.DOTALL,
)


def check_edge_type_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate edge type record against constitutional guards.

    Args:
        record: Edge type record to validate

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

    # Check edge summary
    if "v12_edge_summary" in record:
        summary = record["v12_edge_summary"]
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

            # Edge coupling guard (NEW)
            coupling_warnings = check_edge_coupling(summary)
            warnings.extend(coupling_warnings)

    # Check edge warnings field
    if "v12_edge_warnings" in record:
        edge_warnings = record["v12_edge_warnings"]
        if isinstance(edge_warnings, list):
            for warning in edge_warnings:
                if isinstance(warning, str):
                    # Token literals guard
                    token_warnings = check_observation_token_literals(warning)
                    warnings.extend(token_warnings)

                    # Numeric pattern guard
                    numeric_warnings = check_drift_numeric_patterns(warning)
                    warnings.extend(numeric_warnings)

    return warnings


def check_edge_coupling(text: str) -> List[str]:
    """
    Check for edge coupling patterns (NEW in PR135).

    Detects:
        - "EDGE_AMPLIFY therefore trade"
        - "EDGE_SHIELD so stop"
        - "amplify means execute"
        - Edge type coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Edge + action coupling
    if EDGE_COUPLING_RE.search(text):
        warnings.append("Edge coupling detected (edge therefore act).")

    # Pattern 2: Direct edge label + action proximity
    edge_action_patterns = [
        r'\b(EDGE_AMPLIFY|EDGE_SHIELD|EDGE_LEAK|EDGE_NEUTRAL)\b.{0,30}\b(touch|execute|trade|swap|buy|sell|proceed|act|stop|avoid)\\b',
        r'\b(edge|amplify|shield|leak)\b.{0,30}\b(therefore|so|thus|means|implies)\b.{0,30}\b(action|execute|proceed|stop)\\b',
    ]

    for pattern in edge_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Edge-action proximity detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Edge Type Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean edge record (no warnings)
    print("Test 1: Clean edge record (no warnings)")
    clean_record = {
        "v12_edge_summary": "Edge type EDGE_AMPLIFY may indicate structural pattern for REGIME_MEDIUM × VOLATILITY_ROLE × D1_LIQUIDATION.",
    }
    clean_warnings = check_edge_type_record(clean_record)
    print(f"Clean record warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty edge record (numeric patterns)
    print("Test 2: Dirty edge record (numeric patterns)")
    dirty_numeric = {
        "v12_edge_summary": "Edge type expected to yield 30% improvement.",
    }
    dirty_warnings = check_edge_type_record(dirty_numeric)
    print(f"Dirty record warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings[:2]:
            print(f"    - {w}")
    print()

    # Test 3: Dirty edge record (edge coupling)
    print("Test 3: Dirty edge record (edge coupling)")
    dirty_coupling = {
        "v12_edge_summary": "Edge type EDGE_AMPLIFY therefore execute trade.",
    }
    dirty_warnings_coupling = check_edge_type_record(dirty_coupling)
    print(f"Dirty record warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 4: Dirty edge record (EDGE_SHIELD so stop)
    print("Test 4: Dirty edge record (EDGE_SHIELD so stop)")
    dirty_shield = {
        "v12_edge_summary": "Edge type EDGE_SHIELD so stop trading.",
    }
    dirty_warnings_shield = check_edge_type_record(dirty_shield)
    print(f"Dirty record warnings: {len(dirty_warnings_shield)}")
    if dirty_warnings_shield:
        print("  Warnings:")
        for w in dirty_warnings_shield:
            print(f"    - {w}")
    print()

    # Test 5: Dirty edge record (token literals)
    print("Test 5: Dirty edge record (token literals)")
    dirty_token = {
        "v12_edge_summary": "Edge type with SUI and USDC tokens.",
    }
    dirty_warnings_token = check_edge_type_record(dirty_token)
    print(f"Dirty record warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token[:2]:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
