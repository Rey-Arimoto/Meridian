#!/usr/bin/env python3
"""
PR137: v1.2 Rescue Flow Graph Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on rescue flow graph records.
    Guards against numeric patterns, token literals, trading vocabulary,
    prescriptive language, and flow coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No numeric patterns: No digits, %, decimals
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - NEW: No flow coupling: No "this edge means execute", "strong rescue therefore trade"

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


# Flow coupling pattern (NEW in PR137)
FLOW_COUPLING_RE = re.compile(
    r"\b(edge|flow|graph|node|rescue)\\b.{0,40}\\b(therefore|so|thus|hence|then|means|implies)\\b.{0,40}\\b(act|execute|proceed|touch|trade|swap|buy|sell|sign|transfer|broadcast)\\b",
    re.IGNORECASE | re.DOTALL,
)


def check_flow_graph_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate flow graph record against constitutional guards.

    Args:
        record: Flow graph record to validate

    Returns:
        List of warnings (empty if valid)
    """
    # Import existing guards
    from observation.v10_observation_constitutional_guard import (
        check_observation_token_literals,
    )
    from drift.v10_drift_constitutional_guard import (
        check_drift_numeric_patterns,
    )
    from preview.v11_preview_constitutional_guard import (
        check_trading_vocabulary,
        check_execution_operations,
        check_address_patterns,
    )
    from execution.v10_constitutional_guard import (
        check_forbidden_vocabulary,
    )
    from policy.v10_drift_policy_constitutional_guard import (
        check_prescriptive_language,
    )

    warnings = []

    # Check flow summary
    if "v12_flow_summary" in record:
        summary = record["v12_flow_summary"]
        if isinstance(summary, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(summary)
            warnings.extend(token_warnings)

            # Numeric pattern guard
            numeric_warnings = check_drift_numeric_patterns(summary)
            warnings.extend(numeric_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(summary)
            warnings.extend(trading_warnings)

            # Execution operation guard
            execution_warnings = check_execution_operations(summary)
            warnings.extend(execution_warnings)

            # Address pattern guard
            address_warnings = check_address_patterns(summary)
            warnings.extend(address_warnings)

            # Forbidden vocabulary guard
            vocab_warnings = check_forbidden_vocabulary(summary)
            warnings.extend(vocab_warnings)

            # Prescriptive language guard
            prescriptive_warnings = check_prescriptive_language(summary)
            warnings.extend(prescriptive_warnings)

            # Flow coupling guard (NEW)
            coupling_warnings = check_flow_coupling(summary)
            warnings.extend(coupling_warnings)

    # Check flow edges for coupling
    if "v12_flow_edges" in record:
        edges = record["v12_flow_edges"]
        if isinstance(edges, list):
            for edge in edges:
                if isinstance(edge, dict) and "note" in edge:
                    note = edge["note"]
                    if isinstance(note, str):
                        # Flow coupling guard
                        coupling_warnings = check_flow_coupling(note)
                        warnings.extend(coupling_warnings)

                        # Token literals guard
                        token_warnings = check_observation_token_literals(note)
                        warnings.extend(token_warnings)

                        # Numeric pattern guard
                        numeric_warnings = check_drift_numeric_patterns(note)
                        warnings.extend(numeric_warnings)

    # Check flow warnings field
    if "v12_flow_warnings" in record:
        flow_warnings = record["v12_flow_warnings"]
        if isinstance(flow_warnings, list):
            for warning in flow_warnings:
                if isinstance(warning, str):
                    # Token literals guard
                    token_warnings = check_observation_token_literals(warning)
                    warnings.extend(token_warnings)

                    # Numeric pattern guard
                    numeric_warnings = check_drift_numeric_patterns(warning)
                    warnings.extend(numeric_warnings)

    return warnings


def check_flow_coupling(text: str) -> List[str]:
    """
    Check for flow coupling patterns (NEW in PR137).

    Detects:
        - "this edge means execute"
        - "strong rescue therefore trade"
        - "flow graph therefore act"
        - Flow coupling to action

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Flow element + action coupling
    if FLOW_COUPLING_RE.search(text):
        warnings.append("Flow coupling detected (flow element therefore act).")

    # Pattern 2: Direct flow element + action proximity
    flow_action_patterns = [
        r'\\b(edge|flow|graph|node|rescue|strong|medium|weak)\\b.{0,30}\\b(touch|execute|trade|swap|buy|sell|proceed|act)\\b',
        r'\\b(this edge|this flow|this graph)\\b.{0,30}\\b(therefore|so|thus|means|implies)\\b.{0,30}\\b(action|execute|proceed)\\b',
    ]

    for pattern in flow_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Flow-action proximity detected: '{pattern}' in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Rescue Flow Graph Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean flow graph record (no warnings)
    print("Test 1: Clean flow graph record (no warnings)")
    clean_record = {
        "v12_flow_summary": "Rescue flow graph available. Role nodes and rescue edges assembled as structural mapping.",
        "v12_flow_edges": [
            {
                "from_role": "STABILITY_ROLE",
                "to_role": "VOLATILITY_ROLE",
                "edge_type": "EDGE_SHIELD",
                "rescue_strength": "RESCUE_MEDIUM",
                "conditions": ["REGIME_MEDIUM", "D1_LIQUIDATION"],
                "note": "Stability provides shielding support to volatility role",
            }
        ],
    }
    clean_warnings = check_flow_graph_record(clean_record)
    print(f"Clean record warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty flow graph record (numeric patterns)
    print("Test 2: Dirty flow graph record (numeric patterns)")
    dirty_numeric = {
        "v12_flow_summary": "Flow graph expected to yield 30% improvement.",
    }
    dirty_warnings = check_flow_graph_record(dirty_numeric)
    print(f"Dirty record warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings[:2]:
            print(f"    - {w}")
    print()

    # Test 3: Dirty flow graph record (flow coupling)
    print("Test 3: Dirty flow graph record (flow coupling)")
    dirty_coupling = {
        "v12_flow_summary": "This edge therefore execute trade.",
    }
    dirty_warnings_coupling = check_flow_graph_record(dirty_coupling)
    print(f"Dirty record warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 4: Dirty flow graph record (strong rescue means proceed)
    print("Test 4: Dirty flow graph record (strong rescue means proceed)")
    dirty_means = {
        "v12_flow_summary": "Strong rescue means proceed with swap.",
    }
    dirty_warnings_means = check_flow_graph_record(dirty_means)
    print(f"Dirty record warnings: {len(dirty_warnings_means)}")
    if dirty_warnings_means:
        print("  Warnings:")
        for w in dirty_warnings_means:
            print(f"    - {w}")
    print()

    # Test 5: Dirty flow graph record (token literals in edge note)
    print("Test 5: Dirty flow graph record (token literals in edge note)")
    dirty_token = {
        "v12_flow_edges": [
            {
                "note": "Edge with SUI and USDC tokens.",
            }
        ],
    }
    dirty_warnings_token = check_flow_graph_record(dirty_token)
    print(f"Dirty record warnings: {len(dirty_warnings_token)}")
    if dirty_warnings_token:
        print("  Warnings:")
        for w in dirty_warnings_token[:2]:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
