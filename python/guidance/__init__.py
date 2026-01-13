#!/usr/bin/env python3
"""
PR144-PR145: v1.4 Role Safe Band Guidance + Overlay (READ-ONLY)

Purpose:
    Build role safe band guidance from portfolio snapshot and regime record.
    Overlay static guidance with dynamic distortion signals for stress state.
    This is NOT advice, NOT instruction, NOT recommendation.

Exports:
    PR144 - Role Safe Band Guidance:
    - V14RoleSafeBandSchema: Guidance schema class
    - get_safe_band_schema_info: Schema metadata
    - Version/status/mode constants
    - Band bucket constants (BAND_*)
    - Ratio bucket constants (RATIO_*)
    - Role status constants (STATUS_*)
    - Role constants (ROLE_*)
    - Regime constants (REGIME_*)
    - build_role_safe_band_guidance_v1: Build guidance from portfolio + regime
    - get_safe_band_engine_v1_info: Engine metadata
    - check_guidance_record: Guidance record guard

    PR145 - Safe Band × Distortion Overlay:
    - V14SafeBandDistortionOverlaySchema: Overlay schema class
    - get_overlay_schema_info: Overlay schema metadata
    - Overlay version/status/mode constants
    - Distortion presence constants (DISTORTION_PRESENCE_*)
    - Band stress label constants (BAND_STRESS_*)
    - build_safe_band_distortion_overlay_v1: Build overlay from artifact bundle
    - get_overlay_engine_v1_info: Overlay engine metadata
    - check_overlay_record: Overlay record guard
    - check_eligibility_coupling: Eligibility coupling guard

    Constitutional Guards:
    - check_forbidden_vocabulary: Vocabulary guard
    - check_token_literals: Token literal guard
    - check_address_patterns: Address pattern guard
    - check_coupling_phrases: Coupling phrase guard
    - check_numeric_patterns: Numeric pattern guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

from .v14_role_safe_band_schema import (
    V14RoleSafeBandSchema,
    get_safe_band_schema_info,
    GUIDANCE_VERSION_V1_4,
    GUIDANCE_STATUS_AVAILABLE,
    GUIDANCE_STATUS_ERROR,
    GUIDANCE_MODE_READ_ONLY,
    BAND_ZERO,
    BAND_MINIMAL,
    BAND_LOW,
    BAND_MEDIUM,
    BAND_HIGH,
    BAND_MAXIMAL,
    BAND_UNKNOWN,
    RATIO_ZERO,
    RATIO_MINIMAL,
    RATIO_LOW,
    RATIO_MEDIUM,
    RATIO_HIGH,
    RATIO_MAXIMAL,
    RATIO_UNKNOWN,
    STATUS_BELOW_SAFE,
    STATUS_WITHIN_SAFE,
    STATUS_ABOVE_SAFE,
    STATUS_UNKNOWN,
    ROLE_VOLATILITY,
    ROLE_LIQUIDITY,
    ROLE_STABILITY,
    ROLE_HEDGE,
    ROLE_GAS,
    REGIME_LOW,
    REGIME_MEDIUM,
    REGIME_HIGH,
    REGIME_CRITICAL,
    REGIME_UNKNOWN,
)
from .v14_role_safe_band_engine_v1 import (
    build_role_safe_band_guidance_v1,
    get_safe_band_engine_v1_info,
)
from .v14_guidance_constitutional_guard import (
    check_guidance_record,
    check_forbidden_vocabulary,
    check_token_literals,
    check_address_patterns,
    check_coupling_phrases,
    check_numeric_patterns,
    FORBIDDEN_VOCABULARY,
)
from .v14_safe_band_distortion_overlay_schema import (
    V14SafeBandDistortionOverlaySchema,
    get_overlay_schema_info,
    OVERLAY_VERSION_V1_0,
    OVERLAY_STATUS_AVAILABLE,
    OVERLAY_STATUS_ERROR,
    OVERLAY_MODE_READ_ONLY,
    DISTORTION_PRESENCE_NONE,
    DISTORTION_PRESENCE_PRESENT,
    DISTORTION_PRESENCE_MULTIPLE,
    DISTORTION_PRESENCE_UNKNOWN,
    BAND_STRESS_CALM,
    BAND_STRESS_TENSE,
    BAND_STRESS_STRESSED,
    BAND_STRESS_UNKNOWN,
)
from .v14_safe_band_distortion_overlay_engine_v1 import (
    build_safe_band_distortion_overlay_v1,
    get_overlay_engine_v1_info,
)
from .v14_overlay_constitutional_guard import (
    check_overlay_record,
    check_eligibility_coupling,
)

__all__ = [
    # PR144 - Role Safe Band Guidance Schema
    "V14RoleSafeBandSchema",
    "get_safe_band_schema_info",
    "GUIDANCE_VERSION_V1_4",
    "GUIDANCE_STATUS_AVAILABLE",
    "GUIDANCE_STATUS_ERROR",
    "GUIDANCE_MODE_READ_ONLY",
    # Band buckets
    "BAND_ZERO",
    "BAND_MINIMAL",
    "BAND_LOW",
    "BAND_MEDIUM",
    "BAND_HIGH",
    "BAND_MAXIMAL",
    "BAND_UNKNOWN",
    # Ratio buckets
    "RATIO_ZERO",
    "RATIO_MINIMAL",
    "RATIO_LOW",
    "RATIO_MEDIUM",
    "RATIO_HIGH",
    "RATIO_MAXIMAL",
    "RATIO_UNKNOWN",
    # Role statuses
    "STATUS_BELOW_SAFE",
    "STATUS_WITHIN_SAFE",
    "STATUS_ABOVE_SAFE",
    "STATUS_UNKNOWN",
    # Roles
    "ROLE_VOLATILITY",
    "ROLE_LIQUIDITY",
    "ROLE_STABILITY",
    "ROLE_HEDGE",
    "ROLE_GAS",
    # Regimes
    "REGIME_LOW",
    "REGIME_MEDIUM",
    "REGIME_HIGH",
    "REGIME_CRITICAL",
    "REGIME_UNKNOWN",
    # PR144 - Engine
    "build_role_safe_band_guidance_v1",
    "get_safe_band_engine_v1_info",
    # PR145 - Safe Band × Distortion Overlay Schema
    "V14SafeBandDistortionOverlaySchema",
    "get_overlay_schema_info",
    "OVERLAY_VERSION_V1_0",
    "OVERLAY_STATUS_AVAILABLE",
    "OVERLAY_STATUS_ERROR",
    "OVERLAY_MODE_READ_ONLY",
    # Distortion presence
    "DISTORTION_PRESENCE_NONE",
    "DISTORTION_PRESENCE_PRESENT",
    "DISTORTION_PRESENCE_MULTIPLE",
    "DISTORTION_PRESENCE_UNKNOWN",
    # Band stress labels
    "BAND_STRESS_CALM",
    "BAND_STRESS_TENSE",
    "BAND_STRESS_STRESSED",
    "BAND_STRESS_UNKNOWN",
    # PR145 - Engine
    "build_safe_band_distortion_overlay_v1",
    "get_overlay_engine_v1_info",
    # Constitutional Guards
    "check_guidance_record",
    "check_overlay_record",
    "check_forbidden_vocabulary",
    "check_token_literals",
    "check_address_patterns",
    "check_coupling_phrases",
    "check_eligibility_coupling",
    "check_numeric_patterns",
    "FORBIDDEN_VOCABULARY",
]
