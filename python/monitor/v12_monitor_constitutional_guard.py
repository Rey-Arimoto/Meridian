#!/usr/bin/env python3
"""
PR126: v1.2 Monitor Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on monitor records.
    Guards against trading vocabulary, token literals, numeric patterns,
    prescriptive language, and trajectory coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No counts, percentages, scores
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - No trajectory coupling: No "permission improved therefore act", "suppressed so do X"

Guards:
    1. Token literal guard (from observation)
    2. Numeric pattern guard (from drift)
    3. Address pattern guard (from preview)
    4. Trading vocabulary guard (from preview)
    5. Execution operation guard (from preview)
    6. Forbidden vocabulary guard (from execution)
    7. Prescriptive language guard (from policy)
    8. Trajectory coupling guard (NEW)

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


def check_monitor_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate monitor record against constitutional guards.

    Args:
        record: Monitor record to validate

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

    # Check monitor summary
    if "v12_monitor_summary" in record:
        summary = record["v12_monitor_summary"]
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

            # Trajectory coupling guard (NEW)
            trajectory_warnings = check_trajectory_coupling(summary)
            warnings.extend(trajectory_warnings)

    return warnings


def check_trajectory_coupling(text: str) -> List[str]:
    """
    Check for trajectory coupling patterns (NEW in PR126).

    Detects:
        - "permission improved therefore act"
        - "suppressed so do X"
        - "recovering therefore execute"
        - State trajectory coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Permission state + action coupling
    permission_action_patterns = [
        r'(allow|allowed|permission)\s+(therefore|so|thus|then)\s+(act|execute|proceed)',
        r'(suppressed|hold|degrading)\s+(therefore|so|thus|then)\s+(stop|halt|do)',
        r'(recovering|recovery)\s+(therefore|so|thus|then)\s+(execute|proceed|act)',
        r'if\s+(allow|permission)\s+(then|,)\s+(execute|proceed)',
        r'when\s+(recovering|allow)\s+(execute|proceed|act)',
    ]

    for pattern in permission_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Trajectory coupling detected: '{pattern}' in text")

    # Pattern 2: State transition coupling
    transition_coupling_patterns = [
        r'(improved|degraded)\s+(therefore|so|thus)',
        r'transition\s+(means|implies|indicates\s+that)\s+(should|must)',
        r'(stable|degrading|recovering|suppressed)\s+(means|implies)\s+(action|execute)',
    ]

    for pattern in transition_coupling_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"State transition coupling detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Monitor Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean monitor (no warnings)
    print("Test 1: Clean monitor (no warnings)")
    clean_monitor = {
        "v12_monitor_summary": "current permission labeled as DRY_RUN_ONLY. suppression state labeled as STABLE.",
    }
    clean_warnings = check_monitor_record(clean_monitor)
    print(f"Clean monitor warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty monitor (token literals)
    print("Test 2: Dirty monitor (token literals)")
    dirty_token = {
        "v12_monitor_summary": "permission monitored for SUI and USDC.",
    }
    dirty_warnings = check_monitor_record(dirty_token)
    print(f"Dirty monitor warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty monitor (numeric patterns)
    print("Test 3: Dirty monitor (numeric patterns)")
    dirty_numeric = {
        "v12_monitor_summary": "detected 5 transitions in window.",
    }
    dirty_warnings_numeric = check_monitor_record(dirty_numeric)
    print(f"Dirty monitor warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 4: Dirty monitor (trajectory coupling - NEW)
    print("Test 4: Dirty monitor (trajectory coupling)")
    dirty_coupling = {
        "v12_monitor_summary": "permission improved therefore execute operation.",
    }
    dirty_warnings_coupling = check_monitor_record(dirty_coupling)
    print(f"Dirty monitor warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 5: Dirty monitor (suppressed so do X)
    print("Test 5: Dirty monitor (suppressed so do X)")
    dirty_suppressed = {
        "v12_monitor_summary": "state is suppressed so stop operations.",
    }
    dirty_warnings_suppressed = check_monitor_record(dirty_suppressed)
    print(f"Dirty monitor warnings: {len(dirty_warnings_suppressed)}")
    if dirty_warnings_suppressed:
        print("  Warnings:")
        for w in dirty_warnings_suppressed:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
