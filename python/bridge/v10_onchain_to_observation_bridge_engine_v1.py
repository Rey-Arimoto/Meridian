#!/usr/bin/env python3
"""
PR108: v1.0 Onchain to Observation Bridge Engine v1 (READ-ONLY)

Purpose:
    Bridge onchain observations to normalized observations.
    Bridge = Structural Join + Normalization (not execution).

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Qualitative states only
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance/holdings/portfolio
    - Defensive: Never raises, returns ERROR state on failure

Bridge Philosophy:
    Bridge ≠ Execution
    Bridge = Structural Join

    Bridge converts onchain observations to normalized format:
    - CHAIN_STATE.gas_price_bucket → market_cost_regime
    - POOL_ACTIVITY.liquidity_state → liquidity_regime
    - EVENT_ACTIVITY.event_type_seen → event_activity_present
    - OBJECT_DYNAMICS.object_count_delta → object_dynamics

    Bridge does NOT:
    - Execute trades
    - Track asset balances
    - Provide recommendations
    - Enable ownership queries

Engine Design:
    - Input: v10_onchain_observation_record (PR107)
    - Output: v10_normalized_observation_record
    - Defensive (handles None/invalid gracefully)
    - Warning-only (never raises, always returns valid record)
"""

from typing import Any, Dict, Optional
from .v10_onchain_to_observation_bridge_schema import V10OnchainToObservationBridgeSchema


def bridge_onchain_observation_v1(
    onchain_obs_record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Bridge onchain observation to normalized observation.

    Args:
        onchain_obs_record: Onchain observation record from PR107

    Returns:
        Normalized observation record

    Design:
        - Defensive (None/invalid → ERROR record)
        - Warning-only (never raises)
        - Always returns valid normalized observation record
    """
    # Validate input
    if not isinstance(onchain_obs_record, dict):
        import time
        return V10OnchainToObservationBridgeSchema.create_error_record(
            network="unknown",
            timestamp=int(time.time()),
            error_info="invalid onchain observation record type",
        )

    # Extract common fields
    network = onchain_obs_record.get("v10_obs_network", "unknown")
    timestamp = onchain_obs_record.get("v10_obs_timestamp", 0)
    obs_status = onchain_obs_record.get("v10_obs_status", "UNAVAILABLE")
    obs_type = onchain_obs_record.get("v10_obs_type", "UNKNOWN")

    # Handle ERROR or UNAVAILABLE status
    if obs_status == "ERROR":
        error_info = onchain_obs_record.get("v10_obs_error_info", "unknown error")
        return V10OnchainToObservationBridgeSchema.create_error_record(
            network=network,
            timestamp=timestamp,
            error_info=f"onchain observation error: {error_info}",
        )

    if obs_status == "UNAVAILABLE":
        return V10OnchainToObservationBridgeSchema.create_error_record(
            network=network,
            timestamp=timestamp,
            error_info="onchain observation unavailable",
        )

    # Extract observation data
    obs_data = onchain_obs_record.get("v10_obs_data", {})
    if not isinstance(obs_data, dict):
        return V10OnchainToObservationBridgeSchema.create_error_record(
            network=network,
            timestamp=timestamp,
            error_info="invalid observation data format",
        )

    # Normalize based on observation type
    if obs_type == "CHAIN_STATE":
        return _normalize_chain_state(network, timestamp, obs_data)
    elif obs_type == "POOL_ACTIVITY":
        return _normalize_pool_activity(network, timestamp, obs_data)
    elif obs_type == "EVENT_ACTIVITY":
        return _normalize_event_activity(network, timestamp, obs_data)
    elif obs_type == "OBJECT_DYNAMICS":
        return _normalize_object_dynamics(network, timestamp, obs_data)
    else:
        return V10OnchainToObservationBridgeSchema.create_error_record(
            network=network,
            timestamp=timestamp,
            error_info=f"unknown observation type: {obs_type}",
        )


def _normalize_chain_state(
    network: str,
    timestamp: int,
    obs_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Normalize CHAIN_STATE observation.

    Normalization:
        gas_price_bucket (LOW/MEDIUM/HIGH) → market_cost_regime

    Args:
        network: Network name
        timestamp: Observation timestamp
        obs_data: Observation data

    Returns:
        Normalized observation record
    """
    gas_price_bucket = obs_data.get("gas_price_bucket", None)

    if gas_price_bucket not in ["LOW", "MEDIUM", "HIGH"]:
        return V10OnchainToObservationBridgeSchema.create_error_record(
            network=network,
            timestamp=timestamp,
            error_info=f"invalid gas_price_bucket: {gas_price_bucket}",
        )

    # Normalize: gas_price_bucket → market_cost_regime
    return V10OnchainToObservationBridgeSchema.create_normalized_record(
        network=network,
        timestamp=timestamp,
        market_cost_regime=gas_price_bucket,
    )


def _normalize_pool_activity(
    network: str,
    timestamp: int,
    obs_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Normalize POOL_ACTIVITY observation.

    Normalization:
        liquidity_state (LOW/MEDIUM/HIGH) → liquidity_regime
        activity_present (bool) → event_activity_present (TRUE/FALSE)

    Args:
        network: Network name
        timestamp: Observation timestamp
        obs_data: Observation data

    Returns:
        Normalized observation record
    """
    liquidity_state = obs_data.get("liquidity_state", None)
    activity_present = obs_data.get("activity_present", None)

    # Validate liquidity_state
    if liquidity_state not in ["LOW", "MEDIUM", "HIGH"]:
        return V10OnchainToObservationBridgeSchema.create_error_record(
            network=network,
            timestamp=timestamp,
            error_info=f"invalid liquidity_state: {liquidity_state}",
        )

    # Normalize activity_present to TRUE/FALSE string
    event_activity_str = "TRUE" if activity_present else "FALSE"

    # Normalize: liquidity_state → liquidity_regime, activity_present → event_activity_present
    return V10OnchainToObservationBridgeSchema.create_normalized_record(
        network=network,
        timestamp=timestamp,
        liquidity_regime=liquidity_state,
        event_activity_present=event_activity_str,
    )


def _normalize_event_activity(
    network: str,
    timestamp: int,
    obs_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Normalize EVENT_ACTIVITY observation.

    Normalization:
        event_type_seen (bool) → event_activity_present (TRUE/FALSE)

    Args:
        network: Network name
        timestamp: Observation timestamp
        obs_data: Observation data

    Returns:
        Normalized observation record
    """
    event_type_seen = obs_data.get("event_type_seen", None)

    # Normalize event_type_seen to TRUE/FALSE string
    event_activity_str = "TRUE" if event_type_seen else "FALSE"

    # Normalize: event_type_seen → event_activity_present
    return V10OnchainToObservationBridgeSchema.create_normalized_record(
        network=network,
        timestamp=timestamp,
        event_activity_present=event_activity_str,
    )


def _normalize_object_dynamics(
    network: str,
    timestamp: int,
    obs_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Normalize OBJECT_DYNAMICS observation.

    Normalization:
        object_count_delta (DECREASE/STABLE/INCREASE) → object_dynamics

    Args:
        network: Network name
        timestamp: Observation timestamp
        obs_data: Observation data

    Returns:
        Normalized observation record
    """
    object_count_delta = obs_data.get("object_count_delta", None)

    if object_count_delta not in ["DECREASE", "STABLE", "INCREASE"]:
        return V10OnchainToObservationBridgeSchema.create_error_record(
            network=network,
            timestamp=timestamp,
            error_info=f"invalid object_count_delta: {object_count_delta}",
        )

    # Normalize: object_count_delta → object_dynamics
    return V10OnchainToObservationBridgeSchema.create_normalized_record(
        network=network,
        timestamp=timestamp,
        object_dynamics=object_count_delta,
    )


def get_bridge_engine_v1_info() -> Dict[str, Any]:
    """
    Get bridge engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "onchain_to_observation_bridge",
        "supported_observations": [
            "CHAIN_STATE",
            "POOL_ACTIVITY",
            "EVENT_ACTIVITY",
            "OBJECT_DYNAMICS",
        ],
        "normalization_mappings": {
            "CHAIN_STATE": {
                "gas_price_bucket": "market_cost_regime",
            },
            "POOL_ACTIVITY": {
                "liquidity_state": "liquidity_regime",
                "activity_present": "event_activity_present",
            },
            "EVENT_ACTIVITY": {
                "event_type_seen": "event_activity_present",
            },
            "OBJECT_DYNAMICS": {
                "object_count_delta": "object_dynamics",
            },
        },
    }


if __name__ == "__main__":
    # Self-test
    import json
    import time

    print("=" * 60)
    print("v1.0 Onchain to Observation Bridge Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Bridge CHAIN_STATE
    print("Test 1: Bridge CHAIN_STATE")
    chain_state_obs = {
        "v10_obs_mode": "ON",
        "v10_obs_status": "AVAILABLE",
        "v10_obs_type": "CHAIN_STATE",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "testnet",
        "v10_obs_data": {
            "epoch": 100,
            "gas_price_bucket": "MEDIUM",
        },
    }
    normalized = bridge_onchain_observation_v1(chain_state_obs)
    print(json.dumps(normalized, indent=2))
    print()

    # Test 2: Bridge POOL_ACTIVITY
    print("Test 2: Bridge POOL_ACTIVITY")
    pool_activity_obs = {
        "v10_obs_mode": "ON",
        "v10_obs_status": "AVAILABLE",
        "v10_obs_type": "POOL_ACTIVITY",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "mainnet",
        "v10_obs_data": {
            "activity_present": True,
            "liquidity_state": "HIGH",
        },
    }
    normalized = bridge_onchain_observation_v1(pool_activity_obs)
    print(json.dumps(normalized, indent=2))
    print()

    # Test 3: Bridge EVENT_ACTIVITY
    print("Test 3: Bridge EVENT_ACTIVITY")
    event_activity_obs = {
        "v10_obs_mode": "ON",
        "v10_obs_status": "AVAILABLE",
        "v10_obs_type": "EVENT_ACTIVITY",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "devnet",
        "v10_obs_data": {
            "event_type_seen": True,
        },
    }
    normalized = bridge_onchain_observation_v1(event_activity_obs)
    print(json.dumps(normalized, indent=2))
    print()

    # Test 4: Bridge OBJECT_DYNAMICS
    print("Test 4: Bridge OBJECT_DYNAMICS")
    object_dynamics_obs = {
        "v10_obs_mode": "ON",
        "v10_obs_status": "AVAILABLE",
        "v10_obs_type": "OBJECT_DYNAMICS",
        "v10_obs_timestamp": int(time.time()),
        "v10_obs_network": "testnet",
        "v10_obs_data": {
            "object_count_delta": "INCREASE",
        },
    }
    normalized = bridge_onchain_observation_v1(object_dynamics_obs)
    print(json.dumps(normalized, indent=2))
    print()

    # Test 5: Error case (invalid type)
    print("Test 5: Error case (invalid type)")
    invalid_obs = "invalid"
    error_normalized = bridge_onchain_observation_v1(invalid_obs)  # type: ignore
    print(json.dumps(error_normalized, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
