#!/usr/bin/env python3
"""
PR132: v1.2 Contribution → Constraint Binding v1 (READ-ONLY)

Purpose:
    Bind contribution model (PR131) to existing pipeline as non-prescriptive constraint labels.
    Binding = Label propagation (not evaluation, not decision, not instruction).

Exports:
    Schema:
    - V12ContributionConstraintSchema: Constraint binding schema class
    - get_contribution_constraint_schema_info: Schema metadata
    - Zone label constants: CONTRIB_ZONE_NONE, CONTRIB_ZONE_SECONDARY,
                           CONTRIB_ZONE_PRIMARY, CONTRIB_ZONE_BLOCKED
    - Constraint label constants: CONSTRAINT_CONTRIB_*

    Engine:
    - bind_contribution_constraints_v1: Constraint binding function
    - get_contribution_binding_engine_v1_info: Engine metadata

    Guards:
    - check_contribution_binding_record: Constitutional guard
    - check_contribution_zone_coupling: Zone coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

# Schema
from .v12_contribution_constraint_schema import (
    V12ContributionConstraintSchema,
    get_contribution_constraint_schema_info,
    CONTRIB_ZONE_NONE,
    CONTRIB_ZONE_SECONDARY,
    CONTRIB_ZONE_PRIMARY,
    CONTRIB_ZONE_BLOCKED,
    VALID_ZONE_LABELS,
    CONSTRAINT_CONTRIB_BLOCKED_REGIME_CRITICAL,
    CONSTRAINT_CONTRIB_BLOCKED_INELIGIBLE,
    CONSTRAINT_CONTRIB_BLOCKED_SUPPRESSED,
    CONSTRAINT_CONTRIB_SECONDARY_REGIME_NON_MEDIUM,
    CONSTRAINT_CONTRIB_PRIMARY_MEDIUM_VOLATILITY_DISTORTION,
    CONSTRAINT_CONTRIB_NONE_DEFAULT,
)

# Engine
from .v12_contribution_constraint_binding_engine_v1 import (
    bind_contribution_constraints_v1,
    get_contribution_binding_engine_v1_info,
)

# Guards
from .v12_contribution_binding_constitutional_guard import (
    check_contribution_binding_record,
    check_contribution_zone_coupling,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Schema
    "V12ContributionConstraintSchema",
    "get_contribution_constraint_schema_info",
    "CONTRIB_ZONE_NONE",
    "CONTRIB_ZONE_SECONDARY",
    "CONTRIB_ZONE_PRIMARY",
    "CONTRIB_ZONE_BLOCKED",
    "VALID_ZONE_LABELS",
    "CONSTRAINT_CONTRIB_BLOCKED_REGIME_CRITICAL",
    "CONSTRAINT_CONTRIB_BLOCKED_INELIGIBLE",
    "CONSTRAINT_CONTRIB_BLOCKED_SUPPRESSED",
    "CONSTRAINT_CONTRIB_SECONDARY_REGIME_NON_MEDIUM",
    "CONSTRAINT_CONTRIB_PRIMARY_MEDIUM_VOLATILITY_DISTORTION",
    "CONSTRAINT_CONTRIB_NONE_DEFAULT",
    # Engine
    "bind_contribution_constraints_v1",
    "get_contribution_binding_engine_v1_info",
    # Guards
    "check_contribution_binding_record",
    "check_contribution_zone_coupling",
    "FORBIDDEN_VOCABULARY",
]
