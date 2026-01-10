#!/usr/bin/env python3
"""
PR60: v0.6 Interpretation Schema Definition (READ-ONLY)

Purpose:
    Define the constitutional schema for v0.6 Interpretation layer.
    Interpretation maps observations to structural meaning types
    without evaluation, judgment, or recommendation.

Constitutional Constraints:
    - READ-ONLY: No execution logic or decision changes
    - Non-evaluative: No good/bad, correct/wrong vocabulary
    - Non-scoric: No scores, grades, rankings
    - Non-prescriptive: No "should" or recommendations
    - Observation-bound: Only uses observation fields as basis
    - v0.4 boundary protection: No confidence_reason analysis

Interpretation vs Evaluation:
    Interpretation = Structural Mapping (what structure this represents)
    Interpretation ≠ Evaluation (good/bad judgment)
    Interpretation ≠ Recommendation (what should be done)

v0.6 Philosophy:
    v0.5 completed observation (what happened).
    v0.6 maps observation to meaning type (what structure this represents).
    That is not judgment, but structural language.
"""

from typing import Any, Dict, List, Literal, Optional


# v0.6 Schema Version
V6_SCHEMA_VERSION = "v0.6"

# v0.6 Field Prefix
V6_PREFIX = "v6_"


# ============================================================================
# v0.6 Interpretation Schema
# ============================================================================

class V6InterpretationSchema:
    """
    v0.6 Interpretation Schema Definition.

    This schema defines the structure for interpretation records,
    which map observations to structural meaning types.
    """

    # Required fields for interpretation records
    REQUIRED_FIELDS = [
        "v6_meaning_mode",
        "v6_meaning_status",
        "v6_meaning_tag",
        "v6_meaning_summary",
        "v6_meaning_basis",
    ]

    # Field types
    FIELD_TYPES = {
        "v6_meaning_mode": str,      # "ON" | "OFF"
        "v6_meaning_status": str,    # "AVAILABLE" | "UNAVAILABLE"
        "v6_meaning_tag": str,       # Structural meaning type
        "v6_meaning_summary": str,   # Non-evaluative explanation
        "v6_meaning_basis": list,    # List of observation field names
    }

    # Valid values for enum fields
    VALID_VALUES = {
        "v6_meaning_mode": ["ON", "OFF"],
        "v6_meaning_status": ["AVAILABLE", "UNAVAILABLE"],
    }

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty interpretation record with safe defaults.

        Returns dict with all required fields set to safe values.
        """
        return {
            "v6_meaning_mode": "OFF",
            "v6_meaning_status": "UNAVAILABLE",
            "v6_meaning_tag": "UNKNOWN",
            "v6_meaning_summary": "interpretation unavailable.",
            "v6_meaning_basis": [],
        }

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate interpretation record structure.

        Returns list of validation warnings (empty if valid).
        Warning-only: never raises exceptions.
        """
        warnings = []

        # Check required fields present
        for field in V6InterpretationSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"PR60 schema violation: missing required field '{field}'")

        # Check field types
        for field, expected_type in V6InterpretationSchema.FIELD_TYPES.items():
            if field in record:
                if not isinstance(record[field], expected_type):
                    warnings.append(
                        f"PR60 schema violation: field '{field}' type mismatch "
                        f"(expected {expected_type.__name__}, got {type(record[field]).__name__})"
                    )

        # Check enum values
        for field, valid_values in V6InterpretationSchema.VALID_VALUES.items():
            if field in record:
                if record[field] not in valid_values:
                    warnings.append(
                        f"PR60 schema violation: field '{field}' has invalid value "
                        f"'{record[field]}' (expected one of: {valid_values})"
                    )

        # Check v6_meaning_basis is list of strings
        if "v6_meaning_basis" in record:
            basis = record["v6_meaning_basis"]
            if isinstance(basis, list):
                for item in basis:
                    if not isinstance(item, str):
                        warnings.append(
                            f"PR60 schema violation: v6_meaning_basis contains non-string item: {item}"
                        )
            # else: type error already reported above

        return warnings


# ============================================================================
# Allowed Observation Fields (Basis)
# ============================================================================

# Fields that can be used as basis for interpretation
# These are observation-layer fields from v0.5
ALLOWED_BASIS_FIELDS = [
    # Shadow diff fields (PR44-46)
    "v5_decision_diff_status",
    "v5_decision_diff_pair",
    "v5_decision_diff_summary",
    "v5_decision_diff_semantics_tag",
    "v5_decision_diff_semantics_context",
    "v5_shadow_decision_action",

    # Constitutional fields (PR4/PR13)
    "regime",
    "base_action",

    # Intent fields (PR3)
    "intent_primary",

    # Timestamp/metadata
    "timestamp_utc",
]

# Fields that are FORBIDDEN as basis (v0.4 boundary)
FORBIDDEN_BASIS_FIELDS = [
    "confidence_reason",
    "confidence_reason_version",
    "confidence_reason_generated_at",
]


def validate_basis_fields(basis: List[str]) -> List[str]:
    """
    Validate that basis fields are allowed observation fields.

    Returns list of warnings (empty if valid).
    Warning-only: never raises exceptions.
    """
    warnings = []

    for field in basis:
        # Check for v0.4 boundary violations
        if field in FORBIDDEN_BASIS_FIELDS:
            warnings.append(
                f"PR60 boundary violation: interpretation basis uses forbidden field '{field}' "
                f"(v0.4 confidence boundary must not be crossed)"
            )

        # Check if field is in allowed list (informational only)
        if field not in ALLOWED_BASIS_FIELDS and field not in FORBIDDEN_BASIS_FIELDS:
            warnings.append(
                f"PR60 basis warning: field '{field}' not in standard observation allowlist "
                f"(may be valid but should be reviewed)"
            )

    return warnings


# ============================================================================
# Meaning Tag Guidelines
# ============================================================================

# Example meaning tags (illustrative, not exhaustive)
# These are structural types, not evaluative categories
EXAMPLE_MEANING_TAGS = [
    "UNKNOWN",                                      # Default/fallback
    "UNCLASSIFIED",                                 # Insufficient information
    "STABILITY_OVERLAY_UNDER_TRANSITION",           # Structural pattern
    "INTENT_MISMATCH_OBSERVED",                     # Structural divergence
    "STRUCTURAL_DIVERGENCE_WITHOUT_REGIME_SHIFT",   # Pattern observation
    "OBSERVATION_INSUFFICIENT",                     # Data availability
]

# Notes on meaning tags:
# - Tags are not evaluative (no good/bad implication)
# - Tags have no correctness (no right/wrong)
# - UNKNOWN/UNCLASSIFIED are always valid
# - Tags describe structure, not value


# ============================================================================
# Schema Export
# ============================================================================

def get_schema_info() -> Dict[str, Any]:
    """
    Get schema information for documentation/validation.

    Returns dict with schema metadata.
    """
    return {
        "version": V6_SCHEMA_VERSION,
        "prefix": V6_PREFIX,
        "required_fields": V6InterpretationSchema.REQUIRED_FIELDS,
        "field_types": {
            k: v.__name__ for k, v in V6InterpretationSchema.FIELD_TYPES.items()
        },
        "allowed_basis_fields": ALLOWED_BASIS_FIELDS,
        "forbidden_basis_fields": FORBIDDEN_BASIS_FIELDS,
        "example_meaning_tags": EXAMPLE_MEANING_TAGS,
    }


if __name__ == "__main__":
    # Print schema info for documentation
    import json

    print("=" * 60)
    print("v0.6 Interpretation Schema")
    print("=" * 60)
    print()
    print(json.dumps(get_schema_info(), indent=2))
    print()
    print("=" * 60)
    print("Constitutional Constraints:")
    print("  - READ-ONLY (no execution changes)")
    print("  - Non-evaluative (no good/bad)")
    print("  - Non-scoric (no scores/ranks)")
    print("  - Observation-bound (only uses observation fields)")
    print("  - v0.4 boundary protection (no confidence_reason)")
    print("=" * 60)
