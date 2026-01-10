#!/usr/bin/env python3
"""
PR60: v0.6 Constitutional Guard for Interpretation (READ-ONLY)

Purpose:
    Guard against constitutional violations in interpretation layer.
    Ensures interpretation remains non-evaluative, non-prescriptive,
    and observation-bound.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Observation-bound: Only uses observation fields as basis
    - v0.4 boundary protection: No confidence_reason analysis

Warning-Only:
    All violations generate warnings but never fail (exit code 0).
    This allows observation to continue even with violations.
"""

import re
from typing import Any, Dict, List


# ============================================================================
# Forbidden Vocabulary (Non-Evaluative Constraint)
# ============================================================================

# Evaluative vocabulary (good/bad axis)
FORBIDDEN_EVALUATIVE = [
    "good", "bad",
    "better", "worse",
    "best", "worst",
    "optimal", "suboptimal",
    "superior", "inferior",
]

# Correctness vocabulary (right/wrong axis)
FORBIDDEN_CORRECTNESS = [
    "correct", "incorrect",
    "right", "wrong",
    "valid", "invalid",
    "accurate", "inaccurate",
]

# Scoring vocabulary (measurement axis)
FORBIDDEN_SCORIC = [
    "score", "scoring",
    "grade", "grading",
    "rank", "ranking",
    "rating", "rated",
    "accuracy", "precision",
]

# Outcome vocabulary (profit/loss axis)
FORBIDDEN_OUTCOME = [
    "profit", "loss", "pnl",
    "gain", "lose",
    "win", "loss",
    "success", "failure",
    "successful", "failed",
]

# Prescriptive vocabulary (recommendation axis)
FORBIDDEN_PRESCRIPTIVE = [
    "should", "must",
    "recommend", "recommendation",
    "suggest", "suggestion",
    "advise", "advice",
    "prefer", "preference",
    "fix", "improve",
]

# Combined forbidden vocabulary
FORBIDDEN_VOCABULARY = (
    FORBIDDEN_EVALUATIVE +
    FORBIDDEN_CORRECTNESS +
    FORBIDDEN_SCORIC +
    FORBIDDEN_OUTCOME +
    FORBIDDEN_PRESCRIPTIVE
)


def check_forbidden_vocabulary(text: str) -> List[str]:
    """
    Check text for forbidden evaluative/prescriptive vocabulary.

    Returns list of warnings (empty if clean).
    Uses word boundaries to avoid false positives.
    """
    warnings = []

    if not isinstance(text, str):
        return warnings

    text_lower = text.lower()

    for word in FORBIDDEN_VOCABULARY:
        # Use word boundaries to avoid false positives
        # e.g., "upgrade" should not match "grade"
        pattern = r'\b' + re.escape(word.lower()) + r'\b'
        if re.search(pattern, text_lower):
            warnings.append(
                f"PR60 vocabulary violation: forbidden word '{word}' found in text"
            )

    return warnings


def check_record_vocabulary(record: Dict[str, Any]) -> List[str]:
    """
    Check interpretation record for forbidden vocabulary.

    Returns list of warnings (empty if clean).
    Checks all string fields in the record.
    """
    warnings = []

    # Fields to check
    text_fields = [
        "v6_meaning_tag",
        "v6_meaning_summary",
    ]

    for field in text_fields:
        if field in record:
            value = record[field]
            if isinstance(value, str):
                field_warnings = check_forbidden_vocabulary(value)
                for warning in field_warnings:
                    warnings.append(f"in field '{field}': {warning}")

    return warnings


# ============================================================================
# Boundary Guard (v0.4 Confidence Protection)
# ============================================================================

# v0.4 confidence fields that must not be accessed
V04_CONFIDENCE_FIELDS = [
    "confidence_reason",
    "confidence_reason_version",
    "confidence_reason_generated_at",
]


def check_confidence_boundary(basis: List[str]) -> List[str]:
    """
    Check that interpretation basis does not violate v0.4 boundary.

    Returns list of warnings (empty if clean).
    """
    warnings = []

    if not isinstance(basis, list):
        return warnings

    for field in basis:
        if field in V04_CONFIDENCE_FIELDS:
            warnings.append(
                f"PR60 boundary violation: interpretation basis references "
                f"v0.4 confidence field '{field}' (boundary must not be crossed)"
            )

    return warnings


# ============================================================================
# Combined Guard
# ============================================================================

def validate_interpretation_record(record: Dict[str, Any]) -> List[str]:
    """
    Run all constitutional guards on an interpretation record.

    Returns list of warnings (empty if clean).
    Warning-only: never raises exceptions, exit code always 0.
    """
    warnings = []

    # Check vocabulary
    vocab_warnings = check_record_vocabulary(record)
    warnings.extend(vocab_warnings)

    # Check v0.4 boundary
    if "v6_meaning_basis" in record:
        basis = record["v6_meaning_basis"]
        boundary_warnings = check_confidence_boundary(basis)
        warnings.extend(boundary_warnings)

    return warnings


# ============================================================================
# Module-Level Validation
# ============================================================================

def validate_code_for_violations(code_text: str) -> List[str]:
    """
    Scan code text for potential constitutional violations.

    Used for static analysis / pre-commit checks.
    Returns list of warnings (empty if clean).
    """
    warnings = []

    # Check for confidence_reason access patterns
    confidence_patterns = [
        r'confidence_reason\s*=',
        r'\[\s*["\']confidence_reason["\']\s*\]',
        r'\.get\s*\(\s*["\']confidence_reason["\']\s*\)',
        r'confidence_reason\s+in\s+',
    ]

    for pattern in confidence_patterns:
        if re.search(pattern, code_text):
            warnings.append(
                f"PR60 code scan: potential confidence_reason access detected "
                f"(pattern: {pattern})"
            )

    # Check for evaluative vocabulary in string literals
    # (This is informational only, as false positives are common)
    for word in FORBIDDEN_VOCABULARY[:10]:  # Check first 10 for performance
        pattern = r'["\'].*\b' + re.escape(word) + r'\b.*["\']'
        if re.search(pattern, code_text, re.IGNORECASE):
            warnings.append(
                f"PR60 code scan: forbidden word '{word}' found in string literal "
                f"(review for context)"
            )

    return warnings


# ============================================================================
# Warning Reporter
# ============================================================================

def report_warnings(warnings: List[str], prefix: str = "[WARNING][PR60]") -> None:
    """
    Report warnings to stdout.

    Warnings are informational only and do not affect execution.
    """
    if warnings:
        for warning in warnings:
            print(f"{prefix} {warning}")


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v0.6 Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test forbidden vocabulary detection
    test_cases = [
        ("this is a good result", True),
        ("observed divergence pattern", False),
        ("the score is high", True),
        ("structural mapping observed", False),
        ("you should fix this", True),
        ("observation continues", False),
    ]

    print("Vocabulary Detection Tests:")
    for text, should_warn in test_cases:
        warnings = check_forbidden_vocabulary(text)
        has_warning = len(warnings) > 0
        status = "✓" if has_warning == should_warn else "✗"
        print(f"{status} '{text}' -> {len(warnings)} warnings")

    print()

    # Test boundary detection
    print("Boundary Detection Tests:")
    basis_tests = [
        (["regime", "intent_primary"], False),
        (["confidence_reason"], True),
        (["v5_decision_diff_status"], False),
    ]

    for basis, should_warn in basis_tests:
        warnings = check_confidence_boundary(basis)
        has_warning = len(warnings) > 0
        status = "✓" if has_warning == should_warn else "✗"
        print(f"{status} {basis} -> {len(warnings)} warnings")

    print()
    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
