#!/usr/bin/env python3
"""
PR110: v1.1 Regime Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on regime classification.
    Guards against action vocabulary and evaluation.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No asset vocabulary: No balance, holdings, portfolio
    - No execution vocabulary: No buy, sell, trade, swap
    - No action vocabulary: No recommend, suggest, should, must
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-prescriptive: No should/must recommendations

Guards:
    1. Token literal guard (token names)
    2. Asset vocabulary guard (balance, holdings, portfolio)
    3. Execution vocabulary guard (buy, sell, trade, swap)
    4. Action vocabulary guard (recommend, suggest, optimize)
    5. Forbidden vocabulary guard (evaluative/prescriptive)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


def check_action_vocabulary(text: str) -> List[str]:
    """
    Check for action vocabulary patterns.

    Detects vocabulary that indicates recommendations or suggestions,
    which violates the regime-as-state-only principle.

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if no action vocabulary detected)
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # Action vocabulary patterns (word boundaries)
    action_vocabulary = [
        "recommend",
        "recommends",
        "recommended",
        "suggest",
        "suggests",
        "suggested",
        "optimize",
        "optimizes",
        "optimized",
        "improve",
        "improves",
        "improved",
        "enhance",
        "enhances",
        "enhanced",
    ]

    for vocab in action_vocabulary:
        pattern = r'\b' + re.escape(vocab) + r'\b'
        if re.search(pattern, text_lower):
            warnings.append(f"Action vocabulary detected: {vocab}")

    return warnings


def validate_regime_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate regime record against all constitutional guards.

    Args:
        record: Regime record to validate

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
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )

    warnings = []

    # Check regime summary
    if "v11_regime_summary" in record:
        summary = record["v11_regime_summary"]

        # Token literals guard
        token_warnings = check_observation_token_literals(summary)
        warnings.extend(token_warnings)

        # Asset vocabulary guard
        asset_warnings = check_asset_vocabulary(summary)
        warnings.extend(asset_warnings)

        # Execution vocabulary guard
        exec_warnings = check_execution_vocabulary_bridge(summary)
        warnings.extend(exec_warnings)

        # Action vocabulary guard (regime-specific)
        action_warnings = check_action_vocabulary(summary)
        warnings.extend(action_warnings)

        # Forbidden vocabulary guard
        vocab_warnings = check_forbidden_vocabulary(summary)
        warnings.extend(vocab_warnings)

    # Check error info
    if "v11_regime_error_info" in record:
        error_info = record["v11_regime_error_info"]
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
    print("v1.1 Regime Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean regime record
    print("Test 1: Clean regime record")
    clean_regime = {
        "v11_regime_summary": "regime classified as medium. moderate variation observed.",
    }
    clean_warnings = validate_regime_record(clean_regime)
    print(f"Clean regime warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty regime (action vocabulary)
    print("Test 2: Dirty regime (action vocabulary)")
    dirty_regime_action = {
        "v11_regime_summary": "regime classified as high. recommend reducing exposure.",
    }
    dirty_warnings = validate_regime_record(dirty_regime_action)
    print(f"Dirty regime warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty regime (asset vocabulary)
    print("Test 3: Dirty regime (asset vocabulary)")
    dirty_regime_asset = {
        "v11_regime_summary": "regime classified based on portfolio balance patterns.",
    }
    dirty_warnings_asset = validate_regime_record(dirty_regime_asset)
    print(f"Dirty regime warnings: {len(dirty_warnings_asset)}")
    if dirty_warnings_asset:
        print("  Warnings:")
        for w in dirty_warnings_asset:
            print(f"    - {w}")
    print()

    # Test 4: Dirty regime (execution vocabulary)
    print("Test 4: Dirty regime (execution vocabulary)")
    dirty_regime_exec = {
        "v11_regime_summary": "regime high. time to buy or sell positions.",
    }
    dirty_warnings_exec = validate_regime_record(dirty_regime_exec)
    print(f"Dirty regime warnings: {len(dirty_warnings_exec)}")
    if dirty_warnings_exec:
        print("  Warnings:")
        for w in dirty_warnings_exec:
            print(f"    - {w}")
    print()

    # Test 5: Dirty regime (token literals)
    print("Test 5: Dirty regime (token literals)")
    dirty_regime_token = {
        "v11_regime_summary": "regime classified based on SUI and USDC patterns.",
    }
    dirty_warnings_token = validate_regime_record(dirty_regime_token)
    print(f"Dirty regime warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
