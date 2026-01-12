#!/usr/bin/env python3
"""
PR132: v1.2 Contribution Binding Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on contribution constraint binding records.
    Guards against numeric patterns, token literals, trading vocabulary,
    prescriptive language, and contribution zone coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No numeric patterns: No digits, %, decimals
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - No contribution zone coupling: No "primary therefore trade", "blocked so stop"

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
TOKEN_LITERALS = {"SUI", "USDC", "BTC", "ETH", "SOL", "AVAX", "MATIC", "DEEP", "CETUS"}

# Regex patterns
ADDRESS_RE = re.compile(r"\b0x[a-fA-F0-9]{6,}\b")
NUMERIC_RE = re.compile(r"(?<![A-Za-z_])\d+(\.\d+)?(?![A-Za-z_])|%")

# Contribution zone coupling pattern
CONTRIBUTION_ZONE_COUPLING_RE = re.compile(
    r"\b(primary|secondary|blocked|none|CONTRIB_ZONE_PRIMARY|CONTRIB_ZONE_SECONDARY|CONTRIB_ZONE_BLOCKED)\b.{0,40}\b(therefore|so|thus|hence|then|means)\b.{0,40}\b(act|execute|proceed|touch|trade|swap|buy|sell|stop|avoid|pause)\b",
    re.IGNORECASE | re.DOTALL,
)


def check_contribution_binding_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate contribution binding record against constitutional guards.

    Args:
        record: Contribution binding record to validate

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

    # Check constraint summary
    if "v12_contrib_constraint_summary" in record:
        summary = record["v12_contrib_constraint_summary"]
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

            # Contribution zone coupling guard (NEW)
            coupling_warnings = check_contribution_zone_coupling(summary)
            warnings.extend(coupling_warnings)

    # Check constraint labels
    if "v12_contrib_constraint_labels" in record:
        labels = record["v12_contrib_constraint_labels"]
        if isinstance(labels, list):
            for label in labels:
                if isinstance(label, str):
                    # Token literals guard
                    token_warnings = check_observation_token_literals(label)
                    warnings.extend(token_warnings)

                    # Numeric pattern guard
                    numeric_warnings = check_drift_numeric_patterns(label)
                    warnings.extend(numeric_warnings)

    return warnings


def check_contribution_zone_coupling(text: str) -> List[str]:
    """
    Check for contribution zone coupling patterns (NEW in PR132).

    Detects:
        - "primary therefore trade"
        - "blocked so stop"
        - "zone primary means proceed"
        - Contribution zone coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Contribution zone + action coupling
    if CONTRIBUTION_ZONE_COUPLING_RE.search(text):
        warnings.append("Contribution zone coupling detected (zone therefore act).")

    # Pattern 2: Direct zone status + action proximity
    zone_action_patterns = [
        r'\b(primary|secondary|blocked)\b.{0,30}\b(touch|execute|trade|swap|buy|sell|proceed|avoid|stop)\b',
        r'\b(zone|constraint)\b.{0,30}\b(therefore|so|thus|means)\b.{0,30}\b(action|execute|proceed)\b',
    ]

    for pattern in zone_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Zone-action proximity detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Contribution Binding Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean binding (no warnings)
    print("Test 1: Clean binding (no warnings)")
    clean_record = {
        "v12_contrib_constraint_summary": "contribution zone labeled CONTRIB_ZONE_PRIMARY with constraints: contrib_primary_medium_volatility_distortion.",
        "v12_contrib_constraint_labels": ["contrib_primary_medium_volatility_distortion"],
    }
    clean_warnings = check_contribution_binding_record(clean_record)
    print(f"Clean record warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty binding (numeric patterns)
    print("Test 2: Dirty binding (numeric patterns)")
    dirty_numeric = {
        "v12_contrib_constraint_summary": "contribution zone expected to yield 30% return in primary zone.",
    }
    dirty_warnings = check_contribution_binding_record(dirty_numeric)
    print(f"Dirty record warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings[:2]:
            print(f"    - {w}")
    print()

    # Test 3: Dirty binding (zone coupling)
    print("Test 3: Dirty binding (zone coupling)")
    dirty_coupling = {
        "v12_contrib_constraint_summary": "contribution zone primary therefore execute trade.",
    }
    dirty_warnings_coupling = check_contribution_binding_record(dirty_coupling)
    print(f"Dirty record warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 4: Dirty binding (blocked so stop)
    print("Test 4: Dirty binding (blocked so stop)")
    dirty_blocked = {
        "v12_contrib_constraint_summary": "contribution zone blocked so stop trading.",
    }
    dirty_warnings_blocked = check_contribution_binding_record(dirty_blocked)
    print(f"Dirty record warnings: {len(dirty_warnings_blocked)}")
    if dirty_warnings_blocked:
        print("  Warnings:")
        for w in dirty_warnings_blocked:
            print(f"    - {w}")
    print()

    # Test 5: Dirty binding (token literals in labels)
    print("Test 5: Dirty binding (token literals in labels)")
    dirty_token = {
        "v12_contrib_constraint_summary": "contribution zone labeled primary.",
        "v12_contrib_constraint_labels": ["contrib_SUI_primary", "contrib_USDC_secondary"],
    }
    dirty_warnings_token = check_contribution_binding_record(dirty_token)
    print(f"Dirty record warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token[:2]:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
