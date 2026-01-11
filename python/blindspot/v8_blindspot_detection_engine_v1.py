#!/usr/bin/env python3
"""
PR81: v0.8 Blindspot Detection Engine v1 (Structural Absence Scan, READ-ONLY)

Purpose:
    Detect structural absences by enumerating differences between
    possible structures and observed structures.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Interpretation/Reflection-bound: Only uses v6/v7 fields as basis

Blindspot Detection v1 Philosophy:
    Blindspot Detection v1 = Structural Absence Scan

    This is not "finding problems".
    This is enumerating what structures have not been observed.

    Input: Interpretation analytics + Reflection record
    Output: Blindspot record (structural absence description)

Blindspot Tags (v1 Fixed Set):
    - ABSENCE_INSUFFICIENT_EVIDENCE: Analytics data insufficient
    - ABSENCE_UNSEEN_SIGNAL_TYPES: Certain signal types not observed
    - ABSENCE_UNSEEN_FACTOR_TYPES: Certain factor types not observed
    - ABSENCE_UNOBSERVED_MEANING_TYPES: Certain meaning types not observed
    - ABSENCE_TRANSITION_NOT_OBSERVED: Certain transitions not observed
    - ABSENCE_SCHEMA_CANNOT_EXPRESS: Structure cannot be expressed
    - UNCLASSIFIED: Cannot classify with current rules

Note: UNCLASSIFIED is a normal outcome (not a failure).
"""

from typing import Any, Dict, List

# Import schema and guards
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blindspot.v8_blindspot_schema import (
    V8BlindspotSchema,
)
from blindspot.v8_constitutional_guard import (
    validate_blindspot_record,
)


# ============================================================================
# v1 Blindspot Tags (Fixed Set)
# ============================================================================

class V1BlindspotTags:
    """v1 Blindspot Detection Engine Blindspot Tags (Fixed Set)."""

    # Evidence
    ABSENCE_INSUFFICIENT_EVIDENCE = "ABSENCE_INSUFFICIENT_EVIDENCE"

    # Signal/Factor/Meaning gaps
    ABSENCE_UNSEEN_SIGNAL_TYPES = "ABSENCE_UNSEEN_SIGNAL_TYPES"
    ABSENCE_UNSEEN_FACTOR_TYPES = "ABSENCE_UNSEEN_FACTOR_TYPES"
    ABSENCE_UNOBSERVED_MEANING_TYPES = "ABSENCE_UNOBSERVED_MEANING_TYPES"

    # Transition gaps
    ABSENCE_TRANSITION_NOT_OBSERVED = "ABSENCE_TRANSITION_NOT_OBSERVED"

    # Schema limitation
    ABSENCE_SCHEMA_CANNOT_EXPRESS = "ABSENCE_SCHEMA_CANNOT_EXPRESS"

    # Neutral
    UNCLASSIFIED = "UNCLASSIFIED"


# ============================================================================
# Known Structures (Definition Space)
# ============================================================================

# Known signal types from v6 interpretation engine v2
KNOWN_SIGNAL_TYPES = [
    "DIFF_STATUS_ALIGNED",
    "DIFF_STATUS_DIVERGED",
    "DIFF_STATUS_UNAVAILABLE",
    "SEMANTICS_RULE_OVERLAY",
    "SEMANTICS_ALIGNED",
    "SEMANTICS_UNKNOWN",
    "SEMANTICS_NO_SHADOW",
]

# Known factor types from v6 interpretation engine v2
KNOWN_FACTOR_TYPES = [
    "REGIME_PRESENT",
    "SHADOW_PRESENT",
    "ALIGNMENT_PRESENT",
    "DIVERGENCE_PRESENT",
]

# Known meaning types from v6 interpretation engine
KNOWN_MEANING_TYPES = [
    "OVERLAY_OBSERVED",
    "ALIGNMENT_STABLE",
    "DIVERGENCE_WITHOUT_CLASS",
    "SHADOW_ONLY",
    "REGIME_ONLY",
    "OBSERVATION_INSUFFICIENT",
    "UNCLASSIFIED",
]


# ============================================================================
# Blindspot Detection Logic
# ============================================================================

def detect_blindspot_v1(
    interpretation_analytics: Dict[str, Any],
    reflection_record: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Detect structural absences from interpretation analytics and reflection.

    Args:
        interpretation_analytics: PR64 interpretation analytics output
        reflection_record: PR71 reflection record (optional)

    Returns:
        v8 blindspot record (dict)

    Warning-only: Never raises exceptions, always returns valid record.
    """
    # Initialize basis tracking
    basis_used = []

    # Start with safe defaults
    blindspot_mode = "ON"
    blindspot_status = "UNAVAILABLE"
    blindspot_tag = V1BlindspotTags.UNCLASSIFIED
    blindspot_summary = "blindspot unavailable."
    blindspot_artifacts = []

    # Check for required analytics data
    if not isinstance(interpretation_analytics, dict):
        blindspot_status = "UNAVAILABLE"
        blindspot_tag = V1BlindspotTags.ABSENCE_INSUFFICIENT_EVIDENCE
        blindspot_summary = "interpretation analytics not available."
        # basis_used remains empty
    else:
        # Extract distribution data (defensive against None)
        distribution = interpretation_analytics.get("distribution", {})
        if not isinstance(distribution, dict):
            distribution = {}
        transitions = interpretation_analytics.get("transitions", {})
        if not isinstance(transitions, dict):
            transitions = {}

        # Get counts (defensive against None)
        total_records = distribution.get("total_records", 0) if distribution else 0
        if not isinstance(total_records, int):
            total_records = 0
        meaning_tag_counts = distribution.get("meaning_tag_counts", {}) if distribution else {}
        if not isinstance(meaning_tag_counts, dict):
            meaning_tag_counts = {}
        factor_counts = distribution.get("factor_counts", {}) if distribution else {}
        if not isinstance(factor_counts, dict):
            factor_counts = {}
        signal_counts = distribution.get("signal_counts", {}) if distribution else {}
        if not isinstance(signal_counts, dict):
            signal_counts = {}

        # Check for data sufficiency
        if total_records == 0 or not meaning_tag_counts:
            blindspot_status = "UNAVAILABLE"
            blindspot_tag = V1BlindspotTags.ABSENCE_INSUFFICIENT_EVIDENCE
            blindspot_summary = "interpretation analytics contains insufficient data for blindspot detection."
            basis_used = ["meaning_tag_counts", "total_records"]
        else:
            # Data is available, perform detection
            blindspot_status = "AVAILABLE"
            blindspot_artifacts = ["pr64_interpretation_analytics"]

            # Track what we use
            basis_used.append("meaning_tag_counts")
            basis_used.append("total_records")

            # Add reflection if available
            if reflection_record and isinstance(reflection_record, dict):
                blindspot_artifacts.append("pr71_reflection_record")
                basis_used.append("v7_reflection_tag")

            # Rule 1: Check for unseen signal types
            if signal_counts:
                basis_used.append("signal_counts")

                observed_signals = set(signal_counts.keys())
                known_signals = set(KNOWN_SIGNAL_TYPES)
                unseen_signals = known_signals - observed_signals

                if len(unseen_signals) >= 3:  # 3+ signals never observed
                    blindspot_tag = V1BlindspotTags.ABSENCE_UNSEEN_SIGNAL_TYPES
                    blindspot_summary = (
                        f"{len(unseen_signals)} signal types not observed in data. "
                        "certain observational patterns not present."
                    )

            # Rule 2: Check for unseen factor types (only if no tag assigned yet)
            if blindspot_tag == V1BlindspotTags.UNCLASSIFIED and factor_counts:
                basis_used.append("factor_counts")

                observed_factors = set(factor_counts.keys())
                known_factors = set(KNOWN_FACTOR_TYPES)
                unseen_factors = known_factors - observed_factors

                if len(unseen_factors) >= 2:  # 2+ factors never observed
                    blindspot_tag = V1BlindspotTags.ABSENCE_UNSEEN_FACTOR_TYPES
                    blindspot_summary = (
                        f"{len(unseen_factors)} factor types not observed in data. "
                        "certain structural patterns not present."
                    )

            # Rule 3: Check for unobserved meaning types (only if no tag assigned yet)
            if blindspot_tag == V1BlindspotTags.UNCLASSIFIED:
                observed_meanings = set(meaning_tag_counts.keys())
                known_meanings = set(KNOWN_MEANING_TYPES)
                unseen_meanings = known_meanings - observed_meanings

                if len(unseen_meanings) >= 3:  # 3+ meanings never observed
                    blindspot_tag = V1BlindspotTags.ABSENCE_UNOBSERVED_MEANING_TYPES
                    blindspot_summary = (
                        f"{len(unseen_meanings)} meaning types not observed in data. "
                        "certain interpretation patterns not present."
                    )

            # Rule 4: Check for transition gaps (only if no tag assigned yet)
            if blindspot_tag == V1BlindspotTags.UNCLASSIFIED and transitions:
                basis_used.append("transitions")

                # Count transition types observed
                num_transitions = len(transitions)

                # Theoretical max transitions (for observed meanings)
                num_meanings = len(meaning_tag_counts)
                theoretical_max = num_meanings * (num_meanings - 1)  # N * (N-1) possible transitions

                if theoretical_max > 0:
                    coverage_ratio = num_transitions / theoretical_max

                    if coverage_ratio < 0.1:  # Less than 10% of possible transitions observed
                        blindspot_tag = V1BlindspotTags.ABSENCE_TRANSITION_NOT_OBSERVED
                        blindspot_summary = (
                            f"{num_transitions} transitions observed out of {theoretical_max} possible. "
                            "certain meaning transition patterns not present."
                        )

            # If still unclassified, keep it
            if blindspot_tag == V1BlindspotTags.UNCLASSIFIED:
                blindspot_summary = (
                    "interpretation analytics structure analyzed, no significant structural absence detected."
                )

    # Create v8 blindspot record
    blindspot = {
        "v8_blindspot_mode": blindspot_mode,
        "v8_blindspot_status": blindspot_status,
        "v8_blindspot_tag": blindspot_tag,
        "v8_blindspot_summary": blindspot_summary,
        "v8_blindspot_basis": basis_used,
        "v8_blindspot_artifacts": blindspot_artifacts,
    }

    # Validate against schema (warning-only)
    schema_warnings = V8BlindspotSchema.validate_structure(blindspot)
    if schema_warnings:
        for warning in schema_warnings:
            print(f"[WARNING][PR81] Schema validation: {warning}")

    # Validate against constitutional guards (warning-only)
    guard_warnings = validate_blindspot_record(blindspot)
    if guard_warnings:
        for warning in guard_warnings:
            print(f"[WARNING][PR81] Constitutional guard: {warning}")

    return blindspot


# ============================================================================
# Batch Processing Utility
# ============================================================================

def detect_blindspot_batch_v1(
    analytics_list: List[Dict[str, Any]],
    reflection_list: List[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Detect blindspots from multiple analytics outputs.

    Args:
        analytics_list: List of interpretation analytics dicts
        reflection_list: Optional list of reflection records

    Returns:
        List of v8 blindspot records

    Warning-only: Never raises exceptions.
    """
    blindspots = []

    for i, analytics in enumerate(analytics_list):
        try:
            # Get corresponding reflection if available
            reflection = None
            if reflection_list and i < len(reflection_list):
                reflection = reflection_list[i]

            blindspot = detect_blindspot_v1(analytics, reflection)
            blindspots.append(blindspot)
        except Exception as e:
            # Fallback to safe empty record
            print(f"[WARNING][PR81] Blindspot detection failed: {e}")
            blindspot = V8BlindspotSchema.create_empty_record()
            blindspots.append(blindspot)

    return blindspots


# ============================================================================
# Engine Info
# ============================================================================

def get_engine_v1_info() -> Dict[str, Any]:
    """
    Get blindspot detection engine v1 information.

    Returns dict with engine metadata.
    """
    return {
        "engine_version": "v1",
        "engine_type": "structural_absence_scan",
        "blindspot_tags": [
            V1BlindspotTags.ABSENCE_INSUFFICIENT_EVIDENCE,
            V1BlindspotTags.ABSENCE_UNSEEN_SIGNAL_TYPES,
            V1BlindspotTags.ABSENCE_UNSEEN_FACTOR_TYPES,
            V1BlindspotTags.ABSENCE_UNOBSERVED_MEANING_TYPES,
            V1BlindspotTags.ABSENCE_TRANSITION_NOT_OBSERVED,
            V1BlindspotTags.ABSENCE_SCHEMA_CANNOT_EXPRESS,
            V1BlindspotTags.UNCLASSIFIED,
        ],
        "required_input": "pr64_interpretation_analytics",
        "optional_input": "pr71_reflection_record",
        "known_signal_types": KNOWN_SIGNAL_TYPES,
        "known_factor_types": KNOWN_FACTOR_TYPES,
        "known_meaning_types": KNOWN_MEANING_TYPES,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v0.8 Blindspot Detection Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Print engine info
    print("Engine Info:")
    print(json.dumps(get_engine_v1_info(), indent=2))
    print()

    # Test cases
    test_cases = [
        {
            "name": "Insufficient evidence",
            "analytics": {
                "distribution": {
                    "total_records": 0,
                    "meaning_tag_counts": {},
                    "factor_counts": {},
                    "signal_counts": {},
                },
                "transitions": {},
            },
            "expected_tag": V1BlindspotTags.ABSENCE_INSUFFICIENT_EVIDENCE,
        },
        {
            "name": "Unseen signal types",
            "analytics": {
                "distribution": {
                    "total_records": 100,
                    "meaning_tag_counts": {
                        "OVERLAY_OBSERVED": 50,
                        "ALIGNMENT_STABLE": 50,
                    },
                    "factor_counts": {},
                    "signal_counts": {
                        "DIFF_STATUS_ALIGNED": 50,
                        # Missing: DIFF_STATUS_DIVERGED, DIFF_STATUS_UNAVAILABLE, etc.
                    },
                },
                "transitions": {},
            },
            "expected_tag": V1BlindspotTags.ABSENCE_UNSEEN_SIGNAL_TYPES,
        },
        {
            "name": "Unseen meaning types",
            "analytics": {
                "distribution": {
                    "total_records": 100,
                    "meaning_tag_counts": {
                        "OVERLAY_OBSERVED": 100,
                        # Only 1 meaning type observed, 6 others missing
                    },
                    "factor_counts": {},
                    "signal_counts": {},
                },
                "transitions": {},
            },
            "expected_tag": V1BlindspotTags.ABSENCE_UNOBSERVED_MEANING_TYPES,
        },
    ]

    print("Test Cases:")
    for tc in test_cases:
        print(f"\nTest: {tc['name']}")
        blindspot = detect_blindspot_v1(tc["analytics"])
        tag = blindspot["v8_blindspot_tag"]
        expected = tc["expected_tag"]
        status = "✓" if tag == expected else "✗"
        print(f"{status} Tag: {tag} (expected: {expected})")
        print(f"  Summary: {blindspot['v8_blindspot_summary']}")
        print(f"  Basis: {blindspot['v8_blindspot_basis']}")

    print()
    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
