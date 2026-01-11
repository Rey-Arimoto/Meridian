#!/usr/bin/env python3
"""
PR121: v1.0 Drift → Boundary Hinting v1 (READ-ONLY)

Purpose:
    Enhance boundary records with drift classification context.
    Drift provides observability stability hints (non-prescriptive).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - Compatible with existing v0.9 boundary structure
    - Drift hint = structural context only

Hinting Philosophy:
    Hint ≠ Action
    Hint ≠ Recommendation
    Hint = Observability Context

    Hinting provides:
    - Drift level as boundary artifact reference
    - Enhanced boundary description (observability stability)
    - Safe integration with existing boundary schema

    Hinting does NOT:
    - Recommend pause/stop/continue
    - Evaluate drift quality
    - Prescribe responses
    - Contain numeric patterns
"""

from typing import Any, Dict, List, Optional


def hint_boundary_with_drift_v1(
    boundary_record: Optional[Dict[str, Any]] = None,
    drift_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Enhance boundary record with drift classification context.

    Args:
        boundary_record: v9 boundary record
        drift_record: v10 drift record

    Returns:
        Enhanced boundary record with drift hints

    Design:
        - Adds drift artifacts to boundary_artifacts list
        - Enhances boundary_description with observability stability context
        - Never modifies boundary_type
        - Defensive (None → return original or empty)
        - Warning-only (never raises)
    """
    # Defensive: validate inputs
    if boundary_record is None or not isinstance(boundary_record, dict):
        # Return minimal valid boundary if input invalid
        from boundary.v9_boundary_schema import V9BoundarySchema
        return V9BoundarySchema.create_empty_record()

    if drift_record is None or not isinstance(drift_record, dict):
        # No drift to hint → return original boundary
        return boundary_record.copy()

    # Copy boundary record (defensive)
    enhanced = boundary_record.copy()

    # Extract drift information
    drift_mode = drift_record.get("v10_drift_mode", "OFF")
    drift_status = drift_record.get("v10_drift_status", "UNAVAILABLE")
    drift_level = drift_record.get("v10_drift_level", "UNCLASSIFIED")

    # Only hint if drift is AVAILABLE
    if drift_mode == "ON" and drift_status == "AVAILABLE":
        # Add drift artifacts reference
        artifacts = enhanced.get("v9_boundary_artifacts", [])
        if not isinstance(artifacts, list):
            artifacts = []

        # Add drift artifact reference (string only, no data)
        if "pr120_drift_record" not in artifacts:
            artifacts.append("pr120_drift_record")

        enhanced["v9_boundary_artifacts"] = artifacts

        # Add drift level to boundary basis (safe, non-numeric label)
        basis = enhanced.get("v9_boundary_basis", [])
        if not isinstance(basis, list):
            basis = []

        # Add drift level to basis if not already present
        if "v10_drift_level" not in basis:
            basis.append("v10_drift_level")

        enhanced["v9_boundary_basis"] = basis

        # Enhance boundary description with drift context (non-prescriptive)
        description = enhanced.get("v9_boundary_description", "")
        if isinstance(description, str):
            # Add drift stability hint based on drift level
            drift_hint = _generate_drift_stability_hint(drift_level)

            # Append hint if not already present
            if drift_hint and drift_hint not in description:
                enhanced["v9_boundary_description"] = (
                    f"{description} {drift_hint}"
                )

    return enhanced


def _generate_drift_stability_hint(drift_level: str) -> str:
    """
    Generate non-prescriptive drift stability hint for boundary description.

    Args:
        drift_level: Drift classification level

    Returns:
        Non-prescriptive hint string

    Note:
        Hints describe observability stability, not actions.
    """
    # Map drift levels to observability stability hints (non-prescriptive)
    hints = {
        "DRIFT_CRITICAL": "observability unstable under critical drift.",
        "DRIFT_HIGH": "observability unstable under high drift.",
        "DRIFT_MEDIUM": "observability moderate under drift.",
        "DRIFT_LOW": "observability stable under low drift.",
        "DRIFT_NONE": "observability stable with no drift.",
        "UNCLASSIFIED": "drift classification unavailable.",
    }

    return hints.get(drift_level, "")


def get_drift_boundary_hint_v1_info() -> Dict[str, Any]:
    """
    Get drift boundary hint v1 information.

    Returns:
        Dict with hint metadata
    """
    return {
        "hint_version": "v1",
        "hint_type": "drift_to_boundary",
        "hint_approach": "observability_stability_context",
        "modifies_boundary_type": False,
        "modifies_boundary_description": True,  # Appends hint only
        "defensive": True,
        "warning_only": True,
        "constitutional_validation": True,
        "no_numeric_output": True,
        "no_prescriptive_language": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Drift → Boundary Hinting v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Valid boundary + valid drift (CRITICAL)
    print("Test 1: Valid boundary + DRIFT_CRITICAL")
    from boundary.v9_boundary_schema import V9BoundarySchema

    boundary = V9BoundarySchema.create_empty_record()
    boundary["v9_boundary_type"] = "SAMPLING_BOUNDARY"
    boundary["v9_boundary_description"] = "sampling boundary detected."

    drift_critical = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "AVAILABLE",
        "v10_drift_level": "DRIFT_CRITICAL",
        "v10_drift_summary": "critical structural changes detected.",
    }

    enhanced_critical = hint_boundary_with_drift_v1(boundary, drift_critical)
    print(f"Artifacts: {enhanced_critical.get('v9_boundary_artifacts', [])}")
    print(f"Basis: {enhanced_critical.get('v9_boundary_basis', [])}")
    print(f"Description: {enhanced_critical.get('v9_boundary_description', '')}")
    print(f"Includes 'unstable': {'unstable' in enhanced_critical.get('v9_boundary_description', '')}")
    print()

    # Test 2: Valid boundary + DRIFT_LOW
    print("Test 2: Valid boundary + DRIFT_LOW")
    drift_low = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "AVAILABLE",
        "v10_drift_level": "DRIFT_LOW",
    }

    enhanced_low = hint_boundary_with_drift_v1(boundary, drift_low)
    print(f"Description: {enhanced_low.get('v9_boundary_description', '')}")
    print(f"Includes 'stable': {'stable' in enhanced_low.get('v9_boundary_description', '')}")
    print()

    # Test 3: Valid boundary + unavailable drift (no hint)
    print("Test 3: Valid boundary + unavailable drift (no hint)")
    drift_unavailable = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "ERROR",
        "v10_drift_level": "UNCLASSIFIED",
    }

    enhanced_unavailable = hint_boundary_with_drift_v1(boundary, drift_unavailable)
    print(f"Unchanged: {enhanced_unavailable == boundary}")
    print()

    # Test 4: None inputs (defensive)
    print("Test 4: None inputs (defensive)")
    enhanced_none = hint_boundary_with_drift_v1(None, None)
    print(f"Returns valid record: {enhanced_none.get('v9_boundary_mode') == 'ON'}")
    print(f"Status: {enhanced_none.get('v9_boundary_status')}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
