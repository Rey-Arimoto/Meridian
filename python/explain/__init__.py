#!/usr/bin/env python3
"""
PR122: v1.1 Human Explanation Context Schema v1 (READ-ONLY)

Purpose:
    Human explanation context layer for packaging structural situation as
    non-prescriptive context prior to approval workflow.

Exports:
    - V11HumanExplanationContextSchema: Explanation context schema class
    - get_explanation_schema_info: Schema metadata
    - validate_explanation_context: Constitutional guard
    - check_prescriptive_coupling: Prescriptive coupling guard
"""

from .v11_human_explanation_context_schema import (
    V11HumanExplanationContextSchema,
    get_explanation_schema_info,
)
from .v11_explain_constitutional_guard import (
    validate_explanation_context,
    check_prescriptive_coupling,
)

__all__ = [
    "V11HumanExplanationContextSchema",
    "get_explanation_schema_info",
    "validate_explanation_context",
    "check_prescriptive_coupling",
]
