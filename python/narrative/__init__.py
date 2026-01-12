#!/usr/bin/env python3
"""
PR123/PR139: v1.1/v1.2 Human Narrative Builder v1 (READ-ONLY)

Purpose:
    Human narrative layer for converting explanation context into
    human-readable structural situation stories.
    PR139 adds rescue flow graph extension for structural rescue narrative.

Exports:
    PR123 (v1.1):
    - V11HumanNarrativeSchema: Narrative schema class
    - get_narrative_schema_info: Schema metadata
    - build_human_narrative_v1: Narrative builder function
    - get_narrative_builder_v1_info: Builder metadata
    - check_narrative_record: Constitutional guard
    - check_narrative_coupling: Narrative coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list

    PR139 (v1.2):
    - V12NarrativeRescueFlowExtensionSchema: Rescue narrative schema class
    - RESCUE_NARRATIVE_MODE_ON/OFF: Mode constants
    - RESCUE_NARRATIVE_STATUS_*: Status constants
    - RESCUE_NARRATIVE_STYLE_*: Style constants
    - build_rescue_flow_narrative_extension_v1: Extension builder function
    - get_rescue_flow_narrative_extension_info: Extension metadata
    - check_rescue_narrative_record: Rescue narrative constitutional guard
    - check_rescue_narrative_coupling: Rescue narrative coupling guard
    - check_narrative_action_vocabulary: Action vocabulary guard
    - check_narrative_prescriptive_language: Prescriptive language guard
"""

from .v11_human_narrative_schema import (
    V11HumanNarrativeSchema,
    get_narrative_schema_info,
)
from .v11_human_narrative_builder_engine_v1 import (
    build_human_narrative_v1,
    get_narrative_builder_v1_info,
)
from .v11_narrative_constitutional_guard import (
    check_narrative_record,
    check_narrative_coupling,
    FORBIDDEN_VOCABULARY,
)
from .v12_narrative_rescue_flow_extension_schema import (
    V12NarrativeRescueFlowExtensionSchema,
    RESCUE_NARRATIVE_MODE_ON,
    RESCUE_NARRATIVE_MODE_OFF,
    RESCUE_NARRATIVE_STATUS_AVAILABLE,
    RESCUE_NARRATIVE_STATUS_ERROR,
    RESCUE_NARRATIVE_STATUS_SKIPPED,
    RESCUE_NARRATIVE_STYLE_CONCISE,
    RESCUE_NARRATIVE_STYLE_STANDARD,
    RESCUE_NARRATIVE_STYLE_DETAILED,
)
from .v12_rescue_flow_narrative_extension_engine_v1 import (
    build_rescue_flow_narrative_extension_v1,
    get_rescue_flow_narrative_extension_info,
)
from .v12_rescue_flow_narrative_constitutional_guard import (
    check_rescue_narrative_record,
    check_rescue_narrative_coupling,
    check_narrative_action_vocabulary,
    check_narrative_prescriptive_language,
)

__all__ = [
    # PR123 (v1.1)
    "V11HumanNarrativeSchema",
    "get_narrative_schema_info",
    "build_human_narrative_v1",
    "get_narrative_builder_v1_info",
    "check_narrative_record",
    "check_narrative_coupling",
    "FORBIDDEN_VOCABULARY",
    # PR139 (v1.2)
    "V12NarrativeRescueFlowExtensionSchema",
    "RESCUE_NARRATIVE_MODE_ON",
    "RESCUE_NARRATIVE_MODE_OFF",
    "RESCUE_NARRATIVE_STATUS_AVAILABLE",
    "RESCUE_NARRATIVE_STATUS_ERROR",
    "RESCUE_NARRATIVE_STATUS_SKIPPED",
    "RESCUE_NARRATIVE_STYLE_CONCISE",
    "RESCUE_NARRATIVE_STYLE_STANDARD",
    "RESCUE_NARRATIVE_STYLE_DETAILED",
    "build_rescue_flow_narrative_extension_v1",
    "get_rescue_flow_narrative_extension_info",
    "check_rescue_narrative_record",
    "check_rescue_narrative_coupling",
    "check_narrative_action_vocabulary",
    "check_narrative_prescriptive_language",
]
