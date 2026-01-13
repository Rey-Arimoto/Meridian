#!/usr/bin/env python3
"""
PR148: v1.4 Watchlist + Observation Profile v1 (READ-ONLY)

Purpose:
    Watchlist = "What to observe" (pair_ref × source × profile_ref).
    Profile = "How to observe" (windows / cadence / featureset).
    Windows are NOT in watchlist, but in observation profiles.

Exports:
    Watchlist Schema:
    - V14WatchlistSchema: Watchlist schema class
    - get_watchlist_schema_info: Watchlist schema metadata
    - Watchlist constants (WATCHLIST_STATUS_*, PRIORITY_*, ENABLED_*)

    Observation Profile Schema:
    - V14ObservationProfileSchema: Profile schema class
    - get_observation_profile_schema_info: Profile schema metadata
    - get_default_profiles: Get built-in default profiles
    - get_profile_by_ref: Get profile by reference
    - Profile constants (WINDOW_*, CADENCE_*, FEATURESET_*)

    Engine:
    - build_watchlist_record_v1: Build watchlist from items
    - expand_watchlist_to_observation_plan_v1: Expand watchlist to observation plan
    - extract_pair_refs_v1: Extract pair_refs for TS bridge
    - get_watchlist_engine_v1_info: Engine metadata

    Constitutional Guard:
    - check_watchlist_record: Watchlist record guard
    - check_forbidden_vocabulary: Vocabulary guard
    - check_token_literals: Token literal guard
    - check_address_patterns: Address pattern guard
    - check_coupling_phrases: Coupling phrase guard
    - check_numeric_patterns: Numeric pattern guard
    - FORBIDDEN_VOCABULARY: Forbidden vocabulary list
"""

from .v14_watchlist_schema import (
    V14WatchlistSchema,
    get_watchlist_schema_info,
    WATCHLIST_VERSION_V1,
    WATCHLIST_STATUS_AVAILABLE,
    WATCHLIST_STATUS_ERROR,
    WATCHLIST_MODE_READ_ONLY,
    PRIORITY_CORE,
    PRIORITY_EXTENDED,
    PRIORITY_EXPERIMENTAL,
    ENABLED_ON,
    ENABLED_OFF,
)
from .v14_observation_profile_schema import (
    V14ObservationProfileSchema,
    get_observation_profile_schema_info,
    get_default_profiles,
    get_profile_by_ref,
    WINDOW_SHORT,
    WINDOW_MEDIUM,
    WINDOW_LONG,
    CADENCE_FAST,
    CADENCE_NORMAL,
    CADENCE_SLOW,
    FEATURESET_FULL_MINIMAL,
    FEATURESET_ALERT_MINIMAL,
    FEATURESET_RESEARCH_MINIMAL,
)
from .v14_watchlist_engine_v1 import (
    build_watchlist_record_v1,
    expand_watchlist_to_observation_plan_v1,
    extract_pair_refs_v1,
    get_watchlist_engine_v1_info,
)
from .v14_watchlist_constitutional_guard import (
    check_watchlist_record,
    check_forbidden_vocabulary,
    check_token_literals,
    check_address_patterns,
    check_coupling_phrases,
    check_numeric_patterns,
    FORBIDDEN_VOCABULARY,
)

__all__ = [
    # Watchlist Schema
    "V14WatchlistSchema",
    "get_watchlist_schema_info",
    "WATCHLIST_VERSION_V1",
    "WATCHLIST_STATUS_AVAILABLE",
    "WATCHLIST_STATUS_ERROR",
    "WATCHLIST_MODE_READ_ONLY",
    "PRIORITY_CORE",
    "PRIORITY_EXTENDED",
    "PRIORITY_EXPERIMENTAL",
    "ENABLED_ON",
    "ENABLED_OFF",
    # Observation Profile Schema
    "V14ObservationProfileSchema",
    "get_observation_profile_schema_info",
    "get_default_profiles",
    "get_profile_by_ref",
    "WINDOW_SHORT",
    "WINDOW_MEDIUM",
    "WINDOW_LONG",
    "CADENCE_FAST",
    "CADENCE_NORMAL",
    "CADENCE_SLOW",
    "FEATURESET_FULL_MINIMAL",
    "FEATURESET_ALERT_MINIMAL",
    "FEATURESET_RESEARCH_MINIMAL",
    # Engine
    "build_watchlist_record_v1",
    "expand_watchlist_to_observation_plan_v1",
    "extract_pair_refs_v1",
    "get_watchlist_engine_v1_info",
    # Constitutional Guard
    "check_watchlist_record",
    "check_forbidden_vocabulary",
    "check_token_literals",
    "check_address_patterns",
    "check_coupling_phrases",
    "check_numeric_patterns",
    "FORBIDDEN_VOCABULARY",
]
