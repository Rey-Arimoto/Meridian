#!/usr/bin/env python3
"""
PR105: v1.0 Execution Audit Trail Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on audit trail records.
    Guards against violations of v1.0 audit trail principles.

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
    2. Execution safety guard (trading vocabulary)
    3. Token literal guard (token names)
    4. Numeric pattern guard (amounts/prices/addresses)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


def validate_v10_audit_trail_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate complete audit trail record against all constitutional guards.

    Args:
        record: Audit trail record to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import from existing constitutional guards
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
        check_execution_safety,
    )
    from execution.v10_plan_constitutional_guard import (
        check_token_literals,
        check_numeric_patterns,
    )

    warnings = []

    # Check audit summary
    if "v10_audit_summary" in record:
        summary = record["v10_audit_summary"]

        # Forbidden vocabulary
        vocab_warnings = check_forbidden_vocabulary(summary)
        warnings.extend(vocab_warnings)

        # Execution safety
        safety_warnings = check_execution_safety(summary)
        warnings.extend(safety_warnings)

        # Token literals
        token_warnings = check_token_literals(summary)
        warnings.extend(token_warnings)

        # Numeric patterns
        numeric_warnings = check_numeric_patterns(summary)
        warnings.extend(numeric_warnings)

    # Check chain events
    if "v10_audit_chain" in record:
        chain = record["v10_audit_chain"]
        if isinstance(chain, list):
            for event in chain:
                if isinstance(event, dict):
                    # Check layer name
                    if "layer" in event:
                        layer = event["layer"]
                        if isinstance(layer, str):
                            # Forbidden vocabulary in layer name
                            layer_vocab_warnings = check_forbidden_vocabulary(layer)
                            warnings.extend(layer_vocab_warnings)

                    # Check artifact identifier
                    if "artifact" in event:
                        artifact = event["artifact"]
                        if isinstance(artifact, str):
                            # Token literals in artifact name
                            artifact_token_warnings = check_token_literals(artifact)
                            warnings.extend(artifact_token_warnings)

                            # Numeric patterns in artifact name
                            artifact_numeric_warnings = check_numeric_patterns(artifact)
                            warnings.extend(artifact_numeric_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Execution Audit Trail Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test clean audit trail record
    print("Test 1: Clean audit trail record")
    clean_audit = {
        "v10_audit_summary": "audit trail built with multiple layers of causal chain.",
        "v10_audit_chain": [
            {
                "layer": "BLINDSPOT",
                "artifact": "pr81_blindspot_record",
                "basis": ["v8_blindspot_tag"]
            },
            {
                "layer": "PERMISSION",
                "artifact": "pr101_execution_record",
                "basis": ["v10_execution_permission"]
            }
        ],
    }

    clean_warnings = validate_v10_audit_trail_record(clean_audit)
    print(f"Clean audit trail warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test dirty audit trail record
    print("Test 2: Dirty audit trail record")
    dirty_audit = {
        "v10_audit_summary": "swap 100 SUI tokens at $2.50 - this is a good trade",
        "v10_audit_chain": [
            {
                "layer": "PERMISSION",
                "artifact": "execute_sui_transfer_to_0x123abc",
                "basis": []
            }
        ],
    }

    dirty_warnings = validate_v10_audit_trail_record(dirty_audit)
    print(f"Dirty audit trail warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
