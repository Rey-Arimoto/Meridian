#!/usr/bin/env python3
"""
PR123: v1.1 Human Narrative Builder Engine v1 (READ-ONLY)

Purpose:
    Convert explanation context (PR122) into human-readable narrative.
    Narrative = Structural Situation Story (not action/recommendation).

Engine Philosophy:
    - Deterministic templates (no LLM, no randomness)
    - Label-based language (regime, drift, permission)
    - Style toggles only change verbosity (CONCISE/STANDARD/DETAILED)
    - Defensive: invalid input → valid ERROR record

Narrative Language:
    Use "may / can / indicates / is labeled as" language.
    Avoid "should / must / do X".

Constitutional Guarantees:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals, addresses, amounts
    - No trading vocabulary
"""

from typing import Any, Dict, List, Optional
from .v11_human_narrative_schema import V11HumanNarrativeSchema


def build_human_narrative_v1(
    explain_context_record: Optional[Dict[str, Any]] = None,
    style: str = "STANDARD",
) -> Dict[str, Any]:
    """
    Build human narrative from explanation context.

    Args:
        explain_context_record: Explanation context record (PR122)
        style: CONCISE | STANDARD | DETAILED

    Returns:
        Narrative record (always valid, ERROR on failure)
    """
    # Defensive: validate input
    if not explain_context_record or not isinstance(explain_context_record, dict):
        return V11HumanNarrativeSchema.create_error_record(
            "narrative generation failed. no explanation context provided."
        )

    # Validate style
    if style not in V11HumanNarrativeSchema.VALID_STYLES:
        style = "STANDARD"

    # Extract explanation context fields
    explain_status = explain_context_record.get("v11_explain_status", "UNAVAILABLE")
    explain_summary = explain_context_record.get("v11_explain_summary", "")
    explain_signals = explain_context_record.get("v11_explain_signals", [])
    explain_basis = explain_context_record.get("v11_explain_basis", [])
    explain_artifacts = explain_context_record.get("v11_explain_artifacts", [])

    # If explanation unavailable, return error
    if explain_status != "AVAILABLE":
        return V11HumanNarrativeSchema.create_error_record(
            "narrative generation failed. explanation context unavailable."
        )

    # Build narrative text from signals
    narrative_text = _generate_narrative_from_signals(explain_signals, style)

    # If no narrative generated, fallback to summary
    if not narrative_text:
        narrative_text = _generate_narrative_from_summary(explain_summary, style)

    # If still no narrative, return error
    if not narrative_text:
        return V11HumanNarrativeSchema.create_error_record(
            "narrative generation failed. insufficient context."
        )

    # Create narrative record
    return V11HumanNarrativeSchema.create_narrative_record(
        text=narrative_text,
        style=style,
        basis=explain_basis,
        artifacts=explain_artifacts,
    )


def _generate_narrative_from_signals(signals: List[str], style: str) -> str:
    """
    Generate narrative text from signal labels.

    Args:
        signals: Signal labels from explanation context
        style: CONCISE | STANDARD | DETAILED

    Returns:
        Narrative text (or empty string if no signals)
    """
    if not signals or not isinstance(signals, list):
        return ""

    # Categorize signals
    regime_signals = [s for s in signals if s.startswith("REGIME_")]
    drift_signals = [s for s in signals if s.startswith("DRIFT_")]
    permission_signals = [s for s in signals if s.startswith("PERMISSION_")]
    preview_signals = [s for s in signals if s.startswith("PREVIEW_")]
    approval_signals = [s for s in signals if s.startswith("APPROVAL_")]

    # Build narrative fragments
    fragments = []

    # Regime fragment
    if regime_signals:
        regime_fragment = _build_regime_fragment(regime_signals[0], style)
        if regime_fragment:
            fragments.append(regime_fragment)

    # Drift fragment
    if drift_signals:
        drift_fragment = _build_drift_fragment(drift_signals[0], style)
        if drift_fragment:
            fragments.append(drift_fragment)

    # Permission fragment
    if permission_signals:
        permission_fragment = _build_permission_fragment(permission_signals[0], style)
        if permission_fragment:
            fragments.append(permission_fragment)

    # Preview fragment
    if preview_signals:
        preview_fragment = _build_preview_fragment(preview_signals[0], style)
        if preview_fragment:
            fragments.append(preview_fragment)

    # Approval fragment
    if approval_signals:
        approval_fragment = _build_approval_fragment(approval_signals[0], style)
        if approval_fragment:
            fragments.append(approval_fragment)

    # Join fragments
    if not fragments:
        return ""

    return " ".join(fragments)


def _build_regime_fragment(signal: str, style: str) -> str:
    """Build regime narrative fragment."""
    templates = {
        "REGIME_LOW": {
            "CONCISE": "regime label low.",
            "STANDARD": "current regime label indicates low entropy.",
            "DETAILED": "current entropy regime label indicates low market entropy. structural assumptions may hold.",
        },
        "REGIME_MEDIUM": {
            "CONCISE": "regime label medium.",
            "STANDARD": "current regime label indicates elevated uncertainty.",
            "DETAILED": "current entropy regime label indicates elevated market uncertainty. structural assumptions may weaken.",
        },
        "REGIME_HIGH": {
            "CONCISE": "regime label high.",
            "STANDARD": "current regime label indicates high entropy.",
            "DETAILED": "current entropy regime label indicates high market entropy. structural assumptions are weakening.",
        },
        "REGIME_CRITICAL": {
            "CONCISE": "regime label critical.",
            "STANDARD": "current regime label indicates critical entropy.",
            "DETAILED": "current entropy regime label indicates critical market entropy. structural assumptions may collapse.",
        },
    }

    return templates.get(signal, {}).get(style, "")


def _build_drift_fragment(signal: str, style: str) -> str:
    """Build drift narrative fragment."""
    templates = {
        "DRIFT_NONE": {
            "CONCISE": "drift label none.",
            "STANDARD": "structural drift label indicates stable vocabulary.",
            "DETAILED": "structural vocabulary drift label indicates no observable language shift. market structure vocabulary remains stable.",
        },
        "DRIFT_LOW": {
            "CONCISE": "drift label low.",
            "STANDARD": "structural drift label indicates low vocabulary shift.",
            "DETAILED": "structural vocabulary drift label indicates low language shift. market structure vocabulary shows minor changes.",
        },
        "DRIFT_MEDIUM": {
            "CONCISE": "drift label medium.",
            "STANDARD": "structural drift label indicates shifting market vocabulary.",
            "DETAILED": "structural vocabulary drift label indicates observable language shift. market structure vocabulary is changing.",
        },
        "DRIFT_HIGH": {
            "CONCISE": "drift label high.",
            "STANDARD": "structural drift label indicates significant vocabulary shift.",
            "DETAILED": "structural vocabulary drift label indicates significant language shift. market structure vocabulary is unstable.",
        },
        "DRIFT_CRITICAL": {
            "CONCISE": "drift label critical.",
            "STANDARD": "structural drift label indicates critical vocabulary disruption.",
            "DETAILED": "structural vocabulary drift label indicates critical language disruption. market structure vocabulary may be unreliable.",
        },
    }

    return templates.get(signal, {}).get(style, "")


def _build_permission_fragment(signal: str, style: str) -> str:
    """Build permission narrative fragment."""
    templates = {
        "PERMISSION_UNKNOWN": {
            "CONCISE": "permission label unknown.",
            "STANDARD": "execution permission label is unknown.",
            "DETAILED": "execution permission label is unknown. permission state cannot be determined from available context.",
        },
        "PERMISSION_HOLD": {
            "CONCISE": "permission label hold.",
            "STANDARD": "execution permission label indicates hold state.",
            "DETAILED": "execution permission label indicates hold state. consideration of execution operations is withheld.",
        },
        "PERMISSION_DRY_RUN_ONLY": {
            "CONCISE": "permission label dry-run-only.",
            "STANDARD": "execution permission label limits consideration to dry-run-only.",
            "DETAILED": "execution permission label limits consideration to dry-run-only. live execution operations are withheld.",
        },
        "PERMISSION_ALLOW": {
            "CONCISE": "permission label allow.",
            "STANDARD": "execution permission label indicates allow state.",
            "DETAILED": "execution permission label indicates allow state. execution operations may be considered subject to approval.",
        },
    }

    return templates.get(signal, {}).get(style, "")


def _build_preview_fragment(signal: str, style: str) -> str:
    """Build preview narrative fragment."""
    templates = {
        "PREVIEW_BLOCKED": {
            "CONCISE": "preview label blocked.",
            "STANDARD": "preview label indicates interaction surface is blocked.",
            "DETAILED": "execution preview label indicates interaction surface is blocked. operations cannot proceed.",
        },
        "PREVIEW_AVAILABLE": {
            "CONCISE": "preview label available.",
            "STANDARD": "preview label indicates interaction surface is available.",
            "DETAILED": "execution preview label indicates interaction surface is available. operations can be considered.",
        },
    }

    return templates.get(signal, {}).get(style, "")


def _build_approval_fragment(signal: str, style: str) -> str:
    """Build approval narrative fragment."""
    templates = {
        "APPROVAL_NOT_REQUIRED": {
            "CONCISE": "approval label not required.",
            "STANDARD": "approval label indicates human withholding is not required.",
            "DETAILED": "human approval label indicates withholding is not required for current structural state.",
        },
        "APPROVAL_REQUIRED": {
            "CONCISE": "approval label required.",
            "STANDARD": "approval label indicates human withholding may be required.",
            "DETAILED": "human approval label indicates withholding may be required. human review is recommended for current structural state.",
        },
        "APPROVAL_REQUIRED_STRICT": {
            "CONCISE": "approval label required strict.",
            "STANDARD": "approval label indicates human withholding is required.",
            "DETAILED": "human approval label indicates withholding is required. human review is mandatory for current structural state.",
        },
    }

    return templates.get(signal, {}).get(style, "")


def _generate_narrative_from_summary(summary: str, style: str) -> str:
    """
    Generate narrative text from explanation summary (fallback).

    Args:
        summary: Explanation summary text
        style: CONCISE | STANDARD | DETAILED

    Returns:
        Narrative text (or empty string if no summary)
    """
    if not summary or not isinstance(summary, str):
        return ""

    # Use summary as-is (already non-prescriptive from PR122)
    if style == "CONCISE":
        # Take first sentence only
        first_sentence = summary.split(".")[0] + "."
        return first_sentence
    elif style == "DETAILED":
        # Add context prefix
        return f"structural situation summary: {summary}"
    else:
        # STANDARD: use as-is
        return summary


def get_narrative_builder_v1_info() -> Dict[str, Any]:
    """
    Get narrative builder v1 information.

    Returns:
        Dict with builder metadata
    """
    return {
        "builder_version": "v1",
        "builder_type": "human_narrative_builder",
        "supported_styles": V11HumanNarrativeSchema.VALID_STYLES,
        "input_schema": "v11_explanation_context",
        "output_schema": "v11_human_narrative",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "deterministic_templates",
            "no_llm",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Human Narrative Builder Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Invalid input → ERROR record
    print("Test 1: Invalid input → ERROR record")
    result1 = build_human_narrative_v1(None)
    print(f"Status: {result1['v11_narrative_status']}")
    print(f"Text: {result1['v11_narrative_text']}")
    print()

    # Test 2: Minimal valid context
    print("Test 2: Minimal valid context")
    context2 = {
        "v11_explain_status": "AVAILABLE",
        "v11_explain_summary": "test summary.",
        "v11_explain_signals": ["REGIME_MEDIUM", "DRIFT_LOW"],
        "v11_explain_basis": ["v11_regime_level", "v10_drift_level"],
    }
    result2 = build_human_narrative_v1(context2, style="STANDARD")
    print(f"Status: {result2['v11_narrative_status']}")
    print(f"Text: {result2['v11_narrative_text']}")
    print()

    # Test 3: CONCISE style
    print("Test 3: CONCISE style")
    result3 = build_human_narrative_v1(context2, style="CONCISE")
    print(f"Text: {result3['v11_narrative_text']}")
    print()

    # Test 4: DETAILED style
    print("Test 4: DETAILED style")
    result4 = build_human_narrative_v1(context2, style="DETAILED")
    print(f"Text: {result4['v11_narrative_text']}")
    print()

    # Test 5: Full signal set
    print("Test 5: Full signal set")
    context5 = {
        "v11_explain_status": "AVAILABLE",
        "v11_explain_summary": "test",
        "v11_explain_signals": [
            "REGIME_HIGH",
            "DRIFT_MEDIUM",
            "PERMISSION_DRY_RUN_ONLY",
            "PREVIEW_AVAILABLE",
            "APPROVAL_REQUIRED",
        ],
        "v11_explain_basis": ["v11_regime_level", "v10_drift_level", "v10_execution_permission"],
        "v11_explain_artifacts": ["pr110_regime_record", "pr120_drift_record"],
    }
    result5 = build_human_narrative_v1(context5, style="STANDARD")
    print(f"Text: {result5['v11_narrative_text']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
