#!/usr/bin/env python3
"""
PR118: v1.0 Digest Renderer v1 (READ-ONLY)

Purpose:
    Render artifact bundle as human-readable structural digest.
    Renderer = Display (not instruction/recommendation).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No numeric amounts: No prices, balances, fees
    - Renderer = display only (not instruction)
    - Uses only labels, statuses, constraint names

Renderer Philosophy:
    Renderer ≠ Instruction
    Renderer ≠ Recommendation
    Renderer = Structural Display

    Renderer shows:
    - Regime level (LOW/MEDIUM/HIGH)
    - Permission status (HOLD/DRY_RUN_ONLY/AUTHORIZED)
    - Plan type + constraints
    - Preview impact shape (qualitative)
    - Approval requirement state
    - Layer statuses

    Renderer does NOT:
    - Show amounts or prices
    - Show token names
    - Show addresses
    - Recommend actions
    - Provide instructions
"""

import json
from typing import Any, Dict


def render_digest(bundle: Dict[str, Any], format: str = "text") -> str:
    """
    Render artifact bundle as structural digest.

    Args:
        bundle: Artifact bundle from PR116
        format: Output format ("text" or "json")

    Returns:
        Formatted digest string

    Design:
        - Extracts key structural fields from bundle
        - Formats as human-readable text or JSON
        - Uses only safe labels (no tokens/amounts/addresses)
        - Defensive (missing fields → placeholders)
    """
    # Defensive: handle None or invalid input
    if bundle is None or not isinstance(bundle, dict):
        return "Bundle Status: ERROR\n\nError: Invalid bundle input (None or not dict)\n"

    if format == "json":
        return _render_json_digest(bundle)
    else:
        return _render_text_digest(bundle)


def _render_text_digest(bundle: Dict[str, Any]) -> str:
    """
    Render bundle as plain text digest.

    Args:
        bundle: Artifact bundle

    Returns:
        Plain text digest
    """
    lines = []

    # Bundle status
    bundle_status = bundle.get("v10_bundle_status", "UNKNOWN")
    lines.append(f"Bundle Status: {bundle_status}")
    lines.append("")

    # Get artifacts
    artifacts = bundle.get("v10_bundle_artifacts", {})

    # Regime classification
    if "REGIME" in artifacts:
        regime = artifacts["REGIME"]
        regime_level = regime.get("v11_regime_level", "UNKNOWN")
        regime_basis = regime.get("v11_regime_basis", [])
        lines.append(f"Regime Level: {regime_level}")
        lines.append(f"  Basis: {', '.join(regime_basis) if regime_basis else 'none'}")
        lines.append("")

    # Policy binding
    if "POLICY_BINDING" in artifacts:
        policy = artifacts["POLICY_BINDING"]
        permission = policy.get("v11_execution_permission_override", "UNKNOWN")
        policy_basis = policy.get("v11_policy_basis", [])
        lines.append(f"Execution Permission: {permission}")
        lines.append(
            f"  Basis: {', '.join(policy_basis) if policy_basis else 'none'}"
        )
        lines.append("")

    # Execution plan
    if "PLAN" in artifacts:
        plan = artifacts["PLAN"]
        plan_type = plan.get("v10_plan_type", "UNKNOWN")
        plan_constraints = plan.get("v10_plan_constraints", [])
        lines.append(f"Plan Type: {plan_type}")
        if plan_constraints:
            lines.append(f"  Constraints: {', '.join(plan_constraints)}")
        lines.append("")

    # Execution preview
    if "PREVIEW" in artifacts:
        preview = artifacts["PREVIEW"]
        preview_mode = preview.get("v11_preview_mode", "UNKNOWN")
        preview_basis = preview.get("v11_preview_basis", [])
        lines.append(f"Preview Mode: {preview_mode}")
        lines.append(
            f"  Basis: {', '.join(preview_basis) if preview_basis else 'none'}"
        )
        lines.append("")

    # Approval gate
    if "APPROVAL_GATE" in artifacts:
        approval = artifacts["APPROVAL_GATE"]
        requirement = approval.get("v11_approval_requirement", "UNKNOWN")
        approval_basis = approval.get("v11_approval_basis", [])
        lines.append(f"Approval Requirement: {requirement}")
        lines.append(
            f"  Basis: {', '.join(approval_basis) if approval_basis else 'none'}"
        )
        lines.append("")

    # Approval registry
    if "APPROVAL_REGISTRY" in artifacts:
        registry = artifacts["APPROVAL_REGISTRY"]
        registry_state = registry.get("v11_registry_state", "UNKNOWN")
        registry_event = registry.get("v11_registry_event", "UNKNOWN")
        lines.append(f"Registry State: {registry_state}")
        lines.append(f"  Event: {registry_event}")
        lines.append("")

    # Layer summary
    layers = bundle.get("v10_bundle_layers", [])
    lines.append(f"Layers Present: {len(layers)}")
    if layers:
        lines.append(f"  {', '.join(layers)}")
    lines.append("")

    # Warnings
    warnings = bundle.get("v10_bundle_warnings", [])
    if warnings:
        lines.append(f"Warnings: {len(warnings)}")
        for i, warning in enumerate(warnings[:5], 1):  # Show first 5
            lines.append(f"  {i}. {warning}")
        if len(warnings) > 5:
            lines.append(f"  ... and {len(warnings) - 5} more")
        lines.append("")

    return "\n".join(lines)


def _render_json_digest(bundle: Dict[str, Any]) -> str:
    """
    Render bundle as JSON digest.

    Args:
        bundle: Artifact bundle

    Returns:
        JSON digest
    """
    # Extract key fields only (safe subset)
    artifacts = bundle.get("v10_bundle_artifacts", {})

    digest = {
        "bundle_status": bundle.get("v10_bundle_status", "UNKNOWN"),
        "layers_count": len(bundle.get("v10_bundle_layers", [])),
    }

    # Regime
    if "REGIME" in artifacts:
        regime = artifacts["REGIME"]
        digest["regime_level"] = regime.get("v11_regime_level", "UNKNOWN")

    # Policy
    if "POLICY_BINDING" in artifacts:
        policy = artifacts["POLICY_BINDING"]
        digest["execution_permission"] = policy.get(
            "v11_execution_permission_override", "UNKNOWN"
        )

    # Plan
    if "PLAN" in artifacts:
        plan = artifacts["PLAN"]
        digest["plan_type"] = plan.get("v10_plan_type", "UNKNOWN")
        digest["plan_constraints"] = plan.get("v10_plan_constraints", [])

    # Preview
    if "PREVIEW" in artifacts:
        preview = artifacts["PREVIEW"]
        digest["preview_mode"] = preview.get("v11_preview_mode", "UNKNOWN")

    # Approval
    if "APPROVAL_GATE" in artifacts:
        approval = artifacts["APPROVAL_GATE"]
        digest["approval_requirement"] = approval.get(
            "v11_approval_requirement", "UNKNOWN"
        )

    # Registry
    if "APPROVAL_REGISTRY" in artifacts:
        registry = artifacts["APPROVAL_REGISTRY"]
        digest["registry_state"] = registry.get("v11_registry_state", "UNKNOWN")

    # Warnings
    warnings = bundle.get("v10_bundle_warnings", [])
    if warnings:
        digest["warnings_count"] = len(warnings)

    return json.dumps(digest, indent=2)


def get_digest_renderer_v1_info() -> Dict[str, Any]:
    """
    Get digest renderer v1 information.

    Returns:
        Dict with renderer metadata
    """
    return {
        "renderer_version": "v1",
        "renderer_type": "structural_digest",
        "supported_formats": ["text", "json"],
        "displays_only_labels": True,
        "no_token_literals": True,
        "no_numeric_amounts": True,
        "no_addresses": True,
        "defensive": True,
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.0 Digest Renderer v1 - Self Test")
    print("=" * 60)
    print()

    # Create mock bundle
    mock_bundle = {
        "v10_bundle_status": "AVAILABLE",
        "v10_bundle_layers": ["REGIME", "POLICY_BINDING", "PLAN"],
        "v10_bundle_artifacts": {
            "REGIME": {
                "v11_regime_level": "LOW",
                "v11_regime_basis": ["entropy_classifier"],
            },
            "POLICY_BINDING": {
                "v11_execution_permission_override": "DRY_RUN_ONLY",
                "v11_policy_basis": ["regime_level"],
            },
            "PLAN": {
                "v10_plan_type": "MAINTENANCE",
                "v10_plan_constraints": ["dry_run_only", "read_only"],
            },
        },
    }

    # Render text digest
    print("Text Digest:")
    print("-" * 60)
    text_digest = render_digest(mock_bundle, format="text")
    print(text_digest)
    print()

    # Render JSON digest
    print("JSON Digest:")
    print("-" * 60)
    json_digest = render_digest(mock_bundle, format="json")
    print(json_digest)
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
