"""
v0.7 Reflection Layer

This package contains the constitutional schema and guards for v0.7 reflection.

Reflection observes interpretation system characteristics without evaluation,
judgment, or recommendation.

Reflection Definition:
    Reflection = Interpretive System Description

    Reflection observes what meanings exist, what structures appear,
    and what the interpretation engine implicitly assumes.

    Reflection does NOT evaluate, recommend, or optimize.

Modules:
    - v7_reflection_schema: Schema definition for reflection records
    - v7_constitutional_guard: Constitutional guards against violations
"""

from .v7_reflection_schema import (
    V7ReflectionSchema,
    validate_basis_fields,
    get_schema_info,
)

# Export class attributes as module-level constants
ALLOWED_BASIS_FIELDS = V7ReflectionSchema.ALLOWED_BASIS_FIELDS
FORBIDDEN_BASIS_FIELDS = V7ReflectionSchema.FORBIDDEN_BASIS_FIELDS

from .v7_constitutional_guard import (
    validate_reflection_record,
    check_forbidden_vocabulary,
    check_confidence_boundary,
    check_observation_boundary,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Schema
    "V7ReflectionSchema",
    "ALLOWED_BASIS_FIELDS",
    "FORBIDDEN_BASIS_FIELDS",
    "validate_basis_fields",
    "get_schema_info",

    # Guards
    "validate_reflection_record",
    "check_forbidden_vocabulary",
    "check_confidence_boundary",
    "check_observation_boundary",
    "FORBIDDEN_VOCABULARY",
]
