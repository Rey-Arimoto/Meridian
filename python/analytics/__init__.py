"""
v1.0 Interpretation Analytics Extension Layer

This package contains extensions to v0.6 Interpretation Analytics
for onchain observation awareness.

Analytics = Meaning Generation (not execution).

Analytics Definition:
    Analytics extends interpretation to include onchain observations.

    Analytics aggregates:
    - market_cost_regime_counts (LOW/MEDIUM/HIGH counts)
    - liquidity_regime_presence (presence flags)
    - event_activity_frequency (activity frequency)
    - object_dynamics_distribution (DECREASE/STABLE/INCREASE counts)

    Analytics does NOT:
    - Make trading decisions
    - Provide recommendations
    - Evaluate good/bad
    - Execute operations

Modules:
    - pr109_interpretation_analytics_onchain_extension: Onchain analytics extension
    - pr109_analytics_constitutional_guard: Constitutional guards for analytics
"""

from .pr109_interpretation_analytics_onchain_extension import (
    aggregate_onchain_observations,
    extend_interpretation_analytics_v1,
    get_onchain_analytics_summary,
    get_interpretation_analytics_onchain_extension_info,
)

from .pr109_analytics_constitutional_guard import (
    check_analytics_numeric_values,
    validate_interpretation_analytics_record,
    validate_onchain_analytics_summary,
)

__all__ = [
    # Onchain Extension
    "aggregate_onchain_observations",
    "extend_interpretation_analytics_v1",
    "get_onchain_analytics_summary",
    "get_interpretation_analytics_onchain_extension_info",
    # Constitutional Guards
    "check_analytics_numeric_values",
    "validate_interpretation_analytics_record",
    "validate_onchain_analytics_summary",
]
