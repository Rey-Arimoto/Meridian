#!/usr/bin/env python3
"""
PR122: v1.1 Human Explanation Context Schema v1 (READ-ONLY)

Purpose:
    Define schema for human explanation context records.
    Explanation Context = Structural Situation Summary (not action/recommendation).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals: No SUI, USDC, BTC, ETH
    - No amounts: No numeric values in output
    - No addresses: No 0x... patterns

Explanation Context Philosophy:
    Context ≠ Action
    Context ≠ Recommendation
    Context = Structural Situation Description

    Context provides:
    - Current state signals (regime, drift, permission, etc.)
    - Artifact references (which records explain this state)
    - Non-evaluative summary
    - Basis field names (no raw values)

    Context does NOT:
    - Recommend actions
    - Evaluate quality (good/bad)
    - Contain token names, amounts, addresses
    - Prescribe responses

v11_explain_ Prefix:
    All explanation context fields use v11_explain_ prefix for clear separation
    from other v1.1 fields.

Schema Fields:
    - v11_explain_mode: ON | OFF
    - v11_explain_status: AVAILABLE | UNAVAILABLE
    - v11_explain_summary: Non-evaluative structural situation description
    - v11_explain_signals: Array of structural signal labels (regime, drift, permission, etc.)
    - v11_explain_basis: Array of field names referenced
    - v11_explain_artifacts: Array of artifact names referenced
"""

from typing import Any, Dict, List, Optional


class V11HumanExplanationContextSchema:
    """v1.1 Human Explanation Context Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "v11_explain_mode",
        "v11_explain_status",
        "v11_explain_summary",
        "v11_explain_signals",
        "v11_explain_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v11_explain_artifacts",
        "v11_explain_warnings",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE"]

    # Example signal types (not exhaustive - signals are extensible)
    EXAMPLE_SIGNAL_TYPES = [
        # Regime signals
        "REGIME_LOW",
        "REGIME_MEDIUM",
        "REGIME_HIGH",
        "REGIME_CRITICAL",
        # Drift signals
        "DRIFT_NONE",
        "DRIFT_LOW",
        "DRIFT_MEDIUM",
        "DRIFT_HIGH",
        "DRIFT_CRITICAL",
        # Permission signals
        "PERMISSION_UNKNOWN",
        "PERMISSION_HOLD",
        "PERMISSION_DRY_RUN_ONLY",
        "PERMISSION_ALLOW",
        # Preview signals
        "PREVIEW_BLOCKED",
        "PREVIEW_AVAILABLE",
        # Approval signals
        "APPROVAL_NOT_REQUIRED",
        "APPROVAL_REQUIRED",
        "APPROVAL_REQUIRED_STRICT",
    ]

    # Allowed basis fields (extensible - includes all upstream v10/v11 fields)
    ALLOWED_BASIS_FIELDS = [
        # Regime (v11)
        "v11_regime_level",
        "v11_regime_status",
        # Drift (v10)
        "v10_drift_level",
        "v10_drift_status",
        # Policy (v11)
        "v11_policy_permission",
        "v11_policy_status",
        # Execution (v10)
        "v10_execution_permission",
        "v10_execution_status",
        # Preview (v11)
        "v11_preview_status",
        "v11_preview_risk_surface",
        # Approval (v11)
        "v11_approval_requirement",
        "v11_approval_status",
        # Plan (v10)
        "v10_plan_type",
        "v10_plan_status",
        # Simulation (v10)
        "v10_simulation_type",
        "v10_simulation_status",
    ]

    # Forbidden basis fields (v0.4 boundary protection)
    FORBIDDEN_BASIS_FIELDS = [
        "confidence_reason",
        "confidence_reason_version",
        "confidence_reason_generated_at",
    ]

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty explanation context record.

        Returns:
            Empty explanation context record
        """
        return {
            "v11_explain_mode": "ON",
            "v11_explain_status": "UNAVAILABLE",
            "v11_explain_summary": "no explanation context available.",
            "v11_explain_signals": [],
            "v11_explain_basis": [],
        }

    @staticmethod
    def create_explanation_record(
        summary: str,
        signals: List[str],
        basis: List[str],
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an explanation context record.

        Args:
            summary: Non-evaluative structural situation description
            signals: Array of structural signal labels
            basis: Array of field names referenced
            artifacts: Optional array of artifact names
            warnings: Optional array of warnings

        Returns:
            Explanation context record
        """
        record = {
            "v11_explain_mode": "ON",
            "v11_explain_status": "AVAILABLE",
            "v11_explain_summary": summary,
            "v11_explain_signals": signals,
            "v11_explain_basis": basis,
        }

        if artifacts:
            record["v11_explain_artifacts"] = artifacts

        if warnings:
            record["v11_explain_warnings"] = warnings

        return record

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate explanation context record structure.

        Args:
            record: Explanation context record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V11HumanExplanationContextSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v11_explain_mode" in record:
            if record["v11_explain_mode"] not in V11HumanExplanationContextSchema.VALID_MODES:
                warnings.append(f"Invalid explain mode: {record['v11_explain_mode']}")

        # Validate status
        if "v11_explain_status" in record:
            if record["v11_explain_status"] not in V11HumanExplanationContextSchema.VALID_STATUSES:
                warnings.append(f"Invalid explain status: {record['v11_explain_status']}")

        # Validate signals (must be list of strings)
        if "v11_explain_signals" in record:
            if not isinstance(record["v11_explain_signals"], list):
                warnings.append("Signals must be a list")
            else:
                for signal in record["v11_explain_signals"]:
                    if not isinstance(signal, str):
                        warnings.append(f"Signal must be string: {signal}")

        # Validate basis (must be list of strings)
        if "v11_explain_basis" in record:
            if not isinstance(record["v11_explain_basis"], list):
                warnings.append("Basis must be a list")
            else:
                for basis_field in record["v11_explain_basis"]:
                    if not isinstance(basis_field, str):
                        warnings.append(f"Basis field must be string: {basis_field}")
                    # Check for forbidden basis fields
                    if basis_field in V11HumanExplanationContextSchema.FORBIDDEN_BASIS_FIELDS:
                        warnings.append(f"Forbidden basis field: {basis_field}")

        # Validate artifacts (must be list of strings if present)
        if "v11_explain_artifacts" in record:
            if not isinstance(record["v11_explain_artifacts"], list):
                warnings.append("Artifacts must be a list")
            else:
                for artifact in record["v11_explain_artifacts"]:
                    if not isinstance(artifact, str):
                        warnings.append(f"Artifact must be string: {artifact}")

        return warnings


def get_explanation_schema_info() -> Dict[str, Any]:
    """
    Get explanation context schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.1",
        "schema_type": "human_explanation_context",
        "valid_modes": V11HumanExplanationContextSchema.VALID_MODES,
        "valid_statuses": V11HumanExplanationContextSchema.VALID_STATUSES,
        "example_signal_types": V11HumanExplanationContextSchema.EXAMPLE_SIGNAL_TYPES,
        "required_fields": V11HumanExplanationContextSchema.REQUIRED_FIELDS,
        "optional_fields": V11HumanExplanationContextSchema.OPTIONAL_FIELDS,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "no_token_literals",
            "no_amounts",
            "no_addresses",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Human Explanation Context Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V11HumanExplanationContextSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Validate empty record
    print("Test 2: Validate empty record")
    warnings = V11HumanExplanationContextSchema.validate_structure(empty)
    print(f"Warnings: {warnings}")
    print()

    # Test 3: Create full explanation record
    print("Test 3: Create full explanation record")
    explanation = V11HumanExplanationContextSchema.create_explanation_record(
        summary="current structural situation: regime medium, drift low, permission dry-run-only.",
        signals=["REGIME_MEDIUM", "DRIFT_LOW", "PERMISSION_DRY_RUN_ONLY"],
        basis=["v11_regime_level", "v10_drift_level", "v10_execution_permission"],
        artifacts=["pr110_regime_record", "pr120_drift_record", "pr101_execution_record"],
    )
    print(json.dumps(explanation, indent=2))
    print()

    # Test 4: Validate full record
    print("Test 4: Validate full record")
    warnings = V11HumanExplanationContextSchema.validate_structure(explanation)
    print(f"Warnings: {warnings}")
    print()

    # Test 5: Validate record with forbidden basis
    print("Test 5: Validate record with forbidden basis (should warn)")
    dirty_explanation = V11HumanExplanationContextSchema.create_explanation_record(
        summary="test",
        signals=[],
        basis=["confidence_reason"],  # Forbidden
    )
    warnings = V11HumanExplanationContextSchema.validate_structure(dirty_explanation)
    print(f"Warnings: {warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
