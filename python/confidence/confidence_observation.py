# python/confidence/confidence_observation.py
"""
PR26: Confidence Observation Wiring (READ-ONLY)

Purpose: Define observation context schema for Confidence evaluation.

This module provides the fixed keyset for observations passed to Confidence
evaluator, enforcing PR25 source category boundaries.

Requirements:
- Fixed keyset (no arbitrary keys)
- Graceful handling of missing observations
- No exceptions thrown
- READ-ONLY (no behavior changes)

Non-Goals:
- No observation value interpretation
- No Confidence logic
- No decision influence
"""


def build_confidence_observation(
    intent_primary,
    regime,
    base_action,
    overlay_rule,
    entropy_bp,
    recent_intent_primary="",
    recent_regime="",
    recent_base_action="",
    recent_overlay_rule="",
    data_health_flag=""
):
    """
    Build observation context for Confidence evaluation.

    Args:
        intent_primary: Current Intent classification
        regime: Current regime classification
        base_action: Current base action
        overlay_rule: Current overlay rule
        entropy_bp: Current entropy in basis points
        recent_intent_primary: Recent Intent sequence (optional)
        recent_regime: Recent regime sequence (optional)
        recent_base_action: Recent action sequence (optional)
        recent_overlay_rule: Recent overlay sequence (optional)
        data_health_flag: Data health status (optional)

    Returns:
        Dict with observation context for Confidence evaluator

    Never raises exceptions - returns dict with available observations.
    """
    # Required observations (always present)
    observation = {
        "intent_primary": intent_primary if intent_primary else "",
        "regime": regime if regime else "",
        "base_action": base_action if base_action else "",
        "overlay_rule": overlay_rule if overlay_rule else "",
        "entropy_bp": entropy_bp,
    }

    # Optional observations (include only if provided)
    if recent_intent_primary:
        observation["recent_intent_primary"] = recent_intent_primary
    if recent_regime:
        observation["recent_regime"] = recent_regime
    if recent_base_action:
        observation["recent_base_action"] = recent_base_action
    if recent_overlay_rule:
        observation["recent_overlay_rule"] = recent_overlay_rule
    if data_health_flag:
        observation["data_health_flag"] = data_health_flag

    return observation
