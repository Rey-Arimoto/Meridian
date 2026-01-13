#!/usr/bin/env python3
"""
PR145: v1.4 Safe Band × Distortion Stress Overlay v1 Schema (READ-ONLY)

Purpose:
    Define schema for safe band × distortion stress overlay records.
    This overlays static safe band guidance (PR144) with dynamic distortion signals (PR129/PR134).
    This is NOT eligibility, NOT permission, NOT recommendation, NOT instruction.
    It describes structural stress state for human understanding.

Record Prefix:
    v14_overlay_

Required Fields:
    v14_overlay_version: "v1.0"
    v14_overlay_status: AVAILABLE | ERROR
    v14_overlay_mode: READ_ONLY
    v14_overlay_summary: Non-prescriptive summary
    v14_overlay_inputs_present: Dict[str, bool]
    v14_overlay_regime_label: Regime label (label-only)
    v14_overlay_role_type: Role type (label-only)
    v14_overlay_safe_band_bucket: Safe band bucket (bucket-only)
    v14_overlay_distortion_presence: NONE | PRESENT | MULTIPLE | UNKNOWN
    v14_overlay_distortion_subtypes: List[str] (dedup, bounded)
    v14_overlay_band_stress_label: CALM | TENSE | STRESSED | UNKNOWN
    v14_overlay_notes: List[str] (state description only)
    v14_overlay_basis: List[str]
    v14_overlay_artifacts: List[str]
    v14_overlay_warnings: List[str]

Constitutional Constraints:
    - READ-ONLY: No execution, no signing, no transaction construction
    - Non-prescriptive: No should/must/need to/recommend/advise
    - No trading verbs: No buy/sell/swap/execute/sign/transfer
    - No token literals: No SUI/USDC/BTC/ETH
    - No numeric values in text: Bucket labels only
    - No addresses: No 0x... patterns
    - No causal coupling: No therefore/so/hence
    - No eligibility coupling: No "eligible therefore", "permission improved so"
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Overlay version
OVERLAY_VERSION_V1_0 = "v1.0"

# Overlay status constants
OVERLAY_STATUS_AVAILABLE = "AVAILABLE"
OVERLAY_STATUS_ERROR = "ERROR"

# Overlay mode constants
OVERLAY_MODE_READ_ONLY = "READ_ONLY"

# Distortion presence constants
DISTORTION_PRESENCE_NONE = "NONE"
DISTORTION_PRESENCE_PRESENT = "PRESENT"
DISTORTION_PRESENCE_MULTIPLE = "MULTIPLE"
DISTORTION_PRESENCE_UNKNOWN = "UNKNOWN"

# Band stress label constants
BAND_STRESS_CALM = "CALM"
BAND_STRESS_TENSE = "TENSE"
BAND_STRESS_STRESSED = "STRESSED"
BAND_STRESS_UNKNOWN = "UNKNOWN"


class V14SafeBandDistortionOverlaySchema:
    """Schema for safe band × distortion stress overlay records."""

    # Valid statuses
    VALID_STATUSES = [
        OVERLAY_STATUS_AVAILABLE,
        OVERLAY_STATUS_ERROR,
    ]

    # Valid modes
    VALID_MODES = [
        OVERLAY_MODE_READ_ONLY,
    ]

    # Valid distortion presence values
    VALID_DISTORTION_PRESENCE = [
        DISTORTION_PRESENCE_NONE,
        DISTORTION_PRESENCE_PRESENT,
        DISTORTION_PRESENCE_MULTIPLE,
        DISTORTION_PRESENCE_UNKNOWN,
    ]

    # Valid band stress labels
    VALID_BAND_STRESS_LABELS = [
        BAND_STRESS_CALM,
        BAND_STRESS_TENSE,
        BAND_STRESS_STRESSED,
        BAND_STRESS_UNKNOWN,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "v14_overlay_version",
        "v14_overlay_status",
        "v14_overlay_mode",
        "v14_overlay_summary",
        "v14_overlay_inputs_present",
        "v14_overlay_regime_label",
        "v14_overlay_role_type",
        "v14_overlay_safe_band_bucket",
        "v14_overlay_distortion_presence",
        "v14_overlay_distortion_subtypes",
        "v14_overlay_band_stress_label",
        "v14_overlay_notes",
        "v14_overlay_basis",
        "v14_overlay_artifacts",
        "v14_overlay_warnings",
    ]

    # Maximum distortion subtypes list length
    MAX_DISTORTION_SUBTYPES = 20

    @staticmethod
    def create_overlay_record(
        version: str = OVERLAY_VERSION_V1_0,
        status: str = OVERLAY_STATUS_AVAILABLE,
        mode: str = OVERLAY_MODE_READ_ONLY,
        summary: str = "",
        inputs_present: Optional[Dict[str, bool]] = None,
        regime_label: str = "REGIME_UNKNOWN",
        role_type: str = "ROLE_UNKNOWN",
        safe_band_bucket: str = "BAND_UNKNOWN",
        distortion_presence: str = DISTORTION_PRESENCE_UNKNOWN,
        distortion_subtypes: Optional[List[str]] = None,
        band_stress_label: str = BAND_STRESS_UNKNOWN,
        overlay_notes: Optional[List[str]] = None,
        basis: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create safe band × distortion stress overlay record.

        Args:
            version: Overlay version (default "v1.0")
            status: AVAILABLE | ERROR
            mode: READ_ONLY
            summary: Non-prescriptive summary
            inputs_present: Dict of input presence flags
            regime_label: Regime label
            role_type: Role type
            safe_band_bucket: Safe band bucket
            distortion_presence: NONE | PRESENT | MULTIPLE | UNKNOWN
            distortion_subtypes: List of distortion subtypes (dedup, bounded)
            band_stress_label: CALM | TENSE | STRESSED | UNKNOWN
            overlay_notes: List of state description strings
            basis: List of basis strings
            artifacts: List of artifact strings
            warnings: List of warning strings

        Returns:
            Overlay record
        """
        # Dedup and bound distortion_subtypes
        if distortion_subtypes:
            distortion_subtypes = list(dict.fromkeys(distortion_subtypes))  # dedup
            distortion_subtypes = distortion_subtypes[:V14SafeBandDistortionOverlaySchema.MAX_DISTORTION_SUBTYPES]
        else:
            distortion_subtypes = []

        record = {
            "v14_overlay_version": version,
            "v14_overlay_status": status,
            "v14_overlay_mode": mode,
            "v14_overlay_summary": summary,
            "v14_overlay_inputs_present": inputs_present if inputs_present else {},
            "v14_overlay_regime_label": regime_label,
            "v14_overlay_role_type": role_type,
            "v14_overlay_safe_band_bucket": safe_band_bucket,
            "v14_overlay_distortion_presence": distortion_presence,
            "v14_overlay_distortion_subtypes": distortion_subtypes,
            "v14_overlay_band_stress_label": band_stress_label,
            "v14_overlay_notes": overlay_notes if overlay_notes else [],
            "v14_overlay_basis": basis if basis else [],
            "v14_overlay_artifacts": artifacts if artifacts else [],
            "v14_overlay_warnings": warnings if warnings else [],
        }

        return record

    @staticmethod
    def create_error_record(
        summary: str = "safe band distortion overlay generation failed.",
    ) -> Dict[str, Any]:
        """
        Create error record.

        Args:
            summary: Error summary

        Returns:
            Error record
        """
        return V14SafeBandDistortionOverlaySchema.create_overlay_record(
            status=OVERLAY_STATUS_ERROR,
            summary=summary,
            inputs_present={},
            regime_label="REGIME_UNKNOWN",
            role_type="ROLE_UNKNOWN",
            safe_band_bucket="BAND_UNKNOWN",
            distortion_presence=DISTORTION_PRESENCE_UNKNOWN,
            distortion_subtypes=[],
            band_stress_label=BAND_STRESS_UNKNOWN,
            overlay_notes=[],
            basis=[],
            artifacts=[],
            warnings=[],
        )

    @staticmethod
    def validate_overlay_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate overlay record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V14SafeBandDistortionOverlaySchema.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate version
        version = record.get("v14_overlay_version")
        if version != OVERLAY_VERSION_V1_0:
            errors.append(f"invalid version: {version} (expected {OVERLAY_VERSION_V1_0})")

        # Validate status
        status = record.get("v14_overlay_status")
        if status not in V14SafeBandDistortionOverlaySchema.VALID_STATUSES:
            errors.append(f"invalid status: {status}")

        # Validate mode
        mode = record.get("v14_overlay_mode")
        if mode not in V14SafeBandDistortionOverlaySchema.VALID_MODES:
            errors.append(f"invalid mode: {mode}")

        # Validate distortion_presence
        distortion_presence = record.get("v14_overlay_distortion_presence")
        if distortion_presence not in V14SafeBandDistortionOverlaySchema.VALID_DISTORTION_PRESENCE:
            errors.append(f"invalid distortion_presence: {distortion_presence}")

        # Validate band_stress_label
        band_stress_label = record.get("v14_overlay_band_stress_label")
        if band_stress_label not in V14SafeBandDistortionOverlaySchema.VALID_BAND_STRESS_LABELS:
            errors.append(f"invalid band_stress_label: {band_stress_label}")

        # Validate types
        if not isinstance(record.get("v14_overlay_summary"), str):
            errors.append("summary must be string")

        if not isinstance(record.get("v14_overlay_inputs_present"), dict):
            errors.append("inputs_present must be dict")

        if not isinstance(record.get("v14_overlay_regime_label"), str):
            errors.append("regime_label must be string")

        if not isinstance(record.get("v14_overlay_role_type"), str):
            errors.append("role_type must be string")

        if not isinstance(record.get("v14_overlay_safe_band_bucket"), str):
            errors.append("safe_band_bucket must be string")

        if not isinstance(record.get("v14_overlay_distortion_subtypes"), list):
            errors.append("distortion_subtypes must be list")

        if not isinstance(record.get("v14_overlay_notes"), list):
            errors.append("overlay_notes must be list")

        if not isinstance(record.get("v14_overlay_basis"), list):
            errors.append("basis must be list")

        if not isinstance(record.get("v14_overlay_artifacts"), list):
            errors.append("artifacts must be list")

        if not isinstance(record.get("v14_overlay_warnings"), list):
            errors.append("warnings must be list")

        # Validate distortion_subtypes length
        distortion_subtypes = record.get("v14_overlay_distortion_subtypes", [])
        if isinstance(distortion_subtypes, list):
            if len(distortion_subtypes) > V14SafeBandDistortionOverlaySchema.MAX_DISTORTION_SUBTYPES:
                errors.append(f"distortion_subtypes exceeds max length: {len(distortion_subtypes)} > {V14SafeBandDistortionOverlaySchema.MAX_DISTORTION_SUBTYPES}")

        return errors


def get_overlay_schema_info() -> Dict[str, Any]:
    """
    Get overlay schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.0",
        "schema_type": "safe_band_distortion_overlay",
        "record_prefix": "v14_overlay_",
        "valid_statuses": V14SafeBandDistortionOverlaySchema.VALID_STATUSES,
        "valid_modes": V14SafeBandDistortionOverlaySchema.VALID_MODES,
        "valid_distortion_presence": V14SafeBandDistortionOverlaySchema.VALID_DISTORTION_PRESENCE,
        "valid_band_stress_labels": V14SafeBandDistortionOverlaySchema.VALID_BAND_STRESS_LABELS,
        "philosophy": "Overlay static safe band guidance with dynamic distortion signals. Describe structural stress state only.",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "no_trading_verbs",
            "no_token_literals",
            "no_numeric_values_in_text",
            "no_addresses",
            "no_causal_coupling",
            "no_eligibility_coupling",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Safe Band × Distortion Overlay Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create valid record
    print("Test 1: Create valid record")
    record1 = V14SafeBandDistortionOverlaySchema.create_overlay_record(
        status=OVERLAY_STATUS_AVAILABLE,
        summary="safe band distortion overlay assembled for structural stress state.",
        inputs_present={
            "regime_record": True,
            "role_safe_band_guidance": True,
            "distortion_catalog_record": True,
        },
        regime_label="REGIME_MEDIUM",
        role_type="VOLATILITY_ROLE",
        safe_band_bucket="BAND_MEDIUM",
        distortion_presence=DISTORTION_PRESENCE_PRESENT,
        distortion_subtypes=["SUBTYPE_A"],
        band_stress_label=BAND_STRESS_TENSE,
        overlay_notes=["allocation within safe band but distortion signal present indicates structural tension."],
        basis=["REGIME_LABEL_USED", "SAFE_BAND_USED", "DISTORTION_CATALOG_USED"],
    )
    errors1 = V14SafeBandDistortionOverlaySchema.validate_overlay_record(record1)
    print(f"Valid record errors: {len(errors1)}")
    if errors1:
        for e in errors1:
            print(f"  - {e}")
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    record2 = V14SafeBandDistortionOverlaySchema.create_error_record(
        summary="safe band distortion overlay generation failed: invalid inputs."
    )
    errors2 = V14SafeBandDistortionOverlaySchema.validate_overlay_record(record2)
    print(f"Error record status: {record2['v14_overlay_status']}")
    print(f"Error record errors: {len(errors2)}")
    print()

    # Test 3: Get schema info
    print("Test 3: Get schema info")
    info = get_overlay_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
