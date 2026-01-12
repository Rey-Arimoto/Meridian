#!/usr/bin/env python3
"""
PR123: v1.1 Human Narrative Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on human narrative records.
    Guards against trading vocabulary, token literals, numeric patterns,
    prescriptive language, and narrative-specific coupling.

Constitutional Constraints:
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No counts, percentages, scores
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No execution operations: No transaction, broadcast, submit
    - No forbidden vocabulary: No good/bad, correct/wrong
    - No prescriptive language: No "should", "must", "need to"
    - No narrative coupling: No "this means X", "therefore Y"

Guards:
    1. Token literal guard (from observation)
    2. Numeric pattern guard (from drift)
    3. Address pattern guard (from preview)
    4. Trading vocabulary guard (from preview)
    5. Execution operation guard (from preview)
    6. Forbidden vocabulary guard (from execution)
    7. Prescriptive language guard (from policy)
    8. Prescriptive coupling guard (from explain)
    9. Narrative coupling guard (NEW)

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


def check_narrative_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate narrative record against constitutional guards.

    Args:
        record: Narrative record to validate

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

    warnings = []

    # Check narrative text
    if "v11_narrative_text" in record:
        text = record["v11_narrative_text"]
        if isinstance(text, str):
            # Token literals guard
            token_warnings = check_observation_token_literals(text)
            warnings.extend(token_warnings)

            # Trading vocabulary guard
            trading_warnings = check_trading_vocabulary(text)
            warnings.extend(trading_warnings)

            # Execution operation guard
            execution_warnings = check_execution_operations(text)
            warnings.extend(execution_warnings)

            # Address pattern guard
            address_warnings = check_address_patterns(text)
            warnings.extend(address_warnings)

            # Forbidden vocabulary guard
            vocab_warnings = check_forbidden_vocabulary(text)
            warnings.extend(vocab_warnings)

            # Numeric pattern guard
            numeric_warnings = check_drift_numeric_patterns(text)
            warnings.extend(numeric_warnings)

            # Prescriptive language guard
            prescriptive_warnings = check_prescriptive_language(text)
            warnings.extend(prescriptive_warnings)

            # Prescriptive coupling guard
            coupling_warnings = check_prescriptive_coupling(text)
            warnings.extend(coupling_warnings)

            # Narrative coupling guard (NEW)
            narrative_coupling_warnings = check_narrative_coupling(text)
            warnings.extend(narrative_coupling_warnings)

    # Check sections (if present)
    if "v11_narrative_sections" in record:
        sections = record["v11_narrative_sections"]
        if isinstance(sections, list):
            for section in sections:
                if isinstance(section, dict):
                    for key, value in section.items():
                        if isinstance(value, str):
                            # Apply all guards to section text
                            section_warnings = check_narrative_record({"v11_narrative_text": value})
                            warnings.extend(section_warnings)

    return warnings


def check_narrative_coupling(text: str) -> List[str]:
    """
    Check for narrative coupling patterns (NEW in PR123).

    Detects:
        - "this means X" / "this implies Y"
        - "therefore X" / "thus Y"
        - "as a result X" / "consequently Y"
        - Direct causal coupling in narrative

    Args:
        text: Text to check

    Returns:
        List of warnings
    """
    if not isinstance(text, str):
        return []

    warnings = []

    # Pattern 1: "this means/implies/suggests"
    meaning_patterns = [
        r'this\s+(means|implies|suggests|indicates\s+that)',
        r'which\s+(means|implies|suggests)',
    ]

    for pattern in meaning_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Narrative coupling detected: '{pattern}' in text")

    # Pattern 2: "therefore/thus/consequently"
    causal_patterns = [
        r'therefore\s+\w+',
        r'thus\s+\w+',
        r'consequently\s+\w+',
        r'as\s+a\s+result\s+\w+',
    ]

    for pattern in causal_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Causal coupling detected: '{pattern}' in text")

    # Pattern 3: "because X, Y" (causal structure)
    if re.search(r'because\s+.*,\s+\w+', text, re.IGNORECASE):
        warnings.append("Causal structure detected: 'because X, Y' pattern in text")

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.1 Human Narrative Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test 1: Clean narrative (no warnings)
    print("Test 1: Clean narrative (no warnings)")
    clean_narrative = {
        "v11_narrative_text": "current regime label indicates elevated uncertainty. structural drift label indicates shifting market vocabulary.",
    }
    clean_warnings = check_narrative_record(clean_narrative)
    print(f"Clean narrative warnings: {len(clean_warnings)}")
    if clean_warnings:
        print(f"  Warnings: {clean_warnings}")
    print()

    # Test 2: Dirty narrative (token literals)
    print("Test 2: Dirty narrative (token literals)")
    dirty_token = {
        "v11_narrative_text": "current situation: SUI and USDC activity detected.",
    }
    dirty_warnings = check_narrative_record(dirty_token)
    print(f"Dirty narrative warnings: {len(dirty_warnings)}")
    if dirty_warnings:
        print("  Warnings:")
        for w in dirty_warnings:
            print(f"    - {w}")
    print()

    # Test 3: Dirty narrative (numeric patterns)
    print("Test 3: Dirty narrative (numeric patterns)")
    dirty_numeric = {
        "v11_narrative_text": "drift detected with 5 terms added and 3 removed.",
    }
    dirty_warnings_numeric = check_narrative_record(dirty_numeric)
    print(f"Dirty narrative warnings: {len(dirty_warnings_numeric)}")
    if dirty_warnings_numeric:
        print("  Warnings:")
        for w in dirty_warnings_numeric:
            print(f"    - {w}")
    print()

    # Test 4: Dirty narrative (trading vocabulary)
    print("Test 4: Dirty narrative (trading vocabulary)")
    dirty_trading = {
        "v11_narrative_text": "approved. execute swap operations now.",
    }
    dirty_warnings_trading = check_narrative_record(dirty_trading)
    print(f"Dirty narrative warnings: {len(dirty_warnings_trading)}")
    if dirty_warnings_trading:
        print("  Warnings:")
        for w in dirty_warnings_trading:
            print(f"    - {w}")
    print()

    # Test 5: Dirty narrative (prescriptive language)
    print("Test 5: Dirty narrative (prescriptive language)")
    dirty_prescriptive = {
        "v11_narrative_text": "system should execute the trade. you must proceed.",
    }
    dirty_warnings_prescriptive = check_narrative_record(dirty_prescriptive)
    print(f"Dirty narrative warnings: {len(dirty_warnings_prescriptive)}")
    if dirty_warnings_prescriptive:
        print("  Warnings:")
        for w in dirty_warnings_prescriptive:
            print(f"    - {w}")
    print()

    # Test 6: Dirty narrative (narrative coupling - NEW)
    print("Test 6: Dirty narrative (narrative coupling)")
    dirty_coupling = {
        "v11_narrative_text": "regime is high. this means execution is risky.",
    }
    dirty_warnings_coupling = check_narrative_record(dirty_coupling)
    print(f"Dirty narrative warnings: {len(dirty_warnings_coupling)}")
    if dirty_warnings_coupling:
        print("  Warnings:")
        for w in dirty_warnings_coupling:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
