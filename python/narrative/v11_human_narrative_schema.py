#!/usr/bin/env python3
"""
PR123: v1.1 Human Narrative Schema v1 (READ-ONLY)

Purpose:
    Define schema for human-readable narrative records.
    Narrative = Structural Situation Story (not action/recommendation).

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-evaluative: No good/bad vocabulary
    - Non-prescriptive: No "should" language
    - No token literals: No SUI, USDC, BTC, ETH
    - No amounts: No numeric values in output
    - No addresses: No 0x... patterns
    - No trading vocabulary: No swap, buy, sell, execute, sign, transfer

Narrative Philosophy:
    Narrative ≠ Instruction
    Narrative ≠ Recommendation
    Narrative = Structural Situation Description

    Narrative provides:
    - Human-readable story of current state
    - Label-based language (regime, drift, permission)
    - Non-evaluative description
    - Artifact references (which records explain state)

    Narrative does NOT:
    - Recommend actions
    - Evaluate quality (good/bad)
    - Contain token names, amounts, addresses
    - Prescribe responses
    - Use imperative language

v11_narrative_ Prefix:
    All narrative fields use v11_narrative_ prefix for clear separation
    from other v1.1 fields.

Schema Fields:
    - v11_narrative_mode: ON | OFF
    - v11_narrative_status: AVAILABLE | UNAVAILABLE | ERROR
    - v11_narrative_style: CONCISE | STANDARD | DETAILED
    - v11_narrative_text: Human-readable narrative (non-prescriptive)
    - v11_narrative_sections: Optional array of labeled sections
    - v11_narrative_basis: Array of field names referenced
    - v11_narrative_artifacts: Array of artifact names referenced
"""

from typing import Any, Dict, List, Optional


class V11HumanNarrativeSchema:
    """v1.1 Human Narrative Schema Definition."""

    # Required fields
    REQUIRED_FIELDS = [
        "v11_narrative_mode",
        "v11_narrative_status",
        "v11_narrative_style",
        "v11_narrative_text",
        "v11_narrative_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v11_narrative_sections",
        "v11_narrative_artifacts",
        "v11_narrative_warnings",
    ]

    # Valid enum values
    VALID_MODES = ["ON", "OFF"]
    VALID_STATUSES = ["AVAILABLE", "UNAVAILABLE", "ERROR"]
    VALID_STYLES = ["CONCISE", "STANDARD", "DETAILED"]

    @staticmethod
    def create_empty_record() -> Dict[str, Any]:
        """
        Create an empty narrative record.

        Returns:
            Empty narrative record
        """
        return {
            "v11_narrative_mode": "ON",
            "v11_narrative_status": "UNAVAILABLE",
            "v11_narrative_style": "STANDARD",
            "v11_narrative_text": "no narrative available.",
            "v11_narrative_basis": [],
        }

    @staticmethod
    def create_error_record(error_message: str = "narrative generation failed.") -> Dict[str, Any]:
        """
        Create an ERROR narrative record.

        Args:
            error_message: Error description

        Returns:
            ERROR narrative record
        """
        return {
            "v11_narrative_mode": "ON",
            "v11_narrative_status": "ERROR",
            "v11_narrative_style": "STANDARD",
            "v11_narrative_text": error_message,
            "v11_narrative_basis": [],
        }

    @staticmethod
    def create_narrative_record(
        text: str,
        style: str = "STANDARD",
        basis: Optional[List[str]] = None,
        artifacts: Optional[List[str]] = None,
        sections: Optional[List[Dict[str, str]]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a narrative record.

        Args:
            text: Human-readable narrative text
            style: CONCISE | STANDARD | DETAILED
            basis: Optional array of field names referenced
            artifacts: Optional array of artifact names
            sections: Optional array of labeled sections
            warnings: Optional array of warnings

        Returns:
            Narrative record
        """
        record = {
            "v11_narrative_mode": "ON",
            "v11_narrative_status": "AVAILABLE",
            "v11_narrative_style": style,
            "v11_narrative_text": text,
            "v11_narrative_basis": basis or [],
        }

        if artifacts:
            record["v11_narrative_artifacts"] = artifacts

        if sections:
            record["v11_narrative_sections"] = sections

        if warnings:
            record["v11_narrative_warnings"] = warnings

        return record

    @staticmethod
    def validate_structure(record: Dict[str, Any]) -> List[str]:
        """
        Validate narrative record structure.

        Args:
            record: Narrative record to validate

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        # Check required fields
        for field in V11HumanNarrativeSchema.REQUIRED_FIELDS:
            if field not in record:
                warnings.append(f"Missing required field: {field}")

        # Validate mode
        if "v11_narrative_mode" in record:
            if record["v11_narrative_mode"] not in V11HumanNarrativeSchema.VALID_MODES:
                warnings.append(f"Invalid narrative mode: {record['v11_narrative_mode']}")

        # Validate status
        if "v11_narrative_status" in record:
            if record["v11_narrative_status"] not in V11HumanNarrativeSchema.VALID_STATUSES:
                warnings.append(f"Invalid narrative status: {record['v11_narrative_status']}")

        # Validate style
        if "v11_narrative_style" in record:
            if record["v11_narrative_style"] not in V11HumanNarrativeSchema.VALID_STYLES:
                warnings.append(f"Invalid narrative style: {record['v11_narrative_style']}")

        # Validate text (must be string)
        if "v11_narrative_text" in record:
            if not isinstance(record["v11_narrative_text"], str):
                warnings.append("Narrative text must be string")

        # Validate basis (must be list of strings)
        if "v11_narrative_basis" in record:
            if not isinstance(record["v11_narrative_basis"], list):
                warnings.append("Basis must be a list")
            else:
                for basis_field in record["v11_narrative_basis"]:
                    if not isinstance(basis_field, str):
                        warnings.append(f"Basis field must be string: {basis_field}")

        # Validate artifacts (must be list of strings if present)
        if "v11_narrative_artifacts" in record:
            if not isinstance(record["v11_narrative_artifacts"], list):
                warnings.append("Artifacts must be a list")
            else:
                for artifact in record["v11_narrative_artifacts"]:
                    if not isinstance(artifact, str):
                        warnings.append(f"Artifact must be string: {artifact}")

        # Validate sections (must be list of dicts if present)
        if "v11_narrative_sections" in record:
            if not isinstance(record["v11_narrative_sections"], list):
                warnings.append("Sections must be a list")
            else:
                for section in record["v11_narrative_sections"]:
                    if not isinstance(section, dict):
                        warnings.append(f"Section must be dict: {section}")

        return warnings


def get_narrative_schema_info() -> Dict[str, Any]:
    """
    Get narrative schema information.

    Returns:
        Dict with schema metadata
    """
    return {
        "schema_version": "v1.1",
        "schema_type": "human_narrative",
        "valid_modes": V11HumanNarrativeSchema.VALID_MODES,
        "valid_statuses": V11HumanNarrativeSchema.VALID_STATUSES,
        "valid_styles": V11HumanNarrativeSchema.VALID_STYLES,
        "required_fields": V11HumanNarrativeSchema.REQUIRED_FIELDS,
        "optional_fields": V11HumanNarrativeSchema.OPTIONAL_FIELDS,
        "constitutional_guarantees": [
            "READ-ONLY",
            "non-evaluative",
            "non-prescriptive",
            "no_token_literals",
            "no_amounts",
            "no_addresses",
            "no_trading_vocabulary",
        ],
    }


if __name__ == "__main__":
    # Self-test
    import json

    print("=" * 60)
    print("v1.1 Human Narrative Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create empty record
    print("Test 1: Create empty record")
    empty = V11HumanNarrativeSchema.create_empty_record()
    print(json.dumps(empty, indent=2))
    print()

    # Test 2: Validate empty record
    print("Test 2: Validate empty record")
    warnings = V11HumanNarrativeSchema.validate_structure(empty)
    print(f"Warnings: {warnings}")
    print()

    # Test 3: Create error record
    print("Test 3: Create error record")
    error = V11HumanNarrativeSchema.create_error_record("test error")
    print(json.dumps(error, indent=2))
    print()

    # Test 4: Create full narrative record
    print("Test 4: Create full narrative record")
    narrative = V11HumanNarrativeSchema.create_narrative_record(
        text="current regime label indicates elevated uncertainty. structural drift label indicates shifting market vocabulary.",
        style="STANDARD",
        basis=["v11_regime_level", "v10_drift_level"],
        artifacts=["pr110_regime_record", "pr120_drift_record"],
    )
    print(json.dumps(narrative, indent=2))
    print()

    # Test 5: Validate full record
    print("Test 5: Validate full record")
    warnings = V11HumanNarrativeSchema.validate_structure(narrative)
    print(f"Warnings: {warnings}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
