#!/usr/bin/env python3
"""
PR108: v1.0 Bridge Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on bridge normalization.
    Guards against asset vocabulary and execution operations.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No amounts, prices, addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No execution vocabulary: No buy, sell, trade, swap
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No should/must recommendations

Guards:
    1. Token literal guard (token names)
    2. Numeric pattern guard (amounts, prices, addresses)
    3. Asset vocabulary guard (balance, holdings, portfolio, etc.)
    4. Execution vocabulary guard (buy, sell, trade, swap)
    5. Forbidden vocabulary guard (evaluative/prescriptive)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


def check_asset_vocabulary(text: str) -> List[str]:
    """
    Check for asset vocabulary patterns.

    Detects vocabulary that indicates asset ownership or balances,
    which violates the observation-not-ownership principle.

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if no asset vocabulary detected)
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # Asset vocabulary patterns (word boundaries)
    asset_vocabulary = [
        "balance",
        "balances",
        "holding",
        "holdings",
        "portfolio",
        "asset",
        "assets",
        "position",
        "positions",
        "ownership",
        "owned",
        "possess",
        "possesses",
        "wallet",
        "account",
    ]

    for vocab in asset_vocabulary:
        pattern = r'\b' + re.escape(vocab) + r'\b'
        if re.search(pattern, text_lower):
            warnings.append(f"Asset vocabulary detected: {vocab}")

    return warnings


def check_execution_vocabulary_bridge(text: str) -> List[str]:
    """
    Check for execution vocabulary patterns.

    Detects vocabulary that indicates execution operations,
    which violates the read-only principle.

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if no execution vocabulary detected)
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # Execution vocabulary patterns (word boundaries)
    execution_vocabulary = [
        "buy",
        "buying",
        "sell",
        "selling",
        "trade",
        "trading",
        "swap",
        "swapping",
        "execute",
        "executing",
        "transact",
        "transacting",
    ]

    for vocab in execution_vocabulary:
        pattern = r'\b' + re.escape(vocab) + r'\b'
        if re.search(pattern, text_lower):
            warnings.append(f"Execution vocabulary detected: {vocab}")

    return warnings


def validate_normalized_observation_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate normalized observation record against all constitutional guards.

    Args:
        record: Normalized observation record to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import existing guards
    from observation.v10_observation_constitutional_guard import (
        check_observation_token_literals,
        check_observation_numeric_patterns,
    )
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )

    warnings = []

    # Check summary
    if "v10_norm_obs_summary" in record:
        summary = record["v10_norm_obs_summary"]

        # Token literals guard (from PR107)
        token_warnings = check_observation_token_literals(summary)
        warnings.extend(token_warnings)

        # Numeric patterns guard (from PR107)
        numeric_warnings = check_observation_numeric_patterns(summary)
        warnings.extend(numeric_warnings)

        # Asset vocabulary guard (bridge-specific)
        asset_warnings = check_asset_vocabulary(summary)
        warnings.extend(asset_warnings)

        # Execution vocabulary guard (bridge-specific)
        exec_warnings = check_execution_vocabulary_bridge(summary)
        warnings.extend(exec_warnings)

        # Forbidden vocabulary guard (from PR100)
        vocab_warnings = check_forbidden_vocabulary(summary)
        warnings.extend(vocab_warnings)

    # Check error info
    if "v10_norm_obs_error_info" in record:
        error_info = record["v10_norm_obs_error_info"]
        if isinstance(error_info, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(error_info)
            warnings.extend(token_warnings)

            # Asset vocabulary guard
            asset_warnings = check_asset_vocabulary(error_info)
            warnings.extend(asset_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Bridge Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean normalized observation record
    print("Test 1: Clean normalized observation record")
    clean_norm = {
        "v10_norm_obs_summary": "normalized observation available. structural facts captured.",
    }
    clean_warnings = validate_normalized_observation_record(clean_norm)
    print(f"Clean normalized observation warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty normalized observation (asset vocabulary)
    print("Test 2: Dirty normalized observation (asset vocabulary)")
    dirty_norm_asset = {
        "v10_norm_obs_summary": "normalized observation of wallet balance and holdings.",
    }
    dirty_warnings = validate_normalized_observation_record(dirty_norm_asset)
    print(f"Dirty normalized observation warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty normalized observation (execution vocabulary)
    print("Test 3: Dirty normalized observation (execution vocabulary)")
    dirty_norm_exec = {
        "v10_norm_obs_summary": "normalized observation ready for buy and sell operations.",
    }
    dirty_warnings_exec = validate_normalized_observation_record(dirty_norm_exec)
    print(f"Dirty normalized observation warnings: {len(dirty_warnings_exec)}")
    if dirty_warnings_exec:
        print("  Warnings:")
        for w in dirty_warnings_exec:
            print(f"    - {w}")
    print()

    # Test 4: Dirty normalized observation (token literals)
    print("Test 4: Dirty normalized observation (token literals)")
    dirty_norm_token = {
        "v10_norm_obs_summary": "normalized observation of SUI and USDC market activity.",
    }
    dirty_warnings_token = validate_normalized_observation_record(dirty_norm_token)
    print(f"Dirty normalized observation warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 5: Dirty normalized observation (numeric patterns)
    print("Test 5: Dirty normalized observation (numeric patterns)")
    dirty_norm_numeric = {
        "v10_norm_obs_summary": "normalized observation shows 1000 tokens at $2.50 price.",
    }
    dirty_warnings_numeric = validate_normalized_observation_record(dirty_norm_numeric)
    print(f"Dirty normalized observation warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
