#!/usr/bin/env python3
"""
PR120: v1.0 Market Structure Drift Schema v1 (READ-ONLY)

Purpose:
    Define schema for market structure drift records.
    Drift = Language Shift (not profit/loss, not prediction).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No numeric amounts: No drift scores, percentages, counts
    - Drift = structural description (not evaluation/action)

Drift Philosophy:
    Drift ≠ Evaluation
    Drift ≠ Recommendation
    Drift = Structural Language Shift

    Drift provides:
    - Qualitative drift classification
    - Evidence terms (names only, no counts)
    - Structural change detection
    - Safe signal for downstream

    Drift does NOT:
    - Expose raw numbers
    - Contain token names
    - Contain addresses
    - Recommend actions
    - Evaluate quality/profit

Drift Fields:
    - v10_drift_mode: ON/OFF
    - v10_drift_status: AVAILABLE/ERROR
    - v10_drift_level: DRIFT_NONE/DRIFT_LOW/DRIFT_MEDIUM/DRIFT_HIGH/DRIFT_CRITICAL/UNCLASSIFIED
    - v10_drift_summary: non-evaluative summary string
    - v10_drift_basis: list of field names used (structural)
    - v10_drift_evidence: list[str] of vocabulary term deltas (term names only)
    - v10_drift_warnings: optional list of warning strings
    - v10_drift_error_info: optional error description (if status=ERROR)

Drift Levels:
    - DRIFT_NONE: No structural change detected
    - DRIFT_LOW: Minor structural changes (small delta)
    - DRIFT_MEDIUM: Moderate structural changes (moderate delta)
    - DRIFT_HIGH: Significant structural changes (large delta)
    - DRIFT_CRITICAL: Critical structural changes (very large delta)
    - UNCLASSIFIED: Cannot classify (insufficient data, invalid input)
"""

from typing import Any, Dict, List, Optional


class V10MarketStructureDriftSchema:
    """Market structure drift schema v1.0"""

    # Valid modes
    VALID_MODES = ["ON", "OFF"]

    # Valid statuses
    VALID_STATUSES = ["AVAILABLE", "ERROR"]

    # Valid drift levels
    VALID_DRIFT_LEVELS = [
        "DRIFT_NONE",
        "DRIFT_LOW",
        "DRIFT_MEDIUM",
        "DRIFT_HIGH",
        "DRIFT_CRITICAL",
        "UNCLASSIFIED",
    ]

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty drift record.

        Returns:
            Empty drift record
        """
        return {
            "v10_drift_mode": "ON",
            "v10_drift_status": "AVAILABLE",
            "v10_drift_level": "UNCLASSIFIED",
            "v10_drift_summary": "empty market structure drift record. no classification available.",
            "v10_drift_basis": [],
            "v10_drift_evidence": [],
        }

    @staticmethod
    def create_error_record(
        error_info: str = "unknown error",
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an error drift record.

        Args:
            error_info: Error description
            warnings: Optional list of warnings

        Returns:
            Error drift record
        """
        record = {
            "v10_drift_mode": "ON",
            "v10_drift_status": "ERROR",
            "v10_drift_level": "UNCLASSIFIED",
            "v10_drift_summary": f"market structure drift error. {error_info}",
            "v10_drift_basis": [],
            "v10_drift_evidence": [],
            "v10_drift_error_info": error_info,
        }

        if warnings:
            record["v10_drift_warnings"] = warnings

        return record

    @staticmethod
    def create_drift_record(
        drift_level: str,
        summary: str,
        basis: List[str],
        evidence: List[str],
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a drift record.

        Args:
            drift_level: Drift classification level
            summary: Non-evaluative summary
            basis: List of field names used
            evidence: List of vocabulary term deltas (term names only)
            warnings: Optional list of warnings

        Returns:
            Drift record
        """
        record = {
            "v10_drift_mode": "ON",
            "v10_drift_status": "AVAILABLE",
            "v10_drift_level": drift_level,
            "v10_drift_summary": summary,
            "v10_drift_basis": basis,
            "v10_drift_evidence": evidence,
        }

        if warnings:
            record["v10_drift_warnings"] = warnings

        return record

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate drift record structure.

        Args:
            record: Drift record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        required_fields = [
            "v10_drift_mode",
            "v10_drift_status",
            "v10_drift_level",
            "v10_drift_summary",
            "v10_drift_basis",
            "v10_drift_evidence",
        ]

        for field in required_fields:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v10_drift_mode" in record:
            if record["v10_drift_mode"] not in V10MarketStructureDriftSchema.VALID_MODES:
                warnings.append(f"Invalid drift mode: {record['v10_drift_mode']}")

        # Validate status
        if "v10_drift_status" in record:
            if (
                record["v10_drift_status"]
                not in V10MarketStructureDriftSchema.VALID_STATUSES
            ):
                warnings.append(f"Invalid drift status: {record['v10_drift_status']}")

        # Validate drift level
        if "v10_drift_level" in record:
            if (
                record["v10_drift_level"]
                not in V10MarketStructureDriftSchema.VALID_DRIFT_LEVELS
            ):
                warnings.append(f"Invalid drift level: {record['v10_drift_level']}")

        # Validate evidence
        if "v10_drift_evidence" in record:
            if not isinstance(record["v10_drift_evidence"], list):
                warnings.append("Drift evidence must be a list")
            else:
                for evidence_item in record["v10_drift_evidence"]:
                    if not isinstance(evidence_item, str):
                        warnings.append(
                            f"Drift evidence item must be string: {evidence_item}"
                        )

        # Validate basis
        if "v10_drift_basis" in record:
            if not isinstance(record["v10_drift_basis"], list):
                warnings.append("Drift basis must be a list")

        return warnings


def get_drift_schema_info() -> Dict[str, Any]:
    """
    Get drift schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "market_structure_drift",
        "valid_modes": V10MarketStructureDriftSchema.VALID_MODES,
        "valid_statuses": V10MarketStructureDriftSchema.VALID_STATUSES,
        "valid_drift_levels": V10MarketStructureDriftSchema.VALID_DRIFT_LEVELS,
        "drift_level_meanings": {
            "DRIFT_NONE": "No structural change detected",
            "DRIFT_LOW": "Minor structural changes (small delta)",
            "DRIFT_MEDIUM": "Moderate structural changes (moderate delta)",
            "DRIFT_HIGH": "Significant structural changes (large delta)",
            "DRIFT_CRITICAL": "Critical structural changes (very large delta)",
            "UNCLASSIFIED": "Cannot classify (insufficient data)",
        },
        "required_fields": [
            "v10_drift_mode",
            "v10_drift_status",
            "v10_drift_level",
            "v10_drift_summary",
            "v10_drift_basis",
            "v10_drift_evidence",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Market Structure Drift Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V10MarketStructureDriftSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Validate empty record
    print("Test 2: Validate empty record")
    warnings = V10MarketStructureDriftSchema.validate_structure(empty)
    print(f"Warnings: {warnings}")
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V10MarketStructureDriftSchema.create_error_record(
        error_info="test error",
        warnings=["test warning"],
    )
    print(json.dumps(error, indent=2))
    print()

    # Test 4: Create drift record
    print("Test 4: Create drift record")
    drift = V10MarketStructureDriftSchema.create_drift_record(
        drift_level="DRIFT_MEDIUM",
        summary="market structure drift detected. moderate structural changes in vocabulary.",
        basis=["vocab_window_A", "vocab_window_B"],
        evidence=["COST_HIGH_PRESENT_ADDED", "EVENT_ACTIVITY_ABSENT_REMOVED"],
    )
    print(json.dumps(drift, indent=2))
    print()

    # Test 5: Validate drift record
    print("Test 5: Validate drift record")
    warnings = V10MarketStructureDriftSchema.validate_structure(drift)
    print(f"Warnings: {warnings}")
    print()

    # Test 6: Validate invalid drift level
    print("Test 6: Validate invalid drift level")
    invalid_drift = V10MarketStructureDriftSchema.create_drift_record(
        drift_level="INVALID_LEVEL",
        summary="test",
        basis=[],
        evidence=[],
    )
    warnings = V10MarketStructureDriftSchema.validate_structure(invalid_drift)
    print(f"Warnings: {warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
