#!/usr/bin/env python3
"""
PR146: v1.4 Stress Engine v1 (READ-ONLY)

Purpose:
    Build stress label from inputs or artifact bundle.
    Uses fixed table lookup (table-first approach).

API:
    build_stress_label_from_inputs_v1(regime_label, band_bucket, distortion_presence) -> dict
    build_stress_label_from_bundle_v1(artifact_bundle) -> dict

Bundle Interpretation:
    - regime_record (v11): Extract regime label
    - safe_band_guidance (PR144): Extract band bucket (use "worst bucket" across roles)
    - distortion_catalog_record (v12): Extract distortion presence

Worst Bucket Priority:
    OUTSIDE > EDGE > SAFE > UNKNOWN

Distortion Presence:
    - Empty list → NONE
    - Non-empty list → PRESENT
    - Missing/invalid → UNKNOWN

Band Bucket Mapping (PR144 → simplified):
    - BAND_ZERO → OUTSIDE (most constrained)
    - BAND_MINIMAL → EDGE
    - BAND_LOW → SAFE
    - BAND_MEDIUM → SAFE
    - BAND_HIGH → SAFE
    - BAND_MAXIMAL → EDGE
    - BAND_UNKNOWN → UNKNOWN

    Or use STATUS field:
    - STATUS_BELOW_SAFE → OUTSIDE
    - STATUS_WITHIN_SAFE → SAFE
    - STATUS_ABOVE_SAFE → EDGE
    - STATUS_UNKNOWN → UNKNOWN

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Label-only extraction: No numeric values
    - Defensive: Invalid input → valid ERROR record
    - Warning-only: Never raises exceptions
"""

from typing import Any, Dict, List, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stress.v14_stress_rule_table_schema import (
    V14StressRuleTableSchema,
    STRESS_VERSION_V1,
    STRESS_STATUS_AVAILABLE,
    STRESS_STATUS_ERROR,
    STRESS_MODE_READ_ONLY,
    STRESS_CALM,
    STRESS_TENSE,
    STRESS_STRESSED,
    STRESS_UNKNOWN,
    BAND_SAFE,
    BAND_EDGE,
    BAND_OUTSIDE,
    BAND_UNKNOWN,
    DIST_NONE,
    DIST_PRESENT,
    DIST_UNKNOWN,
    REGIME_LOW,
    REGIME_MEDIUM,
    REGIME_HIGH,
    REGIME_CRITICAL,
    REGIME_UNKNOWN,
)
from stress.v14_stress_rule_table_v1 import (
    lookup_stress_label_v1,
)


# Band bucket mapping priority for "worst bucket" logic
BAND_BUCKET_PRIORITY = {
    BAND_OUTSIDE: 4,
    BAND_EDGE: 3,
    BAND_SAFE: 2,
    BAND_UNKNOWN: 1,
}


def _map_pr144_bucket_to_simplified(pr144_bucket: str) -> str:
    """
    Map PR144 band bucket to simplified bucket.

    Args:
        pr144_bucket: PR144 band bucket (BAND_ZERO, BAND_MINIMAL, etc.)

    Returns:
        Simplified bucket: SAFE | EDGE | OUTSIDE | UNKNOWN
    """
    # Mapping from PR144 buckets to simplified buckets
    mapping = {
        "BAND_ZERO": BAND_OUTSIDE,       # 0-1% (most constrained)
        "BAND_MINIMAL": BAND_EDGE,        # 1-10%
        "BAND_LOW": BAND_SAFE,            # 10-25%
        "BAND_MEDIUM": BAND_SAFE,         # 25-50%
        "BAND_HIGH": BAND_SAFE,           # 50-75%
        "BAND_MAXIMAL": BAND_EDGE,        # 75-100%
        "BAND_UNKNOWN": BAND_UNKNOWN,
    }

    return mapping.get(pr144_bucket, BAND_UNKNOWN)


def _map_pr144_status_to_simplified(pr144_status: str) -> str:
    """
    Map PR144 status to simplified bucket.

    Args:
        pr144_status: PR144 status (STATUS_BELOW_SAFE, STATUS_WITHIN_SAFE, etc.)

    Returns:
        Simplified bucket: SAFE | EDGE | OUTSIDE | UNKNOWN
    """
    # Mapping from PR144 status to simplified buckets
    mapping = {
        "BELOW_SAFE": BAND_OUTSIDE,
        "WITHIN_SAFE": BAND_SAFE,
        "ABOVE_SAFE": BAND_EDGE,
        "UNKNOWN": BAND_UNKNOWN,
    }

    return mapping.get(pr144_status, BAND_UNKNOWN)


def _get_worst_bucket(buckets: List[str]) -> str:
    """
    Get worst bucket from list using priority.

    Args:
        buckets: List of bucket labels

    Returns:
        Worst bucket (highest priority)
    """
    if not buckets:
        return BAND_UNKNOWN

    # Sort by priority (highest first)
    sorted_buckets = sorted(buckets, key=lambda b: BAND_BUCKET_PRIORITY.get(b, 0), reverse=True)
    return sorted_buckets[0]


def _extract_regime_label_from_bundle(artifact_bundle: Dict[str, Any]) -> tuple[str, List[str]]:
    """
    Extract regime label from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle

    Returns:
        Tuple of (regime_label, warnings)
    """
    warnings = []

    artifacts = artifact_bundle.get("artifacts", {})
    regime_record = artifacts.get("regime_record")

    if not regime_record or not isinstance(regime_record, dict):
        warnings.append("missing or invalid regime_record in bundle")
        return (REGIME_UNKNOWN, warnings)

    # Extract regime label
    regime_label = regime_record.get("v11_regime_level", REGIME_UNKNOWN)

    return (regime_label, warnings)


def _extract_band_bucket_from_bundle(artifact_bundle: Dict[str, Any]) -> tuple[str, List[str]]:
    """
    Extract band bucket from artifact bundle (use worst bucket across roles).

    Args:
        artifact_bundle: Artifact bundle

    Returns:
        Tuple of (band_bucket, warnings)
    """
    warnings = []

    artifacts = artifact_bundle.get("artifacts", {})
    safe_band_guidance = artifacts.get("role_safe_band_guidance")

    if not safe_band_guidance or not isinstance(safe_band_guidance, dict):
        warnings.append("missing or invalid role_safe_band_guidance in bundle")
        return (BAND_UNKNOWN, warnings)

    # Extract roles
    guidance_roles = safe_band_guidance.get("v14_guidance_roles", {})

    if not isinstance(guidance_roles, dict) or len(guidance_roles) == 0:
        warnings.append("no roles found in safe_band_guidance")
        return (BAND_UNKNOWN, warnings)

    # Collect buckets across all roles (use status field as primary)
    buckets = []
    for role_name, role_entry in guidance_roles.items():
        if not isinstance(role_entry, dict):
            continue

        # Try status field first (more direct)
        status = role_entry.get("status")
        if status:
            bucket = _map_pr144_status_to_simplified(status)
            buckets.append(bucket)
        else:
            # Fallback to safe_band_bucket field
            safe_band_bucket = role_entry.get("safe_band_bucket")
            if safe_band_bucket:
                bucket = _map_pr144_bucket_to_simplified(safe_band_bucket)
                buckets.append(bucket)

    if not buckets:
        warnings.append("no valid buckets extracted from roles")
        return (BAND_UNKNOWN, warnings)

    # Get worst bucket
    worst_bucket = _get_worst_bucket(buckets)

    return (worst_bucket, warnings)


def _extract_distortion_presence_from_bundle(artifact_bundle: Dict[str, Any]) -> tuple[str, List[str]]:
    """
    Extract distortion presence from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle

    Returns:
        Tuple of (distortion_presence, warnings)
    """
    warnings = []

    artifacts = artifact_bundle.get("artifacts", {})
    distortion_catalog = artifacts.get("distortion_catalog_record")

    if not distortion_catalog or not isinstance(distortion_catalog, dict):
        # No distortion catalog → NONE
        return (DIST_NONE, warnings)

    # Extract distortion records
    distortion_records = distortion_catalog.get("v12_distortion_records", [])

    if not isinstance(distortion_records, list):
        warnings.append("invalid distortion_records format")
        return (DIST_UNKNOWN, warnings)

    # Check if list is empty or non-empty
    if len(distortion_records) == 0:
        return (DIST_NONE, warnings)
    else:
        return (DIST_PRESENT, warnings)


def build_stress_label_from_inputs_v1(
    regime_label: str,
    band_bucket: str,
    distortion_presence: str,
) -> Dict[str, Any]:
    """
    Build stress label from direct inputs.

    Args:
        regime_label: Regime label (REGIME_LOW | REGIME_MEDIUM | REGIME_HIGH | REGIME_CRITICAL | REGIME_UNKNOWN)
        band_bucket: Band bucket (SAFE | EDGE | OUTSIDE | UNKNOWN)
        distortion_presence: Distortion presence (NONE | PRESENT | UNKNOWN)

    Returns:
        Dict with:
        - stress_record: PR146-compliant stress record
        - warnings: List of warnings
    """
    warnings = []

    # Lookup stress label from table
    stress_label, basis_labels, lookup_warnings = lookup_stress_label_v1(
        regime_label=regime_label,
        band_bucket=band_bucket,
        distortion_presence=distortion_presence,
    )

    warnings.extend(lookup_warnings)

    # Create stress record
    stress_summary = "stress label determined from fixed table."
    stress_record = V14StressRuleTableSchema.create_stress_record(
        version=STRESS_VERSION_V1,
        status=STRESS_STATUS_AVAILABLE,
        mode=STRESS_MODE_READ_ONLY,
        summary=stress_summary,
        inputs={
            "regime_label": regime_label,
            "band_bucket": band_bucket,
            "distortion_presence": distortion_presence,
        },
        stress_label=stress_label,
        basis=basis_labels,
        artifacts=["TABLE_LOOKUP_V1"],
        warnings=warnings,
    )

    # Validate schema
    schema_errors = V14StressRuleTableSchema.validate_stress_record(stress_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    # Add warnings to stress record
    stress_record["v14_stress_warnings"] = warnings

    return {
        "stress_record": stress_record,
        "warnings": warnings,
    }


def build_stress_label_from_bundle_v1(
    artifact_bundle: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build stress label from artifact bundle.

    Args:
        artifact_bundle: Artifact bundle with regime_record, safe_band_guidance, optional distortion_catalog

    Returns:
        Dict with:
        - stress_record: PR146-compliant stress record
        - warnings: List of warnings
    """
    warnings = []

    # Defensive: Handle invalid artifact_bundle
    if artifact_bundle is None or not isinstance(artifact_bundle, dict):
        warnings.append("invalid artifact_bundle (expected dict, got None or non-dict)")
        error_record = V14StressRuleTableSchema.create_error_record(
            summary="stress label determination failed: invalid artifact bundle."
        )
        return {
            "stress_record": error_record,
            "warnings": warnings,
        }

    # Extract inputs from bundle
    regime_label, regime_warnings = _extract_regime_label_from_bundle(artifact_bundle)
    warnings.extend(regime_warnings)

    band_bucket, band_warnings = _extract_band_bucket_from_bundle(artifact_bundle)
    warnings.extend(band_warnings)

    distortion_presence, distortion_warnings = _extract_distortion_presence_from_bundle(artifact_bundle)
    warnings.extend(distortion_warnings)

    # Track component presence
    components_present = {
        "regime_record": regime_label != REGIME_UNKNOWN,
        "safe_band_guidance": band_bucket != BAND_UNKNOWN,
        "distortion_catalog": distortion_presence != DIST_UNKNOWN,
    }

    # Lookup stress label from table
    stress_label, basis_labels, lookup_warnings = lookup_stress_label_v1(
        regime_label=regime_label,
        band_bucket=band_bucket,
        distortion_presence=distortion_presence,
    )

    warnings.extend(lookup_warnings)

    # Create stress record
    stress_summary = "stress label determined from artifact bundle via fixed table."
    stress_record = V14StressRuleTableSchema.create_stress_record(
        version=STRESS_VERSION_V1,
        status=STRESS_STATUS_AVAILABLE,
        mode=STRESS_MODE_READ_ONLY,
        summary=stress_summary,
        inputs={
            "regime_label": regime_label,
            "band_bucket": band_bucket,
            "distortion_presence": distortion_presence,
        },
        stress_label=stress_label,
        basis=basis_labels,
        artifacts=["regime_record", "safe_band_guidance", "distortion_catalog", "TABLE_LOOKUP_V1"],
        warnings=warnings,
        components_present=components_present,
    )

    # Validate schema
    schema_errors = V14StressRuleTableSchema.validate_stress_record(stress_record)
    if schema_errors:
        warnings.extend([f"schema validation: {e}" for e in schema_errors])

    # Add warnings to stress record
    stress_record["v14_stress_warnings"] = warnings

    return {
        "stress_record": stress_record,
        "warnings": warnings,
    }


def get_stress_engine_v1_info() -> Dict[str, Any]:
    """
    Get stress engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "stress_rule_table",
        "philosophy": "Table-first approach. Stress = structural load state (not action).",
        "input_formats": [
            "Direct inputs: regime_label, band_bucket, distortion_presence",
            "Artifact bundle: regime_record, safe_band_guidance, distortion_catalog (optional)",
        ],
        "output_format": "stress_record (PR146)",
        "bucket_mapping": {
            "PR144_to_simplified": "BAND_ZERO→OUTSIDE, BAND_MINIMAL→EDGE, BAND_LOW/MEDIUM/HIGH→SAFE, BAND_MAXIMAL→EDGE",
            "worst_bucket_priority": "OUTSIDE > EDGE > SAFE > UNKNOWN",
        },
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "label_output_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Stress Engine - Self Test")
    print("=" * 60)
    print()

    # Test 1: Direct inputs (CALM)
    print("Test 1: Direct inputs (CALM)")
    result1 = build_stress_label_from_inputs_v1(
        regime_label=REGIME_LOW,
        band_bucket=BAND_SAFE,
        distortion_presence=DIST_NONE,
    )
    print(f"Stress label: {result1['stress_record']['v14_stress_label']}")
    print(f"Warnings: {len(result1['warnings'])}")
    print()

    # Test 2: Direct inputs (STRESSED via CRITICAL)
    print("Test 2: Direct inputs (STRESSED via CRITICAL)")
    result2 = build_stress_label_from_inputs_v1(
        regime_label=REGIME_CRITICAL,
        band_bucket=BAND_SAFE,
        distortion_presence=DIST_NONE,
    )
    print(f"Stress label: {result2['stress_record']['v14_stress_label']}")
    print(f"Warnings: {len(result2['warnings'])}")
    print()

    # Test 3: Bundle path (minimal)
    print("Test 3: Bundle path (minimal)")
    test_bundle = {
        "artifacts": {
            "regime_record": {
                "v11_regime_level": REGIME_MEDIUM,
            },
            "role_safe_band_guidance": {
                "v14_guidance_roles": {
                    "VOLATILITY_ROLE": {
                        "status": "WITHIN_SAFE",
                        "safe_band_bucket": "BAND_MEDIUM",
                    }
                }
            },
        }
    }
    result3 = build_stress_label_from_bundle_v1(test_bundle)
    print(f"Stress label: {result3['stress_record']['v14_stress_label']}")
    print(f"Warnings: {len(result3['warnings'])}")
    print()

    # Test 4: Invalid bundle (defensive)
    print("Test 4: Invalid bundle (defensive)")
    result4 = build_stress_label_from_bundle_v1(None)
    print(f"Stress status: {result4['stress_record']['v14_stress_status']}")
    print(f"Warnings: {len(result4['warnings'])}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
