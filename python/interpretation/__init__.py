"""
v0.6 Interpretation Layer

This package contains the constitutional schema and guards for v0.6 interpretation.

Interpretation maps observations to structural meaning types without evaluation,
judgment, or recommendation.

Modules:
    - v6_interpretation_schema: Schema definition for interpretation records
    - v6_constitutional_guard: Constitutional guards against violations
"""

from .v6_interpretation_schema import (
    V6InterpretationSchema,
    ALLOWED_BASIS_FIELDS,
    FORBIDDEN_BASIS_FIELDS,
    get_schema_info,
)

from .v6_constitutional_guard import (
    validate_interpretation_record,
    check_forbidden_vocabulary,
    check_confidence_boundary,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Schema
    "V6InterpretationSchema",
    "ALLOWED_BASIS_FIELDS",
    "FORBIDDEN_BASIS_FIELDS",
    "get_schema_info",

    # Guards
    "validate_interpretation_record",
    "check_forbidden_vocabulary",
    "check_confidence_boundary",
    "FORBIDDEN_VOCABULARY",
]
