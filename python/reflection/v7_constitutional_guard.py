#!/usr/bin/env python3
"""
PR70: v0.7 Reflection Constitutional Guard (READ-ONLY)

Purpose:
    Constitutional guards for reflection records (v7_*).
    Enforce non-evaluative, non-prescriptive constraints.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Interpretation-bound: Only uses interpretation fields as basis
    - v0.4 boundary protection: No confidence_reason analysis

Warning-only: All functions return warnings, never raise exceptions.
"""

import re
from typing import Any, Dict, List


# Forbidden vocabulary (evaluative, prescriptive, scoric)
FORBIDDEN_VOCABULARY = [
    # Evaluative
    "good",
    "bad",
    "better",
    "worse",
    "best",
    "worst",
    "correct",
    "incorrect",
    "wrong",
    "right",
    "superior",
    "inferior",
    # Outcome
    "success",
    "failure",
    "fail",
    "win",
    "loss",
    "lose",
    "profit",
    "pnl",
    # Scoric
    "score",
    "grade",
    "rank",
    "rating",
    "accuracy",
    "performance",
    # Prescriptive
    "should",
    "must",
    "recommend",
    "suggest",
    "fix",
    "improve",
    "optimize",
    "enhance",
    "upgrade",
    "degrade",
]


def check_forbidden_vocabulary(text: str) -> List[str]:
    """
    Check for forbidden vocabulary in text.

    Warning-only: Returns list of warnings.

    Args:
        text: Text to check

    Returns:
        List of warning messages
    """
    if not isinstance(text, str):
        return []

    warnings = []
    text_lower = text.lower()

    for word in FORBIDDEN_VOCABULARY:
        # Use word boundaries to avoid false positives
        # e.g., "upgrade" should match as whole word, not in "background"
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        if re.search(pattern, text_lower):
            warnings.append(
                f"Forbidden vocabulary detected: '{word}' in text. "
                "Reflection must be non-evaluative and non-prescriptive."
            )

    return warnings


def check_confidence_boundary(basis: List[str]) -> List[str]:
    """
    Check for v0.4 confidence_reason boundary violations.

    Warning-only: Returns list of warnings.

    Args:
        basis: List of basis field names

    Returns:
        List of warning messages
    """
    warnings = []

    forbidden_v04_fields = [
        "confidence_reason",
        "confidence_reason_version",
        "confidence_reason_generated_at",
    ]

    for field in basis:
        if field in forbidden_v04_fields:
            warnings.append(
                f"v0.4 boundary violation: '{field}' in basis. "
                "Reflection must not use v0.4 confidence fields."
            )

    return warnings


def check_observation_boundary(basis: List[str]) -> List[str]:
    """
    Check for direct observation field access (should use interpretation).

    Warning-only: Returns list of warnings.

    Args:
        basis: List of basis field names

    Returns:
        List of warning messages
    """
    warnings = []

    # Direct observation fields (v5_*) should not be in reflection basis
    # Reflection should work from interpretation (v6_*), not raw observation
    observation_fields = [
        "v5_decision_diff_status",
        "v5_decision_diff_semantics_tag",
        "v5_shadow_decision_action",
        "v5_decision_pair",
    ]

    for field in basis:
        if field in observation_fields:
            warnings.append(
                f"Direct observation access: '{field}' in basis. "
                "Reflection should use interpretation fields (v6_*), not raw observations (v5_*)."
            )

    return warnings


def validate_reflection_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate reflection record against all constitutional constraints.

    Warning-only: Returns list of warnings.

    Args:
        record: Reflection record to validate

    Returns:
        List of warning messages
    """
    warnings = []

    # Check reflection tag for forbidden vocabulary
    if "v7_reflection_tag" in record:
        tag = record["v7_reflection_tag"]
        tag_warnings = check_forbidden_vocabulary(tag)
        warnings.extend(tag_warnings)

    # Check reflection summary for forbidden vocabulary
    if "v7_reflection_summary" in record:
        summary = record["v7_reflection_summary"]
        summary_warnings = check_forbidden_vocabulary(summary)
        warnings.extend(summary_warnings)

    # Check basis for v0.4 boundary violations
    if "v7_reflection_basis" in record:
        basis = record["v7_reflection_basis"]
        if isinstance(basis, list):
            confidence_warnings = check_confidence_boundary(basis)
            warnings.extend(confidence_warnings)

            observation_warnings = check_observation_boundary(basis)
            warnings.extend(observation_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v0.7 Reflection Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test forbidden vocabulary detection
    print("Test: Forbidden vocabulary detection")
    test_cases = [
        ("this is a good result", True),
        ("observed structural pattern", False),
        ("we should fix this", True),
        ("coverage gap detected", False),
        ("performance is bad", True),
        ("distribution skew observed", False),
    ]

    for text, should_warn in test_cases:
        warnings = check_forbidden_vocabulary(text)
        has_warning = len(warnings) > 0

        if has_warning == should_warn:
            status = "✓"
        else:
            status = "✗"

        print(f"{status} '{text}' -> {'warns' if has_warning else 'clean'}")

    print()

    # Test v0.4 boundary guard
    print("Test: v0.4 boundary guard")
    clean_basis = ["v6_meaning_tag", "pr64_interpretation_analytics"]
    dirty_basis = ["v6_meaning_tag", "confidence_reason"]

    warnings = check_confidence_boundary(clean_basis)
    if len(warnings) == 0:
        print("✓ Clean basis has no warnings")
    else:
        print(f"✗ Clean basis has warnings: {warnings}")

    warnings = check_confidence_boundary(dirty_basis)
    if len(warnings) > 0:
        print(f"✓ Dirty basis detected: {len(warnings)} warnings")
    else:
        print("✗ Dirty basis not detected")

    print()

    # Test observation boundary guard
    print("Test: Observation boundary guard")
    interpretation_basis = ["v6_meaning_tag", "v6_factors"]
    observation_basis = ["v6_meaning_tag", "v5_decision_diff_status"]

    warnings = check_observation_boundary(interpretation_basis)
    if len(warnings) == 0:
        print("✓ Interpretation basis has no warnings")
    else:
        print(f"✗ Interpretation basis has warnings: {warnings}")

    warnings = check_observation_boundary(observation_basis)
    if len(warnings) > 0:
        print(f"✓ Observation access detected: {len(warnings)} warnings")
    else:
        print("✗ Observation access not detected")

    print()

    # Test complete record validation
    print("Test: Complete record validation")
    clean_record = {
        "v7_reflection_mode": "ON",
        "v7_reflection_status": "AVAILABLE",
        "v7_reflection_tag": "COVERAGE_GAP_DETECTED",
        "v7_reflection_summary": "certain factor combinations not observed in data.",
        "v7_reflection_basis": ["v6_factors", "pr64_interpretation_analytics"],
    }

    warnings = validate_reflection_record(clean_record)
    if len(warnings) == 0:
        print("✓ Clean record passes all guards")
    else:
        print(f"✗ Clean record has warnings: {warnings}")

    dirty_record = {
        "v7_reflection_mode": "ON",
        "v7_reflection_status": "AVAILABLE",
        "v7_reflection_tag": "BAD_COVERAGE",
        "v7_reflection_summary": "this is a bad result that we should fix.",
        "v7_reflection_basis": ["confidence_reason", "v5_decision_diff_status"],
    }

    warnings = validate_reflection_record(dirty_record)
    if len(warnings) > 0:
        print(f"✓ Dirty record detected: {len(warnings)} violations")
    else:
        print("✗ Dirty record not detected")

    print()
    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
