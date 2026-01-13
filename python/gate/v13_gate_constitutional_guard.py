#!/usr/bin/env python3
"""
PR143: v1.3 Gate Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on execution gate records.
    Guards against prescriptive language, action vocabulary, and allow states.

Constitutional Constraints:
    - No prescriptive language: No should/must/need to
    - No causal coupling: No "therefore execute", "approved so", etc.
    - No action/trading vocabulary: No execute/sign/transfer/swap/buy/sell/bridge
    - No token literals: No SUI/USDC/BTC/ETH
    - No numeric patterns: No amounts, no 0x addresses
    - No allow states: No "ALLOW", "READY", "PERMITTED" in gate_state
    - Gate must always be BLOCKED

Guards:
    1. Prescriptive language guard (reuse from draft)
    2. Action vocabulary guard (trading verbs)
    3. Token literal guard (reuse from draft)
    4. Address pattern guard (reuse from draft)
    5. Gate coupling guard (NEW: approval/gate → execution patterns)
    6. Gate state guard (NEW: must be BLOCKED, never ALLOW)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


# Forbidden prescriptive language (reuse from draft)
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
]

# Forbidden action/trading vocabulary
FORBIDDEN_ACTION_VOCABULARY = [
    "execute",
    "sign",
    "transfer",
    "swap",
    "buy",
    "sell",
    "bridge",
    "send",
    "broadcast",
    "submit",
    "approve",  # In execution context
    "trade",
]

# Forbidden token literals (reuse from draft)
FORBIDDEN_TOKEN_LITERALS = ["SUI", "USDC", "BTC", "ETH", "DEEP", "CETUS"]

# Gate-specific causal coupling patterns
# Pattern: (condition_label, coupling_word)
GATE_COUPLING_PATTERNS = [
    # Gate → action
    ("gate", "therefore"),
    ("gate", "so"),
    ("gate", "means"),
    ("blocked", "therefore"),
    ("blocked", "so"),
    # Approval → execution
    ("approved", "execute"),
    ("approved", "proceed"),
    ("approved", "trade"),
    # Ready → action
    ("ready", "execute"),
    ("ready", "proceed"),
    ("ready", "trade"),
    # Allow → action
    ("allow", "execute"),
    ("allow", "proceed"),
    ("allow", "trade"),
    ("permitted", "execute"),
    ("permitted", "proceed"),
]

# Forbidden allow states (gate must always be BLOCKED)
FORBIDDEN_ALLOW_STATES = [
    "ALLOW",
    "ALLOWED",
    "PERMITTED",
    "READY",
    "EXECUTABLE",
    "APPROVED",
]


def check_prescriptive_language(text: str) -> List[str]:
    """
    Check for prescriptive language.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for word in FORBIDDEN_PRESCRIPTIVE_LANGUAGE:
        if word.lower() in text_lower:
            warnings.append(
                f"prescriptive language detected: '{word}' "
                f"(gate records must be descriptive only)"
            )

    return warnings


def check_action_vocabulary(text: str) -> List[str]:
    """
    Check for action/trading vocabulary.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for word in FORBIDDEN_ACTION_VOCABULARY:
        if word.lower() in text_lower:
            warnings.append(
                f"action vocabulary detected: '{word}' "
                f"(gate records must not contain action verbs)"
            )

    return warnings


def check_token_literals(text: str) -> List[str]:
    """
    Check for token literal patterns.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_upper = text.upper()

    for token in FORBIDDEN_TOKEN_LITERALS:
        if token in text_upper:
            warnings.append(
                f"token literal detected: '{token}' "
                f"(gate records must not contain token literals)"
            )

    return warnings


def check_address_patterns(text: str) -> List[str]:
    """
    Check for address patterns (0x...).

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    # Check for 0x followed by hex characters
    if "0x" in text.lower():
        warnings.append(
            "address pattern detected: '0x...' "
            "(gate records must not contain addresses)"
        )

    return warnings


def check_gate_coupling(text: str) -> List[str]:
    """
    Check for gate-specific causal coupling patterns.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for condition_label, coupling_word in GATE_COUPLING_PATTERNS:
        # Check if both appear in text (may not be adjacent, but proximity is suspicious)
        if condition_label.lower() in text_lower and coupling_word.lower() in text_lower:
            warnings.append(
                f"gate causal coupling detected: '{condition_label}' with '{coupling_word}' "
                f"(may indicate prescriptive coupling in gate)"
            )

    return warnings


def check_gate_state_blocked(gate_state: str) -> List[str]:
    """
    Check that gate_state is BLOCKED (never ALLOW).

    Args:
        gate_state: Gate state to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(gate_state, str):
        warnings.append(
            f"gate_state is not string: {type(gate_state).__name__} "
            f"(must be BLOCKED)"
        )
        return warnings

    gate_state_upper = gate_state.upper()

    # Check that gate is BLOCKED
    if gate_state_upper != "BLOCKED":
        warnings.append(
            f"gate_state is not BLOCKED: '{gate_state}' "
            f"(gate must always be BLOCKED, never ALLOW)"
        )

    # Check for forbidden allow states
    for forbidden in FORBIDDEN_ALLOW_STATES:
        if forbidden in gate_state_upper:
            warnings.append(
                f"forbidden allow state detected: '{forbidden}' in gate_state "
                f"(gate must never contain ALLOW/PERMITTED/READY states)"
            )

    return warnings


def check_gate_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate gate record against constitutional guards.

    Args:
        record: Gate record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check summary
    if "v13_gate_summary" in record:
        summary = record["v13_gate_summary"]
        if isinstance(summary, str):
            # Check for prescriptive language
            prescriptive_warnings = check_prescriptive_language(summary)
            warnings.extend(prescriptive_warnings)

            # Check for action vocabulary
            action_warnings = check_action_vocabulary(summary)
            warnings.extend(action_warnings)

            # Check for token literals
            token_warnings = check_token_literals(summary)
            warnings.extend(token_warnings)

            # Check for address patterns
            address_warnings = check_address_patterns(summary)
            warnings.extend(address_warnings)

            # Check for gate coupling
            coupling_warnings = check_gate_coupling(summary)
            warnings.extend(coupling_warnings)

    # Check notes (if present)
    if "v13_gate_notes" in record:
        notes = record["v13_gate_notes"]
        if isinstance(notes, str):
            # Apply same guards to notes
            prescriptive_warnings = check_prescriptive_language(notes)
            warnings.extend(prescriptive_warnings)

            action_warnings = check_action_vocabulary(notes)
            warnings.extend(action_warnings)

            token_warnings = check_token_literals(notes)
            warnings.extend(token_warnings)

            address_warnings = check_address_patterns(notes)
            warnings.extend(address_warnings)

            coupling_warnings = check_gate_coupling(notes)
            warnings.extend(coupling_warnings)

    # Check gate_state (MUST be BLOCKED)
    if "v13_gate_gate_state" in record:
        gate_state = record["v13_gate_gate_state"]
        state_warnings = check_gate_state_blocked(gate_state)
        warnings.extend(state_warnings)

    # Check block_reasons (should not contain action verbs)
    if "v13_gate_block_reasons" in record:
        block_reasons = record["v13_gate_block_reasons"]
        if isinstance(block_reasons, list):
            block_reasons_str = " ".join(str(r) for r in block_reasons)
            # Check for action vocabulary in reasons
            action_warnings = check_action_vocabulary(block_reasons_str)
            warnings.extend(action_warnings)

    # Check reason_details (should not contain token literals or action verbs)
    if "v13_gate_reason_details" in record:
        reason_details = record["v13_gate_reason_details"]
        if isinstance(reason_details, list):
            details_str = str(reason_details)
            # Check for token literals
            token_warnings = check_token_literals(details_str)
            warnings.extend(token_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.3 Gate Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean gate record (no warnings)
    print("Test 1: Clean gate record (no warnings)")
    clean_gate = {
        "v13_gate_summary": "execution gate produced. state blocked. reasons enumerated.",
        "v13_gate_gate_state": "BLOCKED",
        "v13_gate_block_reasons": ["REASON_SIMULATION_ONLY", "REASON_NO_EXECUTION_LOGIC"],
    }
    clean_warnings = check_gate_record(clean_gate)
    print(f"Clean gate warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty gate (prescriptive language)
    print("Test 2: Dirty gate (prescriptive language)")
    dirty_prescriptive = {
        "v13_gate_summary": "System should execute trade operation.",
        "v13_gate_gate_state": "BLOCKED",
    }
    dirty_warnings = check_gate_record(dirty_prescriptive)
    print(f"Dirty gate warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty gate (action vocabulary)
    print("Test 3: Dirty gate (action vocabulary)")
    dirty_action = {
        "v13_gate_summary": "Gate approved therefore execute swap.",
        "v13_gate_gate_state": "BLOCKED",
    }
    dirty_warnings_action = check_gate_record(dirty_action)
    print(f"Dirty gate warnings: {len(dirty_warnings_action)}")
    if dirty_warnings_action:
        print("  Warnings:")
        for w in dirty_warnings_action:
            print(f"    - {w}")
    print()

    # Test 4: Dirty gate (forbidden allow state)
    print("Test 4: Dirty gate (forbidden allow state)")
    dirty_allow = {
        "v13_gate_summary": "execution gate produced.",
        "v13_gate_gate_state": "ALLOWED",  # FORBIDDEN
    }
    dirty_warnings_allow = check_gate_record(dirty_allow)
    print(f"Dirty gate warnings: {len(dirty_warnings_allow)}")
    if dirty_warnings_allow:
        print("  Warnings:")
        for w in dirty_warnings_allow:
            print(f"    - {w}")
    print()

    # Test 5: Dirty gate (token literals)
    print("Test 5: Dirty gate (token literals)")
    dirty_token = {
        "v13_gate_summary": "gate blocked: SUI and USDC amounts missing.",
        "v13_gate_gate_state": "BLOCKED",
    }
    dirty_warnings_token = check_gate_record(dirty_token)
    print(f"Dirty gate warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
