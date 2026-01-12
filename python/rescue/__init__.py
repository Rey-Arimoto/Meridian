#!/usr/bin/env python3
"""
PR133/PR136: v1.2 Role Rescue Relation & Rescue Strength (READ-ONLY)

Purpose:
    Classify ROLE→ROLE structural rescue relations and rescue strength.
    Rescue = Structural label propagation (not action, not recommendation).

Exports:
    PR133 - Role Rescue Relation:
    - V12RoleRescueRelationSchema: Rescue relation schema class
    - get_rescue_relation_schema_info: Schema metadata
    - Edge type constants: RESCUE_EDGE_BUFFER, RESCUE_EDGE_ANCHOR,
                          RESCUE_EDGE_CONTINUITY, RESCUE_EDGE_ESCAPE,
                          RESCUE_EDGE_DAMPEN, RESCUE_EDGE_UNCLASSIFIED
    - Strength constants (PR133): RESCUE_STRENGTH_NONE, RESCUE_STRENGTH_WEAK,
                         RESCUE_STRENGTH_MODERATE, RESCUE_STRENGTH_STRONG
    - Role constants: ROLE_GAS, ROLE_STABILITY, ROLE_LIQUIDITY,
                     ROLE_VOLATILITY, ROLE_HEDGE, ROLE_UNCLASSIFIED
    - classify_role_rescue_relation_v1: Rescue relation classification function
    - get_role_rescue_relation_engine_v1_info: Engine metadata

    PR136 - Rescue Strength:
    - V12RescueStrengthSchema: Rescue strength schema class
    - get_rescue_strength_schema_info: Schema metadata
    - Strength constants (PR136): RESCUE_NONE, RESCUE_WEAK, RESCUE_MEDIUM, RESCUE_STRONG
    - classify_rescue_strength_v1: Rescue strength classification function
    - get_rescue_strength_engine_v1_info: Engine metadata

    Guards:
    - check_rescue_relation_record: Constitutional guard (PR133)
    - check_rescue_strength_record: Constitutional guard (PR136)
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

# PR136: Rescue Strength
from .v12_rescue_strength_schema import (
    V12RescueStrengthSchema,
    get_rescue_strength_schema_info,
    RESCUE_NONE,
    RESCUE_WEAK,
    RESCUE_MEDIUM,
    RESCUE_STRONG,
    VALID_RESCUE_STRENGTHS,
)

from .v12_rescue_strength_engine_v1 import (
    classify_rescue_strength_v1,
    get_rescue_strength_engine_v1_info,
)

# Guards
from .v12_rescue_constitutional_guard import (
    check_rescue_strength_record,
    check_rescue_coupling,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # PR133: Role Rescue Relation Schema
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
    # PR133: Role Rescue Relation Engine
    "classify_role_rescue_relation_v1",
    "get_role_rescue_relation_engine_v1_info",
    # PR136: Rescue Strength Schema
    "V12RescueStrengthSchema",
    "get_rescue_strength_schema_info",
    "RESCUE_NONE",
    "RESCUE_WEAK",
    "RESCUE_MEDIUM",
    "RESCUE_STRONG",
    "VALID_RESCUE_STRENGTHS",
    # PR136: Rescue Strength Engine
    "classify_rescue_strength_v1",
    "get_rescue_strength_engine_v1_info",
    # Guards
    "check_rescue_strength_record",
    "check_rescue_coupling",
    "FORBIDDEN_VOCABULARY",
]
