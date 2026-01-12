#!/usr/bin/env python3
"""
PR130: v1.2 Role Carrier Qualification Engine v1 (READ-ONLY)

Purpose:
    Assess asset-to-role fit by comparing asset profile against role requirements.
    Static, deterministic, threshold-based only (no learning, no weights).

Rules:
    1. Invalid input → ERROR + DISQUALIFIED
    2. Unknown role type → ERROR + DISQUALIFIED
    3. Check each axis against role requirements:
       - min_* requirements: asset value >= required value
       - max_* requirements: asset value <= required value
    4. Track failed axes
    5. Return:
       - QUALIFIED: All axes meet requirements (0 failures)
       - PARTIALLY_QUALIFIED: Some axes meet requirements (1-3 failures)
       - DISQUALIFIED: No axes meet requirements or all fail (4 failures)

Qualification ≠ Signal ≠ Recommendation. Output is a label only.
"""

from typing import Any, Dict, List, Optional

from .v12_asset_profile_schema import V12AssetProfileSchema
from .v12_role_requirements_schema import (
    VALID_ROLE_TYPES,
    get_role_requirements,
    meets_minimum,
    meets_maximum,
    OBSERVABILITY_ORDER,
    CENSORSHIP_RESISTANCE_ORDER,
    LIQUIDATABILITY_ORDER,
    DEPENDENCY_ORDER,
)
from .v12_role_carrier_qualification_schema import (
    V12RoleCarrierQualificationSchema,
    QUALIFIED,
    PARTIALLY_QUALIFIED,
    DISQUALIFIED,
)


def _safe_get(d: Optional[Dict[str, Any]], key: str, default: Any = None) -> Any:
    """
    Safely get value from dict.

    Args:
        d: Dictionary (may be None)
        key: Key to get
        default: Default value if not found

    Returns:
        Value or default
    """
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def qualify_asset_for_role_v1(
    asset_profile_record: Optional[Dict[str, Any]],
    role_type: str,
) -> Dict[str, Any]:
    """
    Assess asset-to-role fit.

    Args:
        asset_profile_record: PR130 asset profile record
        role_type: Role type to assess (GAS_ROLE, STABILITY_ROLE, etc.)

    Returns:
        Qualification record (always valid, ERROR on failure)
    """
    try:
        # Validate inputs
        if not isinstance(asset_profile_record, dict):
            return V12RoleCarrierQualificationSchema.create_error_record(
                role_type=role_type,
                error_message="invalid asset_profile_record (not a dict).",
            )

        if role_type not in VALID_ROLE_TYPES:
            return V12RoleCarrierQualificationSchema.create_error_record(
                role_type=role_type,
                error_message=f"unknown role_type: {role_type}.",
            )

        # Get role requirements
        role_reqs = get_role_requirements(role_type)
        if not role_reqs:
            return V12RoleCarrierQualificationSchema.create_error_record(
                role_type=role_type,
                error_message=f"failed to retrieve requirements for {role_type}.",
            )

        # Extract asset profile axes
        observability = _safe_get(asset_profile_record, "asset_profile_observability", "UNCLASSIFIED")
        censorship_resistance = _safe_get(asset_profile_record, "asset_profile_censorship_resistance", "UNCLASSIFIED")
        liquidatability = _safe_get(asset_profile_record, "asset_profile_liquidatability", "UNCLASSIFIED")
        dependency = _safe_get(asset_profile_record, "asset_profile_dependency", "UNCLASSIFIED")
        asset_summary = _safe_get(asset_profile_record, "asset_profile_summary", "")

        # Check if asset profile has ERROR status
        asset_status = _safe_get(asset_profile_record, "asset_profile_status", "AVAILABLE")
        if asset_status == "ERROR":
            return V12RoleCarrierQualificationSchema.create_error_record(
                role_type=role_type,
                error_message="asset_profile has ERROR status.",
            )

        basis = []
        failed_axes = []

        # Check observability (minimum requirement)
        min_observability = role_reqs.get("min_observability")
        if min_observability:
            basis.append("asset_profile_observability")
            if not meets_minimum(observability, min_observability, OBSERVABILITY_ORDER):
                failed_axes.append("observability")

        # Check censorship resistance (minimum requirement)
        min_censorship_resistance = role_reqs.get("min_censorship_resistance")
        if min_censorship_resistance:
            basis.append("asset_profile_censorship_resistance")
            if not meets_minimum(censorship_resistance, min_censorship_resistance, CENSORSHIP_RESISTANCE_ORDER):
                failed_axes.append("censorship_resistance")

        # Check liquidatability (minimum requirement)
        min_liquidatability = role_reqs.get("min_liquidatability")
        if min_liquidatability:
            basis.append("asset_profile_liquidatability")
            if not meets_minimum(liquidatability, min_liquidatability, LIQUIDATABILITY_ORDER):
                failed_axes.append("liquidatability")

        # Check dependency (maximum requirement - lower is better)
        max_dependency = role_reqs.get("max_dependency")
        if max_dependency:
            basis.append("asset_profile_dependency")
            if not meets_maximum(dependency, max_dependency, DEPENDENCY_ORDER):
                failed_axes.append("dependency")

        # Determine qualification status
        num_failures = len(failed_axes)
        if num_failures == 0:
            qualification_status = QUALIFIED
        elif num_failures >= 4:
            # All 4 axes failed
            qualification_status = DISQUALIFIED
        else:
            # Some axes failed (1-3)
            qualification_status = PARTIALLY_QUALIFIED

        return V12RoleCarrierQualificationSchema.create_qualification_record(
            role_type=role_type,
            qualification_status=qualification_status,
            failed_axes=failed_axes,
            basis=basis,
            asset_profile_summary=asset_summary if asset_summary else None,
        )

    except Exception as e:
        return V12RoleCarrierQualificationSchema.create_error_record(
            role_type=role_type,
            error_message=f"exception: {type(e).__name__}",
        )


def get_qualification_engine_v1_info() -> Dict[str, Any]:
    """
    Get qualification engine v1 information.

    Returns:
        Dict with engine metadata
    """
    return {
        "engine_version": "v1",
        "engine_type": "role_carrier_qualification",
        "input_schema": "asset_profile + role_type",
        "output_schema": "v12_role_carrier_qualification",
        "qualification_rules": [
            "invalid_input → ERROR + DISQUALIFIED",
            "unknown_role_type → ERROR + DISQUALIFIED",
            "check_each_axis_against_requirements",
            "0_failures → QUALIFIED",
            "1-3_failures → PARTIALLY_QUALIFIED",
            "4_failures → DISQUALIFIED",
        ],
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "deterministic",
            "defensive",
            "no_token_literals",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json
    from .v12_asset_profile_schema import (
        V12AssetProfileSchema,
        OBS_HIGH,
        OBS_MEDIUM,
        OBS_LOW,
        CENS_HIGH,
        CENS_MEDIUM,
        CENS_LOW,
        LIQ_HIGH,
        LIQ_MEDIUM,
        LIQ_LOW,
        DEP_NONE,
        DEP_LOW,
        DEP_MEDIUM,
        DEP_HIGH,
    )
    from .v12_role_requirements_schema import GAS_ROLE, STABILITY_ROLE, LIQUIDITY_ROLE

    print("=" * 60)
    print("v1.2 Role Carrier Qualification Engine v1 - Self Test")
    print("=" * 60)
    print()

    # Test 1: Invalid input
    print("Test 1: Invalid input → ERROR")
    result1 = qualify_asset_for_role_v1(None, GAS_ROLE)
    print(f"Status: {result1['v12_role_carrier_status']}")
    print(f"Qualification: {result1['v12_role_carrier_qualification_status']}")
    print()

    # Test 2: Perfect GAS_ROLE match
    print("Test 2: Perfect GAS_ROLE match → QUALIFIED")
    perfect_gas_profile = V12AssetProfileSchema.create_asset_profile(
        observability=OBS_HIGH,
        censorship_resistance=CENS_HIGH,
        liquidatability=LIQ_MEDIUM,
        dependency=DEP_LOW,
    )
    result2 = qualify_asset_for_role_v1(perfect_gas_profile, GAS_ROLE)
    print(f"Qualification: {result2['v12_role_carrier_qualification_status']}")
    print(f"Failed axes: {result2['v12_role_carrier_failed_axes']}")
    print(f"Summary: {result2['v12_role_carrier_summary']}")
    print()

    # Test 3: Partial match (1 failure)
    print("Test 3: Partial match (1 failure) → PARTIALLY_QUALIFIED")
    partial_profile = V12AssetProfileSchema.create_asset_profile(
        observability=OBS_HIGH,
        censorship_resistance=CENS_HIGH,
        liquidatability=LIQ_LOW,  # Fails for GAS_ROLE (needs MEDIUM)
        dependency=DEP_LOW,
    )
    result3 = qualify_asset_for_role_v1(partial_profile, GAS_ROLE)
    print(f"Qualification: {result3['v12_role_carrier_qualification_status']}")
    print(f"Failed axes: {result3['v12_role_carrier_failed_axes']}")
    print()

    # Test 4: Complete mismatch (all 4 failures)
    print("Test 4: Complete mismatch (all 4 failures) → DISQUALIFIED")
    bad_profile = V12AssetProfileSchema.create_asset_profile(
        observability=OBS_LOW,
        censorship_resistance=CENS_LOW,
        liquidatability=LIQ_LOW,
        dependency=DEP_HIGH,
    )
    result4 = qualify_asset_for_role_v1(bad_profile, GAS_ROLE)
    print(f"Qualification: {result4['v12_role_carrier_qualification_status']}")
    print(f"Failed axes: {result4['v12_role_carrier_failed_axes']}")
    print()

    # Test 5: STABILITY_ROLE match
    print("Test 5: STABILITY_ROLE match → QUALIFIED")
    stability_profile = V12AssetProfileSchema.create_asset_profile(
        observability=OBS_MEDIUM,
        censorship_resistance=CENS_MEDIUM,
        liquidatability=LIQ_HIGH,
        dependency=DEP_MEDIUM,
    )
    result5 = qualify_asset_for_role_v1(stability_profile, STABILITY_ROLE)
    print(f"Qualification: {result5['v12_role_carrier_qualification_status']}")
    print(f"Failed axes: {result5['v12_role_carrier_failed_axes']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
