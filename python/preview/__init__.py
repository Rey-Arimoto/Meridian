#!/usr/bin/env python3
"""
PR112: v1.1 Execution Preview Engine v1 (READ-ONLY)

Purpose:
    Execution preview layer.
    Describes structural impact shape of potential execution.

    Preview ≠ Simulation ≠ Execution
    Preview = Impact Shape Description

Exports:
    - V11ExecutionPreviewSchema: Preview record schema
    - generate_execution_preview_v1: Core preview generation function
    - validate_preview_record: Constitutional guard validator
"""

from .v11_execution_preview_schema import (
    V11ExecutionPreviewSchema,
    get_execution_preview_schema_info,
)
from .v11_execution_preview_engine_v1 import (
    generate_execution_preview_v1,
    get_execution_preview_engine_v1_info,
)
from .v11_preview_constitutional_guard import (
    validate_preview_record,
)

__all__ = [
    "V11ExecutionPreviewSchema",
    "get_execution_preview_schema_info",
    "generate_execution_preview_v1",
    "get_execution_preview_engine_v1_info",
    "validate_preview_record",
]
