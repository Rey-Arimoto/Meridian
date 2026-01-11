"""
v1.0 Execution Layer

This package contains the constitutional schema and guards for v1.0 execution.

Execution describes executability without evaluation, judgment, or trading.

Execution Definition:
    Execution = Executability Description

    Based on observation/interpretation/reflection/blindspot/boundary,
    generate a record describing execution intent.

    Execution does NOT:
    - Trade (swap, transfer, send, approve, sign)
    - Make position changes, fund movement, rebalancing
    - Provide recommendations (should/must)
    - Evaluate profit/loss
    - Score, rank, optimize

Modules:
    - v10_execution_schema: Schema definition for execution records
    - v10_constitutional_guard: Constitutional guards against violations
"""

from .v10_execution_schema import (
    V10ExecutionSchema,
    validate_basis_fields,
    get_schema_info,
)

# Export class attributes as module-level constants
ALLOWED_BASIS_FIELDS = V10ExecutionSchema.ALLOWED_BASIS_FIELDS
FORBIDDEN_BASIS_FIELDS_V04 = V10ExecutionSchema.FORBIDDEN_BASIS_FIELDS_V04
FORBIDDEN_BASIS_FIELDS_V5 = V10ExecutionSchema.FORBIDDEN_BASIS_FIELDS_V5

from .v10_constitutional_guard import (
    validate_execution_record,
    check_forbidden_vocabulary,
    check_execution_safety,
    check_confidence_boundary,
    check_observation_boundary,
    FORBIDDEN_VOCABULARY,
    EXECUTION_ACTION_VOCABULARY,
)

__all__ = [
    # Schema
    "V10ExecutionSchema",
    "ALLOWED_BASIS_FIELDS",
    "FORBIDDEN_BASIS_FIELDS_V04",
    "FORBIDDEN_BASIS_FIELDS_V5",
    "validate_basis_fields",
    "get_schema_info",
    # Guards
    "validate_execution_record",
    "check_forbidden_vocabulary",
    "check_execution_safety",
    "check_confidence_boundary",
    "check_observation_boundary",
    "FORBIDDEN_VOCABULARY",
    "EXECUTION_ACTION_VOCABULARY",
]
