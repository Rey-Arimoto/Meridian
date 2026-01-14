#!/usr/bin/env python3
"""
PR150: v1.4 Stress Escalation Binding Package (READ-ONLY)

Purpose:
    Export schema class, engine functions, guards, and constants for stress escalation binding.

Exports:
    Schema:
        - V14StressEscalationSchema
        - ESCALATION_VERSION_V1
        - ESCALATION_STATUS_AVAILABLE
        - ESCALATION_STATUS_UNKNOWN
        - ESCALATION_STATUS_ERROR
        - ESCALATION_MODE_READ_ONLY
        - ESCALATED_FLAG_ON
        - ESCALATED_FLAG_OFF
        - ESCALATED_FLAG_UNKNOWN
        - get_stress_escalation_schema_info

    Engine:
        - build_stress_escalation_record_v1
        - build_stress_escalation_from_bundle_v1
        - get_stress_escalation_info

    Guards:
        - check_forbidden_vocabulary
        - check_token_literals
        - check_address_patterns
        - check_coupling_phrases
        - check_numeric_patterns
        - check_escalation_record
        - FORBIDDEN_TRADING_VERBS
        - FORBIDDEN_PRESCRIPTIVE_LANGUAGE
        - FORBIDDEN_VOCABULARY
        - FORBIDDEN_TOKEN_LITERALS
        - COUPLING_PATTERNS
        - ESCALATION_COUPLING_PATTERNS
"""

from escalation.v14_stress_escalation_schema import (
    V14StressEscalationSchema,
    ESCALATION_VERSION_V1,
    ESCALATION_STATUS_AVAILABLE,
    ESCALATION_STATUS_UNKNOWN,
    ESCALATION_STATUS_ERROR,
    ESCALATION_MODE_READ_ONLY,
    ESCALATED_FLAG_ON,
    ESCALATED_FLAG_OFF,
    ESCALATED_FLAG_UNKNOWN,
    get_stress_escalation_schema_info,
)

from escalation.v14_stress_escalation_engine_v1 import (
    build_stress_escalation_record_v1,
    build_stress_escalation_from_bundle_v1,
    get_stress_escalation_info,
)

from escalation.v14_escalation_constitutional_guard import (
    check_forbidden_vocabulary,
    check_token_literals,
    check_address_patterns,
    check_coupling_phrases,
    check_numeric_patterns,
    check_escalation_record,
    FORBIDDEN_TRADING_VERBS,
    FORBIDDEN_PRESCRIPTIVE_LANGUAGE,
    FORBIDDEN_VOCABULARY,
    FORBIDDEN_TOKEN_LITERALS,
    COUPLING_PATTERNS,
    ESCALATION_COUPLING_PATTERNS,
)

__all__ = [
    # Schema
    "V14StressEscalationSchema",
    "ESCALATION_VERSION_V1",
    "ESCALATION_STATUS_AVAILABLE",
    "ESCALATION_STATUS_UNKNOWN",
    "ESCALATION_STATUS_ERROR",
    "ESCALATION_MODE_READ_ONLY",
    "ESCALATED_FLAG_ON",
    "ESCALATED_FLAG_OFF",
    "ESCALATED_FLAG_UNKNOWN",
    "get_stress_escalation_schema_info",
    # Engine
    "build_stress_escalation_record_v1",
    "build_stress_escalation_from_bundle_v1",
    "get_stress_escalation_info",
    # Guards
    "check_forbidden_vocabulary",
    "check_token_literals",
    "check_address_patterns",
    "check_coupling_phrases",
    "check_numeric_patterns",
    "check_escalation_record",
    "FORBIDDEN_TRADING_VERBS",
    "FORBIDDEN_PRESCRIPTIVE_LANGUAGE",
    "FORBIDDEN_VOCABULARY",
    "FORBIDDEN_TOKEN_LITERALS",
    "COUPLING_PATTERNS",
    "ESCALATION_COUPLING_PATTERNS",
]
