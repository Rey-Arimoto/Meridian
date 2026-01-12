#!/usr/bin/env python3
"""
PR128: v1.2 Role × Distortion Eligibility v1 (READ-ONLY)

Purpose:
    Classify eligibility based on Role × Distortion × Regime × Boundary × Suppression.
    Eligibility ≠ Permission ≠ Action.

Exports:
    - V12RoleDistortionEligibilityRecord: Eligibility record dataclass
    - get_eligibility_schema_info: Schema metadata
    - eligibility_record_to_dict: Convert record to dict
    - classify_role_distortion_eligibility_v1: Classification function
    - check_eligibility_record: Constitutional guard
    - FORBIDDEN_VOCAB: Forbidden vocabulary set
"""

from .v12_role_distortion_eligibility_schema import (
    V12RoleDistortionEligibilityRecord,
    get_eligibility_schema_info,
    eligibility_record_to_dict,
)
from .v12_role_distortion_eligibility_engine_v1 import (
    classify_role_distortion_eligibility_v1,
)
from .v12_eligibility_constitutional_guard import (
    check_eligibility_record,
    FORBIDDEN_VOCAB,
)

__all__ = [
    "V12RoleDistortionEligibilityRecord",
    "get_eligibility_schema_info",
    "eligibility_record_to_dict",
    "classify_role_distortion_eligibility_v1",
    "check_eligibility_record",
    "FORBIDDEN_VOCAB",
]
