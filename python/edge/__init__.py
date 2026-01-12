#!/usr/bin/env python3
"""
PR135: v1.2 Edge Type Classification Engine v1 (READ-ONLY)

Purpose:
    Classify edge types for regime × role × distortion combinations.
    EdgeType = Structural label propagation (not action, not recommendation).

Exports:
    Schema:
    - V12EdgeTypeSchema: Edge type schema class
    - get_edge_type_schema_info: Schema metadata
    - Edge type constants: EDGE_NONE, EDGE_AMPLIFY, EDGE_SHIELD, EDGE_LEAK, EDGE_NEUTRAL
    - VALID_EDGE_TYPES: List of valid edge types

    Engine:
    - classify_edge_type_v1: Edge type classification function
    - get_edge_type_classifier_v1_info: Engine metadata

    Guards:
    - check_edge_type_record: Constitutional guard
    - check_edge_coupling: Edge coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

# Schema
from .v12_edge_type_schema import (
    V12EdgeTypeSchema,
    get_edge_type_schema_info,
    EDGE_NONE,
    EDGE_AMPLIFY,
    EDGE_SHIELD,
    EDGE_LEAK,
    EDGE_NEUTRAL,
    VALID_EDGE_TYPES,
)

# Engine
from .v12_edge_type_classifier_v1 import (
    classify_edge_type_v1,
    get_edge_type_classifier_v1_info,
)

# Guards
from .v12_edge_constitutional_guard import (
    check_edge_type_record,
    check_edge_coupling,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Schema
    "V12EdgeTypeSchema",
    "get_edge_type_schema_info",
    "EDGE_NONE",
    "EDGE_AMPLIFY",
    "EDGE_SHIELD",
    "EDGE_LEAK",
    "EDGE_NEUTRAL",
    "VALID_EDGE_TYPES",
    # Engine
    "classify_edge_type_v1",
    "get_edge_type_classifier_v1_info",
    # Guards
    "check_edge_type_record",
    "check_edge_coupling",
    "FORBIDDEN_VOCABULARY",
]
