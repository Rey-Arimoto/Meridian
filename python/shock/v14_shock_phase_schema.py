#!/usr/bin/env python3
"""
PR149: v1.4 Shock Phase Detection Schema (READ-ONLY)

Purpose:
    Define schema for shock phase detection records.
    Shock Phase = Structural phase label (not instruction, not prediction).
    Phase labels based on observation labels (not raw numeric values).

Record Prefix:
    v14_shock_

Required Fields:
    v14_shock_version: "v1"
    v14_shock_status: AVAILABLE | UNKNOWN | ERROR
    v14_shock_pair_ref: Pair reference (e.g., "deep:wBTC/USDC")
    v14_shock_source: AUTO | DEEP | CETUS | MIXED | UNKNOWN
    v14_shock_profile_ref: Observation profile reference
    v14_shock_phase_label: Phase label
    v14_shock_phase_direction: UP | DOWN | NONE | UNKNOWN
    v14_shock_basis_labels: List of basis labels
    v14_shock_observation_presence: Dict of observation presence flags
    v14_shock_warnings: List of warnings

Optional:
    v14_shock_notes: List of short notes

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Non-prescriptive: No should/must/recommend/advise
    - Label-only output: No numeric values in text
    - No token literals: No BTC/USDC/SUI/ETH in text
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/hence
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Shock version
SHOCK_VERSION_V1 = "v1"

# Shock status constants
SHOCK_STATUS_AVAILABLE = "AVAILABLE"
SHOCK_STATUS_UNKNOWN = "UNKNOWN"
SHOCK_STATUS_ERROR = "ERROR"

# Shock source constants
SHOCK_SOURCE_AUTO = "AUTO"
SHOCK_SOURCE_DEEP = "DEEP"
SHOCK_SOURCE_CETUS = "CETUS"
SHOCK_SOURCE_MIXED = "MIXED"
SHOCK_SOURCE_UNKNOWN = "UNKNOWN"

# Shock phase labels (fixed)
PHASE_UNKNOWN = "PHASE_UNKNOWN"
PHASE_NORMAL = "PHASE_NORMAL"
PHASE_PRE_SHOCK = "PHASE_PRE_SHOCK"
PHASE_UP_SHOCK = "PHASE_UP_SHOCK"
PHASE_DOWN_SHOCK = "PHASE_DOWN_SHOCK"
PHASE_UP_REVERSAL = "PHASE_UP_REVERSAL"
PHASE_DOWN_REVERSAL = "PHASE_DOWN_REVERSAL"
PHASE_RECOVERY = "PHASE_RECOVERY"
PHASE_ERROR = "PHASE_ERROR"

# Shock phase direction constants
DIRECTION_UP = "UP"
DIRECTION_DOWN = "DOWN"
DIRECTION_NONE = "NONE"
DIRECTION_UNKNOWN = "UNKNOWN"

# Observation label constants (for reference)
# price_impulse_label
IMPULSE_UP = "IMPULSE_UP"
IMPULSE_DOWN = "IMPULSE_DOWN"
IMPULSE_FLAT = "IMPULSE_FLAT"
IMPULSE_UNKNOWN = "IMPULSE_UNKNOWN"

# absorption_label
ASK_ABSORPTION = "ASK_ABSORPTION"
BID_ABSORPTION = "BID_ABSORPTION"
NO_ABSORPTION = "NO_ABSORPTION"
ABSORPTION_UNKNOWN = "ABSORPTION_UNKNOWN"

# flow_dominance_label
AGG_BUY_DOMINANCE = "AGG_BUY_DOMINANCE"
AGG_SELL_DOMINANCE = "AGG_SELL_DOMINANCE"
FLOW_BALANCED = "FLOW_BALANCED"
FLOW_UNKNOWN = "FLOW_UNKNOWN"

# liquidity_thinning_label
LIQUIDITY_THINNING = "LIQUIDITY_THINNING"
LIQUIDITY_OK = "LIQUIDITY_OK"
LIQUIDITY_UNKNOWN = "LIQUIDITY_UNKNOWN"


class V14ShockPhaseSchema:
    """Schema for shock phase detection records."""

    # Valid statuses
    VALID_STATUSES = [
        SHOCK_STATUS_AVAILABLE,
        SHOCK_STATUS_UNKNOWN,
        SHOCK_STATUS_ERROR,
    ]

    # Valid sources
    VALID_SOURCES = [
        SHOCK_SOURCE_AUTO,
        SHOCK_SOURCE_DEEP,
        SHOCK_SOURCE_CETUS,
        SHOCK_SOURCE_MIXED,
        SHOCK_SOURCE_UNKNOWN,
    ]

    # Valid phase labels
    VALID_PHASE_LABELS = [
        PHASE_UNKNOWN,
        PHASE_NORMAL,
        PHASE_PRE_SHOCK,
        PHASE_UP_SHOCK,
        PHASE_DOWN_SHOCK,
        PHASE_UP_REVERSAL,
        PHASE_DOWN_REVERSAL,
        PHASE_RECOVERY,
        PHASE_ERROR,
    ]

    # Valid directions
    VALID_DIRECTIONS = [
        DIRECTION_UP,
        DIRECTION_DOWN,
        DIRECTION_NONE,
        DIRECTION_UNKNOWN,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "v14_shock_version",
        "v14_shock_status",
        "v14_shock_pair_ref",
        "v14_shock_source",
        "v14_shock_profile_ref",
        "v14_shock_phase_label",
        "v14_shock_phase_direction",
        "v14_shock_basis_labels",
        "v14_shock_observation_presence",
        "v14_shock_warnings",
    ]

    @staticmethod
    def create_shock_record(
        version: str = SHOCK_VERSION_V1,
        status: str = SHOCK_STATUS_AVAILABLE,
        pair_ref: str = "",
        source: str = SHOCK_SOURCE_AUTO,
        profile_ref: str = "ALERT_ONLY",
        phase_label: str = PHASE_UNKNOWN,
        phase_direction: str = DIRECTION_UNKNOWN,
        basis_labels: Optional[List[str]] = None,
        observation_presence: Optional[Dict[str, bool]] = None,
        warnings: Optional[List[str]] = None,
        notes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create shock phase detection record.

        Args:
            version: Shock version (default "v1")
            status: AVAILABLE | UNKNOWN | ERROR
            pair_ref: Pair reference (e.g., "deep:wBTC/USDC")
            source: AUTO | DEEP | CETUS | MIXED | UNKNOWN
            profile_ref: Observation profile reference
            phase_label: Phase label
            phase_direction: UP | DOWN | NONE | UNKNOWN
            basis_labels: List of basis labels
            observation_presence: Dict of observation presence flags
            warnings: List of warnings
            notes: Optional notes

        Returns:
            Shock phase record
        """
        record = {
            "v14_shock_version": version,
            "v14_shock_status": status,
            "v14_shock_pair_ref": pair_ref,
            "v14_shock_source": source,
            "v14_shock_profile_ref": profile_ref,
            "v14_shock_phase_label": phase_label,
            "v14_shock_phase_direction": phase_direction,
            "v14_shock_basis_labels": basis_labels if basis_labels else [],
            "v14_shock_observation_presence": observation_presence if observation_presence else {},
            "v14_shock_warnings": warnings if warnings else [],
        }

        # Add optional fields if provided
        if notes is not None:
            record["v14_shock_notes"] = notes

        return record

    @staticmethod
    def create_error_record(
        pair_ref: str = "",
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create error record.

        Args:
            pair_ref: Pair reference
            warnings: List of warnings

        Returns:
            Error record
        """
        return V14ShockPhaseSchema.create_shock_record(
            status=SHOCK_STATUS_ERROR,
            pair_ref=pair_ref,
            phase_label=PHASE_ERROR,
            phase_direction=DIRECTION_UNKNOWN,
            basis_labels=[],
            observation_presence={},
            warnings=warnings if warnings else [],
        )

    @staticmethod
    def validate_shock_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate shock phase record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V14ShockPhaseSchema.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate version
        version = record.get("v14_shock_version")
        if version != SHOCK_VERSION_V1:
            errors.append(f"invalid version: {version} (expected {SHOCK_VERSION_V1})")

        # Validate status
        status = record.get("v14_shock_status")
        if status not in V14ShockPhaseSchema.VALID_STATUSES:
            errors.append(f"invalid status: {status}")

        # Validate source
        source = record.get("v14_shock_source")
        if source not in V14ShockPhaseSchema.VALID_SOURCES:
            errors.append(f"invalid source: {source}")

        # Validate phase_label
        phase_label = record.get("v14_shock_phase_label")
        if phase_label not in V14ShockPhaseSchema.VALID_PHASE_LABELS:
            errors.append(f"invalid phase_label: {phase_label}")

        # Validate phase_direction
        phase_direction = record.get("v14_shock_phase_direction")
        if phase_direction not in V14ShockPhaseSchema.VALID_DIRECTIONS:
            errors.append(f"invalid phase_direction: {phase_direction}")

        # Validate types
        if not isinstance(record.get("v14_shock_pair_ref"), str):
            errors.append("pair_ref must be string")

        if not isinstance(record.get("v14_shock_profile_ref"), str):
            errors.append("profile_ref must be string")

        if not isinstance(record.get("v14_shock_basis_labels"), list):
            errors.append("basis_labels must be list")

        if not isinstance(record.get("v14_shock_observation_presence"), dict):
            errors.append("observation_presence must be dict")

        if not isinstance(record.get("v14_shock_warnings"), list):
            errors.append("warnings must be list")

        return errors


def get_shock_phase_schema_info() -> Dict[str, Any]:
    """
    Get shock phase schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1",
        "schema_type": "shock_phase_detection",
        "record_prefix": "v14_shock_",
        "valid_statuses": V14ShockPhaseSchema.VALID_STATUSES,
        "valid_sources": V14ShockPhaseSchema.VALID_SOURCES,
        "valid_phase_labels": V14ShockPhaseSchema.VALID_PHASE_LABELS,
        "valid_directions": V14ShockPhaseSchema.VALID_DIRECTIONS,
        "philosophy": "Shock Phase = Structural phase label (not instruction, not prediction). Phase detection from observation labels.",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "label_output_only",
            "no_addresses",
            "no_causal_coupling",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Shock Phase Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create valid record
    print("Test 1: Create valid record")
    record1 = V14ShockPhaseSchema.create_shock_record(
        status=SHOCK_STATUS_AVAILABLE,
        pair_ref="deep:wBTC/USDC",
        source=SHOCK_SOURCE_DEEP,
        profile_ref="ALERT_ONLY",
        phase_label=PHASE_PRE_SHOCK,
        phase_direction=DIRECTION_NONE,
        basis_labels=["BASIS_LIQUIDITY_THINNING", "BASIS_IMPULSE_UP"],
        observation_presence={
            "price_impulse": True,
            "absorption": True,
            "flow_dominance": True,
            "liquidity_thinning": True,
        },
    )
    errors1 = V14ShockPhaseSchema.validate_shock_record(record1)
    print(f"Valid record errors: {len(errors1)}")
    if errors1:
        for e in errors1:
            print(f"  - {e}")
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    record2 = V14ShockPhaseSchema.create_error_record(
        pair_ref="deep:wBTC/USDC",
        warnings=["invalid observation bundle"],
    )
    errors2 = V14ShockPhaseSchema.validate_shock_record(record2)
    print(f"Error record status: {record2['v14_shock_status']}")
    print(f"Error record errors: {len(errors2)}")
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    info = get_shock_phase_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Phase labels: {len(info['valid_phase_labels'])}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
