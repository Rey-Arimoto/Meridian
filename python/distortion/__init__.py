#!/usr/bin/env python3
"""
PR129: v1.2 Distortion Detector v1 (READ-ONLY)

Purpose:
    Classify distortion types D1-D5 from existing Meridian pipeline artifacts.
    Distortion ≠ Signal ≠ Recommendation.
    Distortion = Structural label (failure-mode classification).

Exports:
    - V12DistortionSchema: Distortion schema class
    - get_distortion_schema_info: Schema metadata
    - detect_distortion_v1: Detection function
    - get_detector_v1_info: Detector metadata
    - check_distortion_record: Constitutional guard
    - check_distortion_coupling: Distortion coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
    - Distortion type constants: D0_NONE, D1_LIQUIDATION, D2_RANGE_STICKINESS,
                                D3_BOOK_HOLLOWING, D4_EVENT_DISTORTION,
                                D5_CORRELATION_DISTORTION, DISTORTION_UNCLASSIFIED
"""

from .v12_distortion_schema import (
    V12DistortionSchema,
    get_distortion_schema_info,
    D0_NONE,
    D1_LIQUIDATION,
    D2_RANGE_STICKINESS,
    D3_BOOK_HOLLOWING,
    D4_EVENT_DISTORTION,
    D5_CORRELATION_DISTORTION,
    DISTORTION_UNCLASSIFIED,
)
from .v12_distortion_detector_engine_v1 import (
    detect_distortion_v1,
    get_detector_v1_info,
)
from .v12_distortion_constitutional_guard import (
    check_distortion_record,
    check_distortion_coupling,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    "V12DistortionSchema",
    "get_distortion_schema_info",
    "detect_distortion_v1",
    "get_detector_v1_info",
    "check_distortion_record",
    "check_distortion_coupling",
    "FORBIDDEN_VOCABULARY",
    "D0_NONE",
    "D1_LIQUIDATION",
    "D2_RANGE_STICKINESS",
    "D3_BOOK_HOLLOWING",
    "D4_EVENT_DISTORTION",
    "D5_CORRELATION_DISTORTION",
    "DISTORTION_UNCLASSIFIED",
]
