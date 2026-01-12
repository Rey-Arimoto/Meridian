#!/usr/bin/env python3
"""
PR127: v1.2 Permission Trajectory Signal v1 (READ-ONLY)

Purpose:
    Bind PR126 monitor records into human-readable trajectory signals for
    v1.1 Human Interface Layer (PR122-PR125).

Exports:
    - V12PermissionTrajectorySignalSchema: Signal schema class
    - get_signal_schema_info: Schema metadata
    - bind_permission_trajectory_signal_v1: Binding function
    - get_binding_v1_info: Binding metadata
    - check_signal_record: Constitutional guard
    - check_signal_trajectory_coupling: Signal-specific coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

from .v12_permission_trajectory_signal_schema import (
    V12PermissionTrajectorySignalSchema,
    get_signal_schema_info,
)
from .v12_permission_trajectory_binding_engine_v1 import (
    bind_permission_trajectory_signal_v1,
    get_binding_v1_info,
)
from .v12_signal_constitutional_guard import (
    check_signal_record,
    check_signal_trajectory_coupling,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    "V12PermissionTrajectorySignalSchema",
    "get_signal_schema_info",
    "bind_permission_trajectory_signal_v1",
    "get_binding_v1_info",
    "check_signal_record",
    "check_signal_trajectory_coupling",
    "FORBIDDEN_VOCABULARY",
]
