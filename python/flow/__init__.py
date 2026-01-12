#!/usr/bin/env python3
"""
PR137: v1.2 Rescue Flow Graph Engine v1 (READ-ONLY)

Purpose:
    Build READ-ONLY graph artifact describing ROLE-to-ROLE rescue structure
    using label-only edges from PR135 EdgeType and PR136 RescueStrength.

Exports:
    PR137 - Rescue Flow Graph:
    - V12RescueFlowGraphSchema: Flow graph schema class
    - get_flow_schema_info: Schema metadata
    - Flow mode constants: FLOW_MODE_ON, FLOW_MODE_OFF
    - Flow status constants: FLOW_STATUS_AVAILABLE, FLOW_STATUS_ERROR
    - Graph type constant: FLOW_GRAPH_TYPE_RESCUE
    - build_rescue_flow_graph_v1: Flow graph builder function
    - get_rescue_flow_graph_engine_v1_info: Engine metadata
    - check_flow_graph_record: Constitutional guard (PR137)
    - check_flow_coupling: Flow coupling guard

Flow Graph = Structural mapping (not action, not instruction)
"""

# Schema
from .v12_rescue_flow_graph_schema import (
    V12RescueFlowGraphSchema,
    get_flow_schema_info,
    FLOW_MODE_ON,
    FLOW_MODE_OFF,
    FLOW_STATUS_AVAILABLE,
    FLOW_STATUS_ERROR,
    FLOW_GRAPH_TYPE_RESCUE,
)

# Engine
from .v12_rescue_flow_graph_engine_v1 import (
    build_rescue_flow_graph_v1,
    get_rescue_flow_graph_engine_v1_info,
)

# Guards
from .v12_flow_constitutional_guard import (
    check_flow_graph_record,
    check_flow_coupling,
)

__all__ = [
    # PR137: Rescue Flow Graph Schema
    "V12RescueFlowGraphSchema",
    "get_flow_schema_info",
    "FLOW_MODE_ON",
    "FLOW_MODE_OFF",
    "FLOW_STATUS_AVAILABLE",
    "FLOW_STATUS_ERROR",
    "FLOW_GRAPH_TYPE_RESCUE",
    # PR137: Rescue Flow Graph Engine
    "build_rescue_flow_graph_v1",
    "get_rescue_flow_graph_engine_v1_info",
    # Guards
    "check_flow_graph_record",
    "check_flow_coupling",
]
