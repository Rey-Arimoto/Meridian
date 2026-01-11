"""
v0.8 Blindspot Layer

This package contains the constitutional schema and guards for v0.8 blindspot.

Blindspot observes structural absences in the interpretation/reflection systems
without evaluation, judgment, or recommendation.

Blindspot Definition:
    Blindspot = Structural Absence Description

    Blindspot observes what the interpretation/reflection systems cannot see:
    - Unseen signal types
    - Unseen factor types
    - Unobserved meaning types
    - Transitions never observed
    - Structures the schema cannot express

    Blindspot does NOT evaluate, recommend, or optimize.

Modules:
    - v8_blindspot_schema: Schema definition for blindspot records
    - v8_constitutional_guard: Constitutional guards against violations
"""

from .v8_blindspot_schema import (
    V8BlindspotSchema,
    validate_basis_fields,
    get_schema_info,
)

# Export class attributes as module-level constants
ALLOWED_BASIS_FIELDS = V8BlindspotSchema.ALLOWED_BASIS_FIELDS
FORBIDDEN_BASIS_FIELDS_V04 = V8BlindspotSchema.FORBIDDEN_BASIS_FIELDS_V04
FORBIDDEN_BASIS_FIELDS_V5 = V8BlindspotSchema.FORBIDDEN_BASIS_FIELDS_V5

from .v8_constitutional_guard import (
    validate_blindspot_record,
    check_forbidden_vocabulary,
    check_confidence_boundary,
    check_observation_boundary,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Schema
    "V8BlindspotSchema",
    "ALLOWED_BASIS_FIELDS",
    "FORBIDDEN_BASIS_FIELDS_V04",
    "FORBIDDEN_BASIS_FIELDS_V5",
    "validate_basis_fields",
    "get_schema_info",
    # Guards
    "validate_blindspot_record",
    "check_forbidden_vocabulary",
    "check_confidence_boundary",
    "check_observation_boundary",
    "FORBIDDEN_VOCABULARY",
]
