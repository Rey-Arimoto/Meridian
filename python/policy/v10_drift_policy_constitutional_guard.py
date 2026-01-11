#!/usr/bin/env python3
"""
PR121: v1.0 Drift Policy Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on drift policy binding outputs.
    Guards against numeric patterns, prescriptive language, and trading vocabulary.

Constitutional Constraints:
    - No numeric patterns: No counts, percentages, scores in output
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No prescriptive language: No should/must recommendations
    - Drift policy = classification labels only (not instructions)

Guards:
    1. Numeric pattern guard (from PR120)
    2. Token literal guard (from PR119)
    3. Address pattern guard (from PR102)
    4. Trading vocabulary guard (from PR112)
    5. Execution operation guard (from PR100)
    6. Forbidden vocabulary guard (from PR100)
    7. Prescriptive language guard (NEW)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


def validate_drift_policy_binding(record: Dict[str, Any]) -> List[str]:
    """
    Validate drift policy binding against constitutional guards.

    Args:
        record: Drift policy binding record to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import existing guards
    from drift.v10_drift_constitutional_guard import (
        check_drift_numeric_patterns,
    )
    from observation.v10_observation_constitutional_guard import (
        check_observation_token_literals,
    )
    from preview.v11_preview_constitutional_guard import (
        check_trading_vocabulary,
        check_execution_operations,
        check_address_patterns,
    )
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )

    warnings = []

    # Check execution summary
    if "v10_execution_summary" in record:
        summary = record["v10_execution_summary"]
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

            # Prescriptive language guard (NEW)
            prescriptive_warnings = check_prescriptive_language(summary)
            warnings.extend(prescriptive_warnings)

    # Check execution constraints
    if "v10_execution_constraints" in record:
        constraints = record["v10_execution_constraints"]
        if isinstance(constraints, list):
            for constraint in constraints:
                if isinstance(constraint, str):
                    # Check constraint labels don't contain numeric patterns
                    numeric_warnings = check_drift_numeric_patterns(constraint)
                    warnings.extend(numeric_warnings)

                    # Check constraint labels don't contain prescriptive language
                    prescriptive_warnings = check_prescriptive_language(constraint)
                    warnings.extend(prescriptive_warnings)

    return warnings


def check_prescriptive_language(text: str) -> List[str]:
    """
    Check for prescriptive language in text (NEW in PR121).

    Detects:
        - "should" / "must" / "need to" patterns
        - "proceed" / "continue" / "stop" / "pause" commands
        - "go ahead" / "wait" instruction patterns

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Should/must/need to language
    should_patterns = [
        r'\bshould\b',
        r'\bmust\b',
        r'\bneed to\b',
        r'\brequired to\b',
        r'\bhas to\b',
        r'\bought to\b',
    ]

    for pattern in should_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Prescriptive language detected: '{pattern}' in text")

    # Pattern 2: Command/instruction language
    command_patterns = [
        r'\bproceed\b',
        r'\bcontinue\b',
        r'\bstop\b',
        r'\bpause\b',
        r'\bgo ahead\b',
        r'\bwait\b',
        r'\bhalt\b',
    ]

    for pattern in command_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Command language detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Drift Policy Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean drift policy binding (no warnings)
    print("Test 1: Clean drift policy binding (no warnings)")
    clean_binding = {
        "v10_execution_summary": "execution permission classified. drift-based permission binding applied. drift_critical_observed.",
        "v10_execution_constraints": ["drift_critical_observed", "dry_run_only"],
    }
    clean_warnings = validate_drift_policy_binding(clean_binding)
    print(f"Clean binding warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty binding (numeric patterns)
    print("Test 2: Dirty binding (numeric patterns)")
    dirty_numeric = {
        "v10_execution_summary": "drift detected with 5 terms added and 3 terms removed. delta=8. should pause execution.",
        "v10_execution_constraints": ["drift_critical_observed"],
    }
    dirty_warnings = validate_drift_policy_binding(dirty_numeric)
    print(f"Dirty binding warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty binding (token literals)
    print("Test 3: Dirty binding (token literals)")
    dirty_token = {
        "v10_execution_summary": "drift detected with SUI and USDC activity changes. execution blocked.",
        "v10_execution_constraints": [],
    }
    dirty_warnings_token = validate_drift_policy_binding(dirty_token)
    print(f"Dirty binding warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 4: Dirty binding (trading vocabulary)
    print("Test 4: Dirty binding (trading vocabulary)")
    dirty_trading = {
        "v10_execution_summary": "drift detected. execute swap operations now. transfer funds.",
        "v10_execution_constraints": [],
    }
    dirty_warnings_trading = validate_drift_policy_binding(dirty_trading)
    print(f"Dirty binding warnings: {len(dirty_warnings_trading)}")
    if dirty_warnings_trading:
        print("  Warnings:")
        for w in dirty_warnings_trading:
            print(f"    - {w}")
    print()

    # Test 5: Dirty binding (prescriptive language)
    print("Test 5: Dirty binding (prescriptive language)")
    dirty_prescriptive = {
        "v10_execution_summary": "drift critical. you should pause execution and must wait for approval. need to stop immediately.",
        "v10_execution_constraints": ["should_wait"],
    }
    dirty_warnings_prescriptive = validate_drift_policy_binding(dirty_prescriptive)
    print(f"Dirty binding warnings: {len(dirty_warnings_prescriptive)}")
    if dirty_warnings_prescriptive:
        print("  Warnings:")
        for w in dirty_warnings_prescriptive:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
