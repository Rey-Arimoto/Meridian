#!/usr/bin/env python3
"""
PR116: v1.0 Artifact Bundle Schema v1 (READ-ONLY)

Purpose:
    Define schema for artifact bundle records.
    Bundle = Chain-of-custody container for all pipeline artifacts.

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No should/must vocabulary
    - Bundle = container (not decision/evaluation/action)

Bundle Philosophy:
    Bundle ≠ Decision
    Bundle ≠ Evaluation
    Bundle ≠ Action
    Bundle = Output Container

    Bundle provides:
    - Chain-of-custody for artifacts
    - Stable schema for saving/comparing
    - Constitutional boundary enforcement
    - Regression testing foundation

    Bundle does NOT:
    - Make decisions
    - Evaluate quality
    - Recommend actions
    - Execute operations

Bundle Fields:
    - v10_bundle_mode: ON/OFF
    - v10_bundle_status: AVAILABLE/ERROR
    - v10_bundle_layers: ordered list of layer names
    - v10_bundle_artifacts: dict of {layer_name: artifact_record}
    - v10_bundle_summary: non-evaluative summary string
    - v10_bundle_basis: list of field names used (structural)
    - v10_bundle_warnings: optional list of warning strings
    - v10_bundle_error_info: optional error description (if status=ERROR)

Layer Names (Fixed Vocabulary):
    - CONNECTION: Sui connection layer (PR106)
    - OBSERVATION: Onchain observation fetch (PR107)
    - BRIDGE: Observation→Analytics bridge (PR108)
    - ANALYTICS: Onchain analytics layer (PR109)
    - REGIME: Entropy regime classification (PR110)
    - POLICY_BINDING: Regime→Policy binding (PR111)
    - BOUNDARY: Execution boundary guard (PR103)
    - PERMISSION: Execution permissioning (PR102)
    - PLAN: Execution plan generator (PR103)
    - SIMULATION: Execution simulation (PR104)
    - PREVIEW: Execution preview (PR112)
    - APPROVAL_GATE: Human approval gate (PR113)
    - APPROVAL_REGISTRY: Manual approval registry (PR114)
    - AUDIT_TRAIL: Execution audit trail (PR105)
"""

from typing import Any, Dict, List, Optional


class V10ArtifactBundleSchema:
    """Artifact bundle schema v1.0"""

    # Valid modes
    VALID_MODES = ["ON", "OFF"]

    # Valid statuses
    VALID_STATUSES = ["AVAILABLE", "ERROR"]

    # Valid layer names (fixed vocabulary)
    VALID_LAYERS = [
        "CONNECTION",
        "OBSERVATION",
        "BRIDGE",
        "ANALYTICS",
        "REGIME",
        "POLICY_BINDING",
        "BOUNDARY",
        "PERMISSION",
        "PLAN",
        "SIMULATION",
        "PREVIEW",
        "APPROVAL_GATE",
        "APPROVAL_REGISTRY",
        "AUDIT_TRAIL",
    ]

    # Standard pipeline order (v1)
    STANDARD_PIPELINE_ORDER = [
        "CONNECTION",
        "OBSERVATION",
        "BRIDGE",
        "ANALYTICS",
        "REGIME",
        "POLICY_BINDING",
        "PLAN",
        "PREVIEW",
        "APPROVAL_GATE",
        "APPROVAL_REGISTRY",
    ]

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty bundle record.

        Returns:
            Empty bundle record
        """
        return {
            "v10_bundle_mode": "ON",
            "v10_bundle_status": "AVAILABLE",
            "v10_bundle_layers": [],
            "v10_bundle_artifacts": {},
            "v10_bundle_summary": "empty artifact bundle. no layers present.",
            "v10_bundle_basis": [],
        }

    @staticmethod
    def create_error_record(
        error_info: str = "unknown error",
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an error bundle record.

        Args:
            error_info: Error description
            warnings: Optional list of warnings

        Returns:
            Error bundle record
        """
        record = {
            "v10_bundle_mode": "ON",
            "v10_bundle_status": "ERROR",
            "v10_bundle_layers": [],
            "v10_bundle_artifacts": {},
            "v10_bundle_summary": f"artifact bundle error. {error_info}",
            "v10_bundle_basis": [],
            "v10_bundle_error_info": error_info,
        }

        if warnings:
            record["v10_bundle_warnings"] = warnings

        return record

    @staticmethod
    def create_bundle_record(
        layers: List[str],
        artifacts: Dict[str, Any],
        summary: str,
        basis: List[str],
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a bundle record.

        Args:
            layers: Ordered list of layer names
            artifacts: Dict of {layer_name: artifact_record}
            summary: Non-evaluative summary
            basis: List of field names used
            warnings: Optional list of warnings

        Returns:
            Bundle record
        """
        record = {
            "v10_bundle_mode": "ON",
            "v10_bundle_status": "AVAILABLE",
            "v10_bundle_layers": layers,
            "v10_bundle_artifacts": artifacts,
            "v10_bundle_summary": summary,
            "v10_bundle_basis": basis,
        }

        if warnings:
            record["v10_bundle_warnings"] = warnings

        return record

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate bundle record structure.

        Args:
            record: Bundle record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        required_fields = [
            "v10_bundle_mode",
            "v10_bundle_status",
            "v10_bundle_layers",
            "v10_bundle_artifacts",
            "v10_bundle_summary",
            "v10_bundle_basis",
        ]

        for field in required_fields:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v10_bundle_mode" in record:
            if record["v10_bundle_mode"] not in V10ArtifactBundleSchema.VALID_MODES:
                warnings.append(
                    f"Invalid bundle mode: {record['v10_bundle_mode']}"
                )

        # Validate status
        if "v10_bundle_status" in record:
            if (
                record["v10_bundle_status"]
                not in V10ArtifactBundleSchema.VALID_STATUSES
            ):
                warnings.append(
                    f"Invalid bundle status: {record['v10_bundle_status']}"
                )

        # Validate layers
        if "v10_bundle_layers" in record:
            if not isinstance(record["v10_bundle_layers"], list):
                warnings.append("Bundle layers must be a list")
            else:
                for layer in record["v10_bundle_layers"]:
                    if layer not in V10ArtifactBundleSchema.VALID_LAYERS:
                        warnings.append(f"Invalid layer name: {layer}")

        # Validate artifacts
        if "v10_bundle_artifacts" in record:
            if not isinstance(record["v10_bundle_artifacts"], dict):
                warnings.append("Bundle artifacts must be a dict")
            else:
                # Check that all layer names in artifacts are in layers list
                layers = record.get("v10_bundle_layers", [])
                for layer_name in record["v10_bundle_artifacts"].keys():
                    if layer_name not in layers:
                        warnings.append(
                            f"Artifact layer '{layer_name}' not in layers list"
                        )

        # Validate basis
        if "v10_bundle_basis" in record:
            if not isinstance(record["v10_bundle_basis"], list):
                warnings.append("Bundle basis must be a list")

        return warnings


def get_bundle_schema_info() -> Dict[str, Any]:
    """
    Get bundle schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "artifact_bundle",
        "valid_modes": V10ArtifactBundleSchema.VALID_MODES,
        "valid_statuses": V10ArtifactBundleSchema.VALID_STATUSES,
        "valid_layers": V10ArtifactBundleSchema.VALID_LAYERS,
        "standard_pipeline_order": V10ArtifactBundleSchema.STANDARD_PIPELINE_ORDER,
        "required_fields": [
            "v10_bundle_mode",
            "v10_bundle_status",
            "v10_bundle_layers",
            "v10_bundle_artifacts",
            "v10_bundle_summary",
            "v10_bundle_basis",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Artifact Bundle Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V10ArtifactBundleSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Validate empty record
    print("Test 2: Validate empty record")
    warnings = V10ArtifactBundleSchema.validate_structure(empty)
    print(f"Warnings: {warnings}")
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V10ArtifactBundleSchema.create_error_record(
        error_info="test error",
        warnings=["test warning"],
    )
    print(json.dumps(error, indent=2))
    print()

    # Test 4: Create bundle record
    print("Test 4: Create bundle record")
    bundle = V10ArtifactBundleSchema.create_bundle_record(
        layers=["REGIME", "POLICY_BINDING", "PREVIEW"],
        artifacts={
            "REGIME": {"v11_regime_level": "LOW"},
            "POLICY_BINDING": {"v11_execution_permission_override": "DRY_RUN_ONLY"},
            "PREVIEW": {"v11_preview_mode": "ON"},
        },
        summary="artifact bundle with 3 layers. pipeline output captured.",
        basis=["pipeline_artifacts"],
        warnings=None,
    )
    print(json.dumps(bundle, indent=2))
    print()

    # Test 5: Validate bundle record
    print("Test 5: Validate bundle record")
    warnings = V10ArtifactBundleSchema.validate_structure(bundle)
    print(f"Warnings: {warnings}")
    print()

    # Test 6: Validate invalid record
    print("Test 6: Validate invalid record (missing fields)")
    invalid = {"v10_bundle_mode": "ON"}
    warnings = V10ArtifactBundleSchema.validate_structure(invalid)
    print(f"Warnings: {warnings}")
    print()

    # Test 7: Validate invalid layer names
    print("Test 7: Validate invalid layer names")
    invalid_layers = V10ArtifactBundleSchema.create_bundle_record(
        layers=["INVALID_LAYER", "REGIME"],
        artifacts={"INVALID_LAYER": {}, "REGIME": {}},
        summary="test",
        basis=[],
    )
    warnings = V10ArtifactBundleSchema.validate_structure(invalid_layers)
    print(f"Warnings: {warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
