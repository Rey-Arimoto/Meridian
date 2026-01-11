"""
v0.9 Boundary Layer

This package contains the constitutional schema and guards for v0.9 boundary.

Boundary describes structural limits of observability without evaluation,
judgment, or recommendation.

Boundary Definition:
    Boundary = Structural Limit Description

    Boundary describes where observability stops, not what should be done.

    Boundary classifies blindspots into structural boundary types:
    - SCHEMA_BOUNDARY: Structure cannot be expressed with current schema
    - DATA_BOUNDARY: Required data does not exist or is insufficient
    - ENGINE_BOUNDARY: Interpretation/reflection rules cannot map structure
    - SAMPLING_BOUNDARY: Structure exists in definition space but not observed
    - TEMPORAL_BOUNDARY: Structure exists but cannot be observed in time window

    Boundary does NOT evaluate, recommend, or optimize.

Modules:
    - v9_boundary_schema: Schema definition for boundary records
    - v9_constitutional_guard: Constitutional guards against violations
"""

from .v9_boundary_schema import (
    V9BoundarySchema,
    validate_basis_fields,
    get_schema_info,
)

# Export class attributes as module-level constants
ALLOWED_BASIS_FIELDS = V9BoundarySchema.ALLOWED_BASIS_FIELDS
FORBIDDEN_BASIS_FIELDS_V04 = V9BoundarySchema.FORBIDDEN_BASIS_FIELDS_V04
FORBIDDEN_BASIS_FIELDS_V5 = V9BoundarySchema.FORBIDDEN_BASIS_FIELDS_V5

from .v9_constitutional_guard import (
    validate_boundary_record,
    check_forbidden_vocabulary,
    check_confidence_boundary,
    check_observation_boundary,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Schema
    "V9BoundarySchema",
    "ALLOWED_BASIS_FIELDS",
    "FORBIDDEN_BASIS_FIELDS_V04",
    "FORBIDDEN_BASIS_FIELDS_V5",
    "validate_basis_fields",
    "get_schema_info",
    # Guards
    "validate_boundary_record",
    "check_forbidden_vocabulary",
    "check_confidence_boundary",
    "check_observation_boundary",
    "FORBIDDEN_VOCABULARY",
]
