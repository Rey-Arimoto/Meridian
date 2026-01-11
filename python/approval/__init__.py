#!/usr/bin/env python3
"""
PR113: v1.1 Human Approval Gate v1 (READ-ONLY)
PR114: v1.1 Manual Approval Registry v1 (READ-ONLY)

Purpose:
    Human approval gate and registry layer.
    Determines approval requirement and records state transitions.

    Approval Gate = Requirement Classification (not action/recommendation)
    Approval Registry = State Transition Record (not action/instruction)

Exports:
    PR113:
    - V11ApprovalSchema: Approval gate record schema
    - gate_human_approval_v1: Core approval gate function
    - validate_approval_record: Approval gate constitutional guard

    PR114:
    - V11ApprovalRegistrySchema: Approval registry record schema
    - apply_approval_event_v1: Core registry state transition function
    - validate_registry_record: Registry constitutional guard
"""

from .v11_approval_schema import (
    V11ApprovalSchema,
    get_approval_schema_info,
)
from .v11_human_approval_gate_engine_v1 import (
    gate_human_approval_v1,
    get_human_approval_gate_v1_info,
)
from .v11_approval_constitutional_guard import (
    validate_approval_record,
)
from .v11_approval_registry_schema import (
    V11ApprovalRegistrySchema,
    get_approval_registry_schema_info,
)
from .v11_manual_approval_registry_engine_v1 import (
    apply_approval_event_v1,
    get_manual_approval_registry_engine_v1_info,
)
from .v11_registry_constitutional_guard import (
    validate_registry_record,
)

__all__ = [
    # PR113 exports
    "V11ApprovalSchema",
    "get_approval_schema_info",
    "gate_human_approval_v1",
    "get_human_approval_gate_v1_info",
    "validate_approval_record",
    # PR114 exports
    "V11ApprovalRegistrySchema",
    "get_approval_registry_schema_info",
    "apply_approval_event_v1",
    "get_manual_approval_registry_engine_v1_info",
    "validate_registry_record",
]
