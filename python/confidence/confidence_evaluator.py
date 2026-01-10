# python/confidence/confidence_evaluator.py
"""
PR24: Confidence Evaluator (Minimal Hook)

Purpose: Provide evaluation hook for Confidence assessment.

This is a minimal implementation that reserves the architectural seat.
Actual Confidence logic will be implemented in future PRs.

Requirements (PR20 Representation Charter):
- Return human-readable representation
- Deterministic (same state → same output)
- Auditable (value + reason explain assessment)

PR24 Implementation:
- Returns undefined (empty strings)
- No decision logic
- No action influence
- READ-ONLY hook
"""

from typing import Tuple, Dict, Any


def evaluate_confidence(context: Dict[str, Any]) -> Tuple[str, str]:
    """
    Evaluate Confidence from system state.

    Args:
        context: Dictionary containing system state (entropy, regime, etc.)

    Returns:
        Tuple of (confidence_value, confidence_reason)

    PR24: Minimal implementation - returns undefined (empty strings).
    Future PRs will implement actual Confidence assessment logic.
    """
    # PR24: Minimal hook - return undefined
    # This reserves the architectural seat without introducing logic
    confidence_value = ""
    confidence_reason = ""

    return confidence_value, confidence_reason
