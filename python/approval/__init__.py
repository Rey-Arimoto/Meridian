#!/usr/bin/env python3
"""
PR113: v1.1 Human Approval Gate v1 (READ-ONLY)

Purpose:
    Human approval gate layer.
    Determines approval requirement from upstream records.

    Approval Gate = State Machine (not action/recommendation)

Exports:
    - V11ApprovalSchema: Approval record schema
    - gate_human_approval_v1: Core approval gate function
    - validate_approval_record: Constitutional guard validator
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

__all__ = [
    "V11ApprovalSchema",
    "get_approval_schema_info",
    "gate_human_approval_v1",
    "get_human_approval_gate_v1_info",
    "validate_approval_record",
]
