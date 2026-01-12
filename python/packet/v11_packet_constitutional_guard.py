#!/usr/bin/env python3
"""
PR124: v1.1 Approval Packet Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on approval packet records.
    Guards against trading vocabulary, token literals, numeric patterns,
    prescriptive language, and cross-component coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No counts, percentages, scores
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - No cross-component coupling: No "approved therefore execute", "REQUIRED so do X"

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
    10. Cross-component coupling guard (NEW)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List
import re


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


def check_packet_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate packet record against constitutional guards.

    Args:
        record: Packet record to validate

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

    warnings = []

    # Check packet summary
    if "v11_packet_summary" in record:
        summary = record["v11_packet_summary"]
        if isinstance(summary, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(summary)
            warnings.extend(token_warnings)

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

            # Numeric pattern guard
            numeric_warnings = check_drift_numeric_patterns(summary)
            warnings.extend(numeric_warnings)

            # Prescriptive language guard
            prescriptive_warnings = check_prescriptive_language(summary)
            warnings.extend(prescriptive_warnings)

            # Prescriptive coupling guard
            coupling_warnings = check_prescriptive_coupling(summary)
            warnings.extend(coupling_warnings)

            # Narrative coupling guard
            narrative_coupling_warnings = check_narrative_coupling(summary)
            warnings.extend(narrative_coupling_warnings)

            # Cross-component coupling guard (NEW)
            cross_coupling_warnings = check_cross_component_coupling(summary)
            warnings.extend(cross_coupling_warnings)

    # Check components (if present)
    if "v11_packet_components" in record:
        components = record["v11_packet_components"]
        if isinstance(components, dict):
            # Check each component's text fields
            for component_name, component_record in components.items():
                if isinstance(component_record, dict):
                    # Check narrative text
                    if "v11_narrative_text" in component_record:
                        text = component_record["v11_narrative_text"]
                        if isinstance(text, str):
                            text_warnings = check_observation_token_literals(text)
                            warnings.extend(text_warnings)

                    # Check explain summary
                    if "v11_explain_summary" in component_record:
                        summary = component_record["v11_explain_summary"]
                        if isinstance(summary, str):
                            summary_warnings = check_observation_token_literals(summary)
                            warnings.extend(summary_warnings)

                    # Check preview summary
                    if "v11_preview_summary" in component_record:
                        summary = component_record["v11_preview_summary"]
                        if isinstance(summary, str):
                            summary_warnings = check_observation_token_literals(summary)
                            warnings.extend(summary_warnings)

                    # Check approval summary
                    if "v11_approval_summary" in component_record:
                        summary = component_record["v11_approval_summary"]
                        if isinstance(summary, str):
                            summary_warnings = check_observation_token_literals(summary)
                            warnings.extend(summary_warnings)

    return warnings


def check_cross_component_coupling(text: str) -> List[str]:
    """
    Check for cross-component coupling patterns (NEW in PR124).

    Detects:
        - "APPROVED therefore ALLOW" / "REQUIRED so execute"
        - Approval state words near execution verbs
        - State label coupling to action words

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: Approval state + action coupling
    approval_action_patterns = [
        r'approved\s+(therefore|so|thus|then)\s+(allow|execute|proceed)',
        r'required\s+(therefore|so|thus|then)\s+(execute|proceed|do)',
        r'if\s+approved\s+(then|,)\s+(allow|execute)',
        r'when\s+approved\s+(allow|execute|proceed)',
    ]

    for pattern in approval_action_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Cross-component coupling detected: '{pattern}' in text")

    # Pattern 2: State label proximity to execution verbs (within 10 words)
    # This is a heuristic to catch "REQUIRED. Execute now." type coupling
    approval_words = ["approved", "required", "allow", "blocked", "hold"]
    execution_words = ["execute", "swap", "transfer", "sign", "send", "proceed"]

    words = text.lower().split()
    for i, word in enumerate(words):
        if any(approval_word in word for approval_word in approval_words):
            # Check next 10 words for execution verbs
            for j in range(i + 1, min(i + 11, len(words))):
                if any(exec_word in words[j] for exec_word in execution_words):
                    warnings.append(f"Approval-execution proximity detected: '{word}' near '{words[j]}' (distance {j-i})")
                    break

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.1 Approval Packet Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean packet (no warnings)
    print("Test 1: Clean packet (no warnings)")
    clean_packet = {
        "v11_packet_summary": "approval packet assembled. narrative and preview included. approval requirement labeled as REQUIRED.",
    }
    clean_warnings = check_packet_record(clean_packet)
    print(f"Clean packet warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty packet (token literals)
    print("Test 2: Dirty packet (token literals)")
    dirty_token = {
        "v11_packet_summary": "packet assembled with SUI and USDC details.",
    }
    dirty_warnings = check_packet_record(dirty_token)
    print(f"Dirty packet warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty packet (numeric patterns)
    print("Test 3: Dirty packet (numeric patterns)")
    dirty_numeric = {
        "v11_packet_summary": "packet with 5 components and 3 artifacts.",
    }
    dirty_warnings_numeric = check_packet_record(dirty_numeric)
    print(f"Dirty packet warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 4: Dirty packet (trading vocabulary)
    print("Test 4: Dirty packet (trading vocabulary)")
    dirty_trading = {
        "v11_packet_summary": "approved. execute swap now.",
    }
    dirty_warnings_trading = check_packet_record(dirty_trading)
    print(f"Dirty packet warnings: {len(dirty_warnings_trading)}")
    if dirty_warnings_trading:
        print("  Warnings:")
        for w in dirty_warnings_trading:
            print(f"    - {w}")
    print()

    # Test 5: Dirty packet (cross-component coupling - NEW)
    print("Test 5: Dirty packet (cross-component coupling)")
    dirty_coupling = {
        "v11_packet_summary": "approval requirement REQUIRED therefore execute operation.",
    }
    dirty_warnings_coupling = check_packet_record(dirty_coupling)
    print(f"Dirty packet warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    # Test 6: Dirty packet (approval-execution proximity)
    print("Test 6: Dirty packet (approval-execution proximity)")
    dirty_proximity = {
        "v11_packet_summary": "approval state is approved. proceed with swap execution.",
    }
    dirty_warnings_proximity = check_packet_record(dirty_proximity)
    print(f"Dirty packet warnings: {len(dirty_warnings_proximity)}")
    if dirty_warnings_proximity:
        print("  Warnings:")
        for w in dirty_warnings_proximity:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
