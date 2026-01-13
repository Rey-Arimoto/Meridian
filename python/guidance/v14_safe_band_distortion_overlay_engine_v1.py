#!/usr/bin/env python3
"""
PR145: v1.4 Safe Band × Distortion Stress Overlay Engine v1 (READ-ONLY)

Purpose:
    Overlay static safe band guidance (PR144) with dynamic distortion signals (PR129/PR134).
    Output is a structural stress label for human understanding.
    This is NOT eligibility, NOT permission, NOT recommendation, NOT instruction.

API:
    build_safe_band_distortion_overlay_v1(artifact_bundle) -> dict

Behavior:
    - Extract required artifacts: regime_record, role_safe_band_guidance
    - Extract optional artifacts: distortion_catalog_record, distortion_subtype_record
    - Determine distortion_presence: NONE|PRESENT|MULTIPLE|UNKNOWN
    - Determine band_stress_label using deterministic rules
    - Generate non-prescriptive overlay_notes
    - Defensive: invalid input → valid ERROR record

Deterministic Rules:
    distortion_presence:
        - no distortion/empty → NONE
        - one distortion → PRESENT
        - multiple distortions → MULTIPLE
        - malformed → UNKNOWN

    band_stress_label (structural only; NOT action):
        - if regime CRITICAL → STRESSED
        - if regime HIGH and distortion present → STRESSED
        - if regime MEDIUM and distortion present → TENSE
        - if regime LOW and distortion present → TENSE
        - if distortion NONE → CALM
        - if safe_band_bucket is BAND_ZERO and distortion present → STRESSED
        - if safe_band_bucket is BAND_UNKNOWN → UNKNOWN
        - invalid inputs → ERROR or UNKNOWN (never raise)

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Non-prescriptive: No should/must/recommend
    - No trading verbs: No buy/sell/swap/execute
    - No token literals: No SUI/USDC/BTC/ETH
    - No numeric values in output text: Bucket labels only
    - No causal coupling: No therefore/so/hence
    - No eligibility coupling: No "eligible therefore"
    - Defensive: Invalid input → valid ERROR record
    - Warning-only: Never raises exceptions
"""

from typing import Any, Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from guidance.v14_safe_band_distortion_overlay_schema import (
    V14SafeBandDistortionOverlaySchema,
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


def _extract_distortion_info(artifact_bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract distortion information from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle with optional distortion artifacts

    Returns:
        Dict with distortion_presence and distortion_subtypes
    """
    distortion_presence = DISTORTION_PRESENCE_NONE
    distortion_subtypes = []
    warnings = []

    artifacts = artifact_bundle.get("artifacts", {})

    # Check for distortion catalog record (PR129)
    distortion_catalog = artifacts.get("distortion_catalog_record")
    if distortion_catalog and isinstance(distortion_catalog, dict):
        # Extract distortion entries
        distortion_records = distortion_catalog.get("v12_distortion_records", [])
        if isinstance(distortion_records, list) and len(distortion_records) > 0:
            if len(distortion_records) == 1:
                distortion_presence = DISTORTION_PRESENCE_PRESENT
            elif len(distortion_records) > 1:
                distortion_presence = DISTORTION_PRESENCE_MULTIPLE

            # Extract distortion identifiers (avoid leaking internal IDs)
            for idx, record in enumerate(distortion_records):
                if isinstance(record, dict):
                    # Use generic labels instead of raw IDs
                    subtype = record.get("distortion_subtype", f"DISTORTION_{idx+1}")
                    distortion_subtypes.append(subtype)

    # Check for distortion subtype record (PR134)
    distortion_subtype = artifacts.get("distortion_subtype_record")
    if distortion_subtype and isinstance(distortion_subtype, dict):
        # If we already found distortions in catalog, this confirms
        if distortion_presence == DISTORTION_PRESENCE_NONE:
            distortion_presence = DISTORTION_PRESENCE_PRESENT
            # Extract subtype label
            subtype_label = distortion_subtype.get("v13_distortion_subtype", "DISTORTION_SUBTYPE")
            distortion_subtypes.append(subtype_label)

    # Dedup distortion_subtypes
    distortion_subtypes = list(dict.fromkeys(distortion_subtypes))

    return {
        "distortion_presence": distortion_presence,
        "distortion_subtypes": distortion_subtypes,
        "warnings": warnings,
    }


def _determine_band_stress_label(
    regime_label: str,
    safe_band_bucket: str,
    distortion_presence: str,
) -> str:
    """
    Determine band stress label using deterministic rules.

    Args:
        regime_label: Regime label from regime record
        safe_band_bucket: Safe band bucket from PR144 guidance
        distortion_presence: Distortion presence state

    Returns:
        Band stress label: CALM | TENSE | STRESSED | UNKNOWN
    """
    # Rule: distortion UNKNOWN → UNKNOWN
    if distortion_presence == DISTORTION_PRESENCE_UNKNOWN:
        return BAND_STRESS_UNKNOWN

    # Rule: if regime CRITICAL → STRESSED (always, regardless of distortion)
    if regime_label == "REGIME_CRITICAL":
        return BAND_STRESS_STRESSED

    # Rule: distortion NONE → CALM (after checking CRITICAL)
    if distortion_presence == DISTORTION_PRESENCE_NONE:
        return BAND_STRESS_CALM

    # Rule: if safe_band_bucket is BAND_ZERO and distortion present → STRESSED (prioritize over regime)
    if safe_band_bucket == "BAND_ZERO" and distortion_presence in [DISTORTION_PRESENCE_PRESENT, DISTORTION_PRESENCE_MULTIPLE]:
        return BAND_STRESS_STRESSED

    # Rule: if regime HIGH and distortion present → STRESSED
    if regime_label == "REGIME_HIGH" and distortion_presence in [DISTORTION_PRESENCE_PRESENT, DISTORTION_PRESENCE_MULTIPLE]:
        return BAND_STRESS_STRESSED

    # Rule: if regime MEDIUM and distortion present → TENSE
    if regime_label == "REGIME_MEDIUM" and distortion_presence in [DISTORTION_PRESENCE_PRESENT, DISTORTION_PRESENCE_MULTIPLE]:
        return BAND_STRESS_TENSE

    # Rule: if regime LOW and distortion present → TENSE
    if regime_label == "REGIME_LOW" and distortion_presence in [DISTORTION_PRESENCE_PRESENT, DISTORTION_PRESENCE_MULTIPLE]:
        return BAND_STRESS_TENSE

    # Rule: if safe_band_bucket is BAND_UNKNOWN → UNKNOWN
    if safe_band_bucket == "BAND_UNKNOWN":
        return BAND_STRESS_UNKNOWN

    # Rule: if regime UNKNOWN → UNKNOWN
    if regime_label == "REGIME_UNKNOWN":
        return BAND_STRESS_UNKNOWN

    # Default: UNKNOWN (defensive)
    return BAND_STRESS_UNKNOWN


def _create_overlay_notes(
    band_stress_label: str,
    distortion_presence: str,
    safe_band_bucket: str,
) -> List[str]:
    """
    Create non-prescriptive overlay notes.

    Args:
        band_stress_label: Band stress label
        distortion_presence: Distortion presence state
        safe_band_bucket: Safe band bucket

    Returns:
        List of overlay notes
    """
    notes = []

    if band_stress_label == BAND_STRESS_CALM:
        notes.append("allocation within safe band with no distortion signals detected indicates structural calm.")
    elif band_stress_label == BAND_STRESS_TENSE:
        notes.append("allocation within safe band but distortion signal present indicates structural tension.")
    elif band_stress_label == BAND_STRESS_STRESSED:
        if distortion_presence in [DISTORTION_PRESENCE_PRESENT, DISTORTION_PRESENCE_MULTIPLE]:
            notes.append("allocation combined with distortion signal in constrained regime indicates structural stress.")
        else:
            notes.append("regime constraints indicate structural stress state.")
    else:
        notes.append("structural stress state could not be determined from available inputs.")

    return notes


def build_safe_band_distortion_overlay_v1(
    artifact_bundle: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build safe band × distortion stress overlay record (READ-ONLY).

    Args:
        artifact_bundle: Artifact bundle with:
            - Required: regime_record, role_safe_band_guidance
            - Optional: distortion_catalog_record, distortion_subtype_record

    Returns:
        Dict with:
        - overlay_record: PR145-compliant overlay record
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid artifact_bundle
    if artifact_bundle is None or not isinstance(artifact_bundle, dict):
        warnings.append("invalid artifact_bundle (expected dict, got None or non-dict)")
        error_record = V14SafeBandDistortionOverlaySchema.create_error_record(
            summary="safe band distortion overlay generation failed: invalid artifact bundle."
        )
        return {
            "overlay_record": error_record,
            "warnings": warnings,
        }

    artifacts = artifact_bundle.get("artifacts", {})
    if not isinstance(artifacts, dict):
        warnings.append("invalid artifacts in bundle (expected dict)")
        error_record = V14SafeBandDistortionOverlaySchema.create_error_record(
            summary="safe band distortion overlay generation failed: invalid artifacts dict."
        )
        return {
            "overlay_record": error_record,
            "warnings": warnings,
        }

    # Track input presence
    inputs_present = {
        "regime_record": False,
        "role_safe_band_guidance": False,
        "distortion_catalog_record": False,
        "distortion_subtype_record": False,
    }

    # Extract regime_record (required)
    regime_record = artifacts.get("regime_record")
    if regime_record and isinstance(regime_record, dict):
        inputs_present["regime_record"] = True
    else:
        warnings.append("missing or invalid regime_record in artifact bundle")
        error_record = V14SafeBandDistortionOverlaySchema.create_error_record(
            summary="safe band distortion overlay generation failed: missing regime record."
        )
        return {
            "overlay_record": error_record,
            "warnings": warnings,
        }

    # Extract role_safe_band_guidance (required)
    role_safe_band_guidance = artifacts.get("role_safe_band_guidance")
    if role_safe_band_guidance and isinstance(role_safe_band_guidance, dict):
        inputs_present["role_safe_band_guidance"] = True
    else:
        warnings.append("missing or invalid role_safe_band_guidance in artifact bundle")
        error_record = V14SafeBandDistortionOverlaySchema.create_error_record(
            summary="safe band distortion overlay generation failed: missing safe band guidance."
        )
        return {
            "overlay_record": error_record,
            "warnings": warnings,
        }

    # Check for optional distortion artifacts
    if artifacts.get("distortion_catalog_record"):
        inputs_present["distortion_catalog_record"] = True

    if artifacts.get("distortion_subtype_record"):
        inputs_present["distortion_subtype_record"] = True

    # Extract regime label
    regime_label = regime_record.get("v11_regime_level", "REGIME_UNKNOWN")

    # Extract role type and safe band bucket from guidance
    # Guidance contains multiple roles, we need to select one role
    # For simplicity, use the first role found (or user can specify which role)
    # Let's extract VOLATILITY_ROLE as default for this overlay
    guidance_roles = role_safe_band_guidance.get("v14_guidance_roles", {})

    # Default to first role if available
    role_type = "ROLE_UNKNOWN"
    safe_band_bucket = "BAND_UNKNOWN"

    if isinstance(guidance_roles, dict) and len(guidance_roles) > 0:
        # Use first role
        first_role = list(guidance_roles.keys())[0]
        role_type = first_role
        role_entry = guidance_roles[first_role]
        if isinstance(role_entry, dict):
            safe_band_bucket = role_entry.get("safe_band_bucket", "BAND_UNKNOWN")

    # Extract distortion information
    distortion_info = _extract_distortion_info(artifact_bundle)
    distortion_presence = distortion_info["distortion_presence"]
    distortion_subtypes = distortion_info["distortion_subtypes"]
    warnings.extend(distortion_info["warnings"])

    # Determine band stress label
    band_stress_label = _determine_band_stress_label(
        regime_label=regime_label,
        safe_band_bucket=safe_band_bucket,
        distortion_presence=distortion_presence,
    )

    # Create overlay notes
    overlay_notes = _create_overlay_notes(
        band_stress_label=band_stress_label,
        distortion_presence=distortion_presence,
        safe_band_bucket=safe_band_bucket,
    )

    # Create overlay record
    overlay_summary = "safe band distortion overlay assembled for structural stress state."
    overlay_record = V14SafeBandDistortionOverlaySchema.create_overlay_record(
        version=OVERLAY_VERSION_V1_0,
        status=OVERLAY_STATUS_AVAILABLE,
        mode=OVERLAY_MODE_READ_ONLY,
        summary=overlay_summary,
        inputs_present=inputs_present,
        regime_label=regime_label,
        role_type=role_type,
        safe_band_bucket=safe_band_bucket,
        distortion_presence=distortion_presence,
        distortion_subtypes=distortion_subtypes,
        band_stress_label=band_stress_label,
        overlay_notes=overlay_notes,
        basis=["REGIME_LABEL_USED", "SAFE_BAND_GUIDANCE_USED", "DISTORTION_SIGNALS_CHECKED"],
        artifacts=list(inputs_present.keys()),
        warnings=warnings,
    )

    # Validate schema
    schema_errors = V14SafeBandDistortionOverlaySchema.validate_overlay_record(overlay_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    # Add warnings to overlay record
    overlay_record["v14_overlay_warnings"] = warnings

    return {
        "overlay_record": overlay_record,
        "warnings": warnings,
    }


def get_overlay_engine_v1_info() -> Dict[str, Any]:
    """
    Get overlay engine information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "safe_band_distortion_overlay",
        "philosophy": "Overlay static safe band guidance with dynamic distortion signals. Describe structural stress state only.",
        "input_formats": [
            "artifact_bundle (regime_record, role_safe_band_guidance, optional distortion artifacts)",
        ],
        "output_format": "safe_band_distortion_overlay (PR145)",
        "deterministic_rules": [
            "distortion_presence: NONE|PRESENT|MULTIPLE|UNKNOWN",
            "band_stress_label: CALM|TENSE|STRESSED|UNKNOWN",
            "regime CRITICAL → STRESSED",
            "regime HIGH + distortion → STRESSED",
            "regime MEDIUM + distortion → TENSE",
            "regime LOW + distortion → TENSE",
            "distortion NONE → CALM",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "bucket_output_only",
            "no_causal_coupling",
            "no_eligibility_coupling",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Safe Band × Distortion Overlay Engine - Self Test")
    print("=" * 60)
    print()

    # Test 1: Valid inputs (MEDIUM regime, distortion PRESENT)
    print("Test 1: Valid inputs (MEDIUM regime, distortion PRESENT)")
    test_bundle = {
        "artifacts": {
            "regime_record": {
                "v11_regime_level": "REGIME_MEDIUM",
            },
            "role_safe_band_guidance": {
                "v14_guidance_roles": {
                    "VOLATILITY_ROLE": {
                        "safe_band_bucket": "BAND_MEDIUM",
                    }
                }
            },
            "distortion_catalog_record": {
                "v12_distortion_records": [
                    {"distortion_subtype": "SUBTYPE_A"}
                ]
            },
        }
    }

    result1 = build_safe_band_distortion_overlay_v1(test_bundle)
    print(f"Overlay status: {result1['overlay_record']['v14_overlay_status']}")
    print(f"Band stress label: {result1['overlay_record']['v14_overlay_band_stress_label']}")
    print(f"Distortion presence: {result1['overlay_record']['v14_overlay_distortion_presence']}")
    print(f"Warnings: {len(result1['warnings'])}")
    print()

    # Test 2: Invalid inputs (defensive)
    print("Test 2: Invalid inputs (defensive)")
    result2 = build_safe_band_distortion_overlay_v1(None)
    print(f"Overlay status: {result2['overlay_record']['v14_overlay_status']}")
    print(f"Warnings: {len(result2['warnings'])}")
    print()

    # Test 3: CALM state (no distortion)
    print("Test 3: CALM state (no distortion)")
    test_bundle_calm = {
        "artifacts": {
            "regime_record": {
                "v11_regime_level": "REGIME_MEDIUM",
            },
            "role_safe_band_guidance": {
                "v14_guidance_roles": {
                    "VOLATILITY_ROLE": {
                        "safe_band_bucket": "BAND_MEDIUM",
                    }
                }
            },
        }
    }

    result3 = build_safe_band_distortion_overlay_v1(test_bundle_calm)
    print(f"Overlay status: {result3['overlay_record']['v14_overlay_status']}")
    print(f"Band stress label: {result3['overlay_record']['v14_overlay_band_stress_label']}")
    print(f"Distortion presence: {result3['overlay_record']['v14_overlay_distortion_presence']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
