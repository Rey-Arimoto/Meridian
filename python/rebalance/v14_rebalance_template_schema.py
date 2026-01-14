#!/usr/bin/env python3
"""
PR151: v1.4 Rebalance Template Guidance Schema (READ-ONLY)

Purpose:
    Define schema for rebalance template guidance records.
    Maps Shock Phase + Stress + Action Shape + Trend → Template ID (abstract risk/safe ratio).

    IMPORTANT: Python does NOT hold token names (wBTC/USDC).
    IMPORTANT: Python does NOT output numeric ratios in text.
    Output is template_id only (e.g., TPL_RISK_90).
    Numeric tables exist only on TS side.

Record Prefix:
    v14_rebalance_

Template IDs:
    TPL_UNKNOWN - Unknown state (safe default)
    TPL_RISK_0 - Maximum safe (0% risk asset)
    TPL_RISK_20 - Low risk (20% risk asset)
    TPL_RISK_50 - Balanced (50% risk asset)
    TPL_RISK_90 - High risk (90% risk asset)

Rule IDs (for debugging):
    RULE_GUARD_FREEZE - Freeze state guard
    RULE_GUARD_STRESSED - Stressed state guard
    RULE_DOWN_SHOCK - Down shock phase
    RULE_DOWN_REVERSAL - Down reversal phase
    RULE_UP_SHOCK - Up shock phase
    RULE_UP_REVERSAL - Up reversal phase
    RULE_NORMAL_UP_TREND - Normal phase + up trend
    RULE_NORMAL_DOWN_TREND - Normal phase + down trend
    RULE_NORMAL_RANGE - Normal phase + range
    RULE_FALLBACK_UNKNOWN - Fallback to unknown

Required Fields:
    v14_rebalance_version: "v1"
    v14_rebalance_status: AVAILABLE | ERROR
    v14_rebalance_template_id: Template ID (TPL_*)
    v14_rebalance_scope: SCOPE_PORTFOLIO_REBALANCE
    v14_rebalance_rule_id: Rule ID (RULE_*)
    v14_rebalance_basis_labels: Dict of input labels (shock/stress/action_shape/trend)
    v14_rebalance_inputs_present: Dict of input presence flags
    v14_rebalance_warnings: List of warnings

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - No token names: No wBTC/USDC/SUI in text
    - No numeric ratios: No percentages in text
    - Non-prescriptive: No should/must/recommend/advise
    - Label-only output: Template ID is abstract label
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Version
REBALANCE_VERSION_V1 = "v1"

# Status constants
REBALANCE_STATUS_AVAILABLE = "AVAILABLE"
REBALANCE_STATUS_ERROR = "ERROR"

# Template IDs (abstract risk/safe ratios - TS side resolves to actual tokens)
TPL_UNKNOWN = "TPL_UNKNOWN"
TPL_RISK_0 = "TPL_RISK_0"
TPL_RISK_20 = "TPL_RISK_20"
TPL_RISK_50 = "TPL_RISK_50"
TPL_RISK_90 = "TPL_RISK_90"

# Strategy scope
SCOPE_PORTFOLIO_REBALANCE = "SCOPE_PORTFOLIO_REBALANCE"

# Rule IDs (for debugging/tracing)
RULE_GUARD_FREEZE = "RULE_GUARD_FREEZE"
RULE_GUARD_STRESSED = "RULE_GUARD_STRESSED"
RULE_DOWN_SHOCK = "RULE_DOWN_SHOCK"
RULE_DOWN_REVERSAL = "RULE_DOWN_REVERSAL"
RULE_UP_SHOCK = "RULE_UP_SHOCK"
RULE_UP_REVERSAL = "RULE_UP_REVERSAL"
RULE_NORMAL_UP_TREND = "RULE_NORMAL_UP_TREND"
RULE_NORMAL_DOWN_TREND = "RULE_NORMAL_DOWN_TREND"
RULE_NORMAL_RANGE = "RULE_NORMAL_RANGE"
RULE_FALLBACK_UNKNOWN = "RULE_FALLBACK_UNKNOWN"


class V14RebalanceTemplateSchema:
    """Schema for rebalance template guidance records."""

    # Valid statuses
    VALID_STATUSES = [
        REBALANCE_STATUS_AVAILABLE,
        REBALANCE_STATUS_ERROR,
    ]

    # Valid template IDs
    VALID_TEMPLATE_IDS = [
        TPL_UNKNOWN,
        TPL_RISK_0,
        TPL_RISK_20,
        TPL_RISK_50,
        TPL_RISK_90,
    ]

    # Valid scopes
    VALID_SCOPES = [
        SCOPE_PORTFOLIO_REBALANCE,
    ]

    # Valid rule IDs
    VALID_RULE_IDS = [
        RULE_GUARD_FREEZE,
        RULE_GUARD_STRESSED,
        RULE_DOWN_SHOCK,
        RULE_DOWN_REVERSAL,
        RULE_UP_SHOCK,
        RULE_UP_REVERSAL,
        RULE_NORMAL_UP_TREND,
        RULE_NORMAL_DOWN_TREND,
        RULE_NORMAL_RANGE,
        RULE_FALLBACK_UNKNOWN,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "v14_rebalance_version",
        "v14_rebalance_status",
        "v14_rebalance_template_id",
        "v14_rebalance_scope",
        "v14_rebalance_rule_id",
        "v14_rebalance_basis_labels",
        "v14_rebalance_inputs_present",
        "v14_rebalance_warnings",
    ]

    @staticmethod
    def build_rebalance_record(
        version: str = REBALANCE_VERSION_V1,
        status: str = REBALANCE_STATUS_AVAILABLE,
        template_id: str = TPL_UNKNOWN,
        scope: str = SCOPE_PORTFOLIO_REBALANCE,
        rule_id: str = RULE_FALLBACK_UNKNOWN,
        basis_labels: Optional[Dict[str, str]] = None,
        inputs_present: Optional[Dict[str, bool]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Build rebalance template guidance record.

        Args:
            version: Rebalance version (default "v1")
            status: AVAILABLE | ERROR
            template_id: Template ID (TPL_*)
            scope: Strategy scope
            rule_id: Rule ID (RULE_*)
            basis_labels: Dict of input labels (shock/stress/action_shape/trend)
            inputs_present: Dict of input presence flags
            warnings: List of warnings

        Returns:
            Rebalance record
        """
        record = {
            "v14_rebalance_version": version,
            "v14_rebalance_status": status,
            "v14_rebalance_template_id": template_id,
            "v14_rebalance_scope": scope,
            "v14_rebalance_rule_id": rule_id,
            "v14_rebalance_basis_labels": basis_labels if basis_labels else {},
            "v14_rebalance_inputs_present": inputs_present if inputs_present else {},
            "v14_rebalance_warnings": warnings if warnings else [],
        }

        return record

    @staticmethod
    def build_rebalance_record_ok(
        template_id: str,
        rule_id: str,
        basis_labels: Optional[Dict[str, str]] = None,
        inputs_present: Optional[Dict[str, bool]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Build AVAILABLE rebalance record.

        Args:
            template_id: Template ID (TPL_*)
            rule_id: Rule ID (RULE_*)
            basis_labels: Dict of input labels
            inputs_present: Dict of input presence flags
            warnings: List of warnings

        Returns:
            AVAILABLE rebalance record
        """
        return V14RebalanceTemplateSchema.build_rebalance_record(
            status=REBALANCE_STATUS_AVAILABLE,
            template_id=template_id,
            rule_id=rule_id,
            basis_labels=basis_labels,
            inputs_present=inputs_present,
            warnings=warnings,
        )

    @staticmethod
    def build_rebalance_record_error(
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Build ERROR rebalance record.

        Args:
            warnings: List of warnings

        Returns:
            ERROR rebalance record
        """
        return V14RebalanceTemplateSchema.build_rebalance_record(
            status=REBALANCE_STATUS_ERROR,
            template_id=TPL_UNKNOWN,
            rule_id=RULE_FALLBACK_UNKNOWN,
            basis_labels={},
            inputs_present={},
            warnings=warnings if warnings else [],
        )

    @staticmethod
    def validate_rebalance_record(record: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate rebalance record.

        Args:
            record: Record to validate

        Returns:
            Tuple of (is_valid: bool, warnings: List[str])
        """
        warnings = []

        # Check required fields
        for field in V14RebalanceTemplateSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"missing required field: {field}")

        if warnings:
            return (False, warnings)

        # Validate version
        version = record.get("v14_rebalance_version")
        if version != REBALANCE_VERSION_V1:
            warnings.append(f"invalid version: {version} (expected {REBALANCE_VERSION_V1})")

        # Validate status
        status = record.get("v14_rebalance_status")
        if status not in V14RebalanceTemplateSchema.VALID_STATUSES:
            warnings.append(f"invalid status: {status}")

        # Validate template_id
        template_id = record.get("v14_rebalance_template_id")
        if template_id not in V14RebalanceTemplateSchema.VALID_TEMPLATE_IDS:
            warnings.append(f"invalid template_id: {template_id}")

        # Validate scope
        scope = record.get("v14_rebalance_scope")
        if scope not in V14RebalanceTemplateSchema.VALID_SCOPES:
            warnings.append(f"invalid scope: {scope}")

        # Validate rule_id
        rule_id = record.get("v14_rebalance_rule_id")
        if rule_id not in V14RebalanceTemplateSchema.VALID_RULE_IDS:
            warnings.append(f"invalid rule_id: {rule_id}")

        # Validate types
        if not isinstance(record.get("v14_rebalance_basis_labels"), dict):
            warnings.append("basis_labels must be dict")

        if not isinstance(record.get("v14_rebalance_inputs_present"), dict):
            warnings.append("inputs_present must be dict")

        if not isinstance(record.get("v14_rebalance_warnings"), list):
            warnings.append("warnings must be list")

        return (len(warnings) == 0, warnings)


def get_rebalance_template_schema_info() -> Dict[str, Any]:
    """
    Get rebalance template schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1",
        "schema_type": "rebalance_template_guidance",
        "record_prefix": "v14_rebalance_",
        "valid_statuses": V14RebalanceTemplateSchema.VALID_STATUSES,
        "valid_template_ids": V14RebalanceTemplateSchema.VALID_TEMPLATE_IDS,
        "valid_scopes": V14RebalanceTemplateSchema.VALID_SCOPES,
        "valid_rule_ids": V14RebalanceTemplateSchema.VALID_RULE_IDS,
        "philosophy": "Template ID only. No token names, no numeric ratios. TS side resolves templates.",
        "constitutional_guarantees": [
            "READ-ONLY",
            "no_token_names",
            "no_numeric_ratios_in_text",
            "non_prescriptive",
            "label_output_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Rebalance Template Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Build valid AVAILABLE record
    print("Test 1: Build valid AVAILABLE record")
    record1 = V14RebalanceTemplateSchema.build_rebalance_record_ok(
        template_id=TPL_RISK_90,
        rule_id=RULE_UP_SHOCK,
        basis_labels={
            "shock_phase": "PHASE_UP_SHOCK",
            "stress": "STRESS_CALM",
            "action_shape": "NORMAL_STATE",
            "trend": "UNKNOWN",
        },
        inputs_present={
            "shock_phase": True,
            "stress": True,
            "action_shape": True,
            "trend": False,
        },
    )
    is_valid1, warnings1 = V14RebalanceTemplateSchema.validate_rebalance_record(record1)
    print(f"Valid: {is_valid1}, Warnings: {len(warnings1)}")
    if warnings1:
        for w in warnings1:
            print(f"  - {w}")
    print()

    # Test 2: Build ERROR record
    print("Test 2: Build ERROR record")
    record2 = V14RebalanceTemplateSchema.build_rebalance_record_error(
        warnings=["invalid inputs"],
    )
    is_valid2, warnings2 = V14RebalanceTemplateSchema.validate_rebalance_record(record2)
    print(f"Status: {record2['v14_rebalance_status']}")
    print(f"Valid: {is_valid2}, Warnings: {len(warnings2)}")
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    info = get_rebalance_template_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
