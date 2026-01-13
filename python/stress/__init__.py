#!/usr/bin/env python3
"""
PR146: v1.4 Stress Rule Table v1 (READ-ONLY)

Purpose:
    Fixed table mapping (regime, band_bucket, distortion_presence) → stress_label.
    Stress = structural load state (not action, not instruction).

Exports:
    Schema:
    - V14StressRuleTableSchema: Stress schema class
    - get_stress_rule_table_schema_info: Schema metadata
    - Version/status/mode constants
    - Stress label constants (STRESS_*)
    - Band bucket constants (BAND_*)
    - Distortion presence constants (DIST_*)
    - Regime constants (REGIME_*)

    Rule Table:
    - RULE_TABLE_V1: Fixed mapping table
    - lookup_stress_label_v1: Table lookup function
    - get_stress_rule_table_v1_info: Table metadata

    Engine:
    - build_stress_label_from_inputs_v1: Build from direct inputs
    - build_stress_label_from_bundle_v1: Build from artifact bundle
    - get_stress_engine_v1_info: Engine metadata

    Constitutional Guard:
    - check_stress_record: Stress record guard
    - check_forbidden_vocabulary: Vocabulary guard
    - check_token_literals: Token literal guard
    - check_address_patterns: Address pattern guard
    - check_coupling_phrases: Coupling phrase guard
    - check_numeric_patterns: Numeric pattern guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

from .v14_stress_rule_table_schema import (
    V14StressRuleTableSchema,
    get_stress_rule_table_schema_info,
    STRESS_VERSION_V1,
    STRESS_STATUS_AVAILABLE,
    STRESS_STATUS_ERROR,
    STRESS_MODE_READ_ONLY,
    STRESS_CALM,
    STRESS_TENSE,
    STRESS_STRESSED,
    STRESS_UNKNOWN,
    BAND_SAFE,
    BAND_EDGE,
    BAND_OUTSIDE,
    BAND_UNKNOWN,
    DIST_NONE,
    DIST_PRESENT,
    DIST_UNKNOWN,
    REGIME_LOW,
    REGIME_MEDIUM,
    REGIME_HIGH,
    REGIME_CRITICAL,
    REGIME_UNKNOWN,
)
from .v14_stress_rule_table_v1 import (
    RULE_TABLE_V1,
    lookup_stress_label_v1,
    get_stress_rule_table_v1_info,
)
from .v14_stress_engine_v1 import (
    build_stress_label_from_inputs_v1,
    build_stress_label_from_bundle_v1,
    get_stress_engine_v1_info,
)
from .v14_stress_constitutional_guard import (
    check_stress_record,
    check_forbidden_vocabulary,
    check_token_literals,
    check_address_patterns,
    check_coupling_phrases,
    check_numeric_patterns,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Schema
    "V14StressRuleTableSchema",
    "get_stress_rule_table_schema_info",
    "STRESS_VERSION_V1",
    "STRESS_STATUS_AVAILABLE",
    "STRESS_STATUS_ERROR",
    "STRESS_MODE_READ_ONLY",
    # Stress labels
    "STRESS_CALM",
    "STRESS_TENSE",
    "STRESS_STRESSED",
    "STRESS_UNKNOWN",
    # Band buckets
    "BAND_SAFE",
    "BAND_EDGE",
    "BAND_OUTSIDE",
    "BAND_UNKNOWN",
    # Distortion presence
    "DIST_NONE",
    "DIST_PRESENT",
    "DIST_UNKNOWN",
    # Regimes
    "REGIME_LOW",
    "REGIME_MEDIUM",
    "REGIME_HIGH",
    "REGIME_CRITICAL",
    "REGIME_UNKNOWN",
    # Rule Table
    "RULE_TABLE_V1",
    "lookup_stress_label_v1",
    "get_stress_rule_table_v1_info",
    # Engine
    "build_stress_label_from_inputs_v1",
    "build_stress_label_from_bundle_v1",
    "get_stress_engine_v1_info",
    # Constitutional Guard
    "check_stress_record",
    "check_forbidden_vocabulary",
    "check_token_literals",
    "check_address_patterns",
    "check_coupling_phrases",
    "check_numeric_patterns",
    "FORBIDDEN_VOCABULARY",
]
