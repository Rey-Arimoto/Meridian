#!/usr/bin/env python3
"""
PR129/PR134: v1.2 Distortion Detector & Subtype Classifier (READ-ONLY)

Purpose:
    Classify distortion types D1-D5 and subtypes D1A-D5C from Meridian pipeline artifacts.
    Distortion ≠ Signal ≠ Recommendation.
    Distortion = Structural label (failure-mode classification).

Exports:
    Parent Distortion (PR129):
    - V12DistortionSchema: Distortion schema class
    - get_distortion_schema_info: Schema metadata
    - detect_distortion_v1: Detection function
    - get_detector_v1_info: Detector metadata
    - check_distortion_record: Constitutional guard
    - check_distortion_coupling: Distortion coupling guard
    - Distortion type constants: D0_NONE, D1_LIQUIDATION, D2_RANGE_STICKINESS,
                                D3_BOOK_HOLLOWING, D4_EVENT_DISTORTION,
                                D5_CORRELATION_DISTORTION, DISTORTION_UNCLASSIFIED

    Distortion Subtype (PR134):
    - V12DistortionSubtypeSchema: Subtype schema class
    - get_distortion_subtype_schema_info: Subtype schema metadata
    - classify_distortion_subtype_v1: Subtype classification function
    - get_distortion_subtype_classifier_v1_info: Subtype classifier metadata
    - check_distortion_subtype_record: Subtype constitutional guard
    - check_subtype_coupling: Subtype coupling guard
    - Subtype constants: SUBTYPE_D1A_FORCED_FLOW, SUBTYPE_D1B_CASCADE_RISK, etc.
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
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

# PR134: Distortion Subtype
from .v12_distortion_subtype_schema import (
    V12DistortionSubtypeSchema,
    get_distortion_subtype_schema_info,
    SUBTYPE_D1A_FORCED_FLOW,
    SUBTYPE_D1B_CASCADE_RISK,
    SUBTYPE_D1C_STRESS_UNWIND,
    SUBTYPE_D2A_MEAN_REVERT_PRESSURE,
    SUBTYPE_D2B_RANGE_PINNING,
    SUBTYPE_D2C_BREAKOUT_FAKEOUT,
    SUBTYPE_D3A_TOP_GAP,
    SUBTYPE_D3B_DEPTH_EVAPORATION,
    SUBTYPE_D3C_SPREAD_SHOCK,
    SUBTYPE_D4A_EVENT_SPIKE,
    SUBTYPE_D4B_EVENT_AFTERSHOCK,
    SUBTYPE_D4C_EVENT_SILENCE,
    SUBTYPE_D5A_COUPLING_TIGHTEN,
    SUBTYPE_D5B_DECOUPLING,
    SUBTYPE_D5C_ROTATION_PRESSURE,
    D1_SUBTYPES,
    D2_SUBTYPES,
    D3_SUBTYPES,
    D4_SUBTYPES,
    D5_SUBTYPES,
    VALID_SUBTYPES,
)
from .v12_distortion_subtype_classifier_v1 import (
    classify_distortion_subtype_v1,
    get_distortion_subtype_classifier_v1_info,
)
from .v12_distortion_subtype_constitutional_guard import (
    check_distortion_subtype_record,
    check_subtype_coupling,
)

__all__ = [
    # PR129: Parent Distortion
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
    # PR134: Distortion Subtype
    "V12DistortionSubtypeSchema",
    "get_distortion_subtype_schema_info",
    "classify_distortion_subtype_v1",
    "get_distortion_subtype_classifier_v1_info",
    "check_distortion_subtype_record",
    "check_subtype_coupling",
    "SUBTYPE_D1A_FORCED_FLOW",
    "SUBTYPE_D1B_CASCADE_RISK",
    "SUBTYPE_D1C_STRESS_UNWIND",
    "SUBTYPE_D2A_MEAN_REVERT_PRESSURE",
    "SUBTYPE_D2B_RANGE_PINNING",
    "SUBTYPE_D2C_BREAKOUT_FAKEOUT",
    "SUBTYPE_D3A_TOP_GAP",
    "SUBTYPE_D3B_DEPTH_EVAPORATION",
    "SUBTYPE_D3C_SPREAD_SHOCK",
    "SUBTYPE_D4A_EVENT_SPIKE",
    "SUBTYPE_D4B_EVENT_AFTERSHOCK",
    "SUBTYPE_D4C_EVENT_SILENCE",
    "SUBTYPE_D5A_COUPLING_TIGHTEN",
    "SUBTYPE_D5B_DECOUPLING",
    "SUBTYPE_D5C_ROTATION_PRESSURE",
    "D1_SUBTYPES",
    "D2_SUBTYPES",
    "D3_SUBTYPES",
    "D4_SUBTYPES",
    "D5_SUBTYPES",
    "VALID_SUBTYPES",
]
