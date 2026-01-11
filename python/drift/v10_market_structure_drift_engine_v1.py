#!/usr/bin/env python3
"""
PR120: v1.0 Market Structure Drift Detection Engine v1 (READ-ONLY)

Purpose:
    Detect market structure drift by comparing vocabulary windows.
    Engine = Structural Change Detector (not evaluator/predictor).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No numeric amounts: No drift scores, percentages, counts in output
    - Engine = detector (not evaluation/action)

Engine Philosophy:
    Engine ≠ Evaluation
    Engine ≠ Prediction
    Engine = Vocabulary Window Comparator

    Engine provides:
    - Qualitative drift classification
    - Evidence terms (names only, no counts)
    - Structural change detection
    - Defensive handling

    Engine does NOT:
    - Expose raw numbers in output
    - Evaluate quality
    - Predict future drift
    - Recommend actions

Detection Approach (v1 - Static, Qualitative):

    1. Extract term presence sets from each window
       - Window A (past): union of all terms across all vocab records
       - Window B (current): union of all terms across all vocab records

    2. Compute structural deltas:
       - terms_added: terms in B but not in A (B \ A)
       - terms_removed: terms in A but not in B (A \ B)

    3. Bucket into drift levels (INTERNAL bucketing - NO numbers in output):
       - DRIFT_NONE: no delta
       - DRIFT_LOW: small delta
       - DRIFT_MEDIUM: moderate delta
       - DRIFT_HIGH: large delta
       - DRIFT_CRITICAL: very large delta
       - UNCLASSIFIED: insufficient data

    4. Generate evidence list (term names only, no counts):
       - Format: "{TERM_NAME}_ADDED" or "{TERM_NAME}_REMOVED"
"""

from typing import Any, Dict, List, Optional, Set
from .v10_market_structure_drift_schema import V10MarketStructureDriftSchema


def detect_market_structure_drift_v1(
    vocab_window_A: Optional[List[Dict[str, Any]]] = None,
    vocab_window_B: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Detect market structure drift between two vocabulary windows.

    Args:
        vocab_window_A: List of vocabulary records (past window)
        vocab_window_B: List of vocabulary records (current window)

    Returns:
        Drift record (always valid)

    Design:
        - Compares term presence sets
        - Buckets delta into qualitative levels
        - NO numbers in output (constitutional)
        - Defensive (None/empty → UNCLASSIFIED or ERROR)
        - Warning-only (never raises)
    """
    warnings: List[str] = []

    # Defensive: validate inputs
    if not isinstance(vocab_window_A, list) or not isinstance(vocab_window_B, list):
        return V10MarketStructureDriftSchema.create_error_record(
            error_info="invalid window inputs (None or not list)",
            warnings=["Windows must be lists of vocabulary records"],
        )

    # Defensive: handle empty windows
    if len(vocab_window_A) == 0 or len(vocab_window_B) == 0:
        # Empty windows → UNCLASSIFIED (safer default)
        return V10MarketStructureDriftSchema.create_drift_record(
            drift_level="UNCLASSIFIED",
            summary="market structure drift unclassified. insufficient data in windows.",
            basis=["vocab_window_A", "vocab_window_B"],
            evidence=[],
            warnings=["One or both windows empty"] if len(vocab_window_A) == 0 or len(vocab_window_B) == 0 else None,
        )

    # Extract term presence sets
    terms_A = _extract_term_set(vocab_window_A)
    terms_B = _extract_term_set(vocab_window_B)

    # Compute deltas
    terms_added = terms_B - terms_A
    terms_removed = terms_A - terms_B

    # Bucket into drift levels (INTERNAL - no numbers in output)
    drift_level = _classify_drift_level(terms_added, terms_removed)

    # Generate evidence (term names only, no counts)
    evidence = []
    for term in sorted(terms_added):
        evidence.append(f"{term}_ADDED")
    for term in sorted(terms_removed):
        evidence.append(f"{term}_REMOVED")

    # Generate summary
    summary = _generate_drift_summary(drift_level, terms_added, terms_removed)

    # Create drift record
    drift = V10MarketStructureDriftSchema.create_drift_record(
        drift_level=drift_level,
        summary=summary,
        basis=["vocab_window_A", "vocab_window_B"],
        evidence=evidence,
        warnings=warnings if warnings else None,
    )

    # Validate drift against constitutional guard
    from .v10_drift_constitutional_guard import validate_drift_record

    guard_warnings = validate_drift_record(drift)
    if guard_warnings:
        # Add guard warnings to drift warnings
        existing_warnings = drift.get("v10_drift_warnings", [])
        all_warnings = existing_warnings + guard_warnings
        drift["v10_drift_warnings"] = all_warnings

    return drift


def _extract_term_set(vocab_window: List[Dict[str, Any]]) -> Set[str]:
    """
    Extract union of all vocabulary terms from window.

    Args:
        vocab_window: List of vocabulary records

    Returns:
        Set of vocabulary terms
    """
    all_terms: Set[str] = set()

    for vocab_record in vocab_window:
        if not isinstance(vocab_record, dict):
            continue

        terms = vocab_record.get("v10_vocab_terms", [])
        if isinstance(terms, list):
            for term in terms:
                if isinstance(term, str):
                    all_terms.add(term)

    return all_terms


def _classify_drift_level(terms_added: Set[str], terms_removed: Set[str]) -> str:
    """
    Classify drift level based on delta size (INTERNAL bucketing).

    Args:
        terms_added: Set of added terms
        terms_removed: Set of removed terms

    Returns:
        Drift level classification

    Note:
        Bucketing thresholds are internal implementation details.
        Only the qualitative label is exposed externally.
    """
    # Compute total delta (INTERNAL only - not exposed)
    total_delta = len(terms_added) + len(terms_removed)

    # Bucket into drift levels
    if total_delta == 0:
        return "DRIFT_NONE"
    elif total_delta <= 2:
        return "DRIFT_LOW"
    elif total_delta <= 4:
        return "DRIFT_MEDIUM"
    elif total_delta <= 6:
        return "DRIFT_HIGH"
    else:
        return "DRIFT_CRITICAL"


def _generate_drift_summary(
    drift_level: str,
    terms_added: Set[str],
    terms_removed: Set[str],
) -> str:
    """
    Generate drift summary (NO numbers, qualitative only).

    Args:
        drift_level: Drift classification level
        terms_added: Set of added terms
        terms_removed: Set of removed terms

    Returns:
        Non-evaluative summary string
    """
    # Base description by level
    level_descriptions = {
        "DRIFT_NONE": "no structural change detected. vocabulary stable.",
        "DRIFT_LOW": "minor structural changes detected. small vocabulary shift.",
        "DRIFT_MEDIUM": "moderate structural changes detected. vocabulary evolving.",
        "DRIFT_HIGH": "significant structural changes detected. substantial vocabulary shift.",
        "DRIFT_CRITICAL": "critical structural changes detected. major vocabulary transformation.",
        "UNCLASSIFIED": "drift classification unavailable. insufficient data.",
    }

    base_summary = level_descriptions.get(
        drift_level, "drift classification unknown."
    )

    # Add context about directionality (NO counts)
    if len(terms_added) > 0 and len(terms_removed) > 0:
        direction = "terms added and removed."
    elif len(terms_added) > 0:
        direction = "new terms added."
    elif len(terms_removed) > 0:
        direction = "existing terms removed."
    else:
        direction = "no term changes."

    return f"market structure drift classified as {drift_level.lower()}. {base_summary} {direction}"


def get_drift_engine_v1_info() -> Dict[str, Any]:
    """
    Get drift engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "market_structure_drift_detection",
        "detection_approach": "vocabulary_window_comparison",
        "bucketing": "internal_qualitative",
        "output_format": "drift_level_label_only",
        "defensive": True,
        "warning_only": True,
        "constitutional_validation": True,
        "no_numeric_output": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Market Structure Drift Detection Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Create mock vocabulary records
    vocab_record_1 = {
        "v10_vocab_terms": ["COST_LOW_PRESENT", "LIQUIDITY_LOW_PRESENT", "EVENT_ACTIVITY_ABSENT"],
    }
    vocab_record_2 = {
        "v10_vocab_terms": ["COST_LOW_PRESENT", "COST_MEDIUM_PRESENT", "LIQUIDITY_LOW_PRESENT"],
    }
    vocab_record_3 = {
        "v10_vocab_terms": ["COST_HIGH_PRESENT", "LIQUIDITY_HIGH_PRESENT", "EVENT_ACTIVITY_PRESENT"],
    }

    # Test 1: No drift (same vocab)
    print("Test 1: No drift (same vocabulary)")
    window_A = [vocab_record_1]
    window_B = [vocab_record_1]
    drift_none = detect_market_structure_drift_v1(window_A, window_B)
    print(f"Drift level: {drift_none.get('v10_drift_level')}")
    print(f"Evidence count: {len(drift_none.get('v10_drift_evidence', []))}")
    print()

    # Test 2: Low drift (small change)
    print("Test 2: Low drift (small change)")
    window_A = [vocab_record_1]
    window_B = [vocab_record_2]
    drift_low = detect_market_structure_drift_v1(window_A, window_B)
    print(f"Drift level: {drift_low.get('v10_drift_level')}")
    print(f"Evidence: {drift_low.get('v10_drift_evidence')}")
    print()

    # Test 3: High/Critical drift (large change)
    print("Test 3: High/Critical drift (large change)")
    window_A = [vocab_record_1]
    window_B = [vocab_record_3]
    drift_high = detect_market_structure_drift_v1(window_A, window_B)
    print(f"Drift level: {drift_high.get('v10_drift_level')}")
    print(f"Evidence count: {len(drift_high.get('v10_drift_evidence', []))}")
    print()

    # Test 4: Empty windows (defensive)
    print("Test 4: Empty windows (defensive)")
    drift_empty = detect_market_structure_drift_v1([], [])
    print(f"Drift level: {drift_empty.get('v10_drift_level')}")
    print(f"Status: {drift_empty.get('v10_drift_status')}")
    print()

    # Test 5: None inputs (defensive)
    print("Test 5: None inputs (defensive)")
    drift_none_input = detect_market_structure_drift_v1(None, None)
    print(f"Status: {drift_none_input.get('v10_drift_status')}")
    print(f"Error info: {drift_none_input.get('v10_drift_error_info')}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
