#!/usr/bin/env python3
"""
PR108: v1.0 Onchain to Observation Bridge Schema (READ-ONLY)

Purpose:
    Schema for normalized observation records.
    Bridge = Structural Join + Normalization (not execution).

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Qualitative states only (LOW/MEDIUM/HIGH)
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance/holdings/portfolio
    - Non-evaluative: No good/bad vocabulary

Bridge Philosophy:
    Bridge ≠ Execution
    Bridge = Structural Join

    Bridge normalizes onchain observations for interpretation:
    - CHAIN_STATE → market_cost_regime
    - POOL_ACTIVITY → liquidity_regime, event_activity_present
    - EVENT_ACTIVITY → event_activity_present
    - OBJECT_DYNAMICS → object_dynamics

    Bridge does NOT:
    - Trade or execute
    - Track asset balances
    - Provide recommendations
    - Enable ownership queries

Normalization Design:
    - v10_norm_obs_ prefix for normalized observation fields
    - Qualitative states (LOW/MEDIUM/HIGH, INCREASE/STABLE/DECREASE)
    - Boolean presence flags (TRUE/FALSE)
    - No numeric values exposed
"""

from typing import Any, Dict, List, Optional


class V10OnchainToObservationBridgeSchema:
    """
    Schema for v1.0 normalized observation records.

    Bridge = Structural Join (not execution).
    """

    # Required fields for normalized observation
    REQUIRED_FIELDS = [
        "v10_norm_obs_mode",           # Normalized observation mode (ON/OFF)
        "v10_norm_obs_status",         # Normalized observation status (AVAILABLE/UNAVAILABLE/ERROR)
        "v10_norm_obs_network",        # Network (mainnet/testnet/devnet/localnet)
        "v10_norm_obs_timestamp",      # Observation timestamp (epoch seconds)
        "v10_norm_obs_summary",        # Summary of normalized observation
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v10_norm_obs_market_cost_regime",     # Market cost regime (LOW/MEDIUM/HIGH)
        "v10_norm_obs_liquidity_regime",       # Liquidity regime (LOW/MEDIUM/HIGH)
        "v10_norm_obs_event_activity_present", # Event activity present (TRUE/FALSE)
        "v10_norm_obs_object_dynamics",        # Object dynamics (INCREASE/STABLE/DECREASE)
        "v10_norm_obs_error_info",             # Error information if status is ERROR
        "v10_norm_obs_metadata",               # Additional metadata
    ]

    # Valid normalized observation modes
    VALID_MODES = ["ON", "OFF"]

    # Valid normalized observation statuses
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]

    # Valid networks
    VALID_NETWORKS = ["mainnet", "testnet", "devnet", "localnet"]

    # Valid market cost regimes
    VALID_MARKET_COST_REGIMES = ["LOW", "MEDIUM", "HIGH"]

    # Valid liquidity regimes
    VALID_LIQUIDITY_REGIMES = ["LOW", "MEDIUM", "HIGH"]

    # Valid event activity states
    VALID_EVENT_ACTIVITY_STATES = ["TRUE", "FALSE"]

    # Valid object dynamics
    VALID_OBJECT_DYNAMICS = ["DECREASE", "STABLE", "INCREASE"]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate normalized observation record structure.

        Args:
            record: Normalized observation record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V10OnchainToObservationBridgeSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v10_norm_obs_mode" in record:
            mode = record["v10_norm_obs_mode"]
            if mode not in V10OnchainToObservationBridgeSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v10_norm_obs_mode: {mode}. "
                    f"Must be one of {V10OnchainToObservationBridgeSchema.VALID_MODES}"
                )

        # Validate status
        if "v10_norm_obs_status" in record:
            status = record["v10_norm_obs_status"]
            if status not in V10OnchainToObservationBridgeSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v10_norm_obs_status: {status}. "
                    f"Must be one of {V10OnchainToObservationBridgeSchema.VALID_STATUSES}"
                )

        # Validate network
        if "v10_norm_obs_network" in record:
            network = record["v10_norm_obs_network"]
            if network not in V10OnchainToObservationBridgeSchema.VALID_NETWORKS:
                warnings.append(
                    f"Invalid v10_norm_obs_network: {network}. "
                    f"Must be one of {V10OnchainToObservationBridgeSchema.VALID_NETWORKS}"
                )

        # Validate timestamp
        if "v10_norm_obs_timestamp" in record:
            timestamp = record["v10_norm_obs_timestamp"]
            if not isinstance(timestamp, int):
                warnings.append("v10_norm_obs_timestamp must be an integer")
            elif timestamp < 0:
                warnings.append("v10_norm_obs_timestamp must be non-negative")

        # Validate market cost regime
        if "v10_norm_obs_market_cost_regime" in record:
            regime = record["v10_norm_obs_market_cost_regime"]
            if regime not in V10OnchainToObservationBridgeSchema.VALID_MARKET_COST_REGIMES:
                warnings.append(
                    f"Invalid v10_norm_obs_market_cost_regime: {regime}. "
                    f"Must be one of {V10OnchainToObservationBridgeSchema.VALID_MARKET_COST_REGIMES}"
                )

        # Validate liquidity regime
        if "v10_norm_obs_liquidity_regime" in record:
            regime = record["v10_norm_obs_liquidity_regime"]
            if regime not in V10OnchainToObservationBridgeSchema.VALID_LIQUIDITY_REGIMES:
                warnings.append(
                    f"Invalid v10_norm_obs_liquidity_regime: {regime}. "
                    f"Must be one of {V10OnchainToObservationBridgeSchema.VALID_LIQUIDITY_REGIMES}"
                )

        # Validate event activity present
        if "v10_norm_obs_event_activity_present" in record:
            activity = record["v10_norm_obs_event_activity_present"]
            if activity not in V10OnchainToObservationBridgeSchema.VALID_EVENT_ACTIVITY_STATES:
                warnings.append(
                    f"Invalid v10_norm_obs_event_activity_present: {activity}. "
                    f"Must be one of {V10OnchainToObservationBridgeSchema.VALID_EVENT_ACTIVITY_STATES}"
                )

        # Validate object dynamics
        if "v10_norm_obs_object_dynamics" in record:
            dynamics = record["v10_norm_obs_object_dynamics"]
            if dynamics not in V10OnchainToObservationBridgeSchema.VALID_OBJECT_DYNAMICS:
                warnings.append(
                    f"Invalid v10_norm_obs_object_dynamics: {dynamics}. "
                    f"Must be one of {V10OnchainToObservationBridgeSchema.VALID_OBJECT_DYNAMICS}"
                )

        # Validate summary
        if "v10_norm_obs_summary" in record:
            summary = record["v10_norm_obs_summary"]
            if not isinstance(summary, str):
                warnings.append("v10_norm_obs_summary must be a string")
            elif len(summary) == 0:
                warnings.append("v10_norm_obs_summary must not be empty")

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty normalized observation record with safe defaults.

        Returns:
            Empty normalized observation record (unavailable state)
        """
        import time
        return {
            "v10_norm_obs_mode": "OFF",
            "v10_norm_obs_status": "UNAVAILABLE",
            "v10_norm_obs_network": "localnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_summary": "normalized observation not initialized. no onchain observation available.",
        }

    @staticmethod
    def create_normalized_record(
        network: str,
        timestamp: int,
        market_cost_regime: Optional[str] = None,
        liquidity_regime: Optional[str] = None,
        event_activity_present: Optional[str] = None,
        object_dynamics: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create normalized observation record.

        Args:
            network: Network name
            timestamp: Observation timestamp
            market_cost_regime: Optional market cost regime (LOW/MEDIUM/HIGH)
            liquidity_regime: Optional liquidity regime (LOW/MEDIUM/HIGH)
            event_activity_present: Optional event activity present (TRUE/FALSE)
            object_dynamics: Optional object dynamics (DECREASE/STABLE/INCREASE)

        Returns:
            Normalized observation record
        """
        record = {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": network,
            "v10_norm_obs_timestamp": timestamp,
            "v10_norm_obs_summary": "normalized observation available. structural facts captured.",
        }

        # Add optional fields if provided
        if market_cost_regime is not None:
            record["v10_norm_obs_market_cost_regime"] = market_cost_regime

        if liquidity_regime is not None:
            record["v10_norm_obs_liquidity_regime"] = liquidity_regime

        if event_activity_present is not None:
            record["v10_norm_obs_event_activity_present"] = event_activity_present

        if object_dynamics is not None:
            record["v10_norm_obs_object_dynamics"] = object_dynamics

        return record

    @staticmethod
    def create_error_record(
        network: str,
        timestamp: int,
        error_info: str,
    ) -> Dict[str, Any]:
        """
        Create error normalized observation record.

        Args:
            network: Network name
            timestamp: Observation timestamp
            error_info: Error information

        Returns:
            Error normalized observation record
        """
        return {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "ERROR",
            "v10_norm_obs_network": network,
            "v10_norm_obs_timestamp": timestamp,
            "v10_norm_obs_error_info": error_info,
            "v10_norm_obs_summary": f"normalized observation error on {network}. check error info for details.",
        }


def get_bridge_schema_info() -> Dict[str, Any]:
    """
    Get bridge schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "onchain_to_observation_bridge",
        "required_fields": V10OnchainToObservationBridgeSchema.REQUIRED_FIELDS,
        "optional_fields": V10OnchainToObservationBridgeSchema.OPTIONAL_FIELDS,
        "valid_modes": V10OnchainToObservationBridgeSchema.VALID_MODES,
        "valid_statuses": V10OnchainToObservationBridgeSchema.VALID_STATUSES,
        "valid_networks": V10OnchainToObservationBridgeSchema.VALID_NETWORKS,
        "valid_market_cost_regimes": V10OnchainToObservationBridgeSchema.VALID_MARKET_COST_REGIMES,
        "valid_liquidity_regimes": V10OnchainToObservationBridgeSchema.VALID_LIQUIDITY_REGIMES,
        "valid_event_activity_states": V10OnchainToObservationBridgeSchema.VALID_EVENT_ACTIVITY_STATES,
        "valid_object_dynamics": V10OnchainToObservationBridgeSchema.VALID_OBJECT_DYNAMICS,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Onchain to Observation Bridge Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Empty record
    print("Test 1: Empty record")
    empty = V10OnchainToObservationBridgeSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    warnings = V10OnchainToObservationBridgeSchema.validate_structure(empty)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 2: Normalized record (market cost regime)
    print("Test 2: Normalized record (market cost regime)")
    import time
    normalized = V10OnchainToObservationBridgeSchema.create_normalized_record(
        network="testnet",
        timestamp=int(time.time()),
        market_cost_regime="MEDIUM",
    )
    print(json.dumps(normalized, indent=2))
    warnings = V10OnchainToObservationBridgeSchema.validate_structure(normalized)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 3: Normalized record (full)
    print("Test 3: Normalized record (full)")
    normalized_full = V10OnchainToObservationBridgeSchema.create_normalized_record(
        network="mainnet",
        timestamp=int(time.time()),
        market_cost_regime="HIGH",
        liquidity_regime="MEDIUM",
        event_activity_present="TRUE",
        object_dynamics="INCREASE",
    )
    print(json.dumps(normalized_full, indent=2))
    warnings = V10OnchainToObservationBridgeSchema.validate_structure(normalized_full)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 4: Error record
    print("Test 4: Error record")
    error = V10OnchainToObservationBridgeSchema.create_error_record(
        network="devnet",
        timestamp=int(time.time()),
        error_info="bridge normalization failed. invalid observation type.",
    )
    print(json.dumps(error, indent=2))
    warnings = V10OnchainToObservationBridgeSchema.validate_structure(error)
    print(f"Validation warnings: {len(warnings)}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
