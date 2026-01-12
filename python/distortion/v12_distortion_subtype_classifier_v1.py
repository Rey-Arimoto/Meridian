#!/usr/bin/env python3
"""
PR134: v1.2 Distortion Subtype Classifier v1 (READ-ONLY)

Purpose:
    Classify distortion subtypes (D1A-D5C) using qualitative labels.
    Static deterministic first-match-wins classification.

Classification Rules (First-match-wins):
    0. Invalid inputs → ERROR
    1. Parent distortion D1-D5 → classify subtype using qualitative inputs:
       - market_cost_regime (HIGH/MEDIUM/LOW)
       - liquidity_regime (HIGH/MEDIUM/LOW/DECREASING)
       - event_activity_present (True/False)
       - event_pattern (SPIKE/AFTERSHOCK/SILENCE)
       - book_pattern (TOP_GAP/DEPTH_EVAPORATION/SPREAD_SHOCK)
       - range_pattern (MEAN_REVERT/PINNING/BREAKOUT)
       - correlation_pattern (TIGHTEN/DECOUPLE/ROTATION)
    2. Default → first subtype for parent (D1A, D2A, etc.)

Subtype ≠ Action
Subtype = Fine-grained label propagation
"""

from typing import Any, Dict, List, Optional

from .v12_distortion_subtype_schema import (
    V12DistortionSubtypeSchema,
    PARENT_D1_LIQUIDATION,
    PARENT_D2_RANGE_STICKINESS,
    PARENT_D3_BOOK_HOLLOWING,
    PARENT_D4_EVENT_DISTORTION,
    PARENT_D5_CORRELATION_DISTORTION,
    PARENT_UNCLASSIFIED,
    SUBTYPE_D1A_FORCED_FLOW,
    SUBTYPE_D1B_CASCADE_RISK,
    SUBTYPE_D1C_STRESS_UNWIND,
    SUBTYPE_D2A_MEAN_REVERT_PRESSURE,
    SUBTYPE_D2B_RANGE_PINNING,
    SUBTYPE_D2C_BREAKOUT_FAKEOUT,
    SUBTYPE_D3A_TOP_GAP,
    SUBTYPE_D3B_DEPTH_EVAPORATION,
    SUBTYPE_D3C_SPREAD_SHOCK,
    SUBTYPE_D4A_EVENT_SPIKE,
    SUBTYPE_D4B_EVENT_AFTERSHOCK,
    SUBTYPE_D4C_EVENT_SILENCE,
    SUBTYPE_D5A_COUPLING_TIGHTEN,
    SUBTYPE_D5B_DECOUPLING,
    SUBTYPE_D5C_ROTATION_PRESSURE,
)


def _safe_get(d: Optional[Dict[str, Any]], key: str, default: Any = None) -> Any:
    """
    Safely get value from dict.

    Args:
        d: Dictionary (may be None)
        key: Key to get
        default: Default value if not found

    Returns:
        Value or default
    """
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def classify_distortion_subtype_v1(
    parent_distortion_record: Optional[Dict[str, Any]] = None,
    normalized_observation: Optional[Dict[str, Any]] = None,
    analytics: Optional[Dict[str, Any]] = None,
    vocabulary: Optional[Dict[str, Any]] = None,
    regime_record: Optional[Dict[str, Any]] = None,
    drift_record: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Classify distortion subtype using qualitative labels.

    Args:
        parent_distortion_record: PR129 parent distortion record
        normalized_observation: Optional normalized observation
        analytics: Optional analytics dict with qualitative labels
        vocabulary: Optional vocabulary record
        regime_record: Optional PR110 regime record
        drift_record: Optional drift record

    Returns:
        Distortion subtype record (always valid, ERROR on failure)
    """
    try:
        basis = []

        # Extract parent distortion type
        parent_distortion = _safe_get(parent_distortion_record, "v12_distortion_type", PARENT_UNCLASSIFIED)
        if parent_distortion_record:
            basis.append("v12_distortion_type")

        # Extract qualitative inputs from analytics
        market_cost_regime = _safe_get(analytics, "market_cost_regime", "UNCLASSIFIED")
        liquidity_regime = _safe_get(analytics, "liquidity_regime", "UNCLASSIFIED")
        event_activity_present = _safe_get(analytics, "event_activity_present", False)
        event_pattern = _safe_get(analytics, "event_pattern", "UNCLASSIFIED")
        book_pattern = _safe_get(analytics, "book_pattern", "UNCLASSIFIED")
        range_pattern = _safe_get(analytics, "range_pattern", "UNCLASSIFIED")
        correlation_pattern = _safe_get(analytics, "correlation_pattern", "UNCLASSIFIED")

        if analytics:
            basis.append("analytics")

        # -----------------------------
        # Rule 0: Defensive (invalid inputs)
        # -----------------------------
        if parent_distortion == PARENT_UNCLASSIFIED:
            return V12DistortionSubtypeSchema.create_error_record(
                "invalid inputs: parent_distortion must be classified.",
            )

        # -----------------------------
        # Rule 1: Classify by parent distortion type
        # -----------------------------

        # D1 (Liquidation) subtypes
        if parent_distortion == PARENT_D1_LIQUIDATION:
            subtype = _classify_d1_subtype(market_cost_regime, liquidity_regime)
            return V12DistortionSubtypeSchema.create_subtype_record(
                parent_distortion=parent_distortion,
                subtype_label=subtype,
                basis=basis,
            )

        # D2 (Range Stickiness) subtypes
        if parent_distortion == PARENT_D2_RANGE_STICKINESS:
            subtype = _classify_d2_subtype(range_pattern)
            return V12DistortionSubtypeSchema.create_subtype_record(
                parent_distortion=parent_distortion,
                subtype_label=subtype,
                basis=basis,
            )

        # D3 (Book Hollowing) subtypes
        if parent_distortion == PARENT_D3_BOOK_HOLLOWING:
            subtype = _classify_d3_subtype(book_pattern)
            return V12DistortionSubtypeSchema.create_subtype_record(
                parent_distortion=parent_distortion,
                subtype_label=subtype,
                basis=basis,
            )

        # D4 (Event Distortion) subtypes
        if parent_distortion == PARENT_D4_EVENT_DISTORTION:
            subtype = _classify_d4_subtype(event_pattern)
            return V12DistortionSubtypeSchema.create_subtype_record(
                parent_distortion=parent_distortion,
                subtype_label=subtype,
                basis=basis,
            )

        # D5 (Correlation Distortion) subtypes
        if parent_distortion == PARENT_D5_CORRELATION_DISTORTION:
            subtype = _classify_d5_subtype(correlation_pattern)
            return V12DistortionSubtypeSchema.create_subtype_record(
                parent_distortion=parent_distortion,
                subtype_label=subtype,
                basis=basis,
            )

        # -----------------------------
        # Rule 2: Default → error (unrecognized parent)
        # -----------------------------
        return V12DistortionSubtypeSchema.create_error_record(
            f"unrecognized parent distortion: {parent_distortion}",
            parent_distortion=parent_distortion,
        )

    except Exception as e:
        return V12DistortionSubtypeSchema.create_error_record(
            f"exception: {type(e).__name__}",
        )


def _classify_d1_subtype(market_cost_regime: str, liquidity_regime: str) -> str:
    """
    Classify D1 (Liquidation) subtype.

    Args:
        market_cost_regime: Market cost regime (HIGH/MEDIUM/LOW)
        liquidity_regime: Liquidity regime (HIGH/MEDIUM/LOW/DECREASING)

    Returns:
        D1 subtype
    """
    # D1B: Cascade risk (high cost + decreasing liquidity)
    if market_cost_regime == "HIGH" and liquidity_regime == "DECREASING":
        return SUBTYPE_D1B_CASCADE_RISK

    # D1A: Forced flow (high cost + low liquidity)
    if market_cost_regime == "HIGH" and liquidity_regime == "LOW":
        return SUBTYPE_D1A_FORCED_FLOW

    # D1C: Stress unwind (moderate cost + low liquidity)
    if market_cost_regime == "MEDIUM" and liquidity_regime == "LOW":
        return SUBTYPE_D1C_STRESS_UNWIND

    # Default: D1A
    return SUBTYPE_D1A_FORCED_FLOW


def _classify_d2_subtype(range_pattern: str) -> str:
    """
    Classify D2 (Range Stickiness) subtype.

    Args:
        range_pattern: Range pattern (MEAN_REVERT/PINNING/BREAKOUT)

    Returns:
        D2 subtype
    """
    # D2A: Mean revert pressure
    if range_pattern == "MEAN_REVERT":
        return SUBTYPE_D2A_MEAN_REVERT_PRESSURE

    # D2B: Range pinning
    if range_pattern == "PINNING":
        return SUBTYPE_D2B_RANGE_PINNING

    # D2C: Breakout fakeout
    if range_pattern == "BREAKOUT":
        return SUBTYPE_D2C_BREAKOUT_FAKEOUT

    # Default: D2A
    return SUBTYPE_D2A_MEAN_REVERT_PRESSURE


def _classify_d3_subtype(book_pattern: str) -> str:
    """
    Classify D3 (Book Hollowing) subtype.

    Args:
        book_pattern: Book pattern (TOP_GAP/DEPTH_EVAPORATION/SPREAD_SHOCK)

    Returns:
        D3 subtype
    """
    # D3A: Top gap
    if book_pattern == "TOP_GAP":
        return SUBTYPE_D3A_TOP_GAP

    # D3B: Depth evaporation
    if book_pattern == "DEPTH_EVAPORATION":
        return SUBTYPE_D3B_DEPTH_EVAPORATION

    # D3C: Spread shock
    if book_pattern == "SPREAD_SHOCK":
        return SUBTYPE_D3C_SPREAD_SHOCK

    # Default: D3A
    return SUBTYPE_D3A_TOP_GAP


def _classify_d4_subtype(event_pattern: str) -> str:
    """
    Classify D4 (Event Distortion) subtype.

    Args:
        event_pattern: Event pattern (SPIKE/AFTERSHOCK/SILENCE)

    Returns:
        D4 subtype
    """
    # D4A: Event spike
    if event_pattern == "SPIKE":
        return SUBTYPE_D4A_EVENT_SPIKE

    # D4B: Event aftershock
    if event_pattern == "AFTERSHOCK":
        return SUBTYPE_D4B_EVENT_AFTERSHOCK

    # D4C: Event silence
    if event_pattern == "SILENCE":
        return SUBTYPE_D4C_EVENT_SILENCE

    # Default: D4A
    return SUBTYPE_D4A_EVENT_SPIKE


def _classify_d5_subtype(correlation_pattern: str) -> str:
    """
    Classify D5 (Correlation Distortion) subtype.

    Args:
        correlation_pattern: Correlation pattern (TIGHTEN/DECOUPLE/ROTATION)

    Returns:
        D5 subtype
    """
    # D5A: Coupling tighten
    if correlation_pattern == "TIGHTEN":
        return SUBTYPE_D5A_COUPLING_TIGHTEN

    # D5B: Decoupling
    if correlation_pattern == "DECOUPLE":
        return SUBTYPE_D5B_DECOUPLING

    # D5C: Rotation pressure
    if correlation_pattern == "ROTATION":
        return SUBTYPE_D5C_ROTATION_PRESSURE

    # Default: D5A
    return SUBTYPE_D5A_COUPLING_TIGHTEN


def get_distortion_subtype_classifier_v1_info() -> Dict[str, Any]:
    """
    Get distortion subtype classifier v1 information.

    Returns:
        Dict with classifier metadata
    """
    return {
        "classifier_version": "v1",
        "classifier_type": "distortion_subtype",
        "input_schema": "parent_distortion + analytics (qualitative labels)",
        "output_schema": "v12_subtype",
        "classification_rules": [
            "invalid_inputs → ERROR",
            "D1_LIQUIDATION → D1A/D1B/D1C (market_cost × liquidity)",
            "D2_RANGE_STICKINESS → D2A/D2B/D2C (range_pattern)",
            "D3_BOOK_HOLLOWING → D3A/D3B/D3C (book_pattern)",
            "D4_EVENT_DISTORTION → D4A/D4B/D4C (event_pattern)",
            "D5_CORRELATION_DISTORTION → D5A/D5B/D5C (correlation_pattern)",
            "default → first subtype for parent",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_subtype_coupling",
            "deterministic",
            "defensive",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Distortion Subtype Classifier v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Invalid input → ERROR
    print("Test 1: Invalid input → ERROR")
    result1 = classify_distortion_subtype_v1(
        parent_distortion_record={"v12_distortion_type": PARENT_UNCLASSIFIED},
    )
    print(f"Status: {result1['v12_subtype_status']}")
    print()

    # Test 2: D1 classification (cascade risk)
    print("Test 2: D1 classification (cascade risk)")
    result2 = classify_distortion_subtype_v1(
        parent_distortion_record={"v12_distortion_type": PARENT_D1_LIQUIDATION},
        analytics={"market_cost_regime": "HIGH", "liquidity_regime": "DECREASING"},
    )
    print(f"Subtype: {result2['v12_subtype_label']}")
    print()

    # Test 3: D2 classification (mean revert)
    print("Test 3: D2 classification (mean revert)")
    result3 = classify_distortion_subtype_v1(
        parent_distortion_record={"v12_distortion_type": PARENT_D2_RANGE_STICKINESS},
        analytics={"range_pattern": "MEAN_REVERT"},
    )
    print(f"Subtype: {result3['v12_subtype_label']}")
    print()

    # Test 4: D4 classification (event spike)
    print("Test 4: D4 classification (event spike)")
    result4 = classify_distortion_subtype_v1(
        parent_distortion_record={"v12_distortion_type": PARENT_D4_EVENT_DISTORTION},
        analytics={"event_pattern": "SPIKE"},
    )
    print(f"Subtype: {result4['v12_subtype_label']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
