#!/usr/bin/env python3
"""
PR139: v1.2 Narrative Rescue Flow Extension Schema (READ-ONLY)

Purpose:
    Schema for PR137 Rescue Flow Graph extension to PR123 Human Narrative Builder.
    Provides structural explanation (not instruction/conclusion).

Record Prefix:
    v12_rescue_narrative_

Required Fields:
    v12_rescue_narrative_mode : ON|OFF
    v12_rescue_narrative_status : AVAILABLE|ERROR|SKIPPED
    v12_rescue_narrative_style : CONCISE|STANDARD|DETAILED
    v12_rescue_narrative_summary : Non-instructive short text
    v12_rescue_narrative_paragraphs : list[str] (label-focused, short sentences)
    v12_rescue_narrative_basis : list[str]

Optional Fields:
    v12_rescue_narrative_warnings : list[str]

Constitutional Constraints:
    - READ-ONLY: No execution, no recommendations
    - Non-prescriptive: No "should", "must", "therefore"
    - No token literals: No SUI, USDC, BTC, ETH
    - No numeric patterns: No amounts, percentages
    - No trading vocabulary: No swap, buy, sell, execute
    - Narrative ≠ Instruction ≠ Conclusion
"""

from typing import Any, Dict, List, Optional


# Mode constants
RESCUE_NARRATIVE_MODE_ON = "ON"
RESCUE_NARRATIVE_MODE_OFF = "OFF"

# Status constants
RESCUE_NARRATIVE_STATUS_AVAILABLE = "AVAILABLE"
RESCUE_NARRATIVE_STATUS_ERROR = "ERROR"
RESCUE_NARRATIVE_STATUS_SKIPPED = "SKIPPED"

# Style constants
RESCUE_NARRATIVE_STYLE_CONCISE = "CONCISE"
RESCUE_NARRATIVE_STYLE_STANDARD = "STANDARD"
RESCUE_NARRATIVE_STYLE_DETAILED = "DETAILED"


class V12NarrativeRescueFlowExtensionSchema:
    """Schema for narrative rescue flow extension records."""

    # Valid modes
    VALID_MODES = [
        RESCUE_NARRATIVE_MODE_ON,
        RESCUE_NARRATIVE_MODE_OFF,
    ]

    # Valid statuses
    VALID_STATUSES = [
        RESCUE_NARRATIVE_STATUS_AVAILABLE,
        RESCUE_NARRATIVE_STATUS_ERROR,
        RESCUE_NARRATIVE_STATUS_SKIPPED,
    ]

    # Valid styles
    VALID_STYLES = [
        RESCUE_NARRATIVE_STYLE_CONCISE,
        RESCUE_NARRATIVE_STYLE_STANDARD,
        RESCUE_NARRATIVE_STYLE_DETAILED,
    ]

    # Required fields
    REQUIRED_FIELDS = [
        "v12_rescue_narrative_mode",
        "v12_rescue_narrative_status",
        "v12_rescue_narrative_style",
        "v12_rescue_narrative_summary",
        "v12_rescue_narrative_paragraphs",
        "v12_rescue_narrative_basis",
    ]

    # Optional fields
    OPTIONAL_FIELDS = [
        "v12_rescue_narrative_warnings",
    ]

    @staticmethod
    def create_rescue_narrative_record(
        mode: str = RESCUE_NARRATIVE_MODE_ON,
        status: str = RESCUE_NARRATIVE_STATUS_AVAILABLE,
        style: str = RESCUE_NARRATIVE_STYLE_STANDARD,
        summary: str = "",
        paragraphs: Optional[List[str]] = None,
        basis: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create rescue narrative record.

        Args:
            mode: ON | OFF
            status: AVAILABLE | ERROR | SKIPPED
            style: CONCISE | STANDARD | DETAILED
            summary: Non-instructive short text
            paragraphs: List of label-focused paragraphs
            basis: List of basis field names
            warnings: Optional list of warnings

        Returns:
            Rescue narrative record
        """
        record = {
            "v12_rescue_narrative_mode": mode,
            "v12_rescue_narrative_status": status,
            "v12_rescue_narrative_style": style,
            "v12_rescue_narrative_summary": summary,
            "v12_rescue_narrative_paragraphs": paragraphs if paragraphs else [],
            "v12_rescue_narrative_basis": basis if basis else [],
        }

        if warnings:
            record["v12_rescue_narrative_warnings"] = warnings

        return record

    @staticmethod
    def create_error_record(
        summary: str = "rescue narrative generation failed.",
        style: str = RESCUE_NARRATIVE_STYLE_STANDARD,
    ) -> Dict[str, Any]:
        """
        Create error record.

        Args:
            summary: Error summary
            style: Style (for context)

        Returns:
            Error record
        """
        return V12NarrativeRescueFlowExtensionSchema.create_rescue_narrative_record(
            mode=RESCUE_NARRATIVE_MODE_OFF,
            status=RESCUE_NARRATIVE_STATUS_ERROR,
            style=style,
            summary=summary,
            paragraphs=[],
            basis=[],
        )

    @staticmethod
    def create_skipped_record(
        summary: str = "rescue narrative skipped (mode OFF or unavailable).",
        style: str = RESCUE_NARRATIVE_STYLE_STANDARD,
    ) -> Dict[str, Any]:
        """
        Create skipped record.

        Args:
            summary: Skip reason
            style: Style (for context)

        Returns:
            Skipped record
        """
        return V12NarrativeRescueFlowExtensionSchema.create_rescue_narrative_record(
            mode=RESCUE_NARRATIVE_MODE_OFF,
            status=RESCUE_NARRATIVE_STATUS_SKIPPED,
            style=style,
            summary=summary,
            paragraphs=[],
            basis=[],
        )

    @staticmethod
    def validate_rescue_narrative_record(record: Dict[str, Any]) -> List[str]:
        """
        Validate rescue narrative record.

        Args:
            record: Record to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required fields
        for field in V12NarrativeRescueFlowExtensionSchema.REQUIRED_FIELDS:
            if field not in record:
                errors.append(f"missing required field: {field}")

        if errors:
            return errors

        # Validate mode
        mode = record.get("v12_rescue_narrative_mode")
        if mode not in V12NarrativeRescueFlowExtensionSchema.VALID_MODES:
            errors.append(f"invalid mode: {mode}")

        # Validate status
        status = record.get("v12_rescue_narrative_status")
        if status not in V12NarrativeRescueFlowExtensionSchema.VALID_STATUSES:
            errors.append(f"invalid status: {status}")

        # Validate style
        style = record.get("v12_rescue_narrative_style")
        if style not in V12NarrativeRescueFlowExtensionSchema.VALID_STYLES:
            errors.append(f"invalid style: {style}")

        # Validate types
        if not isinstance(record.get("v12_rescue_narrative_summary"), str):
            errors.append("summary must be string")

        if not isinstance(record.get("v12_rescue_narrative_paragraphs"), list):
            errors.append("paragraphs must be list")

        if not isinstance(record.get("v12_rescue_narrative_basis"), list):
            errors.append("basis must be list")

        return errors


if __name__ == "__main__":
    # Self-test
    print("=" * 60)
    print("v1.2 Narrative Rescue Flow Extension Schema - Self Test")
    print("=" * 60)
    print()

    # Test 1: Create valid record
    print("Test 1: Create valid record")
    record1 = V12NarrativeRescueFlowExtensionSchema.create_rescue_narrative_record(
        mode=RESCUE_NARRATIVE_MODE_ON,
        status=RESCUE_NARRATIVE_STATUS_AVAILABLE,
        style=RESCUE_NARRATIVE_STYLE_STANDARD,
        summary="rescue flow structural narrative available.",
        paragraphs=["flow graph indicates STABILITY_ROLE may support VOLATILITY_ROLE."],
        basis=["v12_flow_edges"],
    )
    errors1 = V12NarrativeRescueFlowExtensionSchema.validate_rescue_narrative_record(record1)
    print(f"Valid record errors: {len(errors1)}")
    if errors1:
        for e in errors1:
            print(f"  - {e}")
    print()

    # Test 2: Create error record
    print("Test 2: Create error record")
    record2 = V12NarrativeRescueFlowExtensionSchema.create_error_record(
        summary="flow graph unavailable."
    )
    errors2 = V12NarrativeRescueFlowExtensionSchema.validate_rescue_narrative_record(record2)
    print(f"Error record status: {record2['v12_rescue_narrative_status']}")
    print(f"Error record errors: {len(errors2)}")
    print()

    # Test 3: Create skipped record
    print("Test 3: Create skipped record")
    record3 = V12NarrativeRescueFlowExtensionSchema.create_skipped_record(
        summary="mode OFF."
    )
    errors3 = V12NarrativeRescueFlowExtensionSchema.validate_rescue_narrative_record(record3)
    print(f"Skipped record status: {record3['v12_rescue_narrative_status']}")
    print(f"Skipped record errors: {len(errors3)}")
    print()

    # Test 4: Invalid record (missing field)
    print("Test 4: Invalid record (missing field)")
    record4 = {
        "v12_rescue_narrative_mode": RESCUE_NARRATIVE_MODE_ON,
        "v12_rescue_narrative_status": RESCUE_NARRATIVE_STATUS_AVAILABLE,
    }
    errors4 = V12NarrativeRescueFlowExtensionSchema.validate_rescue_narrative_record(record4)
    print(f"Invalid record errors: {len(errors4)}")
    if errors4:
        for e in errors4:
            print(f"  - {e}")
    print()

    print("=" * 60)
    print("Self-test complete")
    print("=" * 60)
