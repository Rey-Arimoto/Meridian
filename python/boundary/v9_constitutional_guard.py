#!/usr/bin/env python3
"""
PR90: v0.9 Boundary Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on boundary records.
    Guards against violations of v0.9 boundary principles.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Blindspot-bound: Only uses v8/v7/v6 fields as basis

Guards:
    1. Forbidden vocabulary (evaluative/scoric/prescriptive)
    2. v0.4 boundary (no confidence_reason)
    3. Observation boundary (no v5 observation fields)

All guards are warning-only (never fail, exit 0).
"""

from typing import Any, Dict, List


# ============================================================================
# Forbidden Vocabulary (Non-Evaluative / Non-Scoric / Non-Prescriptive)
# ============================================================================

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
    "optimal",
    "suboptimal",
    # Scoric
    "score",
    "grade",
    "rank",
    "rating",
    "performance",
    # Prescriptive
    "should",
    "must",
    "need to",
    "ought to",
    "recommend",
    "suggest",
    "improve",
    "fix",
    "enhance",
    "optimize",
    # Financial evaluation
    "profit",
    "loss",
    "pnl",
    "gain",
    "lose",
    "win",
    "winning",
    "losing",
    "success",
    "failure",
    "successful",
    "failed",
]


def check_forbidden_vocabulary(text: str) -> List[str]:
    """
    Check if text contains forbidden vocabulary.

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if clean)
    """
    warnings = []
    text_lower = text.lower()

    for word in FORBIDDEN_VOCABULARY:
        if word in text_lower:
            warnings.append(f"Forbidden vocabulary detected: '{word}' in text")

    return warnings


# ============================================================================
# v0.4 Boundary Guard (confidence_reason)
# ============================================================================

CONFIDENCE_FIELDS = [
    "confidence_reason",
    "confidence_reason_version",
    "confidence_detail",
]


def check_confidence_boundary(basis: List[str]) -> List[str]:
    """
    Check if basis violates v0.4 boundary (confidence_reason).

    Args:
        basis: List of basis field names

    Returns:
        List of warnings (empty if no violation)
    """
    warnings = []

    for field in basis:
        if field in CONFIDENCE_FIELDS:
            warnings.append(
                f"v0.4 boundary violation: basis references '{field}' "
                "(boundary must not access v0.4 confidence layer)"
            )

    return warnings


# ============================================================================
# Observation Boundary Guard (v5 fields)
# ============================================================================

OBSERVATION_FIELDS = [
    "v5_decision_diff_status",
    "v5_decision_diff_semantics_tag",
    "v5_decision_diff_semantics_detail",
    "v5_shadow_decision_status",
    "v5_primary_decision_status",
]


def check_observation_boundary(basis: List[str]) -> List[str]:
    """
    Check if basis violates observation boundary (v5 fields).

    Args:
        basis: List of basis field names

    Returns:
        List of warnings (empty if no violation)
    """
    warnings = []

    for field in basis:
        if field in OBSERVATION_FIELDS:
            warnings.append(
                f"Observation boundary violation: basis references '{field}' "
                "(boundary must only access blindspot/interpretation/reflection fields)"
            )

    return warnings


# ============================================================================
# Complete Record Validation
# ============================================================================

def validate_boundary_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate complete boundary record against all constitutional guards.

    Args:
        record: Boundary record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check type vocabulary
    if "v9_boundary_type" in record:
        type_warnings = check_forbidden_vocabulary(record["v9_boundary_type"])
        warnings.extend(type_warnings)

    # Check description vocabulary
    if "v9_boundary_description" in record:
        description_warnings = check_forbidden_vocabulary(record["v9_boundary_description"])
        warnings.extend(description_warnings)

    # Check basis boundaries
    if "v9_boundary_basis" in record:
        basis = record["v9_boundary_basis"]

        # v0.4 boundary
        confidence_warnings = check_confidence_boundary(basis)
        warnings.extend(confidence_warnings)

        # Observation boundary
        observation_warnings = check_observation_boundary(basis)
        warnings.extend(observation_warnings)

    return warnings


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v0.9 Boundary Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test forbidden vocabulary
    print("Test 1: Forbidden vocabulary")
    clean_text = "observability limit at schema boundary"
    dirty_text = "this is a bad boundary that should be fixed"

    clean_warnings = check_forbidden_vocabulary(clean_text)
    dirty_warnings = check_forbidden_vocabulary(dirty_text)

    print(f"Clean text: '{clean_text}'")
    print(f"  Warnings: {len(clean_warnings)}")
    print(f"Dirty text: '{dirty_text}'")
    print(f"  Warnings: {len(dirty_warnings)} - {dirty_warnings}")
    print()

    # Test v0.4 boundary
    print("Test 2: v0.4 boundary")
    clean_basis = ["v8_blindspot_tag", "v7_reflection_tag"]
    dirty_basis = ["v8_blindspot_tag", "confidence_reason"]

    clean_conf_warnings = check_confidence_boundary(clean_basis)
    dirty_conf_warnings = check_confidence_boundary(dirty_basis)

    print(f"Clean basis: {clean_basis}")
    print(f"  Warnings: {len(clean_conf_warnings)}")
    print(f"Dirty basis: {dirty_basis}")
    print(f"  Warnings: {len(dirty_conf_warnings)} - {dirty_conf_warnings}")
    print()

    # Test observation boundary
    print("Test 3: Observation boundary")
    clean_obs_basis = ["v8_blindspot_tag", "v7_reflection_tag"]
    dirty_obs_basis = ["v8_blindspot_tag", "v5_decision_diff_status"]

    clean_obs_warnings = check_observation_boundary(clean_obs_basis)
    dirty_obs_warnings = check_observation_boundary(dirty_obs_basis)

    print(f"Clean basis: {clean_obs_basis}")
    print(f"  Warnings: {len(clean_obs_warnings)}")
    print(f"Dirty basis: {dirty_obs_basis}")
    print(f"  Warnings: {len(dirty_obs_warnings)} - {dirty_obs_warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
