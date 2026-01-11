#!/usr/bin/env python3
"""
PR105: v1.0 Execution Audit Trail Schema (READ-ONLY)

Purpose:
    Define schema for v1.0 execution audit trail records.
    Audit Trail = Causal Chain Trace (not execution).

Constitutional Constraints:
    - READ-ONLY: No execution logic or trading
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - No amounts: No numeric values, prices, quantities
    - No token literals: No SUI, USDC, BTC, etc.
    - No addresses: No wallet/contract addresses

Audit Trail Definition:
    Audit Trail = Causal Chain Documentation

    Links interpretation analytics → blindspot → boundary →
    permission → plan → simulation as explicit chain-of-custody.

    Audit Trail is NOT:
    - Execution (no trading, no wallet, no transactions)
    - Evaluation (no good/bad judgment)
    - Recommendation (no should/must)

Schema Fields (v10_audit_ prefix):
    - v10_audit_mode: ON | OFF
    - v10_audit_status: AVAILABLE | UNAVAILABLE
    - v10_audit_chain: Array of chain events (ordered)
    - v10_audit_summary: Non-evaluative audit description

Chain Event Structure:
    - layer: Layer name (INTERPRETATION_ANALYTICS, BLINDSPOT, etc.)
    - artifact: Artifact identifier
    - basis: Array of field names referenced
"""

from typing import Any, Dict, List


class V10ExecutionAuditTrailSchema:
    """v1.0 Execution Audit Trail Schema Definition."""

    # Required fields in all audit trail records
    REQUIRED_FIELDS = [
        "v10_audit_mode",
        "v10_audit_status",
        "v10_audit_chain",
        "v10_audit_summary",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE"]

    # Valid chain layers (fixed order in v1)
    VALID_LAYERS = [
        "INTERPRETATION_ANALYTICS",  # PR64
        "BLINDSPOT",                 # PR81
        "BOUNDARY",                  # PR91
        "PERMISSION",                # PR101
        "PLAN",                      # PR103
        "SIMULATION",                # PR104
    ]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate audit trail record structure.

        Args:
            record: Audit trail record to validate

        Returns:
            List of warning messages (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V10ExecutionAuditTrailSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Check mode enum
        if "v10_audit_mode" in record:
            if record["v10_audit_mode"] not in V10ExecutionAuditTrailSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v10_audit_mode: {record['v10_audit_mode']}"
                )

        # Check status enum
        if "v10_audit_status" in record:
            if record["v10_audit_status"] not in V10ExecutionAuditTrailSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v10_audit_status: {record['v10_audit_status']}"
                )

        # Check chain is list
        if "v10_audit_chain" in record:
            if not isinstance(record["v10_audit_chain"], list):
                warnings.append(
                    f"v10_audit_chain must be list, got {type(record['v10_audit_chain'])}"
                )

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty audit trail record with safe defaults.

        Returns:
            Empty audit trail record
        """
        return {
            "v10_audit_mode": "OFF",
            "v10_audit_status": "UNAVAILABLE",
            "v10_audit_chain": [],
            "v10_audit_summary": "audit trail unavailable.",
        }

    @staticmethod
    def create_chain_event(
        layer: str,
        artifact: str,
        basis: List[str],
    ) -> Dict[str, Any]:
        """
        Create chain event.

        Args:
            layer: Layer name
            artifact: Artifact identifier
            basis: Array of field names referenced

        Returns:
            Chain event dict
        """
        return {
            "layer": layer,
            "artifact": artifact,
            "basis": basis,
        }


def get_audit_trail_schema_info() -> Dict[str, Any]:
    """
    Get audit trail schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "execution_audit_trail",
        "required_fields": V10ExecutionAuditTrailSchema.REQUIRED_FIELDS,
        "valid_modes": V10ExecutionAuditTrailSchema.VALID_MODES,
        "valid_statuses": V10ExecutionAuditTrailSchema.VALID_STATUSES,
        "valid_layers": V10ExecutionAuditTrailSchema.VALID_LAYERS,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Execution Audit Trail Schema - Self Test")
    print("=" * 60)
    print()

    # Print schema info
    print("Schema Info:")
    print(json.dumps(get_audit_trail_schema_info(), indent=2))
    print()

    # Test empty record
    print("Empty Record:")
    empty = V10ExecutionAuditTrailSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Validate empty record
    print("Validation:")
    warnings = V10ExecutionAuditTrailSchema.validate_structure(empty)
    if warnings:
        print(f"✗ Warnings: {warnings}")
    else:
        print("✓ Empty record is valid")
    print()

    # Test chain event
    print("Chain Event:")
    event = V10ExecutionAuditTrailSchema.create_chain_event(
        "BLINDSPOT",
        "pr81_blindspot_record",
        ["v8_blindspot_tag"]
    )
    print(json.dumps(event, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
