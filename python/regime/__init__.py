"""
v1.1 Entropy Regime Classification Layer

This package contains schemas, classifier, and constitutional guards
for entropy regime classification.

Regime = State Classification (not action).

Regime Definition:
    Regime classifies market state into discrete levels.

    Regime levels:
    - REGIME_LOW: Stable, predictable patterns
    - REGIME_MEDIUM: Moderate variation, typical conditions
    - REGIME_HIGH: Elevated variation, increased uncertainty
    - REGIME_CRITICAL: Extreme variation, observability breakdown

    Regime does NOT:
    - Recommend actions
    - Evaluate good/bad
    - Suggest positions
    - Optimize outcomes

Modules:
    - v11_entropy_regime_schema: Schema for regime classification records
    - v11_entropy_regime_classifier_v1: Regime classifier v1
    - v11_regime_constitutional_guard: Constitutional guards for regime
"""

from .v11_entropy_regime_schema import (
    V11EntropyRegimeSchema,
    get_entropy_regime_schema_info,
)

from .v11_entropy_regime_classifier_v1 import (
    classify_entropy_regime_v1,
    get_regime_classifier_v1_info,
)

from .v11_regime_constitutional_guard import (
    check_action_vocabulary,
    validate_regime_record,
)

__all__ = [
    # Regime Schema
    "V11EntropyRegimeSchema",
    "get_entropy_regime_schema_info",
    # Regime Classifier
    "classify_entropy_regime_v1",
    "get_regime_classifier_v1_info",
    # Constitutional Guards
    "check_action_vocabulary",
    "validate_regime_record",
]
