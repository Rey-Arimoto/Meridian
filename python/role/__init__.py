#!/usr/bin/env python3
"""
PR130: v1.2 Role Carrier Qualification v1 (READ-ONLY)

Purpose:
    Assess asset-to-role fit through 4-axis asset profile.
    Role carrier qualification = structural fit classification.

Exports:
    Asset Profile:
    - V12AssetProfileSchema: Asset profile schema class
    - get_asset_profile_schema_info: Schema metadata
    - Axis constants: OBS_LOW/MEDIUM/HIGH, CENS_LOW/MEDIUM/HIGH,
                     LIQ_LOW/MEDIUM/HIGH, DEP_NONE/LOW/MEDIUM/HIGH

    Role Requirements:
    - VALID_ROLE_TYPES: List of valid role types
    - Role type constants: GAS_ROLE, STABILITY_ROLE, LIQUIDITY_ROLE,
                          VOLATILITY_ROLE, HEDGE_ROLE
    - get_role_requirements: Get requirements for role type
    - get_role_requirements_info: Requirements metadata
    - meets_minimum, meets_maximum: Threshold comparison functions

    Qualification:
    - V12RoleCarrierQualificationSchema: Qualification schema class
    - get_qualification_schema_info: Schema metadata
    - qualify_asset_for_role_v1: Qualification engine
    - get_qualification_engine_v1_info: Engine metadata
    - Qualification status constants: QUALIFIED, PARTIALLY_QUALIFIED, DISQUALIFIED

    Guards:
    - check_role_carrier_record: Constitutional guard
    - check_role_coupling: Role coupling guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

# Asset Profile
from .v12_asset_profile_schema import (
    V12AssetProfileSchema,
    get_asset_profile_schema_info,
    OBS_LOW,
    OBS_MEDIUM,
    OBS_HIGH,
    CENS_LOW,
    CENS_MEDIUM,
    CENS_HIGH,
    LIQ_LOW,
    LIQ_MEDIUM,
    LIQ_HIGH,
    DEP_NONE,
    DEP_LOW,
    DEP_MEDIUM,
    DEP_HIGH,
)

# Role Requirements
from .v12_role_requirements_schema import (
    VALID_ROLE_TYPES,
    GAS_ROLE,
    STABILITY_ROLE,
    LIQUIDITY_ROLE,
    VOLATILITY_ROLE,
    HEDGE_ROLE,
    get_role_requirements,
    get_role_requirements_info,
    meets_minimum,
    meets_maximum,
)

# Qualification
from .v12_role_carrier_qualification_schema import (
    V12RoleCarrierQualificationSchema,
    get_qualification_schema_info,
    QUALIFIED,
    PARTIALLY_QUALIFIED,
    DISQUALIFIED,
)
from .v12_role_carrier_qualification_engine_v1 import (
    qualify_asset_for_role_v1,
    get_qualification_engine_v1_info,
)

# Guards
from .v12_role_carrier_constitutional_guard import (
    check_role_carrier_record,
    check_role_coupling,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Asset Profile
    "V12AssetProfileSchema",
    "get_asset_profile_schema_info",
    "OBS_LOW",
    "OBS_MEDIUM",
    "OBS_HIGH",
    "CENS_LOW",
    "CENS_MEDIUM",
    "CENS_HIGH",
    "LIQ_LOW",
    "LIQ_MEDIUM",
    "LIQ_HIGH",
    "DEP_NONE",
    "DEP_LOW",
    "DEP_MEDIUM",
    "DEP_HIGH",
    # Role Requirements
    "VALID_ROLE_TYPES",
    "GAS_ROLE",
    "STABILITY_ROLE",
    "LIQUIDITY_ROLE",
    "VOLATILITY_ROLE",
    "HEDGE_ROLE",
    "get_role_requirements",
    "get_role_requirements_info",
    "meets_minimum",
    "meets_maximum",
    # Qualification
    "V12RoleCarrierQualificationSchema",
    "get_qualification_schema_info",
    "qualify_asset_for_role_v1",
    "get_qualification_engine_v1_info",
    "QUALIFIED",
    "PARTIALLY_QUALIFIED",
    "DISQUALIFIED",
    # Guards
    "check_role_carrier_record",
    "check_role_coupling",
    "FORBIDDEN_VOCABULARY",
]
