#!/usr/bin/env python3
"""
PR131: v1.2 Explain Context Contribution Extension (READ-ONLY)

Purpose:
    Extend PR122 explanation context with contribution model signals.
    Append-only extension (does not replace existing context).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: No "should" language
    - No numeric patterns: No digits, %, decimals
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No return guarantee language
    - No coupling: No "contribution therefore act"

Integration Pattern:
    PR122 Explanation Context → append contribution signals → enhanced context
"""

from typing import Any, Dict, List, Optional


def extend_explain_context_with_contribution_v1(
    explain_context: Dict[str, Any],
    contribution_record: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Extend explanation context with contribution signals (append-only).

    Args:
        explain_context: Existing PR122 explanation context
        contribution_record: PR131 contribution record

    Returns:
        Extended explanation context (new dict, original unchanged)
    """
    # Import contribution signal converter
    from contribution import contribution_to_explain_signals_v1

    # Create extended context (copy)
    extended_context = dict(explain_context)

    # Get contribution signals
    contrib_signals = contribution_to_explain_signals_v1(contribution_record)

    # Append to signal extensions (if exists)
    if "signal_extensions" not in extended_context:
        extended_context["signal_extensions"] = []

    # Create contribution signal extension block
    contrib_extension = {
        "extension_type": "CONTRIBUTION_MODEL",
        "extension_version": "v1.2",
        "contribution_label": contribution_record.get("v12_contrib_contribution_label", "CONTRIB_UNKNOWN"),
        "contribution_rationale": contribution_record.get("v12_contrib_contribution_rationale", []),
        "contribution_signals": contrib_signals,
        "regime_level": contribution_record.get("v12_contrib_regime_level", "UNCLASSIFIED"),
        "role_type": contribution_record.get("v12_contrib_role_type", "UNCLASSIFIED"),
        "distortion_type": contribution_record.get("v12_contrib_distortion_type", "UNCLASSIFIED"),
    }

    # Optionally include eligibility label if present
    if "v12_contrib_eligibility_label" in contribution_record:
        contrib_extension["eligibility_label"] = contribution_record["v12_contrib_eligibility_label"]

    # Append contribution extension
    extended_context["signal_extensions"].append(contrib_extension)

    return extended_context


def get_contribution_extension_summary_v1(
    contribution_record: Dict[str, Any],
) -> str:
    """
    Generate human-readable summary of contribution extension (label-only).

    Args:
        contribution_record: PR131 contribution record

    Returns:
        Summary text (no numeric patterns)
    """
    contribution_label = contribution_record.get("v12_contrib_contribution_label", "CONTRIB_UNKNOWN")
    regime_level = contribution_record.get("v12_contrib_regime_level", "UNCLASSIFIED")
    role_type = contribution_record.get("v12_contrib_role_type", "UNCLASSIFIED")
    distortion_type = contribution_record.get("v12_contrib_distortion_type", "UNCLASSIFIED")
    rationale = contribution_record.get("v12_contrib_contribution_rationale", [])

    # Label-only summary
    rationale_str = ", ".join(rationale) if rationale else "no rationale"
    summary = f"Contribution labeled {contribution_label} for {regime_level} × {role_type} × {distortion_type}. Rationale: {rationale_str}."

    return summary


def get_contribution_extension_info() -> Dict[str, Any]:
    """
    Get contribution extension metadata.

    Returns:
        Dict with extension metadata
    """
    return {
        "extension_version": "v1.2",
        "extension_type": "contribution_model",
        "extends": "PR122_explanation_context",
        "integration_pattern": "append_only",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_return_guarantees",
            "no_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Explain Context Contribution Extension - Self Test")
    print("=" * 60)
    print()

    # Test 1: Extend explanation context
    print("Test 1: Extend explanation context")
    base_context = {
        "explanation_type": "HUMAN_REVIEW",
        "signal_extensions": [],
    }
    contrib_record = {
        "v12_contrib_contribution_label": "CONTRIB_STRONGLY_POSITIVE",
        "v12_contrib_contribution_rationale": ["DISTORTION_CAPTURE_ZONE", "STRUCTURE_INTELLIGIBLE"],
        "v12_contrib_regime_level": "REGIME_MEDIUM",
        "v12_contrib_role_type": "VOLATILITY_ROLE",
        "v12_contrib_distortion_type": "D1_LIQUIDATION",
        "v12_contrib_eligibility_label": "ELIGIBLE_CONSIDERATION_ONLY",
    }
    extended = extend_explain_context_with_contribution_v1(base_context, contrib_record)
    print(json.dumps(extended, indent=2))
    print()

    # Test 2: Generate summary
    print("Test 2: Generate summary")
    summary = get_contribution_extension_summary_v1(contrib_record)
    print(f"Summary: {summary}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
