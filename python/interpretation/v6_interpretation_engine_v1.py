#!/usr/bin/env python3
"""
PR61: v0.6 Interpretation Engine v1 (Static Structural Mapping, READ-ONLY)

Purpose:
    Map observations to structural meaning types using static rules.
    This is the first implementation of Observation → Interpretation.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Observation-bound: Only uses observation fields as basis
    - v0.4 boundary protection: No confidence_reason analysis

Interpretation v1 Philosophy:
    Interpretation v1 = Static Structural Mapping

    This is not "getting smarter".
    This is structural language for what we can understand.

    v0.6 does not begin judgment.
    v0.6 begins structural language.

Meaning Tags (v1 Fixed Set):
    - OVERLAY_OBSERVED: Overlay pattern detected
    - ALIGNMENT_STABLE: Actions aligned with shadow present
    - DIVERGENCE_WITHOUT_CLASS: Divergence observed but type unclear
    - SHADOW_ABSENT_OR_UNAVAILABLE: Shadow data not available
    - OBSERVATION_INSUFFICIENT: Required fields missing
    - UNCLASSIFIED: Cannot classify with current rules

Note: UNKNOWN/UNCLASSIFIED are normal outcomes (not failures).
"""

from typing import Any, Dict, List

# Import schema and guards
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interpretation.v6_interpretation_schema import (
    V6InterpretationSchema,
)
from interpretation.v6_constitutional_guard import (
    validate_interpretation_record,
)


# ============================================================================
# v1 Meaning Tags (Fixed Set)
# ============================================================================

class V1MeaningTags:
    """v1 Interpretation Engine Meaning Tags (Fixed Set)."""

    OVERLAY_OBSERVED = "OVERLAY_OBSERVED"
    ALIGNMENT_STABLE = "ALIGNMENT_STABLE"
    DIVERGENCE_WITHOUT_CLASS = "DIVERGENCE_WITHOUT_CLASS"
    SHADOW_ABSENT_OR_UNAVAILABLE = "SHADOW_ABSENT_OR_UNAVAILABLE"
    OBSERVATION_INSUFFICIENT = "OBSERVATION_INSUFFICIENT"
    UNCLASSIFIED = "UNCLASSIFIED"


# ============================================================================
# Static Mapping Logic
# ============================================================================

def interpret_v1(observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret observation using v1 static rules.

    Args:
        observation: Observation record (dict with v5 fields)

    Returns:
        v6 interpretation record (dict)

    Warning-only: Never raises exceptions, always returns valid record.
    """
    # Initialize basis tracking
    basis_used = []

    # Start with safe defaults
    meaning_mode = "ON"
    meaning_status = "UNAVAILABLE"
    meaning_tag = V1MeaningTags.UNCLASSIFIED
    meaning_summary = "interpretation unavailable."

    # Check for required observation fields
    required_fields = [
        "v5_decision_diff_status",
        "v5_decision_diff_semantics_tag",
    ]

    has_required = all(field in observation for field in required_fields)

    if not has_required:
        # OBSERVATION_INSUFFICIENT: Required fields missing
        meaning_status = "UNAVAILABLE"
        meaning_tag = V1MeaningTags.OBSERVATION_INSUFFICIENT
        meaning_summary = "required observation fields not present."
        # basis_used remains empty

    else:
        # Get observation values
        diff_status = observation.get("v5_decision_diff_status", "UNKNOWN")
        semantics_tag = observation.get("v5_decision_diff_semantics_tag", "UNKNOWN")

        # Track which fields we actually use
        basis_used.append("v5_decision_diff_status")
        basis_used.append("v5_decision_diff_semantics_tag")

        # Check shadow availability
        shadow_present = (
            "v5_shadow_decision_action" in observation
            and observation.get("v5_shadow_decision_action") not in [None, "", "UNKNOWN"]
        )

        if shadow_present:
            basis_used.append("v5_shadow_decision_action")

        # Apply static mapping rules
        if diff_status == "UNAVAILABLE" or semantics_tag == "NO_SHADOW":
            # SHADOW_ABSENT_OR_UNAVAILABLE
            meaning_status = "AVAILABLE"
            meaning_tag = V1MeaningTags.SHADOW_ABSENT_OR_UNAVAILABLE
            meaning_summary = "shadow observation not available."

        elif semantics_tag == "DIVERGED_RULE_OVERLAY":
            # OVERLAY_OBSERVED: Overlay pattern detected
            meaning_status = "AVAILABLE"
            meaning_tag = V1MeaningTags.OVERLAY_OBSERVED
            meaning_summary = "overlay pattern observed in decision divergence."

        elif diff_status == "ALIGNED" and shadow_present:
            # ALIGNMENT_STABLE: Actions aligned with shadow present
            meaning_status = "AVAILABLE"
            meaning_tag = V1MeaningTags.ALIGNMENT_STABLE
            meaning_summary = "decision actions aligned with shadow present."

        elif diff_status == "DIVERGED" and semantics_tag in ["UNKNOWN", "DIVERGED_UNKNOWN"]:
            # DIVERGENCE_WITHOUT_CLASS: Divergence but type unclear
            meaning_status = "AVAILABLE"
            meaning_tag = V1MeaningTags.DIVERGENCE_WITHOUT_CLASS
            meaning_summary = "decision divergence observed without clear classification."

        else:
            # UNCLASSIFIED: Cannot classify with current rules
            meaning_status = "AVAILABLE"
            meaning_tag = V1MeaningTags.UNCLASSIFIED
            meaning_summary = "observation structure not classified by current rules."

        # Optionally include regime/intent if present
        if "regime" in observation and observation["regime"] not in [None, "", "UNKNOWN"]:
            basis_used.append("regime")

        if "intent_primary" in observation and observation["intent_primary"] not in [None, "", "UNKNOWN"]:
            basis_used.append("intent_primary")

    # Create v6 interpretation record
    interpretation = {
        "v6_meaning_mode": meaning_mode,
        "v6_meaning_status": meaning_status,
        "v6_meaning_tag": meaning_tag,
        "v6_meaning_summary": meaning_summary,
        "v6_meaning_basis": basis_used,
    }

    # Validate against schema (warning-only)
    schema_warnings = V6InterpretationSchema.validate_structure(interpretation)
    if schema_warnings:
        for warning in schema_warnings:
            print(f"[WARNING][PR61] Schema validation: {warning}")

    # Validate against constitutional guards (warning-only)
    guard_warnings = validate_interpretation_record(interpretation)
    if guard_warnings:
        for warning in guard_warnings:
            print(f"[WARNING][PR61] Constitutional guard: {warning}")

    return interpretation


# ============================================================================
# Batch Processing Utility
# ============================================================================

def interpret_batch_v1(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Interpret a batch of observations.

    Args:
        observations: List of observation records

    Returns:
        List of v6 interpretation records

    Warning-only: Never raises exceptions.
    """
    interpretations = []

    for obs in observations:
        try:
            interp = interpret_v1(obs)
            interpretations.append(interp)
        except Exception as e:
            # Fallback to safe empty record
            print(f"[WARNING][PR61] Interpretation failed: {e}")
            interp = V6InterpretationSchema.create_empty_record()
            interpretations.append(interp)

    return interpretations


# ============================================================================
# Engine Info
# ============================================================================

def get_engine_info() -> Dict[str, Any]:
    """
    Get interpretation engine v1 information.

    Returns dict with engine metadata.
    """
    return {
        "engine_version": "v1",
        "engine_type": "static_structural_mapping",
        "meaning_tags": [
            V1MeaningTags.OVERLAY_OBSERVED,
            V1MeaningTags.ALIGNMENT_STABLE,
            V1MeaningTags.DIVERGENCE_WITHOUT_CLASS,
            V1MeaningTags.SHADOW_ABSENT_OR_UNAVAILABLE,
            V1MeaningTags.OBSERVATION_INSUFFICIENT,
            V1MeaningTags.UNCLASSIFIED,
        ],
        "required_fields": [
            "v5_decision_diff_status",
            "v5_decision_diff_semantics_tag",
        ],
        "optional_fields": [
            "v5_shadow_decision_action",
            "regime",
            "intent_primary",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v0.6 Interpretation Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Print engine info
    print("Engine Info:")
    print(json.dumps(get_engine_info(), indent=2))
    print()

    # Test cases
    test_cases = [
        {
            "name": "Overlay pattern",
            "obs": {
                "v5_decision_diff_status": "DIVERGED",
                "v5_decision_diff_semantics_tag": "DIVERGED_RULE_OVERLAY",
                "v5_shadow_decision_action": "PAUSE",
            },
            "expected_tag": V1MeaningTags.OVERLAY_OBSERVED,
        },
        {
            "name": "Alignment stable",
            "obs": {
                "v5_decision_diff_status": "ALIGNED",
                "v5_decision_diff_semantics_tag": "ALIGNED",
                "v5_shadow_decision_action": "HOLD",
            },
            "expected_tag": V1MeaningTags.ALIGNMENT_STABLE,
        },
        {
            "name": "Shadow absent",
            "obs": {
                "v5_decision_diff_status": "UNAVAILABLE",
                "v5_decision_diff_semantics_tag": "NO_SHADOW",
            },
            "expected_tag": V1MeaningTags.SHADOW_ABSENT_OR_UNAVAILABLE,
        },
        {
            "name": "Observation insufficient",
            "obs": {},
            "expected_tag": V1MeaningTags.OBSERVATION_INSUFFICIENT,
        },
    ]

    print("Test Cases:")
    for tc in test_cases:
        print(f"\nTest: {tc['name']}")
        interp = interpret_v1(tc["obs"])
        tag = interp["v6_meaning_tag"]
        expected = tc["expected_tag"]
        status = "✓" if tag == expected else "✗"
        print(f"{status} Tag: {tag} (expected: {expected})")
        print(f"  Summary: {interp['v6_meaning_summary']}")
        print(f"  Basis: {interp['v6_meaning_basis']}")

    print()
    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
