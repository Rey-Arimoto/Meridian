#!/usr/bin/env python3
"""
PR120: v1.0 Drift Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on drift records.
    Guards against trading vocabulary, token literals, and numeric patterns.

Constitutional Constraints:
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution vocabulary: No transaction, broadcast, submit
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No 0x... patterns
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad, profitable/unprofitable vocabulary
    - Non-prescriptive: No should/must recommendations
    - Drift-specific: NO numeric patterns in output (especially counts, scores, percentages)
    - Drift = qualitative label only (no numbers)

Guards:
    1. Trading vocabulary guard (swap, buy, sell, execute, sign, transfer)
    2. Execution operation guard (transaction, broadcast, submit)
    3. Token literal guard (token names)
    4. Address pattern guard (0x...)
    5. Asset vocabulary guard (balance, holdings, portfolio)
    6. Action vocabulary guard (recommend, suggest, optimize)
    7. Forbidden vocabulary guard (evaluative/prescriptive)
    8. Numeric pattern guard - STRENGTHENED for PR120 (NEW)
    9. Drift level validation (NEW in PR120)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


def validate_drift_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate drift record against all constitutional guards.

    Args:
        record: Drift record to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import existing guards
    from observation.v10_observation_constitutional_guard import (
        check_observation_token_literals,
    )
    from bridge.v10_bridge_constitutional_guard import (
        check_asset_vocabulary,
        check_execution_vocabulary_bridge,
    )
    from regime.v11_regime_constitutional_guard import (
        check_action_vocabulary,
    )
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )
    from preview.v11_preview_constitutional_guard import (
        check_trading_vocabulary,
        check_execution_operations,
        check_address_patterns,
    )

    warnings = []

    # Check drift summary
    if "v10_drift_summary" in record:
        summary = record["v10_drift_summary"]
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

            # Asset vocabulary guard
            asset_warnings = check_asset_vocabulary(summary)
            warnings.extend(asset_warnings)

            # Action vocabulary guard
            action_warnings = check_action_vocabulary(summary)
            warnings.extend(action_warnings)

            # Forbidden vocabulary guard
            vocab_warnings = check_forbidden_vocabulary(summary)
            warnings.extend(vocab_warnings)

            # STRENGTHENED numeric pattern guard (NEW in PR120)
            numeric_warnings = check_drift_numeric_patterns(summary)
            warnings.extend(numeric_warnings)

    # Check drift evidence
    if "v10_drift_evidence" in record:
        evidence = record["v10_drift_evidence"]
        if isinstance(evidence, list):
            for evidence_item in evidence:
                if isinstance(evidence_item, str):
                    # Token literals guard
                    token_warnings = check_observation_token_literals(evidence_item)
                    warnings.extend(token_warnings)

                    # Trading vocabulary guard
                    trading_warnings = check_trading_vocabulary(evidence_item)
                    warnings.extend(trading_warnings)

                    # Address pattern guard
                    address_warnings = check_address_patterns(evidence_item)
                    warnings.extend(address_warnings)

                    # STRENGTHENED numeric pattern guard (NEW in PR120)
                    numeric_warnings = check_drift_numeric_patterns(evidence_item)
                    warnings.extend(numeric_warnings)

    # Check drift level validation (NEW in PR120)
    if "v10_drift_level" in record:
        level_warnings = check_drift_level_validation(record["v10_drift_level"])
        warnings.extend(level_warnings)

    # Check error info (if present)
    if "v10_drift_error_info" in record:
        error_info = record["v10_drift_error_info"]
        if isinstance(error_info, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(error_info)
            warnings.extend(token_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(error_info)
            warnings.extend(trading_warnings)

    return warnings


def check_drift_numeric_patterns(text: str) -> List[str]:
    """
    Check for numeric patterns in drift output (STRENGTHENED for PR120).

    Detects:
    - Explicit counts: "3 terms", "5 changes", "10 deltas"
    - Percentages: "50%", "10 percent"
    - Numeric comparisons: "delta=3", "count=5", "score=0.8"
    - Raw numbers in context: "added 4", "removed 2"

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Explicit counts with context
    # "N terms", "N changes", "N deltas", "N added", "N removed"
    count_patterns = [
        r'\d+\s+terms?',
        r'\d+\s+changes?',
        r'\d+\s+deltas?',
        r'\d+\s+added',
        r'\d+\s+removed',
        r'\d+\s+items?',
        r'\d+\s+differences?',
        r'added\s+\d+',
        r'removed\s+\d+',
    ]

    for pattern in count_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Numeric count pattern detected: '{pattern}' in text")

    # Pattern 2: Percentages
    if re.search(r'\d+\s*%', text) or re.search(r'\d+\s+percent', text, re.IGNORECASE):
        warnings.append("Percentage pattern detected in text")

    # Pattern 3: Numeric assignments/comparisons
    # "delta=N", "count=N", "score=N"
    assignment_patterns = [
        r'delta\s*=\s*\d+',
        r'count\s*=\s*\d+',
        r'score\s*=\s*[\d.]+',
        r'threshold\s*=\s*\d+',
    ]

    for pattern in assignment_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Numeric assignment pattern detected: '{pattern}' in text")

    # Pattern 4: Currency/price patterns (extra strict)
    if '$' in text or '¥' in text or '€' in text:
        warnings.append("Currency symbol detected in text")

    # Pattern 5: Decimal numbers in suspicious contexts
    if re.search(r'\d+\.\d+', text):
        # Allow version numbers like "v1.0" but flag others
        if not re.search(r'v\d+\.\d+', text, re.IGNORECASE):
            warnings.append("Decimal number detected in text")

    return warnings


def check_drift_level_validation(drift_level: Any) -> List[str]:
    """
    Validate drift level is from approved set (NEW in PR120).

    Args:
        drift_level: Drift level to validate

    Returns:
        List of warnings
    """
    from .v10_market_structure_drift_schema import V10MarketStructureDriftSchema

    warnings = []

    if not isinstance(drift_level, str):
        warnings.append(f"Drift level must be string: {type(drift_level)}")
        return warnings

    if drift_level not in V10MarketStructureDriftSchema.VALID_DRIFT_LEVELS:
        warnings.append(
            f"Invalid drift level: {drift_level} (not in approved set)"
        )

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Drift Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean drift record
    print("Test 1: Clean drift record")
    clean_drift = {
        "v10_drift_summary": "market structure drift classified as drift_medium. moderate structural changes detected. terms added and removed.",
        "v10_drift_level": "DRIFT_MEDIUM",
        "v10_drift_evidence": ["COST_HIGH_PRESENT_ADDED", "EVENT_ACTIVITY_ABSENT_REMOVED"],
    }
    clean_warnings = validate_drift_record(clean_drift)
    print(f"Clean drift warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty drift (numeric patterns)
    print("Test 2: Dirty drift (numeric patterns)")
    dirty_drift_numeric = {
        "v10_drift_summary": "market structure drift detected. 5 terms added and 3 terms removed. delta=8.",
        "v10_drift_level": "DRIFT_HIGH",
        "v10_drift_evidence": ["COST_HIGH_PRESENT_ADDED"],
    }
    dirty_warnings = validate_drift_record(dirty_drift_numeric)
    print(f"Dirty drift warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty drift (token literals)
    print("Test 3: Dirty drift (token literals)")
    dirty_drift_token = {
        "v10_drift_summary": "market structure drift with SUI and USDC activity changes.",
        "v10_drift_level": "DRIFT_LOW",
        "v10_drift_evidence": [],
    }
    dirty_warnings_token = validate_drift_record(dirty_drift_token)
    print(f"Dirty drift warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 4: Dirty drift (trading vocabulary)
    print("Test 4: Dirty drift (trading vocabulary)")
    dirty_drift_trading = {
        "v10_drift_summary": "market structure drift detected. execute swap operations now.",
        "v10_drift_level": "DRIFT_HIGH",
        "v10_drift_evidence": [],
    }
    dirty_warnings_trading = validate_drift_record(dirty_drift_trading)
    print(f"Dirty drift warnings: {len(dirty_warnings_trading)}")
    if dirty_warnings_trading:
        print("  Warnings:")
        for w in dirty_warnings_trading:
            print(f"    - {w}")
    print()

    # Test 5: Dirty drift (invalid level)
    print("Test 5: Dirty drift (invalid level)")
    dirty_drift_level = {
        "v10_drift_summary": "market structure drift.",
        "v10_drift_level": "INVALID_LEVEL",
        "v10_drift_evidence": [],
    }
    dirty_warnings_level = validate_drift_record(dirty_drift_level)
    print(f"Dirty drift warnings: {len(dirty_warnings_level)}")
    if dirty_warnings_level:
        print("  Warnings:")
        for w in dirty_warnings_level:
            print(f"    - {w}")
    print()

    # Test 6: Dirty drift (percentages)
    print("Test 6: Dirty drift (percentages)")
    dirty_drift_percentage = {
        "v10_drift_summary": "market structure drift at 50% change rate.",
        "v10_drift_level": "DRIFT_MEDIUM",
        "v10_drift_evidence": [],
    }
    dirty_warnings_percentage = validate_drift_record(dirty_drift_percentage)
    print(f"Dirty drift warnings: {len(dirty_warnings_percentage)}")
    if dirty_warnings_percentage:
        print("  Warnings:")
        for w in dirty_warnings_percentage:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
