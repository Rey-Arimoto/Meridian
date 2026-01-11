#!/usr/bin/env python3
"""
PR63: v0.6 Interpretation Engine v2 (Compositional Structural Mapping, READ-ONLY)

Purpose:
    Map observations to compositional structural meaning (factors + signals).
    This increases interpretation resolution without evaluation.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Observation-bound: Only uses observation fields as basis
    - v0.4 boundary protection: No confidence_reason analysis

Interpretation v2 Philosophy:
    v1 = Static Structural Mapping (point)
    v2 = Compositional Structural Mapping (surface)

    v2 decomposes interpretation into:
    1. Primary Meaning (main structural type)
    2. Factors (structural elements present)
    3. Signals (concrete observational signs)

    This is not "getting smarter". This is decomposition without loss.

Meaning Types (v2):
    - Primary Meaning: Same as v1 (OVERLAY_OBSERVED, ALIGNMENT_STABLE, etc.)
    - Factors: Structural elements (REGIME_PRESENT, INTENT_PRESENT, etc.)
    - Signals: Observational signs (DIFF_STATUS_ALIGNED, SEMANTICS_RULE_OVERLAY, etc.)

Note: UNKNOWN/UNCLASSIFIED remain normal outcomes (not failures).
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
from interpretation.v6_interpretation_engine_v1 import (
    V1MeaningTags,
)


# ============================================================================
# v2 Meaning Types (Compositional)
# ============================================================================

class V2PrimaryMeaning:
    """v2 Primary Meaning Types (same as v1)."""

    OVERLAY_OBSERVED = "OVERLAY_OBSERVED"
    ALIGNMENT_STABLE = "ALIGNMENT_STABLE"
    DIVERGENCE_WITHOUT_CLASS = "DIVERGENCE_WITHOUT_CLASS"
    SHADOW_ABSENT_OR_UNAVAILABLE = "SHADOW_ABSENT_OR_UNAVAILABLE"
    OBSERVATION_INSUFFICIENT = "OBSERVATION_INSUFFICIENT"
    UNCLASSIFIED = "UNCLASSIFIED"


class V2Factors:
    """v2 Structural Factors (elements present in observation)."""

    # Regime factors
    REGIME_PRESENT = "REGIME_PRESENT"
    REGIME_TRANSITION_PRESENT = "REGIME_TRANSITION_PRESENT"

    # Intent factors
    INTENT_PRESENT = "INTENT_PRESENT"
    INTENT_ABSENT = "INTENT_ABSENT"

    # Semantics factors
    SEMANTICS_AVAILABLE = "SEMANTICS_AVAILABLE"
    SEMANTICS_UNAVAILABLE = "SEMANTICS_UNAVAILABLE"

    # Shadow factors
    SHADOW_PRESENT = "SHADOW_PRESENT"
    SHADOW_ABSENT = "SHADOW_ABSENT"


class V2Signals:
    """v2 Observational Signals (concrete signs from data)."""

    # Diff status signals
    DIFF_STATUS_ALIGNED = "DIFF_STATUS_ALIGNED"
    DIFF_STATUS_DIVERGED = "DIFF_STATUS_DIVERGED"
    DIFF_STATUS_UNAVAILABLE = "DIFF_STATUS_UNAVAILABLE"

    # Semantics signals
    SEMANTICS_RULE_OVERLAY = "SEMANTICS_RULE_OVERLAY"
    SEMANTICS_ALIGNED = "SEMANTICS_ALIGNED"
    SEMANTICS_UNKNOWN = "SEMANTICS_UNKNOWN"
    SEMANTICS_NO_SHADOW = "SEMANTICS_NO_SHADOW"

    # Pair signals
    PAIR_IDENTIFIED = "PAIR_IDENTIFIED"
    PAIR_UNKNOWN = "PAIR_UNKNOWN"


# ============================================================================
# Compositional Mapping Logic
# ============================================================================

def extract_signals(observation: Dict[str, Any]) -> List[str]:
    """
    Extract observational signals from observation.

    Step 1: Direct observation → concrete signs

    Args:
        observation: Observation record (dict with v5 fields)

    Returns:
        List of signal strings
    """
    signals = []

    # Diff status signals
    diff_status = observation.get("v5_decision_diff_status", "UNKNOWN")

    if diff_status == "ALIGNED":
        signals.append(V2Signals.DIFF_STATUS_ALIGNED)
    elif diff_status == "DIVERGED":
        signals.append(V2Signals.DIFF_STATUS_DIVERGED)
    elif diff_status == "UNAVAILABLE":
        signals.append(V2Signals.DIFF_STATUS_UNAVAILABLE)

    # Semantics signals
    semantics_tag = observation.get("v5_decision_diff_semantics_tag", "UNKNOWN")

    if semantics_tag == "DIVERGED_RULE_OVERLAY":
        signals.append(V2Signals.SEMANTICS_RULE_OVERLAY)
    elif semantics_tag == "ALIGNED":
        signals.append(V2Signals.SEMANTICS_ALIGNED)
    elif semantics_tag in ["UNKNOWN", "DIVERGED_UNKNOWN"]:
        signals.append(V2Signals.SEMANTICS_UNKNOWN)
    elif semantics_tag == "NO_SHADOW":
        signals.append(V2Signals.SEMANTICS_NO_SHADOW)

    # Pair signals (if decision_pair present)
    decision_pair = observation.get("v5_decision_pair", "")
    if decision_pair and decision_pair != "UNKNOWN":
        signals.append(V2Signals.PAIR_IDENTIFIED)
    elif "v5_decision_pair" in observation:
        signals.append(V2Signals.PAIR_UNKNOWN)

    return signals


def derive_factors(observation: Dict[str, Any], signals: List[str]) -> List[str]:
    """
    Derive structural factors from observation and signals.

    Step 2: Signals + observation → structural elements

    Args:
        observation: Observation record
        signals: Extracted signals

    Returns:
        List of factor strings
    """
    factors = []

    # Regime factors
    regime = observation.get("regime", "UNKNOWN")
    if regime and regime not in [None, "", "UNKNOWN"]:
        factors.append(V2Factors.REGIME_PRESENT)

        # Check for regime transition (heuristic: regime contains "transition")
        if "transition" in regime.lower():
            factors.append(V2Factors.REGIME_TRANSITION_PRESENT)

    # Intent factors
    intent_primary = observation.get("intent_primary", "UNKNOWN")
    if intent_primary and intent_primary not in [None, "", "UNKNOWN"]:
        factors.append(V2Factors.INTENT_PRESENT)
    else:
        factors.append(V2Factors.INTENT_ABSENT)

    # Semantics factors
    if V2Signals.SEMANTICS_UNKNOWN in signals or V2Signals.SEMANTICS_NO_SHADOW in signals:
        factors.append(V2Factors.SEMANTICS_UNAVAILABLE)
    else:
        factors.append(V2Factors.SEMANTICS_AVAILABLE)

    # Shadow factors
    shadow_present = (
        "v5_shadow_decision_action" in observation
        and observation.get("v5_shadow_decision_action") not in [None, "", "UNKNOWN"]
    )

    if shadow_present:
        factors.append(V2Factors.SHADOW_PRESENT)
    else:
        factors.append(V2Factors.SHADOW_ABSENT)

    return factors


def determine_primary_meaning(
    observation: Dict[str, Any],
    signals: List[str],
    factors: List[str],
) -> str:
    """
    Determine primary meaning from factors and signals.

    Step 3: Factors + Signals → primary structural meaning

    Args:
        observation: Observation record
        signals: Extracted signals
        factors: Derived factors

    Returns:
        Primary meaning tag string
    """
    # Check for observation insufficiency
    required_fields = [
        "v5_decision_diff_status",
        "v5_decision_diff_semantics_tag",
    ]

    has_required = all(field in observation for field in required_fields)

    if not has_required:
        return V2PrimaryMeaning.OBSERVATION_INSUFFICIENT

    # Check for shadow absent
    if V2Signals.DIFF_STATUS_UNAVAILABLE in signals or V2Signals.SEMANTICS_NO_SHADOW in signals:
        return V2PrimaryMeaning.SHADOW_ABSENT_OR_UNAVAILABLE

    # Check for overlay pattern
    if V2Signals.SEMANTICS_RULE_OVERLAY in signals:
        return V2PrimaryMeaning.OVERLAY_OBSERVED

    # Check for alignment stable
    if (
        V2Signals.DIFF_STATUS_ALIGNED in signals
        and V2Factors.SHADOW_PRESENT in factors
    ):
        return V2PrimaryMeaning.ALIGNMENT_STABLE

    # Check for divergence without class
    if (
        V2Signals.DIFF_STATUS_DIVERGED in signals
        and V2Signals.SEMANTICS_UNKNOWN in signals
    ):
        return V2PrimaryMeaning.DIVERGENCE_WITHOUT_CLASS

    # Default: unclassified
    return V2PrimaryMeaning.UNCLASSIFIED


def generate_summary(
    primary_meaning: str,
    factors: List[str],
    signals: List[str],
) -> str:
    """
    Generate non-evaluative summary from compositional elements.

    Step 4: Generate structural explanation (not evaluation)

    Args:
        primary_meaning: Primary meaning tag
        factors: Structural factors
        signals: Observational signals

    Returns:
        Non-evaluative summary string
    """
    # Base summaries for primary meanings
    base_summaries = {
        V2PrimaryMeaning.OVERLAY_OBSERVED: "overlay pattern observed in decision divergence",
        V2PrimaryMeaning.ALIGNMENT_STABLE: "decision actions aligned with shadow present",
        V2PrimaryMeaning.DIVERGENCE_WITHOUT_CLASS: "decision divergence observed without clear classification",
        V2PrimaryMeaning.SHADOW_ABSENT_OR_UNAVAILABLE: "shadow observation not available",
        V2PrimaryMeaning.OBSERVATION_INSUFFICIENT: "required observation fields not present",
        V2PrimaryMeaning.UNCLASSIFIED: "observation structure not classified by current rules",
    }

    summary = base_summaries.get(primary_meaning, "interpretation unavailable")

    # Add contextual modifiers (non-evaluative)
    modifiers = []

    if V2Factors.REGIME_TRANSITION_PRESENT in factors:
        modifiers.append("under regime transition")
    elif V2Factors.REGIME_PRESENT in factors:
        modifiers.append("with regime context")

    if V2Factors.INTENT_PRESENT in factors:
        modifiers.append("with intent present")

    if modifiers:
        summary += ", " + ", ".join(modifiers)

    summary += "."

    return summary


# ============================================================================
# v2 Interpretation Entry Point
# ============================================================================

def interpret_v2(observation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Interpret observation using v2 compositional mapping.

    Args:
        observation: Observation record (dict with v5 fields)

    Returns:
        v6 interpretation record (dict) with compositional fields

    Warning-only: Never raises exceptions, always returns valid record.
    """
    # Initialize basis tracking
    basis_used = []

    # Start with safe defaults
    meaning_mode = "ON"
    meaning_status = "UNAVAILABLE"

    # Step 1: Extract signals
    signals = extract_signals(observation)

    # Step 2: Derive factors
    factors = derive_factors(observation, signals)

    # Step 3: Determine primary meaning
    primary_meaning = determine_primary_meaning(observation, signals, factors)

    # Step 4: Generate summary
    summary = generate_summary(primary_meaning, factors, signals)

    # Update status
    if primary_meaning in [
        V2PrimaryMeaning.OBSERVATION_INSUFFICIENT,
        V2PrimaryMeaning.SHADOW_ABSENT_OR_UNAVAILABLE,
    ]:
        meaning_status = "UNAVAILABLE"
    else:
        meaning_status = "AVAILABLE"

    # Track basis (which fields we used)
    basis_candidates = [
        "v5_decision_diff_status",
        "v5_decision_diff_semantics_tag",
        "v5_shadow_decision_action",
        "v5_decision_pair",
        "regime",
        "intent_primary",
    ]

    for field in basis_candidates:
        if field in observation and observation.get(field) not in [None, "", "UNKNOWN"]:
            basis_used.append(field)

    # Create v6 interpretation record (v2 extended)
    interpretation = {
        "v6_meaning_mode": meaning_mode,
        "v6_meaning_status": meaning_status,
        "v6_meaning_tag": primary_meaning,
        "v6_meaning_factors": factors,
        "v6_meaning_signals": signals,
        "v6_meaning_summary": summary,
        "v6_meaning_basis": basis_used,
    }

    # Validate against schema (warning-only)
    schema_warnings = V6InterpretationSchema.validate_structure(interpretation)
    if schema_warnings:
        for warning in schema_warnings:
            print(f"[WARNING][PR63] Schema validation: {warning}")

    # Validate against constitutional guards (warning-only)
    guard_warnings = validate_interpretation_record(interpretation)
    if guard_warnings:
        for warning in guard_warnings:
            print(f"[WARNING][PR63] Constitutional guard: {warning}")

    return interpretation


# ============================================================================
# Batch Processing Utility
# ============================================================================

def interpret_batch_v2(observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Interpret a batch of observations using v2.

    Args:
        observations: List of observation records

    Returns:
        List of v6 interpretation records (v2 extended)

    Warning-only: Never raises exceptions.
    """
    interpretations = []

    for obs in observations:
        try:
            interp = interpret_v2(obs)
            interpretations.append(interp)
        except Exception as e:
            # Fallback to safe empty record
            print(f"[WARNING][PR63] Interpretation failed: {e}")
            interp = V6InterpretationSchema.create_empty_record()
            # Add v2 fields
            interp["v6_meaning_factors"] = []
            interp["v6_meaning_signals"] = []
            interpretations.append(interp)

    return interpretations


# ============================================================================
# Engine Info
# ============================================================================

def get_engine_v2_info() -> Dict[str, Any]:
    """
    Get interpretation engine v2 information.

    Returns dict with engine metadata.
    """
    return {
        "engine_version": "v2",
        "engine_type": "compositional_structural_mapping",
        "primary_meanings": [
            V2PrimaryMeaning.OVERLAY_OBSERVED,
            V2PrimaryMeaning.ALIGNMENT_STABLE,
            V2PrimaryMeaning.DIVERGENCE_WITHOUT_CLASS,
            V2PrimaryMeaning.SHADOW_ABSENT_OR_UNAVAILABLE,
            V2PrimaryMeaning.OBSERVATION_INSUFFICIENT,
            V2PrimaryMeaning.UNCLASSIFIED,
        ],
        "factors": [
            V2Factors.REGIME_PRESENT,
            V2Factors.REGIME_TRANSITION_PRESENT,
            V2Factors.INTENT_PRESENT,
            V2Factors.INTENT_ABSENT,
            V2Factors.SEMANTICS_AVAILABLE,
            V2Factors.SEMANTICS_UNAVAILABLE,
            V2Factors.SHADOW_PRESENT,
            V2Factors.SHADOW_ABSENT,
        ],
        "signals": [
            V2Signals.DIFF_STATUS_ALIGNED,
            V2Signals.DIFF_STATUS_DIVERGED,
            V2Signals.DIFF_STATUS_UNAVAILABLE,
            V2Signals.SEMANTICS_RULE_OVERLAY,
            V2Signals.SEMANTICS_ALIGNED,
            V2Signals.SEMANTICS_UNKNOWN,
            V2Signals.SEMANTICS_NO_SHADOW,
            V2Signals.PAIR_IDENTIFIED,
            V2Signals.PAIR_UNKNOWN,
        ],
        "required_fields": [
            "v5_decision_diff_status",
            "v5_decision_diff_semantics_tag",
        ],
        "optional_fields": [
            "v5_shadow_decision_action",
            "v5_decision_pair",
            "regime",
            "intent_primary",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v0.6 Interpretation Engine v2 - Self Test")
    print("=" * 60)
    print()

    # Print engine info
    print("Engine Info:")
    print(json.dumps(get_engine_v2_info(), indent=2))
    print()

    # Test cases
    test_cases = [
        {
            "name": "Overlay pattern with regime",
            "obs": {
                "v5_decision_diff_status": "DIVERGED",
                "v5_decision_diff_semantics_tag": "DIVERGED_RULE_OVERLAY",
                "v5_shadow_decision_action": "PAUSE",
                "regime": "stable_range",
                "intent_primary": "IDLE",
            },
            "expected_primary": V2PrimaryMeaning.OVERLAY_OBSERVED,
        },
        {
            "name": "Alignment stable",
            "obs": {
                "v5_decision_diff_status": "ALIGNED",
                "v5_decision_diff_semantics_tag": "ALIGNED",
                "v5_shadow_decision_action": "HOLD",
            },
            "expected_primary": V2PrimaryMeaning.ALIGNMENT_STABLE,
        },
        {
            "name": "Shadow absent",
            "obs": {
                "v5_decision_diff_status": "UNAVAILABLE",
                "v5_decision_diff_semantics_tag": "NO_SHADOW",
            },
            "expected_primary": V2PrimaryMeaning.SHADOW_ABSENT_OR_UNAVAILABLE,
        },
        {
            "name": "Observation insufficient",
            "obs": {},
            "expected_primary": V2PrimaryMeaning.OBSERVATION_INSUFFICIENT,
        },
    ]

    print("Test Cases:")
    for tc in test_cases:
        print(f"\nTest: {tc['name']}")
        interp = interpret_v2(tc["obs"])
        primary = interp["v6_meaning_tag"]
        expected = tc["expected_primary"]
        status = "✓" if primary == expected else "✗"
        print(f"{status} Primary: {primary} (expected: {expected})")
        print(f"  Factors: {interp['v6_meaning_factors']}")
        print(f"  Signals: {interp['v6_meaning_signals']}")
        print(f"  Summary: {interp['v6_meaning_summary']}")
        print(f"  Basis: {interp['v6_meaning_basis']}")

    print()
    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
