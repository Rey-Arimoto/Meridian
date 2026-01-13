#!/usr/bin/env python3
"""
PR144: v1.4 Role Safe Band Guidance v1 (READ-ONLY)

Purpose:
    Define schema for role safe band guidance records.
    This is NOT advice, NOT instruction, NOT recommendation.
    It describes whether role allocations are BELOW/WITHIN/ABOVE safe bands.

Record Prefix:
    v14_guidance_

Required Fields:
    v14_guidance_version: "v1.4"
    v14_guidance_status: AVAILABLE | ERROR
    v14_guidance_mode: READ_ONLY
    v14_guidance_summary: Non-prescriptive summary
    v14_guidance_regime_label: Regime label
    v14_guidance_roles: Dict keyed by role enum
    v14_guidance_basis: List of strings (label-only)
    v14_guidance_artifacts: List of strings
    v14_guidance_warnings: List of strings

Role Entry Schema:
    current_ratio_bucket: String bucket (RATIO_*)
    safe_band_bucket: String bucket (BAND_*)
    status: BELOW_SAFE | WITHIN_SAFE | ABOVE_SAFE | UNKNOWN
    interpretation: Non-prescriptive text

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - Non-prescriptive: No should/must/need to/recommend/advise
    - No trading verbs: No buy/sell/swap/execute/sign/transfer
    - No token literals: No SUI/USDC/BTC/ETH
    - No numeric values in text: Output buckets only, not raw numbers
    - No addresses: No 0x... patterns
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Guidance version
GUIDANCE_VERSION_V1_4 = "v1.4"

# Guidance status constants
GUIDANCE_STATUS_AVAILABLE = "AVAILABLE"
GUIDANCE_STATUS_ERROR = "ERROR"

# Guidance mode constants
GUIDANCE_MODE_READ_ONLY = "READ_ONLY"

# Safe band bucket constants
BAND_ZERO = "BAND_ZERO"
BAND_MINIMAL = "BAND_MINIMAL"
BAND_LOW = "BAND_LOW"
BAND_MEDIUM = "BAND_MEDIUM"
BAND_HIGH = "BAND_HIGH"
BAND_MAXIMAL = "BAND_MAXIMAL"
BAND_UNKNOWN = "BAND_UNKNOWN"

# Current ratio bucket constants
RATIO_ZERO = "RATIO_ZERO"
RATIO_MINIMAL = "RATIO_MINIMAL"
RATIO_LOW = "RATIO_LOW"
RATIO_MEDIUM = "RATIO_MEDIUM"
RATIO_HIGH = "RATIO_HIGH"
RATIO_MAXIMAL = "RATIO_MAXIMAL"
RATIO_UNKNOWN = "RATIO_UNKNOWN"

# Role status constants
STATUS_BELOW_SAFE = "BELOW_SAFE"
STATUS_WITHIN_SAFE = "WITHIN_SAFE"
STATUS_ABOVE_SAFE = "ABOVE_SAFE"
STATUS_UNKNOWN = "UNKNOWN"

# Role constants (reuse from v1.2)
ROLE_VOLATILITY = "VOLATILITY_ROLE"
ROLE_LIQUIDITY = "LIQUIDITY_ROLE"
ROLE_STABILITY = "STABILITY_ROLE"
ROLE_HEDGE = "HEDGE_ROLE"
ROLE_GAS = "GAS_ROLE"

# Regime label constants (reuse from v1.2)
REGIME_LOW = "REGIME_LOW"
REGIME_MEDIUM = "REGIME_MEDIUM"
REGIME_HIGH = "REGIME_HIGH"
REGIME_CRITICAL = "REGIME_CRITICAL"
REGIME_UNKNOWN = "REGIME_UNKNOWN"


class V14RoleSafeBandSchema:
    """Schema for role safe band guidance records."""

    # Valid statuses
    VALID_STATUSES = [
        GUIDANCE_STATUS_AVAILABLE,
        GUIDANCE_STATUS_ERROR,
    ]

    # Valid modes
    VALID_MODES = [
        GUIDANCE_MODE_READ_ONLY,
    ]

    # Valid band buckets
    VALID_BAND_BUCKETS = [
        BAND_ZERO,
        BAND_MINIMAL,
        BAND_LOW,
        BAND_MEDIUM,
        BAND_HIGH,
        BAND_MAXIMAL,
        BAND_UNKNOWN,
    ]

    # Valid ratio buckets
    VALID_RATIO_BUCKETS = [
        RATIO_ZERO,
        RATIO_MINIMAL,
        RATIO_LOW,
        RATIO_MEDIUM,
        RATIO_HIGH,
        RATIO_MAXIMAL,
        RATIO_UNKNOWN,
    ]

    # Valid role statuses
    VALID_ROLE_STATUSES = [
        STATUS_BELOW_SAFE,
        STATUS_WITHIN_SAFE,
        STATUS_ABOVE_SAFE,
        STATUS_UNKNOWN,
    ]

    # Valid roles
    VALID_ROLES = [
        ROLE_VOLATILITY,
        ROLE_LIQUIDITY,
        ROLE_STABILITY,
        ROLE_HEDGE,
        ROLE_GAS,
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
        "v14_guidance_version",
        "v14_guidance_status",
        "v14_guidance_mode",
        "v14_guidance_summary",
        "v14_guidance_regime_label",
        "v14_guidance_roles",
        "v14_guidance_basis",
        "v14_guidance_artifacts",
        "v14_guidance_warnings",
    ]

    # Required role entry fields
    REQUIRED_ROLE_FIELDS = [
        "current_ratio_bucket",
        "safe_band_bucket",
        "status",
        "interpretation",
    ]

    @staticmethod
    def create_guidance_record(
        version: str = GUIDANCE_VERSION_V1_4,
        status: str = GUIDANCE_STATUS_AVAILABLE,
        mode: str = GUIDANCE_MODE_READ_ONLY,
        summary: str = "",
        regime_label: str = REGIME_UNKNOWN,
        roles: Optional[Dict[str, Dict[str, Any]]] = None,
        basis: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create role safe band guidance record.

        Args:
            version: Guidance version (default "v1.4")
            status: AVAILABLE | ERROR
            mode: READ_ONLY
            summary: Non-prescriptive summary
            regime_label: Regime label
            roles: Dict keyed by role enum
            basis: List of strings (label-only)
            artifacts: List of strings
            warnings: List of strings

        Returns:
            Role safe band guidance record
        """
        record = {
            "v14_guidance_version": version,
            "v14_guidance_status": status,
            "v14_guidance_mode": mode,
            "v14_guidance_summary": summary,
            "v14_guidance_regime_label": regime_label,
            "v14_guidance_roles": roles if roles else {},
            "v14_guidance_basis": basis if basis else [],
            "v14_guidance_artifacts": artifacts if artifacts else [],
            "v14_guidance_warnings": warnings if warnings else [],
        }

        return record

    @staticmethod
    def create_error_record(
        summary: str = "role safe band guidance generation failed.",
    ) -> Dict[str, Any]:
        """
        Create error record.

        Args:
            summary: Error summary

        Returns:
            Error record
        """
        return V14RoleSafeBandSchema.create_guidance_record(
            status=GUIDANCE_STATUS_ERROR,
            summary=summary,
            regime_label=REGIME_UNKNOWN,
            roles={},
            basis=[],
            artifacts=[],
            warnings=[],
        )

    @staticmethod
    def validate_guidance_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate role safe band guidance record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V14RoleSafeBandSchema.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate version
        version = record.get("v14_guidance_version")
        if version != GUIDANCE_VERSION_V1_4:
            errors.append(f"invalid version: {version} (expected {GUIDANCE_VERSION_V1_4})")

        # Validate status
        status = record.get("v14_guidance_status")
        if status not in V14RoleSafeBandSchema.VALID_STATUSES:
            errors.append(f"invalid status: {status}")

        # Validate mode
        mode = record.get("v14_guidance_mode")
        if mode not in V14RoleSafeBandSchema.VALID_MODES:
            errors.append(f"invalid mode: {mode}")

        # Validate regime_label
        regime_label = record.get("v14_guidance_regime_label")
        if regime_label not in V14RoleSafeBandSchema.VALID_REGIME_LABELS:
            errors.append(f"invalid regime_label: {regime_label}")

        # Validate types
        if not isinstance(record.get("v14_guidance_summary"), str):
            errors.append("summary must be string")

        if not isinstance(record.get("v14_guidance_roles"), dict):
            errors.append("roles must be dict")

        if not isinstance(record.get("v14_guidance_basis"), list):
            errors.append("basis must be list")

        if not isinstance(record.get("v14_guidance_artifacts"), list):
            errors.append("artifacts must be list")

        if not isinstance(record.get("v14_guidance_warnings"), list):
            errors.append("warnings must be list")

        # Validate roles entries
        roles = record.get("v14_guidance_roles", {})
        if isinstance(roles, dict):
            for role_name, role_entry in roles.items():
                if not isinstance(role_entry, dict):
                    errors.append(f"role entry '{role_name}' must be dict")
                    continue

                # Check required role fields
                for field in V14RoleSafeBandSchema.REQUIRED_ROLE_FIELDS:
                    if field not in role_entry:
                        errors.append(f"role '{role_name}' missing field: {field}")

                # Validate bucket values
                current_bucket = role_entry.get("current_ratio_bucket")
                if current_bucket and current_bucket not in V14RoleSafeBandSchema.VALID_RATIO_BUCKETS:
                    errors.append(f"role '{role_name}' has invalid current_ratio_bucket: {current_bucket}")

                safe_bucket = role_entry.get("safe_band_bucket")
                if safe_bucket and safe_bucket not in V14RoleSafeBandSchema.VALID_BAND_BUCKETS:
                    errors.append(f"role '{role_name}' has invalid safe_band_bucket: {safe_bucket}")

                status_val = role_entry.get("status")
                if status_val and status_val not in V14RoleSafeBandSchema.VALID_ROLE_STATUSES:
                    errors.append(f"role '{role_name}' has invalid status: {status_val}")

        return errors


def get_safe_band_schema_info() -> Dict[str, Any]:
    """
    Get role safe band guidance schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.4",
        "schema_type": "role_safe_band_guidance",
        "record_prefix": "v14_guidance_",
        "valid_statuses": V14RoleSafeBandSchema.VALID_STATUSES,
        "valid_modes": V14RoleSafeBandSchema.VALID_MODES,
        "valid_band_buckets": V14RoleSafeBandSchema.VALID_BAND_BUCKETS,
        "valid_ratio_buckets": V14RoleSafeBandSchema.VALID_RATIO_BUCKETS,
        "valid_role_statuses": V14RoleSafeBandSchema.VALID_ROLE_STATUSES,
        "valid_roles": V14RoleSafeBandSchema.VALID_ROLES,
        "valid_regime_labels": V14RoleSafeBandSchema.VALID_REGIME_LABELS,
        "philosophy": "Guidance ≠ Instruction. Describe shape, not recommend action.",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "no_numeric_values_in_text",
            "no_addresses",
            "bucket_output_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Role Safe Band Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create valid record
    print("Test 1: Create valid record")
    record1 = V14RoleSafeBandSchema.create_guidance_record(
        status=GUIDANCE_STATUS_AVAILABLE,
        summary="role safe band guidance assembled for current regime label.",
        regime_label=REGIME_MEDIUM,
        roles={
            ROLE_VOLATILITY: {
                "current_ratio_bucket": RATIO_MEDIUM,
                "safe_band_bucket": BAND_MEDIUM,
                "status": STATUS_WITHIN_SAFE,
                "interpretation": "allocation appears within the structurally safe band for the current regime label.",
            }
        },
        basis=["REGIME_LABEL_USED", "PORTFOLIO_SNAPSHOT_USED"],
    )
    errors1 = V14RoleSafeBandSchema.validate_guidance_record(record1)
    print(f"Valid record errors: {len(errors1)}")
    if errors1:
        for e in errors1:
            print(f"  - {e}")
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    record2 = V14RoleSafeBandSchema.create_error_record(
        summary="role safe band guidance generation failed: invalid inputs."
    )
    errors2 = V14RoleSafeBandSchema.validate_guidance_record(record2)
    print(f"Error record status: {record2['v14_guidance_status']}")
    print(f"Error record errors: {len(errors2)}")
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    info = get_safe_band_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
