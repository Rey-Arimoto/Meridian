#!/usr/bin/env python3
"""
PR110: v1.1 Entropy Regime Classifier v1 (READ-ONLY)

Purpose:
    Classify entropy regime from onchain analytics.
    Classifier = State Classification (not action).

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Regime labels only
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No execution vocabulary: No buy, sell, trade, swap
    - Non-evaluative: No good/bad vocabulary
    - Defensive: Never raises, returns REGIME_CRITICAL on error

Classifier Philosophy:
    Classifier ≠ Action
    Classifier ≠ Optimization
    Classifier = State Label

    Classifier evaluates:
    - Market cost regime distribution (concentrated vs dispersed)
    - Liquidity regime presence (single vs multiple)
    - Event activity patterns (active vs quiet)
    - Object dynamics patterns (stable vs volatile)
    - Observation count (sufficient vs insufficient)

    Classifier does NOT:
    - Recommend trades
    - Evaluate profitability
    - Suggest positions
    - Optimize outcomes

Classification Logic:
    REGIME_LOW:
        - Observations present (count > 0)
        - Single dominant market cost regime
        - Single liquidity regime present
        - Stable object dynamics
        - Low event activity variation

    REGIME_MEDIUM:
        - Observations present
        - Moderate market cost variation
        - Multiple liquidity regimes
        - Mixed object dynamics
        - Moderate event activity

    REGIME_HIGH:
        - Observations present
        - High market cost variation
        - All liquidity regimes present
        - Volatile object dynamics
        - High event activity variation

    REGIME_CRITICAL:
        - No observations (count = 0)
        - Analytics unavailable
        - Error state
        - Extreme variation patterns
"""

from typing import Any, Dict, List, Optional
from .v11_entropy_regime_schema import V11EntropyRegimeSchema


def classify_entropy_regime_v1(
    onchain_analytics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Classify entropy regime from onchain analytics.

    Args:
        onchain_analytics: Onchain analytics aggregation (from PR109)

    Returns:
        Regime classification record

    Design:
        - Defensive (None/invalid → REGIME_CRITICAL)
        - Warning-only (never raises)
        - Rule-based classification
        - Basis tracks which analytics informed regime
    """
    import time

    # Validate input
    if not isinstance(onchain_analytics, dict):
        return V11EntropyRegimeSchema.create_error_record(
            error_info="invalid onchain analytics type",
        )

    # Check analytics status
    if onchain_analytics.get("onchain_analytics_status") != "AVAILABLE":
        return V11EntropyRegimeSchema.create_error_record(
            error_info="onchain analytics not available",
        )

    # Extract observation count
    observation_count = onchain_analytics.get("observation_count", 0)

    # REGIME_CRITICAL: No observations
    if observation_count == 0:
        return V11EntropyRegimeSchema.create_regime_record(
            regime_level="REGIME_CRITICAL",
            basis=["observation_count"],
        )

    # Extract analytics
    market_cost_counts = onchain_analytics.get("market_cost_regime_counts", {})
    liquidity_presence = onchain_analytics.get("liquidity_regime_presence", {})
    event_frequency = onchain_analytics.get("event_activity_frequency", {})
    object_distribution = onchain_analytics.get("object_dynamics_distribution", {})

    # Calculate variation metrics
    basis = []

    # 1. Market cost regime variation
    market_cost_variation = _calculate_distribution_variation(market_cost_counts)
    basis.append("market_cost_regime_counts")

    # 2. Liquidity regime diversity
    liquidity_diversity = sum(1 for present in liquidity_presence.values() if present)
    basis.append("liquidity_regime_presence")

    # 3. Event activity variation
    event_variation = _calculate_distribution_variation(event_frequency)
    basis.append("event_activity_frequency")

    # 4. Object dynamics variation
    object_variation = _calculate_distribution_variation(object_distribution)
    basis.append("object_dynamics_distribution")

    # Classify regime based on variation metrics
    # Count how many metrics are elevated
    # High threshold: near-maximum entropy (balanced distribution)
    high_metrics = 0
    if market_cost_variation >= 0.9:
        high_metrics += 1
    if liquidity_diversity >= 3:
        high_metrics += 1
    if event_variation >= 0.9:
        high_metrics += 1
    if object_variation >= 0.9:
        high_metrics += 1

    # Medium threshold: moderate entropy
    medium_metrics = 0
    if market_cost_variation >= 0.5:
        medium_metrics += 1
    if liquidity_diversity >= 2:
        medium_metrics += 1
    if event_variation >= 0.5:
        medium_metrics += 1
    if object_variation >= 0.5:
        medium_metrics += 1

    # REGIME_CRITICAL: All metrics at maximum variation (extreme conditions)
    if high_metrics >= 4:
        return V11EntropyRegimeSchema.create_regime_record(
            regime_level="REGIME_CRITICAL",
            basis=basis,
        )

    # REGIME_HIGH: Multiple metrics at high variation
    if high_metrics >= 2:
        return V11EntropyRegimeSchema.create_regime_record(
            regime_level="REGIME_HIGH",
            basis=basis,
        )

    # REGIME_MEDIUM: Some metrics at moderate variation
    if medium_metrics >= 2:
        return V11EntropyRegimeSchema.create_regime_record(
            regime_level="REGIME_MEDIUM",
            basis=basis,
        )

    # REGIME_LOW: Low variation (all metrics low)
    return V11EntropyRegimeSchema.create_regime_record(
        regime_level="REGIME_LOW",
        basis=basis,
    )


def _calculate_distribution_variation(distribution: Dict[str, int]) -> float:
    """
    Calculate variation in a distribution.

    Returns value between 0.0 (concentrated) and 1.0 (dispersed).

    Args:
        distribution: Distribution of counts

    Returns:
        Variation metric (0.0 to 1.0)
    """
    if not isinstance(distribution, dict) or not distribution:
        return 0.0

    counts = list(distribution.values())
    total = sum(counts)

    if total == 0:
        return 0.0

    # Calculate normalized entropy
    # High entropy = dispersed (high variation)
    # Low entropy = concentrated (low variation)
    import math
    entropy = 0.0
    for count in counts:
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)

    # Normalize to [0, 1]
    # Maximum entropy for n categories is log2(n)
    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    return normalized_entropy


def get_regime_classifier_v1_info() -> Dict[str, Any]:
    """
    Get regime classifier v1 information.

    Returns:
        Dict with classifier metadata
    """
    return {
        "classifier_version": "v1",
        "classifier_type": "entropy_regime",
        "regime_levels": [
            "REGIME_LOW",
            "REGIME_MEDIUM",
            "REGIME_HIGH",
            "REGIME_CRITICAL",
        ],
        "inputs": [
            "market_cost_regime_counts",
            "liquidity_regime_presence",
            "event_activity_frequency",
            "object_dynamics_distribution",
            "observation_count",
        ],
        "defensive": True,
        "warning_only": True,
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Entropy Regime Classifier v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: REGIME_LOW (concentrated, stable)
    print("Test 1: REGIME_LOW (concentrated, stable)")
    low_analytics = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 10, "MEDIUM": 0, "HIGH": 0},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": False, "HIGH": False},
        "event_activity_frequency": {"TRUE": 0, "FALSE": 10},
        "object_dynamics_distribution": {"DECREASE": 0, "STABLE": 10, "INCREASE": 0},
        "observation_count": 10,
    }
    regime_low = classify_entropy_regime_v1(low_analytics)
    print(json.dumps(regime_low, indent=2))
    print()

    # Test 2: REGIME_MEDIUM (moderate variation)
    print("Test 2: REGIME_MEDIUM (moderate variation)")
    medium_analytics = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 3, "MEDIUM": 5, "HIGH": 2},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": True, "HIGH": False},
        "event_activity_frequency": {"TRUE": 5, "FALSE": 5},
        "object_dynamics_distribution": {"DECREASE": 2, "STABLE": 6, "INCREASE": 2},
        "observation_count": 10,
    }
    regime_medium = classify_entropy_regime_v1(medium_analytics)
    print(json.dumps(regime_medium, indent=2))
    print()

    # Test 3: REGIME_HIGH (elevated variation)
    print("Test 3: REGIME_HIGH (elevated variation)")
    high_analytics = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 2, "MEDIUM": 3, "HIGH": 5},
        "liquidity_regime_presence": {"LOW": True, "MEDIUM": True, "HIGH": True},
        "event_activity_frequency": {"TRUE": 7, "FALSE": 3},
        "object_dynamics_distribution": {"DECREASE": 3, "STABLE": 2, "INCREASE": 5},
        "observation_count": 10,
    }
    regime_high = classify_entropy_regime_v1(high_analytics)
    print(json.dumps(regime_high, indent=2))
    print()

    # Test 4: REGIME_CRITICAL (no observations)
    print("Test 4: REGIME_CRITICAL (no observations)")
    critical_analytics = {
        "onchain_analytics_mode": "ON",
        "onchain_analytics_status": "AVAILABLE",
        "market_cost_regime_counts": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
        "liquidity_regime_presence": {"LOW": False, "MEDIUM": False, "HIGH": False},
        "event_activity_frequency": {"TRUE": 0, "FALSE": 0},
        "object_dynamics_distribution": {"DECREASE": 0, "STABLE": 0, "INCREASE": 0},
        "observation_count": 0,
    }
    regime_critical = classify_entropy_regime_v1(critical_analytics)
    print(json.dumps(regime_critical, indent=2))
    print()

    # Test 5: Error case (invalid analytics)
    print("Test 5: Error case (invalid analytics)")
    error_regime = classify_entropy_regime_v1("invalid")  # type: ignore
    print(json.dumps(error_regime, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
