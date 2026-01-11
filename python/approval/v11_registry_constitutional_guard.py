#!/usr/bin/env python3
"""
PR114: v1.1 Registry Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on registry records.
    Guards against trading vocabulary, execution operations, and instructional coupling.

Constitutional Constraints:
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution vocabulary: No transaction, broadcast, submit
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No 0x... patterns
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad, profitable/unprofitable vocabulary
    - Non-prescriptive: No should/must recommendations
    - Registry-specific: No "instructional coupling" phrases
    - APPROVED must not be described as instruction

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
    10. Instructional coupling guard (NEW in PR114)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def validate_registry_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate registry record against all constitutional guards.

    Args:
        record: Registry record to validate

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
    from approval.v11_approval_constitutional_guard import (
        check_approval_specific_vocabulary,
    )

    warnings = []

    # Check registry summary
    if "v11_registry_summary" in record:
        summary = record["v11_registry_summary"]

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

        # Instructional coupling guard (NEW in PR114)
        coupling_warnings = check_instructional_coupling(summary)
        warnings.extend(coupling_warnings)

    # Check error info (if present)
    if "v11_registry_error_info" in record:
        error_info = record["v11_registry_error_info"]
        if isinstance(error_info, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(error_info)
            warnings.extend(token_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(error_info)
            warnings.extend(trading_warnings)

    return warnings


def check_instructional_coupling(text: str) -> List[str]:
    """
    Check for instructional coupling phrases (NEW in PR114).

    Detects phrases that couple APPROVED state to execution instructions.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    # Instructional coupling patterns
    # These phrases couple "approved" to execution verbs
    coupling_patterns = [
        "approved therefore execute",
        "approved so execute",
        "approved so proceed",
        "approved therefore proceed",
        "approved so run",
        "approved therefore run",
        "approved so submit",
        "approved therefore submit",
        "approved so sign",
        "approved therefore sign",
        "approval granted, run",
        "approval granted, execute",
        "approval granted, proceed",
        "approval granted, submit",
        "approval granted, sign",
    ]

    for pattern in coupling_patterns:
        if pattern in text_lower:
            warnings.append(f"Instructional coupling detected: '{pattern}' in text")

    # Also check for "approved" + execution verb proximity (simplified check)
    if "approved" in text_lower:
        execution_verbs = ["execute", "proceed", "run", "submit", "sign", "trade", "swap"]
        for verb in execution_verbs:
            # Check if execution verb appears near "approved"
            # Simple proximity check: within same sentence (rough approximation)
            if verb in text_lower:
                # More sophisticated check: look for "approved" followed by verb within 50 chars
                approved_pos = text_lower.find("approved")
                verb_pos = text_lower.find(verb)
                if approved_pos >= 0 and verb_pos >= 0 and abs(approved_pos - verb_pos) < 50:
                    warnings.append(f"Possible instructional coupling: 'approved' near '{verb}' in text")
                    break  # Only report once

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.1 Registry Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean registry record
    print("Test 1: Clean registry record")
    clean_registry = {
        "v11_registry_summary": "approval request recorded. registry state set to requested.",
    }
    clean_warnings = validate_registry_record(clean_registry)
    print(f"Clean registry warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty registry (trading vocabulary)
    print("Test 2: Dirty registry (trading vocabulary)")
    dirty_registry_trading = {
        "v11_registry_summary": "approval granted. execute swap operations.",
    }
    dirty_warnings = validate_registry_record(dirty_registry_trading)
    print(f"Dirty registry warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty registry (instructional coupling - explicit)
    print("Test 3: Dirty registry (instructional coupling - explicit)")
    dirty_registry_coupling = {
        "v11_registry_summary": "approval granted, proceed with execution.",
    }
    dirty_warnings_coupling = validate_registry_record(dirty_registry_coupling)
    print(f"Dirty registry warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 4: Dirty registry (instructional coupling - proximity)
    print("Test 4: Dirty registry (instructional coupling - proximity)")
    dirty_registry_proximity = {
        "v11_registry_summary": "state approved so execute plan.",
    }
    dirty_warnings_proximity = validate_registry_record(dirty_registry_proximity)
    print(f"Dirty registry warnings: {len(dirty_warnings_proximity)}")
    if dirty_warnings_proximity:
        print("  Warnings:")
        for w in dirty_warnings_proximity:
            print(f"    - {w}")
    print()

    # Test 5: Dirty registry (token literals)
    print("Test 5: Dirty registry (token literals)")
    dirty_registry_token = {
        "v11_registry_summary": "approval for SUI and USDC operations.",
    }
    dirty_warnings_token = validate_registry_record(dirty_registry_token)
    print(f"Dirty registry warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token:
            print(f"    - {w}")
    print()

    # Test 6: Dirty registry (numeric patterns)
    print("Test 6: Dirty registry (numeric patterns)")
    dirty_registry_numeric = {
        "v11_registry_summary": "approval for $1000 transaction at 5% fee.",
    }
    dirty_warnings_numeric = validate_registry_record(dirty_registry_numeric)
    print(f"Dirty registry warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 7: Clean registry with "approved" (label only)
    print("Test 7: Clean registry with 'approved' (label only)")
    clean_approved_registry = {
        "v11_registry_summary": "approval state recorded as approved. this is a state label only.",
    }
    clean_approved_warnings = validate_registry_record(clean_approved_registry)
    print(f"Clean approved registry warnings: {len(clean_approved_warnings)}")
    if clean_approved_warnings:
        print(f"  Warnings: {clean_approved_warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
