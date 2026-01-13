#!/usr/bin/env python3
"""
PR143: v1.3 Execution Gate Engine v1 (READ-ONLY)

Purpose:
    Build execution gate from execution draft (PR141/PR142).
    ALWAYS returns BLOCKED with structural block reasons.

Gate Philosophy:
    Gate ≠ Allow
    Gate = Explain why execution is not reachable (yet)
    Execution is defined by prohibition first.

API:
    build_execution_gate_from_draft_v1(draft_record) -> dict
    build_execution_gate_from_bundle_v1(artifact_bundle) -> dict

Behavior:
    - ALWAYS return gate_state = "BLOCKED"
    - Determine block reasons from draft fields (label-only)
    - Never produce "ALLOW" or "ready to execute" language
    - Defensive: invalid input → valid ERROR record with BLOCKED + reasons

Block Reason Mapping (label-only, structural):
    - draft.status == "ERROR" → REASON_INVALID_DRAFT
    - ACTION_CLASS_NO_ACTION → REASON_NO_ACTION_SHAPE
    - ACTION_CLASS_HUMAN_REVIEW_REQUIRED → REASON_HUMAN_REVIEW_REQUIRED
    - ACTION_CLASS_SIMULATION_ONLY → REASON_SIMULATION_ONLY
    - ACTION_CLASS_CONSIDERATION_ONLY → REASON_CONSIDERATION_ONLY
    - HARD_* constraints → REASON_HARD_CONSTRAINT
    - SUPPRESSED → REASON_SUPPRESSED
    - Missing inputs → REASON_MISSING_INPUTS
    - Draft warnings present → REASON_DRAFT_WARNINGS
    - Always include → REASON_NO_EXECUTION_LOGIC

Constitutional Constraints:
    - READ-ONLY: No execution logic
    - Always BLOCKED: Never allows execution
    - Label-only: No numeric values, no token literals
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gate.v13_execution_gate_schema import (
    V13ExecutionGateSchema,
    GATE_VERSION_V1_3,
    GATE_STATUS_AVAILABLE,
    GATE_STATUS_ERROR,
    GATE_MODE_READ_ONLY,
    GATE_STATE_BLOCKED,
    REASON_INVALID_DRAFT,
    REASON_NO_ACTION_SHAPE,
    REASON_HUMAN_REVIEW_REQUIRED,
    REASON_SIMULATION_ONLY,
    REASON_CONSIDERATION_ONLY,
    REASON_HARD_CONSTRAINT,
    REASON_SUPPRESSED,
    REASON_MISSING_INPUTS,
    REASON_DRAFT_WARNINGS,
    REASON_NO_EXECUTION_LOGIC,
)


def _determine_block_reasons_from_draft(draft_record: Dict[str, Any]) -> List[str]:
    """
    Determine block reasons from draft record (label-only, structural).

    Args:
        draft_record: Execution draft record

    Returns:
        List of block reason labels
    """
    reasons = []

    if not isinstance(draft_record, dict):
        return [REASON_INVALID_DRAFT, REASON_NO_EXECUTION_LOGIC]

    # Check draft status
    draft_status = draft_record.get("v13_draft_status")
    if draft_status == "ERROR":
        reasons.append(REASON_INVALID_DRAFT)

    # Check intended_shape (action_class)
    intended_shape = draft_record.get("v13_draft_intended_shape", {})
    if isinstance(intended_shape, dict):
        action_class = intended_shape.get("action_class", "")

        if action_class == "NO_ACTION" or action_class == "NONE":
            reasons.append(REASON_NO_ACTION_SHAPE)
        elif action_class == "HUMAN_REVIEW_REQUIRED":
            reasons.append(REASON_HUMAN_REVIEW_REQUIRED)
        elif action_class == "SIMULATION_ONLY":
            reasons.append(REASON_SIMULATION_ONLY)
        elif action_class == "CONSIDERATION_ONLY":
            reasons.append(REASON_CONSIDERATION_ONLY)
        elif action_class == "DRAFT_ONLY":
            # DRAFT_ONLY also blocks (draft is not execution)
            reasons.append(REASON_SIMULATION_ONLY)

    # Check constraints for HARD_* patterns
    constraints = draft_record.get("v13_draft_constraints", {})
    if isinstance(constraints, dict):
        for key, value in constraints.items():
            if isinstance(value, str):
                if "HARD_" in value.upper() or "HARD" in value.upper():
                    reasons.append(REASON_HARD_CONSTRAINT)
                    break

        # Check for SUPPRESSED
        for key, value in constraints.items():
            if isinstance(value, str):
                if "SUPPRESSED" in value.upper():
                    reasons.append(REASON_SUPPRESSED)
                    break

    # Check inputs_present flags
    inputs = draft_record.get("v13_draft_inputs", {})
    if isinstance(inputs, dict):
        # Check for missing critical inputs
        has_regime = any("regime" in k.lower() for k in inputs.keys())
        has_drift = any("drift" in k.lower() for k in inputs.keys())

        if not has_regime or not has_drift:
            reasons.append(REASON_MISSING_INPUTS)

    # Check draft warnings
    warnings = draft_record.get("v13_draft_warnings", [])
    if isinstance(warnings, list) and len(warnings) > 0:
        reasons.append(REASON_DRAFT_WARNINGS)

    # ALWAYS include REASON_NO_EXECUTION_LOGIC (gate never allows execution)
    if REASON_NO_EXECUTION_LOGIC not in reasons:
        reasons.append(REASON_NO_EXECUTION_LOGIC)

    # Remove duplicates while preserving order
    seen = set()
    unique_reasons = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique_reasons.append(r)

    return unique_reasons


def _extract_reason_details(draft_record: Dict[str, Any], reasons: List[str]) -> List[Dict[str, Any]]:
    """
    Extract reason details from draft record (label-only).

    Args:
        draft_record: Execution draft record
        reasons: List of block reasons

    Returns:
        List of reason detail dicts
    """
    details = []

    for reason in reasons:
        detail = {
            "reason": reason,
            "source": "execution_draft",
        }

        # Add context based on reason type (label-only)
        if reason == REASON_INVALID_DRAFT:
            draft_status = draft_record.get("v13_draft_status", "UNKNOWN")
            detail["draft_status"] = draft_status

        elif reason in [REASON_NO_ACTION_SHAPE, REASON_HUMAN_REVIEW_REQUIRED,
                       REASON_SIMULATION_ONLY, REASON_CONSIDERATION_ONLY]:
            intended_shape = draft_record.get("v13_draft_intended_shape", {})
            if isinstance(intended_shape, dict):
                detail["action_class"] = intended_shape.get("action_class", "UNKNOWN")

        elif reason == REASON_HARD_CONSTRAINT:
            constraints = draft_record.get("v13_draft_constraints", {})
            if isinstance(constraints, dict):
                hard_constraints = {k: v for k, v in constraints.items()
                                  if isinstance(v, str) and "HARD" in v.upper()}
                if hard_constraints:
                    detail["constraints"] = hard_constraints

        elif reason == REASON_SUPPRESSED:
            constraints = draft_record.get("v13_draft_constraints", {})
            if isinstance(constraints, dict):
                suppressed = {k: v for k, v in constraints.items()
                            if isinstance(v, str) and "SUPPRESSED" in v.upper()}
                if suppressed:
                    detail["constraints"] = suppressed

        elif reason == REASON_MISSING_INPUTS:
            inputs = draft_record.get("v13_draft_inputs", {})
            detail["inputs_present"] = isinstance(inputs, dict) and len(inputs) > 0

        elif reason == REASON_DRAFT_WARNINGS:
            warnings = draft_record.get("v13_draft_warnings", [])
            detail["warning_count"] = len(warnings) if isinstance(warnings, list) else 0

        details.append(detail)

    return details


def build_execution_gate_from_draft_v1(
    draft_record: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build execution gate from execution draft (ALWAYS BLOCKED).

    Args:
        draft_record: Execution draft record (PR141/PR142)

    Returns:
        Dict with:
        - execution_gate: PR143-compliant gate record (ALWAYS BLOCKED)
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid input
    if draft_record is None or not isinstance(draft_record, dict):
        warnings.append("invalid draft_record (expected dict, got None or non-dict)")
        error_record = V13ExecutionGateSchema.create_error_record(
            summary="execution gate generation failed: invalid draft.",
            block_reasons=[REASON_INVALID_DRAFT, REASON_NO_EXECUTION_LOGIC],
        )
        return {
            "execution_gate": error_record,
            "warnings": warnings,
        }

    # Determine block reasons (structural mapping, label-only)
    block_reasons = _determine_block_reasons_from_draft(draft_record)

    # Extract reason details (label-only)
    reason_details = _extract_reason_details(draft_record, block_reasons)

    # Extract basis
    basis = ["v13_execution_draft"]
    draft_basis = draft_record.get("v13_draft_basis", [])
    if isinstance(draft_basis, list):
        basis.extend(draft_basis)

    # Carry draft warnings
    draft_warnings = draft_record.get("v13_draft_warnings", [])
    if isinstance(draft_warnings, list):
        warnings.extend(draft_warnings)

    # Create gate record (ALWAYS BLOCKED)
    gate_summary = "execution gate produced. state blocked. reasons enumerated."
    gate_record = V13ExecutionGateSchema.create_gate_record(
        version=GATE_VERSION_V1_3,
        status=GATE_STATUS_AVAILABLE,
        mode=GATE_MODE_READ_ONLY,
        summary=gate_summary,
        gate_state=GATE_STATE_BLOCKED,  # ALWAYS BLOCKED
        block_reasons=block_reasons,
        reason_details=reason_details,
        basis=basis,
        artifacts=["v13_execution_draft"],
        warnings=warnings,
    )

    # Validate schema
    schema_errors = V13ExecutionGateSchema.validate_gate_record(gate_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    # Add warnings to gate record
    gate_record["v13_gate_warnings"] = warnings

    return {
        "execution_gate": gate_record,
        "warnings": warnings,
    }


def build_execution_gate_from_bundle_v1(
    artifact_bundle: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Build execution gate from artifact bundle (via draft).

    Args:
        artifact_bundle: Artifact bundle containing execution_draft or draft_record

    Returns:
        Dict with:
        - execution_gate: PR143-compliant gate record (ALWAYS BLOCKED)
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid input
    if artifact_bundle is None or not isinstance(artifact_bundle, dict):
        warnings.append("invalid artifact_bundle (expected dict, got None or non-dict)")
        error_record = V13ExecutionGateSchema.create_error_record(
            summary="execution gate generation failed: invalid bundle.",
            block_reasons=[REASON_INVALID_DRAFT, REASON_NO_EXECUTION_LOGIC],
        )
        return {
            "execution_gate": error_record,
            "warnings": warnings,
        }

    # Extract draft record from bundle
    draft_record = None
    if "execution_draft" in artifact_bundle:
        draft_record = artifact_bundle["execution_draft"]
    elif "draft_record" in artifact_bundle:
        draft_record = artifact_bundle["draft_record"]
    elif "artifacts" in artifact_bundle and isinstance(artifact_bundle["artifacts"], dict):
        artifacts = artifact_bundle["artifacts"]
        if "execution_draft" in artifacts:
            draft_record = artifacts["execution_draft"]
        elif "draft_record" in artifacts:
            draft_record = artifacts["draft_record"]

    if draft_record is None:
        warnings.append("artifact_bundle missing execution_draft or draft_record")
        error_record = V13ExecutionGateSchema.create_error_record(
            summary="execution gate generation failed: no draft in bundle.",
            block_reasons=[REASON_INVALID_DRAFT, REASON_NO_EXECUTION_LOGIC],
        )
        return {
            "execution_gate": error_record,
            "warnings": warnings,
        }

    # Build gate from draft
    result = build_execution_gate_from_draft_v1(draft_record)

    # Merge warnings
    result["warnings"].extend(warnings)
    result["execution_gate"]["v13_gate_warnings"] = result["warnings"]

    return result


def get_execution_gate_engine_v1_info() -> Dict[str, Any]:
    """
    Get execution gate engine information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "execution_gate",
        "philosophy": "Gate ≠ Allow. Gate = Explain why execution is not reachable (yet)",
        "input_formats": [
            "execution_draft (PR141)",
            "artifact_bundle (containing draft)",
        ],
        "output_format": "execution_gate (PR143)",
        "gate_state": "BLOCKED (always)",
        "block_reason_mapping": {
            "draft_error": "REASON_INVALID_DRAFT",
            "NO_ACTION": "REASON_NO_ACTION_SHAPE",
            "HUMAN_REVIEW_REQUIRED": "REASON_HUMAN_REVIEW_REQUIRED",
            "SIMULATION_ONLY": "REASON_SIMULATION_ONLY",
            "CONSIDERATION_ONLY": "REASON_CONSIDERATION_ONLY",
            "HARD_constraint": "REASON_HARD_CONSTRAINT",
            "SUPPRESSED": "REASON_SUPPRESSED",
            "missing_inputs": "REASON_MISSING_INPUTS",
            "draft_warnings": "REASON_DRAFT_WARNINGS",
            "always": "REASON_NO_EXECUTION_LOGIC",
        },
        "constitutional_guarantees": [
            "READ-ONLY",
            "always_blocked",
            "no_execution",
            "no_allow_state",
            "label_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.3 Execution Gate Engine - Self Test")
    print("=" * 60)
    print()

    # Test 1: Gate from valid draft (SIMULATION_ONLY)
    print("Test 1: Gate from valid draft (SIMULATION_ONLY)")
    test_draft = {
        "v13_draft_version": "v1",
        "v13_draft_status": "AVAILABLE",
        "v13_draft_mode": "READ_ONLY",
        "v13_draft_summary": "execution draft available.",
        "v13_draft_inputs": {"regime_record_present": "true", "drift_record_present": "true"},
        "v13_draft_constraints": {"permission": "PERMISSION_ALLOWED", "eligibility": "ELIGIBLE"},
        "v13_draft_intended_shape": {"action_class": "SIMULATION_ONLY"},
        "v13_draft_basis": ["v13_approval_packet"],
        "v13_draft_artifacts": [],
        "v13_draft_warnings": [],
    }

    result1 = build_execution_gate_from_draft_v1(test_draft)
    print(f"Gate status: {result1['execution_gate'].get('v13_gate_status')}")
    print(f"Gate state: {result1['execution_gate'].get('v13_gate_gate_state')}")
    print(f"Block reasons: {result1['execution_gate'].get('v13_gate_block_reasons')}")
    print(f"Warnings: {len(result1['warnings'])}")
    print()

    # Test 2: Gate from ERROR draft
    print("Test 2: Gate from ERROR draft")
    test_draft_error = {
        "v13_draft_version": "v1",
        "v13_draft_status": "ERROR",
        "v13_draft_mode": "READ_ONLY",
        "v13_draft_summary": "execution draft failed.",
        "v13_draft_inputs": {},
        "v13_draft_constraints": {},
        "v13_draft_intended_shape": {"action_class": "NONE"},
        "v13_draft_basis": [],
        "v13_draft_artifacts": [],
        "v13_draft_warnings": ["test warning"],
    }

    result2 = build_execution_gate_from_draft_v1(test_draft_error)
    print(f"Gate state: {result2['execution_gate'].get('v13_gate_gate_state')}")
    print(f"Block reasons: {result2['execution_gate'].get('v13_gate_block_reasons')}")
    print()

    # Test 3: Gate from invalid input (defensive)
    print("Test 3: Gate from invalid input (defensive)")
    result3 = build_execution_gate_from_draft_v1(None)
    print(f"Gate status: {result3['execution_gate'].get('v13_gate_status')}")
    print(f"Gate state: {result3['execution_gate'].get('v13_gate_gate_state')}")
    print(f"Warnings: {len(result3['warnings'])}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
