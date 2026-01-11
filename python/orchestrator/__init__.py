#!/usr/bin/env python3
"""
PR115: v1.0 Pipeline Orchestrator v1 (READ-ONLY)

Purpose:
    Orchestrate the full Meridian pipeline in fixed order.
    Orchestrator = Wiring (not decision/action).

Exports:
    - run_pipeline_v1: Core orchestrator function
    - get_pipeline_orchestrator_v1_info: Orchestrator metadata
    - validate_orchestrator_artifacts: Constitutional guard for orchestrator artifacts
"""

from .v10_pipeline_orchestrator_v1 import (
    run_pipeline_v1,
    get_pipeline_orchestrator_v1_info,
)
from .v10_orchestrator_constitutional_guard import (
    validate_orchestrator_artifacts,
)

__all__ = [
    "run_pipeline_v1",
    "get_pipeline_orchestrator_v1_info",
    "validate_orchestrator_artifacts",
]
