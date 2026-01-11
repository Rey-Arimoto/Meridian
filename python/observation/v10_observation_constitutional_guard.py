#!/usr/bin/env python3
"""
PR107: v1.0 Observation Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on observation records.
    Guards against asset knowledge and execution vocabulary.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH, etc.
    - No numeric patterns: No amounts, prices, addresses
    - No execution vocabulary: No getBalance, sign, executeTransaction
    - No evaluative vocabulary: No good/bad, correct/wrong
    - Non-prescriptive: No should/must recommendations

Guards:
    1. Token literal guard (token names)
    2. Numeric pattern guard (amounts, prices, addresses)
    3. RPC execution guard (execution RPC calls)
    4. Forbidden vocabulary guard (evaluative/prescriptive)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def check_observation_token_literals(text: str) -> List[str]:
    """
    Check for token literal patterns in observation text.

    Detects common token names that indicate asset knowledge.

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if no token literals detected)
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_upper = text.upper()

    # Common token literals (case-insensitive)
    token_literals = [
        "SUI",
        "USDC",
        "USDT",
        "BTC",
        "ETH",
        "SOL",
        "DEEP",
        "CETUS",
    ]

    for token in token_literals:
        # Check for standalone token name (not part of word)
        # e.g., "SUI" but not "SUITE"
        import re
        pattern = r'\b' + re.escape(token) + r'\b'
        if re.search(pattern, text_upper):
            warnings.append(f"Token literal detected: {token}")

    return warnings


def check_observation_numeric_patterns(text: str) -> List[str]:
    """
    Check for numeric pattern violations in observation text.

    Detects:
        - Numeric values (amounts, prices)
        - Currency symbols ($, €, ¥)
        - Address patterns (0x...)
        - Percentage patterns (XX%)

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if no numeric patterns detected)
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Numeric patterns (digits)
    import re
    numeric_pattern = r'\d+'
    if re.search(numeric_pattern, text):
        # Allow epoch numbers and timestamps (context-dependent)
        # Warn only if it looks like an amount/price
        # For now, we'll be strict and warn on any digits in summaries
        # But allow digits in data fields (epoch, timestamp)
        # This check is primarily for summaries
        if "epoch" not in text.lower() and "timestamp" not in text.lower():
            warnings.append(f"Numeric pattern detected: contains digits")

    # Currency symbols
    currency_symbols = ["$", "€", "¥", "£"]
    for symbol in currency_symbols:
        if symbol in text:
            warnings.append(f"Currency symbol detected: {symbol}")

    # Address patterns (0x followed by 40+ hex chars)
    address_pattern = r'0x[a-fA-F0-9]{40,}'
    if re.search(address_pattern, text):
        warnings.append(f"Address pattern detected: {address_pattern}")

    # Percentage patterns (could indicate price changes)
    percentage_pattern = r'\d+\.?\d*%'
    if re.search(percentage_pattern, text):
        warnings.append(f"Percentage pattern detected: indicates price change")

    return warnings


def check_rpc_execution_vocabulary(text: str) -> List[str]:
    """
    Check for RPC execution operation vocabulary.

    Detects vocabulary that indicates execution operations
    rather than read-only observations.

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if read-only)
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # RPC execution operations (prohibited)
    execution_operations = [
        "getbalance",
        "getcoins",
        "sign",
        "executetransaction",
        "sendtransaction",
        "transfer",
        "movecall",
        "publish",
        "splitcoin",
        "mergecoin",
    ]

    import re
    for operation in execution_operations:
        pattern = r'\b' + re.escape(operation) + r'\b'
        if re.search(pattern, text_lower):
            warnings.append(f"RPC execution operation detected: {operation}")

    return warnings


def validate_observation_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate observation record against all constitutional guards.

    Args:
        record: Observation record to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import existing constitutional guards
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )

    warnings = []

    # Check summary
    if "v10_obs_summary" in record:
        summary = record["v10_obs_summary"]

        # Token literals guard
        token_warnings = check_observation_token_literals(summary)
        warnings.extend(token_warnings)

        # Numeric patterns guard
        numeric_warnings = check_observation_numeric_patterns(summary)
        warnings.extend(numeric_warnings)

        # RPC execution guard
        rpc_warnings = check_rpc_execution_vocabulary(summary)
        warnings.extend(rpc_warnings)

        # Forbidden vocabulary guard (from PR100)
        vocab_warnings = check_forbidden_vocabulary(summary)
        warnings.extend(vocab_warnings)

    # Check observation data
    if "v10_obs_data" in record:
        obs_data = record["v10_obs_data"]
        if isinstance(obs_data, dict):
            # Convert data to string for checking
            data_str = str(obs_data)

            # Token literals guard
            token_warnings = check_observation_token_literals(data_str)
            warnings.extend(token_warnings)

            # Note: We allow numeric values in obs_data fields (epoch, timestamp)
            # But not in qualitative states (liquidity_state, gas_price_bucket)

    # Check error info
    if "v10_obs_error_info" in record:
        error_info = record["v10_obs_error_info"]
        if isinstance(error_info, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(error_info)
            warnings.extend(token_warnings)

            # RPC execution guard
            rpc_warnings = check_rpc_execution_vocabulary(error_info)
            warnings.extend(rpc_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Observation Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean observation record
    print("Test 1: Clean observation record")
    clean_obs = {
        "v10_obs_summary": "chain state observed on testnet. epoch and gas price bucket captured.",
        "v10_obs_data": {
            "epoch": 100,
            "gas_price_bucket": "MEDIUM",
        },
    }
    clean_warnings = validate_observation_record(clean_obs)
    print(f"Clean observation warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty observation record (token literals)
    print("Test 2: Dirty observation record (token literals)")
    dirty_obs_tokens = {
        "v10_obs_summary": "observed SUI and USDC pool activity on mainnet.",
    }
    dirty_warnings = validate_observation_record(dirty_obs_tokens)
    print(f"Dirty observation warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty observation record (numeric patterns)
    print("Test 3: Dirty observation record (numeric patterns)")
    dirty_obs_numeric = {
        "v10_obs_summary": "observed balance of 1000 tokens at $2.50 price.",
    }
    dirty_warnings_numeric = validate_observation_record(dirty_obs_numeric)
    print(f"Dirty observation warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 4: Dirty observation record (RPC execution)
    print("Test 4: Dirty observation record (RPC execution)")
    dirty_obs_rpc = {
        "v10_obs_summary": "fetched using getBalance and sign operations.",
    }
    dirty_warnings_rpc = validate_observation_record(dirty_obs_rpc)
    print(f"Dirty observation warnings: {len(dirty_warnings_rpc)}")
    if dirty_warnings_rpc:
        print("  Warnings:")
        for w in dirty_warnings_rpc:
            print(f"    - {w}")
    print()

    # Test 5: Dirty observation record (evaluative vocabulary)
    print("Test 5: Dirty observation record (evaluative vocabulary)")
    dirty_obs_eval = {
        "v10_obs_summary": "good liquidity state observed. this is the best pool.",
    }
    dirty_warnings_eval = validate_observation_record(dirty_obs_eval)
    print(f"Dirty observation warnings: {len(dirty_warnings_eval)}")
    if dirty_warnings_eval:
        print("  Warnings:")
        for w in dirty_warnings_eval:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
