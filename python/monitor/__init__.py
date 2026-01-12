#!/usr/bin/env python3
"""
PR126: v1.2 Continuous Permission Monitor v1 (READ-ONLY)

Purpose:
    Continuous permission monitoring layer for tracking execution permission
    state evolution over time without executing or recommending actions.

Exports:
    - V12PermissionMonitorSchema: Monitor schema class
    - get_monitor_schema_info: Schema metadata
    - monitor_permission_v1: Monitor function
    - get_monitor_v1_info: Monitor metadata
    - check_monitor_record: Constitutional guard
    - check_trajectory_coupling: Trajectory coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

from .v12_permission_monitor_schema import (
    V12PermissionMonitorSchema,
    get_monitor_schema_info,
)
from .v12_continuous_permission_monitor_engine_v1 import (
    monitor_permission_v1,
    get_monitor_v1_info,
)
from .v12_monitor_constitutional_guard import (
    check_monitor_record,
    check_trajectory_coupling,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    "V12PermissionMonitorSchema",
    "get_monitor_schema_info",
    "monitor_permission_v1",
    "get_monitor_v1_info",
    "check_monitor_record",
    "check_trajectory_coupling",
    "FORBIDDEN_VOCABULARY",
]
