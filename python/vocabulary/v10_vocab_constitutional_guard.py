#!/usr/bin/env python3
"""
PR119: v1.0 Vocabulary Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on vocabulary records.
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
    - Vocabulary-specific: Terms must be from fixed vocabulary set
    - No numeric amounts: No counts, prices, percentages in terms/summary

Guards:
    1. Trading vocabulary guard (swap, buy, sell, execute, sign, transfer)
    2. Execution operation guard (transaction, broadcast, submit)
    3. Token literal guard (token names)
    4. Address pattern guard (0x...)
    5. Asset vocabulary guard (balance, holdings, portfolio)
    6. Action vocabulary guard (recommend, suggest, optimize)
    7. Forbidden vocabulary guard (evaluative/prescriptive)
    8. Numeric pattern guard (amounts, prices, percentages - relaxed for counts)
    9. Vocabulary term validation (NEW in PR119)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def validate_vocabulary_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate vocabulary record against all constitutional guards.

    Args:
        record: Vocabulary record to validate

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
        check_numeric_patterns,
    )

    warnings = []

    # Check vocabulary summary
    if "v10_vocab_summary" in record:
        summary = record["v10_vocab_summary"]
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

            # Numeric pattern guard (relaxed for term counts)
            numeric_warnings = check_numeric_patterns(summary)
            # Filter out acceptable patterns (term counts, observation counts)
            forbidden_numeric = [
                w
                for w in numeric_warnings
                if any(
                    pattern in summary
                    for pattern in ["$", "USD", "fee", "price", "amount", "balance"]
                )
            ]
            warnings.extend(forbidden_numeric)

    # Check vocabulary terms
    if "v10_vocab_terms" in record:
        terms = record["v10_vocab_terms"]
        if isinstance(terms, list):
            # Validate term vocabulary (NEW in PR119)
            term_warnings = check_vocabulary_terms(terms)
            warnings.extend(term_warnings)

            # Check each term for forbidden content
            for term in terms:
                if isinstance(term, str):
                    # Token literals guard
                    token_warnings = check_observation_token_literals(term)
                    warnings.extend(token_warnings)

                    # Trading vocabulary guard
                    trading_warnings = check_trading_vocabulary(term)
                    warnings.extend(trading_warnings)

                    # Address pattern guard
                    address_warnings = check_address_patterns(term)
                    warnings.extend(address_warnings)

    # Check error info (if present)
    if "v10_vocab_error_info" in record:
        error_info = record["v10_vocab_error_info"]
        if isinstance(error_info, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(error_info)
            warnings.extend(token_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(error_info)
            warnings.extend(trading_warnings)

    return warnings


def check_vocabulary_terms(terms: List[str]) -> List[str]:
    """
    Check vocabulary terms against fixed vocabulary set (NEW in PR119).

    Validates that all terms are from the approved vocabulary.

    Args:
        terms: List of vocabulary terms

    Returns:
        List of warnings
    """
    from .v10_market_structure_vocabulary_schema import (
        V10MarketStructureVocabularySchema,
    )

    warnings = []

    if not isinstance(terms, list):
        warnings.append("Vocabulary terms must be a list")
        return warnings

    for term in terms:
        if not isinstance(term, str):
            warnings.append(f"Vocabulary term must be string: {term}")
            continue

        if term not in V10MarketStructureVocabularySchema.VALID_TERMS:
            warnings.append(f"Invalid vocabulary term: {term} (not in approved set)")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Vocabulary Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean vocabulary record
    print("Test 1: Clean vocabulary record")
    clean_vocab = {
        "v10_vocab_summary": "market structure vocabulary with 4 terms. low cost and low liquidity regimes present.",
        "v10_vocab_terms": [
            "COST_LOW_PRESENT",
            "LIQUIDITY_LOW_PRESENT",
            "EVENT_ACTIVITY_ABSENT",
            "OBJECT_DYNAMICS_STABLE_PRESENT",
        ],
    }
    clean_warnings = validate_vocabulary_record(clean_vocab)
    print(f"Clean vocabulary warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty vocabulary (trading vocabulary)
    print("Test 2: Dirty vocabulary (trading vocabulary)")
    dirty_vocab_trading = {
        "v10_vocab_summary": "market structure vocabulary. execute swap operations.",
        "v10_vocab_terms": ["COST_LOW_PRESENT"],
    }
    dirty_warnings = validate_vocabulary_record(dirty_vocab_trading)
    print(f"Dirty vocabulary warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty vocabulary (token literals)
    print("Test 3: Dirty vocabulary (token literals)")
    dirty_vocab_token = {
        "v10_vocab_summary": "market structure vocabulary with SUI and USDC terms.",
        "v10_vocab_terms": ["COST_LOW_PRESENT"],
    }
    dirty_warnings_token = validate_vocabulary_record(dirty_vocab_token)
    print(f"Dirty vocabulary warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 4: Dirty vocabulary (invalid terms)
    print("Test 4: Dirty vocabulary (invalid terms)")
    dirty_vocab_terms = {
        "v10_vocab_summary": "market structure vocabulary with invalid terms.",
        "v10_vocab_terms": ["COST_LOW_PRESENT", "INVALID_TERM", "TRADE_NOW"],
    }
    dirty_warnings_terms = validate_vocabulary_record(dirty_vocab_terms)
    print(f"Dirty vocabulary warnings: {len(dirty_warnings_terms)}")
    if dirty_warnings_terms:
        print("  Warnings:")
        for w in dirty_warnings_terms:
            print(f"    - {w}")
    print()

    # Test 5: Dirty vocabulary (numeric patterns - forbidden)
    print("Test 5: Dirty vocabulary (numeric patterns - forbidden)")
    dirty_vocab_numeric = {
        "v10_vocab_summary": "market structure vocabulary for $1000 transaction.",
        "v10_vocab_terms": ["COST_LOW_PRESENT"],
    }
    dirty_warnings_numeric = validate_vocabulary_record(dirty_vocab_numeric)
    print(f"Dirty vocabulary warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 6: Clean vocabulary with term count (acceptable)
    print("Test 6: Clean vocabulary with term count (acceptable)")
    clean_count_vocab = {
        "v10_vocab_summary": "market structure vocabulary with 4 terms. converted from analytics.",
        "v10_vocab_terms": [
            "COST_LOW_PRESENT",
            "LIQUIDITY_LOW_PRESENT",
            "EVENT_ACTIVITY_PRESENT",
            "OBJECT_DYNAMICS_STABLE_PRESENT",
        ],
    }
    clean_count_warnings = validate_vocabulary_record(clean_count_vocab)
    print(f"Clean count vocabulary warnings: {len(clean_count_warnings)}")
    if clean_count_warnings:
        print(f"  Warnings: {clean_count_warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
