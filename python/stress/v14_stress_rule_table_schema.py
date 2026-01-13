#!/usr/bin/env python3
"""
PR146: v1.4 Stress Rule Table v1 Schema (READ-ONLY)

Purpose:
    Define schema for stress rule table records.
    Stress = structural load state (not action, not instruction).

Record Prefix:
    v14_stress_

Required Fields:
    v14_stress_version: "v1"
    v14_stress_status: AVAILABLE | ERROR
    v14_stress_mode: READ_ONLY
    v14_stress_summary: Non-prescriptive summary
    v14_stress_inputs: Dict with regime_label, band_bucket, distortion_presence
    v14_stress_label: CALM | TENSE | STRESSED | UNKNOWN
    v14_stress_basis: List[str] (label-only)
    v14_stress_artifacts: List[str] (label-only references)
    v14_stress_warnings: List[str]

Optional:
    v14_stress_components_present: Dict[str, bool] (source presence flags)
    v14_stress_notes: List[str]

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - Non-prescriptive: No should/must/need to/recommend/advise
    - No trading verbs: No buy/sell/swap/execute/sign/transfer
    - No token literals: No SUI/USDC/BTC/ETH
    - No numeric values in text: Label-only output
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/hence
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Stress version
STRESS_VERSION_V1 = "v1"

# Stress status constants
STRESS_STATUS_AVAILABLE = "AVAILABLE"
STRESS_STATUS_ERROR = "ERROR"

# Stress mode constants
STRESS_MODE_READ_ONLY = "READ_ONLY"

# Stress label constants
STRESS_CALM = "CALM"
STRESS_TENSE = "TENSE"
STRESS_STRESSED = "STRESSED"
STRESS_UNKNOWN = "UNKNOWN"

# Band bucket constants (simplified from PR144)
BAND_SAFE = "SAFE"
BAND_EDGE = "EDGE"
BAND_OUTSIDE = "OUTSIDE"
BAND_UNKNOWN = "UNKNOWN"

# Distortion presence constants
DIST_NONE = "NONE"
DIST_PRESENT = "PRESENT"
DIST_UNKNOWN = "UNKNOWN"

# Regime label constants (from v1.2)
REGIME_LOW = "REGIME_LOW"
REGIME_MEDIUM = "REGIME_MEDIUM"
REGIME_HIGH = "REGIME_HIGH"
REGIME_CRITICAL = "REGIME_CRITICAL"
REGIME_UNKNOWN = "REGIME_UNKNOWN"


class V14StressRuleTableSchema:
    """Schema for stress rule table records."""

    # Valid statuses
    VALID_STATUSES = [
        STRESS_STATUS_AVAILABLE,
        STRESS_STATUS_ERROR,
    ]

    # Valid modes
    VALID_MODES = [
        STRESS_MODE_READ_ONLY,
    ]

    # Valid stress labels
    VALID_STRESS_LABELS = [
        STRESS_CALM,
        STRESS_TENSE,
        STRESS_STRESSED,
        STRESS_UNKNOWN,
    ]

    # Valid band buckets
    VALID_BAND_BUCKETS = [
        BAND_SAFE,
        BAND_EDGE,
        BAND_OUTSIDE,
        BAND_UNKNOWN,
    ]

    # Valid distortion presence values
    VALID_DISTORTION_PRESENCE = [
        DIST_NONE,
        DIST_PRESENT,
        DIST_UNKNOWN,
    ]

    # Valid regime labels
    VALID_REGIME_LABELS = [
        REGIME_LOW,
        REGIME_MEDIUM,
        REGIME_HIGH,
        REGIME_CRITICAL,
        REGIME_UNKNOWN,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "v14_stress_version",
        "v14_stress_status",
        "v14_stress_mode",
        "v14_stress_summary",
        "v14_stress_inputs",
        "v14_stress_label",
        "v14_stress_basis",
        "v14_stress_artifacts",
        "v14_stress_warnings",
    ]

    # Required input fields
    REQUIRED_INPUT_FIELDS = [
        "regime_label",
        "band_bucket",
        "distortion_presence",
    ]

    @staticmethod
    def create_stress_record(
        version: str = STRESS_VERSION_V1,
        status: str = STRESS_STATUS_AVAILABLE,
        mode: str = STRESS_MODE_READ_ONLY,
        summary: str = "",
        inputs: Optional[Dict[str, str]] = None,
        stress_label: str = STRESS_UNKNOWN,
        basis: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        components_present: Optional[Dict[str, bool]] = None,
        notes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create stress rule table record.

        Args:
            version: Stress version (default "v1")
            status: AVAILABLE | ERROR
            mode: READ_ONLY
            summary: Non-prescriptive summary
            inputs: Dict with regime_label, band_bucket, distortion_presence
            stress_label: CALM | TENSE | STRESSED | UNKNOWN
            basis: List of basis strings (label-only)
            artifacts: List of artifact strings
            warnings: List of warning strings
            components_present: Optional source presence flags
            notes: Optional notes

        Returns:
            Stress record
        """
        record = {
            "v14_stress_version": version,
            "v14_stress_status": status,
            "v14_stress_mode": mode,
            "v14_stress_summary": summary,
            "v14_stress_inputs": inputs if inputs else {},
            "v14_stress_label": stress_label,
            "v14_stress_basis": basis if basis else [],
            "v14_stress_artifacts": artifacts if artifacts else [],
            "v14_stress_warnings": warnings if warnings else [],
        }

        # Add optional fields if provided
        if components_present is not None:
            record["v14_stress_components_present"] = components_present

        if notes is not None:
            record["v14_stress_notes"] = notes

        return record

    @staticmethod
    def create_error_record(
        summary: str = "stress rule table lookup failed.",
    ) -> Dict[str, Any]:
        """
        Create error record.

        Args:
            summary: Error summary

        Returns:
            Error record
        """
        return V14StressRuleTableSchema.create_stress_record(
            status=STRESS_STATUS_ERROR,
            summary=summary,
            inputs={
                "regime_label": REGIME_UNKNOWN,
                "band_bucket": BAND_UNKNOWN,
                "distortion_presence": DIST_UNKNOWN,
            },
            stress_label=STRESS_UNKNOWN,
            basis=[],
            artifacts=[],
            warnings=[],
        )

    @staticmethod
    def validate_stress_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate stress record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V14StressRuleTableSchema.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate version
        version = record.get("v14_stress_version")
        if version != STRESS_VERSION_V1:
            errors.append(f"invalid version: {version} (expected {STRESS_VERSION_V1})")

        # Validate status
        status = record.get("v14_stress_status")
        if status not in V14StressRuleTableSchema.VALID_STATUSES:
            errors.append(f"invalid status: {status}")

        # Validate mode
        mode = record.get("v14_stress_mode")
        if mode not in V14StressRuleTableSchema.VALID_MODES:
            errors.append(f"invalid mode: {mode}")

        # Validate stress_label
        stress_label = record.get("v14_stress_label")
        if stress_label not in V14StressRuleTableSchema.VALID_STRESS_LABELS:
            errors.append(f"invalid stress_label: {stress_label}")

        # Validate types
        if not isinstance(record.get("v14_stress_summary"), str):
            errors.append("summary must be string")

        if not isinstance(record.get("v14_stress_inputs"), dict):
            errors.append("inputs must be dict")

        if not isinstance(record.get("v14_stress_basis"), list):
            errors.append("basis must be list")

        if not isinstance(record.get("v14_stress_artifacts"), list):
            errors.append("artifacts must be list")

        if not isinstance(record.get("v14_stress_warnings"), list):
            errors.append("warnings must be list")

        # Validate inputs dict
        inputs = record.get("v14_stress_inputs", {})
        if isinstance(inputs, dict):
            for field in V14StressRuleTableSchema.REQUIRED_INPUT_FIELDS:
                if field not in inputs:
                    errors.append(f"missing required input field: {field}")

            # Validate input values
            regime_label = inputs.get("regime_label")
            if regime_label and regime_label not in V14StressRuleTableSchema.VALID_REGIME_LABELS:
                errors.append(f"invalid regime_label: {regime_label}")

            band_bucket = inputs.get("band_bucket")
            if band_bucket and band_bucket not in V14StressRuleTableSchema.VALID_BAND_BUCKETS:
                errors.append(f"invalid band_bucket: {band_bucket}")

            distortion_presence = inputs.get("distortion_presence")
            if distortion_presence and distortion_presence not in V14StressRuleTableSchema.VALID_DISTORTION_PRESENCE:
                errors.append(f"invalid distortion_presence: {distortion_presence}")

        return errors


def get_stress_rule_table_schema_info() -> Dict[str, Any]:
    """
    Get stress rule table schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1",
        "schema_type": "stress_rule_table",
        "record_prefix": "v14_stress_",
        "valid_statuses": V14StressRuleTableSchema.VALID_STATUSES,
        "valid_modes": V14StressRuleTableSchema.VALID_MODES,
        "valid_stress_labels": V14StressRuleTableSchema.VALID_STRESS_LABELS,
        "valid_band_buckets": V14StressRuleTableSchema.VALID_BAND_BUCKETS,
        "valid_distortion_presence": V14StressRuleTableSchema.VALID_DISTORTION_PRESENCE,
        "valid_regime_labels": V14StressRuleTableSchema.VALID_REGIME_LABELS,
        "philosophy": "Stress = structural load state (not action, not instruction). Fixed table lookup.",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "no_numeric_values_in_text",
            "no_addresses",
            "no_causal_coupling",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Stress Rule Table Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create valid record
    print("Test 1: Create valid record")
    record1 = V14StressRuleTableSchema.create_stress_record(
        status=STRESS_STATUS_AVAILABLE,
        summary="stress label determined from fixed table.",
        inputs={
            "regime_label": REGIME_MEDIUM,
            "band_bucket": BAND_SAFE,
            "distortion_presence": DIST_NONE,
        },
        stress_label=STRESS_TENSE,
        basis=["BASIS_REGIME_MEDIUM", "BASIS_BAND_SAFE", "BASIS_NO_DISTORTION"],
    )
    errors1 = V14StressRuleTableSchema.validate_stress_record(record1)
    print(f"Valid record errors: {len(errors1)}")
    if errors1:
        for e in errors1:
            print(f"  - {e}")
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    record2 = V14StressRuleTableSchema.create_error_record(
        summary="stress rule table lookup failed: invalid inputs."
    )
    errors2 = V14StressRuleTableSchema.validate_stress_record(record2)
    print(f"Error record status: {record2['v14_stress_status']}")
    print(f"Error record errors: {len(errors2)}")
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    info = get_stress_rule_table_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
