#!/usr/bin/env python3
"""
PR124/PR140: v1.1/v1.2 Approval Packet Builder (READ-ONLY)

Purpose:
    Approval packet layer for bundling component records into
    a single review unit for human interface.
    PR140 adds v1.2 integration orchestrator for artifact bundle assembly.

Exports:
    PR124 (v1.1):
    - V11ApprovalPacketSchema: Packet schema class
    - get_packet_schema_info: Schema metadata
    - build_approval_packet_v1: Packet builder function
    - get_packet_builder_v1_info: Builder metadata
    - check_packet_record: Constitutional guard
    - check_cross_component_coupling: Cross-component coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list

    PR140 (v1.2):
    - build_approval_packet_v12: Integration orchestrator function
    - get_integration_orchestrator_v1_info: Orchestrator metadata
"""

from .v11_approval_packet_schema import (
    V11ApprovalPacketSchema,
    get_packet_schema_info,
)
from .v11_approval_packet_builder_engine_v1 import (
    build_approval_packet_v1,
    get_packet_builder_v1_info,
)
from .v11_packet_constitutional_guard import (
    check_packet_record,
    check_cross_component_coupling,
    FORBIDDEN_VOCABULARY,
)
from .v12_approval_packet_integration_orchestrator_engine_v1 import (
    build_approval_packet_v12,
    get_integration_orchestrator_v1_info,
)

__all__ = [
    # PR124 (v1.1)
    "V11ApprovalPacketSchema",
    "get_packet_schema_info",
    "build_approval_packet_v1",
    "get_packet_builder_v1_info",
    "check_packet_record",
    "check_cross_component_coupling",
    "FORBIDDEN_VOCABULARY",
    # PR140 (v1.2)
    "build_approval_packet_v12",
    "get_integration_orchestrator_v1_info",
]
