#!/usr/bin/env python3
"""
PR107: v1.0 Sui Onchain Observation Schema (READ-ONLY)

Purpose:
    Schema for onchain observation records.
    Observation = Structural Facts (not asset knowledge).

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Numeric values bucketed (LOW/MEDIUM/HIGH)
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - Non-evaluative: No good/bad vocabulary

Observation Philosophy:
    Observation ≠ Asset Knowledge
    Observation = Structure Ingestion

    Observation provides:
    - Chain state structure (epoch, reference_gas_price bucket)
    - Pool activity patterns (activity_present, liquidity_state)
    - Event activity patterns (event_type_seen)
    - Object dynamics patterns (object_count_delta)

    Observation does NOT provide:
    - Token balances
    - Wallet addresses
    - Trade recommendations
    - Asset ownership

Schema Design:
    - v10_obs_ prefix for observation fields
    - Observation types: CHAIN_STATE, POOL_ACTIVITY, EVENT_ACTIVITY, OBJECT_DYNAMICS
    - Numeric bucketing (no raw values)
    - Qualitative states (LOW/MEDIUM/HIGH, INCREASE/DECREASE/STABLE)
"""

from typing import Any, Dict, List, Optional


class V10SuiOnchainObservationSchema:
    """
    Schema for v1.0 Sui onchain observation records.

    Observation = Structural Facts (not asset knowledge).
    """

    # Required fields for observation record
    REQUIRED_FIELDS = [
        "v10_obs_mode",           # Observation mode (ON/OFF)
        "v10_obs_status",         # Observation status (AVAILABLE/UNAVAILABLE/ERROR)
        "v10_obs_type",           # Observation type
        "v10_obs_timestamp",      # Observation timestamp (epoch seconds)
        "v10_obs_network",        # Network (mainnet/testnet/devnet/localnet)
        "v10_obs_summary",        # Summary of observation
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v10_obs_data",           # Observation data (type-specific)
        "v10_obs_error_info",     # Error information if status is ERROR
        "v10_obs_metadata",       # Additional metadata
    ]

    # Valid observation modes
    VALID_MODES = ["ON", "OFF"]

    # Valid observation statuses
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]

    # Valid observation types
    VALID_TYPES = [
        "CHAIN_STATE",        # Chain state observation
        "POOL_ACTIVITY",      # Pool activity observation
        "EVENT_ACTIVITY",     # Event activity observation
        "OBJECT_DYNAMICS",    # Object dynamics observation
    ]

    # Valid networks
    VALID_NETWORKS = ["mainnet", "testnet", "devnet", "localnet"]

    # Valid liquidity states (bucketed)
    VALID_LIQUIDITY_STATES = ["LOW", "MEDIUM", "HIGH"]

    # Valid object count deltas (bucketed)
    VALID_OBJECT_COUNT_DELTAS = ["DECREASE", "STABLE", "INCREASE"]

    # Valid gas price buckets
    VALID_GAS_PRICE_BUCKETS = ["LOW", "MEDIUM", "HIGH"]

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate observation record structure.

        Args:
            record: Observation record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V10SuiOnchainObservationSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v10_obs_mode" in record:
            mode = record["v10_obs_mode"]
            if mode not in V10SuiOnchainObservationSchema.VALID_MODES:
                warnings.append(
                    f"Invalid v10_obs_mode: {mode}. "
                    f"Must be one of {V10SuiOnchainObservationSchema.VALID_MODES}"
                )

        # Validate status
        if "v10_obs_status" in record:
            status = record["v10_obs_status"]
            if status not in V10SuiOnchainObservationSchema.VALID_STATUSES:
                warnings.append(
                    f"Invalid v10_obs_status: {status}. "
                    f"Must be one of {V10SuiOnchainObservationSchema.VALID_STATUSES}"
                )

        # Validate type
        if "v10_obs_type" in record:
            obs_type = record["v10_obs_type"]
            if obs_type not in V10SuiOnchainObservationSchema.VALID_TYPES:
                warnings.append(
                    f"Invalid v10_obs_type: {obs_type}. "
                    f"Must be one of {V10SuiOnchainObservationSchema.VALID_TYPES}"
                )

        # Validate network
        if "v10_obs_network" in record:
            network = record["v10_obs_network"]
            if network not in V10SuiOnchainObservationSchema.VALID_NETWORKS:
                warnings.append(
                    f"Invalid v10_obs_network: {network}. "
                    f"Must be one of {V10SuiOnchainObservationSchema.VALID_NETWORKS}"
                )

        # Validate timestamp
        if "v10_obs_timestamp" in record:
            timestamp = record["v10_obs_timestamp"]
            if not isinstance(timestamp, int):
                warnings.append("v10_obs_timestamp must be an integer")
            elif timestamp < 0:
                warnings.append("v10_obs_timestamp must be non-negative")

        # Validate summary
        if "v10_obs_summary" in record:
            summary = record["v10_obs_summary"]
            if not isinstance(summary, str):
                warnings.append("v10_obs_summary must be a string")
            elif len(summary) == 0:
                warnings.append("v10_obs_summary must not be empty")

        # Validate observation data (type-specific)
        if "v10_obs_data" in record:
            obs_data = record["v10_obs_data"]
            if not isinstance(obs_data, dict):
                warnings.append("v10_obs_data must be a dict")

        return warnings

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create empty observation record with safe defaults.

        Returns:
            Empty observation record (unavailable state)
        """
        import time
        return {
            "v10_obs_mode": "OFF",
            "v10_obs_status": "UNAVAILABLE",
            "v10_obs_type": "CHAIN_STATE",
            "v10_obs_timestamp": int(time.time()),
            "v10_obs_network": "localnet",
            "v10_obs_summary": "observation not initialized. no connection available.",
        }

    @staticmethod
    def create_chain_state_record(
        network: str,
        epoch: int,
        gas_price_bucket: str,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create chain state observation record.

        Args:
            network: Network name
            epoch: Current epoch number
            gas_price_bucket: Gas price bucket (LOW/MEDIUM/HIGH)
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Chain state observation record
        """
        import time
        if timestamp is None:
            timestamp = int(time.time())

        return {
            "v10_obs_mode": "ON",
            "v10_obs_status": "AVAILABLE",
            "v10_obs_type": "CHAIN_STATE",
            "v10_obs_timestamp": timestamp,
            "v10_obs_network": network,
            "v10_obs_data": {
                "epoch": epoch,
                "gas_price_bucket": gas_price_bucket,
            },
            "v10_obs_summary": f"chain state observed on {network}. epoch and gas price bucket captured.",
        }

    @staticmethod
    def create_pool_activity_record(
        network: str,
        activity_present: bool,
        liquidity_state: str,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create pool activity observation record.

        Args:
            network: Network name
            activity_present: Whether activity is present
            liquidity_state: Liquidity state (LOW/MEDIUM/HIGH)
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Pool activity observation record
        """
        import time
        if timestamp is None:
            timestamp = int(time.time())

        return {
            "v10_obs_mode": "ON",
            "v10_obs_status": "AVAILABLE",
            "v10_obs_type": "POOL_ACTIVITY",
            "v10_obs_timestamp": timestamp,
            "v10_obs_network": network,
            "v10_obs_data": {
                "activity_present": activity_present,
                "liquidity_state": liquidity_state,
            },
            "v10_obs_summary": f"pool activity observed on {network}. activity and liquidity state captured.",
        }

    @staticmethod
    def create_event_activity_record(
        network: str,
        event_type_seen: bool,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create event activity observation record.

        Args:
            network: Network name
            event_type_seen: Whether event type was seen
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Event activity observation record
        """
        import time
        if timestamp is None:
            timestamp = int(time.time())

        return {
            "v10_obs_mode": "ON",
            "v10_obs_status": "AVAILABLE",
            "v10_obs_type": "EVENT_ACTIVITY",
            "v10_obs_timestamp": timestamp,
            "v10_obs_network": network,
            "v10_obs_data": {
                "event_type_seen": event_type_seen,
            },
            "v10_obs_summary": f"event activity observed on {network}. event type presence captured.",
        }

    @staticmethod
    def create_object_dynamics_record(
        network: str,
        object_count_delta: str,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create object dynamics observation record.

        Args:
            network: Network name
            object_count_delta: Object count delta (DECREASE/STABLE/INCREASE)
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Object dynamics observation record
        """
        import time
        if timestamp is None:
            timestamp = int(time.time())

        return {
            "v10_obs_mode": "ON",
            "v10_obs_status": "AVAILABLE",
            "v10_obs_type": "OBJECT_DYNAMICS",
            "v10_obs_timestamp": timestamp,
            "v10_obs_network": network,
            "v10_obs_data": {
                "object_count_delta": object_count_delta,
            },
            "v10_obs_summary": f"object dynamics observed on {network}. object count delta captured.",
        }

    @staticmethod
    def create_error_record(
        obs_type: str,
        network: str,
        error_info: str,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create error observation record.

        Args:
            obs_type: Observation type
            network: Network name
            error_info: Error information
            timestamp: Optional timestamp (defaults to current time)

        Returns:
            Error observation record
        """
        import time
        if timestamp is None:
            timestamp = int(time.time())

        return {
            "v10_obs_mode": "ON",
            "v10_obs_status": "ERROR",
            "v10_obs_type": obs_type,
            "v10_obs_timestamp": timestamp,
            "v10_obs_network": network,
            "v10_obs_error_info": error_info,
            "v10_obs_summary": f"observation error on {network}. check error info for details.",
        }


def get_onchain_observation_schema_info() -> Dict[str, Any]:
    """
    Get onchain observation schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "sui_onchain_observation",
        "required_fields": V10SuiOnchainObservationSchema.REQUIRED_FIELDS,
        "optional_fields": V10SuiOnchainObservationSchema.OPTIONAL_FIELDS,
        "valid_modes": V10SuiOnchainObservationSchema.VALID_MODES,
        "valid_statuses": V10SuiOnchainObservationSchema.VALID_STATUSES,
        "valid_types": V10SuiOnchainObservationSchema.VALID_TYPES,
        "valid_networks": V10SuiOnchainObservationSchema.VALID_NETWORKS,
        "valid_liquidity_states": V10SuiOnchainObservationSchema.VALID_LIQUIDITY_STATES,
        "valid_object_count_deltas": V10SuiOnchainObservationSchema.VALID_OBJECT_COUNT_DELTAS,
        "valid_gas_price_buckets": V10SuiOnchainObservationSchema.VALID_GAS_PRICE_BUCKETS,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Sui Onchain Observation Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Empty record
    print("Test 1: Empty record")
    empty = V10SuiOnchainObservationSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    warnings = V10SuiOnchainObservationSchema.validate_structure(empty)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 2: Chain state record
    print("Test 2: Chain state record")
    chain_state = V10SuiOnchainObservationSchema.create_chain_state_record(
        network="testnet",
        epoch=100,
        gas_price_bucket="MEDIUM",
    )
    print(json.dumps(chain_state, indent=2))
    warnings = V10SuiOnchainObservationSchema.validate_structure(chain_state)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 3: Pool activity record
    print("Test 3: Pool activity record")
    pool_activity = V10SuiOnchainObservationSchema.create_pool_activity_record(
        network="mainnet",
        activity_present=True,
        liquidity_state="HIGH",
    )
    print(json.dumps(pool_activity, indent=2))
    warnings = V10SuiOnchainObservationSchema.validate_structure(pool_activity)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 4: Event activity record
    print("Test 4: Event activity record")
    event_activity = V10SuiOnchainObservationSchema.create_event_activity_record(
        network="devnet",
        event_type_seen=True,
    )
    print(json.dumps(event_activity, indent=2))
    warnings = V10SuiOnchainObservationSchema.validate_structure(event_activity)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 5: Object dynamics record
    print("Test 5: Object dynamics record")
    object_dynamics = V10SuiOnchainObservationSchema.create_object_dynamics_record(
        network="testnet",
        object_count_delta="INCREASE",
    )
    print(json.dumps(object_dynamics, indent=2))
    warnings = V10SuiOnchainObservationSchema.validate_structure(object_dynamics)
    print(f"Validation warnings: {len(warnings)}")
    print()

    # Test 6: Error record
    print("Test 6: Error record")
    error = V10SuiOnchainObservationSchema.create_error_record(
        obs_type="CHAIN_STATE",
        network="mainnet",
        error_info="connection timeout during fetch",
    )
    print(json.dumps(error, indent=2))
    warnings = V10SuiOnchainObservationSchema.validate_structure(error)
    print(f"Validation warnings: {len(warnings)}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
