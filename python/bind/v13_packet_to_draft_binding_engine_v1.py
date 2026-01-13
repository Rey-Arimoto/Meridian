#!/usr/bin/env python3
"""
PR142: v1.3 Approval Packet → Execution Draft Binding Engine v1 (READ-ONLY)

Purpose:
    Map v1.2 Approval Packet (PR124/PR140) or Artifact Bundle (PR115/PR116)
    to PR141 Execution Draft Schema (v13_draft_) with labels and constraints only.

Binding Philosophy:
    Binding only (not recommendation, not instruction).
    Draft ≠ Action ≠ Recommendation.
    Extract structural labels, remove numeric values/tokens.

API:
    build_execution_draft_from_bundle_v1(artifact_bundle, mode="DRAFT_ONLY")
    build_execution_draft_from_packet_v1(approval_packet, mode="DRAFT_ONLY")

Intended Shape Mapping (structural binding, not recommendation):
    INELIGIBLE → NO_ACTION
    SUPPRESSED → NO_ACTION
    REQUIRED → HUMAN_REVIEW_REQUIRED
    DRY_RUN_ONLY → SIMULATION_ONLY
    CONSIDERATION_ONLY → CONSIDERATION_ONLY
    else → SIMULATION_ONLY

Constitutional Constraints:
    - READ-ONLY: No signing, no sending, no tx building
    - Label projection only (no numeric values, no token literals)
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from draft import (
    V13ExecutionDraftSchema,
    check_draft_record,
    DRAFT_VERSION_V1,
    DRAFT_STATUS_AVAILABLE,
    DRAFT_STATUS_ERROR,
    DRAFT_MODE_READ_ONLY,
    ACTION_CLASS_NONE,
    ACTION_CLASS_DRAFT_ONLY,
)


def _extract_inputs_from_bundle(artifact_bundle: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract input labels from artifact bundle (source presence only, no values).

    Args:
        artifact_bundle: Artifact bundle

    Returns:
        Dict with source presence labels only
    """
    inputs = {}

    if not isinstance(artifact_bundle, dict):
        return inputs

    artifacts = artifact_bundle.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return inputs

    # Map artifact presence to labels (no values)
    artifact_types = [
        "regime_record",
        "drift_record",
        "permission_record",
        "trajectory_record",
        "distortion_catalog_record",
        "eligibility_record",
        "role_qualification_record",
        "contribution_record",
        "boundary_record",
        "rescue_flow_graph",
        "narrative_record",
    ]

    for artifact_type in artifact_types:
        if artifact_type in artifacts and artifacts[artifact_type]:
            inputs[f"{artifact_type}_present"] = "true"

    return inputs


def _extract_inputs_from_packet(approval_packet: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract input labels from approval packet (source presence only, no values).

    Args:
        approval_packet: Approval packet

    Returns:
        Dict with source presence labels only
    """
    inputs = {}

    if not isinstance(approval_packet, dict):
        return inputs

    # Check packet status
    packet_status = approval_packet.get("v11_packet_status")
    if packet_status:
        inputs["approval_packet_status"] = packet_status

    # Check artifacts list (presence only, no values)
    artifacts = approval_packet.get("v11_packet_artifacts", [])
    if isinstance(artifacts, list) and len(artifacts) > 0:
        inputs["approval_packet_artifacts_present"] = "true"

    return inputs


def _extract_constraints_from_bundle(artifact_bundle: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract constraint labels from artifact bundle (labels only, no values).

    Args:
        artifact_bundle: Artifact bundle

    Returns:
        Dict with constraint labels only
    """
    constraints = {}

    if not isinstance(artifact_bundle, dict):
        return constraints

    artifacts = artifact_bundle.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return constraints

    # Extract permission label
    permission_record = artifacts.get("permission_record", {})
    if isinstance(permission_record, dict):
        permission_label = permission_record.get("v10_permission_label")
        if permission_label:
            constraints["permission"] = permission_label

    # Extract trajectory signal
    trajectory_record = artifacts.get("trajectory_record", {})
    if isinstance(trajectory_record, dict):
        trajectory_signal = trajectory_record.get("v11_trajectory_signal")
        if trajectory_signal:
            constraints["trajectory"] = trajectory_signal

    # Extract eligibility label
    eligibility_record = artifacts.get("eligibility_record", {})
    if isinstance(eligibility_record, dict):
        eligibility_label = eligibility_record.get("v11_eligibility_label")
        if eligibility_label:
            constraints["eligibility"] = eligibility_label

    # Extract boundary signal
    boundary_record = artifacts.get("boundary_record", {})
    if isinstance(boundary_record, dict):
        boundary_signal = boundary_record.get("v11_boundary_signal")
        if boundary_signal:
            constraints["boundary"] = boundary_signal

    return constraints


def _extract_constraints_from_packet(approval_packet: Dict[str, Any]) -> Dict[str, str]:
    """
    Extract constraint labels from approval packet (labels only, no values).

    Args:
        approval_packet: Approval packet

    Returns:
        Dict with constraint labels only
    """
    constraints = {}

    if not isinstance(approval_packet, dict):
        return constraints

    # Extract permission label
    permission_label = approval_packet.get("v11_packet_permission_label")
    if permission_label:
        constraints["permission"] = permission_label

    # Extract trajectory signal
    trajectory_signal = approval_packet.get("v11_packet_trajectory_signal")
    if trajectory_signal:
        constraints["trajectory"] = trajectory_signal

    # Extract eligibility label
    eligibility_label = approval_packet.get("v11_packet_eligibility_label")
    if eligibility_label:
        constraints["eligibility"] = eligibility_label

    # Extract boundary signal
    boundary_signal = approval_packet.get("v11_packet_boundary_signal")
    if boundary_signal:
        constraints["boundary"] = boundary_signal

    return constraints


def _determine_intended_shape(constraints: Dict[str, str], mode: str) -> Dict[str, str]:
    """
    Determine intended shape from constraints (structural binding, not recommendation).

    Args:
        constraints: Constraint labels
        mode: Binding mode (DRAFT_ONLY, etc.)

    Returns:
        Intended shape dict with action_class
    """
    # Default to SIMULATION_ONLY
    action_class = "SIMULATION_ONLY"

    # Check eligibility
    eligibility = constraints.get("eligibility", "").upper()
    if "INELIGIBLE" in eligibility:
        action_class = "NO_ACTION"

    # Check permission
    permission = constraints.get("permission", "").upper()
    if "SUPPRESSED" in permission:
        action_class = "NO_ACTION"

    # Check boundary
    boundary = constraints.get("boundary", "").upper()
    if "REQUIRED" in boundary:
        action_class = "HUMAN_REVIEW_REQUIRED"
    elif "DRY_RUN" in boundary or "DRY_RUN_ONLY" in boundary:
        action_class = "SIMULATION_ONLY"
    elif "CONSIDERATION" in boundary or "CONSIDERATION_ONLY" in boundary:
        action_class = "CONSIDERATION_ONLY"

    return {"action_class": action_class}


def _extract_basis_from_bundle(artifact_bundle: Dict[str, Any]) -> List[str]:
    """
    Extract basis list from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle

    Returns:
        List of basis strings
    """
    basis = []

    if not isinstance(artifact_bundle, dict):
        return basis

    artifacts = artifact_bundle.get("artifacts", {})
    if not isinstance(artifacts, dict):
        return basis

    # List artifact types that are present
    artifact_types = [
        "regime_record",
        "drift_record",
        "permission_record",
        "trajectory_record",
        "distortion_catalog_record",
        "eligibility_record",
        "role_qualification_record",
        "contribution_record",
        "boundary_record",
        "rescue_flow_graph",
        "narrative_record",
    ]

    for artifact_type in artifact_types:
        if artifact_type in artifacts and artifacts[artifact_type]:
            basis.append(artifact_type)

    return basis


def _extract_basis_from_packet(approval_packet: Dict[str, Any]) -> List[str]:
    """
    Extract basis list from approval packet.

    Args:
        approval_packet: Approval packet

    Returns:
        List of basis strings
    """
    basis = ["v11_approval_packet"]

    if not isinstance(approval_packet, dict):
        return basis

    # Add artifacts if present
    artifacts = approval_packet.get("v11_packet_artifacts", [])
    if isinstance(artifacts, list):
        basis.extend(artifacts)

    return basis


def build_execution_draft_from_bundle_v1(
    artifact_bundle: Optional[Dict[str, Any]],
    mode: str = "DRAFT_ONLY",
) -> Dict[str, Any]:
    """
    Build execution draft from artifact bundle (binding only, not recommendation).

    Args:
        artifact_bundle: Artifact bundle (PR115/PR116 format)
        mode: Binding mode (DRAFT_ONLY, etc.)

    Returns:
        Dict with:
        - execution_draft: PR141-compliant draft record
        - warnings: List of constitutional guard warnings
    """
    warnings = []

    # Defensive: Handle invalid input
    if artifact_bundle is None or not isinstance(artifact_bundle, dict):
        warnings.append("invalid artifact_bundle (expected dict, got None or non-dict)")
        error_record = V13ExecutionDraftSchema.create_error_record(
            summary="execution draft binding failed: invalid artifact bundle."
        )
        return {
            "execution_draft": error_record,
            "warnings": warnings,
        }

    # Extract inputs (source presence only, no values)
    inputs = _extract_inputs_from_bundle(artifact_bundle)

    # Extract constraints (labels only, no values)
    constraints = _extract_constraints_from_bundle(artifact_bundle)

    # Determine intended shape (structural binding, not recommendation)
    intended_shape = _determine_intended_shape(constraints, mode)

    # Extract basis
    basis = _extract_basis_from_bundle(artifact_bundle)

    # Create draft record
    draft_summary = "execution draft available from artifact bundle."
    draft_record = V13ExecutionDraftSchema.create_draft_record(
        version=DRAFT_VERSION_V1,
        status=DRAFT_STATUS_AVAILABLE,
        mode=DRAFT_MODE_READ_ONLY,
        summary=draft_summary,
        inputs=inputs,
        constraints=constraints,
        intended_shape=intended_shape,
        basis=basis,
        artifacts=[],
        warnings=[],
    )

    # Validate schema
    schema_errors = V13ExecutionDraftSchema.validate_draft_record(draft_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    # Run constitutional guards
    guard_warnings = check_draft_record(draft_record)
    if guard_warnings:
        warnings.extend(guard_warnings)

    # Add warnings to draft record
    draft_record["v13_draft_warnings"] = warnings

    return {
        "execution_draft": draft_record,
        "warnings": warnings,
    }


def build_execution_draft_from_packet_v1(
    approval_packet: Optional[Dict[str, Any]],
    mode: str = "DRAFT_ONLY",
) -> Dict[str, Any]:
    """
    Build execution draft from approval packet (binding only, not recommendation).

    Args:
        approval_packet: Approval packet (PR124/PR140 format)
        mode: Binding mode (DRAFT_ONLY, etc.)

    Returns:
        Dict with:
        - execution_draft: PR141-compliant draft record
        - warnings: List of constitutional guard warnings
    """
    warnings = []

    # Defensive: Handle invalid input
    if approval_packet is None or not isinstance(approval_packet, dict):
        warnings.append("invalid approval_packet (expected dict, got None or non-dict)")
        error_record = V13ExecutionDraftSchema.create_error_record(
            summary="execution draft binding failed: invalid approval packet."
        )
        return {
            "execution_draft": error_record,
            "warnings": warnings,
        }

    # Check packet status
    packet_status = approval_packet.get("v11_packet_status")
    if packet_status != "AVAILABLE":
        warnings.append(f"approval packet status: {packet_status} (expected AVAILABLE)")
        error_record = V13ExecutionDraftSchema.create_error_record(
            summary="execution draft binding failed: approval packet not available."
        )
        return {
            "execution_draft": error_record,
            "warnings": warnings,
        }

    # Extract inputs (source presence only, no values)
    inputs = _extract_inputs_from_packet(approval_packet)

    # Extract constraints (labels only, no values)
    constraints = _extract_constraints_from_packet(approval_packet)

    # Determine intended shape (structural binding, not recommendation)
    intended_shape = _determine_intended_shape(constraints, mode)

    # Extract basis
    basis = _extract_basis_from_packet(approval_packet)

    # Create draft record
    draft_summary = "execution draft available from approval packet."
    draft_record = V13ExecutionDraftSchema.create_draft_record(
        version=DRAFT_VERSION_V1,
        status=DRAFT_STATUS_AVAILABLE,
        mode=DRAFT_MODE_READ_ONLY,
        summary=draft_summary,
        inputs=inputs,
        constraints=constraints,
        intended_shape=intended_shape,
        basis=basis,
        artifacts=[],
        warnings=[],
    )

    # Validate schema
    schema_errors = V13ExecutionDraftSchema.validate_draft_record(draft_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    # Run constitutional guards
    guard_warnings = check_draft_record(draft_record)
    if guard_warnings:
        warnings.extend(guard_warnings)

    # Add warnings to draft record
    draft_record["v13_draft_warnings"] = warnings

    return {
        "execution_draft": draft_record,
        "warnings": warnings,
    }


def get_binding_engine_v1_info() -> Dict[str, Any]:
    """
    Get binding engine information.

    Returns:
        Dict with binding engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "packet_to_draft_binding",
        "philosophy": "Binding only (not recommendation, not instruction)",
        "input_formats": [
            "artifact_bundle (PR115/PR116)",
            "approval_packet (PR124/PR140)",
        ],
        "output_format": "execution_draft (PR141)",
        "intended_shape_mapping": {
            "INELIGIBLE": "NO_ACTION",
            "SUPPRESSED": "NO_ACTION",
            "REQUIRED": "HUMAN_REVIEW_REQUIRED",
            "DRY_RUN_ONLY": "SIMULATION_ONLY",
            "CONSIDERATION_ONLY": "CONSIDERATION_ONLY",
            "default": "SIMULATION_ONLY",
        },
        "constitutional_guarantees": [
            "READ-ONLY",
            "label_projection_only",
            "no_numeric_values",
            "no_token_literals",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.3 Packet → Draft Binding Engine - Self Test")
    print("=" * 60)
    print()

    # Test 1: Bind from artifact bundle
    print("Test 1: Bind from artifact bundle")
    test_bundle = {
        "artifacts": {
            "regime_record": {"v11_regime_level": "REGIME_MEDIUM"},
            "drift_record": {"v10_drift_level": "DRIFT_LOW"},
            "permission_record": {"v10_permission_label": "PERMISSION_ALLOWED"},
            "trajectory_record": {"v11_trajectory_signal": "IMPROVING"},
            "eligibility_record": {"v11_eligibility_label": "ELIGIBLE"},
        }
    }

    result1 = build_execution_draft_from_bundle_v1(test_bundle)
    print(f"Draft status: {result1['execution_draft'].get('v13_draft_status')}")
    print(f"Inputs: {result1['execution_draft'].get('v13_draft_inputs')}")
    print(f"Constraints: {result1['execution_draft'].get('v13_draft_constraints')}")
    print(f"Intended shape: {result1['execution_draft'].get('v13_draft_intended_shape')}")
    print(f"Warnings: {len(result1['warnings'])}")
    print()

    # Test 2: Bind from approval packet
    print("Test 2: Bind from approval packet")
    test_packet = {
        "v11_packet_status": "AVAILABLE",
        "v11_packet_permission_label": "PERMISSION_ALLOWED",
        "v11_packet_trajectory_signal": "IMPROVING",
        "v11_packet_eligibility_label": "ELIGIBLE",
        "v11_packet_artifacts": ["regime_record", "drift_record"],
    }

    result2 = build_execution_draft_from_packet_v1(test_packet)
    print(f"Draft status: {result2['execution_draft'].get('v13_draft_status')}")
    print(f"Inputs: {result2['execution_draft'].get('v13_draft_inputs')}")
    print(f"Constraints: {result2['execution_draft'].get('v13_draft_constraints')}")
    print(f"Intended shape: {result2['execution_draft'].get('v13_draft_intended_shape')}")
    print(f"Warnings: {len(result2['warnings'])}")
    print()

    # Test 3: Invalid input (defensive)
    print("Test 3: Invalid input (defensive)")
    result3 = build_execution_draft_from_bundle_v1(None)
    print(f"Draft status: {result3['execution_draft'].get('v13_draft_status')}")
    print(f"Warnings: {len(result3['warnings'])}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
