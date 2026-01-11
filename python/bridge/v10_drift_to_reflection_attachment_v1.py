#!/usr/bin/env python3
"""
PR121: v1.0 Drift → Reflection Attachment v1 (READ-ONLY)

Purpose:
    Attach drift classification to reflection records as structural addenda.
    Drift = first-class input to explainability chain.

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - Compatible with existing v0.7 reflection structure
    - Drift attachment = structural information only

Attachment Philosophy:
    Attachment ≠ Action
    Attachment ≠ Recommendation
    Attachment = Structural Addenda

    Attachment provides:
    - Drift level as reflection artifact reference
    - Drift status as structural context
    - Safe integration with existing reflection schema

    Attachment does NOT:
    - Recommend actions
    - Evaluate drift quality
    - Prescribe responses
    - Contain numeric patterns
"""

from typing import Any, Dict, List, Optional


def attach_drift_to_reflection_v1(
    reflection_record: Optional[Dict[str, Any]] = None,
    drift_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Attach drift classification to reflection record as structural addenda.

    Args:
        reflection_record: v7 reflection record
        drift_record: v10 drift record

    Returns:
        Enhanced reflection record with drift attachment

    Design:
        - Adds drift artifacts to reflection_artifacts list
        - Adds drift level to reflection_basis (if AVAILABLE)
        - Never modifies reflection_tag or reflection_summary
        - Defensive (None → return original or empty)
        - Warning-only (never raises)
    """
    # Defensive: validate inputs
    if reflection_record is None or not isinstance(reflection_record, dict):
        # Return minimal valid reflection if input invalid
        from reflection.v7_reflection_schema import V7ReflectionSchema
        return V7ReflectionSchema.create_empty_record()

    if drift_record is None or not isinstance(drift_record, dict):
        # No drift to attach → return original reflection
        return reflection_record.copy()

    # Copy reflection record (defensive)
    enhanced = reflection_record.copy()

    # Extract drift information
    drift_mode = drift_record.get("v10_drift_mode", "OFF")
    drift_status = drift_record.get("v10_drift_status", "UNAVAILABLE")
    drift_level = drift_record.get("v10_drift_level", "UNCLASSIFIED")

    # Only attach if drift is AVAILABLE
    if drift_mode == "ON" and drift_status == "AVAILABLE":
        # Add drift artifacts reference
        artifacts = enhanced.get("v7_reflection_artifacts", [])
        if not isinstance(artifacts, list):
            artifacts = []

        # Add drift artifact reference (string only, no data)
        if "pr120_drift_record" not in artifacts:
            artifacts.append("pr120_drift_record")

        enhanced["v7_reflection_artifacts"] = artifacts

        # Add drift level to reflection basis (safe, non-numeric label)
        basis = enhanced.get("v7_reflection_basis", [])
        if not isinstance(basis, list):
            basis = []

        # Add drift level to basis if not already present
        if "v10_drift_level" not in basis:
            basis.append("v10_drift_level")

        enhanced["v7_reflection_basis"] = basis

        # Optionally update reflection summary to mention drift context
        # (only if summary doesn't already mention it)
        summary = enhanced.get("v7_reflection_summary", "")
        if isinstance(summary, str) and "drift" not in summary.lower():
            # Append drift context to summary (non-prescriptive)
            enhanced["v7_reflection_summary"] = (
                f"{summary} drift classification available as structural context."
            )

    return enhanced


def get_drift_reflection_attachment_v1_info() -> Dict[str, Any]:
    """
    Get drift reflection attachment v1 information.

    Returns:
        Dict with attachment metadata
    """
    return {
        "attachment_version": "v1",
        "attachment_type": "drift_to_reflection",
        "attachment_approach": "structural_addenda_only",
        "modifies_reflection_tag": False,
        "modifies_reflection_summary": True,  # Appends context only
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
    print("v1.0 Drift → Reflection Attachment v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Valid reflection + valid drift
    print("Test 1: Valid reflection + valid drift")
    from reflection.v7_reflection_schema import V7ReflectionSchema

    reflection = V7ReflectionSchema.create_empty_record()
    reflection["v7_reflection_tag"] = "MEANING_COVERAGE_NARROW"
    reflection["v7_reflection_summary"] = "limited meaning types observed."

    drift = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "AVAILABLE",
        "v10_drift_level": "DRIFT_MEDIUM",
        "v10_drift_summary": "moderate structural changes detected.",
    }

    enhanced = attach_drift_to_reflection_v1(reflection, drift)
    print(f"Artifacts: {enhanced.get('v7_reflection_artifacts', [])}")
    print(f"Basis: {enhanced.get('v7_reflection_basis', [])}")
    print(f"Summary includes drift context: {'drift' in enhanced.get('v7_reflection_summary', '').lower()}")
    print()

    # Test 2: Valid reflection + unavailable drift
    print("Test 2: Valid reflection + unavailable drift (no attachment)")
    drift_unavailable = {
        "v10_drift_mode": "ON",
        "v10_drift_status": "ERROR",
        "v10_drift_level": "UNCLASSIFIED",
    }

    enhanced_unavailable = attach_drift_to_reflection_v1(reflection, drift_unavailable)
    print(f"Artifacts: {enhanced_unavailable.get('v7_reflection_artifacts', [])}")
    print(f"Unchanged: {enhanced_unavailable == reflection}")
    print()

    # Test 3: None inputs (defensive)
    print("Test 3: None inputs (defensive)")
    enhanced_none = attach_drift_to_reflection_v1(None, None)
    print(f"Returns valid record: {enhanced_none.get('v7_reflection_mode') == 'ON'}")
    print(f"Status: {enhanced_none.get('v7_reflection_status')}")
    print()

    # Test 4: Valid reflection + None drift (defensive)
    print("Test 4: Valid reflection + None drift (returns original)")
    enhanced_no_drift = attach_drift_to_reflection_v1(reflection, None)
    print(f"Returns original: {enhanced_no_drift == reflection}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
