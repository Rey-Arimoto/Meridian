#!/usr/bin/env python3
"""
PR113: v1.1 Approval Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on approval records.
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
    - Approval-specific: No "go ahead", "proceed", "continue"
    - APPROVED must not be described as an instruction

Guards:
    1. Trading vocabulary guard (swap, buy, sell, execute, sign, transfer)
    2. Execution operation guard (transaction, broadcast, submit)
    3. Token literal guard (token names)
    4. Address pattern guard (0x...)
    5. Asset vocabulary guard (balance, holdings, portfolio)
    6. Action vocabulary guard (recommend, suggest, optimize)
    7. Forbidden vocabulary guard (evaluative/prescriptive)
    8. Numeric pattern guard (amounts, prices, percentages)
    9. Approval-specific guard (go ahead, proceed, instruction)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def validate_approval_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate approval record against all constitutional guards.

    Args:
        record: Approval record to validate

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

    # Check approval summary
    if "v11_approval_summary" in record:
        summary = record["v11_approval_summary"]

        # Trading vocabulary guard
        trading_warnings = check_trading_vocabulary(summary)
        warnings.extend(trading_warnings)

        # Execution operation guard
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

        # Approval-specific guard
        approval_warnings = check_approval_specific_vocabulary(summary)
        warnings.extend(approval_warnings)

    # Check error info (if present)
    if "v11_approval_error_info" in record:
        error_info = record["v11_approval_error_info"]
        if isinstance(error_info, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(error_info)
            warnings.extend(token_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(error_info)
            warnings.extend(trading_warnings)

    return warnings


def check_approval_specific_vocabulary(text: str) -> List[str]:
    """
    Check for approval-specific forbidden vocabulary.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # Approval-specific forbidden terms
    # These make approval sound like an instruction/recommendation
    approval_terms = [
        "go ahead",
        "proceed",
        "continue",
        "you should",
        "you must",
        "recommended to",
        "advised to",
        "instruction",
        "instruct",
        "command",
    ]

    for term in approval_terms:
        if term in text_lower:
            warnings.append(f"Approval-specific forbidden vocabulary detected: '{term}' in text")

    # Check for "approved" used as instruction
    # Valid: "approval state approved" or "approved state"
    # Invalid: "you are approved to", "approved for execution"
    if "approved to" in text_lower or "approved for" in text_lower:
        warnings.append("APPROVED used as instruction detected in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.1 Approval Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean approval record
    print("Test 1: Clean approval record")
    clean_approval = {
        "v11_approval_summary": "approval required under critical regime conditions. no approval requested.",
    }
    clean_warnings = validate_approval_record(clean_approval)
    print(f"Clean approval warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty approval (trading vocabulary)
    print("Test 2: Dirty approval (trading vocabulary)")
    dirty_approval_trading = {
        "v11_approval_summary": "approval granted. proceed to execute swap operations.",
    }
    dirty_warnings = validate_approval_record(dirty_approval_trading)
    print(f"Dirty approval warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty approval (approval-specific vocabulary)
    print("Test 3: Dirty approval (approval-specific vocabulary)")
    dirty_approval_specific = {
        "v11_approval_summary": "approval granted. go ahead and proceed with execution.",
    }
    dirty_warnings_specific = validate_approval_record(dirty_approval_specific)
    print(f"Dirty approval warnings: {len(dirty_warnings_specific)}")
    if dirty_warnings_specific:
        print("  Warnings:")
        for w in dirty_warnings_specific:
            print(f"    - {w}")
    print()

    # Test 4: Dirty approval (APPROVED as instruction)
    print("Test 4: Dirty approval (APPROVED as instruction)")
    dirty_approval_instruction = {
        "v11_approval_summary": "you are approved to execute this trade.",
    }
    dirty_warnings_instruction = validate_approval_record(dirty_approval_instruction)
    print(f"Dirty approval warnings: {len(dirty_warnings_instruction)}")
    if dirty_warnings_instruction:
        print("  Warnings:")
        for w in dirty_warnings_instruction:
            print(f"    - {w}")
    print()

    # Test 5: Dirty approval (token literals)
    print("Test 5: Dirty approval (token literals)")
    dirty_approval_token = {
        "v11_approval_summary": "approval for SUI and USDC operations.",
    }
    dirty_warnings_token = validate_approval_record(dirty_approval_token)
    print(f"Dirty approval warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 6: Dirty approval (numeric patterns)
    print("Test 6: Dirty approval (numeric patterns)")
    dirty_approval_numeric = {
        "v11_approval_summary": "approval for $1000 transaction at 5% fee.",
    }
    dirty_warnings_numeric = validate_approval_record(dirty_approval_numeric)
    print(f"Dirty approval warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 7: Dirty approval (action vocabulary)
    print("Test 7: Dirty approval (action vocabulary)")
    dirty_approval_action = {
        "v11_approval_summary": "recommend proceeding with optimized execution plan.",
    }
    dirty_warnings_action = validate_approval_record(dirty_approval_action)
    print(f"Dirty approval warnings: {len(dirty_warnings_action)}")
    if dirty_warnings_action:
        print("  Warnings:")
        for w in dirty_warnings_action:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
