#!/usr/bin/env python3
"""
PR128: v1.2 Role × Distortion Eligibility Engine v1 (READ-ONLY)

Rules (static, no learning):
- CRITICAL -> INELIGIBLE
- Hard boundary types (SCHEMA/DATA/ENGINE) -> INELIGIBLE
- SUPPRESSED -> INELIGIBLE
- HIGH -> DRY_RUN_ONLY
- LOW -> DRY_RUN_ONLY
- MEDIUM:
    - VOLATILITY_ROLE + defined distortion (D1..D5) -> CONSIDERATION_ONLY
    - else -> DRY_RUN_ONLY

Eligibility ≠ Action. Output is a label only.
"""

from __future__ import annotations
from typing import Any, Dict, Optional

from .v12_role_distortion_eligibility_schema import (
    V12RoleDistortionEligibilityRecord,
    new_empty_eligibility_record,
    new_error_eligibility_record,
    ELIG_INELIGIBLE,
    ELIG_ELIGIBLE_CONSIDERATION_ONLY,
    ELIG_ELIGIBLE_DRY_RUN_ONLY,
    REGIME_CRITICAL,
    REGIME_HIGH,
    REGIME_LOW,
    REGIME_MEDIUM,
    ROLE_VOLATILITY,
    D1_LIQUIDATION,
    D2_RANGE_STICKINESS,
    D3_BOOK_HOLLOWING,
    D4_EVENT_DISTORTION,
    D5_CORRELATION_DISTORTION,
    BOUNDARY_SCHEMA,
    BOUNDARY_DATA,
    BOUNDARY_ENGINE,
    SUPPRESSION_SUPPRESSED,
)

_DEFINED_DISTORTIONS = {
    D1_LIQUIDATION,
    D2_RANGE_STICKINESS,
    D3_BOOK_HOLLOWING,
    D4_EVENT_DISTORTION,
    D5_CORRELATION_DISTORTION,
}

_HARD_BOUNDARIES = {BOUNDARY_SCHEMA, BOUNDARY_DATA, BOUNDARY_ENGINE}


def _safe_get(d: Optional[Dict[str, Any]], key: str, default: str = "UNCLASSIFIED") -> str:
    if not isinstance(d, dict):
        return default
    v = d.get(key, default)
    return v if isinstance(v, str) and v else default


def classify_role_distortion_eligibility_v1(
    regime_record: Optional[Dict[str, Any]],
    distortion_record: Optional[Dict[str, Any]],
    role_record: Optional[Dict[str, Any]],
    boundary_record: Optional[Dict[str, Any]] = None,
    permission_monitor_record: Optional[Dict[str, Any]] = None,
    policy_record: Optional[Dict[str, Any]] = None,
) -> V12RoleDistortionEligibilityRecord:
    try:
        rec = new_empty_eligibility_record()

        # Extract labels (best-effort, no assumptions about upstream schema)
        regime_level = _safe_get(regime_record, "v11_regime_level", _safe_get(regime_record, "regime", "UNCLASSIFIED"))
        distortion_type = _safe_get(distortion_record, "v12_distortion_type", _safe_get(distortion_record, "distortion", "UNCLASSIFIED"))
        role_type = _safe_get(role_record, "v12_role_type", _safe_get(role_record, "role", "UNCLASSIFIED"))

        boundary_type = _safe_get(boundary_record, "v9_boundary_type", _safe_get(boundary_record, "boundary", "UNCLASSIFIED"))

        suppression_state = _safe_get(permission_monitor_record, "v12_monitor_suppression_state", _safe_get(permission_monitor_record, "suppression", "UNCLASSIFIED"))

        # Signals
        rec.v12_elig_signals = {
            "regime": regime_level,
            "distortion": distortion_type,
            "role": role_type,
            "boundary": boundary_type,
            "suppression": suppression_state,
        }

        # Basis (field names only)
        rec.v12_elig_basis = [
            "v11_regime_level",
            "v12_distortion_type",
            "v12_role_type",
            "v9_boundary_type",
            "v12_monitor_suppression_state",
        ]

        # -----------------------------
        # Hard stop (first match wins)
        # -----------------------------
        if regime_level == REGIME_CRITICAL:
            rec.v12_elig_eligibility = ELIG_INELIGIBLE
            rec.v12_elig_summary = "eligibility label indicates ineligible under critical regime."
            return rec

        if boundary_type in _HARD_BOUNDARIES:
            rec.v12_elig_eligibility = ELIG_INELIGIBLE
            rec.v12_elig_summary = "eligibility label indicates ineligible under hard boundary type."
            return rec

        if suppression_state == SUPPRESSION_SUPPRESSED:
            rec.v12_elig_eligibility = ELIG_INELIGIBLE
            rec.v12_elig_summary = "eligibility label indicates ineligible under suppressed permission trajectory."
            return rec

        # -----------------------------
        # Regime gating
        # -----------------------------
        if regime_level == REGIME_HIGH:
            rec.v12_elig_eligibility = ELIG_ELIGIBLE_DRY_RUN_ONLY
            rec.v12_elig_summary = "eligibility label indicates dry-run-only under high regime."
            return rec

        if regime_level == REGIME_LOW:
            rec.v12_elig_eligibility = ELIG_ELIGIBLE_DRY_RUN_ONLY
            rec.v12_elig_summary = "eligibility label indicates dry-run-only under low regime."
            return rec

        # -----------------------------
        # Medium: the only consideration zone
        # -----------------------------
        if regime_level == REGIME_MEDIUM:
            if (role_type == ROLE_VOLATILITY) and (distortion_type in _DEFINED_DISTORTIONS):
                rec.v12_elig_eligibility = ELIG_ELIGIBLE_CONSIDERATION_ONLY
                rec.v12_elig_summary = "eligibility label indicates consideration-only under medium regime with volatility role and defined distortion."
                return rec

            rec.v12_elig_eligibility = ELIG_ELIGIBLE_DRY_RUN_ONLY
            rec.v12_elig_summary = "eligibility label indicates dry-run-only under medium regime without volatility-role plus defined-distortion alignment."
            return rec

        # Default: unknown/unclassified regime
        rec.v12_elig_eligibility = ELIG_ELIGIBLE_DRY_RUN_ONLY
        rec.v12_elig_summary = "eligibility label indicates dry-run-only under unclassified regime label."
        return rec

    except Exception as e:
        return new_error_eligibility_record(f"exception: {type(e).__name__}")
