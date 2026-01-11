"""
v1.0 Sui Onchain Observation Layer

This package contains schemas, fetch engine, and constitutional guards for Sui onchain observations.

Observation = Structural Facts (not asset knowledge).

Observation Definition:
    Observation ingests onchain state as structural facts.

    Observation provides:
    - Chain state structure (epoch, reference_gas_price bucket)
    - Pool activity patterns (activity_present, liquidity_state)
    - Event activity patterns (event_type_seen)
    - Object dynamics patterns (object_count_delta)

    Observation does NOT:
    - Track token balances
    - Store wallet addresses
    - Provide trade recommendations
    - Execute transactions

Modules:
    - v10_sui_onchain_observation_schema: Schema for observation records
    - v10_sui_readonly_fetch_engine_v1: Fetch engine for onchain observations
    - v10_observation_constitutional_guard: Constitutional guards for observations
"""

from .v10_sui_onchain_observation_schema import (
    V10SuiOnchainObservationSchema,
    get_onchain_observation_schema_info,
)

from .v10_sui_readonly_fetch_engine_v1 import (
    fetch_chain_state_observation,
    fetch_pool_activity_observation,
    fetch_event_activity_observation,
    fetch_object_dynamics_observation,
    bucket_gas_price,
    bucket_liquidity,
    bucket_object_count_delta,
    get_fetch_engine_v1_info,
)

from .v10_observation_constitutional_guard import (
    check_observation_token_literals,
    check_observation_numeric_patterns,
    check_rpc_execution_vocabulary,
    validate_observation_record,
)

__all__ = [
    # Observation Schema
    "V10SuiOnchainObservationSchema",
    "get_onchain_observation_schema_info",
    # Fetch Engine
    "fetch_chain_state_observation",
    "fetch_pool_activity_observation",
    "fetch_event_activity_observation",
    "fetch_object_dynamics_observation",
    "bucket_gas_price",
    "bucket_liquidity",
    "bucket_object_count_delta",
    "get_fetch_engine_v1_info",
    # Constitutional Guards
    "check_observation_token_literals",
    "check_observation_numeric_patterns",
    "check_rpc_execution_vocabulary",
    "validate_observation_record",
]
