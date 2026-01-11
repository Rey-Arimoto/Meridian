#!/usr/bin/env python3
"""
PR71: v0.7 Reflection Engine v1 (Coverage / Skew / Unseen Detection, READ-ONLY)

Purpose:
    Generate reflection records from interpretation analytics.
    Describe interpretation system characteristics using static rules.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Interpretation-bound: Only uses interpretation fields as basis

Reflection v1 Philosophy:
    Reflection v1 = Structural Self-Description

    This is not "getting better".
    This is describing what the system sees and doesn't see.

    v0.6: Observation → Interpretation (meaning)
    v0.7: Interpretation → Reflection (system description)

Reflection Tags (v1 Fixed Set):
    - MEANING_COVERAGE_NARROW: Limited meaning types observed
    - MEANING_COVERAGE_BROAD: Diverse meaning types observed
    - MEANING_DISTRIBUTION_SKEWED: Concentration on limited subset
    - FACTOR_DOMINANCE_OBSERVED: Certain factors almost always present
    - UNSEEN_MEANING_COMBINATIONS: Theoretically possible combinations never observed
    - SIGNAL_NEVER_OBSERVED: Certain signals not present in data
    - REFLECTION_INSUFFICIENT: Analytics data insufficient
    - UNCLASSIFIED: Cannot classify with current rules

Note: UNCLASSIFIED is a normal outcome (not a failure).
"""

from typing import Any, Dict, List

# Import schema and guards
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reflection.v7_reflection_schema import (
    V7ReflectionSchema,
)
from reflection.v7_constitutional_guard import (
    validate_reflection_record,
)


# ============================================================================
# v1 Reflection Tags (Fixed Set)
# ============================================================================

class V1ReflectionTags:
    """v1 Reflection Engine Reflection Tags (Fixed Set)."""

    # Coverage
    MEANING_COVERAGE_NARROW = "MEANING_COVERAGE_NARROW"
    MEANING_COVERAGE_BROAD = "MEANING_COVERAGE_BROAD"

    # Skew
    MEANING_DISTRIBUTION_SKEWED = "MEANING_DISTRIBUTION_SKEWED"
    FACTOR_DOMINANCE_OBSERVED = "FACTOR_DOMINANCE_OBSERVED"

    # Unseen
    UNSEEN_MEANING_COMBINATIONS = "UNSEEN_MEANING_COMBINATIONS"
    SIGNAL_NEVER_OBSERVED = "SIGNAL_NEVER_OBSERVED"

    # Neutral
    REFLECTION_INSUFFICIENT = "REFLECTION_INSUFFICIENT"
    UNCLASSIFIED = "UNCLASSIFIED"


# ============================================================================
# Static Reflection Logic
# ============================================================================

def reflect_v1(interpretation_analytics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate reflection record from interpretation analytics.

    Args:
        interpretation_analytics: PR64 interpretation analytics output

    Returns:
        v7 reflection record (dict)

    Warning-only: Never raises exceptions, always returns valid record.
    """
    # Initialize basis tracking
    basis_used = []

    # Start with safe defaults
    reflection_mode = "ON"
    reflection_status = "UNAVAILABLE"
    reflection_tag = V1ReflectionTags.UNCLASSIFIED
    reflection_summary = "reflection unavailable."
    reflection_artifacts = []

    # Check for required analytics data
    if not isinstance(interpretation_analytics, dict):
        reflection_status = "UNAVAILABLE"
        reflection_tag = V1ReflectionTags.REFLECTION_INSUFFICIENT
        reflection_summary = "interpretation analytics not available."
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
            reflection_status = "UNAVAILABLE"
            reflection_tag = V1ReflectionTags.REFLECTION_INSUFFICIENT
            reflection_summary = "interpretation analytics contains insufficient data for reflection."
            basis_used = ["meaning_tag_counts", "total_records"]
        else:
            # Data is available, perform reflection
            reflection_status = "AVAILABLE"
            reflection_artifacts = ["pr64_interpretation_analytics"]

            # Track what we use
            basis_used.append("meaning_tag_counts")
            basis_used.append("total_records")

            # Rule 1: Check meaning coverage (priority: narrow > broad)
            num_meaning_types = len(meaning_tag_counts)

            if num_meaning_types <= 2:
                reflection_tag = V1ReflectionTags.MEANING_COVERAGE_NARROW
                reflection_summary = (
                    f"observed interpretation output uses {num_meaning_types} meaning types. "
                    "limited structural variety in interpretation."
                )

            elif num_meaning_types >= 4:
                reflection_tag = V1ReflectionTags.MEANING_COVERAGE_BROAD
                reflection_summary = (
                    f"observed interpretation output uses {num_meaning_types} meaning types. "
                    "diverse structural coverage in interpretation."
                )

            # Rule 2: Check for skew (only if coverage not already assigned)
            elif meaning_tag_counts:
                max_count = max(meaning_tag_counts.values())
                skew_ratio = max_count / total_records

                if skew_ratio >= 0.8:  # 80%+ concentration
                    dominant_tag = max(meaning_tag_counts, key=meaning_tag_counts.get)
                    reflection_tag = V1ReflectionTags.MEANING_DISTRIBUTION_SKEWED
                    reflection_summary = (
                        f"observed interpretation output concentrates on limited subset. "
                        f"'{dominant_tag}' appears in {int(skew_ratio * 100)}% of records."
                    )

            # Rule 3: Check for factor dominance (only if no tag assigned yet)
            if reflection_tag == V1ReflectionTags.UNCLASSIFIED and factor_counts:
                basis_used.append("factor_counts")

                max_factor_count = max(factor_counts.values())
                factor_presence_ratio = max_factor_count / total_records

                if factor_presence_ratio >= 0.9:  # 90%+ presence
                    dominant_factor = max(factor_counts, key=factor_counts.get)
                    reflection_tag = V1ReflectionTags.FACTOR_DOMINANCE_OBSERVED
                    reflection_summary = (
                        f"certain structural factors almost always present. "
                        f"'{dominant_factor}' observed in {int(factor_presence_ratio * 100)}% of records."
                    )

            # Rule 4: Check for never-observed signals (only if no tag assigned yet)
            if reflection_tag == V1ReflectionTags.UNCLASSIFIED and signal_counts:
                basis_used.append("signal_counts")

                # Known signals from v2 engine
                known_signals = [
                    "DIFF_STATUS_ALIGNED",
                    "DIFF_STATUS_DIVERGED",
                    "DIFF_STATUS_UNAVAILABLE",
                    "SEMANTICS_RULE_OVERLAY",
                    "SEMANTICS_ALIGNED",
                    "SEMANTICS_UNKNOWN",
                    "SEMANTICS_NO_SHADOW",
                ]

                missing_signals = [s for s in known_signals if s not in signal_counts]

                if len(missing_signals) >= 3:
                    reflection_tag = V1ReflectionTags.SIGNAL_NEVER_OBSERVED
                    reflection_summary = (
                        f"{len(missing_signals)} observational signals not present in data. "
                        "certain structural patterns not observed."
                    )

            # If still unclassified, keep it
            if reflection_tag == V1ReflectionTags.UNCLASSIFIED:
                reflection_summary = (
                    "interpretation analytics structure not classified by current reflection rules."
                )

    # Create v7 reflection record
    reflection = {
        "v7_reflection_mode": reflection_mode,
        "v7_reflection_status": reflection_status,
        "v7_reflection_tag": reflection_tag,
        "v7_reflection_summary": reflection_summary,
        "v7_reflection_basis": basis_used,
        "v7_reflection_artifacts": reflection_artifacts,
    }

    # Validate against schema (warning-only)
    schema_warnings = V7ReflectionSchema.validate_structure(reflection)
    if schema_warnings:
        for warning in schema_warnings:
            print(f"[WARNING][PR71] Schema validation: {warning}")

    # Validate against constitutional guards (warning-only)
    guard_warnings = validate_reflection_record(reflection)
    if guard_warnings:
        for warning in guard_warnings:
            print(f"[WARNING][PR71] Constitutional guard: {warning}")

    return reflection


# ============================================================================
# Batch Processing Utility
# ============================================================================

def reflect_batch_v1(analytics_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate reflection records from multiple analytics outputs.

    Args:
        analytics_list: List of interpretation analytics dicts

    Returns:
        List of v7 reflection records

    Warning-only: Never raises exceptions.
    """
    reflections = []

    for analytics in analytics_list:
        try:
            reflection = reflect_v1(analytics)
            reflections.append(reflection)
        except Exception as e:
            # Fallback to safe empty record
            print(f"[WARNING][PR71] Reflection failed: {e}")
            reflection = V7ReflectionSchema.create_empty_record()
            reflections.append(reflection)

    return reflections


# ============================================================================
# Engine Info
# ============================================================================

def get_engine_v1_info() -> Dict[str, Any]:
    """
    Get reflection engine v1 information.

    Returns dict with engine metadata.
    """
    return {
        "engine_version": "v1",
        "engine_type": "static_structural_self_description",
        "reflection_tags": [
            V1ReflectionTags.MEANING_COVERAGE_NARROW,
            V1ReflectionTags.MEANING_COVERAGE_BROAD,
            V1ReflectionTags.MEANING_DISTRIBUTION_SKEWED,
            V1ReflectionTags.FACTOR_DOMINANCE_OBSERVED,
            V1ReflectionTags.UNSEEN_MEANING_COMBINATIONS,
            V1ReflectionTags.SIGNAL_NEVER_OBSERVED,
            V1ReflectionTags.REFLECTION_INSUFFICIENT,
            V1ReflectionTags.UNCLASSIFIED,
        ],
        "required_input": "pr64_interpretation_analytics",
        "basis_fields": [
            "meaning_tag_counts",
            "factor_counts",
            "signal_counts",
            "total_records",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v0.7 Reflection Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Print engine info
    print("Engine Info:")
    print(json.dumps(get_engine_v1_info(), indent=2))
    print()

    # Test cases
    test_cases = [
        {
            "name": "Narrow coverage",
            "analytics": {
                "distribution": {
                    "total_records": 100,
                    "meaning_tag_counts": {
                        "OVERLAY_OBSERVED": 90,
                        "ALIGNMENT_STABLE": 10,
                    },
                    "factor_counts": {},
                    "signal_counts": {},
                },
                "transitions": {},
            },
            "expected_tag": V1ReflectionTags.MEANING_COVERAGE_NARROW,
        },
        {
            "name": "Skewed distribution",
            "analytics": {
                "distribution": {
                    "total_records": 100,
                    "meaning_tag_counts": {
                        "OVERLAY_OBSERVED": 85,
                        "ALIGNMENT_STABLE": 10,
                        "UNCLASSIFIED": 5,
                    },
                    "factor_counts": {},
                    "signal_counts": {},
                },
                "transitions": {},
            },
            "expected_tag": V1ReflectionTags.MEANING_DISTRIBUTION_SKEWED,
        },
        {
            "name": "Insufficient data",
            "analytics": {
                "distribution": {
                    "total_records": 0,
                    "meaning_tag_counts": {},
                    "factor_counts": {},
                    "signal_counts": {},
                },
                "transitions": {},
            },
            "expected_tag": V1ReflectionTags.REFLECTION_INSUFFICIENT,
        },
    ]

    print("Test Cases:")
    for tc in test_cases:
        print(f"\nTest: {tc['name']}")
        reflection = reflect_v1(tc["analytics"])
        tag = reflection["v7_reflection_tag"]
        expected = tc["expected_tag"]
        status = "✓" if tag == expected else "✗"
        print(f"{status} Tag: {tag} (expected: {expected})")
        print(f"  Summary: {reflection['v7_reflection_summary']}")
        print(f"  Basis: {reflection['v7_reflection_basis']}")

    print()
    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
