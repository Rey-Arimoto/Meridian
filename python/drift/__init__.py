#!/usr/bin/env python3
"""
PR120: v1.0 Market Structure Drift Detection Engine v1 (READ-ONLY)

Purpose:
    Market structure drift detection layer for vocabulary window comparison.
    Drift = Structural Language Shift (not evaluation, not prediction).

Exports:
    - V10MarketStructureDriftSchema: Drift schema class
    - get_drift_schema_info: Drift schema metadata
    - detect_market_structure_drift_v1: Core drift detection function
    - get_drift_engine_v1_info: Engine metadata
    - validate_drift_record: Constitutional guard for drift records
"""

from .v10_market_structure_drift_schema import (
    V10MarketStructureDriftSchema,
    get_drift_schema_info,
)
from .v10_market_structure_drift_engine_v1 import (
    detect_market_structure_drift_v1,
    get_drift_engine_v1_info,
)
from .v10_drift_constitutional_guard import (
    validate_drift_record,
)

__all__ = [
    "V10MarketStructureDriftSchema",
    "get_drift_schema_info",
    "detect_market_structure_drift_v1",
    "get_drift_engine_v1_info",
    "validate_drift_record",
]
