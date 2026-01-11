#!/usr/bin/env python3
"""
PR112: v1.1 Execution Preview Schema (READ-ONLY)

Purpose:
    Schema for execution preview records.
    Preview = Impact Shape Description (not simulation/execution).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No amounts: Impact types only (INCREASE/DECREASE/NONE)
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No asset vocabulary: No balance, holdings, portfolio
    - No action vocabulary: No recommend, suggest, optimize
    - Non-evaluative: No good/bad, profitable/unprofitable vocabulary

Preview Philosophy:
    Preview ≠ Simulation ≠ Execution
    Preview = Impact Shape Description

    Preview describes:
    - Exposure change type (INCREASE/DECREASE/NONE)
    - Interaction type (POOL_TOUCH/EVENT_INTERACTION/NONE)
    - Risk surface (LOW/MEDIUM/HIGH based on regime)
    - Structural impact summary

    Preview does NOT:
    - Recommend actions
    - Optimize outcomes
    - Execute trades
    - Evaluate profitability
    - Provide numeric outcomes

Schema Design:
    - v11_preview_ prefix for preview fields
    - Exposure types: NONE, INCREASE, DECREASE
    - Interaction types: NONE, POOL_TOUCH, EVENT_INTERACTION
    - Risk surface: LOW, MEDIUM, HIGH
    - Status: AVAILABLE, BLOCKED, ERROR
"""

from typing import Any, Dict, List, Optional


class V11ExecutionPreviewSchema:
    """
    Schema for v1.1 execution preview records.

    Preview = Impact Shape Description (not action).
    """

    # Required fields for preview record
    REQUIRED_FIELDS = [
        "v11_preview_mode",                 # Preview mode (ON/OFF)
        "v11_preview_status",               # Preview status (AVAILABLE/BLOCKED/ERROR)
        "v11_preview_exposure_change",      # Exposure change type
        "v11_preview_interaction_type",     # Interaction type
        "v11_preview_risk_surface",         # Risk surface level
        "v11_preview_summary",              # Summary of preview
        "v11_preview_basis",                # Basis (upstream fields used)
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v11_preview_error_info",           # Error information if status is ERROR
        "v11_preview_block_reason",         # Block reason if status is BLOCKED
        "v11_preview_metadata",             # Additional metadata
    ]

    # Valid preview modes
    VALID_MODES = ["ON", "OFF"]

    # Valid preview statuses
    VALID_STATUSES = ["AVAILABLE", "BLOCKED", "ERROR"]

    # Valid exposure change types
    VALID_EXPOSURE_CHANGES = [
        "NONE",         # No exposure change (NOOP, MAINTENANCE)
        "INCREASE",     # Exposure increase (LIQUIDITY, some REBALANCE)
        "DECREASE",     # Exposure decrease (HEDGE, some REBALANCE)
    ]

    # Valid interaction types
    VALID_INTERACTION_TYPES = [
        "NONE",                 # No interaction (NOOP, MAINTENANCE)
        "POOL_TOUCH",          # Pool interaction (REBALANCE, HEDGE, LIQUIDITY)
        "EVENT_INTERACTION",   # Event-based interaction (reserved for future)
    ]

    # Valid risk surface levels
    VALID_RISK_SURFACES = [
        "LOW",      # Low risk (REGIME_LOW)
        "MEDIUM",   # Medium risk (REGIME_MEDIUM)
        "HIGH",     # High risk (REGIME_HIGH, REGIME_CRITICAL)
    ]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate preview record structure.

        Args:
            record: Preview record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V11ExecutionPreviewSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v11_preview_mode" in record:
            mode = record["v11_preview_mode"]
            if mode not in V11ExecutionPreviewSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v11_preview_mode: {mode}. "
                    f"Must be one of {V11ExecutionPreviewSchema.VALID_MODES}"
                )

        # Validate status
        if "v11_preview_status" in record:
            status = record["v11_preview_status"]
            if status not in V11ExecutionPreviewSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v11_preview_status: {status}. "
                    f"Must be one of {V11ExecutionPreviewSchema.VALID_STATUSES}"
                )

        # Validate exposure change
        if "v11_preview_exposure_change" in record:
            exposure = record["v11_preview_exposure_change"]
            if exposure not in V11ExecutionPreviewSchema.VALID_EXPOSURE_CHANGES:
                warnings.append(
                    f"Invalid v11_preview_exposure_change: {exposure}. "
                    f"Must be one of {V11ExecutionPreviewSchema.VALID_EXPOSURE_CHANGES}"
                )

        # Validate interaction type
        if "v11_preview_interaction_type" in record:
            interaction = record["v11_preview_interaction_type"]
            if interaction not in V11ExecutionPreviewSchema.VALID_INTERACTION_TYPES:
                warnings.append(
                    f"Invalid v11_preview_interaction_type: {interaction}. "
                    f"Must be one of {V11ExecutionPreviewSchema.VALID_INTERACTION_TYPES}"
                )

        # Validate risk surface
        if "v11_preview_risk_surface" in record:
            risk = record["v11_preview_risk_surface"]
            if risk not in V11ExecutionPreviewSchema.VALID_RISK_SURFACES:
                warnings.append(
                    f"Invalid v11_preview_risk_surface: {risk}. "
                    f"Must be one of {V11ExecutionPreviewSchema.VALID_RISK_SURFACES}"
                )

        # Validate basis
        if "v11_preview_basis" in record:
            basis = record["v11_preview_basis"]
            if not isinstance(basis, list):
                warnings.append("v11_preview_basis must be a list")

        # Validate summary
        if "v11_preview_summary" in record:
            summary = record["v11_preview_summary"]
            if not isinstance(summary, str):
                warnings.append("v11_preview_summary must be a string")
            elif len(summary) == 0:
                warnings.append("v11_preview_summary must not be empty")

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty preview record with safe defaults.

        Returns:
            Empty preview record (unavailable state)
        """
        return {
            "v11_preview_mode": "OFF",
            "v11_preview_status": "ERROR",
            "v11_preview_exposure_change": "NONE",
            "v11_preview_interaction_type": "NONE",
            "v11_preview_risk_surface": "HIGH",
            "v11_preview_summary": "preview unavailable. no execution plan available.",
            "v11_preview_basis": [],
        }

    @staticmethod
    def create_preview_record(
        exposure_change: str,
        interaction_type: str,
        risk_surface: str,
        summary: str,
        basis: List[str],
    ) -> Dict[str, Any]:
        """
        Create preview record.

        Args:
            exposure_change: Exposure change type (NONE/INCREASE/DECREASE)
            interaction_type: Interaction type (NONE/POOL_TOUCH/EVENT_INTERACTION)
            risk_surface: Risk surface level (LOW/MEDIUM/HIGH)
            summary: Human-readable summary
            basis: List of upstream fields that informed preview

        Returns:
            Preview record
        """
        return {
            "v11_preview_mode": "ON",
            "v11_preview_status": "AVAILABLE",
            "v11_preview_exposure_change": exposure_change,
            "v11_preview_interaction_type": interaction_type,
            "v11_preview_risk_surface": risk_surface,
            "v11_preview_summary": summary,
            "v11_preview_basis": basis,
        }

    @staticmethod
    def create_blocked_record(
        block_reason: str,
        basis: List[str],
    ) -> Dict[str, Any]:
        """
        Create blocked preview record.

        Args:
            block_reason: Reason for blocking
            basis: List of upstream fields that informed decision

        Returns:
            Blocked preview record
        """
        return {
            "v11_preview_mode": "ON",
            "v11_preview_status": "BLOCKED",
            "v11_preview_exposure_change": "NONE",
            "v11_preview_interaction_type": "NONE",
            "v11_preview_risk_surface": "HIGH",
            "v11_preview_block_reason": block_reason,
            "v11_preview_summary": f"preview blocked. {block_reason}",
            "v11_preview_basis": basis,
        }

    @staticmethod
    def create_error_record(
        error_info: str,
    ) -> Dict[str, Any]:
        """
        Create error preview record.

        Args:
            error_info: Error information

        Returns:
            Error preview record
        """
        return {
            "v11_preview_mode": "ON",
            "v11_preview_status": "ERROR",
            "v11_preview_exposure_change": "NONE",
            "v11_preview_interaction_type": "NONE",
            "v11_preview_risk_surface": "HIGH",
            "v11_preview_error_info": error_info,
            "v11_preview_summary": "preview error. defaulting to safe state.",
            "v11_preview_basis": [],
        }


def get_execution_preview_schema_info() -> Dict[str, Any]:
    """
    Get execution preview schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.1",
        "schema_type": "execution_preview",
        "required_fields": V11ExecutionPreviewSchema.REQUIRED_FIELDS,
        "optional_fields": V11ExecutionPreviewSchema.OPTIONAL_FIELDS,
        "valid_modes": V11ExecutionPreviewSchema.VALID_MODES,
        "valid_statuses": V11ExecutionPreviewSchema.VALID_STATUSES,
        "valid_exposure_changes": V11ExecutionPreviewSchema.VALID_EXPOSURE_CHANGES,
        "valid_interaction_types": V11ExecutionPreviewSchema.VALID_INTERACTION_TYPES,
        "valid_risk_surfaces": V11ExecutionPreviewSchema.VALID_RISK_SURFACES,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Execution Preview Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Empty record
    print("Test 1: Empty record")
    empty = V11ExecutionPreviewSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    warnings = V11ExecutionPreviewSchema.validate_structure(empty)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 2: AVAILABLE preview
    print("Test 2: AVAILABLE preview (DECREASE exposure)")
    available_preview = V11ExecutionPreviewSchema.create_preview_record(
        exposure_change="DECREASE",
        interaction_type="POOL_TOUCH",
        risk_surface="HIGH",
        summary="hedge-type plan would reduce exposure with pool interaction under elevated market regime.",
        basis=["v10_plan_type", "v11_regime_level"],
    )
    print(json.dumps(available_preview, indent=2))
    warnings = V11ExecutionPreviewSchema.validate_structure(available_preview)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 3: BLOCKED preview
    print("Test 3: BLOCKED preview (REGIME_CRITICAL)")
    blocked_preview = V11ExecutionPreviewSchema.create_blocked_record(
        block_reason="regime critical observed. execution halted.",
        basis=["v11_regime_level", "v11_policy_permission"],
    )
    print(json.dumps(blocked_preview, indent=2))
    warnings = V11ExecutionPreviewSchema.validate_structure(blocked_preview)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 4: ERROR preview
    print("Test 4: ERROR preview")
    error_preview = V11ExecutionPreviewSchema.create_error_record(
        error_info="invalid plan record type",
    )
    print(json.dumps(error_preview, indent=2))
    warnings = V11ExecutionPreviewSchema.validate_structure(error_preview)
    print(f"Validation warnings: {len(warnings)}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
