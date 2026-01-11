#!/usr/bin/env python3
"""
PR116: v1.0 Artifact Bundle Schema v1 (READ-ONLY)

Purpose:
    Artifact bundle schema for pipeline output.
    Bundle = Chain-of-custody container (not decision/evaluation).

Exports:
    - V10ArtifactBundleSchema: Bundle schema class
    - get_bundle_schema_info: Bundle schema metadata
    - build_artifact_bundle_v1: Core bundle builder function
    - get_bundle_builder_v1_info: Builder metadata
    - validate_bundle_record: Constitutional guard for bundle records
"""

from .v10_artifact_bundle_schema import (
    V10ArtifactBundleSchema,
    get_bundle_schema_info,
)
from .v10_bundle_builder_v1 import (
    build_artifact_bundle_v1,
    get_bundle_builder_v1_info,
)
from .v10_bundle_constitutional_guard import (
    validate_bundle_record,
)

__all__ = [
    "V10ArtifactBundleSchema",
    "get_bundle_schema_info",
    "build_artifact_bundle_v1",
    "get_bundle_builder_v1_info",
    "validate_bundle_record",
]
