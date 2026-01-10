# python/confidence/confidence_reason_builder.py
"""
PR28: Confidence Reason Generation Stub (READ-ONLY)

Purpose: Generate confidence_reason following PR27 structure.

This is a minimal stub implementation that produces structurally compliant
reason text without semantic content. Actual reason generation logic will
be implemented in future PRs.

Requirements (PR27 Reason Structure Charter):
- Format: Source:<text>; Stability:<text>; Consistency:<text>; Completeness:<text>
- Human-readable
- Deterministic
- Non-numeric
- Optional (empty string always valid per PR21)

PR28 Implementation:
- Returns empty string (undefined) or minimal structured stub
- No semantic content
- No evaluation logic
- READ-ONLY stub
"""


def build_confidence_reason(observation):
    """
    Build confidence_reason from observation context.

    Args:
        observation: Dict with observation context from PR26

    Returns:
        str: Structured confidence_reason following PR27 format,
             or empty string (undefined per PR21)

    Never raises exceptions - returns empty string or structured stub.

    PR28: Minimal stub - returns empty string (undefined).
    Future PRs will implement actual reason generation logic.
    """
    # PR28: Minimal stub - return undefined (empty string)
    # This satisfies PR21 absence semantics and PR27 structure requirement
    # Future PRs will generate semantic content within PR27 structure
    return ""
