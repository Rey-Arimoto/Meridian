#!/usr/bin/env python3
"""
PR127: v1.2 Signal Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on trajectory signal records.
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
    8. Trajectory coupling guard (from monitor, strengthened)

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


def check_signal_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate signal record against constitutional guards.

    Args:
        record: Signal record to validate

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
    from monitor.v12_monitor_constitutional_guard import (
        check_trajectory_coupling,
    )

    warnings = []

    # Check signal summary
    if "v12_signal_summary" in record:
        summary = record["v12_signal_summary"]
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

            # Trajectory coupling guard (strengthened)
            trajectory_warnings = check_trajectory_coupling(summary)
            warnings.extend(trajectory_warnings)

            # Additional signal-specific coupling patterns
            signal_coupling_warnings = check_signal_trajectory_coupling(summary)
            warnings.extend(signal_coupling_warnings)

    return warnings


def check_signal_trajectory_coupling(text: str) -> List[str]:
    """
    Check for signal-specific trajectory coupling patterns (strengthened).

    Detects:
        - "level improved therefore act"
        - "state degrading so halt"
        - "recovering means execute"
        - "transition indicates action"
        - Signal label coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Signal label + action coupling
    signal_action_patterns = [
        r'(level|state|transition)\s+(improved|degraded|recovering)\s+(therefore|so|thus|then)\s+(act|execute|proceed)',
        r'(stable|degrading|recovering|suppressed)\s+(means|implies|indicates)\s+(action|execute|proceed)',
        r'if\s+(stable|recovering|allow)\s+(then|,)\s+(execute|proceed|act)',
        r'when\s+(recovering|stable|allow)\s+(execute|proceed|act)',
        r'(degrading|suppressed)\s+(therefore|so|thus|then)\s+(stop|halt|avoid)',
    ]

    for pattern in signal_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Signal trajectory coupling detected: '{pattern}' in text")

    # Pattern 2: Directional signal coupling
    directional_coupling_patterns = [
        r'level\s+(up|down|higher|lower)\s+(therefore|so|thus|means)',
        r'transition\s+(to|from)\s+\w+\s+(means|implies|indicates)\s+(should|must)',
        r'(improvement|degradation|recovery)\s+(indicates|means)\s+(time\s+to|ready\s+to)',
    ]

    for pattern in directional_coupling_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Directional signal coupling detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Signal Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean signal (no warnings)
    print("Test 1: Clean signal (no warnings)")
    clean_signal = {
        "v12_signal_summary": "permission level labeled as DRY_RUN_ONLY. suppression state labeled as STABLE.",
    }
    clean_warnings = check_signal_record(clean_signal)
    print(f"Clean signal warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty signal (token literals)
    print("Test 2: Dirty signal (token literals)")
    dirty_token = {
        "v12_signal_summary": "permission trajectory for SUI and USDC.",
    }
    dirty_warnings = check_signal_record(dirty_token)
    print(f"Dirty signal warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings[:3]:
            print(f"    - {w}")
    print()

    # Test 3: Dirty signal (numeric patterns)
    print("Test 3: Dirty signal (numeric patterns)")
    dirty_numeric = {
        "v12_signal_summary": "detected 5 transitions with 80% confidence.",
    }
    dirty_warnings_numeric = check_signal_record(dirty_numeric)
    print(f"Dirty signal warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 4: Dirty signal (trajectory coupling)
    print("Test 4: Dirty signal (trajectory coupling)")
    dirty_coupling = {
        "v12_signal_summary": "permission level improved therefore execute operation.",
    }
    dirty_warnings_coupling = check_signal_record(dirty_coupling)
    print(f"Dirty signal warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 5: Dirty signal (state degrading so halt)
    print("Test 5: Dirty signal (state degrading so halt)")
    dirty_state = {
        "v12_signal_summary": "state degrading so halt operations.",
    }
    dirty_warnings_state = check_signal_record(dirty_state)
    print(f"Dirty signal warnings: {len(dirty_warnings_state)}")
    if dirty_warnings_state:
        print("  Warnings:")
        for w in dirty_warnings_state:
            print(f"    - {w}")
    print()

    # Test 6: Dirty signal (recovering means execute)
    print("Test 6: Dirty signal (recovering means execute)")
    dirty_recovering = {
        "v12_signal_summary": "recovering means proceed with execution.",
    }
    dirty_warnings_recovering = check_signal_record(dirty_recovering)
    print(f"Dirty signal warnings: {len(dirty_warnings_recovering)}")
    if dirty_warnings_recovering:
        print("  Warnings:")
        for w in dirty_warnings_recovering:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
