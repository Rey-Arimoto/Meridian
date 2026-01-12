#!/usr/bin/env python3
"""
PR132: v1.2 Contribution → Constraint Binding Schema v1 (READ-ONLY)

Purpose:
    Define constraint binding schema for contribution model integration.
    Binding = Label propagation (not evaluation, not decision, not instruction).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: No "should" language
    - No numeric patterns: No digits, %, decimals
    - No token literals: No SUI, USDC, BTC, ETH, DEEP, CETUS
    - No trading vocabulary: No swap, buy, sell, execute
    - No coupling: No "primary therefore trade", "blocked so stop"

Binding Philosophy:
    Binding ≠ Decision
    Binding ≠ Instruction
    Binding = Label propagation

    PRIMARY zone = Contribution center observed structurally
    SECONDARY zone = Non-MEDIUM regime observed
    BLOCKED zone = Critical/ineligible/suppressed observed
    NONE zone = Default (no contribution zone detected)

v12_contrib_constraint_ Prefix:
    All constraint binding fields use v12_contrib_constraint_ prefix.
"""

from typing import Any, Dict, List, Optional


# Zone label constants
CONTRIB_ZONE_NONE = "CONTRIB_ZONE_NONE"
CONTRIB_ZONE_SECONDARY = "CONTRIB_ZONE_SECONDARY"
CONTRIB_ZONE_PRIMARY = "CONTRIB_ZONE_PRIMARY"
CONTRIB_ZONE_BLOCKED = "CONTRIB_ZONE_BLOCKED"

VALID_ZONE_LABELS = [
    CONTRIB_ZONE_NONE,
    CONTRIB_ZONE_SECONDARY,
    CONTRIB_ZONE_PRIMARY,
    CONTRIB_ZONE_BLOCKED,
]

# Constraint label constants (append to plan/preview/explain)
CONSTRAINT_CONTRIB_BLOCKED_REGIME_CRITICAL = "contrib_blocked_regime_critical"
CONSTRAINT_CONTRIB_BLOCKED_INELIGIBLE = "contrib_blocked_ineligible"
CONSTRAINT_CONTRIB_BLOCKED_SUPPRESSED = "contrib_blocked_suppressed"
CONSTRAINT_CONTRIB_SECONDARY_REGIME_NON_MEDIUM = "contrib_secondary_regime_non_medium"
CONSTRAINT_CONTRIB_PRIMARY_MEDIUM_VOLATILITY_DISTORTION = "contrib_primary_medium_volatility_distortion"
CONSTRAINT_CONTRIB_NONE_DEFAULT = "contrib_none_default"

# Mode/Status
VALID_MODES = ["ON", "OFF"]
VALID_STATUSES = ["AVAILABLE", "ERROR"]


class V12ContributionConstraintSchema:
    """v1.2 Contribution Constraint Binding Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "v12_contrib_constraint_mode",
        "v12_contrib_constraint_status",
        "v12_contrib_constraint_zone_label",
        "v12_contrib_constraint_labels",
        "v12_contrib_constraint_summary",
        "v12_contrib_constraint_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v12_contrib_constraint_warnings",
        "v12_contrib_constraint_contribution_label",
        "v12_contrib_constraint_regime_level",
        "v12_contrib_constraint_role_type",
        "v12_contrib_constraint_distortion_type",
    ]

    # Valid enum values
    VALID_MODES = VALID_MODES
    VALID_STATUSES = VALID_STATUSES
    VALID_ZONE_LABELS = VALID_ZONE_LABELS

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty constraint binding record.

        Returns:
            Empty constraint binding record
        """
        return {
            "v12_contrib_constraint_mode": "ON",
            "v12_contrib_constraint_status": "AVAILABLE",
            "v12_contrib_constraint_zone_label": CONTRIB_ZONE_NONE,
            "v12_contrib_constraint_labels": [],
            "v12_contrib_constraint_summary": "empty constraint binding record with no zone classification.",
            "v12_contrib_constraint_basis": [],
        }

    @staticmethod
    def create_error_record(error_message: str = "constraint binding failed.") -> Dict[str, Any]:
        """
        Create an ERROR constraint binding record.

        Args:
            error_message: Error description

        Returns:
            ERROR constraint binding record
        """
        return {
            "v12_contrib_constraint_mode": "ON",
            "v12_contrib_constraint_status": "ERROR",
            "v12_contrib_constraint_zone_label": CONTRIB_ZONE_NONE,
            "v12_contrib_constraint_labels": [],
            "v12_contrib_constraint_summary": error_message,
            "v12_contrib_constraint_basis": [],
        }

    @staticmethod
    def create_constraint_binding_record(
        zone_label: str,
        constraint_labels: List[str],
        basis: Optional[List[str]] = None,
        contribution_label: Optional[str] = None,
        regime_level: Optional[str] = None,
        role_type: Optional[str] = None,
        distortion_type: Optional[str] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a constraint binding record.

        Args:
            zone_label: Zone label (PRIMARY/SECONDARY/BLOCKED/NONE)
            constraint_labels: List of constraint labels
            basis: Optional array of field names referenced
            contribution_label: Optional contribution label from PR131
            regime_level: Optional regime level
            role_type: Optional role type
            distortion_type: Optional distortion type
            warnings: Optional array of warnings

        Returns:
            Constraint binding record
        """
        # Generate summary
        summary = _generate_summary(zone_label, constraint_labels)

        record = {
            "v12_contrib_constraint_mode": "ON",
            "v12_contrib_constraint_status": "AVAILABLE",
            "v12_contrib_constraint_zone_label": zone_label,
            "v12_contrib_constraint_labels": constraint_labels,
            "v12_contrib_constraint_summary": summary,
            "v12_contrib_constraint_basis": basis or [],
        }

        if contribution_label:
            record["v12_contrib_constraint_contribution_label"] = contribution_label

        if regime_level:
            record["v12_contrib_constraint_regime_level"] = regime_level

        if role_type:
            record["v12_contrib_constraint_role_type"] = role_type

        if distortion_type:
            record["v12_contrib_constraint_distortion_type"] = distortion_type

        if warnings:
            record["v12_contrib_constraint_warnings"] = warnings

        return record


def _generate_summary(
    zone_label: str,
    constraint_labels: List[str],
) -> str:
    """
    Generate non-prescriptive summary.

    Args:
        zone_label: Zone label
        constraint_labels: Constraint labels

    Returns:
        Summary text
    """
    labels_str = ", ".join(constraint_labels) if constraint_labels else "no constraints"
    return f"contribution zone labeled {zone_label} with constraints: {labels_str}."


def get_contribution_constraint_schema_info() -> Dict[str, Any]:
    """
    Get contribution constraint schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.2",
        "schema_type": "contribution_constraint_binding",
        "valid_modes": V12ContributionConstraintSchema.VALID_MODES,
        "valid_statuses": V12ContributionConstraintSchema.VALID_STATUSES,
        "valid_zone_labels": V12ContributionConstraintSchema.VALID_ZONE_LABELS,
        "required_fields": V12ContributionConstraintSchema.REQUIRED_FIELDS,
        "optional_fields": V12ContributionConstraintSchema.OPTIONAL_FIELDS,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-prescriptive",
            "no_numeric_patterns",
            "no_token_literals",
            "no_trading_vocabulary",
            "no_coupling",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.2 Contribution Constraint Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V12ContributionConstraintSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Create PRIMARY zone record
    print("Test 2: Create PRIMARY zone record")
    primary = V12ContributionConstraintSchema.create_constraint_binding_record(
        zone_label=CONTRIB_ZONE_PRIMARY,
        constraint_labels=[CONSTRAINT_CONTRIB_PRIMARY_MEDIUM_VOLATILITY_DISTORTION],
        basis=["regime_level", "role_type", "distortion_type"],
        contribution_label="CONTRIB_STRONGLY_POSITIVE",
        regime_level="REGIME_MEDIUM",
        role_type="VOLATILITY_ROLE",
        distortion_type="D1_LIQUIDATION",
    )
    print(json.dumps(primary, indent=2))
    print()

    # Test 3: Create BLOCKED zone record
    print("Test 3: Create BLOCKED zone record")
    blocked = V12ContributionConstraintSchema.create_constraint_binding_record(
        zone_label=CONTRIB_ZONE_BLOCKED,
        constraint_labels=[CONSTRAINT_CONTRIB_BLOCKED_REGIME_CRITICAL],
        basis=["regime_level"],
        regime_level="REGIME_CRITICAL",
    )
    print(json.dumps(blocked, indent=2))
    print()

    # Test 4: Create error record
    print("Test 4: Create error record")
    error = V12ContributionConstraintSchema.create_error_record("test error")
    print(json.dumps(error, indent=2))
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
