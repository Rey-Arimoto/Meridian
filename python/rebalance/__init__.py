#!/usr/bin/env python3
"""
PR151: v1.4 Rebalance Template Guidance Package (READ-ONLY)

Purpose:
    Export schema class, engine functions, guards, and constants for rebalance template guidance.

Exports:
    Schema:
        - V14RebalanceTemplateSchema
        - REBALANCE_VERSION_V1
        - REBALANCE_STATUS_AVAILABLE
        - REBALANCE_STATUS_ERROR
        - TPL_UNKNOWN
        - TPL_RISK_0
        - TPL_RISK_20
        - TPL_RISK_50
        - TPL_RISK_90
        - SCOPE_PORTFOLIO_REBALANCE
        - RULE_GUARD_FREEZE
        - RULE_GUARD_STRESSED
        - RULE_DOWN_SHOCK
        - RULE_DOWN_REVERSAL
        - RULE_UP_SHOCK
        - RULE_UP_REVERSAL
        - RULE_NORMAL_UP_TREND
        - RULE_NORMAL_DOWN_TREND
        - RULE_NORMAL_RANGE
        - RULE_FALLBACK_UNKNOWN
        - get_rebalance_template_schema_info

    Engine:
        - build_rebalance_template_guidance_v1
        - extract_rebalance_inputs_v1
        - get_rebalance_engine_info
        - TREND_UP_TREND
        - TREND_DOWN_TREND
        - TREND_RANGE
        - TREND_UNKNOWN

    Guards:
        - check_forbidden_vocabulary
        - check_token_names
        - check_coupling_phrases
        - check_numeric_ratios_in_text
        - check_rebalance_record
        - FORBIDDEN_TRADING_VERBS
        - FORBIDDEN_PRESCRIPTIVE_LANGUAGE
        - FORBIDDEN_VOCABULARY
        - FORBIDDEN_TOKEN_NAMES
        - COUPLING_PATTERNS
        - TEMPLATE_COUPLING_PATTERNS
"""

from rebalance.v14_rebalance_template_schema import (
    V14RebalanceTemplateSchema,
    REBALANCE_VERSION_V1,
    REBALANCE_STATUS_AVAILABLE,
    REBALANCE_STATUS_ERROR,
    TPL_UNKNOWN,
    TPL_RISK_0,
    TPL_RISK_20,
    TPL_RISK_50,
    TPL_RISK_90,
    SCOPE_PORTFOLIO_REBALANCE,
    RULE_GUARD_FREEZE,
    RULE_GUARD_STRESSED,
    RULE_DOWN_SHOCK,
    RULE_DOWN_REVERSAL,
    RULE_UP_SHOCK,
    RULE_UP_REVERSAL,
    RULE_NORMAL_UP_TREND,
    RULE_NORMAL_DOWN_TREND,
    RULE_NORMAL_RANGE,
    RULE_FALLBACK_UNKNOWN,
    get_rebalance_template_schema_info,
)

from rebalance.v14_rebalance_template_engine_v1 import (
    build_rebalance_template_guidance_v1,
    extract_rebalance_inputs_v1,
    get_rebalance_engine_info,
    TREND_UP_TREND,
    TREND_DOWN_TREND,
    TREND_RANGE,
    TREND_UNKNOWN,
)

from rebalance.v14_rebalance_constitutional_guard import (
    check_forbidden_vocabulary,
    check_token_names,
    check_coupling_phrases,
    check_numeric_ratios_in_text,
    check_rebalance_record,
    FORBIDDEN_TRADING_VERBS,
    FORBIDDEN_PRESCRIPTIVE_LANGUAGE,
    FORBIDDEN_VOCABULARY,
    FORBIDDEN_TOKEN_NAMES,
    COUPLING_PATTERNS,
    TEMPLATE_COUPLING_PATTERNS,
)

__all__ = [
    # Schema
    "V14RebalanceTemplateSchema",
    "REBALANCE_VERSION_V1",
    "REBALANCE_STATUS_AVAILABLE",
    "REBALANCE_STATUS_ERROR",
    "TPL_UNKNOWN",
    "TPL_RISK_0",
    "TPL_RISK_20",
    "TPL_RISK_50",
    "TPL_RISK_90",
    "SCOPE_PORTFOLIO_REBALANCE",
    "RULE_GUARD_FREEZE",
    "RULE_GUARD_STRESSED",
    "RULE_DOWN_SHOCK",
    "RULE_DOWN_REVERSAL",
    "RULE_UP_SHOCK",
    "RULE_UP_REVERSAL",
    "RULE_NORMAL_UP_TREND",
    "RULE_NORMAL_DOWN_TREND",
    "RULE_NORMAL_RANGE",
    "RULE_FALLBACK_UNKNOWN",
    "get_rebalance_template_schema_info",
    # Engine
    "build_rebalance_template_guidance_v1",
    "extract_rebalance_inputs_v1",
    "get_rebalance_engine_info",
    "TREND_UP_TREND",
    "TREND_DOWN_TREND",
    "TREND_RANGE",
    "TREND_UNKNOWN",
    # Guards
    "check_forbidden_vocabulary",
    "check_token_names",
    "check_coupling_phrases",
    "check_numeric_ratios_in_text",
    "check_rebalance_record",
    "FORBIDDEN_TRADING_VERBS",
    "FORBIDDEN_PRESCRIPTIVE_LANGUAGE",
    "FORBIDDEN_VOCABULARY",
    "FORBIDDEN_TOKEN_NAMES",
    "COUPLING_PATTERNS",
    "TEMPLATE_COUPLING_PATTERNS",
]
