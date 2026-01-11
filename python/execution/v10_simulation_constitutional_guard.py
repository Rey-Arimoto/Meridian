#!/usr/bin/env python3
"""
PR104: v1.0 Execution Simulation Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on simulation records.
    Guards against violations of v1.0 simulation principles.

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


def validate_v10_simulation_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate complete simulation record against all constitutional guards.

    Args:
        record: Simulation record to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import from existing constitutional guards
    from .v10_constitutional_guard import (
        check_forbidden_vocabulary,
        check_execution_safety,
    )
    from .v10_plan_constitutional_guard import (
        check_token_literals,
        check_numeric_patterns,
    )

    warnings = []

    # Check simulation type vocabulary
    if "v10_simulation_type" in record:
        type_warnings = check_forbidden_vocabulary(record["v10_simulation_type"])
        warnings.extend(type_warnings)

    # Check simulation summary
    if "v10_simulation_summary" in record:
        summary = record["v10_simulation_summary"]

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

    # Check trace events
    if "v10_simulation_trace" in record:
        trace = record["v10_simulation_trace"]
        if isinstance(trace, list):
            for event in trace:
                if isinstance(event, dict) and "event_summary" in event:
                    event_summary = event["event_summary"]

                    # Forbidden vocabulary
                    event_vocab_warnings = check_forbidden_vocabulary(event_summary)
                    warnings.extend(event_vocab_warnings)

                    # Execution safety
                    event_safety_warnings = check_execution_safety(event_summary)
                    warnings.extend(event_safety_warnings)

                    # Token literals
                    event_token_warnings = check_token_literals(event_summary)
                    warnings.extend(event_token_warnings)

                    # Numeric patterns
                    event_numeric_warnings = check_numeric_patterns(event_summary)
                    warnings.extend(event_numeric_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Execution Simulation Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test clean simulation record
    print("Test 1: Clean simulation record")
    clean_sim = {
        "v10_simulation_type": "PLAN_APPLICABILITY_SCAN",
        "v10_simulation_summary": "plan applicability scan complete.",
        "v10_simulation_trace": [
            {
                "event_type": "CONSTRAINT_APPLIED",
                "event_summary": "dry-run-only constraint applied.",
                "event_basis": ["v10_plan_constraints"]
            }
        ],
    }

    clean_warnings = validate_v10_simulation_record(clean_sim)
    print(f"Clean simulation warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test dirty simulation record
    print("Test 2: Dirty simulation record")
    dirty_sim = {
        "v10_simulation_type": "PLAN_APPLICABILITY_SCAN",
        "v10_simulation_summary": "swap 100 SUI tokens at $2.50 price - this is a good opportunity",
        "v10_simulation_trace": [
            {
                "event_type": "CONSTRAINT_APPLIED",
                "event_summary": "execute transfer to 0x123abc",
                "event_basis": ["v10_plan_constraints"]
            }
        ],
    }

    dirty_warnings = validate_v10_simulation_record(dirty_sim)
    print(f"Dirty simulation warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
