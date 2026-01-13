#!/usr/bin/env python3
"""
PR142: v1.3 Approval Packet → Execution Draft Binding Engine v1 (READ-ONLY)

Purpose:
    Map v1.2 Approval Packet (PR124/PR140) or Artifact Bundle (PR115/PR116)
    to PR141 Execution Draft Schema (v13_draft_) with labels and constraints only.

Exports:
    Binding Engine:
    - build_execution_draft_from_bundle_v1: Bind from artifact bundle
    - build_execution_draft_from_packet_v1: Bind from approval packet
    - get_binding_engine_v1_info: Binding engine metadata

    Constitutional Guard:
    - check_binding_output: Binding output guard
    - check_label_only_constraints: Label-only constraint guard
    - check_source_presence_only_inputs: Source presence guard
    - check_intended_shape_structural: Intended shape guard

    Constants:
    - VALID_ACTION_CLASSES: Valid action class labels
"""

from .v13_packet_to_draft_binding_engine_v1 import (
    build_execution_draft_from_bundle_v1,
    build_execution_draft_from_packet_v1,
    get_binding_engine_v1_info,
)
from .v13_bind_constitutional_guard import (
    check_binding_output,
    check_label_only_constraints,
    check_source_presence_only_inputs,
    check_intended_shape_structural,
    VALID_ACTION_CLASSES,
)

__all__ = [
    # Binding Engine
    "build_execution_draft_from_bundle_v1",
    "build_execution_draft_from_packet_v1",
    "get_binding_engine_v1_info",
    # Constitutional Guard
    "check_binding_output",
    "check_label_only_constraints",
    "check_source_presence_only_inputs",
    "check_intended_shape_structural",
    # Constants
    "VALID_ACTION_CLASSES",
]
