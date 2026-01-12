#!/usr/bin/env python3
"""
PR124: v1.1 Approval Packet Builder Engine v1 (READ-ONLY)

Purpose:
    Assemble approval packet from component records.
    Packet = Review Unit Carrier (not decision/instruction).

Engine Philosophy:
    - Defensive: missing/invalid components → still returns valid packet
    - Fixed component ordering (stable output)
    - Non-prescriptive summary templates
    - No cross-component coupling language

Packet Assembly:
    Components bundled:
    - PR122: Explanation Context
    - PR123: Narrative
    - PR112: Preview
    - PR113: Approval Gate
    - PR114: Approval Registry

Constitutional Guarantees:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals, addresses, amounts
    - No trading vocabulary
    - No cross-component coupling
"""

from typing import Any, Dict, List, Optional
from .v11_approval_packet_schema import V11ApprovalPacketSchema


def build_approval_packet_v1(
    explain_context_record: Optional[Dict[str, Any]] = None,
    narrative_record: Optional[Dict[str, Any]] = None,
    preview_record: Optional[Dict[str, Any]] = None,
    approval_gate_record: Optional[Dict[str, Any]] = None,
    approval_registry_record: Optional[Dict[str, Any]] = None,
    use_minimal_projections: bool = False,
) -> Dict[str, Any]:
    """
    Build approval packet from component records.

    Args:
        explain_context_record: PR122 explanation context record
        narrative_record: PR123 narrative record
        preview_record: PR112 preview record
        approval_gate_record: PR113 approval gate record
        approval_registry_record: PR114 approval registry record
        use_minimal_projections: If True, store minimal projections instead of full records

    Returns:
        Approval packet record (always valid, ERROR on failure)
    """
    # Defensive: validate at least one component provided
    if not any([explain_context_record, narrative_record, preview_record, approval_gate_record, approval_registry_record]):
        return V11ApprovalPacketSchema.create_error_record(
            "packet assembly failed. no components provided."
        )

    # Build components dict
    components = {}
    basis_fields = []
    artifacts = []

    # Add explain_context (PR122)
    if explain_context_record and isinstance(explain_context_record, dict):
        if use_minimal_projections:
            components["explain_context"] = V11ApprovalPacketSchema.create_minimal_projection(
                explain_context_record, "explain_context"
            )
        else:
            components["explain_context"] = explain_context_record

        # Collect basis and artifacts
        if "v11_explain_basis" in explain_context_record:
            basis_fields.extend(explain_context_record["v11_explain_basis"])
        if "v11_explain_artifacts" in explain_context_record:
            artifacts.extend(explain_context_record["v11_explain_artifacts"])

    # Add narrative (PR123)
    if narrative_record and isinstance(narrative_record, dict):
        if use_minimal_projections:
            components["narrative"] = V11ApprovalPacketSchema.create_minimal_projection(
                narrative_record, "narrative"
            )
        else:
            components["narrative"] = narrative_record

        # Collect basis and artifacts
        if "v11_narrative_basis" in narrative_record:
            basis_fields.extend(narrative_record["v11_narrative_basis"])
        if "v11_narrative_artifacts" in narrative_record:
            artifacts.extend(narrative_record["v11_narrative_artifacts"])

    # Add preview (PR112)
    if preview_record and isinstance(preview_record, dict):
        if use_minimal_projections:
            components["preview"] = V11ApprovalPacketSchema.create_minimal_projection(
                preview_record, "preview"
            )
        else:
            components["preview"] = preview_record

        # Collect basis and artifacts
        if "v11_preview_basis" in preview_record:
            basis_fields.extend(preview_record["v11_preview_basis"])
        if "v11_preview_artifacts" in preview_record:
            artifacts.extend(preview_record["v11_preview_artifacts"])

    # Add approval_gate (PR113)
    if approval_gate_record and isinstance(approval_gate_record, dict):
        if use_minimal_projections:
            components["approval_gate"] = V11ApprovalPacketSchema.create_minimal_projection(
                approval_gate_record, "approval_gate"
            )
        else:
            components["approval_gate"] = approval_gate_record

        # Collect basis and artifacts
        if "v11_approval_basis" in approval_gate_record:
            basis_fields.extend(approval_gate_record["v11_approval_basis"])
        if "v11_approval_artifacts" in approval_gate_record:
            artifacts.extend(approval_gate_record["v11_approval_artifacts"])

    # Add approval_registry (PR114)
    if approval_registry_record and isinstance(approval_registry_record, dict):
        if use_minimal_projections:
            components["approval_registry"] = V11ApprovalPacketSchema.create_minimal_projection(
                approval_registry_record, "approval_registry"
            )
        else:
            components["approval_registry"] = approval_registry_record

        # Collect basis
        if "v11_registry_basis" in approval_registry_record:
            basis_fields.extend(approval_registry_record["v11_registry_basis"])

    # Generate packet summary
    summary = _generate_packet_summary(
        components,
        narrative_record,
        preview_record,
        approval_gate_record,
    )

    # Deduplicate basis and artifacts
    basis_fields = list(dict.fromkeys(basis_fields))  # Preserve order, remove duplicates
    artifacts = list(dict.fromkeys(artifacts))

    # Create packet record
    return V11ApprovalPacketSchema.create_approval_packet_record(
        summary=summary,
        components=components,
        basis=basis_fields,
        artifacts=artifacts,
    )


def _generate_packet_summary(
    components: Dict[str, Any],
    narrative_record: Optional[Dict[str, Any]],
    preview_record: Optional[Dict[str, Any]],
    approval_gate_record: Optional[Dict[str, Any]],
) -> str:
    """
    Generate non-prescriptive packet summary.

    Args:
        components: Components dict
        narrative_record: Narrative record (for detail)
        preview_record: Preview record (for detail)
        approval_gate_record: Approval gate record (for detail)

    Returns:
        Packet summary text
    """
    fragments = []

    # Start with base
    fragments.append("approval packet assembled.")

    # Add component presence
    component_presence = []
    if "explain_context" in components:
        component_presence.append("context")
    if "narrative" in components:
        component_presence.append("narrative")
    if "preview" in components:
        component_presence.append("preview")
    if "approval_gate" in components:
        component_presence.append("gate")
    if "approval_registry" in components:
        component_presence.append("registry")

    if component_presence:
        fragments.append(f"{', '.join(component_presence)} included.")

    # Add approval requirement label (if available)
    if approval_gate_record and isinstance(approval_gate_record, dict):
        requirement = approval_gate_record.get("v11_approval_requirement", "UNKNOWN")
        if requirement != "UNKNOWN":
            fragments.append(f"approval requirement labeled as {requirement}.")

    # Add preview risk surface label (if available)
    if preview_record and isinstance(preview_record, dict):
        risk_surface = preview_record.get("v11_preview_risk_surface", "UNKNOWN")
        if risk_surface != "UNKNOWN":
            fragments.append(f"preview risk surface labeled as {risk_surface}.")

    return " ".join(fragments)


def get_packet_builder_v1_info() -> Dict[str, Any]:
    """
    Get packet builder v1 information.

    Returns:
        Dict with builder metadata
    """
    return {
        "builder_version": "v1",
        "builder_type": "approval_packet_builder",
        "input_components": [
            "explain_context (PR122)",
            "narrative (PR123)",
            "preview (PR112)",
            "approval_gate (PR113)",
            "approval_registry (PR114)",
        ],
        "output_schema": "v11_approval_packet",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "defensive",
            "no_cross_component_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Approval Packet Builder Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: No components → ERROR
    print("Test 1: No components → ERROR")
    result1 = build_approval_packet_v1()
    print(f"Status: {result1['v11_packet_status']}")
    print(f"Summary: {result1['v11_packet_summary']}")
    print()

    # Test 2: Minimal components
    print("Test 2: Minimal components")
    narrative = {
        "v11_narrative_mode": "ON",
        "v11_narrative_status": "AVAILABLE",
        "v11_narrative_style": "STANDARD",
        "v11_narrative_text": "test narrative",
        "v11_narrative_basis": ["v11_regime_level"],
        "v11_narrative_artifacts": ["pr110_regime_record"],
    }
    result2 = build_approval_packet_v1(narrative_record=narrative)
    print(f"Status: {result2['v11_packet_status']}")
    print(f"Summary: {result2['v11_packet_summary']}")
    print(f"Components: {list(result2['v11_packet_components'].keys())}")
    print()

    # Test 3: Full components
    print("Test 3: Full components")
    explain_context = {
        "v11_explain_mode": "ON",
        "v11_explain_status": "AVAILABLE",
        "v11_explain_signals": ["REGIME_MEDIUM"],
        "v11_explain_basis": ["v11_regime_level"],
        "v11_explain_artifacts": ["pr110_regime_record"],
    }
    preview = {
        "v11_preview_mode": "ON",
        "v11_preview_status": "AVAILABLE",
        "v11_preview_risk_surface": "CONSTRAINED",
        "v11_preview_basis": ["v10_execution_permission"],
        "v11_preview_artifacts": ["pr101_execution_record"],
    }
    approval_gate = {
        "v11_approval_mode": "ON",
        "v11_approval_status": "AVAILABLE",
        "v11_approval_requirement": "REQUIRED",
        "v11_approval_state": "UNREQUESTED",
        "v11_approval_basis": ["v11_regime_level"],
        "v11_approval_artifacts": ["pr110_regime_record"],
    }
    result3 = build_approval_packet_v1(
        explain_context_record=explain_context,
        narrative_record=narrative,
        preview_record=preview,
        approval_gate_record=approval_gate,
    )
    print(f"Status: {result3['v11_packet_status']}")
    print(f"Type: {result3['v11_packet_packet_type']}")
    print(f"Summary: {result3['v11_packet_summary']}")
    print(f"Components: {list(result3['v11_packet_components'].keys())}")
    print(f"Basis count: {len(result3['v11_packet_basis'])}")
    print(f"Artifacts count: {len(result3['v11_packet_artifacts'])}")
    print()

    # Test 4: Minimal projections
    print("Test 4: Minimal projections")
    result4 = build_approval_packet_v1(
        explain_context_record=explain_context,
        narrative_record=narrative,
        use_minimal_projections=True,
    )
    print(f"Status: {result4['v11_packet_status']}")
    print(f"Narrative projection: {result4['v11_packet_components']['narrative']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
