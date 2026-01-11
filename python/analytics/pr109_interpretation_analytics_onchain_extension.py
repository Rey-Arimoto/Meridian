#!/usr/bin/env python3
"""
PR109: v1.0 Interpretation Analytics Extension (Onchain-Aware)

Purpose:
    Extend interpretation analytics to include onchain observations.
    Analytics = Meaning Generation (not execution).

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No amounts: Counts only (no numeric values)
    - No token literals: No SUI, USDC, BTC, ETH
    - No addresses: No wallet/contract addresses
    - No asset vocabulary: No balance, holdings, portfolio
    - No execution vocabulary: No buy, sell, trade, swap
    - Non-evaluative: No good/bad vocabulary

Analytics Philosophy:
    Analytics ≠ Action
    Analytics ≠ Evaluation
    Analytics = State Classification

    Analytics aggregates onchain observations:
    - market_cost_regime_counts (LOW/MEDIUM/HIGH counts)
    - liquidity_regime_presence (presence flags)
    - event_activity_frequency (activity frequency)
    - object_dynamics_distribution (DECREASE/STABLE/INCREASE counts)

    Analytics does NOT:
    - Make trading decisions
    - Provide recommendations
    - Evaluate good/bad
    - Execute operations

Extension Design:
    - Input: normalized observations (PR108)
    - Output: onchain-aware analytics record
    - Aggregation only (no interpretation)
    - Defensive (handles None/empty gracefully)
"""

from typing import Any, Dict, List, Optional


def aggregate_onchain_observations(
    normalized_observations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate onchain observations for interpretation analytics.

    Args:
        normalized_observations: List of normalized observation records (PR108)

    Returns:
        Onchain analytics aggregation record

    Design:
        - Defensive (None/empty → empty aggregation)
        - Warning-only (never raises)
        - Counts only (no numeric values)
    """
    # Initialize aggregation record
    aggregation = {
        "onchain_analytics_mode": "OFF",
        "onchain_analytics_status": "UNAVAILABLE",
        "market_cost_regime_counts": {},
        "liquidity_regime_presence": {},
        "event_activity_frequency": {},
        "object_dynamics_distribution": {},
        "observation_count": 0,
    }

    # Validate input
    if not normalized_observations or not isinstance(normalized_observations, list):
        return aggregation

    # Filter AVAILABLE observations
    available_observations = [
        obs for obs in normalized_observations
        if isinstance(obs, dict) and obs.get("v10_norm_obs_status") == "AVAILABLE"
    ]

    if not available_observations:
        return aggregation

    # Update mode and status
    aggregation["onchain_analytics_mode"] = "ON"
    aggregation["onchain_analytics_status"] = "AVAILABLE"
    aggregation["observation_count"] = len(available_observations)

    # Aggregate market cost regime
    market_cost_regime_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
    for obs in available_observations:
        regime = obs.get("v10_norm_obs_market_cost_regime")
        if regime in market_cost_regime_counts:
            market_cost_regime_counts[regime] += 1

    aggregation["market_cost_regime_counts"] = market_cost_regime_counts

    # Aggregate liquidity regime presence
    liquidity_regime_presence = {"LOW": False, "MEDIUM": False, "HIGH": False}
    for obs in available_observations:
        regime = obs.get("v10_norm_obs_liquidity_regime")
        if regime in liquidity_regime_presence:
            liquidity_regime_presence[regime] = True

    aggregation["liquidity_regime_presence"] = liquidity_regime_presence

    # Aggregate event activity frequency
    event_activity_frequency = {"TRUE": 0, "FALSE": 0}
    for obs in available_observations:
        activity = obs.get("v10_norm_obs_event_activity_present")
        if activity in event_activity_frequency:
            event_activity_frequency[activity] += 1

    aggregation["event_activity_frequency"] = event_activity_frequency

    # Aggregate object dynamics distribution
    object_dynamics_distribution = {"DECREASE": 0, "STABLE": 0, "INCREASE": 0}
    for obs in available_observations:
        dynamics = obs.get("v10_norm_obs_object_dynamics")
        if dynamics in object_dynamics_distribution:
            object_dynamics_distribution[dynamics] += 1

    aggregation["object_dynamics_distribution"] = object_dynamics_distribution

    return aggregation


def extend_interpretation_analytics_v1(
    base_analytics: Optional[Dict[str, Any]],
    normalized_observations: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Extend interpretation analytics with onchain observations.

    Args:
        base_analytics: Base interpretation analytics record (v0.6)
        normalized_observations: Optional list of normalized observations (PR108)

    Returns:
        Extended interpretation analytics record

    Design:
        - Defensive (None → empty extension)
        - Warning-only (never raises)
        - Preserves base analytics
        - Adds onchain analytics as extension
    """
    # Initialize extended analytics
    extended_analytics = {
        "analytics_mode": "OFF",
        "analytics_status": "UNAVAILABLE",
        "analytics_summary": "interpretation analytics not available.",
    }

    # Preserve base analytics if provided
    if base_analytics and isinstance(base_analytics, dict):
        extended_analytics.update(base_analytics)
    else:
        # Create minimal base analytics
        extended_analytics = {
            "analytics_mode": "ON",
            "analytics_status": "AVAILABLE",
            "analytics_summary": "interpretation analytics with onchain extension.",
        }

    # Aggregate onchain observations
    if normalized_observations:
        onchain_aggregation = aggregate_onchain_observations(normalized_observations)
        extended_analytics["onchain_analytics"] = onchain_aggregation
    else:
        # No onchain observations available
        extended_analytics["onchain_analytics"] = {
            "onchain_analytics_mode": "OFF",
            "onchain_analytics_status": "UNAVAILABLE",
            "market_cost_regime_counts": {},
            "liquidity_regime_presence": {},
            "event_activity_frequency": {},
            "object_dynamics_distribution": {},
            "observation_count": 0,
        }

    return extended_analytics


def get_onchain_analytics_summary(
    onchain_analytics: Dict[str, Any]
) -> str:
    """
    Generate human-readable summary of onchain analytics.

    Args:
        onchain_analytics: Onchain analytics aggregation

    Returns:
        Summary string

    Design:
        - No amounts, no token names
        - Qualitative descriptions only
        - No evaluative vocabulary
    """
    if onchain_analytics.get("onchain_analytics_status") != "AVAILABLE":
        return "onchain analytics unavailable. no observations aggregated."

    observation_count = onchain_analytics.get("observation_count", 0)
    if observation_count == 0:
        return "onchain analytics available. no observations to aggregate."

    # Describe observation count (bucketed)
    if observation_count == 1:
        count_desc = "single observation"
    elif observation_count < 5:
        count_desc = "few observations"
    elif observation_count < 10:
        count_desc = "several observations"
    else:
        count_desc = "multiple observations"

    # Describe market cost regime
    market_cost_counts = onchain_analytics.get("market_cost_regime_counts", {})
    dominant_regime = max(market_cost_counts, key=market_cost_counts.get) if market_cost_counts else None

    # Describe liquidity regime
    liquidity_presence = onchain_analytics.get("liquidity_regime_presence", {})
    present_regimes = [k for k, v in liquidity_presence.items() if v]

    # Describe event activity
    event_frequency = onchain_analytics.get("event_activity_frequency", {})
    active_count = event_frequency.get("TRUE", 0)

    # Describe object dynamics
    object_distribution = onchain_analytics.get("object_dynamics_distribution", {})
    dominant_dynamics = max(object_distribution, key=object_distribution.get) if object_distribution else None

    summary_parts = [
        f"onchain analytics aggregated from {count_desc}.",
    ]

    if dominant_regime:
        summary_parts.append(f"market cost regime observed as {dominant_regime}.")

    if present_regimes:
        regime_desc = "multiple regimes" if len(present_regimes) > 1 else present_regimes[0]
        summary_parts.append(f"liquidity regime presence: {regime_desc}.")

    if active_count > 0:
        summary_parts.append("event activity detected in observations.")

    if dominant_dynamics:
        summary_parts.append(f"object dynamics shows {dominant_dynamics} pattern.")

    return " ".join(summary_parts)


def get_interpretation_analytics_onchain_extension_info() -> Dict[str, Any]:
    """
    Get interpretation analytics onchain extension information.

    Returns:
        Dict with extension metadata
    """
    return {
        "extension_version": "v1",
        "extension_type": "interpretation_analytics_onchain",
        "aggregations": [
            "market_cost_regime_counts",
            "liquidity_regime_presence",
            "event_activity_frequency",
            "object_dynamics_distribution",
        ],
        "defensive": True,
        "warning_only": True,
    }


if __name__ == "__main__":
    # Self-test
    import json
    import time

    print("=" * 60)
    print("v1.0 Interpretation Analytics Onchain Extension - Self Test")
    print("=" * 60)
    print()

    # Test 1: Aggregate empty observations
    print("Test 1: Aggregate empty observations")
    empty_aggregation = aggregate_onchain_observations([])
    print(json.dumps(empty_aggregation, indent=2))
    print()

    # Test 2: Aggregate single observation
    print("Test 2: Aggregate single observation")
    single_obs = [
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_market_cost_regime": "MEDIUM",
            "v10_norm_obs_summary": "normalized observation available.",
        }
    ]
    single_aggregation = aggregate_onchain_observations(single_obs)
    print(json.dumps(single_aggregation, indent=2))
    print()

    # Test 3: Aggregate multiple observations
    print("Test 3: Aggregate multiple observations")
    multiple_obs = [
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_market_cost_regime": "HIGH",
            "v10_norm_obs_liquidity_regime": "MEDIUM",
            "v10_norm_obs_event_activity_present": "TRUE",
        },
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_object_dynamics": "INCREASE",
            "v10_norm_obs_event_activity_present": "FALSE",
        },
        {
            "v10_norm_obs_mode": "ON",
            "v10_norm_obs_status": "AVAILABLE",
            "v10_norm_obs_network": "testnet",
            "v10_norm_obs_timestamp": int(time.time()),
            "v10_norm_obs_market_cost_regime": "HIGH",
            "v10_norm_obs_liquidity_regime": "HIGH",
        },
    ]
    multiple_aggregation = aggregate_onchain_observations(multiple_obs)
    print(json.dumps(multiple_aggregation, indent=2))
    print()

    # Test 4: Extend interpretation analytics
    print("Test 4: Extend interpretation analytics")
    base_analytics = {
        "analytics_mode": "ON",
        "analytics_status": "AVAILABLE",
        "analytics_summary": "base interpretation analytics.",
    }
    extended = extend_interpretation_analytics_v1(base_analytics, multiple_obs)
    print(json.dumps(extended, indent=2))
    print()

    # Test 5: Get analytics summary
    print("Test 5: Get analytics summary")
    summary = get_onchain_analytics_summary(multiple_aggregation)
    print(f"Summary: {summary}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
