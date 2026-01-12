#!/usr/bin/env python3
"""
PR122: v1.1 Human Explanation Context Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on human explanation context records.
    Guards against trading vocabulary, token literals, numeric patterns, and prescriptive coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No counts, percentages, scores
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive coupling: No "approved therefore execute" patterns

Guards:
    1. Token literal guard (from observation)
    2. Numeric pattern guard (from drift)
    3. Address pattern guard (from preview)
    4. Trading vocabulary guard (from preview)
    5. Execution operation guard (from preview)
    6. Forbidden vocabulary guard (from execution)
    7. Prescriptive coupling guard (NEW)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


def validate_explanation_context(record: Dict[str, Any]) -> List[str]:
    """
    Validate explanation context against constitutional guards.

    Args:
        record: Explanation context record to validate

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

    warnings = []

    # Check summary
    if "v11_explain_summary" in record:
        summary = record["v11_explain_summary"]
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

            # Prescriptive coupling guard (NEW)
            coupling_warnings = check_prescriptive_coupling(summary)
            warnings.extend(coupling_warnings)

    # Check signals (should be label-only, no embedded values)
    if "v11_explain_signals" in record:
        signals = record["v11_explain_signals"]
        if isinstance(signals, list):
            for signal in signals:
                if isinstance(signal, str):
                    # Check for numeric patterns in signals
                    numeric_warnings = check_drift_numeric_patterns(signal)
                    warnings.extend(numeric_warnings)

                    # Check for token literals in signals
                    token_warnings = check_observation_token_literals(signal)
                    warnings.extend(token_warnings)

    return warnings


def check_prescriptive_coupling(text: str) -> List[str]:
    """
    Check for prescriptive coupling patterns (NEW in PR122).

    Detects:
        - "approved therefore execute" / "approved so execute"
        - "if approved then execute" / "when approved execute"
        - "approval means execute" / "approval triggers execution"
        - Action coupling to approval state

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: "approved therefore/so/thus execute"
    coupling_patterns = [
        r'approved\s+(therefore|so|thus|then)\s+execute',
        r'if\s+approved\s+(then|,)\s+execute',
        r'when\s+approved\s+execute',
        r'upon\s+approval\s+execute',
        r'approval\s+(means|triggers|enables)\s+execut',
        r'after\s+approval\s+execute',
    ]

    for pattern in coupling_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Prescriptive coupling detected: '{pattern}' in text")

    # Pattern 2: Generic coupling ("approval state determines action")
    generic_coupling = [
        r'approved\s+.*\s+(swap|buy|sell|transfer|sign)',
        r'if\s+approved\s+.*\s+(proceed|continue|go\s+ahead)',
    ]

    for pattern in generic_coupling:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Action coupling detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.1 Human Explanation Context Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean explanation context (no warnings)
    print("Test 1: Clean explanation context (no warnings)")
    clean_context = {
        "v11_explain_summary": "current structural situation: regime medium, drift low, permission dry-run-only.",
        "v11_explain_signals": ["REGIME_MEDIUM", "DRIFT_LOW", "PERMISSION_DRY_RUN_ONLY"],
    }
    clean_warnings = validate_explanation_context(clean_context)
    print(f"Clean context warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty context (token literals)
    print("Test 2: Dirty context (token literals)")
    dirty_token = {
        "v11_explain_summary": "current situation: SUI and USDC activity detected.",
        "v11_explain_signals": [],
    }
    dirty_warnings = validate_explanation_context(dirty_token)
    print(f"Dirty context warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty context (numeric patterns)
    print("Test 3: Dirty context (numeric patterns)")
    dirty_numeric = {
        "v11_explain_summary": "drift detected with 5 terms added and 3 removed. delta=8.",
        "v11_explain_signals": [],
    }
    dirty_warnings_numeric = validate_explanation_context(dirty_numeric)
    print(f"Dirty context warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 4: Dirty context (trading vocabulary)
    print("Test 4: Dirty context (trading vocabulary)")
    dirty_trading = {
        "v11_explain_summary": "approved. execute swap operations now and transfer funds.",
        "v11_explain_signals": [],
    }
    dirty_warnings_trading = validate_explanation_context(dirty_trading)
    print(f"Dirty context warnings: {len(dirty_warnings_trading)}")
    if dirty_warnings_trading:
        print("  Warnings:")
        for w in dirty_warnings_trading:
            print(f"    - {w}")
    print()

    # Test 5: Dirty context (prescriptive coupling - NEW)
    print("Test 5: Dirty context (prescriptive coupling)")
    dirty_coupling = {
        "v11_explain_summary": "approval state available. if approved then execute the swap operation.",
        "v11_explain_signals": [],
    }
    dirty_warnings_coupling = validate_explanation_context(dirty_coupling)
    print(f"Dirty context warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 6: Dirty signals (numeric in signal)
    print("Test 6: Dirty signals (numeric pattern in signal)")
    dirty_signals = {
        "v11_explain_summary": "test",
        "v11_explain_signals": ["REGIME_MEDIUM", "DRIFT_5_TERMS_ADDED"],  # Invalid - contains number
    }
    dirty_warnings_signals = validate_explanation_context(dirty_signals)
    print(f"Dirty signals warnings: {len(dirty_warnings_signals)}")
    if dirty_warnings_signals:
        print("  Warnings:")
        for w in dirty_warnings_signals:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
