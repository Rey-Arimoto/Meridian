#!/usr/bin/env python3
"""
PR128: v1.2 Role × Distortion Eligibility Schema v1 (READ-ONLY)

Eligibility = "touchability classification" (not action, not recommendation).
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


# -----------------------------
# Enums (string literals)
# -----------------------------

ELIG_MODE_ON = "ON"
ELIG_MODE_OFF = "OFF"

ELIG_STATUS_AVAILABLE = "AVAILABLE"
ELIG_STATUS_ERROR = "ERROR"

ELIG_INELIGIBLE = "INELIGIBLE"
ELIG_ELIGIBLE_CONSIDERATION_ONLY = "ELIGIBLE_CONSIDERATION_ONLY"
ELIG_ELIGIBLE_DRY_RUN_ONLY = "ELIGIBLE_DRY_RUN_ONLY"

REGIME_LOW = "REGIME_LOW"
REGIME_MEDIUM = "REGIME_MEDIUM"
REGIME_HIGH = "REGIME_HIGH"
REGIME_CRITICAL = "REGIME_CRITICAL"
REGIME_UNCLASSIFIED = "UNCLASSIFIED"

ROLE_VOLATILITY = "VOLATILITY_ROLE"
ROLE_LIQUIDITY = "LIQUIDITY_ROLE"
ROLE_STABILITY = "STABILITY_ROLE"
ROLE_HEDGE = "HEDGE_ROLE"
ROLE_GAS = "GAS_ROLE"
ROLE_UNCLASSIFIED = "UNCLASSIFIED"

D1_LIQUIDATION = "D1_LIQUIDATION"
D2_RANGE_STICKINESS = "D2_RANGE_STICKINESS"
D3_BOOK_HOLLOWING = "D3_BOOK_HOLLOWING"
D4_EVENT_DISTORTION = "D4_EVENT_DISTORTION"
D5_CORRELATION_DISTORTION = "D5_CORRELATION_DISTORTION"
DISTORTION_UNCLASSIFIED = "UNCLASSIFIED"

# Boundary types (existing layer names; keep as strings)
BOUNDARY_SCHEMA = "SCHEMA_BOUNDARY"
BOUNDARY_DATA = "DATA_BOUNDARY"
BOUNDARY_ENGINE = "ENGINE_BOUNDARY"
BOUNDARY_TEMPORAL = "TEMPORAL_BOUNDARY"
BOUNDARY_SAMPLING = "SAMPLING_BOUNDARY"
BOUNDARY_UNCLASSIFIED = "UNCLASSIFIED"

# Permission monitor states (PR126)
SUPPRESSION_STABLE = "STABLE"
SUPPRESSION_DEGRADING = "DEGRADING"
SUPPRESSION_RECOVERING = "RECOVERING"
SUPPRESSION_SUPPRESSED = "SUPPRESSED"
SUPPRESSION_UNCLASSIFIED = "UNCLASSIFIED"


@dataclass
class V12RoleDistortionEligibilityRecord:
    v12_elig_mode: str = ELIG_MODE_ON
    v12_elig_status: str = ELIG_STATUS_AVAILABLE

    # Output label
    v12_elig_eligibility: str = ELIG_INELIGIBLE

    # Human-readable (non-prescriptive) summary
    v12_elig_summary: str = ""

    # Signals (labels only)
    v12_elig_signals: Dict[str, str] = None  # type: ignore

    # Provenance (field-name basis only)
    v12_elig_basis: List[str] = None  # type: ignore

    # Optional warnings (strings)
    v12_elig_warnings: List[str] = None  # type: ignore


def new_empty_eligibility_record() -> V12RoleDistortionEligibilityRecord:
    return V12RoleDistortionEligibilityRecord(
        v12_elig_mode=ELIG_MODE_ON,
        v12_elig_status=ELIG_STATUS_AVAILABLE,
        v12_elig_eligibility=ELIG_INELIGIBLE,
        v12_elig_summary="eligibility record available.",
        v12_elig_signals={},
        v12_elig_basis=[],
        v12_elig_warnings=[],
    )


def new_error_eligibility_record(reason: str) -> V12RoleDistortionEligibilityRecord:
    rec = new_empty_eligibility_record()
    rec.v12_elig_status = ELIG_STATUS_ERROR
    rec.v12_elig_eligibility = ELIG_INELIGIBLE
    rec.v12_elig_summary = "eligibility record error. defensive default applied."
    rec.v12_elig_warnings.append(reason[:240])
    return rec


def eligibility_record_to_dict(rec: V12RoleDistortionEligibilityRecord) -> Dict[str, Any]:
    return asdict(rec)


def get_eligibility_schema_info() -> Dict[str, Any]:
    return {
        "schema": "V12RoleDistortionEligibilityRecord",
        "version": "v1",
        "mode_values": [ELIG_MODE_ON, ELIG_MODE_OFF],
        "status_values": [ELIG_STATUS_AVAILABLE, ELIG_STATUS_ERROR],
        "eligibility_values": [
            ELIG_INELIGIBLE,
            ELIG_ELIGIBLE_CONSIDERATION_ONLY,
            ELIG_ELIGIBLE_DRY_RUN_ONLY,
        ],
    }
