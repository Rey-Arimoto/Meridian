#!/usr/bin/env python3
"""
PR112: v1.1 Preview Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on preview records.
    Guards against trading vocabulary, execution operations, and evaluation.

Constitutional Constraints:
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution vocabulary: No transaction, broadcast, submit
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No 0x... patterns
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad, profitable/unprofitable vocabulary
    - Non-prescriptive: No should/must recommendations

Guards:
    1. Trading vocabulary guard (swap, buy, sell, execute, sign, transfer)
    2. Execution operation guard (transaction, broadcast, submit)
    3. Token literal guard (token names)
    4. Address pattern guard (0x...)
    5. Asset vocabulary guard (balance, holdings, portfolio)
    6. Action vocabulary guard (recommend, suggest, optimize)
    7. Forbidden vocabulary guard (evaluative/prescriptive)
    8. Numeric pattern guard (amounts, prices, percentages)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def validate_preview_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate preview record against all constitutional guards.

    Args:
        record: Preview record to validate

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

    warnings = []

    # Check preview summary
    if "v11_preview_summary" in record:
        summary = record["v11_preview_summary"]

        # Trading vocabulary guard (preview-specific)
        trading_warnings = check_trading_vocabulary(summary)
        warnings.extend(trading_warnings)

        # Execution operation guard (preview-specific)
        execution_warnings = check_execution_operations(summary)
        warnings.extend(execution_warnings)

        # Token literals guard
        token_warnings = check_observation_token_literals(summary)
        warnings.extend(token_warnings)

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

        # Numeric pattern guard
        numeric_warnings = check_numeric_patterns(summary)
        warnings.extend(numeric_warnings)

    # Check block reason (if present)
    if "v11_preview_block_reason" in record:
        block_reason = record["v11_preview_block_reason"]
        if isinstance(block_reason, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(block_reason)
            warnings.extend(token_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(block_reason)
            warnings.extend(trading_warnings)

    # Check error info (if present)
    if "v11_preview_error_info" in record:
        error_info = record["v11_preview_error_info"]
        if isinstance(error_info, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(error_info)
            warnings.extend(token_warnings)

    return warnings


def check_trading_vocabulary(text: str) -> List[str]:
    """
    Check for trading vocabulary in text.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # Trading vocabulary
    trading_terms = [
        "swap",
        "buy",
        "sell",
        "execute",
        "sign",
        "transfer",
        "trade",
        "trading",
    ]

    for term in trading_terms:
        if term in text_lower:
            warnings.append(f"Trading vocabulary detected: '{term}' in text")

    return warnings


def check_execution_operations(text: str) -> List[str]:
    """
    Check for execution operation vocabulary in text.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # Execution operation vocabulary
    execution_terms = [
        "transaction",
        "broadcast",
        "submit",
        "send",
        "wallet",
    ]

    for term in execution_terms:
        if term in text_lower:
            warnings.append(f"Execution operation detected: '{term}' in text")

    return warnings


def check_address_patterns(text: str) -> List[str]:
    """
    Check for address patterns in text.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Check for 0x... patterns (addresses)
    import re
    if re.search(r'0x[0-9a-fA-F]+', text):
        warnings.append("Address pattern detected: '0x...' in text")

    return warnings


def check_numeric_patterns(text: str) -> List[str]:
    """
    Check for numeric patterns in text (amounts, prices, percentages).

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Check for numeric patterns with units
    import re

    # Price patterns (e.g., $1.50, 1.5 USDC)
    if re.search(r'\$\d+', text):
        warnings.append("Numeric price pattern detected: '$...' in text")

    # Percentage patterns (e.g., 5%, 10.5%)
    if re.search(r'\d+\.?\d*\s*%', text):
        warnings.append("Numeric percentage pattern detected: '...%' in text")

    # Amount patterns with decimal (e.g., 1.5, 10.25)
    # Allow single digits (common in categories like "3 regimes")
    if re.search(r'\d{2,}\.?\d*', text):
        warnings.append("Numeric amount pattern detected: large number in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.1 Preview Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean preview record
    print("Test 1: Clean preview record")
    clean_preview = {
        "v11_preview_summary": "hedge-type plan would reduce exposure with pool interaction under elevated market regime.",
    }
    clean_warnings = validate_preview_record(clean_preview)
    print(f"Clean preview warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty preview (trading vocabulary)
    print("Test 2: Dirty preview (trading vocabulary)")
    dirty_preview_trading = {
        "v11_preview_summary": "plan will execute swap and buy operations.",
    }
    dirty_warnings = validate_preview_record(dirty_preview_trading)
    print(f"Dirty preview warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty preview (execution operations)
    print("Test 3: Dirty preview (execution operations)")
    dirty_preview_exec = {
        "v11_preview_summary": "plan will submit transaction to blockchain.",
    }
    dirty_warnings_exec = validate_preview_record(dirty_preview_exec)
    print(f"Dirty preview warnings: {len(dirty_warnings_exec)}")
    if dirty_warnings_exec:
        print("  Warnings:")
        for w in dirty_warnings_exec:
            print(f"    - {w}")
    print()

    # Test 4: Dirty preview (token literals)
    print("Test 4: Dirty preview (token literals)")
    dirty_preview_token = {
        "v11_preview_summary": "plan involves SUI and USDC trading.",
    }
    dirty_warnings_token = validate_preview_record(dirty_preview_token)
    print(f"Dirty preview warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 5: Dirty preview (addresses)
    print("Test 5: Dirty preview (addresses)")
    dirty_preview_address = {
        "v11_preview_summary": "plan targets address 0x1234567890abcdef.",
    }
    dirty_warnings_address = validate_preview_record(dirty_preview_address)
    print(f"Dirty preview warnings: {len(dirty_warnings_address)}")
    if dirty_warnings_address:
        print("  Warnings:")
        for w in dirty_warnings_address:
            print(f"    - {w}")
    print()

    # Test 6: Dirty preview (numeric patterns)
    print("Test 6: Dirty preview (numeric patterns)")
    dirty_preview_numeric = {
        "v11_preview_summary": "plan will adjust position by 15.5% to reach $1000 target.",
    }
    dirty_warnings_numeric = validate_preview_record(dirty_preview_numeric)
    print(f"Dirty preview warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 7: Dirty preview (action vocabulary)
    print("Test 7: Dirty preview (action vocabulary)")
    dirty_preview_action = {
        "v11_preview_summary": "recommend optimizing positions to improve performance.",
    }
    dirty_warnings_action = validate_preview_record(dirty_preview_action)
    print(f"Dirty preview warnings: {len(dirty_warnings_action)}")
    if dirty_warnings_action:
        print("  Warnings:")
        for w in dirty_warnings_action:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
