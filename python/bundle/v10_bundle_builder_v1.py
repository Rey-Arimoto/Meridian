#!/usr/bin/env python3
"""
PR116: v1.0 Bundle Builder v1 (READ-ONLY)

Purpose:
    Build artifact bundle from orchestrator output.
    Builder = Wrapper (not decision/evaluation).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - Defensive: Never raises, returns valid records
    - Warning-only: Exit code always 0

Builder Philosophy:
    Builder ≠ Decision
    Builder ≠ Evaluation
    Builder = Format Conversion

    Builder provides:
    - Orchestrator artifacts → Bundle schema
    - Defensive handling (missing artifacts → ERROR)
    - Fixed layer ordering preservation
    - Constitutional validation

    Builder does NOT:
    - Make decisions
    - Evaluate quality
    - Recommend actions
    - Modify artifacts

Artifact Name Mapping:
    Orchestrator output → Bundle layer names:
    - onchain_analytics → ANALYTICS
    - regime_record → REGIME
    - policy_record → POLICY_BINDING
    - execution_plan → PLAN
    - preview_record → PREVIEW
    - approval_gate_record → APPROVAL_GATE
    - registry_record → APPROVAL_REGISTRY
"""

from typing import Any, Dict, List, Optional
from .v10_artifact_bundle_schema import V10ArtifactBundleSchema


def build_artifact_bundle_v1(
    artifacts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build artifact bundle from orchestrator output.

    Args:
        artifacts: Orchestrator output dict (from PR115)

    Returns:
        Bundle record (always valid)

    Design:
        - Defensive (None/invalid → ERROR record)
        - Maps orchestrator names → bundle layer names
        - Preserves fixed layer order
        - Warning-only (never raises)
    """
    warnings: List[str] = []

    # Defensive: validate artifacts input
    if artifacts is None or not isinstance(artifacts, dict):
        return V10ArtifactBundleSchema.create_error_record(
            error_info="invalid artifacts input (None or not dict)",
            warnings=["Artifacts must be a dict"],
        )

    # Artifact name mapping
    artifact_mapping = {
        "onchain_analytics": "ANALYTICS",
        "regime_record": "REGIME",
        "policy_record": "POLICY_BINDING",
        "execution_plan": "PLAN",
        "preview_record": "PREVIEW",
        "approval_gate_record": "APPROVAL_GATE",
        "registry_record": "APPROVAL_REGISTRY",
    }

    # Extract bundle artifacts
    bundle_artifacts = {}
    bundle_layers = []

    for artifact_name, layer_name in artifact_mapping.items():
        if artifact_name in artifacts:
            artifact = artifacts[artifact_name]
            if isinstance(artifact, dict):
                bundle_artifacts[layer_name] = artifact
                bundle_layers.append(layer_name)
            else:
                warnings.append(
                    f"Artifact '{artifact_name}' is not a dict (skipped)"
                )
        else:
            warnings.append(f"Artifact '{artifact_name}' missing (skipped)")

    # Check if any artifacts were extracted
    if len(bundle_artifacts) == 0:
        return V10ArtifactBundleSchema.create_error_record(
            error_info="no valid artifacts found in input",
            warnings=warnings,
        )

    # Copy pipeline warnings if present
    if "pipeline_warnings" in artifacts and isinstance(
        artifacts["pipeline_warnings"], list
    ):
        warnings.extend(artifacts["pipeline_warnings"])

    # Generate summary
    layer_count = len(bundle_layers)
    summary = (
        f"artifact bundle with {layer_count} layers. "
        f"pipeline output captured. layers: {', '.join(bundle_layers)}."
    )

    # Create bundle record
    bundle = V10ArtifactBundleSchema.create_bundle_record(
        layers=bundle_layers,
        artifacts=bundle_artifacts,
        summary=summary,
        basis=["pipeline_artifacts"],
        warnings=warnings if warnings else None,
    )

    # Validate bundle against constitutional guard
    from .v10_bundle_constitutional_guard import validate_bundle_record

    guard_warnings = validate_bundle_record(bundle)
    if guard_warnings:
        # Add guard warnings to bundle warnings
        existing_warnings = bundle.get("v10_bundle_warnings", [])
        all_warnings = existing_warnings + guard_warnings
        bundle["v10_bundle_warnings"] = all_warnings

    return bundle


def get_bundle_builder_v1_info() -> Dict[str, Any]:
    """
    Get bundle builder v1 information.

    Returns:
        Dict with builder metadata
    """
    return {
        "builder_version": "v1",
        "builder_type": "artifact_bundle",
        "artifact_mapping": {
            "onchain_analytics": "ANALYTICS",
            "regime_record": "REGIME",
            "policy_record": "POLICY_BINDING",
            "execution_plan": "PLAN",
            "preview_record": "PREVIEW",
            "approval_gate_record": "APPROVAL_GATE",
            "registry_record": "APPROVAL_REGISTRY",
        },
        "defensive": True,
        "warning_only": True,
        "constitutional_validation": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Bundle Builder v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Build bundle from valid orchestrator output
    print("Test 1: Build bundle from valid orchestrator output")
    orchestrator_output = {
        "pipeline_version": "v1",
        "pipeline_status": "COMPLETE",
        "onchain_analytics": {
            "onchain_analytics_mode": "ON",
            "onchain_analytics_status": "AVAILABLE",
        },
        "regime_record": {
            "v11_regime_mode": "ON",
            "v11_regime_level": "LOW",
        },
        "policy_record": {
            "v11_policy_mode": "ON",
            "v11_execution_permission_override": "DRY_RUN_ONLY",
        },
        "execution_plan": {
            "v10_plan_mode": "ON",
            "v10_plan_type": "MAINTENANCE",
        },
        "preview_record": {
            "v11_preview_mode": "ON",
        },
        "approval_gate_record": {
            "v11_approval_mode": "ON",
            "v11_approval_requirement": "NOT_REQUIRED",
        },
        "registry_record": {
            "v11_registry_mode": "ON",
            "v11_registry_state": "UNREQUESTED",
        },
    }

    bundle = build_artifact_bundle_v1(orchestrator_output)
    print(f"Bundle status: {bundle.get('v10_bundle_status')}")
    print(f"Bundle layers: {bundle.get('v10_bundle_layers')}")
    print(f"Artifacts count: {len(bundle.get('v10_bundle_artifacts', {}))}")
    print()

    # Test 2: Build bundle from partial output (missing artifacts)
    print("Test 2: Build bundle from partial output (missing artifacts)")
    partial_output = {
        "regime_record": {"v11_regime_level": "LOW"},
        "policy_record": {"v11_execution_permission_override": "HOLD"},
    }

    bundle_partial = build_artifact_bundle_v1(partial_output)
    print(f"Bundle status: {bundle_partial.get('v10_bundle_status')}")
    print(f"Bundle layers: {bundle_partial.get('v10_bundle_layers')}")
    print(
        f"Bundle warnings: {len(bundle_partial.get('v10_bundle_warnings', []))}"
    )
    print()

    # Test 3: Build bundle from None input
    print("Test 3: Build bundle from None input (defensive)")
    bundle_none = build_artifact_bundle_v1(None)
    print(f"Bundle status: {bundle_none.get('v10_bundle_status')}")
    print(f"Has error_info: {'v10_bundle_error_info' in bundle_none}")
    print()

    # Test 4: Build bundle from invalid input
    print("Test 4: Build bundle from invalid input (defensive)")
    bundle_invalid = build_artifact_bundle_v1("invalid")  # type: ignore
    print(f"Bundle status: {bundle_invalid.get('v10_bundle_status')}")
    print(f"Has error_info: {'v10_bundle_error_info' in bundle_invalid}")
    print()

    # Test 5: Build bundle from empty dict
    print("Test 5: Build bundle from empty dict")
    bundle_empty = build_artifact_bundle_v1({})
    print(f"Bundle status: {bundle_empty.get('v10_bundle_status')}")
    print(
        f"Bundle warnings: {len(bundle_empty.get('v10_bundle_warnings', []))}"
    )
    print()

    # Test 6: Verify constitutional validation
    print("Test 6: Verify constitutional validation")
    dirty_output = {
        "regime_record": {
            "v11_regime_summary": "regime classified. execute swap operations."
        },
    }

    bundle_dirty = build_artifact_bundle_v1(dirty_output)
    print(f"Bundle status: {bundle_dirty.get('v10_bundle_status')}")
    print(
        f"Bundle warnings (includes guard warnings): {len(bundle_dirty.get('v10_bundle_warnings', []))}"
    )
    if "v10_bundle_warnings" in bundle_dirty:
        print("  Warnings:")
        for w in bundle_dirty["v10_bundle_warnings"]:
            print(f"    - {w}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
