"""
v1.0 Onchain to Observation Bridge Layer

This package contains schemas, bridge engine, and constitutional guards
for bridging onchain observations to normalized observations.

Bridge = Structural Join + Normalization (not execution).

Bridge Definition:
    Bridge normalizes onchain observations for interpretation.

    Bridge converts:
    - CHAIN_STATE → market_cost_regime
    - POOL_ACTIVITY → liquidity_regime, event_activity_present
    - EVENT_ACTIVITY → event_activity_present
    - OBJECT_DYNAMICS → object_dynamics

    Bridge does NOT:
    - Execute trades
    - Track asset balances
    - Provide recommendations
    - Enable ownership queries

Modules:
    - v10_onchain_to_observation_bridge_schema: Schema for normalized observations
    - v10_onchain_to_observation_bridge_engine_v1: Bridge engine v1
    - v10_bridge_constitutional_guard: Constitutional guards for bridge
"""

from .v10_onchain_to_observation_bridge_schema import (
    V10OnchainToObservationBridgeSchema,
    get_bridge_schema_info,
)

from .v10_onchain_to_observation_bridge_engine_v1 import (
    bridge_onchain_observation_v1,
    get_bridge_engine_v1_info,
)

from .v10_bridge_constitutional_guard import (
    check_asset_vocabulary,
    check_execution_vocabulary_bridge,
    validate_normalized_observation_record,
)

__all__ = [
    # Bridge Schema
    "V10OnchainToObservationBridgeSchema",
    "get_bridge_schema_info",
    # Bridge Engine
    "bridge_onchain_observation_v1",
    "get_bridge_engine_v1_info",
    # Constitutional Guards
    "check_asset_vocabulary",
    "check_execution_vocabulary_bridge",
    "validate_normalized_observation_record",
]
