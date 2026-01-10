# python/confidence/confidence_evaluator.py
"""
PR24: Confidence Evaluator (Minimal Hook)
PR28: Confidence Reason Generation Stub

Purpose: Provide evaluation hook for Confidence assessment.

This is a minimal implementation that reserves the architectural seat.
Actual Confidence logic will be implemented in future PRs.

Requirements (PR20 Representation Charter):
- Return human-readable representation
- Deterministic (same state → same output)
- Auditable (value + reason explain assessment)

PR24 Implementation:
- Returns undefined confidence_value (empty string)
- No decision logic
- No action influence
- READ-ONLY hook

PR28 Implementation:
- confidence_reason generated via builder (PR27 structure)
- Still minimal stub (no semantic content)
"""

from confidence.confidence_reason_builder import build_confidence_reason


def evaluate_confidence(context):
    """
    Evaluate Confidence from system state.

    Args:
        context: Dictionary containing system state (entropy, regime, etc.)

    Returns:
        Tuple of (confidence_value, confidence_reason)

    PR24/PR28: Minimal implementation.
    - confidence_value: undefined (empty string)
    - confidence_reason: generated via builder (PR27 structure)
    Future PRs will implement actual Confidence assessment logic.
    """
    # PR24: confidence_value remains undefined (empty string)
    confidence_value = ""

    # PR28: confidence_reason generated via builder (PR27 structure)
    confidence_reason = build_confidence_reason(context)

    return confidence_value, confidence_reason
