#!/usr/bin/env python3
"""
PR131: v1.2 Role × Distortion × Regime Contribution Model v1 (READ-ONLY)

Purpose:
    Classify structural return contribution from regime × role × distortion combinations.
    Contribution = Where returns can exist as structural side-effect (not performance claim).

Exports:
    Schema:
    - V12ContributionSchema: Contribution schema class
    - get_contribution_schema_info: Schema metadata
    - Contribution label constants: CONTRIB_STRONGLY_POSITIVE, CONTRIB_POSITIVE,
                                   CONTRIB_NEUTRAL, CONTRIB_NEGATIVE,
                                   CONTRIB_STRONGLY_NEGATIVE, CONTRIB_UNKNOWN
    - Rationale constants: RATIONALE_*

    Engine:
    - classify_contribution_v1: Contribution classification function
    - build_contribution_cube_v1: Generate all combinations
    - contribution_to_explain_signals_v1: Map to explanation signals
    - get_contribution_engine_v1_info: Engine metadata

    Guards:
    - check_contribution_record: Constitutional guard
    - check_contribution_numeric_patterns: Numeric pattern guard
    - check_guarantee_language: Guarantee language guard
    - check_contribution_coupling: Contribution coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
    - GUARANTEE_VOCABULARY: Guarantee vocabulary list
"""

# Schema
from .v12_contribution_schema import (
    V12ContributionSchema,
    get_contribution_schema_info,
    CONTRIB_STRONGLY_POSITIVE,
    CONTRIB_POSITIVE,
    CONTRIB_NEUTRAL,
    CONTRIB_NEGATIVE,
    CONTRIB_STRONGLY_NEGATIVE,
    CONTRIB_UNKNOWN,
    VALID_CONTRIBUTION_LABELS,
    RATIONALE_DISTORTION_CAPTURE_ZONE,
    RATIONALE_STRUCTURE_INTELLIGIBLE,
    RATIONALE_FORCED_FLOW_PRESENT,
    RATIONALE_LIQUIDITY_PREMIUM_ZONE,
    RATIONALE_STRUCTURE_BREAKDOWN_RISK,
    RATIONALE_NON_ACTION_PRESERVES_OPTIONALITY,
    RATIONALE_ELEVATED_UNCERTAINTY,
    RATIONALE_CAPITAL_PRESERVATION_PRIORITY,
    RATIONALE_LOW_DISTORTION_DENSITY,
    RATIONALE_OPPORTUNITY_THIN,
    RATIONALE_STABILITY_BUFFER_ROLE,
    RATIONALE_HEDGE_ALIGNMENT_ZONE,
    RATIONALE_OPERATIONAL_ENABLER_ONLY,
    RATIONALE_INELIGIBLE_TOUCHABILITY,
)

# Engine
from .v12_role_distortion_regime_contribution_engine_v1 import (
    classify_contribution_v1,
    build_contribution_cube_v1,
    contribution_to_explain_signals_v1,
    get_contribution_engine_v1_info,
)

# Guards
from .v12_contribution_constitutional_guard import (
    check_contribution_record,
    check_contribution_numeric_patterns,
    check_guarantee_language,
    check_contribution_coupling,
    FORBIDDEN_VOCABULARY,
    GUARANTEE_VOCABULARY,
)

__all__ = [
    # Schema
    "V12ContributionSchema",
    "get_contribution_schema_info",
    "CONTRIB_STRONGLY_POSITIVE",
    "CONTRIB_POSITIVE",
    "CONTRIB_NEUTRAL",
    "CONTRIB_NEGATIVE",
    "CONTRIB_STRONGLY_NEGATIVE",
    "CONTRIB_UNKNOWN",
    "VALID_CONTRIBUTION_LABELS",
    "RATIONALE_DISTORTION_CAPTURE_ZONE",
    "RATIONALE_STRUCTURE_INTELLIGIBLE",
    "RATIONALE_FORCED_FLOW_PRESENT",
    "RATIONALE_LIQUIDITY_PREMIUM_ZONE",
    "RATIONALE_STRUCTURE_BREAKDOWN_RISK",
    "RATIONALE_NON_ACTION_PRESERVES_OPTIONALITY",
    "RATIONALE_ELEVATED_UNCERTAINTY",
    "RATIONALE_CAPITAL_PRESERVATION_PRIORITY",
    "RATIONALE_LOW_DISTORTION_DENSITY",
    "RATIONALE_OPPORTUNITY_THIN",
    "RATIONALE_STABILITY_BUFFER_ROLE",
    "RATIONALE_HEDGE_ALIGNMENT_ZONE",
    "RATIONALE_OPERATIONAL_ENABLER_ONLY",
    "RATIONALE_INELIGIBLE_TOUCHABILITY",
    # Engine
    "classify_contribution_v1",
    "build_contribution_cube_v1",
    "contribution_to_explain_signals_v1",
    "get_contribution_engine_v1_info",
    # Guards
    "check_contribution_record",
    "check_contribution_numeric_patterns",
    "check_guarantee_language",
    "check_contribution_coupling",
    "FORBIDDEN_VOCABULARY",
    "GUARANTEE_VOCABULARY",
]
