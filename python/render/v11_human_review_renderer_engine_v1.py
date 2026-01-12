#!/usr/bin/env python3
"""
PR125: v1.1 Human Review Renderer Engine v1 (READ-ONLY)

Purpose:
    Render approval packet (PR124) into human-readable format.
    Render = Display Shape (not instruction/conclusion).

Engine Philosophy:
    - Defensive: invalid packet → valid ERROR render
    - Structured sections (Labels, Narrative, Preview, Approval, etc.)
    - Style control: CONCISE (one screen), STANDARD (normal), DETAILED (all)
    - No prescriptive language, no conclusions

Render Sections:
    1. Title: Approval Packet (READ-ONLY)
    2. Labels: regime/drift/permission/preview/approval labels
    3. Narrative: Human-readable story (PR123)
    4. Preview: Impact shape only (PR112)
    5. Approval: Gate + Registry state labels (PR113/114)
    6. Rescue Flow: ROLE-to-ROLE rescue structure (PR137/PR138, optional)
    7. Basis & Artifacts: Field/artifact references (DETAILED only)

Constitutional Guarantees:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals, addresses, amounts
    - No trading vocabulary
    - No causal coupling
"""

from typing import Any, Dict, List, Optional
from .v11_review_render_schema import V11ReviewRenderSchema
from .v12_rescue_flow_render_adapter import project_rescue_flow_for_render  # PR138


def render_review_packet_v1(
    packet_record: Optional[Dict[str, Any]] = None,
    fmt: str = "MARKDOWN",
    style: str = "STANDARD",
    rescue_flow_graph: Optional[Dict[str, Any]] = None,  # PR138
) -> Dict[str, Any]:
    """
    Render approval packet into human-readable format.

    Args:
        packet_record: PR124 approval packet record
        fmt: MARKDOWN | TEXT
        style: CONCISE | STANDARD | DETAILED
        rescue_flow_graph: PR137 flow graph record (optional, PR138)

    Returns:
        Render record (always valid, ERROR on failure)
    """
    # Defensive: validate input
    if not packet_record or not isinstance(packet_record, dict):
        return V11ReviewRenderSchema.create_error_record(
            "render generation failed. no packet provided."
        )

    # Validate format and style
    if fmt not in V11ReviewRenderSchema.VALID_FORMATS:
        fmt = "MARKDOWN"
    if style not in V11ReviewRenderSchema.VALID_STYLES:
        style = "STANDARD"

    # Extract packet components
    packet_status = packet_record.get("v11_packet_status", "UNAVAILABLE")
    packet_summary = packet_record.get("v11_packet_summary", "")
    components = packet_record.get("v11_packet_components", {})
    basis = packet_record.get("v11_packet_basis", [])
    artifacts = packet_record.get("v11_packet_artifacts", [])

    # If packet unavailable, return error
    if packet_status != "AVAILABLE":
        return V11ReviewRenderSchema.create_error_record(
            "render generation failed. packet unavailable."
        )

    # Render based on format
    if fmt == "MARKDOWN":
        output = _render_markdown(components, packet_summary, basis, artifacts, style, rescue_flow_graph)
    else:  # TEXT
        output = _render_text(components, packet_summary, basis, artifacts, style, rescue_flow_graph)

    # Collect basis fields
    render_basis = list(dict.fromkeys(basis))  # Deduplicate

    return V11ReviewRenderSchema.create_render_record(
        output=output,
        fmt=fmt,
        style=style,
        basis=render_basis,
    )


def _render_markdown(
    components: Dict[str, Any],
    packet_summary: str,
    basis: List[str],
    artifacts: List[str],
    style: str,
    rescue_flow_graph: Optional[Dict[str, Any]] = None,  # PR138
) -> str:
    """
    Render packet as Markdown.

    Args:
        components: Packet components
        packet_summary: Packet summary
        basis: Basis field names
        artifacts: Artifact names
        style: CONCISE | STANDARD | DETAILED
        rescue_flow_graph: PR137 flow graph record (optional, PR138)

    Returns:
        Markdown string
    """
    lines = []

    # Title
    lines.append("# Approval Packet (READ-ONLY)")
    lines.append("")

    # Section 1: Labels
    labels_section = _render_labels_section(components, style)
    if labels_section:
        lines.append("## Labels")
        lines.append("")
        lines.extend(labels_section)
        lines.append("")

    # Section 2: Narrative (if STANDARD or DETAILED)
    if style in ["STANDARD", "DETAILED"]:
        narrative_section = _render_narrative_section(components)
        if narrative_section:
            lines.append("## Narrative")
            lines.append("")
            lines.extend(narrative_section)
            lines.append("")

    # Section 3: Preview (if STANDARD or DETAILED)
    if style in ["STANDARD", "DETAILED"]:
        preview_section = _render_preview_section(components)
        if preview_section:
            lines.append("## Preview")
            lines.append("")
            lines.extend(preview_section)
            lines.append("")

    # Section 4: Approval (if STANDARD or DETAILED)
    if style in ["STANDARD", "DETAILED"]:
        approval_section = _render_approval_section(components)
        if approval_section:
            lines.append("## Approval")
            lines.append("")
            lines.extend(approval_section)
            lines.append("")

    # Section 4.5: Rescue Flow (if STANDARD or DETAILED, PR138)
    if rescue_flow_graph and style in ["STANDARD", "DETAILED"]:
        rescue_flow_section = _render_rescue_flow_section(rescue_flow_graph, style)
        if rescue_flow_section:
            lines.append("## Rescue Flow")
            lines.append("")
            lines.extend(rescue_flow_section)
            lines.append("")

    # Section 5: Basis & Artifacts (if DETAILED only)
    if style == "DETAILED":
        metadata_section = _render_metadata_section(basis, artifacts)
        if metadata_section:
            lines.append("## Metadata")
            lines.append("")
            lines.extend(metadata_section)
            lines.append("")

    return "\n".join(lines)


def _render_text(
    components: Dict[str, Any],
    packet_summary: str,
    basis: List[str],
    artifacts: List[str],
    style: str,
    rescue_flow_graph: Optional[Dict[str, Any]] = None,  # PR138
) -> str:
    """
    Render packet as plain text.

    Args:
        components: Packet components
        packet_summary: Packet summary
        basis: Basis field names
        artifacts: Artifact names
        style: CONCISE | STANDARD | DETAILED
        rescue_flow_graph: PR137 flow graph record (optional, PR138)

    Returns:
        Plain text string
    """
    lines = []

    # Title
    lines.append("=" * 60)
    lines.append("APPROVAL PACKET (READ-ONLY)")
    lines.append("=" * 60)
    lines.append("")

    # Same sections as Markdown, but with plain text formatting
    labels_section = _render_labels_section(components, style)
    if labels_section:
        lines.append("LABELS:")
        lines.append("-" * 60)
        lines.extend(labels_section)
        lines.append("")

    if style in ["STANDARD", "DETAILED"]:
        narrative_section = _render_narrative_section(components)
        if narrative_section:
            lines.append("NARRATIVE:")
            lines.append("-" * 60)
            lines.extend(narrative_section)
            lines.append("")

        preview_section = _render_preview_section(components)
        if preview_section:
            lines.append("PREVIEW:")
            lines.append("-" * 60)
            lines.extend(preview_section)
            lines.append("")

        approval_section = _render_approval_section(components)
        if approval_section:
            lines.append("APPROVAL:")
            lines.append("-" * 60)
            lines.extend(approval_section)
            lines.append("")

        # Rescue Flow section (PR138)
        if rescue_flow_graph:
            rescue_flow_section = _render_rescue_flow_section(rescue_flow_graph, style)
            if rescue_flow_section:
                lines.append("RESCUE FLOW:")
                lines.append("-" * 60)
                lines.extend(rescue_flow_section)
                lines.append("")

    if style == "DETAILED":
        metadata_section = _render_metadata_section(basis, artifacts)
        if metadata_section:
            lines.append("METADATA:")
            lines.append("-" * 60)
            lines.extend(metadata_section)
            lines.append("")

    return "\n".join(lines)


def _render_labels_section(components: Dict[str, Any], style: str) -> List[str]:
    """Render labels section."""
    lines = []

    # Extract labels from components
    explain_context = components.get("explain_context", {})
    preview = components.get("preview", {})
    approval_gate = components.get("approval_gate", {})

    # Extract signals from explain_context
    signals = explain_context.get("v11_explain_signals", [])
    if isinstance(signals, list):
        for signal in signals:
            if style == "CONCISE":
                lines.append(f"- {signal}")
            else:
                lines.append(f"- {signal}")

    # Add preview risk surface
    risk_surface = preview.get("v11_preview_risk_surface", None)
    if risk_surface:
        lines.append(f"- PREVIEW_RISK_SURFACE: {risk_surface}")

    # Add approval requirement
    requirement = approval_gate.get("v11_approval_requirement", None)
    if requirement:
        lines.append(f"- APPROVAL_REQUIREMENT: {requirement}")

    # Add approval state
    state = approval_gate.get("v11_approval_state", None)
    if state:
        lines.append(f"- APPROVAL_STATE: {state}")

    return lines


def _render_narrative_section(components: Dict[str, Any]) -> List[str]:
    """Render narrative section."""
    lines = []

    narrative = components.get("narrative", {})
    text = narrative.get("v11_narrative_text", "")

    if text:
        lines.append(text)

    return lines


def _render_preview_section(components: Dict[str, Any]) -> List[str]:
    """Render preview section."""
    lines = []

    preview = components.get("preview", {})

    # Risk surface
    risk_surface = preview.get("v11_preview_risk_surface", "")
    if risk_surface:
        lines.append(f"Risk Surface: {risk_surface}")

    # Preview status
    status = preview.get("v11_preview_status", "")
    if status:
        lines.append(f"Status: {status}")

    return lines


def _render_approval_section(components: Dict[str, Any]) -> List[str]:
    """Render approval section."""
    lines = []

    approval_gate = components.get("approval_gate", {})
    approval_registry = components.get("approval_registry", {})

    # Gate
    requirement = approval_gate.get("v11_approval_requirement", "")
    state = approval_gate.get("v11_approval_state", "")

    if requirement:
        lines.append(f"Requirement: {requirement}")
    if state:
        lines.append(f"State: {state}")

    # Registry (if present)
    if approval_registry:
        registry_status = approval_registry.get("v11_registry_status", "")
        if registry_status:
            lines.append(f"Registry Status: {registry_status}")

    return lines


def _render_rescue_flow_section(
    rescue_flow_graph: Dict[str, Any],
    style: str,
) -> List[str]:
    """
    Render rescue flow section (PR138).

    Args:
        rescue_flow_graph: PR137 flow graph record
        style: CONCISE | STANDARD | DETAILED

    Returns:
        List of formatted lines
    """
    lines = []

    # Use adapter to project flow graph
    flow_lines = project_rescue_flow_for_render(rescue_flow_graph, style)

    if not flow_lines:
        return []

    # Add intro text (non-prescriptive)
    lines.append("ROLE-to-ROLE structural rescue mapping (label-only):")
    lines.append("")

    # Add flow lines
    for flow_line in flow_lines:
        lines.append(f"- {flow_line}")

    return lines


def _render_metadata_section(basis: List[str], artifacts: List[str]) -> List[str]:
    """Render metadata section (DETAILED only)."""
    lines = []

    if basis:
        lines.append("**Basis Fields:**")
        for field in basis:
            lines.append(f"- {field}")
        lines.append("")

    if artifacts:
        lines.append("**Artifacts:**")
        for artifact in artifacts:
            lines.append(f"- {artifact}")

    return lines


def get_renderer_v1_info() -> Dict[str, Any]:
    """
    Get renderer v1 information.

    Returns:
        Dict with renderer metadata
    """
    return {
        "renderer_version": "v1",
        "renderer_type": "human_review_renderer",
        "supported_formats": V11ReviewRenderSchema.VALID_FORMATS,
        "supported_styles": V11ReviewRenderSchema.VALID_STYLES,
        "input_schema": "v11_approval_packet",
        "output_schema": "v11_review_render",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "defensive",
            "no_causal_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.1 Human Review Renderer Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Invalid input → ERROR
    print("Test 1: Invalid input → ERROR")
    result1 = render_review_packet_v1(None)
    print(f"Status: {result1['v11_render_status']}")
    print(f"Summary: {result1['v11_render_summary']}")
    print()

    # Test 2: Minimal packet
    print("Test 2: Minimal packet")
    packet2 = {
        "v11_packet_status": "AVAILABLE",
        "v11_packet_summary": "test",
        "v11_packet_components": {
            "explain_context": {
                "v11_explain_signals": ["REGIME_MEDIUM", "DRIFT_LOW"],
            },
        },
        "v11_packet_basis": ["v11_regime_level"],
    }
    result2 = render_review_packet_v1(packet2, fmt="MARKDOWN", style="CONCISE")
    print(f"Status: {result2['v11_render_status']}")
    print(f"Output length: {len(result2['v11_render_output'])} chars")
    print("Output preview:")
    print(result2['v11_render_output'][:200])
    print()

    # Test 3: Full packet with narrative
    print("Test 3: Full packet with narrative")
    packet3 = {
        "v11_packet_status": "AVAILABLE",
        "v11_packet_summary": "test",
        "v11_packet_components": {
            "explain_context": {
                "v11_explain_signals": ["REGIME_HIGH", "DRIFT_MEDIUM"],
            },
            "narrative": {
                "v11_narrative_text": "current regime label indicates high entropy. structural drift label indicates shifting market vocabulary.",
            },
            "preview": {
                "v11_preview_status": "AVAILABLE",
                "v11_preview_risk_surface": "CONSTRAINED",
            },
            "approval_gate": {
                "v11_approval_requirement": "REQUIRED",
                "v11_approval_state": "UNREQUESTED",
            },
        },
        "v11_packet_basis": ["v11_regime_level", "v10_drift_level"],
        "v11_packet_artifacts": ["pr110_regime_record", "pr120_drift_record"],
    }
    result3 = render_review_packet_v1(packet3, fmt="MARKDOWN", style="STANDARD")
    print(f"Status: {result3['v11_render_status']}")
    print("Full output:")
    print(result3['v11_render_output'])
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
