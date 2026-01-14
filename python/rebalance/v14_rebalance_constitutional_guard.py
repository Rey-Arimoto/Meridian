#!/usr/bin/env python3
"""
PR151: v1.4 Rebalance Template Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on rebalance template records.
    Guards against token names, numeric ratios in text, prescriptive language, trading verbs, and coupling.

Constitutional Constraints:
    - No token names: No wBTC/USDC/SUI/ETH/BTC in text
    - No numeric ratios: No percentages or ratio text in free fields
    - No prescriptive language: No should/must/need to/recommend/advise
    - No trading verbs: No buy/sell/swap/execute/sign/transfer/bridge/order/trade
    - No causal coupling: No therefore/so/hence/means you should
    - Template ID is allowed to contain numbers (TPL_RISK_90 is OK)

Guards:
    1. Forbidden vocabulary guard (trading verbs + prescriptive words)
    2. Token name guard (wBTC/USDC/SUI/ETH/BTC/etc.)
    3. Coupling phrase guard (causal + template coupling)
    4. Numeric pattern guard (percentages in free text - template_id is exempt)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


# Reuse forbidden vocabulary
FORBIDDEN_TRADING_VERBS = [
    "buy",
    "sell",
    "swap",
    "execute",
    "sign",
    "transfer",
    "bridge",
    "order",
    "trade",
    "send",
    "broadcast",
    "submit",
    "rebalance",
]

FORBIDDEN_PRESCRIPTIVE_LANGUAGE = [
    "should",
    "must",
    "need to",
    "have to",
    "ought to",
    "require",
    "recommend",
    "suggest",
    "advise",
    "instruct",
]

FORBIDDEN_VOCABULARY = FORBIDDEN_TRADING_VERBS + FORBIDDEN_PRESCRIPTIVE_LANGUAGE

# Forbidden token names (case-insensitive)
FORBIDDEN_TOKEN_NAMES = [
    "wBTC",
    "WBTC",
    "USDC",
    "SUI",
    "ETH",
    "BTC",
    "DEEP",
    "CETUS",
    "SOL",
    "USDT",
]

# Causal coupling patterns
COUPLING_PATTERNS = [
    "therefore",
    "so",
    "hence",
    "means you can",
    "means you should",
    "implies you",
    "suggests you",
]

# Template coupling patterns (specific to PR151)
TEMPLATE_COUPLING_PATTERNS = [
    "template=",  # e.g., "template=TPL_RISK_90 therefore buy"
    "risk_90 so",
    "risk_0 so",
    "risk_50 so",
    "risk_20 so",
]


def check_forbidden_vocabulary(text: str) -> List[str]:
    """
    Check for forbidden vocabulary (trading verbs + prescriptive language).

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for word in FORBIDDEN_VOCABULARY:
        if word.lower() in text_lower:
            warnings.append(
                f"forbidden vocabulary detected: '{word}' "
                f"(rebalance records must not contain trading verbs or prescriptive language)"
            )

    return warnings


def check_token_names(text: str) -> List[str]:
    """
    Check for token name patterns.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_upper = text.upper()

    for token in FORBIDDEN_TOKEN_NAMES:
        if token.upper() in text_upper:
            warnings.append(
                f"token name detected: '{token}' "
                f"(rebalance records must not contain token names in text)"
            )

    return warnings


def check_coupling_phrases(text: str) -> List[str]:
    """
    Check for causal coupling phrases and template coupling.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    # Check standard coupling patterns
    for phrase in COUPLING_PATTERNS:
        if phrase.lower() in text_lower:
            warnings.append(
                f"coupling phrase detected: '{phrase}' "
                f"(rebalance records must not contain causal coupling language)"
            )

    # Check template-specific coupling patterns
    for phrase in TEMPLATE_COUPLING_PATTERNS:
        if phrase.lower() in text_lower:
            warnings.append(
                f"template coupling detected: '{phrase}' "
                f"(rebalance records must not couple template to action)"
            )

    return warnings


def check_numeric_ratios_in_text(text: str, field_name: str = "") -> List[str]:
    """
    Check for numeric ratio patterns in free text (percentages).
    Note: Template IDs (TPL_RISK_90) are allowed - this only checks free text fields.

    Args:
        text: Text to check
        field_name: Field name (for context)

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    # Skip if this is a template_id field (allowed to contain numbers)
    if field_name == "v14_rebalance_template_id":
        return warnings

    # Skip if this is a rule_id field (allowed to contain numbers)
    if field_name == "v14_rebalance_rule_id":
        return warnings

    # Skip if text is a known template ID (TPL_RISK_90, etc.)
    if text.startswith("TPL_"):
        return warnings

    # Skip if text is a known rule ID (RULE_*)
    if text.startswith("RULE_"):
        return warnings

    # Check for percentage patterns (e.g., 90%, 50%)
    if re.search(r'\d+%', text):
        warnings.append(
            f"numeric ratio detected in {field_name}: percentage "
            f"(rebalance text must not contain numeric ratios)"
        )

    # Check for ratio patterns (e.g., "90/10", "50:50")
    if re.search(r'\d+[/:][\d]+', text):
        warnings.append(
            f"numeric ratio detected in {field_name}: ratio pattern "
            f"(rebalance text must not contain numeric ratios)"
        )

    return warnings


def check_rebalance_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate rebalance record against constitutional guards.

    Args:
        record: Rebalance record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check warnings field (should be label-only, no token names or ratios)
    if "v14_rebalance_warnings" in record:
        warning_list = record["v14_rebalance_warnings"]
        if isinstance(warning_list, list):
            for warning in warning_list:
                if isinstance(warning, str):
                    # Check for token names in warnings
                    token_warnings = check_token_names(warning)
                    warnings.extend(token_warnings)

                    # Check for numeric ratios in warnings
                    ratio_warnings = check_numeric_ratios_in_text(warning, "warnings")
                    warnings.extend(ratio_warnings)

    # Check basis_labels (should be label-only)
    if "v14_rebalance_basis_labels" in record:
        basis_labels = record["v14_rebalance_basis_labels"]
        if isinstance(basis_labels, dict):
            for key, value in basis_labels.items():
                if isinstance(value, str):
                    # Check for token names
                    token_warnings = check_token_names(value)
                    warnings.extend(token_warnings)

                    # Check for forbidden vocabulary
                    vocab_warnings = check_forbidden_vocabulary(value)
                    warnings.extend(vocab_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Rebalance Template Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean record (no warnings)
    print("Test 1: Clean record (no warnings)")
    clean_record = {
        "v14_rebalance_template_id": "TPL_RISK_90",
        "v14_rebalance_rule_id": "RULE_UP_SHOCK",
        "v14_rebalance_basis_labels": {
            "shock_phase": "PHASE_UP_SHOCK",
            "stress": "STRESS_CALM",
        },
        "v14_rebalance_warnings": [],
    }
    clean_warnings = check_rebalance_record(clean_record)
    print(f"Clean record warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty text (token name)
    print("Test 2: Dirty text (token name)")
    dirty_text = "Rebalance to wBTC 90%."
    dirty_warnings = []
    dirty_warnings.extend(check_token_names(dirty_text))
    dirty_warnings.extend(check_numeric_ratios_in_text(dirty_text, "free_text"))
    print(f"Dirty text warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Template ID is allowed (contains numbers)
    print("Test 3: Template ID is allowed (contains numbers)")
    template_id = "TPL_RISK_90"
    template_warnings = check_numeric_ratios_in_text(template_id, "v14_rebalance_template_id")
    print(f"Template ID warnings: {len(template_warnings)}")
    if template_warnings:
        print(f"  Warnings: {template_warnings}")
    print()

    # Test 4: Dirty coupling
    print("Test 4: Dirty coupling")
    dirty_coupling = "template=TPL_RISK_90 therefore buy."
    dirty_warnings_coupling = []
    dirty_warnings_coupling.extend(check_coupling_phrases(dirty_coupling))
    dirty_warnings_coupling.extend(check_forbidden_vocabulary(dirty_coupling))
    print(f"Dirty coupling warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
