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
    - v10_execution_permissioning_engine_v1: Execution permissioning engine v1
    - v10_execution_plan_schema: Schema definition for execution plan records
    - v10_plan_constitutional_guard: Constitutional guards for plans
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

from .v10_execution_permissioning_engine_v1 import (
    classify_execution_permission_v1,
    V1PermissionTypes,
)

from .v10_execution_plan_schema import (
    V10ExecutionPlanSchema,
    validate_plan_basis_fields,
    get_plan_schema_info,
)

from .v10_plan_constitutional_guard import (
    validate_plan_record,
    check_token_literals,
    check_numeric_patterns,
)

from .v10_execution_plan_generator_v1 import (
    generate_execution_plan_v1,
    get_generator_v1_info,
)

from .v10_execution_simulation_schema import (
    V10ExecutionSimulationSchema,
    validate_simulation_basis_fields,
    get_simulation_schema_info,
)

from .v10_execution_simulation_engine_v1 import (
    simulate_execution_plan_v1,
    get_simulation_engine_v1_info,
)

from .v10_simulation_constitutional_guard import (
    validate_v10_simulation_record,
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
    # Engines
    "classify_execution_permission_v1",
    "V1PermissionTypes",
    # Plan Schema
    "V10ExecutionPlanSchema",
    "validate_plan_basis_fields",
    "get_plan_schema_info",
    # Plan Guards
    "validate_plan_record",
    "check_token_literals",
    "check_numeric_patterns",
    # Plan Generators
    "generate_execution_plan_v1",
    "get_generator_v1_info",
    # Simulation Schema
    "V10ExecutionSimulationSchema",
    "validate_simulation_basis_fields",
    "get_simulation_schema_info",
    # Simulation Engine
    "simulate_execution_plan_v1",
    "get_simulation_engine_v1_info",
    # Simulation Guards
    "validate_v10_simulation_record",
]
