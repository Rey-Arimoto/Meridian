#!/usr/bin/env python3
"""
PR123: v1.1 Human Narrative Builder v1 (READ-ONLY)

Purpose:
    Human narrative layer for converting explanation context into
    human-readable structural situation stories.

Exports:
    - V11HumanNarrativeSchema: Narrative schema class
    - get_narrative_schema_info: Schema metadata
    - build_human_narrative_v1: Narrative builder function
    - get_narrative_builder_v1_info: Builder metadata
    - check_narrative_record: Constitutional guard
    - check_narrative_coupling: Narrative coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
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

__all__ = [
    "V11HumanNarrativeSchema",
    "get_narrative_schema_info",
    "build_human_narrative_v1",
    "get_narrative_builder_v1_info",
    "check_narrative_record",
    "check_narrative_coupling",
    "FORBIDDEN_VOCABULARY",
]
