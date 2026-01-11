#!/usr/bin/env python3
"""
PR110: v1.1 Entropy Regime Classification Schema (READ-ONLY)

Purpose:
    Schema for entropy regime classification records.
    Regime = State Classification (not action).

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Regime labels only (REGIME_LOW/MEDIUM/HIGH/CRITICAL)
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No execution vocabulary: No buy, sell, trade, swap
    - Non-evaluative: No good/bad vocabulary

Regime Philosophy:
    Regime ≠ Action
    Regime ≠ Recommendation
    Regime = State Label

    Regime classifies market state:
    - REGIME_LOW: Stable, predictable patterns
    - REGIME_MEDIUM: Moderate variation, typical conditions
    - REGIME_HIGH: Elevated variation, increased uncertainty
    - REGIME_CRITICAL: Extreme variation, observability breakdown

    Regime does NOT:
    - Recommend actions
    - Evaluate good/bad
    - Suggest positions
    - Optimize outcomes

Schema Design:
    - v11_regime_ prefix for regime fields
    - Regime levels: REGIME_LOW, REGIME_MEDIUM, REGIME_HIGH, REGIME_CRITICAL
    - Basis: list of analytics fields that informed regime
    - Summary: descriptive text (no evaluation)
"""

from typing import Any, Dict, List, Optional


class V11EntropyRegimeSchema:
    """
    Schema for v1.1 entropy regime classification records.

    Regime = State Classification (not action).
    """

    # Required fields for regime record
    REQUIRED_FIELDS = [
        "v11_regime_mode",           # Regime mode (ON/OFF)
        "v11_regime_status",         # Regime status (AVAILABLE/UNAVAILABLE/ERROR)
        "v11_regime_level",          # Regime level
        "v11_regime_basis",          # Basis (analytics fields that informed regime)
        "v11_regime_timestamp",      # Regime timestamp (epoch seconds)
        "v11_regime_summary",        # Summary of regime state
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v11_regime_error_info",     # Error information if status is ERROR
        "v11_regime_metadata",       # Additional metadata
    ]

    # Valid regime modes
    VALID_MODES = ["ON", "OFF"]

    # Valid regime statuses
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]

    # Valid regime levels
    VALID_REGIME_LEVELS = [
        "REGIME_LOW",        # Stable, predictable patterns
        "REGIME_MEDIUM",     # Moderate variation, typical conditions
        "REGIME_HIGH",       # Elevated variation, increased uncertainty
        "REGIME_CRITICAL",   # Extreme variation, observability breakdown
    ]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate regime record structure.

        Args:
            record: Regime record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V11EntropyRegimeSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v11_regime_mode" in record:
            mode = record["v11_regime_mode"]
            if mode not in V11EntropyRegimeSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v11_regime_mode: {mode}. "
                    f"Must be one of {V11EntropyRegimeSchema.VALID_MODES}"
                )

        # Validate status
        if "v11_regime_status" in record:
            status = record["v11_regime_status"]
            if status not in V11EntropyRegimeSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v11_regime_status: {status}. "
                    f"Must be one of {V11EntropyRegimeSchema.VALID_STATUSES}"
                )

        # Validate regime level
        if "v11_regime_level" in record:
            level = record["v11_regime_level"]
            if level not in V11EntropyRegimeSchema.VALID_REGIME_LEVELS:
                warnings.append(
                    f"Invalid v11_regime_level: {level}. "
                    f"Must be one of {V11EntropyRegimeSchema.VALID_REGIME_LEVELS}"
                )

        # Validate basis
        if "v11_regime_basis" in record:
            basis = record["v11_regime_basis"]
            if not isinstance(basis, list):
                warnings.append("v11_regime_basis must be a list")

        # Validate timestamp
        if "v11_regime_timestamp" in record:
            timestamp = record["v11_regime_timestamp"]
            if not isinstance(timestamp, int):
                warnings.append("v11_regime_timestamp must be an integer")
            elif timestamp < 0:
                warnings.append("v11_regime_timestamp must be non-negative")

        # Validate summary
        if "v11_regime_summary" in record:
            summary = record["v11_regime_summary"]
            if not isinstance(summary, str):
                warnings.append("v11_regime_summary must be a string")
            elif len(summary) == 0:
                warnings.append("v11_regime_summary must not be empty")

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty regime record with safe defaults.

        Returns:
            Empty regime record (unavailable state)
        """
        import time
        return {
            "v11_regime_mode": "OFF",
            "v11_regime_status": "UNAVAILABLE",
            "v11_regime_level": "REGIME_CRITICAL",
            "v11_regime_basis": [],
            "v11_regime_timestamp": int(time.time()),
            "v11_regime_summary": "regime classification unavailable. no analytics available.",
        }

    @staticmethod
    def create_regime_record(
        regime_level: str,
        basis: List[str],
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create regime classification record.

        Args:
            regime_level: Regime level (REGIME_LOW/MEDIUM/HIGH/CRITICAL)
            basis: List of analytics fields that informed regime
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Regime classification record
        """
        import time
        if timestamp is None:
            timestamp = int(time.time())

        # Generate summary based on regime level
        summaries = {
            "REGIME_LOW": "regime classified as low. stable patterns observed.",
            "REGIME_MEDIUM": "regime classified as medium. moderate variation observed.",
            "REGIME_HIGH": "regime classified as high. elevated variation observed.",
            "REGIME_CRITICAL": "regime classified as critical. extreme variation or observability breakdown.",
        }

        return {
            "v11_regime_mode": "ON",
            "v11_regime_status": "AVAILABLE",
            "v11_regime_level": regime_level,
            "v11_regime_basis": basis,
            "v11_regime_timestamp": timestamp,
            "v11_regime_summary": summaries.get(regime_level, "regime classified."),
        }

    @staticmethod
    def create_error_record(
        error_info: str,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create error regime record.

        Args:
            error_info: Error information
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Error regime record
        """
        import time
        if timestamp is None:
            timestamp = int(time.time())

        return {
            "v11_regime_mode": "ON",
            "v11_regime_status": "ERROR",
            "v11_regime_level": "REGIME_CRITICAL",
            "v11_regime_basis": [],
            "v11_regime_timestamp": timestamp,
            "v11_regime_error_info": error_info,
            "v11_regime_summary": "regime classification error. defaulting to critical regime.",
        }


def get_entropy_regime_schema_info() -> Dict[str, Any]:
    """
    Get entropy regime schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.1",
        "schema_type": "entropy_regime_classification",
        "required_fields": V11EntropyRegimeSchema.REQUIRED_FIELDS,
        "optional_fields": V11EntropyRegimeSchema.OPTIONAL_FIELDS,
        "valid_modes": V11EntropyRegimeSchema.VALID_MODES,
        "valid_statuses": V11EntropyRegimeSchema.VALID_STATUSES,
        "valid_regime_levels": V11EntropyRegimeSchema.VALID_REGIME_LEVELS,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Entropy Regime Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Empty record
    print("Test 1: Empty record")
    empty = V11EntropyRegimeSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    warnings = V11EntropyRegimeSchema.validate_structure(empty)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 2: REGIME_LOW
    print("Test 2: REGIME_LOW")
    regime_low = V11EntropyRegimeSchema.create_regime_record(
        regime_level="REGIME_LOW",
        basis=["market_cost_regime_counts", "liquidity_regime_presence"],
    )
    print(json.dumps(regime_low, indent=2))
    warnings = V11EntropyRegimeSchema.validate_structure(regime_low)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 3: REGIME_CRITICAL
    print("Test 3: REGIME_CRITICAL")
    regime_critical = V11EntropyRegimeSchema.create_regime_record(
        regime_level="REGIME_CRITICAL",
        basis=["observation_count", "event_activity_frequency"],
    )
    print(json.dumps(regime_critical, indent=2))
    warnings = V11EntropyRegimeSchema.validate_structure(regime_critical)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 4: Error record
    print("Test 4: Error record")
    error = V11EntropyRegimeSchema.create_error_record(
        error_info="analytics unavailable for regime classification",
    )
    print(json.dumps(error, indent=2))
    warnings = V11EntropyRegimeSchema.validate_structure(error)
    print(f"Validation warnings: {len(warnings)}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
