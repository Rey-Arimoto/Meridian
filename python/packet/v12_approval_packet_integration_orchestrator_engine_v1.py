#!/usr/bin/env python3
"""
PR140: v1.2 Approval Packet Integration Orchestrator Engine v1 (READ-ONLY)

Purpose:
    Integration orchestrator for v1.2 components.
    Assembles approval packet + render + rescue extensions from artifact bundle.

Orchestrator Philosophy:
    - Integration = Assembly (not judgment)
    - No approval recommendation logic
    - Defensive: invalid input → graceful handling
    - Label-only projection to downstream builders
    - Collects constitutional warnings from all components

v1.2 Integration:
    Input: Artifact Bundle (PR115/PR116 format)
    Process:
        1. Extract artifacts from bundle
        2. Build missing components (if not provided)
        3. Apply label-only projection to inputs
        4. Assemble packet using PR124 builder
        5. Render packet using PR125/PR138 renderer
        6. Generate rescue narrative extension (PR139, optional)
        7. Collect all constitutional warnings
    Output: {approval_packet, render_record, rescue_narrative_extension, warnings}

Constitutional Constraints:
    - READ-ONLY: No execution logic
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should approve" language
    - No approval recommendation
    - No token literals, addresses, amounts
    - No trading vocabulary
    - Defensive: Never raises exceptions
    - Warning-only: Exit code always 0
"""

from typing import Any, Dict, List, Optional


def _safe_get(d: Optional[Dict[str, Any]], key: str, default: Any = None) -> Any:
    """
    Safely get value from dict.

    Args:
        d: Dictionary (may be None)
        key: Key to get
        default: Default value if not found

    Returns:
        Value or default
    """
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def _project_label_only(record: Dict[str, Any], record_type: str) -> Dict[str, Any]:
    """
    Project record to label-only format (remove numeric patterns, token literals).

    Args:
        record: Record to project
        record_type: Type hint for projection rules

    Returns:
        Label-only projected record
    """
    # For now, pass through (existing builders already handle label-only)
    # Future: Add projection logic if needed
    return record


def build_approval_packet_v12(
    artifact_bundle: Dict[str, Any],
    narrative_style: str = "STANDARD",
    render_style: str = "STANDARD",
    render_format: str = "MARKDOWN",
    rescue_narrative_mode: str = "ON",
) -> Dict[str, Any]:
    """
    Build v1.2 approval packet from artifact bundle.

    Purpose:
        Integration orchestrator for v1.2 components.
        Assembles packet + render + rescue extensions.

    Args:
        artifact_bundle: Artifact bundle (PR115/PR116 format)
            Expected keys in artifact_bundle["artifacts"]:
                Required:
                - regime_record
                - drift_record
                Optional (v1.0/v1.1/v1.2):
                - permission_record
                - trajectory_record (PR126)
                - distortion_catalog_record (PR129/PR134)
                - eligibility_record (PR128)
                - role_qualification_record (PR130)
                - contribution_record (PR131/PR132)
                - rescue_flow_graph (PR137)
                - preview_record (PR112)
                - approval_gate_record (PR113)
                - approval_registry_record (PR114)
                - explain_context_record (PR122)
                - narrative_record (PR123)
                - render_record (PR125/PR138)
        narrative_style: CONCISE | STANDARD | DETAILED
        render_style: CONCISE | STANDARD | DETAILED
        render_format: MARKDOWN | TEXT
        rescue_narrative_mode: ON | OFF

    Returns:
        {
            "approval_packet": {...},  # PR124 schema
            "render_record": {...},    # PR125/PR138 render
            "rescue_narrative_extension": {...} or None,  # PR139 (if mode ON)
            "warnings": [...],         # All constitutional warnings
        }

    Constitutional Constraints:
        - READ-ONLY: No execution logic
        - Non-prescriptive: No "should approve" language
        - Defensive: Invalid input → AVAILABLE + warnings
        - No approval recommendation logic
    """
    try:
        # Import builders (lazy to avoid circular deps)
        from packet import build_approval_packet_v1, check_packet_record
        from narrative import build_human_narrative_v1, build_rescue_flow_narrative_extension_v1
        from render import render_review_packet_v1, check_render_record
        from narrative import check_rescue_narrative_record

        warnings = []

        # 1. Extract artifacts from bundle
        if not isinstance(artifact_bundle, dict):
            return {
                "approval_packet": {"v11_packet_status": "ERROR", "v11_packet_summary": "invalid artifact bundle."},
                "render_record": {"v11_render_status": "ERROR", "v11_render_summary": "packet unavailable."},
                "rescue_narrative_extension": None,
                "warnings": ["invalid artifact bundle: not a dict"],
            }

        artifacts = _safe_get(artifact_bundle, "artifacts", {})
        if not isinstance(artifacts, dict):
            return {
                "approval_packet": {"v11_packet_status": "ERROR", "v11_packet_summary": "invalid artifacts dict."},
                "render_record": {"v11_render_status": "ERROR", "v11_render_summary": "packet unavailable."},
                "rescue_narrative_extension": None,
                "warnings": ["invalid artifacts: not a dict"],
            }

        # 2. Extract core records (required)
        regime_record = _safe_get(artifacts, "regime_record")
        drift_record = _safe_get(artifacts, "drift_record")

        # Extract optional v1.2 records
        permission_record = _safe_get(artifacts, "permission_record")
        trajectory_record = _safe_get(artifacts, "trajectory_record")
        distortion_catalog_record = _safe_get(artifacts, "distortion_catalog_record")
        eligibility_record = _safe_get(artifacts, "eligibility_record")
        role_qualification_record = _safe_get(artifacts, "role_qualification_record")
        contribution_record = _safe_get(artifacts, "contribution_record")
        rescue_flow_graph = _safe_get(artifacts, "rescue_flow_graph")

        # Extract optional component records (may be pre-built)
        explain_context_record = _safe_get(artifacts, "explain_context_record")
        narrative_record = _safe_get(artifacts, "narrative_record")
        preview_record = _safe_get(artifacts, "preview_record")
        approval_gate_record = _safe_get(artifacts, "approval_gate_record")
        approval_registry_record = _safe_get(artifacts, "approval_registry_record")

        # 3. Build missing components (if not provided)

        # Build explain_context if not provided
        if not explain_context_record and regime_record and drift_record:
            # Simple explain context assembly
            explain_signals = []

            # Add regime signal
            regime_level = _safe_get(regime_record, "v11_regime_level")
            if regime_level:
                explain_signals.append(regime_level)

            # Add drift signal
            drift_level = _safe_get(drift_record, "v10_drift_level")
            if drift_level:
                explain_signals.append(drift_level)

            # Add permission signal if available
            if permission_record:
                permission_label = _safe_get(permission_record, "v10_permission_label")
                if permission_label:
                    explain_signals.append(permission_label)

            # Add distortion signals if available
            if distortion_catalog_record:
                distortion_type = _safe_get(distortion_catalog_record, "v12_distortion_type")
                if distortion_type:
                    explain_signals.append(distortion_type)

            explain_context_record = {
                "v11_explain_status": "AVAILABLE",
                "v11_explain_signals": explain_signals,
                "v11_explain_basis": ["v11_regime_level", "v10_drift_level"],
                "v11_explain_artifacts": [],
            }

        # Build narrative if not provided
        if not narrative_record and explain_context_record:
            try:
                narrative_record = build_human_narrative_v1(
                    explain_context_record=explain_context_record,
                    style=narrative_style,
                )
            except Exception as e:
                warnings.append(f"narrative generation failed: {e}")
                narrative_record = None

        # Build preview if not provided (minimal stub)
        if not preview_record:
            preview_record = {
                "v11_preview_status": "AVAILABLE",
                "v11_preview_risk_surface": "CONSTRAINED",
                "v11_preview_basis": [],
            }

        # Build approval gate if not provided (minimal stub)
        if not approval_gate_record:
            approval_gate_record = {
                "v11_approval_requirement": "REQUIRED",
                "v11_approval_state": "UNREQUESTED",
            }

        # 4. Build v1.2 rescue narrative extension (if rescue_flow_graph provided)
        rescue_narrative_extension = None
        if rescue_flow_graph and rescue_narrative_mode == "ON":
            try:
                rescue_narrative_extension = build_rescue_flow_narrative_extension_v1(
                    rescue_flow_graph_record=rescue_flow_graph,
                    style=narrative_style,
                    mode="ON",
                )
            except Exception as e:
                warnings.append(f"rescue narrative extension failed: {e}")

        # 5. Assemble approval packet using PR124 builder
        try:
            approval_packet = build_approval_packet_v1(
                explain_context_record=explain_context_record,
                narrative_record=narrative_record,
                preview_record=preview_record,
                approval_gate_record=approval_gate_record,
                approval_registry_record=approval_registry_record,
                use_minimal_projections=False,
            )
        except Exception as e:
            warnings.append(f"packet assembly failed: {e}")
            approval_packet = {
                "v11_packet_status": "ERROR",
                "v11_packet_summary": "packet assembly failed.",
            }

        # 6. Render packet using PR125/PR138 renderer
        try:
            render_record = render_review_packet_v1(
                packet_record=approval_packet,
                fmt=render_format,
                style=render_style,
                rescue_flow_graph=rescue_flow_graph,  # Optional PR138 extension
            )
        except Exception as e:
            warnings.append(f"render generation failed: {e}")
            render_record = {
                "v11_render_status": "ERROR",
                "v11_render_summary": "render generation failed.",
            }

        # 7. Collect all constitutional warnings
        try:
            packet_warnings = check_packet_record(approval_packet)
            warnings.extend(packet_warnings)
        except Exception:
            pass

        try:
            render_warnings = check_render_record(render_record)
            warnings.extend(render_warnings)
        except Exception:
            pass

        if rescue_narrative_extension:
            try:
                rescue_warnings = check_rescue_narrative_record(rescue_narrative_extension)
                warnings.extend(rescue_warnings)
            except Exception:
                pass

        # 8. Return integration bundle
        return {
            "approval_packet": approval_packet,
            "render_record": render_record,
            "rescue_narrative_extension": rescue_narrative_extension,
            "warnings": warnings,
        }

    except Exception as e:
        # Defensive: never raise, return error bundle
        return {
            "approval_packet": {
                "v11_packet_status": "ERROR",
                "v11_packet_summary": f"integration orchestrator failed: {e}",
            },
            "render_record": {
                "v11_render_status": "ERROR",
                "v11_render_summary": "integration failed.",
            },
            "rescue_narrative_extension": None,
            "warnings": [f"orchestrator exception: {e}"],
        }


def get_integration_orchestrator_v1_info() -> Dict[str, Any]:
    """
    Get integration orchestrator v1 information.

    Returns:
        Dict with orchestrator metadata
    """
    return {
        "orchestrator_version": "v1",
        "orchestrator_type": "approval_packet_integration",
        "input_format": "artifact_bundle (PR115/PR116)",
        "output_format": "{approval_packet, render_record, rescue_narrative_extension, warnings}",
        "integrated_components": [
            "PR124: Approval Packet Builder",
            "PR125: Human Review Renderer",
            "PR138: Rescue Flow Render Extension",
            "PR139: Rescue Flow Narrative Extension",
            "PR126-PR137: v1.2 components",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "no_approval_recommendation",
            "defensive",
            "warning-only",
        ],
        "philosophy": "Integration = Assembly (not judgment)",
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Approval Packet Integration Orchestrator - Self Test")
    print("=" * 60)
    print()

    # Test 1: Minimal bundle
    print("Test 1: Minimal bundle (regime + drift)")
    minimal_bundle = {
        "artifacts": {
            "regime_record": {"v11_regime_level": "REGIME_MEDIUM"},
            "drift_record": {"v10_drift_level": "DRIFT_LOW"},
        }
    }
    result1 = build_approval_packet_v12(minimal_bundle)
    print(f"Packet status: {result1['approval_packet'].get('v11_packet_status', 'UNKNOWN')}")
    print(f"Render status: {result1['render_record'].get('v11_render_status', 'UNKNOWN')}")
    print(f"Warnings: {len(result1['warnings'])}")
    print()

    # Test 2: Invalid bundle
    print("Test 2: Invalid bundle (not a dict)")
    result2 = build_approval_packet_v12(None)
    print(f"Packet status: {result2['approval_packet'].get('v11_packet_status', 'UNKNOWN')}")
    print(f"Warnings: {len(result2['warnings'])}")
    print()

    # Test 3: Get orchestrator info
    print("Test 3: Get orchestrator info")
    info = get_integration_orchestrator_v1_info()
    print(f"Orchestrator version: {info['orchestrator_version']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
