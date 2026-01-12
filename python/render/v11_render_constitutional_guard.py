#!/usr/bin/env python3
"""
PR125/PR138: v1.1 Render Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on render output.
    Guards against trading vocabulary, token literals, numeric patterns,
    prescriptive language, evaluative language, and causal coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No counts, percentages, scores
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - No evaluative language: No quality judgments
    - No causal coupling: No "therefore", "so", "hence"
    - No rescue flow coupling: No "STRONG rescue therefore trade" (PR138)

Guards:
    1. Token literal guard (from observation)
    2. Numeric pattern guard (from drift)
    3. Address pattern guard (from preview)
    4. Trading vocabulary guard (from preview)
    5. Execution operation guard (from preview)
    6. Forbidden vocabulary guard (from execution)
    7. Prescriptive language guard (from policy)
    8. Prescriptive coupling guard (from explain)
    9. Narrative coupling guard (from narrative)
    10. Cross-component coupling guard (from packet)
    11. Rescue flow coupling guard (PR138)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


# Forbidden vocabulary (evaluative/scoric/prescriptive)
FORBIDDEN_VOCABULARY = [
    # Evaluative
    "good", "bad", "better", "worse", "best", "worst",
    "correct", "incorrect", "right", "wrong",
    "optimal", "suboptimal", "ideal", "poor",
    # Scoric
    "score", "grade", "rating", "rank",
    # Prescriptive
    "should", "must", "need to", "have to",
    "recommend", "suggest", "advise",
    # Imperative
    "do", "don't", "perform", "execute",
    "go ahead", "proceed", "continue", "stop",
]


def check_render_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate render record against constitutional guards.

    Args:
        record: Render record to validate

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
    from explain.v11_explain_constitutional_guard import (
        check_prescriptive_coupling,
    )
    from narrative.v11_narrative_constitutional_guard import (
        check_narrative_coupling,
    )
    from packet.v11_packet_constitutional_guard import (
        check_cross_component_coupling,
    )
    from flow.v12_flow_constitutional_guard import (  # PR138
        check_flow_coupling,
    )

    warnings = []

    # Check render output
    if "v11_render_output" in record:
        output = record["v11_render_output"]
        if isinstance(output, str):
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

            # Forbidden vocabulary guard
            vocab_warnings = check_forbidden_vocabulary(output)
            warnings.extend(vocab_warnings)

            # Numeric pattern guard
            numeric_warnings = check_drift_numeric_patterns(output)
            warnings.extend(numeric_warnings)

            # Prescriptive language guard
            prescriptive_warnings = check_prescriptive_language(output)
            warnings.extend(prescriptive_warnings)

            # Prescriptive coupling guard
            coupling_warnings = check_prescriptive_coupling(output)
            warnings.extend(coupling_warnings)

            # Narrative coupling guard
            narrative_coupling_warnings = check_narrative_coupling(output)
            warnings.extend(narrative_coupling_warnings)

            # Cross-component coupling guard
            cross_coupling_warnings = check_cross_component_coupling(output)
            warnings.extend(cross_coupling_warnings)

            # Rescue flow coupling guard (PR138)
            flow_coupling_warnings = check_flow_coupling(output)
            warnings.extend(flow_coupling_warnings)

    # Check render summary
    if "v11_render_summary" in record:
        summary = record["v11_render_summary"]
        if isinstance(summary, str):
            # Apply same guards to summary
            token_warnings = check_observation_token_literals(summary)
            warnings.extend(token_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.1 Render Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean render (no warnings)
    print("Test 1: Clean render (no warnings)")
    clean_render = {
        "v11_render_output": "# Approval Packet\n\nLabels:\n- REGIME_MEDIUM\n- DRIFT_LOW\n",
    }
    clean_warnings = check_render_record(clean_render)
    print(f"Clean render warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty render (token literals)
    print("Test 2: Dirty render (token literals)")
    dirty_token = {
        "v11_render_output": "# Approval Packet\n\nSUI and USDC detected.",
    }
    dirty_warnings = check_render_record(dirty_token)
    print(f"Dirty render warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty render (numeric patterns)
    print("Test 3: Dirty render (numeric patterns)")
    dirty_numeric = {
        "v11_render_output": "# Approval Packet\n\nDetected 5 terms added.",
    }
    dirty_warnings_numeric = check_render_record(dirty_numeric)
    print(f"Dirty render warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 4: Dirty render (trading vocabulary)
    print("Test 4: Dirty render (trading vocabulary)")
    dirty_trading = {
        "v11_render_output": "# Approval Packet\n\nExecute swap now.",
    }
    dirty_warnings_trading = check_render_record(dirty_trading)
    print(f"Dirty render warnings: {len(dirty_warnings_trading)}")
    if dirty_warnings_trading:
        print("  Warnings:")
        for w in dirty_warnings_trading:
            print(f"    - {w}")
    print()

    # Test 5: Dirty render (prescriptive language)
    print("Test 5: Dirty render (prescriptive language)")
    dirty_prescriptive = {
        "v11_render_output": "# Approval Packet\n\nYou should approve this.",
    }
    dirty_warnings_prescriptive = check_render_record(dirty_prescriptive)
    print(f"Dirty render warnings: {len(dirty_warnings_prescriptive)}")
    if dirty_warnings_prescriptive:
        print("  Warnings:")
        for w in dirty_warnings_prescriptive:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
