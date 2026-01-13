#!/usr/bin/env python3
"""
PR143: v1.3 Execution Gate (Always-Blocked) v1 (READ-ONLY)

Purpose:
    Build execution gate from execution draft (PR141/PR142).
    ALWAYS returns BLOCKED with structural block reasons.

Exports:
    Schema:
    - V13ExecutionGateSchema: Gate schema class
    - get_gate_schema_info: Schema metadata
    - GATE_VERSION_V1_3: Version constant
    - GATE_STATUS_AVAILABLE: Status constant
    - GATE_STATUS_ERROR: Status constant
    - GATE_MODE_READ_ONLY: Mode constant
    - GATE_STATE_BLOCKED: Gate state constant (always)
    - Block reason constants: REASON_*

    Engine:
    - build_execution_gate_from_draft_v1: Build gate from draft
    - build_execution_gate_from_bundle_v1: Build gate from bundle
    - get_execution_gate_engine_v1_info: Engine metadata

    Constitutional Guard:
    - check_gate_record: Gate record guard
    - check_prescriptive_language: Prescriptive language guard
    - check_action_vocabulary: Action vocabulary guard
    - check_token_literals: Token literal guard
    - check_address_patterns: Address pattern guard
    - check_gate_coupling: Gate coupling guard
    - check_gate_state_blocked: Gate state guard

    Forbidden Lists:
    - FORBIDDEN_PRESCRIPTIVE_LANGUAGE: Prescriptive language list
    - FORBIDDEN_ACTION_VOCABULARY: Action vocabulary list
    - FORBIDDEN_TOKEN_LITERALS: Token literal list
    - GATE_COUPLING_PATTERNS: Gate coupling pattern list
    - FORBIDDEN_ALLOW_STATES: Forbidden allow states list
"""

from .v13_execution_gate_schema import (
    V13ExecutionGateSchema,
    get_gate_schema_info,
    GATE_VERSION_V1_3,
    GATE_STATUS_AVAILABLE,
    GATE_STATUS_ERROR,
    GATE_MODE_READ_ONLY,
    GATE_STATE_BLOCKED,
    REASON_INVALID_DRAFT,
    REASON_NO_ACTION_SHAPE,
    REASON_HUMAN_REVIEW_REQUIRED,
    REASON_SIMULATION_ONLY,
    REASON_CONSIDERATION_ONLY,
    REASON_HARD_CONSTRAINT,
    REASON_SUPPRESSED,
    REASON_MISSING_INPUTS,
    REASON_DRAFT_WARNINGS,
    REASON_NO_EXECUTION_LOGIC,
)
from .v13_execution_gate_engine_v1 import (
    build_execution_gate_from_draft_v1,
    build_execution_gate_from_bundle_v1,
    get_execution_gate_engine_v1_info,
)
from .v13_gate_constitutional_guard import (
    check_gate_record,
    check_prescriptive_language,
    check_action_vocabulary,
    check_token_literals,
    check_address_patterns,
    check_gate_coupling,
    check_gate_state_blocked,
    FORBIDDEN_PRESCRIPTIVE_LANGUAGE,
    FORBIDDEN_ACTION_VOCABULARY,
    FORBIDDEN_TOKEN_LITERALS,
    GATE_COUPLING_PATTERNS,
    FORBIDDEN_ALLOW_STATES,
)

__all__ = [
    # Schema
    "V13ExecutionGateSchema",
    "get_gate_schema_info",
    "GATE_VERSION_V1_3",
    "GATE_STATUS_AVAILABLE",
    "GATE_STATUS_ERROR",
    "GATE_MODE_READ_ONLY",
    "GATE_STATE_BLOCKED",
    "REASON_INVALID_DRAFT",
    "REASON_NO_ACTION_SHAPE",
    "REASON_HUMAN_REVIEW_REQUIRED",
    "REASON_SIMULATION_ONLY",
    "REASON_CONSIDERATION_ONLY",
    "REASON_HARD_CONSTRAINT",
    "REASON_SUPPRESSED",
    "REASON_MISSING_INPUTS",
    "REASON_DRAFT_WARNINGS",
    "REASON_NO_EXECUTION_LOGIC",
    # Engine
    "build_execution_gate_from_draft_v1",
    "build_execution_gate_from_bundle_v1",
    "get_execution_gate_engine_v1_info",
    # Constitutional Guard
    "check_gate_record",
    "check_prescriptive_language",
    "check_action_vocabulary",
    "check_token_literals",
    "check_address_patterns",
    "check_gate_coupling",
    "check_gate_state_blocked",
    # Forbidden Lists
    "FORBIDDEN_PRESCRIPTIVE_LANGUAGE",
    "FORBIDDEN_ACTION_VOCABULARY",
    "FORBIDDEN_TOKEN_LITERALS",
    "GATE_COUPLING_PATTERNS",
    "FORBIDDEN_ALLOW_STATES",
]
