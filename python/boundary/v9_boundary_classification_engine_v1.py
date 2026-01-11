#!/usr/bin/env python3
"""
PR91: v0.9 Boundary Classification Engine v1 (Structural Limit Classification, READ-ONLY)

Purpose:
    Classify blindspots into structural boundary types.
    Describes where observability stops, not what should be done.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Blindspot-bound: Only uses v8/v7/v6 fields as basis

Boundary Classification v1 Philosophy:
    Boundary Classification v1 = Structural Limit Mapping

    This is not "finding problems".
    This is classifying at which structural layer observability ends.

    Input: Blindspot record (v8)
    Output: Boundary record (v9)

Boundary Types (v1):
    - SCHEMA_BOUNDARY: Structure cannot be expressed with current schema
    - DATA_BOUNDARY: Required data does not exist or is insufficient
    - ENGINE_BOUNDARY: Interpretation/reflection rules cannot map structure
    - SAMPLING_BOUNDARY: Structure exists in definition space but not observed
    - TEMPORAL_BOUNDARY: Structure exists but cannot be observed in time window
    - UNCLASSIFIED: Cannot classify with current rules

Note: UNCLASSIFIED is a normal outcome (not a failure).
"""

from typing import Any, Dict, List

# Import schema and guards
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from boundary.v9_boundary_schema import (
    V9BoundarySchema,
)
from boundary.v9_constitutional_guard import (
    validate_boundary_record,
)


# ============================================================================
# v1 Boundary Types (Fixed Set)
# ============================================================================

class V1BoundaryTypes:
    """v1 Boundary Classification Engine Boundary Types (Fixed Set)."""

    # Structural boundaries
    SCHEMA_BOUNDARY = "SCHEMA_BOUNDARY"
    DATA_BOUNDARY = "DATA_BOUNDARY"
    ENGINE_BOUNDARY = "ENGINE_BOUNDARY"
    SAMPLING_BOUNDARY = "SAMPLING_BOUNDARY"
    TEMPORAL_BOUNDARY = "TEMPORAL_BOUNDARY"

    # Neutral
    UNCLASSIFIED = "UNCLASSIFIED"


# ============================================================================
# Temporal Threshold (Fixed Value)
# ============================================================================

# Minimum days of observation to consider temporal boundary vs sampling boundary
TEMPORAL_BOUNDARY_MIN_DAYS = 30  # Fixed threshold, not optimized


# ============================================================================
# Boundary Classification Logic
# ============================================================================

def classify_boundary_v1(
    blindspot_record: Dict[str, Any],
    artifacts: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Classify blindspot into structural boundary type.

    Args:
        blindspot_record: PR81 blindspot record (v8)
        artifacts: Optional artifacts (analytics, reflection, etc.)

    Returns:
        v9 boundary record (dict)

    Warning-only: Never raises exceptions, always returns valid record.
    """
    # Initialize basis tracking
    basis_used = []

    # Start with safe defaults
    boundary_mode = "ON"
    boundary_status = "UNAVAILABLE"
    boundary_type = V1BoundaryTypes.UNCLASSIFIED
    boundary_description = "boundary unavailable."
    boundary_artifacts = []

    # Check for required blindspot data
    if not isinstance(blindspot_record, dict):
        boundary_status = "UNAVAILABLE"
        boundary_type = V1BoundaryTypes.DATA_BOUNDARY
        boundary_description = "blindspot record not available."
        # basis_used remains empty
    else:
        # Extract blindspot fields (defensive against None)
        blindspot_tag = blindspot_record.get("v8_blindspot_tag", "")
        if not isinstance(blindspot_tag, str):
            blindspot_tag = ""
        blindspot_summary = blindspot_record.get("v8_blindspot_summary", "")
        if not isinstance(blindspot_summary, str):
            blindspot_summary = ""
        blindspot_status = blindspot_record.get("v8_blindspot_status", "UNAVAILABLE")
        if not isinstance(blindspot_status, str):
            blindspot_status = "UNAVAILABLE"

        # Check for data sufficiency
        if blindspot_status == "UNAVAILABLE" or not blindspot_tag:
            boundary_status = "UNAVAILABLE"
            boundary_type = V1BoundaryTypes.DATA_BOUNDARY
            boundary_description = "blindspot record contains insufficient data for boundary classification."
            basis_used = ["v8_blindspot_status"]
        else:
            # Data is available, perform classification
            boundary_status = "AVAILABLE"
            boundary_artifacts = ["pr81_blindspot_record"]

            # Track what we use
            basis_used.append("v8_blindspot_tag")

            # Import blindspot tags for comparison
            # (We need to reference them without circular import)
            ABSENCE_INSUFFICIENT_EVIDENCE = "ABSENCE_INSUFFICIENT_EVIDENCE"
            ABSENCE_SCHEMA_CANNOT_EXPRESS = "ABSENCE_SCHEMA_CANNOT_EXPRESS"
            ABSENCE_TRANSITION_NOT_OBSERVED = "ABSENCE_TRANSITION_NOT_OBSERVED"
            ABSENCE_UNSEEN_SIGNAL_TYPES = "ABSENCE_UNSEEN_SIGNAL_TYPES"
            ABSENCE_UNSEEN_FACTOR_TYPES = "ABSENCE_UNSEEN_FACTOR_TYPES"
            ABSENCE_UNOBSERVED_MEANING_TYPES = "ABSENCE_UNOBSERVED_MEANING_TYPES"

            # Rule 1: ABSENCE_INSUFFICIENT_EVIDENCE → DATA_BOUNDARY
            if blindspot_tag == ABSENCE_INSUFFICIENT_EVIDENCE:
                boundary_type = V1BoundaryTypes.DATA_BOUNDARY
                boundary_description = (
                    "observability limit at data layer. "
                    "required data does not exist or is insufficient."
                )

            # Rule 2: ABSENCE_SCHEMA_CANNOT_EXPRESS → SCHEMA_BOUNDARY
            elif blindspot_tag == ABSENCE_SCHEMA_CANNOT_EXPRESS:
                boundary_type = V1BoundaryTypes.SCHEMA_BOUNDARY
                boundary_description = (
                    "observability limit at schema layer. "
                    "structure cannot be expressed with current schema."
                )

            # Rule 3: ABSENCE_TRANSITION_NOT_OBSERVED → TEMPORAL or SAMPLING
            elif blindspot_tag == ABSENCE_TRANSITION_NOT_OBSERVED:
                # Check temporal artifacts if available
                observation_days = None
                if artifacts and isinstance(artifacts, dict):
                    # Try to extract observation period from analytics
                    analytics = artifacts.get("interpretation_analytics", {})
                    if isinstance(analytics, dict):
                        distribution = analytics.get("distribution", {})
                        if isinstance(distribution, dict):
                            # Infer from total_records (rough heuristic)
                            total_records = distribution.get("total_records", 0)
                            if isinstance(total_records, int) and total_records > 0:
                                # Assume 1 record per day (rough estimate)
                                observation_days = total_records
                                basis_used.append("total_records")

                if observation_days is not None and observation_days < TEMPORAL_BOUNDARY_MIN_DAYS:
                    boundary_type = V1BoundaryTypes.TEMPORAL_BOUNDARY
                    boundary_description = (
                        f"observability limit at temporal layer. "
                        f"observation period ({observation_days} days) insufficient to observe all transition patterns."
                    )
                else:
                    boundary_type = V1BoundaryTypes.SAMPLING_BOUNDARY
                    boundary_description = (
                        "observability limit at sampling layer. "
                        "certain transition patterns exist in definition space but not observed in data."
                    )

            # Rule 4: UNSEEN_SIGNAL/FACTOR/MEANING_TYPES → SAMPLING_BOUNDARY
            elif blindspot_tag in [ABSENCE_UNSEEN_SIGNAL_TYPES, ABSENCE_UNSEEN_FACTOR_TYPES, ABSENCE_UNOBSERVED_MEANING_TYPES]:
                boundary_type = V1BoundaryTypes.SAMPLING_BOUNDARY
                boundary_description = (
                    "observability limit at sampling layer. "
                    "certain structural types exist in definition space but not observed in data."
                )

            # Rule 5: All other tags → UNCLASSIFIED
            else:
                boundary_type = V1BoundaryTypes.UNCLASSIFIED
                boundary_description = (
                    "blindspot structure analyzed, boundary type not classified by current rules."
                )

    # Create v9 boundary record
    boundary = {
        "v9_boundary_mode": boundary_mode,
        "v9_boundary_status": boundary_status,
        "v9_boundary_type": boundary_type,
        "v9_boundary_description": boundary_description,
        "v9_boundary_basis": basis_used,
        "v9_boundary_artifacts": boundary_artifacts,
    }

    # Validate against schema (warning-only)
    schema_warnings = V9BoundarySchema.validate_structure(boundary)
    if schema_warnings:
        for warning in schema_warnings:
            print(f"[WARNING][PR91] Schema validation: {warning}")

    # Validate against constitutional guards (warning-only)
    guard_warnings = validate_boundary_record(boundary)
    if guard_warnings:
        for warning in guard_warnings:
            print(f"[WARNING][PR91] Constitutional guard: {warning}")

    return boundary


# ============================================================================
# Batch Processing Utility
# ============================================================================

def classify_boundary_batch_v1(
    blindspot_list: List[Dict[str, Any]],
    artifacts_list: List[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Classify boundaries from multiple blindspot records.

    Args:
        blindspot_list: List of blindspot records
        artifacts_list: Optional list of artifacts

    Returns:
        List of v9 boundary records

    Warning-only: Never raises exceptions.
    """
    boundaries = []

    for i, blindspot in enumerate(blindspot_list):
        try:
            # Get corresponding artifacts if available
            artifacts = None
            if artifacts_list and i < len(artifacts_list):
                artifacts = artifacts_list[i]

            boundary = classify_boundary_v1(blindspot, artifacts)
            boundaries.append(boundary)
        except Exception as e:
            # Fallback to safe empty record
            print(f"[WARNING][PR91] Boundary classification failed: {e}")
            boundary = V9BoundarySchema.create_empty_record()
            boundaries.append(boundary)

    return boundaries


# ============================================================================
# Engine Info
# ============================================================================

def get_engine_v1_info() -> Dict[str, Any]:
    """
    Get boundary classification engine v1 information.

    Returns dict with engine metadata.
    """
    return {
        "engine_version": "v1",
        "engine_type": "structural_limit_mapping",
        "boundary_types": [
            V1BoundaryTypes.SCHEMA_BOUNDARY,
            V1BoundaryTypes.DATA_BOUNDARY,
            V1BoundaryTypes.ENGINE_BOUNDARY,
            V1BoundaryTypes.SAMPLING_BOUNDARY,
            V1BoundaryTypes.TEMPORAL_BOUNDARY,
            V1BoundaryTypes.UNCLASSIFIED,
        ],
        "required_input": "pr81_blindspot_record",
        "optional_input": "artifacts (analytics, reflection, etc.)",
        "temporal_boundary_min_days": TEMPORAL_BOUNDARY_MIN_DAYS,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v0.9 Boundary Classification Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Print engine info
    print("Engine Info:")
    print(json.dumps(get_engine_v1_info(), indent=2))
    print()

    # Test cases
    test_cases = [
        {
            "name": "Data boundary",
            "blindspot": {
                "v8_blindspot_mode": "ON",
                "v8_blindspot_status": "UNAVAILABLE",
                "v8_blindspot_tag": "ABSENCE_INSUFFICIENT_EVIDENCE",
                "v8_blindspot_summary": "data insufficient",
                "v8_blindspot_basis": [],
            },
            "expected_type": V1BoundaryTypes.DATA_BOUNDARY,
        },
        {
            "name": "Schema boundary",
            "blindspot": {
                "v8_blindspot_mode": "ON",
                "v8_blindspot_status": "AVAILABLE",
                "v8_blindspot_tag": "ABSENCE_SCHEMA_CANNOT_EXPRESS",
                "v8_blindspot_summary": "schema limitation",
                "v8_blindspot_basis": [],
            },
            "expected_type": V1BoundaryTypes.SCHEMA_BOUNDARY,
        },
        {
            "name": "Sampling boundary",
            "blindspot": {
                "v8_blindspot_mode": "ON",
                "v8_blindspot_status": "AVAILABLE",
                "v8_blindspot_tag": "ABSENCE_UNSEEN_SIGNAL_TYPES",
                "v8_blindspot_summary": "signals not observed",
                "v8_blindspot_basis": [],
            },
            "expected_type": V1BoundaryTypes.SAMPLING_BOUNDARY,
        },
    ]

    print("Test Cases:")
    for tc in test_cases:
        print(f"\nTest: {tc['name']}")
        boundary = classify_boundary_v1(tc["blindspot"])
        btype = boundary["v9_boundary_type"]
        expected = tc["expected_type"]
        status = "✓" if btype == expected else "✗"
        print(f"{status} Type: {btype} (expected: {expected})")
        print(f"  Description: {boundary['v9_boundary_description']}")
        print(f"  Basis: {boundary['v9_boundary_basis']}")

    print()
    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
