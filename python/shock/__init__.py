#!/usr/bin/env python3
"""
PR149: v1.4 Shock Phase Detection Engine v1 (READ-ONLY)

Purpose:
    Detect shock phase from observation labels using fixed rules.
    Shock Phase = Structural phase label (not instruction, not prediction).

Exports:
    Schema:
    - V14ShockPhaseSchema: Shock phase schema class
    - get_shock_phase_schema_info: Schema metadata
    - Shock constants (SHOCK_STATUS_*, SHOCK_SOURCE_*, PHASE_*, DIRECTION_*)
    - Observation label constants (IMPULSE_*, ABSORPTION_*, FLOW_*, LIQUIDITY_*)

    Engine:
    - detect_shock_phase_from_bundle_v1: Detect shock phase from bundle
    - get_shock_phase_engine_v1_info: Engine metadata

    Constitutional Guard:
    - check_shock_record: Shock record guard
    - check_forbidden_vocabulary: Vocabulary guard
    - check_token_literals: Token literal guard
    - check_address_patterns: Address pattern guard
    - check_coupling_phrases: Coupling phrase guard
    - check_numeric_patterns: Numeric pattern guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

from .v14_shock_phase_schema import (
    V14ShockPhaseSchema,
    get_shock_phase_schema_info,
    SHOCK_VERSION_V1,
    SHOCK_STATUS_AVAILABLE,
    SHOCK_STATUS_UNKNOWN,
    SHOCK_STATUS_ERROR,
    SHOCK_SOURCE_AUTO,
    SHOCK_SOURCE_DEEP,
    SHOCK_SOURCE_CETUS,
    SHOCK_SOURCE_MIXED,
    SHOCK_SOURCE_UNKNOWN,
    PHASE_UNKNOWN,
    PHASE_NORMAL,
    PHASE_PRE_SHOCK,
    PHASE_UP_SHOCK,
    PHASE_DOWN_SHOCK,
    PHASE_UP_REVERSAL,
    PHASE_DOWN_REVERSAL,
    PHASE_RECOVERY,
    PHASE_ERROR,
    DIRECTION_UP,
    DIRECTION_DOWN,
    DIRECTION_NONE,
    DIRECTION_UNKNOWN,
    IMPULSE_UP,
    IMPULSE_DOWN,
    IMPULSE_FLAT,
    IMPULSE_UNKNOWN,
    ASK_ABSORPTION,
    BID_ABSORPTION,
    NO_ABSORPTION,
    ABSORPTION_UNKNOWN,
    AGG_BUY_DOMINANCE,
    AGG_SELL_DOMINANCE,
    FLOW_BALANCED,
    FLOW_UNKNOWN,
    LIQUIDITY_THINNING,
    LIQUIDITY_OK,
    LIQUIDITY_UNKNOWN,
)
from .v14_shock_phase_engine_v1 import (
    detect_shock_phase_from_bundle_v1,
    get_shock_phase_engine_v1_info,
)
from .v14_shock_constitutional_guard import (
    check_shock_record,
    check_forbidden_vocabulary,
    check_token_literals,
    check_address_patterns,
    check_coupling_phrases,
    check_numeric_patterns,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Schema
    "V14ShockPhaseSchema",
    "get_shock_phase_schema_info",
    "SHOCK_VERSION_V1",
    "SHOCK_STATUS_AVAILABLE",
    "SHOCK_STATUS_UNKNOWN",
    "SHOCK_STATUS_ERROR",
    "SHOCK_SOURCE_AUTO",
    "SHOCK_SOURCE_DEEP",
    "SHOCK_SOURCE_CETUS",
    "SHOCK_SOURCE_MIXED",
    "SHOCK_SOURCE_UNKNOWN",
    # Phase labels
    "PHASE_UNKNOWN",
    "PHASE_NORMAL",
    "PHASE_PRE_SHOCK",
    "PHASE_UP_SHOCK",
    "PHASE_DOWN_SHOCK",
    "PHASE_UP_REVERSAL",
    "PHASE_DOWN_REVERSAL",
    "PHASE_RECOVERY",
    "PHASE_ERROR",
    # Directions
    "DIRECTION_UP",
    "DIRECTION_DOWN",
    "DIRECTION_NONE",
    "DIRECTION_UNKNOWN",
    # Observation labels
    "IMPULSE_UP",
    "IMPULSE_DOWN",
    "IMPULSE_FLAT",
    "IMPULSE_UNKNOWN",
    "ASK_ABSORPTION",
    "BID_ABSORPTION",
    "NO_ABSORPTION",
    "ABSORPTION_UNKNOWN",
    "AGG_BUY_DOMINANCE",
    "AGG_SELL_DOMINANCE",
    "FLOW_BALANCED",
    "FLOW_UNKNOWN",
    "LIQUIDITY_THINNING",
    "LIQUIDITY_OK",
    "LIQUIDITY_UNKNOWN",
    # Engine
    "detect_shock_phase_from_bundle_v1",
    "get_shock_phase_engine_v1_info",
    # Constitutional Guard
    "check_shock_record",
    "check_forbidden_vocabulary",
    "check_token_literals",
    "check_address_patterns",
    "check_coupling_phrases",
    "check_numeric_patterns",
    "FORBIDDEN_VOCABULARY",
]
