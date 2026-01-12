#!/usr/bin/env python3
"""
PR124: v1.1 Approval Packet Schema v1 (READ-ONLY)

Purpose:
    Define schema for approval packet records.
    Packet = Review Unit (not decision/instruction).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals: No SUI, USDC, BTC, ETH
    - No amounts: No numeric values in output
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No cross-component coupling: No "approved therefore execute"

Packet Philosophy:
    Packet ≠ Decision
    Packet ≠ Instruction
    Packet = Review Unit Carrier

    Packet provides:
    - Bundled component records (context, narrative, preview, gate, registry)
    - Non-prescriptive summary
    - Artifact references and basis
    - Current approval state (as label only)

    Packet does NOT:
    - Recommend actions
    - Evaluate quality (good/bad)
    - Contain token names, amounts, addresses
    - Prescribe responses
    - Imply what to do next

v11_packet_ Prefix:
    All packet fields use v11_packet_ prefix for clear separation
    from other v1.1 fields.

Schema Fields:
    - v11_packet_mode: ON | OFF
    - v11_packet_status: AVAILABLE | UNAVAILABLE | ERROR
    - v11_packet_packet_type: APPROVAL_PACKET | UNCLASSIFIED
    - v11_packet_summary: Short non-prescriptive summary
    - v11_packet_components: Object of embedded component records
        - explain_context: PR122 record or projection
        - narrative: PR123 record or projection
        - preview: PR112 record or projection
        - approval_gate: PR113 record or projection
        - approval_registry: PR114 record or projection
    - v11_packet_basis: Array of field names used
    - v11_packet_artifacts: Array of artifact labels
"""

from typing import Any, Dict, List, Optional


class V11ApprovalPacketSchema:
    """v1.1 Approval Packet Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "v11_packet_mode",
        "v11_packet_status",
        "v11_packet_packet_type",
        "v11_packet_summary",
        "v11_packet_components",
        "v11_packet_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v11_packet_artifacts",
        "v11_packet_warnings",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]
    VALID_PACKET_TYPES = ["APPROVAL_PACKET", "UNCLASSIFIED"]

    # Component names
    COMPONENT_NAMES = [
        "explain_context",
        "narrative",
        "preview",
        "approval_gate",
        "approval_registry",
    ]

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty packet record.

        Returns:
            Empty packet record
        """
        return {
            "v11_packet_mode": "ON",
            "v11_packet_status": "UNAVAILABLE",
            "v11_packet_packet_type": "UNCLASSIFIED",
            "v11_packet_summary": "no packet available.",
            "v11_packet_components": {},
            "v11_packet_basis": [],
        }

    @staticmethod
    def create_error_record(error_message: str = "packet assembly failed.") -> Dict[str, Any]:
        """
        Create an ERROR packet record.

        Args:
            error_message: Error description

        Returns:
            ERROR packet record
        """
        return {
            "v11_packet_mode": "ON",
            "v11_packet_status": "ERROR",
            "v11_packet_packet_type": "UNCLASSIFIED",
            "v11_packet_summary": error_message,
            "v11_packet_components": {},
            "v11_packet_basis": [],
        }

    @staticmethod
    def create_approval_packet_record(
        summary: str,
        components: Dict[str, Any],
        basis: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an approval packet record.

        Args:
            summary: Short non-prescriptive summary
            components: Object of embedded component records
            basis: Optional array of field names referenced
            artifacts: Optional array of artifact names
            warnings: Optional array of warnings

        Returns:
            Approval packet record
        """
        record = {
            "v11_packet_mode": "ON",
            "v11_packet_status": "AVAILABLE",
            "v11_packet_packet_type": "APPROVAL_PACKET",
            "v11_packet_summary": summary,
            "v11_packet_components": components,
            "v11_packet_basis": basis or [],
        }

        if artifacts:
            record["v11_packet_artifacts"] = artifacts

        if warnings:
            record["v11_packet_warnings"] = warnings

        return record

    @staticmethod
    def create_minimal_projection(record: Dict[str, Any], record_type: str) -> Dict[str, Any]:
        """
        Create minimal projection of a component record.

        Args:
            record: Full component record
            record_type: Type hint (explain_context, narrative, etc.)

        Returns:
            Minimal projection with mode/status/type + basis/artifacts
        """
        if not record or not isinstance(record, dict):
            return {"status": "UNAVAILABLE", "type": record_type}

        projection = {}

        # Extract common fields based on record type
        if record_type == "explain_context":
            projection["mode"] = record.get("v11_explain_mode", "UNKNOWN")
            projection["status"] = record.get("v11_explain_status", "UNKNOWN")
            projection["signals"] = record.get("v11_explain_signals", [])
            projection["basis"] = record.get("v11_explain_basis", [])
            projection["artifacts"] = record.get("v11_explain_artifacts", [])

        elif record_type == "narrative":
            projection["mode"] = record.get("v11_narrative_mode", "UNKNOWN")
            projection["status"] = record.get("v11_narrative_status", "UNKNOWN")
            projection["style"] = record.get("v11_narrative_style", "UNKNOWN")
            projection["text_length"] = len(record.get("v11_narrative_text", ""))
            projection["basis"] = record.get("v11_narrative_basis", [])
            projection["artifacts"] = record.get("v11_narrative_artifacts", [])

        elif record_type == "preview":
            projection["mode"] = record.get("v11_preview_mode", "UNKNOWN")
            projection["status"] = record.get("v11_preview_status", "UNKNOWN")
            projection["risk_surface"] = record.get("v11_preview_risk_surface", "UNKNOWN")
            projection["basis"] = record.get("v11_preview_basis", [])
            projection["artifacts"] = record.get("v11_preview_artifacts", [])

        elif record_type == "approval_gate":
            projection["mode"] = record.get("v11_approval_mode", "UNKNOWN")
            projection["status"] = record.get("v11_approval_status", "UNKNOWN")
            projection["requirement"] = record.get("v11_approval_requirement", "UNKNOWN")
            projection["state"] = record.get("v11_approval_state", "UNKNOWN")
            projection["basis"] = record.get("v11_approval_basis", [])
            projection["artifacts"] = record.get("v11_approval_artifacts", [])

        elif record_type == "approval_registry":
            projection["mode"] = record.get("v11_registry_mode", "UNKNOWN")
            projection["status"] = record.get("v11_registry_status", "UNKNOWN")
            projection["entry_count"] = len(record.get("v11_registry_entries", []))
            projection["basis"] = record.get("v11_registry_basis", [])

        projection["type"] = record_type
        return projection

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate packet record structure.

        Args:
            record: Packet record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V11ApprovalPacketSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v11_packet_mode" in record:
            if record["v11_packet_mode"] not in V11ApprovalPacketSchema.VALID_MODES:
                warnings.append(f"Invalid packet mode: {record['v11_packet_mode']}")

        # Validate status
        if "v11_packet_status" in record:
            if record["v11_packet_status"] not in V11ApprovalPacketSchema.VALID_STATUSES:
                warnings.append(f"Invalid packet status: {record['v11_packet_status']}")

        # Validate packet_type
        if "v11_packet_packet_type" in record:
            if record["v11_packet_packet_type"] not in V11ApprovalPacketSchema.VALID_PACKET_TYPES:
                warnings.append(f"Invalid packet type: {record['v11_packet_packet_type']}")

        # Validate summary (must be string)
        if "v11_packet_summary" in record:
            if not isinstance(record["v11_packet_summary"], str):
                warnings.append("Packet summary must be string")

        # Validate components (must be dict)
        if "v11_packet_components" in record:
            if not isinstance(record["v11_packet_components"], dict):
                warnings.append("Components must be a dict")

        # Validate basis (must be list of strings)
        if "v11_packet_basis" in record:
            if not isinstance(record["v11_packet_basis"], list):
                warnings.append("Basis must be a list")
            else:
                for basis_field in record["v11_packet_basis"]:
                    if not isinstance(basis_field, str):
                        warnings.append(f"Basis field must be string: {basis_field}")

        # Validate artifacts (must be list of strings if present)
        if "v11_packet_artifacts" in record:
            if not isinstance(record["v11_packet_artifacts"], list):
                warnings.append("Artifacts must be a list")
            else:
                for artifact in record["v11_packet_artifacts"]:
                    if not isinstance(artifact, str):
                        warnings.append(f"Artifact must be string: {artifact}")

        return warnings


def get_packet_schema_info() -> Dict[str, Any]:
    """
    Get packet schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.1",
        "schema_type": "approval_packet",
        "valid_modes": V11ApprovalPacketSchema.VALID_MODES,
        "valid_statuses": V11ApprovalPacketSchema.VALID_STATUSES,
        "valid_packet_types": V11ApprovalPacketSchema.VALID_PACKET_TYPES,
        "component_names": V11ApprovalPacketSchema.COMPONENT_NAMES,
        "required_fields": V11ApprovalPacketSchema.REQUIRED_FIELDS,
        "optional_fields": V11ApprovalPacketSchema.OPTIONAL_FIELDS,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "no_token_literals",
            "no_amounts",
            "no_addresses",
            "no_trading_vocabulary",
            "no_cross_component_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Approval Packet Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V11ApprovalPacketSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Validate empty record
    print("Test 2: Validate empty record")
    warnings = V11ApprovalPacketSchema.validate_structure(empty)
    print(f"Warnings: {warnings}")
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V11ApprovalPacketSchema.create_error_record("test error")
    print(json.dumps(error, indent=2))
    print()

    # Test 4: Create minimal projection
    print("Test 4: Create minimal projection")
    sample_narrative = {
        "v11_narrative_mode": "ON",
        "v11_narrative_status": "AVAILABLE",
        "v11_narrative_style": "STANDARD",
        "v11_narrative_text": "test narrative",
        "v11_narrative_basis": ["v11_regime_level"],
    }
    projection = V11ApprovalPacketSchema.create_minimal_projection(sample_narrative, "narrative")
    print(json.dumps(projection, indent=2))
    print()

    # Test 5: Create full packet record
    print("Test 5: Create full packet record")
    packet = V11ApprovalPacketSchema.create_approval_packet_record(
        summary="approval packet assembled. narrative and preview included. approval requirement labeled as REQUIRED.",
        components={
            "explain_context": projection,
            "narrative": projection,
        },
        basis=["v11_regime_level", "v10_drift_level"],
        artifacts=["pr110_regime_record", "pr120_drift_record"],
    )
    print(json.dumps(packet, indent=2))
    print()

    # Test 6: Validate full record
    print("Test 6: Validate full record")
    warnings = V11ApprovalPacketSchema.validate_structure(packet)
    print(f"Warnings: {warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
