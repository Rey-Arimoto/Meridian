#!/usr/bin/env python3
"""
PR133: v1.2 Role Rescue Relation (READ-ONLY)

Purpose:
    Classify ROLE→ROLE structural rescue relations as dependency edges.
    Rescue = Structural label propagation (not action, not recommendation).

Exports:
    Schema:
    - V12RoleRescueRelationSchema: Rescue relation schema class
    - get_rescue_relation_schema_info: Schema metadata
    - Edge type constants: RESCUE_EDGE_BUFFER, RESCUE_EDGE_ANCHOR,
                          RESCUE_EDGE_CONTINUITY, RESCUE_EDGE_ESCAPE,
                          RESCUE_EDGE_DAMPEN, RESCUE_EDGE_UNCLASSIFIED
    - Strength constants: RESCUE_STRENGTH_NONE, RESCUE_STRENGTH_WEAK,
                         RESCUE_STRENGTH_MODERATE, RESCUE_STRENGTH_STRONG
    - Role constants: ROLE_GAS, ROLE_STABILITY, ROLE_LIQUIDITY,
                     ROLE_VOLATILITY, ROLE_HEDGE, ROLE_UNCLASSIFIED

    Engine:
    - classify_role_rescue_relation_v1: Rescue relation classification function
    - get_role_rescue_relation_engine_v1_info: Engine metadata

    Guards:
    - check_rescue_relation_record: Constitutional guard
    - check_rescue_coupling: Rescue coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

# Schema
from .v12_role_rescue_relation_schema import (
    V12RoleRescueRelationSchema,
    get_rescue_relation_schema_info,
    RESCUE_EDGE_BUFFER,
    RESCUE_EDGE_ANCHOR,
    RESCUE_EDGE_CONTINUITY,
    RESCUE_EDGE_ESCAPE,
    RESCUE_EDGE_DAMPEN,
    RESCUE_EDGE_UNCLASSIFIED,
    VALID_EDGE_TYPES,
    RESCUE_STRENGTH_NONE,
    RESCUE_STRENGTH_WEAK,
    RESCUE_STRENGTH_MODERATE,
    RESCUE_STRENGTH_STRONG,
    VALID_STRENGTH_LEVELS,
    ROLE_GAS,
    ROLE_STABILITY,
    ROLE_LIQUIDITY,
    ROLE_VOLATILITY,
    ROLE_HEDGE,
    ROLE_UNCLASSIFIED,
    VALID_ROLES,
)

# Engine
from .v12_role_rescue_relation_engine_v1 import (
    classify_role_rescue_relation_v1,
    get_role_rescue_relation_engine_v1_info,
)

# Guards
from .v12_rescue_constitutional_guard import (
    check_rescue_relation_record,
    check_rescue_coupling,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Schema
    "V12RoleRescueRelationSchema",
    "get_rescue_relation_schema_info",
    "RESCUE_EDGE_BUFFER",
    "RESCUE_EDGE_ANCHOR",
    "RESCUE_EDGE_CONTINUITY",
    "RESCUE_EDGE_ESCAPE",
    "RESCUE_EDGE_DAMPEN",
    "RESCUE_EDGE_UNCLASSIFIED",
    "VALID_EDGE_TYPES",
    "RESCUE_STRENGTH_NONE",
    "RESCUE_STRENGTH_WEAK",
    "RESCUE_STRENGTH_MODERATE",
    "RESCUE_STRENGTH_STRONG",
    "VALID_STRENGTH_LEVELS",
    "ROLE_GAS",
    "ROLE_STABILITY",
    "ROLE_LIQUIDITY",
    "ROLE_VOLATILITY",
    "ROLE_HEDGE",
    "ROLE_UNCLASSIFIED",
    "VALID_ROLES",
    # Engine
    "classify_role_rescue_relation_v1",
    "get_role_rescue_relation_engine_v1_info",
    # Guards
    "check_rescue_relation_record",
    "check_rescue_coupling",
    "FORBIDDEN_VOCABULARY",
]
