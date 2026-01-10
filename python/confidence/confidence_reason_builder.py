# python/confidence/confidence_reason_builder.py
"""
PR28: Confidence Reason Generation Stub (READ-ONLY)
PR29: Confidence Reason Population (Minimal, READ-ONLY)

Purpose: Generate confidence_reason following PR27 structure.

PR29 Implementation:
- Populates PR27 structure based on observation key presence
- Content is formulaic and non-evaluative
- Based purely on observation structure, not values
- No semantic meaning yet

Requirements (PR27 Reason Structure Charter):
- Format: Source:<text>; Stability:<text>; Consistency:<text>; Completeness:<text>
- Human-readable
- Repeatable (same input → same output)
- Non-numeric (in evaluative sense)
- Optional (empty string always valid per PR21)
"""


def build_confidence_reason(observation):
    """
    Build confidence_reason from observation context.

    Args:
        observation: Dict with observation context from PR26

    Returns:
        str: Structured confidence_reason following PR27 format,
             or empty string (undefined per PR21)

    Never raises exceptions - returns empty string or structured reason.

    PR29: Minimal population based on observation key presence.
    PR29B: Numeric expressions removed, vocabulary-only.
    Future PRs will add semantic content.
    """
    # PR21: Allow empty string for undefined confidence
    if not observation:
        return ""

    # PR27 Structure: Source:<text>; Stability:<text>; Consistency:<text>; Completeness:<text>

    # Source: Which observation keys are present
    source_keys = sorted(observation.keys())
    source_text = ", ".join(source_keys) if source_keys else "empty"

    # Stability: Temporal context availability
    has_recent = any(k.startswith("recent_") for k in observation.keys())
    stability_text = "temporal indicators present" if has_recent else "temporal indicators absent"

    # Consistency: Core signal coverage
    core_keys = {"intent_primary", "regime", "base_action", "overlay_rule"}
    present_core = core_keys & set(observation.keys())
    if len(present_core) == len(core_keys):
        consistency_text = "all core signals present"
    elif len(present_core) > 0:
        consistency_text = "some core signals present"
    else:
        consistency_text = "no core signals present"

    # Completeness: Observation breadth
    has_temporal = any(k.startswith("recent_") for k in observation.keys())
    if not observation:
        completeness_text = "no observations"
    elif has_temporal:
        completeness_text = "temporal and current observations"
    else:
        completeness_text = "current observations only"

    return f"Source:{source_text}; Stability:{stability_text}; Consistency:{consistency_text}; Completeness:{completeness_text}"
