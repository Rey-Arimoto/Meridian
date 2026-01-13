#!/usr/bin/env python3
"""
PR141: v1.3 Execution Draft Schema v1 (READ-ONLY)

Purpose:
    Define strict schema for "execution draft" generated from approval packets.
    This is NOT an instruction, NOT a recommendation, NOT a transaction.
    It is a structured, non-custodial, execution-shaped draft record.

Exports:
    Schema:
    - V13ExecutionDraftSchema: Draft schema class
    - get_draft_schema_info: Schema metadata
    - DRAFT_VERSION_V1: Version constant
    - DRAFT_STATUS_AVAILABLE: Status constant
    - DRAFT_STATUS_ERROR: Status constant
    - DRAFT_MODE_READ_ONLY: Mode constant
    - ACTION_CLASS_NONE: Action class constant
    - ACTION_CLASS_DRAFT_ONLY: Action class constant

    Constitutional Guard:
    - check_draft_record: Draft record guard
    - check_token_literals: Token literal guard
    - check_trading_vocabulary: Trading vocabulary guard
    - check_prescriptive_language: Prescriptive language guard
    - check_draft_causal_coupling: Draft causal coupling guard
    - check_address_patterns: Address pattern guard

    Forbidden Lists:
    - FORBIDDEN_TOKEN_LITERALS: Token literal list
    - FORBIDDEN_TRADING_VOCABULARY: Trading vocabulary list
    - FORBIDDEN_PRESCRIPTIVE_LANGUAGE: Prescriptive language list
    - DRAFT_COUPLING_PATTERNS: Draft coupling pattern list
"""

from .v13_execution_draft_schema import (
    V13ExecutionDraftSchema,
    get_draft_schema_info,
    DRAFT_VERSION_V1,
    DRAFT_STATUS_AVAILABLE,
    DRAFT_STATUS_ERROR,
    DRAFT_MODE_READ_ONLY,
    ACTION_CLASS_NONE,
    ACTION_CLASS_DRAFT_ONLY,
)
from .v13_draft_constitutional_guard import (
    check_draft_record,
    check_token_literals,
    check_trading_vocabulary,
    check_prescriptive_language,
    check_draft_causal_coupling,
    check_address_patterns,
    FORBIDDEN_TOKEN_LITERALS,
    FORBIDDEN_TRADING_VOCABULARY,
    FORBIDDEN_PRESCRIPTIVE_LANGUAGE,
    DRAFT_COUPLING_PATTERNS,
)

__all__ = [
    # Schema
    "V13ExecutionDraftSchema",
    "get_draft_schema_info",
    "DRAFT_VERSION_V1",
    "DRAFT_STATUS_AVAILABLE",
    "DRAFT_STATUS_ERROR",
    "DRAFT_MODE_READ_ONLY",
    "ACTION_CLASS_NONE",
    "ACTION_CLASS_DRAFT_ONLY",
    # Constitutional Guard
    "check_draft_record",
    "check_token_literals",
    "check_trading_vocabulary",
    "check_prescriptive_language",
    "check_draft_causal_coupling",
    "check_address_patterns",
    # Forbidden Lists
    "FORBIDDEN_TOKEN_LITERALS",
    "FORBIDDEN_TRADING_VOCABULARY",
    "FORBIDDEN_PRESCRIPTIVE_LANGUAGE",
    "DRAFT_COUPLING_PATTERNS",
]
