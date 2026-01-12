#!/usr/bin/env python3
"""
PR134: v1.2 Distortion Subtype Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on distortion subtype records.
    Guards against numeric patterns, token literals, trading vocabulary,
    prescriptive language, and subtype coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No numeric patterns: No digits, %, decimals
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - NEW: No subtype coupling: No "D1B therefore act", "subtype implies trade"

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

# Subtype coupling pattern (NEW in PR134)
SUBTYPE_COUPLING_RE = re.compile(
    r"\b(D1A|D1B|D1C|D2A|D2B|D2C|D3A|D3B|D3C|D4A|D4B|D4C|D5A|D5B|D5C|subtype|SUBTYPE|CASCADE|FORCED_FLOW|STRESS_UNWIND|MEAN_REVERT|PINNING|BREAKOUT|TOP_GAP|DEPTH_EVAPORATION|SPREAD_SHOCK|EVENT_SPIKE|AFTERSHOCK|EVENT_SILENCE|COUPLING_TIGHTEN|DECOUPLING|ROTATION)\b.{0,40}\b(therefore|so|thus|hence|then|means|implies)\b.{0,40}\b(act|execute|proceed|touch|trade|swap|buy|sell|sign|transfer|broadcast)\\b",
    re.IGNORECASE | re.DOTALL,
)


def check_distortion_subtype_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate distortion subtype record against constitutional guards.

    Args:
        record: Distortion subtype record to validate

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

    # Check subtype summary
    if "v12_subtype_summary" in record:
        summary = record["v12_subtype_summary"]
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

            # Subtype coupling guard (NEW)
            coupling_warnings = check_subtype_coupling(summary)
            warnings.extend(coupling_warnings)

    # Check subtype warnings field
    if "v12_subtype_warnings" in record:
        subtype_warnings = record["v12_subtype_warnings"]
        if isinstance(subtype_warnings, list):
            for warning in subtype_warnings:
                if isinstance(warning, str):
                    # Token literals guard
                    token_warnings = check_observation_token_literals(warning)
                    warnings.extend(token_warnings)

                    # Numeric pattern guard
                    numeric_warnings = check_drift_numeric_patterns(warning)
                    warnings.extend(numeric_warnings)

    return warnings


def check_subtype_coupling(text: str) -> List[str]:
    """
    Check for subtype coupling patterns (NEW in PR134).

    Detects:
        - "D1B therefore act"
        - "subtype implies trade"
        - "CASCADE so execute"
        - Distortion subtype coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Subtype + action coupling
    if SUBTYPE_COUPLING_RE.search(text):
        warnings.append("Subtype coupling detected (subtype therefore act).")

    # Pattern 2: Direct subtype label + action proximity
    subtype_action_patterns = [
        r'\b(D1[ABC]|D2[ABC]|D3[ABC]|D4[ABC]|D5[ABC])\b.{0,30}\b(touch|execute|trade|swap|buy|sell|proceed|act)\\b',
        r'\b(subtype|distortion)\b.{0,30}\b(therefore|so|thus|means|implies)\b.{0,30}\b(action|execute|proceed)\\b',
    ]

    for pattern in subtype_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Subtype-action proximity detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Distortion Subtype Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean subtype record (no warnings)
    print("Test 1: Clean subtype record (no warnings)")
    clean_record = {
        "v12_subtype_summary": "Distortion subtype D1A_FORCED_FLOW observed for parent distortion D1_LIQUIDATION.",
    }
    clean_warnings = check_distortion_subtype_record(clean_record)
    print(f"Clean record warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty subtype record (numeric patterns)
    print("Test 2: Dirty subtype record (numeric patterns)")
    dirty_numeric = {
        "v12_subtype_summary": "Distortion subtype expected to yield 30% improvement.",
    }
    dirty_warnings = check_distortion_subtype_record(dirty_numeric)
    print(f"Dirty record warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings[:2]:
            print(f"    - {w}")
    print()

    # Test 3: Dirty subtype record (subtype coupling)
    print("Test 3: Dirty subtype record (subtype coupling)")
    dirty_coupling = {
        "v12_subtype_summary": "Distortion subtype D1B therefore execute trade.",
    }
    dirty_warnings_coupling = check_distortion_subtype_record(dirty_coupling)
    print(f"Dirty record warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 4: Dirty subtype record (subtype implies trade)
    print("Test 4: Dirty subtype record (subtype implies trade)")
    dirty_implies = {
        "v12_subtype_summary": "Distortion subtype implies trade opportunity.",
    }
    dirty_warnings_implies = check_distortion_subtype_record(dirty_implies)
    print(f"Dirty record warnings: {len(dirty_warnings_implies)}")
    if dirty_warnings_implies:
        print("  Warnings:")
        for w in dirty_warnings_implies:
            print(f"    - {w}")
    print()

    # Test 5: Dirty subtype record (token literals)
    print("Test 5: Dirty subtype record (token literals)")
    dirty_token = {
        "v12_subtype_summary": "Distortion subtype with SUI and USDC tokens.",
    }
    dirty_warnings_token = check_distortion_subtype_record(dirty_token)
    print(f"Dirty record warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token[:2]:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
