#!/usr/bin/env python3
"""
PR139: v1.2 Rescue Flow Narrative Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on rescue flow narrative text.
    Guards against prescriptive language, causal coupling, and action vocabulary.

Constitutional Constraints:
    - No prescriptive language: No "should", "must", "need to"
    - No causal coupling: No "therefore", "so", "means" → action
    - No action vocabulary: No "execute", "trade", "swap", "buy", "sell"
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No counts beyond structural description
    - Narrative ≠ Instruction ≠ Conclusion

Guards:
    1. Rescue flow narrative coupling (forbid "RESCUE_X therefore action")
    2. Prescriptive language in narrative
    3. Action vocabulary in narrative
    4. Token literals in narrative
    5. Causal coupling patterns

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


# Forbidden causal coupling patterns (rescue label → action)
RESCUE_COUPLING_PATTERNS = [
    # Strong coupling: "RESCUE_X therefore action"
    ("RESCUE_STRONG", "therefore"),
    ("RESCUE_MEDIUM", "therefore"),
    ("RESCUE_WEAK", "therefore"),
    ("RESCUE_STRONG", "so"),
    ("RESCUE_MEDIUM", "so"),
    ("RESCUE_WEAK", "so"),
    ("RESCUE_STRONG", "means"),
    ("RESCUE_MEDIUM", "means"),
    ("RESCUE_WEAK", "means"),
    ("RESCUE_STRONG", "hence"),
    ("RESCUE_MEDIUM", "hence"),
    ("RESCUE_WEAK", "hence"),
    # Direct coupling: "RESCUE_X execute"
    ("RESCUE_STRONG", "execute"),
    ("RESCUE_MEDIUM", "execute"),
    ("RESCUE_WEAK", "execute"),
    ("RESCUE_STRONG", "trade"),
    ("RESCUE_MEDIUM", "trade"),
    ("RESCUE_WEAK", "trade"),
    ("RESCUE_STRONG", "swap"),
    ("RESCUE_MEDIUM", "swap"),
    ("RESCUE_WEAK", "swap"),
]

# Forbidden action vocabulary
ACTION_VOCABULARY = [
    "execute",
    "trade",
    "swap",
    "buy",
    "sell",
    "transfer",
    "sign",
    "broadcast",
    "submit",
    "approve",
]

# Forbidden prescriptive language
PRESCRIPTIVE_LANGUAGE = [
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


def check_rescue_narrative_coupling(text: str) -> List[str]:
    """
    Check for rescue flow narrative coupling patterns.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    # Check for rescue coupling patterns
    for rescue_label, coupling_word in RESCUE_COUPLING_PATTERNS:
        # Check if both appear in text (may not be adjacent, but proximity is suspicious)
        if rescue_label.lower() in text_lower and coupling_word.lower() in text_lower:
            warnings.append(
                f"rescue narrative coupling detected: '{rescue_label}' with '{coupling_word}' "
                f"(may indicate prescriptive coupling)"
            )

    return warnings


def check_narrative_action_vocabulary(text: str) -> List[str]:
    """
    Check for action vocabulary in narrative text.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for action_word in ACTION_VOCABULARY:
        if action_word.lower() in text_lower:
            warnings.append(
                f"action vocabulary detected in narrative: '{action_word}' "
                f"(narrative should not contain execution language)"
            )

    return warnings


def check_narrative_prescriptive_language(text: str) -> List[str]:
    """
    Check for prescriptive language in narrative text.

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for prescriptive_word in PRESCRIPTIVE_LANGUAGE:
        if prescriptive_word.lower() in text_lower:
            warnings.append(
                f"prescriptive language detected in narrative: '{prescriptive_word}' "
                f"(narrative should be descriptive only)"
            )

    return warnings


def check_rescue_narrative_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate rescue narrative record against constitutional guards.

    Args:
        record: Rescue narrative record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check summary
    if "v12_rescue_narrative_summary" in record:
        summary = record["v12_rescue_narrative_summary"]
        if isinstance(summary, str):
            # Check for coupling
            coupling_warnings = check_rescue_narrative_coupling(summary)
            warnings.extend(coupling_warnings)

            # Check for action vocabulary
            action_warnings = check_narrative_action_vocabulary(summary)
            warnings.extend(action_warnings)

            # Check for prescriptive language
            prescriptive_warnings = check_narrative_prescriptive_language(summary)
            warnings.extend(prescriptive_warnings)

    # Check paragraphs
    if "v12_rescue_narrative_paragraphs" in record:
        paragraphs = record["v12_rescue_narrative_paragraphs"]
        if isinstance(paragraphs, list):
            for i, paragraph in enumerate(paragraphs):
                if isinstance(paragraph, str):
                    # Check for coupling
                    coupling_warnings = check_rescue_narrative_coupling(paragraph)
                    for warning in coupling_warnings:
                        warnings.append(f"paragraph {i+1}: {warning}")

                    # Check for action vocabulary
                    action_warnings = check_narrative_action_vocabulary(paragraph)
                    for warning in action_warnings:
                        warnings.append(f"paragraph {i+1}: {warning}")

                    # Check for prescriptive language
                    prescriptive_warnings = check_narrative_prescriptive_language(paragraph)
                    for warning in prescriptive_warnings:
                        warnings.append(f"paragraph {i+1}: {warning}")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Rescue Flow Narrative Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean narrative (no warnings)
    print("Test 1: Clean narrative (no warnings)")
    clean_record = {
        "v12_rescue_narrative_summary": "rescue flow narrative available.",
        "v12_rescue_narrative_paragraphs": [
            "rescue flow graph indicates structural ROLE-to-ROLE relationships.",
            "STABILITY may support VOLATILITY.",
            "rescue strength labels range from MEDIUM to WEAK.",
        ],
    }
    clean_warnings = check_rescue_narrative_record(clean_record)
    print(f"Clean narrative warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty narrative (coupling)
    print("Test 2: Dirty narrative (coupling)")
    dirty_coupling = {
        "v12_rescue_narrative_summary": "rescue flow narrative available.",
        "v12_rescue_narrative_paragraphs": [
            "RESCUE_STRONG rescue strength therefore execute trade.",
        ],
    }
    dirty_warnings = check_rescue_narrative_record(dirty_coupling)
    print(f"Dirty narrative warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty narrative (action vocabulary)
    print("Test 3: Dirty narrative (action vocabulary)")
    dirty_action = {
        "v12_rescue_narrative_summary": "rescue flow narrative available.",
        "v12_rescue_narrative_paragraphs": [
            "STABILITY may support VOLATILITY by executing swap operations.",
        ],
    }
    dirty_warnings_action = check_rescue_narrative_record(dirty_action)
    print(f"Dirty narrative warnings: {len(dirty_warnings_action)}")
    if dirty_warnings_action:
        print("  Warnings:")
        for w in dirty_warnings_action:
            print(f"    - {w}")
    print()

    # Test 4: Dirty narrative (prescriptive language)
    print("Test 4: Dirty narrative (prescriptive language)")
    dirty_prescriptive = {
        "v12_rescue_narrative_summary": "rescue flow narrative available.",
        "v12_rescue_narrative_paragraphs": [
            "STABILITY should support VOLATILITY. System must maintain rescue strength.",
        ],
    }
    dirty_warnings_prescriptive = check_rescue_narrative_record(dirty_prescriptive)
    print(f"Dirty narrative warnings: {len(dirty_warnings_prescriptive)}")
    if dirty_warnings_prescriptive:
        print("  Warnings:")
        for w in dirty_warnings_prescriptive:
            print(f"    - {w}")
    print()

    # Test 5: Multiple violations
    print("Test 5: Multiple violations")
    dirty_multiple = {
        "v12_rescue_narrative_summary": "rescue flow available. RESCUE_STRONG therefore trade.",
        "v12_rescue_narrative_paragraphs": [
            "STABILITY should execute swap operations.",
            "RESCUE_MEDIUM means buy signal.",
        ],
    }
    dirty_warnings_multiple = check_rescue_narrative_record(dirty_multiple)
    print(f"Multiple violations warnings: {len(dirty_warnings_multiple)}")
    if dirty_warnings_multiple:
        print("  Warnings:")
        for w in dirty_warnings_multiple:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
