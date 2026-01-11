"""
v0.6 Interpretation Layer

This package contains the constitutional schema and guards for v0.6 interpretation.

Interpretation maps observations to structural meaning types without evaluation,
judgment, or recommendation.

Modules:
    - v6_interpretation_schema: Schema definition for interpretation records
    - v6_constitutional_guard: Constitutional guards against violations
    - v6_interpretation_engine_v1: Static structural mapping (point)
    - v6_interpretation_engine_v2: Compositional structural mapping (surface)
"""

from .v6_interpretation_schema import (
    V6InterpretationSchema,
    ALLOWED_BASIS_FIELDS,
    FORBIDDEN_BASIS_FIELDS,
    get_schema_info,
)

from .v6_constitutional_guard import (
    validate_interpretation_record,
    check_forbidden_vocabulary,
    check_confidence_boundary,
    FORBIDDEN_VOCABULARY,
)

from .v6_interpretation_engine_v1 import (
    interpret_v1,
    interpret_batch_v1,
    V1MeaningTags,
    get_engine_info,
)

from .v6_interpretation_engine_v2 import (
    interpret_v2,
    interpret_batch_v2,
    V2PrimaryMeaning,
    V2Factors,
    V2Signals,
    get_engine_v2_info,
)

__all__ = [
    # Schema
    "V6InterpretationSchema",
    "ALLOWED_BASIS_FIELDS",
    "FORBIDDEN_BASIS_FIELDS",
    "get_schema_info",

    # Guards
    "validate_interpretation_record",
    "check_forbidden_vocabulary",
    "check_confidence_boundary",
    "FORBIDDEN_VOCABULARY",

    # Engine v1
    "interpret_v1",
    "interpret_batch_v1",
    "V1MeaningTags",
    "get_engine_info",

    # Engine v2
    "interpret_v2",
    "interpret_batch_v2",
    "V2PrimaryMeaning",
    "V2Factors",
    "V2Signals",
    "get_engine_v2_info",
]
