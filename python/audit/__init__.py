"""
v1.0 Execution Audit Trail Layer

This package contains the audit trail schema and engine for v1.0 execution.

Audit Trail documents the causal chain without execution, evaluation, or trading.

Audit Trail Definition:
    Audit Trail = Causal Chain Documentation

    Links interpretation analytics → blindspot → boundary →
    permission → plan → simulation as explicit chain-of-custody.

    Audit Trail does NOT:
    - Execute (no trading, no wallet, no transactions)
    - Evaluate (no good/bad judgment)
    - Recommend (no should/must)

Modules:
    - v10_execution_audit_trail_schema: Schema definition for audit trail records
    - v10_execution_audit_trail_engine_v1: Audit trail engine v1
    - v10_audit_constitutional_guard: Constitutional guards for audit trails
"""

from .v10_execution_audit_trail_schema import (
    V10ExecutionAuditTrailSchema,
    get_audit_trail_schema_info,
)

from .v10_execution_audit_trail_engine_v1 import (
    build_execution_audit_trail_v1,
    get_audit_trail_engine_v1_info,
)

from .v10_audit_constitutional_guard import (
    validate_v10_audit_trail_record,
)

__all__ = [
    # Schema
    "V10ExecutionAuditTrailSchema",
    "get_audit_trail_schema_info",
    # Engine
    "build_execution_audit_trail_v1",
    "get_audit_trail_engine_v1_info",
    # Guards
    "validate_v10_audit_trail_record",
]
