#!/usr/bin/env python3
"""
PR147: v1.4 Action Shape Guidance v1 (READ-ONLY)

Purpose:
    Build action shape guidance from artifact bundle.
    Bundles PR144/PR145/PR146/PR128 and returns label-only action shape.
    Action Shape = Display shape (not instruction, not recommendation).

Exports:
    Schema:
    - V14ActionShapeSchema: Action shape schema class
    - get_action_shape_schema_info: Schema metadata
    - Version/status/mode constants
    - Action shape constants (ACTION_SHAPE_*)
    - Action scope constants (ACTION_SCOPE_*)

    Engine:
    - build_action_shape_from_bundle_v1: Build from artifact bundle
    - get_action_shape_engine_v1_info: Engine metadata

    Constitutional Guard:
    - check_action_record: Action record guard
    - check_forbidden_vocabulary: Vocabulary guard
    - check_token_literals: Token literal guard
    - check_address_patterns: Address pattern guard
    - check_coupling_phrases: Coupling phrase guard (includes action coupling)
    - check_numeric_patterns: Numeric pattern guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

from .v14_action_shape_schema import (
    V14ActionShapeSchema,
    get_action_shape_schema_info,
    ACTION_VERSION_V1,
    ACTION_STATUS_AVAILABLE,
    ACTION_STATUS_ERROR,
    ACTION_MODE_READ_ONLY,
    ACTION_SHAPE_UNKNOWN,
    ACTION_SHAPE_NO_ACTION,
    ACTION_SHAPE_OBSERVE_ONLY,
    ACTION_SHAPE_SIMULATION_ONLY,
    ACTION_SHAPE_CONSIDER_ONLY,
    ACTION_SHAPE_CONSTRAINED_STATE,
    ACTION_SHAPE_FREEZE_STATE,
    ACTION_SCOPE_GLOBAL,
    ACTION_SCOPE_VOLATILITY_ROLE_ONLY,
    ACTION_SCOPE_LIQUIDITY_ROLE_ONLY,
    ACTION_SCOPE_STABILITY_ROLE_ONLY,
    ACTION_SCOPE_HEDGE_ROLE_ONLY,
    ACTION_SCOPE_GAS_ROLE_ONLY,
)
from .v14_action_shape_engine_v1 import (
    build_action_shape_from_bundle_v1,
    get_action_shape_engine_v1_info,
)
from .v14_action_constitutional_guard import (
    check_action_record,
    check_forbidden_vocabulary,
    check_token_literals,
    check_address_patterns,
    check_coupling_phrases,
    check_numeric_patterns,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Schema
    "V14ActionShapeSchema",
    "get_action_shape_schema_info",
    "ACTION_VERSION_V1",
    "ACTION_STATUS_AVAILABLE",
    "ACTION_STATUS_ERROR",
    "ACTION_MODE_READ_ONLY",
    # Action shapes
    "ACTION_SHAPE_UNKNOWN",
    "ACTION_SHAPE_NO_ACTION",
    "ACTION_SHAPE_OBSERVE_ONLY",
    "ACTION_SHAPE_SIMULATION_ONLY",
    "ACTION_SHAPE_CONSIDER_ONLY",
    "ACTION_SHAPE_CONSTRAINED_STATE",
    "ACTION_SHAPE_FREEZE_STATE",
    # Action scopes
    "ACTION_SCOPE_GLOBAL",
    "ACTION_SCOPE_VOLATILITY_ROLE_ONLY",
    "ACTION_SCOPE_LIQUIDITY_ROLE_ONLY",
    "ACTION_SCOPE_STABILITY_ROLE_ONLY",
    "ACTION_SCOPE_HEDGE_ROLE_ONLY",
    "ACTION_SCOPE_GAS_ROLE_ONLY",
    # Engine
    "build_action_shape_from_bundle_v1",
    "get_action_shape_engine_v1_info",
    # Constitutional Guard
    "check_action_record",
    "check_forbidden_vocabulary",
    "check_token_literals",
    "check_address_patterns",
    "check_coupling_phrases",
    "check_numeric_patterns",
    "FORBIDDEN_VOCABULARY",
]
