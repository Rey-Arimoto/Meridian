#!/usr/bin/env python3
"""
PR132: v1.2 Contribution Constraints → Explain Context Extension (READ-ONLY)

Purpose:
    Extend PR122 explanation context with contribution constraint zone labels.
    Append-only extension (does not replace existing context).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: No "should" language
    - No numeric patterns: No digits, %
    - No token literals: No SUI, USDC, BTC, ETH
    - No coupling: No "primary therefore act"

Integration Pattern:
    PR122 Explanation Context → append contribution constraints → enhanced context
"""

from typing import Any, Dict, List, Optional


def extend_explain_context_with_contribution_constraints_v1(
    explain_context: Dict[str, Any],
    contribution_constraint_record: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extend explanation context with contribution constraint zone labels (append-only).

    Args:
        explain_context: Existing PR122 explanation context
        contribution_constraint_record: PR132 contribution constraint record

    Returns:
        Extended explanation context (new dict, original unchanged)
    """
    # Create extended context (copy)
    extended_context = dict(explain_context)

    # Append to signal extensions (if exists)
    if "signal_extensions" not in extended_context:
        extended_context["signal_extensions"] = []

    # Create contribution constraint extension block
    constraint_extension = {
        "extension_type": "CONTRIBUTION_CONSTRAINT_BINDING",
        "extension_version": "v1.2",
        "zone_label": contribution_constraint_record.get("v12_contrib_constraint_zone_label", "CONTRIB_ZONE_NONE"),
        "constraint_labels": contribution_constraint_record.get("v12_contrib_constraint_labels", []),
        "regime_level": contribution_constraint_record.get("v12_contrib_constraint_regime_level", "UNCLASSIFIED"),
        "role_type": contribution_constraint_record.get("v12_contrib_constraint_role_type", "UNCLASSIFIED"),
        "distortion_type": contribution_constraint_record.get("v12_contrib_constraint_distortion_type", "UNCLASSIFIED"),
    }

    # Optionally include contribution label if present
    if "v12_contrib_constraint_contribution_label" in contribution_constraint_record:
        constraint_extension["contribution_label"] = contribution_constraint_record["v12_contrib_constraint_contribution_label"]

    # Append contribution constraint extension
    extended_context["signal_extensions"].append(constraint_extension)

    return extended_context


def get_contribution_constraint_extension_summary_v1(
    contribution_constraint_record: Dict[str, Any],
) -> str:
    """
    Generate human-readable summary of contribution constraint extension (label-only).

    Args:
        contribution_constraint_record: PR132 contribution constraint record

    Returns:
        Summary text (no numeric patterns)
    """
    zone_label = contribution_constraint_record.get("v12_contrib_constraint_zone_label", "CONTRIB_ZONE_NONE")
    constraint_labels = contribution_constraint_record.get("v12_contrib_constraint_labels", [])
    regime_level = contribution_constraint_record.get("v12_contrib_constraint_regime_level", "UNCLASSIFIED")
    role_type = contribution_constraint_record.get("v12_contrib_constraint_role_type", "UNCLASSIFIED")
    distortion_type = contribution_constraint_record.get("v12_contrib_constraint_distortion_type", "UNCLASSIFIED")

    # Label-only summary
    constraints_str = ", ".join(constraint_labels) if constraint_labels else "no constraints"
    summary = f"Contribution zone labeled {zone_label} for {regime_level} × {role_type} × {distortion_type}. Constraints: {constraints_str}."

    return summary


def get_contribution_constraint_extension_info() -> Dict[str, Any]:
    """
    Get contribution constraint extension metadata.

    Returns:
        Dict with extension metadata
    """
    return {
        "extension_version": "v1.2",
        "extension_type": "contribution_constraint_binding",
        "extends": "PR122_explanation_context",
        "integration_pattern": "append_only",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Contribution Constraints → Explain Context Extension - Self Test")
    print("=" * 60)
    print()

    # Test 1: Extend explanation context
    print("Test 1: Extend explanation context")
    base_context = {
        "explanation_type": "HUMAN_REVIEW",
        "signal_extensions": [],
    }
    constraint_record = {
        "v12_contrib_constraint_zone_label": "CONTRIB_ZONE_PRIMARY",
        "v12_contrib_constraint_labels": ["contrib_primary_medium_volatility_distortion"],
        "v12_contrib_constraint_regime_level": "REGIME_MEDIUM",
        "v12_contrib_constraint_role_type": "VOLATILITY_ROLE",
        "v12_contrib_constraint_distortion_type": "D1_LIQUIDATION",
        "v12_contrib_constraint_contribution_label": "CONTRIB_STRONGLY_POSITIVE",
    }
    extended = extend_explain_context_with_contribution_constraints_v1(base_context, constraint_record)
    print(json.dumps(extended, indent=2))
    print()

    # Test 2: Generate summary
    print("Test 2: Generate summary")
    summary = get_contribution_constraint_extension_summary_v1(constraint_record)
    print(f"Summary: {summary}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
