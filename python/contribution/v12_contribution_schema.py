#!/usr/bin/env python3
"""
PR131: v1.2 Role × Distortion × Regime Contribution Model Schema v1 (READ-ONLY)

Purpose:
    Define contribution record schema for structural return contribution classification.
    Contribution = Where returns can exist as structural side-effect (not performance claim).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: No "should" language
    - No numeric patterns: No digits, %, decimals, ratios, time periods, probabilities
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No return guarantee language: No "assured", "risk-free", "annual return" claims
    - No backtest/prediction/optimization language
    - No coupling: No "++ therefore trade", "-- therefore stop"

Contribution Philosophy:
    Contribution ≠ Performance
    Contribution ≠ Return guarantee
    Contribution = Structural side-effect label

    Returns emerge where:
    1. Structure is intelligible (MEDIUM regime)
    2. Touchability is constrained (eligibility gates)
    3. Distortion is present (failure mode exists)

v12_contrib_ Prefix:
    All contribution fields use v12_contrib_ prefix.
"""

from typing import Any, Dict, List, Optional


# Contribution label constants (++/+/0/-/--)
CONTRIB_STRONGLY_POSITIVE = "CONTRIB_STRONGLY_POSITIVE"  # ++
CONTRIB_POSITIVE = "CONTRIB_POSITIVE"  # +
CONTRIB_NEUTRAL = "CONTRIB_NEUTRAL"  # 0
CONTRIB_NEGATIVE = "CONTRIB_NEGATIVE"  # -
CONTRIB_STRONGLY_NEGATIVE = "CONTRIB_STRONGLY_NEGATIVE"  # --
CONTRIB_UNKNOWN = "CONTRIB_UNKNOWN"

VALID_CONTRIBUTION_LABELS = [
    CONTRIB_STRONGLY_POSITIVE,
    CONTRIB_POSITIVE,
    CONTRIB_NEUTRAL,
    CONTRIB_NEGATIVE,
    CONTRIB_STRONGLY_NEGATIVE,
    CONTRIB_UNKNOWN,
]

# Contribution rationale labels (structural only, no numeric claims)
RATIONALE_DISTORTION_CAPTURE_ZONE = "DISTORTION_CAPTURE_ZONE"
RATIONALE_STRUCTURE_INTELLIGIBLE = "STRUCTURE_INTELLIGIBLE"
RATIONALE_FORCED_FLOW_PRESENT = "FORCED_FLOW_PRESENT"
RATIONALE_LIQUIDITY_PREMIUM_ZONE = "LIQUIDITY_PREMIUM_ZONE"
RATIONALE_STRUCTURE_BREAKDOWN_RISK = "STRUCTURE_BREAKDOWN_RISK"
RATIONALE_NON_ACTION_PRESERVES_OPTIONALITY = "NON_ACTION_PRESERVES_OPTIONALITY"
RATIONALE_ELEVATED_UNCERTAINTY = "ELEVATED_UNCERTAINTY"
RATIONALE_CAPITAL_PRESERVATION_PRIORITY = "CAPITAL_PRESERVATION_PRIORITY"
RATIONALE_LOW_DISTORTION_DENSITY = "LOW_DISTORTION_DENSITY"
RATIONALE_OPPORTUNITY_THIN = "OPPORTUNITY_THIN"
RATIONALE_STABILITY_BUFFER_ROLE = "STABILITY_BUFFER_ROLE"
RATIONALE_HEDGE_ALIGNMENT_ZONE = "HEDGE_ALIGNMENT_ZONE"
RATIONALE_OPERATIONAL_ENABLER_ONLY = "OPERATIONAL_ENABLER_ONLY"
RATIONALE_INELIGIBLE_TOUCHABILITY = "INELIGIBLE_TOUCHABILITY"

# Mode/Status
VALID_MODES = ["ON", "OFF"]
VALID_STATUSES = ["AVAILABLE", "ERROR"]


class V12ContributionSchema:
    """v1.2 Contribution Model Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "v12_contrib_mode",
        "v12_contrib_status",
        "v12_contrib_regime_level",
        "v12_contrib_role_type",
        "v12_contrib_distortion_type",
        "v12_contrib_contribution_label",
        "v12_contrib_contribution_rationale",
        "v12_contrib_summary",
        "v12_contrib_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v12_contrib_eligibility_label",
        "v12_contrib_warnings",
    ]

    # Valid enum values
    VALID_MODES = VALID_MODES
    VALID_STATUSES = VALID_STATUSES
    VALID_CONTRIBUTION_LABELS = VALID_CONTRIBUTION_LABELS

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty contribution record.

        Returns:
            Empty contribution record
        """
        return {
            "v12_contrib_mode": "ON",
            "v12_contrib_status": "AVAILABLE",
            "v12_contrib_regime_level": "UNCLASSIFIED",
            "v12_contrib_role_type": "UNCLASSIFIED",
            "v12_contrib_distortion_type": "UNCLASSIFIED",
            "v12_contrib_contribution_label": CONTRIB_UNKNOWN,
            "v12_contrib_contribution_rationale": [],
            "v12_contrib_summary": "empty contribution record with no classification.",
            "v12_contrib_basis": [],
        }

    @staticmethod
    def create_error_record(error_message: str = "contribution classification failed.") -> Dict[str, Any]:
        """
        Create an ERROR contribution record.

        Args:
            error_message: Error description

        Returns:
            ERROR contribution record
        """
        return {
            "v12_contrib_mode": "ON",
            "v12_contrib_status": "ERROR",
            "v12_contrib_regime_level": "UNCLASSIFIED",
            "v12_contrib_role_type": "UNCLASSIFIED",
            "v12_contrib_distortion_type": "UNCLASSIFIED",
            "v12_contrib_contribution_label": CONTRIB_UNKNOWN,
            "v12_contrib_contribution_rationale": [],
            "v12_contrib_summary": error_message,
            "v12_contrib_basis": [],
        }

    @staticmethod
    def create_contribution_record(
        regime_level: str,
        role_type: str,
        distortion_type: str,
        contribution_label: str,
        contribution_rationale: List[str],
        eligibility_label: Optional[str] = None,
        basis: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a contribution record.

        Args:
            regime_level: Regime level
            role_type: Role type
            distortion_type: Distortion type
            contribution_label: Contribution label (++/+/0/-/--)
            contribution_rationale: List of rationale labels
            eligibility_label: Optional eligibility label (passthrough)
            basis: Optional array of field names referenced
            warnings: Optional array of warnings

        Returns:
            Contribution record
        """
        # Generate summary
        summary = _generate_summary(regime_level, role_type, distortion_type, contribution_label)

        record = {
            "v12_contrib_mode": "ON",
            "v12_contrib_status": "AVAILABLE",
            "v12_contrib_regime_level": regime_level,
            "v12_contrib_role_type": role_type,
            "v12_contrib_distortion_type": distortion_type,
            "v12_contrib_contribution_label": contribution_label,
            "v12_contrib_contribution_rationale": contribution_rationale,
            "v12_contrib_summary": summary,
            "v12_contrib_basis": basis or [],
        }

        if eligibility_label:
            record["v12_contrib_eligibility_label"] = eligibility_label

        if warnings:
            record["v12_contrib_warnings"] = warnings

        return record


def _generate_summary(
    regime_level: str,
    role_type: str,
    distortion_type: str,
    contribution_label: str,
) -> str:
    """
    Generate non-prescriptive summary.

    Args:
        regime_level: Regime level
        role_type: Role type
        distortion_type: Distortion type
        contribution_label: Contribution label

    Returns:
        Summary text
    """
    return f"contribution labeled {contribution_label} for {regime_level} × {role_type} × {distortion_type}."


def get_contribution_schema_info() -> Dict[str, Any]:
    """
    Get contribution schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "role_distortion_regime_contribution",
        "valid_modes": V12ContributionSchema.VALID_MODES,
        "valid_statuses": V12ContributionSchema.VALID_STATUSES,
        "valid_contribution_labels": V12ContributionSchema.VALID_CONTRIBUTION_LABELS,
        "required_fields": V12ContributionSchema.REQUIRED_FIELDS,
        "optional_fields": V12ContributionSchema.OPTIONAL_FIELDS,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_return_guarantees",
            "no_backtest_language",
            "no_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Contribution Model Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V12ContributionSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Create contribution record
    print("Test 2: Create contribution record")
    contrib = V12ContributionSchema.create_contribution_record(
        regime_level="REGIME_MEDIUM",
        role_type="VOLATILITY_ROLE",
        distortion_type="D1_LIQUIDATION",
        contribution_label=CONTRIB_STRONGLY_POSITIVE,
        contribution_rationale=[
            RATIONALE_DISTORTION_CAPTURE_ZONE,
            RATIONALE_STRUCTURE_INTELLIGIBLE,
        ],
        eligibility_label="ELIGIBLE_CONSIDERATION_ONLY",
        basis=["regime_level", "role_type", "distortion_type", "eligibility_label"],
    )
    print(json.dumps(contrib, indent=2))
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V12ContributionSchema.create_error_record("test error")
    print(json.dumps(error, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
