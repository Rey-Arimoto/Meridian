#!/usr/bin/env python3
"""
PR118: v1.0 CLI Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on CLI output.
    Guards against trading vocabulary, execution operations, and sensitive data.

Constitutional Constraints:
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution vocabulary: No transaction, broadcast, submit
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No 0x... patterns
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad, profitable/unprofitable vocabulary
    - Non-prescriptive: No should/must recommendations
    - CLI-specific: No instruction/recommendation vocabulary
    - CLI = Display only (not instruction/action)

Guards:
    1. Trading vocabulary guard (swap, buy, sell, execute, sign, transfer)
    2. Execution operation guard (transaction, broadcast, submit)
    3. Token literal guard (token names)
    4. Address pattern guard (0x...)
    5. Asset vocabulary guard (balance, holdings, portfolio)
    6. Action vocabulary guard (recommend, suggest, optimize)
    7. Forbidden vocabulary guard (evaluative/prescriptive)
    8. Numeric pattern guard (amounts, prices, percentages)
    9. CLI instruction guard (NEW in PR118)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def validate_cli_output(output: str) -> List[str]:
    """
    Validate CLI output against all constitutional guards.

    Args:
        output: CLI output text to validate

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

    if not isinstance(output, str):
        warnings.append("CLI output is not a string")
        return warnings

    # Token literals guard
    token_warnings = check_observation_token_literals(output)
    warnings.extend(token_warnings)

    # Trading vocabulary guard
    trading_warnings = check_trading_vocabulary(output)
    warnings.extend(trading_warnings)

    # Execution operation guard
    execution_warnings = check_execution_operations(output)
    warnings.extend(execution_warnings)

    # Address pattern guard
    address_warnings = check_address_patterns(output)
    warnings.extend(address_warnings)

    # Asset vocabulary guard
    asset_warnings = check_asset_vocabulary(output)
    warnings.extend(asset_warnings)

    # Action vocabulary guard
    action_warnings = check_action_vocabulary(output)
    warnings.extend(action_warnings)

    # Forbidden vocabulary guard
    vocab_warnings = check_forbidden_vocabulary(output)
    warnings.extend(vocab_warnings)

    # Numeric pattern guard (relaxed for labels/counts)
    numeric_warnings = check_numeric_patterns(output)
    # Filter out acceptable patterns (layer counts, warning counts)
    # Allow "N layers", "N warnings", but not "$X", "X%", etc.
    forbidden_numeric = [
        w
        for w in numeric_warnings
        if any(
            pattern in output
            for pattern in ["$", "USD", "fee", "price", "amount", "balance"]
        )
    ]
    warnings.extend(forbidden_numeric)

    # CLI instruction guard (NEW in PR118)
    instruction_warnings = check_cli_instruction(output)
    warnings.extend(instruction_warnings)

    return warnings


def check_cli_instruction(text: str) -> List[str]:
    """
    Check for CLI instruction patterns (NEW in PR118).

    Detects phrases that suggest CLI is providing instructions or recommendations.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # CLI instruction patterns
    # These phrases suggest CLI is instructing user
    instruction_patterns = [
        "you should execute",
        "you should trade",
        "you should swap",
        "you should sign",
        "you should submit",
        "recommended action: execute",
        "recommended action: trade",
        "recommended action: swap",
        "next step: execute",
        "next step: trade",
        "next step: swap",
        "proceed to execute",
        "proceed to trade",
        "proceed to swap",
        "cli recommends executing",
        "cli recommends trading",
        "cli suggests executing",
        "cli suggests trading",
    ]

    for pattern in instruction_patterns:
        if pattern in text_lower:
            warnings.append(f"CLI instruction detected: '{pattern}' in text")

    # Also check for instruction vocabulary near action verbs
    if any(
        phrase in text_lower
        for phrase in ["you should", "recommended action", "next step", "proceed to"]
    ):
        action_verbs = ["execute", "trade", "swap", "sign", "submit"]
        for verb in action_verbs:
            if verb in text_lower:
                warnings.append(
                    f"Possible CLI instruction: instruction phrase near '{verb}' in text"
                )
                break  # Only report once

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 CLI Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean CLI output
    print("Test 1: Clean CLI output")
    clean_output = """
Bundle Status: AVAILABLE

Regime Level: LOW
  Basis: entropy_classifier

Execution Permission: DRY_RUN_ONLY
  Basis: regime_level

Plan Type: MAINTENANCE
  Constraints: dry_run_only, read_only

Layers Present: 3
  REGIME, POLICY_BINDING, PLAN
"""
    clean_warnings = validate_cli_output(clean_output)
    print(f"Clean output warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty CLI output (trading vocabulary)
    print("Test 2: Dirty CLI output (trading vocabulary)")
    dirty_output_trading = """
Bundle Status: AVAILABLE
Regime Level: HIGH

Recommended action: execute swap operations immediately.
"""
    dirty_warnings = validate_cli_output(dirty_output_trading)
    print(f"Dirty output warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty CLI output (CLI instruction)
    print("Test 3: Dirty CLI output (CLI instruction)")
    dirty_output_instruction = """
Bundle Status: AVAILABLE
Regime Level: MEDIUM

Next step: execute the plan and sign the transaction.
"""
    dirty_warnings_instruction = validate_cli_output(dirty_output_instruction)
    print(f"Dirty output warnings: {len(dirty_warnings_instruction)}")
    if dirty_warnings_instruction:
        print("  Warnings:")
        for w in dirty_warnings_instruction:
            print(f"    - {w}")
    print()

    # Test 4: Dirty CLI output (token literals)
    print("Test 4: Dirty CLI output (token literals)")
    dirty_output_token = """
Bundle Status: AVAILABLE
Regime Level: LOW

Assets: SUI, USDC, BTC
Balance: 1000 USDC
"""
    dirty_warnings_token = validate_cli_output(dirty_output_token)
    print(f"Dirty output warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 5: Dirty CLI output (addresses)
    print("Test 5: Dirty CLI output (addresses)")
    dirty_output_address = """
Bundle Status: AVAILABLE
Wallet: 0x1234567890abcdef
"""
    dirty_warnings_address = validate_cli_output(dirty_output_address)
    print(f"Dirty output warnings: {len(dirty_warnings_address)}")
    if dirty_warnings_address:
        print("  Warnings:")
        for w in dirty_warnings_address:
            print(f"    - {w}")
    print()

    # Test 6: Clean CLI output with counts (acceptable)
    print("Test 6: Clean CLI output with counts (acceptable)")
    clean_counts_output = """
Bundle Status: AVAILABLE
Layers Present: 5
Warnings: 2
"""
    clean_counts_warnings = validate_cli_output(clean_counts_output)
    print(f"Clean counts output warnings: {len(clean_counts_warnings)}")
    if clean_counts_warnings:
        print(f"  Warnings: {clean_counts_warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
