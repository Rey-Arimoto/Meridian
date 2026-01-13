#!/usr/bin/env python3
"""
PR148: v1.4 Observation Profile Schema (READ-ONLY)

Purpose:
    Define schema for observation profiles.
    Profile = "How to observe" (windows / cadence / featureset).
    Profiles are separate from watchlist to avoid combinatorial explosion.

Record Prefix:
    v14_profile_

Profile Fields:
    profile_ref: Profile reference (e.g., "CORE_3W")
    windows_enabled: List of enabled windows (SHORT/MEDIUM/LONG)
    cadence_label: Cadence label (FAST/NORMAL/SLOW, label-only)
    featureset_ref: Featureset reference (FULL_MINIMAL/ALERT_MINIMAL/RESEARCH_MINIMAL)
    summary: Non-prescriptive summary

Default Profiles (built-in):
    - CORE_3W: SHORT/MEDIUM/LONG, NORMAL cadence, FULL_MINIMAL features
    - CORE_2W: SHORT/MEDIUM, NORMAL cadence, FULL_MINIMAL features
    - ALERT_ONLY: SHORT, FAST cadence, ALERT_MINIMAL features
    - RESEARCH: MEDIUM/LONG, SLOW cadence, RESEARCH_MINIMAL features

Constitutional Constraints:
    - READ-ONLY: No execution, no trading
    - Non-prescriptive: No should/must/recommend/advise
    - Label-only: No numeric values in text
    - Defensive: Invalid input → valid ERROR record
    - Warning-only guards: Always exit 0
"""

from typing import Any, Dict, List, Optional


# Window constants
WINDOW_SHORT = "SHORT"
WINDOW_MEDIUM = "MEDIUM"
WINDOW_LONG = "LONG"

# Cadence constants
CADENCE_FAST = "FAST"
CADENCE_NORMAL = "NORMAL"
CADENCE_SLOW = "SLOW"

# Featureset constants
FEATURESET_FULL_MINIMAL = "FULL_MINIMAL"
FEATURESET_ALERT_MINIMAL = "ALERT_MINIMAL"
FEATURESET_RESEARCH_MINIMAL = "RESEARCH_MINIMAL"


class V14ObservationProfileSchema:
    """Schema for observation profiles."""

    # Valid windows
    VALID_WINDOWS = [
        WINDOW_SHORT,
        WINDOW_MEDIUM,
        WINDOW_LONG,
    ]

    # Valid cadences
    VALID_CADENCES = [
        CADENCE_FAST,
        CADENCE_NORMAL,
        CADENCE_SLOW,
    ]

    # Valid featuresets
    VALID_FEATURESETS = [
        FEATURESET_FULL_MINIMAL,
        FEATURESET_ALERT_MINIMAL,
        FEATURESET_RESEARCH_MINIMAL,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "profile_ref",
        "windows_enabled",
        "cadence_label",
        "featureset_ref",
        "summary",
    ]

    @staticmethod
    def create_profile(
        profile_ref: str,
        windows_enabled: List[str],
        cadence_label: str = CADENCE_NORMAL,
        featureset_ref: str = FEATURESET_FULL_MINIMAL,
        summary: str = "",
    ) -> Dict[str, Any]:
        """
        Create observation profile.

        Args:
            profile_ref: Profile reference (e.g., "CORE_3W")
            windows_enabled: List of enabled windows (SHORT/MEDIUM/LONG)
            cadence_label: Cadence label (FAST/NORMAL/SLOW)
            featureset_ref: Featureset reference
            summary: Non-prescriptive summary

        Returns:
            Observation profile
        """
        profile = {
            "profile_ref": profile_ref,
            "windows_enabled": windows_enabled,
            "cadence_label": cadence_label,
            "featureset_ref": featureset_ref,
            "summary": summary,
        }

        return profile

    @staticmethod
    def validate_profile(profile: Dict[str, Any]) -> List[str]:
        """
        Validate observation profile.

        Args:
            profile: Profile to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V14ObservationProfileSchema.REQUIRED_FIELDS:
            if field not in profile:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate profile_ref
        profile_ref = profile.get("profile_ref")
        if not isinstance(profile_ref, str) or not profile_ref:
            errors.append("profile_ref must be non-empty string")

        # Validate windows_enabled
        windows_enabled = profile.get("windows_enabled")
        if not isinstance(windows_enabled, list):
            errors.append("windows_enabled must be list")
        else:
            for window in windows_enabled:
                if window not in V14ObservationProfileSchema.VALID_WINDOWS:
                    errors.append(f"invalid window: {window}")

        # Validate cadence_label
        cadence_label = profile.get("cadence_label")
        if cadence_label and cadence_label not in V14ObservationProfileSchema.VALID_CADENCES:
            errors.append(f"invalid cadence_label: {cadence_label}")

        # Validate featureset_ref
        featureset_ref = profile.get("featureset_ref")
        if featureset_ref and featureset_ref not in V14ObservationProfileSchema.VALID_FEATURESETS:
            errors.append(f"invalid featureset_ref: {featureset_ref}")

        # Validate summary
        if not isinstance(profile.get("summary"), str):
            errors.append("summary must be string")

        return errors


# Default profiles (built-in, fixed)
DEFAULT_PROFILES = {
    "CORE_3W": V14ObservationProfileSchema.create_profile(
        profile_ref="CORE_3W",
        windows_enabled=[WINDOW_SHORT, WINDOW_MEDIUM, WINDOW_LONG],
        cadence_label=CADENCE_NORMAL,
        featureset_ref=FEATURESET_FULL_MINIMAL,
        summary="core observation profile with short, medium, and long windows.",
    ),
    "CORE_2W": V14ObservationProfileSchema.create_profile(
        profile_ref="CORE_2W",
        windows_enabled=[WINDOW_SHORT, WINDOW_MEDIUM],
        cadence_label=CADENCE_NORMAL,
        featureset_ref=FEATURESET_FULL_MINIMAL,
        summary="core observation profile with short and medium windows.",
    ),
    "ALERT_ONLY": V14ObservationProfileSchema.create_profile(
        profile_ref="ALERT_ONLY",
        windows_enabled=[WINDOW_SHORT],
        cadence_label=CADENCE_FAST,
        featureset_ref=FEATURESET_ALERT_MINIMAL,
        summary="alert-focused observation profile with short window only.",
    ),
    "RESEARCH": V14ObservationProfileSchema.create_profile(
        profile_ref="RESEARCH",
        windows_enabled=[WINDOW_MEDIUM, WINDOW_LONG],
        cadence_label=CADENCE_SLOW,
        featureset_ref=FEATURESET_RESEARCH_MINIMAL,
        summary="research observation profile with medium and long windows.",
    ),
}


def get_default_profiles() -> Dict[str, Dict[str, Any]]:
    """
    Get default observation profiles.

    Returns:
        Dict of default profiles (profile_ref → profile)
    """
    return DEFAULT_PROFILES.copy()


def get_profile_by_ref(profile_ref: str, profiles: Optional[Dict[str, Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
    """
    Get profile by reference.

    Args:
        profile_ref: Profile reference
        profiles: Optional profiles dict (if None, use defaults)

    Returns:
        Profile or None if not found
    """
    if profiles is None:
        profiles = DEFAULT_PROFILES

    return profiles.get(profile_ref)


def get_observation_profile_schema_info() -> Dict[str, Any]:
    """
    Get observation profile schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1",
        "schema_type": "observation_profile",
        "record_prefix": "v14_profile_",
        "valid_windows": V14ObservationProfileSchema.VALID_WINDOWS,
        "valid_cadences": V14ObservationProfileSchema.VALID_CADENCES,
        "valid_featuresets": V14ObservationProfileSchema.VALID_FEATURESETS,
        "default_profiles": list(DEFAULT_PROFILES.keys()),
        "philosophy": "Profile = 'How to observe' (windows / cadence / featureset). Separate from watchlist to avoid explosion.",
        "constitutional_guarantees": [
            "READ-ONLY",
            "non_prescriptive",
            "label_only",
            "defensive",
            "warning-only",
        ],
    }


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.4 Observation Profile Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Get default profiles
    print("Test 1: Get default profiles")
    profiles = get_default_profiles()
    print(f"Default profiles: {len(profiles)}")
    for ref in profiles:
        print(f"  - {ref}: {profiles[ref]['windows_enabled']}")
    print()

    # Test 2: Validate default profiles
    print("Test 2: Validate default profiles")
    for ref, profile in profiles.items():
        errors = V14ObservationProfileSchema.validate_profile(profile)
        print(f"{ref}: {len(errors)} errors")
        if errors:
            for e in errors:
                print(f"    - {e}")
    print()

    # Test 3: Get profile by ref
    print("Test 3: Get profile by ref")
    core_3w = get_profile_by_ref("CORE_3W")
    print(f"CORE_3W: {core_3w['windows_enabled'] if core_3w else 'NOT FOUND'}")
    print()

    # Test 4: Unknown profile_ref
    print("Test 4: Unknown profile_ref")
    unknown = get_profile_by_ref("UNKNOWN_PROFILE")
    print(f"UNKNOWN_PROFILE: {unknown if unknown else 'NOT FOUND (expected)'}")
    print()

    # Test 5: Get schema info
    print("Test 5: Get schema info")
    info = get_observation_profile_schema_info()
    print(f"Schema version: {info['schema_version']}")
    print(f"Default profiles: {info['default_profiles']}")
    print(f"Philosophy: {info['philosophy']}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
