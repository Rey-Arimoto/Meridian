#!/usr/bin/env python3
"""
PR119: v1.0 Market Structure Vocabulary Builder v1 (READ-ONLY)

Purpose:
    Convert onchain analytics (PR109) into market structure vocabulary terms.
    Builder = Converter (not evaluator/recommender).

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No numeric amounts: No counts, prices, balances
    - Builder = converter (not evaluation/action)

Builder Philosophy:
    Builder ≠ Evaluation
    Builder ≠ Recommendation
    Builder = Analytics → Vocabulary Converter

    Builder provides:
    - Analytics → vocabulary term mapping
    - Presence/absence conversion
    - Static conversion rules
    - Defensive handling

    Builder does NOT:
    - Evaluate quality
    - Recommend actions
    - Emit amounts or counts
    - Threshold or classify

Conversion Rules (v1 - Static):

Rule 1: Market Cost Regime Presence
    - If market_cost_regime_counts has any count > 0 for "LOW" → COST_LOW_PRESENT
    - If market_cost_regime_counts has any count > 0 for "MEDIUM" → COST_MEDIUM_PRESENT
    - If market_cost_regime_counts has any count > 0 for "HIGH" → COST_HIGH_PRESENT

Rule 2: Liquidity Regime Presence
    - If liquidity_regime_presence["LOW"] is True → LIQUIDITY_LOW_PRESENT
    - If liquidity_regime_presence["MEDIUM"] is True → LIQUIDITY_MEDIUM_PRESENT
    - If liquidity_regime_presence["HIGH"] is True → LIQUIDITY_HIGH_PRESENT

Rule 3: Event Activity
    - If event_activity_frequency["TRUE"] > 0 → EVENT_ACTIVITY_PRESENT
    - Otherwise → EVENT_ACTIVITY_ABSENT

Rule 4: Object Dynamics Presence
    - If object_dynamics_distribution["DECREASE"] > 0 → OBJECT_DYNAMICS_DECREASE_PRESENT
    - If object_dynamics_distribution["STABLE"] > 0 → OBJECT_DYNAMICS_STABLE_PRESENT
    - If object_dynamics_distribution["INCREASE"] > 0 → OBJECT_DYNAMICS_INCREASE_PRESENT
"""

from typing import Any, Dict, List, Optional
from .v10_market_structure_vocabulary_schema import V10MarketStructureVocabularySchema


def build_market_structure_vocabulary_v1(
    onchain_analytics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build market structure vocabulary from onchain analytics.

    Args:
        onchain_analytics: Onchain analytics record (from PR109)

    Returns:
        Vocabulary record (always valid)

    Design:
        - Static conversion rules (if/elif)
        - Defensive (None/invalid → ERROR record)
        - Warning-only (never raises)
        - Always returns valid records
    """
    warnings: List[str] = []

    # Defensive: validate analytics input
    if not isinstance(onchain_analytics, dict):
        return V10MarketStructureVocabularySchema.create_error_record(
            error_info="invalid analytics input (None or not dict)",
            warnings=["Onchain analytics must be dict"],
        )

    # Check analytics status
    if onchain_analytics.get("onchain_analytics_status") != "AVAILABLE":
        return V10MarketStructureVocabularySchema.create_error_record(
            error_info=f"analytics status not AVAILABLE: {onchain_analytics.get('onchain_analytics_status')}",
            warnings=["Analytics must have AVAILABLE status"],
        )

    # Extract vocabulary terms
    terms: List[str] = []
    basis: List[str] = []

    # Rule 1: Market cost regime presence
    market_cost_counts = onchain_analytics.get("market_cost_regime_counts", {})
    if isinstance(market_cost_counts, dict):
        basis.append("market_cost_regime_counts")
        if market_cost_counts.get("LOW", 0) > 0:
            terms.append("COST_LOW_PRESENT")
        if market_cost_counts.get("MEDIUM", 0) > 0:
            terms.append("COST_MEDIUM_PRESENT")
        if market_cost_counts.get("HIGH", 0) > 0:
            terms.append("COST_HIGH_PRESENT")

    # Rule 2: Liquidity regime presence
    liquidity_presence = onchain_analytics.get("liquidity_regime_presence", {})
    if isinstance(liquidity_presence, dict):
        basis.append("liquidity_regime_presence")
        if liquidity_presence.get("LOW", False):
            terms.append("LIQUIDITY_LOW_PRESENT")
        if liquidity_presence.get("MEDIUM", False):
            terms.append("LIQUIDITY_MEDIUM_PRESENT")
        if liquidity_presence.get("HIGH", False):
            terms.append("LIQUIDITY_HIGH_PRESENT")

    # Rule 3: Event activity
    event_frequency = onchain_analytics.get("event_activity_frequency", {})
    if isinstance(event_frequency, dict):
        basis.append("event_activity_frequency")
        if event_frequency.get("TRUE", 0) > 0:
            terms.append("EVENT_ACTIVITY_PRESENT")
        else:
            terms.append("EVENT_ACTIVITY_ABSENT")

    # Rule 4: Object dynamics presence
    object_dynamics = onchain_analytics.get("object_dynamics_distribution", {})
    if isinstance(object_dynamics, dict):
        basis.append("object_dynamics_distribution")
        if object_dynamics.get("DECREASE", 0) > 0:
            terms.append("OBJECT_DYNAMICS_DECREASE_PRESENT")
        if object_dynamics.get("STABLE", 0) > 0:
            terms.append("OBJECT_DYNAMICS_STABLE_PRESENT")
        if object_dynamics.get("INCREASE", 0) > 0:
            terms.append("OBJECT_DYNAMICS_INCREASE_PRESENT")

    # Build summary
    term_count = len(terms)
    summary = (
        f"market structure vocabulary with {term_count} terms. "
        f"converted from onchain analytics using presence rules."
    )

    # Create vocabulary record
    vocab = V10MarketStructureVocabularySchema.create_vocabulary_record(
        terms=terms,
        summary=summary,
        basis=basis,
        warnings=warnings if warnings else None,
    )

    # Validate vocabulary against constitutional guard
    from .v10_vocab_constitutional_guard import validate_vocabulary_record

    guard_warnings = validate_vocabulary_record(vocab)
    if guard_warnings:
        # Add guard warnings to vocabulary warnings
        existing_warnings = vocab.get("v10_vocab_warnings", [])
        all_warnings = existing_warnings + guard_warnings
        vocab["v10_vocab_warnings"] = all_warnings

    return vocab


def get_vocabulary_builder_v1_info() -> Dict[str, Any]:
    """
    Get vocabulary builder v1 information.

    Returns:
        Dict with builder metadata
    """
    return {
        "builder_version": "v1",
        "builder_type": "market_structure_vocabulary",
        "conversion_rules": {
            "rule_1": "Market cost regime presence (LOW/MEDIUM/HIGH)",
            "rule_2": "Liquidity regime presence (LOW/MEDIUM/HIGH)",
            "rule_3": "Event activity (PRESENT/ABSENT)",
            "rule_4": "Object dynamics presence (DECREASE/STABLE/INCREASE)",
        },
        "defensive": True,
        "warning_only": True,
        "constitutional_validation": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.0 Market Structure Vocabulary Builder v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Build vocabulary from mock analytics (case A)
    print("Test 1: Build vocabulary from mock analytics (stable/low)")
    mock_analytics_a = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 8, "MEDIUM": 1, "HIGH": 1},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": False, "HIGH": False},
        "event_activity_frequency": {"TRUE": 2, "FALSE": 8},
        "object_dynamics_distribution": {"DECREASE": 0, "STABLE": 9, "INCREASE": 1},
        "observation_count": 10,
    }

    vocab_a = build_market_structure_vocabulary_v1(mock_analytics_a)
    print(f"Status: {vocab_a.get('v10_vocab_status')}")
    print(f"Terms: {vocab_a.get('v10_vocab_terms')}")
    print(f"Term count: {len(vocab_a.get('v10_vocab_terms', []))}")
    print()

    # Test 2: Build vocabulary from mock analytics (case B)
    print("Test 2: Build vocabulary from mock analytics (high variation)")
    mock_analytics_b = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 3, "MEDIUM": 4, "HIGH": 3},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": True, "HIGH": True},
        "event_activity_frequency": {"TRUE": 6, "FALSE": 4},
        "object_dynamics_distribution": {"DECREASE": 3, "STABLE": 4, "INCREASE": 3},
        "observation_count": 10,
    }

    vocab_b = build_market_structure_vocabulary_v1(mock_analytics_b)
    print(f"Status: {vocab_b.get('v10_vocab_status')}")
    print(f"Terms: {vocab_b.get('v10_vocab_terms')}")
    print(f"Term count: {len(vocab_b.get('v10_vocab_terms', []))}")
    print()

    # Test 3: Build vocabulary from None input (defensive)
    print("Test 3: Build vocabulary from None input (defensive)")
    vocab_none = build_market_structure_vocabulary_v1(None)
    print(f"Status: {vocab_none.get('v10_vocab_status')}")
    print(f"Error info: {vocab_none.get('v10_vocab_error_info')}")
    print()

    # Test 4: Build vocabulary from invalid status
    print("Test 4: Build vocabulary from invalid status")
    invalid_analytics = {
        "onchain_analytics_status": "ERROR",
    }
    vocab_invalid = build_market_structure_vocabulary_v1(invalid_analytics)
    print(f"Status: {vocab_invalid.get('v10_vocab_status')}")
    print(f"Error info: {vocab_invalid.get('v10_vocab_error_info')}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
