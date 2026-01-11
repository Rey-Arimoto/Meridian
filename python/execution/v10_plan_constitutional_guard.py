#!/usr/bin/env python3
"""
PR102: v1.0 Execution Plan Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on execution plan records.
    Guards against violations of v1.0 plan principles.

Constitutional Constraints:
    - READ-ONLY: No execution logic or trading
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - No amounts: No numeric values, prices, quantities
    - No token literals: No SUI, USDC, BTC, etc.
    - No addresses: No wallet/contract addresses
    - Execution safety: No trading vocabulary

Guards:
    1. Forbidden vocabulary (evaluative/scoric/prescriptive)
    2. Execution safety guard (no trading vocabulary)
    3. Token literal guard (no SUI, USDC, BTC, etc.)
    4. Numeric pattern guard (no amounts, prices, addresses)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


# ============================================================================
# Token Literal Guard (v1.0 NEW for Plans)
# ============================================================================

TOKEN_LITERALS = [
    # Major tokens
    "sui",
    "usdc",
    "usdt",
    "btc",
    "eth",
    "sol",
    "bnb",
    "xrp",
    "ada",
    "doge",
    # DeFi tokens
    "uni",
    "aave",
    "link",
    "dai",
    "wbtc",
    "weth",
    # Stablecoins
    "busd",
    "tusd",
    "usdp",
    "frax",
]


def check_token_literals(text: str) -> List[str]:
    """
    Check if text contains token literal names.

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if clean)
    """
    warnings = []
    text_lower = text.lower()

    for token in TOKEN_LITERALS:
        # Use word boundaries to avoid false positives
        pattern = r'\b' + re.escape(token) + r'\b'
        if re.search(pattern, text_lower):
            warnings.append(f"Token literal detected: '{token}' in text")

    return warnings


# ============================================================================
# Numeric Pattern Guard (v1.0 NEW for Plans)
# ============================================================================

def check_numeric_patterns(text: str) -> List[str]:
    """
    Check if text contains numeric patterns (amounts, prices, addresses).

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if clean)
    """
    warnings = []

    # Pattern 1: Numeric values that look like amounts or prices
    # e.g., "1000", "0.5", "1.234", "$100", "100 SUI"
    amount_pattern = r'\b\d+\.?\d*\b'
    if re.search(amount_pattern, text):
        warnings.append("Numeric pattern detected in text (possible amount or price)")

    # Pattern 2: Hex addresses (0x followed by hex digits)
    address_pattern = r'0x[0-9a-fA-F]{4,}'
    if re.search(address_pattern, text):
        warnings.append("Address pattern detected in text (0x...)")

    # Pattern 3: Price-like patterns ($, €, ¥)
    price_pattern = r'[\$€¥]'
    if re.search(price_pattern, text):
        warnings.append("Currency symbol detected in text")

    return warnings


# ============================================================================
# Complete Plan Record Validation
# ============================================================================

def validate_plan_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate complete plan record against all constitutional guards.

    Args:
        record: Plan record to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import from main constitutional guard
    from .v10_constitutional_guard import (
        check_forbidden_vocabulary,
        check_execution_safety,
    )

    warnings = []

    # Check plan type vocabulary
    if "v10_plan_type" in record:
        plan_type_warnings = check_forbidden_vocabulary(record["v10_plan_type"])
        warnings.extend(plan_type_warnings)

    # Check plan description vocabulary
    if "v10_plan_description" in record:
        description = record["v10_plan_description"]

        # Forbidden vocabulary
        vocab_warnings = check_forbidden_vocabulary(description)
        warnings.extend(vocab_warnings)

        # Execution safety
        safety_warnings = check_execution_safety(description)
        warnings.extend(safety_warnings)

        # Token literals
        token_warnings = check_token_literals(description)
        warnings.extend(token_warnings)

        # Numeric patterns
        numeric_warnings = check_numeric_patterns(description)
        warnings.extend(numeric_warnings)

    # Check plan constraints
    if "v10_plan_constraints" in record:
        constraints = record["v10_plan_constraints"]
        if isinstance(constraints, list):
            for constraint in constraints:
                if isinstance(constraint, str):
                    # Forbidden vocabulary
                    constraint_vocab_warnings = check_forbidden_vocabulary(constraint)
                    warnings.extend(constraint_vocab_warnings)

                    # Token literals
                    constraint_token_warnings = check_token_literals(constraint)
                    warnings.extend(constraint_token_warnings)

                    # Numeric patterns
                    constraint_numeric_warnings = check_numeric_patterns(constraint)
                    warnings.extend(constraint_numeric_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Execution Plan Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test token literals
    print("Test 1: Token literals")
    clean_text = "plan type is rebalance"
    dirty_text = "swap SUI for USDC"

    clean_warnings = check_token_literals(clean_text)
    dirty_warnings = check_token_literals(dirty_text)

    print(f"Clean text: '{clean_text}'")
    print(f"  Warnings: {len(clean_warnings)}")
    print(f"Dirty text: '{dirty_text}'")
    print(f"  Warnings: {len(dirty_warnings)} - {dirty_warnings}")
    print()

    # Test numeric patterns
    print("Test 2: Numeric patterns")
    clean_numeric_text = "plan is available"
    dirty_numeric_text = "swap 1000 tokens at price 0.5"

    clean_numeric_warnings = check_numeric_patterns(clean_numeric_text)
    dirty_numeric_warnings = check_numeric_patterns(dirty_numeric_text)

    print(f"Clean text: '{clean_numeric_text}'")
    print(f"  Warnings: {len(clean_numeric_warnings)}")
    print(f"Dirty text: '{dirty_numeric_text}'")
    print(f"  Warnings: {len(dirty_numeric_warnings)} - {dirty_numeric_warnings}")
    print()

    # Test complete plan record
    print("Test 3: Complete plan record")
    clean_plan = {
        "v10_plan_type": "MAINTENANCE",
        "v10_plan_description": "maintenance plan available.",
        "v10_plan_constraints": ["dry_run_only"],
    }

    dirty_plan = {
        "v10_plan_type": "REBALANCE",
        "v10_plan_description": "swap 100 SUI for USDC at $2.50 price",
        "v10_plan_constraints": ["execute immediately"],
    }

    clean_plan_warnings = validate_plan_record(clean_plan)
    dirty_plan_warnings = validate_plan_record(dirty_plan)

    print(f"Clean plan warnings: {len(clean_plan_warnings)}")
    print(f"Dirty plan warnings: {len(dirty_plan_warnings)}")
    if dirty_plan_warnings:
        print(f"  Warnings: {dirty_plan_warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
