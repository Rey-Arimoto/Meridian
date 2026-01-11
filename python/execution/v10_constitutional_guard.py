#!/usr/bin/env python3
"""
PR100: v1.0 Execution Constitutional Guard (READ-ONLY)

Purpose:
    Enforce constitutional constraints on execution records.
    Guards against violations of v1.0 execution principles.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Boundary-bound: Only uses v6/v7/v8/v9 fields as basis
    - Execution safety: No trading vocabulary

Guards:
    1. Forbidden vocabulary (evaluative/scoric/prescriptive)
    2. v0.4 boundary (no confidence_reason)
    3. Observation boundary (no v5 observation fields)
    4. Execution safety guard (no trading vocabulary)

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
    import re
    warnings = []
    text_lower = text.lower()

    for word in FORBIDDEN_VOCABULARY:
        # Use word boundaries to avoid false positives (e.g., "win" in "window")
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_lower):
            warnings.append(f"Forbidden vocabulary detected: '{word}' in text")

    return warnings


# ============================================================================
# Execution Safety Guard (v1.0 NEW)
# ============================================================================

EXECUTION_ACTION_VOCABULARY = [
    # Trading actions
    "swap",
    "transfer",
    "send",
    "approve",
    "sign",
    "broadcast",
    "execute",
    "trade",
    "buy",
    "sell",
    "order",
    # Position management
    "open position",
    "close position",
    "increase",
    "decrease",
    "liquidate",
    "rebalance",
    # Specific instructions
    "set target",
    "allocate",
    "distribute",
    "move funds",
]


def check_execution_safety(text: str) -> List[str]:
    """
    Check if text contains execution action vocabulary.

    Args:
        text: Text to check

    Returns:
        List of warnings (empty if clean)
    """
    warnings = []
    text_lower = text.lower()

    # Valid intent/plan type patterns that should not trigger warnings
    # (e.g., "rebalance intent", "hedge intent", "rebalance plan", "hedge plan")
    safe_exceptions = [
        # Intent descriptions
        "rebalance intent",
        "hedge intent",
        "liquidity intent",
        "maintenance intent",
        # Plan descriptions
        "rebalance plan",
        "hedge plan",
        "liquidity plan",
        "maintenance plan",
    ]

    for word in EXECUTION_ACTION_VOCABULARY:
        if word in text_lower:
            # Check if this match is part of a safe description
            is_safe_description = False
            for exception in safe_exceptions:
                if word in exception and exception in text_lower:
                    is_safe_description = True
                    break

            if not is_safe_description:
                warnings.append(f"Execution action vocabulary detected: '{word}' in text")

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
                "(execution must not access v0.4 confidence layer)"
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
                "(execution must only access v6/v7/v8/v9 fields)"
            )

    return warnings


# ============================================================================
# Complete Record Validation
# ============================================================================

def validate_execution_record(record: Dict[str, Any]) -> List[str]:
    """
    Validate complete execution record against all constitutional guards.

    Args:
        record: Execution record to validate

    Returns:
        List of warnings (empty if valid)
    """
    warnings = []

    # Check intent vocabulary
    if "v10_execution_intent" in record:
        intent_warnings = check_forbidden_vocabulary(record["v10_execution_intent"])
        warnings.extend(intent_warnings)

        intent_safety_warnings = check_execution_safety(record["v10_execution_intent"])
        warnings.extend(intent_safety_warnings)

    # Check summary vocabulary
    if "v10_execution_summary" in record:
        summary_warnings = check_forbidden_vocabulary(record["v10_execution_summary"])
        warnings.extend(summary_warnings)

        summary_safety_warnings = check_execution_safety(record["v10_execution_summary"])
        warnings.extend(summary_safety_warnings)

    # Check basis boundaries
    if "v10_execution_basis" in record:
        basis = record["v10_execution_basis"]

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
    print("v1.0 Execution Constitutional Guard - Self Test")
    print("=" * 60)
    print()

    # Test forbidden vocabulary
    print("Test 1: Forbidden vocabulary")
    clean_text = "execution intent based on boundary analysis"
    dirty_text = "this is a good opportunity that should be taken"

    clean_warnings = check_forbidden_vocabulary(clean_text)
    dirty_warnings = check_forbidden_vocabulary(dirty_text)

    print(f"Clean text: '{clean_text}'")
    print(f"  Warnings: {len(clean_warnings)}")
    print(f"Dirty text: '{dirty_text}'")
    print(f"  Warnings: {len(dirty_warnings)} - {dirty_warnings}")
    print()

    # Test execution safety
    print("Test 2: Execution safety")
    clean_exec_text = "maintenance intent observed"
    dirty_exec_text = "swap tokens and transfer funds"

    clean_exec_warnings = check_execution_safety(clean_exec_text)
    dirty_exec_warnings = check_execution_safety(dirty_exec_text)

    print(f"Clean text: '{clean_exec_text}'")
    print(f"  Warnings: {len(clean_exec_warnings)}")
    print(f"Dirty text: '{dirty_exec_text}'")
    print(f"  Warnings: {len(dirty_exec_warnings)} - {dirty_exec_warnings}")
    print()

    # Test v0.4 boundary
    print("Test 3: v0.4 boundary")
    clean_basis = ["v9_boundary_type", "v8_blindspot_tag"]
    dirty_basis = ["v9_boundary_type", "confidence_reason"]

    clean_conf_warnings = check_confidence_boundary(clean_basis)
    dirty_conf_warnings = check_confidence_boundary(dirty_basis)

    print(f"Clean basis: {clean_basis}")
    print(f"  Warnings: {len(clean_conf_warnings)}")
    print(f"Dirty basis: {dirty_basis}")
    print(f"  Warnings: {len(dirty_conf_warnings)} - {dirty_conf_warnings}")
    print()

    # Test observation boundary
    print("Test 4: Observation boundary")
    clean_obs_basis = ["v9_boundary_type", "v8_blindspot_tag"]
    dirty_obs_basis = ["v9_boundary_type", "v5_decision_diff_status"]

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
