#!/usr/bin/env python3
"""
PR130: v1.2 Role Carrier Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on role carrier qualification records.
    Guards against trading vocabulary, token literals, numeric patterns,
    prescriptive language, and role coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No counts, percentages, scores
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - No role coupling: No "QUALIFIED therefore act", "DISQUALIFIED so avoid"

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
NUMERIC_RE = re.compile(r"(?<![A-Za-z])\d+(\.\d+)?(?![A-Za-z])")

# Role coupling pattern
ROLE_COUPLING_RE = re.compile(
    r"\b(QUALIFIED|PARTIALLY_QUALIFIED|DISQUALIFIED|qualification)\b.{0,40}\b(therefore|so|thus|hence|then|means)\b.{0,40}\b(act|execute|proceed|touch|trade|swap|buy|sell|avoid|skip)\b",
    re.IGNORECASE | re.DOTALL,
)


def check_role_carrier_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate role carrier qualification record against constitutional guards.

    Args:
        record: Role carrier qualification record to validate

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

    # Check qualification summary
    if "v12_role_carrier_summary" in record:
        summary = record["v12_role_carrier_summary"]
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

            # Role coupling guard (NEW)
            coupling_warnings = check_role_coupling(summary)
            warnings.extend(coupling_warnings)

    # Check asset profile summary if present
    if "v12_role_carrier_asset_profile_summary" in record:
        asset_summary = record["v12_role_carrier_asset_profile_summary"]
        if isinstance(asset_summary, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(asset_summary)
            warnings.extend(token_warnings)

            # Numeric pattern guard
            numeric_warnings = check_drift_numeric_patterns(asset_summary)
            warnings.extend(numeric_warnings)

    return warnings


def check_role_coupling(text: str) -> List[str]:
    """
    Check for role coupling patterns (NEW in PR130).

    Detects:
        - "QUALIFIED therefore act"
        - "DISQUALIFIED so avoid"
        - "qualification means trade"
        - Qualification status coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Qualification status + action coupling
    if ROLE_COUPLING_RE.search(text):
        warnings.append("Role coupling detected (qualification therefore act).")

    # Pattern 2: Direct qualification status + action proximity
    role_action_patterns = [
        r'\b(QUALIFIED|DISQUALIFIED|PARTIALLY_QUALIFIED)\b.{0,30}\b(touch|execute|trade|swap|buy|sell|proceed|avoid)\b',
        r'\b(qualification|qualified|disqualified)\b.{0,30}\b(therefore|so|thus|means)\b.{0,30}\b(action|execute|proceed)\b',
    ]

    for pattern in role_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Role-action proximity detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Role Carrier Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean qualification (no warnings)
    print("Test 1: Clean qualification (no warnings)")
    clean_record = {
        "v12_role_carrier_summary": "asset labeled QUALIFIED for GAS_ROLE (all axes meet requirements).",
    }
    clean_warnings = check_role_carrier_record(clean_record)
    print(f"Clean record warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty qualification (token literals)
    print("Test 2: Dirty qualification (token literals)")
    dirty_token = {
        "v12_role_carrier_summary": "asset SUI is QUALIFIED for GAS_ROLE.",
    }
    dirty_warnings = check_role_carrier_record(dirty_token)
    print(f"Dirty record warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings[:3]:
            print(f"    - {w}")
    print()

    # Test 3: Dirty qualification (numeric patterns)
    print("Test 3: Dirty qualification (numeric patterns)")
    dirty_numeric = {
        "v12_role_carrier_summary": "asset scores 85% qualification for GAS_ROLE.",
    }
    dirty_warnings_numeric = check_role_carrier_record(dirty_numeric)
    print(f"Dirty record warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 4: Dirty qualification (role coupling)
    print("Test 4: Dirty qualification (role coupling)")
    dirty_coupling = {
        "v12_role_carrier_summary": "asset QUALIFIED therefore execute trade.",
    }
    dirty_warnings_coupling = check_role_carrier_record(dirty_coupling)
    print(f"Dirty record warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 5: Dirty qualification (DISQUALIFIED so avoid)
    print("Test 5: Dirty qualification (DISQUALIFIED so avoid)")
    dirty_disqualified = {
        "v12_role_carrier_summary": "asset DISQUALIFIED so avoid trading.",
    }
    dirty_warnings_disq = check_role_carrier_record(dirty_disqualified)
    print(f"Dirty record warnings: {len(dirty_warnings_disq)}")
    if dirty_warnings_disq:
        print("  Warnings:")
        for w in dirty_warnings_disq:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
